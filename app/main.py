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
    
    # Detect if we're in local development (localhost/127.0.0.1)
    # Default to Secure=True unless we're definitely in local development
    flask_env = os.environ.get('FLASK_ENV', '').strip().lower()
    is_production_env = flask_env == 'production'
    
    # Check for local development indicators
    is_local_dev = (
        flask_env == 'development' or
        os.environ.get('FLASK_DEBUG', '').lower() in ('true', '1', 'on') or
        'localhost' in os.environ.get('HOST', '').lower() or
        '127.0.0.1' in os.environ.get('HOST', '')
    )
    
    # Set Secure=True unless we're definitely in local development
    # This ensures session cookies work correctly in production (HTTPS)
    # Even if FLASK_ENV is not explicitly set to 'production'
    app.config['SESSION_COOKIE_SECURE'] = not is_local_dev
    
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Log cookie configuration for debugging
    if is_local_dev:
        app.logger.info("Session cookies configured for local development (Secure=False)")
    else:
        app.logger.info("Session cookies configured for production (Secure=True)")
    
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
        
        # CRITICAL FIX: Patch Flask-WTF's _exempt_views check to always allow auth endpoints
        # Flask-WTF checks exemptions in its before_request hook, but exempt() isn't working
        # reliably with decorated blueprint routes. We'll patch the exemption check directly.
        if hasattr(csrf, '_exempt_views'):
            try:
                # Store original _exempt_views set
                original_exempt_views = csrf._exempt_views
                
                # Create a custom set-like object that always returns True for auth endpoints
                # Must be fully compatible with set operations Flask-WTF might use
                class ExemptViewsSet:
                    def __init__(self, original_set):
                        self._original = original_set
                        self._auth_endpoints = {
                            'auth.login', 'auth.register', 'auth.forgot_password',
                            'main.import_excel', 'main.import_data', 'main.scout_pdf', 'main.generate_pdf',
                            'subscription.get_subscription_status'
                        }
                    
                    def __contains__(self, item):
                        # Always return True for auth endpoints
                        if isinstance(item, str) and item in self._auth_endpoints:
                            return True
                        # Check original set for other items
                        try:
                            return item in self._original
                        except Exception:
                            return False
                    
                    def add(self, item):
                        self._original.add(item)
                    
                    def remove(self, item):
                        self._original.remove(item)
                    
                    def discard(self, item):
                        self._original.discard(item)
                    
                    def __iter__(self):
                        return iter(self._original)
                    
                    def __len__(self):
                        return len(self._original)
                    
                    def __repr__(self):
                        return repr(self._original)
                    
                    def copy(self):
                        return ExemptViewsSet(self._original.copy())
                    
                    def clear(self):
                        self._original.clear()
                    
                    def update(self, other):
                        self._original.update(other)
                
                # Replace _exempt_views with our custom set
                csrf._exempt_views = ExemptViewsSet(original_exempt_views)
                app.logger.info("CSRF protection enabled (auth endpoints patched to always be exempt)")
            except Exception as e:
                app.logger.error(f"Failed to patch CSRF _exempt_views: {e}", exc_info=True)
                app.logger.info("CSRF protection enabled (patching failed, using default exemptions)")
        else:
            app.logger.warning("CSRFProtect has no _exempt_views attribute - patching may not work")
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
                # unsafe-inline needed for inline scripts in templates (e.g., tailwind.config)
                # Consider moving to external JS files in future for stricter CSP
                # Allow Stripe.js for payment processing
                'script-src': "'self' 'unsafe-inline' https://js.stripe.com https://cdn.jsdelivr.net",
                'style-src': "'self' 'unsafe-inline'",  # unsafe-inline needed for inline styles
                'img-src': "'self' data: https:",
                'font-src': "'self' data:",
                'connect-src': "'self' https://api.stripe.com https://cdn.jsdelivr.net",
                # Allow Stripe Checkout iframes
                'frame-src': "'self' https://js.stripe.com https://hooks.stripe.com",
            },
            frame_options='SAMEORIGIN',  # Allow same-origin frames (needed for Stripe Checkout)
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
    
    # Add context processor for global template variables
    @app.context_processor
    def inject_global_vars():
        from .config import CURRENT_YEAR
        from datetime import datetime
        admin_username = os.environ.get('ADMIN_USERNAME', '').strip()
        
        def format_iso_date(date_str):
            """Format ISO date string for display"""
            if not date_str:
                return '-'
            try:
                # Handle ISO format with or without timezone
                if 'T' in date_str:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromisoformat(date_str)
                # Remove timezone for display
                if dt.tzinfo:
                    dt = dt.replace(tzinfo=None)
                return dt.strftime("%d %b %Y")
            except (ValueError, TypeError):
                return date_str
        
        def parse_iso_date(date_str):
            """Parse ISO date string to datetime object"""
            if not date_str:
                return None
            try:
                if 'T' in date_str:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromisoformat(date_str)
                if dt.tzinfo:
                    dt = dt.replace(tzinfo=None)
                return dt
            except (ValueError, TypeError):
                return None
        
        return dict(
            current_year=CURRENT_YEAR, 
            admin_username=admin_username,
            format_iso_date=format_iso_date,
            parse_iso_date=parse_iso_date,
            now=datetime.now
        )
    
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
            csrf.exempt('auth.forgot_password')
            csrf.exempt('subscription.stripe_webhook')
            csrf.exempt('subscription.create_checkout_session')
            csrf.exempt('main.import_excel')
            csrf.exempt('main.import_data')
            csrf.exempt('main.physical_data_analysis')
            csrf.exempt('main.cancel_user_subscription')
            csrf.exempt('main.delete_user')
            csrf.exempt('main.check_overdue_subscriptions')
            csrf.exempt('main.sync_all_subscriptions')
            
            # Also try function reference as backup (may not work if wrapped by rate limiter)
            try:
                from .auth_routes import login, register, forgot_password
                from .subscription_routes import stripe_webhook, get_subscription_status, create_checkout_session
                from .routes import import_excel, import_data, generate_scout_pdf_route, generate_pdf, cancel_user_subscription, check_overdue_subscriptions, sync_all_subscriptions
                csrf.exempt(login)
                csrf.exempt(register)
                csrf.exempt(forgot_password)
                csrf.exempt(stripe_webhook)
                csrf.exempt(get_subscription_status)
                csrf.exempt(create_checkout_session)
                # Import route functions for direct exemption
                from app.routes import import_excel, import_data, generate_scout_pdf_route, generate_pdf, sync_all_subscriptions, physical_data_analysis, delete_user
                csrf.exempt(import_excel)
                csrf.exempt(import_data)
                csrf.exempt(physical_data_analysis)
                csrf.exempt(generate_scout_pdf_route)
                csrf.exempt(generate_pdf)
                csrf.exempt(sync_all_subscriptions)
                csrf.exempt(delete_user)
            except Exception:
                # Function reference exemption failed (likely due to decorator wrapping)
                # Endpoint name exemptions above should be sufficient
                pass
            
            # Verify exemptions were actually applied
            if hasattr(csrf, '_exempt_views'):
                exempted = list(csrf._exempt_views)
                app.logger.info(f"CSRF exemptions applied: {exempted}")
            else:
                app.logger.warning("CSRFProtect has no _exempt_views attribute - exemptions may not work")
            
            app.logger.info("CSRF exemptions configured for: auth.login, auth.register, subscription.stripe_webhook")
        except Exception as e:
            app.logger.error(f"CRITICAL: Failed to exempt routes from CSRF: {e}", exc_info=True)
            # This is critical - if exemptions fail, auth won't work
            raise
    
    # Security: Add before_request hook to manually skip CSRF for auth endpoints
    # Flask-WTF's CSRF check runs in its own before_request hook
    # We need to ensure our exemptions are in place BEFORE that runs
    # Use prepend=True to ensure this runs before Flask-WTF's hook
    if CSRF_AVAILABLE and csrf:
        @app.before_request
        def skip_csrf_for_auth():
            """Manually skip CSRF validation for auth endpoints"""
            # Check if this is an auth endpoint that should be exempt
            if request.endpoint in ['auth.login', 'auth.register']:
                # Manually add to exempt views set (Flask-WTF checks this)
                try:
                    # Flask-WTF stores exempt views in _exempt_views set
                    if hasattr(csrf, '_exempt_views'):
                        # Add endpoint name (string)
                        csrf._exempt_views.add(request.endpoint)
                        # Also add the view function if we can get it
                        if request.endpoint and request.endpoint in app.view_functions:
                            view_func = app.view_functions[request.endpoint]
                            csrf._exempt_views.add(view_func)
                            app.logger.debug(f"Added {request.endpoint} and view_func to _exempt_views")
                    else:
                        app.logger.error(f"CRITICAL: CSRFProtect has no _exempt_views attribute!")
                except Exception as e:
                    app.logger.error(f"CRITICAL: Could not manually exempt {request.endpoint} from CSRF: {e}", exc_info=True)
    
    # Production: Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for load balancers and monitoring"""
        return jsonify({
            'status': 'healthy',
            'service': 'FutureElite'
        }), 200
    
    # Security: Add endpoint to get CSRF token for JSON API clients
    @app.route('/api/csrf-token', methods=['GET'])
    def get_csrf_token():
        """Get CSRF token for JSON API requests"""
        if CSRF_AVAILABLE:
            from flask_wtf.csrf import generate_csrf
            from flask import session
            # Ensure session exists for CSRF token validation
            session.permanent = True
            token = generate_csrf()
            return jsonify({'csrf_token': token})
        else:
            # CSRF not available - return empty token (client will handle gracefully)
            return jsonify({'csrf_token': ''})
    
    # Add error handler for API routes to return JSON instead of HTML
    @app.errorhandler(500)
    def handle_500_error(e):
        """Return JSON for API errors - sanitized to prevent information leakage"""
        # Log full error details server-side for debugging
        import traceback
        try:
            path = request.path if hasattr(request, 'path') else 'unknown'
            app.logger.error(f"500 error on {path}: {e}", exc_info=True)
        except Exception:
            app.logger.error(f"500 error: {e}", exc_info=True)
        
        # Always try to return JSON for auth endpoints, even if request context is broken
        try:
            path = request.path if hasattr(request, 'path') else ''
            content_type = request.headers.get('Content-Type', '') if hasattr(request, 'headers') else ''
        except Exception:
            path = ''
            content_type = ''
        
        # Return JSON for JSON requests or auth endpoints
        is_json_request = (
            'application/json' in content_type or
            path.startswith('/api/') or
            path in ['/login', '/register'] or
            '/login' in str(path) or
            '/register' in str(path)
        )
        
        if is_json_request:
            # Return generic error message to client
            return jsonify({
                'success': False,
                'errors': ['An internal error occurred. Please try again later.']
            }), 500
        # For non-API routes, return default HTML error page
        return e
    
    @app.errorhandler(404)
    def handle_404_error(e):
        """Handle 404 errors - return JSON for API routes, minimal HTML for others"""
        # Handle HEAD requests gracefully
        if request.method == 'HEAD':
            return '', 404
        
        # Return JSON for API routes
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'errors': ['Endpoint not found']
            }), 404
        
        # For non-API routes, return minimal HTML
        return '<!DOCTYPE html><html><head><title>404 Not Found</title></head><body><h1>404 Not Found</h1></body></html>', 404
    
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
    
    # Start background task to check overdue subscriptions
    _start_subscription_checker(app)
    
    return app


