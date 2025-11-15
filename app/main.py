from flask import Flask, render_template, request, jsonify, send_file
import os
import webbrowser
import threading
import time
from pathlib import Path

from .routes import bp
from .storage import StorageManager
from .models import Match, MatchCategory, MatchResult, AppSettings
from .utils import parse_input_date


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    # SECRET_KEY should be set via environment variable in production
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'futureelite-tracker-2025-dev-only')
    app.config['JSON_AS_ASCII'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Register blueprint
    app.register_blueprint(bp)
    
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
    webbrowser.open('http://127.0.0.1:5000')


def main():
    """Main entry point"""
    app = create_app()
    
    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("FutureElite Tracker starting...")
    print("Opening browser at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the application")
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down FutureElite Tracker...")


if __name__ == '__main__':
    main()

