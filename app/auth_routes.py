"""
Authentication routes for FutureElite
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from .storage import StorageManager
from .auth import UserSession

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize storage
storage = StorageManager()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
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
        if not user:
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
        
        # Create user session and login
        user_session = UserSession(user)
        login_user(user_session, remember=True)
        
        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('main.homepage')})
        
        return redirect(url_for('main.homepage'))
    
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip() or None
        
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
        
        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('main.homepage')})
        
        return redirect(url_for('main.homepage'))
    
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    return redirect(url_for('auth.login'))

