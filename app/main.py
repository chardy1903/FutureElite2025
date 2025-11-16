"""
FutureElite - Flask Application

Copyright (c) 2025 [Your Name]. All Rights Reserved.
This software is proprietary and confidential. Unauthorized copying, modification,
distribution, or use of this software, via any medium, is strictly prohibited.
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_login import LoginManager
import os
import webbrowser
import threading
import time
from pathlib import Path

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


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    # SECRET_KEY should be set via environment variable in production
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'futureelite-2025-dev-only')
    app.config['JSON_AS_ASCII'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
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
    
    # Register blueprints
    app.register_blueprint(bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(subscription_bp)
    
    # Add error handler for API routes to return JSON instead of HTML
    @app.errorhandler(500)
    def handle_500_error(e):
        """Return JSON for API errors"""
        if request.path.startswith('/api/'):
            import traceback
            error_details = str(e)
            # Try to get more details from the exception
            if hasattr(e, 'original_exception'):
                error_details = str(e.original_exception)
            return jsonify({
                'success': False,
                'errors': [f'Internal server error: {error_details}']
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
    """Main entry point"""
    app = create_app()
    
    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("FutureElite starting...")
    print("Opening browser at http://127.0.0.1:8080")
    print("Press Ctrl+C to stop the application")
    
    try:
        # Use port 8080 to avoid conflict with AirPlay Receiver
        app.run(host='127.0.0.1', port=8080, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down FutureElite...")


if __name__ == '__main__':
    main()

