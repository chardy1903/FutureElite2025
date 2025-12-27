"""
FutureElite - Flask Application

Copyright (c) 2025 [Your Name]. All Rights Reserved.
This software is proprietary and confidential. Unauthorized copying, modification,
distribution, or use of this software, via any medium, is strictly prohibited.
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_login import LoginManager
import os
import sys
import webbrowser
import threading
import time
from pathlib import Path
from datetime import timedelta

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

from .routes import bp
from .auth_routes import auth_bp
from .subscription_routes import subscription_bp
from .storage import StorageManager
from .models import Match, MatchCategory, MatchResult, AppSettings
from .utils import parse_input_date
from .auth import UserSession

# Security imports
try:
    from flask_wtf.csrf import CSRFProtect
    CSRF_AVAILABLE = True
except ImportError:
    CSRF_AVAILABLE = False
    CSRFProtect = None

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    Limiter = None
    get_remote_address = None

try:
    from flask_talisman import Talisman
    TALISMAN_AVAILABLE = True
except ImportError:
    TALISMAN_AVAILABLE = False
    Talisman = None


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    # SECRET_KEY must be set via environment variable - no default fallback
    secret_key = os.environ.get('SECRET_KEY', '').strip()
    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY environment variable must be set. "
            "Generate a secure key with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )
    if len(secret_key) < 32:
        raise RuntimeError(
            f"SECRET_KEY must be at least 32 characters. Current length: {len(secret_key)}. "
            "Generate a secure key with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )
    app.config['SECRET_KEY'] = secret_key
    app.config['JSON_AS_ASCII'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Security: Disable template auto-reload in production
    app.config['TEMPLATES_AUTO_RELOAD'] = os.environ.get('FLASK_ENV') != 'production'
    
    # Secure session cookie configuration
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    # Only set Secure=True in production (HTTPS required)
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.session_protection = 'basic'  # Use basic session protection
    
    @login_manager.user_loader
    def load_user(user_id):
        storage = StorageManager()
        user = storage.get_user_by_id(user_id)
        if user:
            return UserSession(user)
        return None
    
    # Security: Initialize CSRF protection
    csrf = None
    if CSRF_AVAILABLE:
        csrf = CSRFProtect(app)
        # Store csrf in app.extensions for access in blueprints
        app.extensions['csrf'] = csrf
        # Configure CSRF to accept tokens from headers (for JSON API requests)
        app.config['WTF_CSRF_CHECK_DEFAULT'] = True
        app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit
        app.logger.info("CSRF protection enabled")
    else:
        app.logger.warning("flask-wtf not installed - CSRF protection disabled")
    
    # Security: Initialize rate limiting
    if LIMITER_AVAILABLE:
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri="memory://"  # In-memory storage (TODO: Use Redis in production)
        )
        app.extensions['limiter'] = limiter
        app.logger.info("Rate limiting enabled")
    else:
        app.logger.warning("flask-limiter not installed - rate limiting disabled")
        limiter = None
    
    # Security: Initialize security headers
    if TALISMAN_AVAILABLE:
        is_production = os.environ.get('FLASK_ENV') == 'production'
        Talisman(
            app,
            force_https=is_production,
            strict_transport_security=is_production,
            strict_transport_security_max_age=31536000,
            strict_transport_security_include_subdomains=True,
            strict_transport_security_preload=False,  # Set True after HSTS preload approval
            content_security_policy={
                'default-src': "'self'",
                'script-src': "'self' https://cdn.tailwindcss.com 'unsafe-inline'",  # unsafe-inline needed for Tailwind
                'style-src': "'self' 'unsafe-inline' https://cdn.tailwindcss.com",
                'img-src': "'self' data: https:",
                'font-src': "'self' data:",
                'connect-src': "'self'",
            },
            frame_options='DENY',
            referrer_policy='strict-origin-when-cross-origin'
        )
        app.logger.info("Security headers enabled")
    else:
        app.logger.warning("flask-talisman not installed - security headers disabled")
    
    # Security: Handle reverse proxy headers (X-Forwarded-*)
    # Required when deployed behind nginx, Apache, or load balancer
    try:
        from werkzeug.middleware.proxy_fix import ProxyFix
        num_proxies = int(os.environ.get('PROXY_FIX_NUM_PROXIES', '1'))
        if num_proxies > 0:
            app.wsgi_app = ProxyFix(app.wsgi_app, x_for=num_proxies, x_proto=num_proxies, x_host=num_proxies)
            app.logger.info(f"ProxyFix enabled with {num_proxies} proxy(ies)")
    except ImportError:
        app.logger.warning("werkzeug ProxyFix not available - proxy headers may not be handled correctly")
    except Exception as e:
        app.logger.warning(f"ProxyFix configuration error: {e}")
    
    # Register blueprints
    app.register_blueprint(bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(subscription_bp)
    
    # Security: Exempt auth endpoints and webhook from CSRF
    # Must be done AFTER blueprint registration so endpoints exist
    # Auth endpoints are entry points (no session yet), rate-limited, and require credentials
    # Webhook is verified by Stripe signature instead
    if CSRF_AVAILABLE and csrf:
        try:
            # Exempt by endpoint name string (works even when functions are wrapped by decorators)
            # This is the most reliable method for blueprint routes with multiple decorators
            csrf.exempt('auth.login')
            csrf.exempt('auth.register')
            csrf.exempt('subscription.stripe_webhook')
            
            # Also try function reference as backup (may not work if wrapped by rate limiter)
            try:
                from .auth_routes import login, register
                from .subscription_routes import stripe_webhook
                csrf.exempt(login)
                csrf.exempt(register)
                csrf.exempt(stripe_webhook)
            except Exception:
                # Function reference exemption failed (likely due to decorator wrapping)
                # Endpoint name exemptions above should be sufficient
                pass
            
            app.logger.info("CSRF exemptions applied: auth.login, auth.register, subscription.stripe_webhook")
        except Exception as e:
            app.logger.error(f"CRITICAL: Failed to exempt routes from CSRF: {e}", exc_info=True)
            # This is critical - if exemptions fail, auth won't work
            raise
    
    # Production: Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for load balancers and monitoring"""
        return jsonify({
            'status': 'healthy',
            'service': 'FutureElite'
        }), 200
    
    # Security: Add endpoint to get CSRF token for JSON API clients
    if CSRF_AVAILABLE:
        @app.route('/api/csrf-token', methods=['GET'])
        def get_csrf_token():
            """Get CSRF token for JSON API requests"""
            from flask_wtf.csrf import generate_csrf
            from flask import session
            # Ensure session exists for CSRF token validation
            session.permanent = True
            token = generate_csrf()
            return jsonify({'csrf_token': token})
    
    # Add error handler for API routes to return JSON instead of HTML
    @app.errorhandler(500)
    def handle_500_error(e):
        """Return JSON for API errors - sanitized to prevent information leakage"""
        if request.path.startswith('/api/'):
            # Log full error details server-side for debugging
            import traceback
            app.logger.error(f"500 error on {request.path}: {e}", exc_info=True)
            # Return generic error message to client
            return jsonify({
                'success': False,
                'errors': ['An internal error occurred. Please try again later.']
            }), 500
        # For non-API routes, return default HTML error page
        return e
    
    @app.errorhandler(404)
    def handle_404_error(e):
        """Return JSON for API 404 errors"""
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'errors': ['Endpoint not found']
            }), 404
        # For non-API routes, return default HTML error page
        return e
    
    # Handle 400 errors (including CSRF) for JSON requests
    @app.errorhandler(400)
    def handle_400_error(e):
        """Return JSON for 400 errors on JSON requests (including CSRF)"""
        # Skip CSRF errors for exempted routes (login/register should be exempt)
        if request.endpoint in ['auth.login', 'auth.register']:
            # These routes should be exempt - if we get here, something is wrong
            # But don't return CSRF error, return generic error instead
            error_description = str(e.description) if hasattr(e, 'description') else str(e)
            if 'CSRF' in error_description or 'csrf' in error_description.lower():
                app.logger.error(f"CSRF error on exempted route {request.path}: {error_description}")
                # Return generic error instead of CSRF-specific message
                return jsonify({
                    'success': False,
                    'errors': ['Authentication error. Please try again.']
                }), 400
        
        # Check if this is a JSON request
        content_type = request.headers.get('Content-Type', '')
        is_json_request = (
            'application/json' in content_type or
            request.path.startswith('/api/') or
            request.path in ['/login', '/register']
        )
        
        if is_json_request:
            # Check if this is a CSRF error by examining the description
            error_description = str(e.description) if hasattr(e, 'description') else str(e)
            if 'CSRF' in error_description or 'csrf' in error_description.lower():
                app.logger.warning(f"CSRF error on {request.path}: {error_description}")
                return jsonify({
                    'success': False,
                    'errors': ['CSRF token missing or invalid. Please refresh the page and try again.']
                }), 400
            # Generic 400 error for JSON requests
            return jsonify({
                'success': False,
                'errors': [error_description if error_description else 'Bad request']
            }), 400
        # For form submissions, return default HTML error
        return e
    
    # Security: Handle CSRF errors for JSON requests
    if CSRF_AVAILABLE:
        from flask_wtf.csrf import CSRFError
        @app.errorhandler(CSRFError)
        def handle_csrf_error(e):
            """Return JSON for CSRF errors on JSON requests"""
            # Check if this is a JSON request by Content-Type header or path
            content_type = request.headers.get('Content-Type', '')
            is_json_request = (
                'application/json' in content_type or
                request.path.startswith('/api/') or
                request.path in ['/login', '/register']
            )
            
            if is_json_request:
                app.logger.warning(f"CSRF error on {request.path}: {e.description}")
                return jsonify({
                    'success': False,
                    'errors': ['CSRF token missing or invalid. Please refresh the page and try again.']
                }), 400
            # For form submissions, return default HTML error
            return e
    
    # Initialize storage and sample data
    storage = StorageManager()
    _initialize_sample_data(storage)
    
    return app