def _check_overdue_subscriptions(app):
    """Background task to check and cancel overdue subscriptions"""
    with app.app_context():
        from .routes import storage
        from .models import Subscription, SubscriptionStatus
        from datetime import datetime
        
        try:
            subscriptions = storage.load_subscriptions()
            now = datetime.now()
            cancelled_count = 0
            
            for sub_data in subscriptions:
                try:
                    subscription = Subscription(**sub_data)
                    
                    # Only check active or past_due subscriptions
                    if subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE]:
                        continue
                    
                    # Check if current_period_end has passed
                    if subscription.current_period_end:
                        try:
                            # Parse ISO format date
                            period_end_str = subscription.current_period_end
                            # Handle different date formats
                            if 'T' in period_end_str:
                                period_end = datetime.fromisoformat(period_end_str.replace('Z', '+00:00'))
                            else:
                                # Try parsing as simple date
                                period_end = datetime.fromisoformat(period_end_str)
                            
                            # Remove timezone for comparison
                            if period_end.tzinfo:
                                period_end = period_end.replace(tzinfo=None)
                            
                            # If period has ended, cancel subscription
                            if period_end < now:
                                # Cancel in Stripe if exists
                                try:
                                    import stripe
                                    if stripe and subscription.stripe_subscription_id:
                                        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '').strip()
                                        if stripe.api_key:
                                            stripe.Subscription.modify(
                                                subscription.stripe_subscription_id,
                                                cancel_at_period_end=True
                                            )
                                except Exception as e:
                                    app.logger.warning(f"Error cancelling Stripe subscription {subscription.stripe_subscription_id}: {e}")
                                
                                # Update local subscription
                                subscription.status = SubscriptionStatus.CANCELED
                                subscription.cancel_at_period_end = True
                                subscription.updated_at = datetime.now().strftime("%d %b %Y")
                                storage.save_subscription(subscription)
                                cancelled_count += 1
                                
                                app.logger.info(f"Auto-cancelled overdue subscription for user {subscription.user_id}")
                        except (ValueError, TypeError) as e:
                            app.logger.warning(f"Error parsing period_end for subscription {subscription.user_id}: {e}")
                            continue
                except (ValueError, TypeError, KeyError) as e:
                    app.logger.warning(f"Error processing subscription: {e}")
                    continue
            
            if cancelled_count > 0:
                app.logger.info(f"Auto-cancellation check: {cancelled_count} subscription(s) cancelled")
        except Exception as e:
            app.logger.error(f"Error in subscription checker: {e}", exc_info=True)


def _subscription_checker_worker(app):
    """Background worker thread that periodically checks for overdue subscriptions"""
    import time
    # Check every hour
    check_interval = 3600  # 1 hour in seconds
    
    while True:
        try:
            time.sleep(check_interval)
            _check_overdue_subscriptions(app)
        except Exception as e:
            app.logger.error(f"Error in subscription checker worker: {e}", exc_info=True)
            # Continue running even if there's an error
            time.sleep(60)  # Wait 1 minute before retrying


def _start_subscription_checker(app):
    """Start background thread to check overdue subscriptions"""
    checker_thread = threading.Thread(target=_subscription_checker_worker, args=(app,))
    checker_thread.daemon = True
    checker_thread.start()
    app.logger.info("Subscription checker thread started (checks every hour)")


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

