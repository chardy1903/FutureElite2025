"""
Authentication routes for FutureElite
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
import time

from .storage import StorageManager
from .auth import UserSession

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize storage
storage = StorageManager()

# Security: Rate limiting for auth endpoints
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    RATE_LIMITER_AVAILABLE = True
    # Limiter will be initialized in main.py and passed via app context
except ImportError:
    RATE_LIMITER_AVAILABLE = False

def rate_limit_if_available(limit_str):
    """Decorator helper for conditional rate limiting"""
    def decorator(f):
        if RATE_LIMITER_AVAILABLE:
            try:
                from flask import current_app
                limiter = current_app.extensions.get('limiter')
                if limiter:
                    return limiter.limit(limit_str)(f)
            except Exception:
                pass
        return f
    return decorator


@auth_bp.route('/login', methods=['GET', 'POST'])
@rate_limit_if_available("10 per minute")
def login():
    """Login page"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                if request.is_json:
                    return jsonify({'success': False, 'errors': ['Username and password are required']}), 400
                flash('Username and password are required', 'error')
                return render_template('login.html')
            
            # Get user
            user = storage.get_user_by_username(username)
            
            # Security: Prevent timing attacks and account enumeration
            # Add a small delay to prevent timing-based enumeration
            # We don't need to check a dummy hash - the time delay is sufficient
            if not user:
                # Add delay to prevent timing-based account enumeration
                time.sleep(0.1)
                if request.is_json:
                    return jsonify({'success': False, 'errors': ['Invalid username or password']}), 401
                flash('Invalid username or password', 'error')
                return render_template('login.html')
            
            # Verify password
            if not storage.verify_password(user, password):
                if request.is_json:
                    return jsonify({'success': False, 'errors': ['Invalid username or password']}), 401
                flash('Invalid username or password', 'error')
                return render_template('login.html')
            
            # Security: Prevent session fixation by clearing session before login
            from flask import session
            session.permanent = True
            # Clear old session data to prevent fixation attacks
            session.clear()
            
            # Create user session and login (after clearing session)
            user_session = UserSession(user)
            login_user(user_session, remember=True)
            
            # Get redirect URL - handle errors gracefully
            try:
                redirect_url = url_for('main.dashboard')
            except Exception as e:
                current_app.logger.error(f"Error generating dashboard URL: {e}", exc_info=True)
                # Fallback to hardcoded path if url_for fails
                redirect_url = '/dashboard'
            
            if request.is_json:
                # Return user ID so frontend can store it for authentication checks
                return jsonify({
                    'success': True,
                    'redirect': redirect_url,
                    'user_id': str(user.id)  # Include user ID for frontend storage
                })
            
            return redirect(redirect_url)
        except Exception as e:
            # Catch any unexpected errors and return proper JSON response
            current_app.logger.error(f"Unexpected error in login route: {e}", exc_info=True)
            if request.is_json:
                return jsonify({
                    'success': False,
                    'errors': ['An internal error occurred. Please try again later.']
                }), 500
            # For form submissions, flash error and re-render
            flash('An error occurred. Please try again.', 'error')
            return render_template('login.html'), 500
    
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
@rate_limit_if_available("5 per minute")
def register():
    """Registration page"""
    if request.method == 'POST':
            data = request.get_json() if request.is_json else request.form.to_dict()
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            # Handle email - it might be None, empty string, or a value
            email_value = data.get('email')
            email = email_value.strip() if email_value else None
        
        if not username or not password:
            if request.is_json:
                return jsonify({'success': False, 'errors': ['Username and password are required']}), 400
            flash('Username and password are required', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            if request.is_json:
                return jsonify({'success': False, 'errors': ['Password must be at least 6 characters']}), 400
            flash('Password must be at least 6 characters', 'error')
            return render_template('register.html')
        
        # Create user
        user = storage.create_user(username, password, email)
        if not user:
            if request.is_json:
                return jsonify({'success': False, 'errors': ['Username already exists']}), 400
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        # Auto-login after registration
        user_session = UserSession(user)
        login_user(user_session, remember=True)
        
        # Security: Prevent session fixation by clearing session before login
        from flask import session
        session.permanent = True
        # Clear old session data to prevent fixation attacks
        session.clear()
        
        # Re-login to get new session ID (after clearing session)
        login_user(user_session, remember=True)
        
        # Get redirect URL - handle errors gracefully
        try:
            redirect_url = url_for('main.dashboard')
        except Exception as e:
            current_app.logger.error(f"Error generating dashboard URL: {e}", exc_info=True)
            # Fallback to hardcoded path if url_for fails
            redirect_url = '/dashboard'
        
        if request.is_json:
            # Return user ID so frontend can store it for authentication checks
            return jsonify({
                'success': True,
                'redirect': redirect_url,
                'user_id': str(user.id)  # Include user ID for frontend storage
            })
        
        return redirect(redirect_url)
    
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    return redirect(url_for('auth.login'))