def _initialize_sample_data(storage: StorageManager):
    """Initialize sample data if no matches exist"""
    existing_matches = storage.load_matches()
    if not existing_matches:
        sample_matches = [
            {
                "id": "20250911_120000",
                "category": "Pre-Season Friendly",
                "date": "11 Sep 2025",
                "opponent": "OLE Academy",
                "location": "Al-Farabi School, Khobar",
                "result": "Win",
                "score": "3 - 2",
                "brodie_goals": 1,
                "brodie_assists": 0,
                "minutes_played": 20,
                "notes": "Penalty goal.",
                "is_fixture": False
            },
            {
                "id": "20251009_120000",
                "category": "Pre-Season Friendly",
                "date": "09 Oct 2025",
                "opponent": "Ettifaq Club",
                "location": "Al-Farabi School, Khobar",
                "result": "Loss",
                "score": "2 - 3",
                "brodie_goals": 2,
                "brodie_assists": 0,
                "minutes_played": 40,
                "notes": "Goal 1: Penalty. Goal 2: Long pass; beat two defenders; finished bottom-left.",
                "is_fixture": False
            },
            {
                "id": "20251016_120000",
                "category": "Pre-Season Friendly",
                "date": "16 Oct 2025",
                "opponent": "Al Hilal",
                "location": "Arena Stadiums",
                "result": "Loss",
                "score": "3 - 5",
                "brodie_goals": 0,
                "brodie_assists": 0,
                "minutes_played": 20,
                "notes": "—",
                "is_fixture": False
            },
            {
                "id": "20251017_120000",
                "category": "Pre-Season Friendly",
                "date": "17 Oct 2025",
                "opponent": "Al Fatah",
                "location": "Al-Farabi School, Khobar",
                "result": "Loss",
                "score": "2 - 3",
                "brodie_goals": 1,
                "brodie_assists": 0,
                "minutes_played": 40,
                "notes": "Received outside box; dribbled inside defenders; top-right finish.",
                "is_fixture": False
            },
            {
                "id": "20251023_120000",
                "category": "Pre-Season Friendly",
                "date": "23 Oct 2025",
                "opponent": "Dhahran Academy",
                "location": "Offside Arena",
                "result": "Win",
                "score": "7 - 5",
                "brodie_goals": 1,
                "brodie_assists": 1,
                "minutes_played": 30,
                "notes": "Scored from edge of box after dribbling and losing defenders. Also provided 1 assist.",
                "is_fixture": False
            },
            {
                "id": "20251028_120000",
                "category": "Pre-Season Friendly",
                "date": "28 Oct 2025",
                "opponent": "Bahrain National Team 🇧🇭",
                "location": "TBD",
                "result": None,
                "score": "",
                "brodie_goals": 0,
                "brodie_assists": 0,
                "minutes_played": 0,
                "notes": "",
                "is_fixture": True
            },
            {
                "id": "20251030_120000",
                "category": "Pre-Season Friendly",
                "date": "30 Oct 2025",
                "opponent": "Winners Academy ❤️💛",
                "location": "TBD",
                "result": None,
                "score": "",
                "brodie_goals": 0,
                "brodie_assists": 0,
                "minutes_played": 0,
                "notes": "",
                "is_fixture": True
            }
        ]
        
        # Save sample matches
        storage._save_matches(sample_matches)


def open_browser():
    """Open browser after a short delay"""
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:8080')


def main():
    """Main entry point - Development only"""
    # Security: Prevent running Flask dev server in production
    flask_env = os.environ.get('FLASK_ENV', '').strip().lower()
    if flask_env == 'production':
        print("ERROR: Flask development server cannot run in production mode.")
        print("Use gunicorn or another production WSGI server instead:")
        print("  gunicorn -c gunicorn.conf.py wsgi:app")
        print("Or use the wsgi.py entry point:")
        print("  gunicorn wsgi:app")
        sys.exit(1)
    
    app = create_app()
    
    # Open browser in a separate thread (development only)
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("FutureElite starting in DEVELOPMENT mode...")
    print("Opening browser at http://127.0.0.1:8080")
    print("Press Ctrl+C to stop the application")
    print()
    print("WARNING: This is the development server. For production, use:")
    print("  gunicorn -c gunicorn.conf.py wsgi:app")
    
    try:
        # Use port 8080 to avoid conflict with AirPlay Receiver
        app.run(host='127.0.0.1', port=8080, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down FutureElite...")


if __name__ == '__main__':
    main()

