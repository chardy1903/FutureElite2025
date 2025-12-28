"""
Authentication routes for FutureElite
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import time

from .storage import StorageManager
from .auth import UserSession

# Security: Pre-generated dummy password hash for constant-time checking
# This prevents timing attacks by always performing a hash check
DUMMY_PASSWORD_HASH = generate_password_hash("dummy-password-for-timing-protection")

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
            
            # Security: Constant-time password checking to prevent timing attacks
            # Always perform a hash check, even if user doesn't exist
            password_hash_to_check = DUMMY_PASSWORD_HASH
            if user:
                # Use real user's password hash if user exists
                if not user.password_hash:
                    # Invalid user data - log but don't leak to client
                    current_app.logger.warning(f"User {username} has no password hash")
                    password_hash_to_check = DUMMY_PASSWORD_HASH
                else:
                    password_hash_to_check = user.password_hash
            
            # Perform constant-time password check
            try:
                password_valid = check_password_hash(password_hash_to_check, password)
            except ValueError as e:
                # Invalid hash format - log error and treat as auth failure
                current_app.logger.error(f"Password hash validation error for user {username}: {e}", exc_info=True)
                password_valid = False
            
            # Only succeed if user exists AND password is valid
            if not user or not password_valid:
                # Add small delay to prevent timing-based enumeration
                time.sleep(0.1)
                # Log auth failure (no sensitive data)
                if user:
                    current_app.logger.info(f"Failed login attempt for username: {username}")
                else:
                    current_app.logger.info(f"Failed login attempt for non-existent username: {username}")
                
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
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            # Handle email - it might be None, empty string, or a value
            email_value = data.get('email')
            email = email_value.strip().lower() if email_value and email_value.strip() else None
            
            # Validate inputs
            if not username or not password:
                if request.is_json:
                    return jsonify({'success': False, 'errors': ['Username and password are required']}), 400
                flash('Username and password are required', 'error')
                return render_template('register.html')
            
            if len(password) < 8:
                if request.is_json:
                    return jsonify({'success': False, 'errors': ['Password must be at least 8 characters']}), 400
                flash('Password must be at least 8 characters', 'error')
                return render_template('register.html')
            
            if len(username) < 3:
                if request.is_json:
                    return jsonify({'success': False, 'errors': ['Username must be at least 3 characters']}), 400
                flash('Username must be at least 3 characters', 'error')
                return render_template('register.html')
            
            # Check if username already exists (before attempting creation)
            existing_user = storage.get_user_by_username(username)
            if existing_user:
                if request.is_json:
                    return jsonify({'success': False, 'errors': ['Username already exists']}), 409
                flash('Username already exists', 'error')
                return render_template('register.html')
            
            # Create user
            try:
                user = storage.create_user(username, password, email)
            except Exception as e:
                # Log the error but don't expose details to client
                current_app.logger.error(f"Error creating user {username}: {e}", exc_info=True)
                if request.is_json:
                    return jsonify({'success': False, 'errors': ['An error occurred during registration. Please try again.']}), 500
                flash('An error occurred during registration. Please try again.', 'error')
                return render_template('register.html'), 500
            
            if not user:
                # Should not happen if create_user worked, but handle gracefully
                if request.is_json:
                    return jsonify({'success': False, 'errors': ['Failed to create user. Please try again.']}), 500
                flash('Failed to create user. Please try again.', 'error')
                return render_template('register.html'), 500
            
            # Auto-login after registration
            try:
                user_session = UserSession(user)
                
                # Security: Prevent session fixation by clearing session before login
                from flask import session
                session.permanent = True
                # Clear old session data to prevent fixation attacks
                session.clear()
                
                # Login after clearing session
                login_user(user_session, remember=True)
            except Exception as e:
                current_app.logger.error(f"Error during auto-login for user {username}: {e}", exc_info=True)
                # User was created but login failed - still return success but log the issue
                if request.is_json:
                    return jsonify({
                        'success': True,
                        'redirect': '/login',
                        'user_id': str(user.id),
                        'message': 'Account created. Please log in.'
                    }), 200
                flash('Account created. Please log in.', 'success')
                return redirect(url_for('auth.login'))
            
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
            current_app.logger.error(f"Unexpected error in register route: {e}", exc_info=True)
            if request.is_json:
                return jsonify({
                    'success': False,
                    'errors': ['An internal error occurred. Please try again later.']
                }), 500
            # For form submissions, flash error and re-render
            flash('An error occurred. Please try again.', 'error')
            return render_template('register.html'), 500
    
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    return redirect(url_for('auth.login'))

