#!/usr/bin/env python3
"""
Simple test script to verify FutureElite Tracker functionality
"""

import sys
import os
import tempfile
import json

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.storage import StorageManager
from app.models import Match, MatchCategory, MatchResult, AppSettings
from app.pdf import generate_season_pdf
from app.utils import validate_match_data

def test_storage():
    """Test storage functionality"""
    print("Testing storage functionality...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = StorageManager(data_dir=temp_dir)
        
        # Test saving a match
        match = Match(
            category=MatchCategory.PRE_SEASON_FRIENDLY,
            date="23 Oct 2025",
            opponent="Test Team",
            location="Test Stadium",
            result=MatchResult.WIN,
            score="2 - 1",
            brodie_goals=1,
            brodie_assists=0,
            minutes_played=30,
            notes="Test match"
        )
        
        match_id = storage.save_match(match)
        print(f"✓ Match saved with ID: {match_id}")
        
        # Test loading the match
        loaded_match = storage.get_match(match_id)
        assert loaded_match is not None
        assert loaded_match.opponent == "Test Team"
        print("✓ Match loaded successfully")
        
        # Test season stats
        stats = storage.get_season_stats()
        assert stats['total_matches'] == 1
        assert stats['wins'] == 1
        assert stats['goals'] == 1
        print("✓ Season stats calculated correctly")
        
        print("✓ Storage tests passed!")

def test_validation():
    """Test validation functionality"""
    print("\nTesting validation functionality...")
    
    # Test valid data
    valid_data = {
        'date': '23 Oct 2025',
        'opponent': 'Test Team',
        'location': 'Test Stadium',
        'category': 'Pre-Season Friendly',
        'brodie_goals': '1',
        'brodie_assists': '0',
        'minutes_played': '30',
        'score': '2 - 1'
    }
    
    errors = validate_match_data(valid_data)
    assert len(errors) == 0
    print("✓ Valid data validation passed")
    
    # Test invalid data
    invalid_data = {
        'date': '',
        'opponent': '',
        'location': '',
        'category': ''
    }
    
    errors = validate_match_data(invalid_data)
    assert len(errors) > 0
    print("✓ Invalid data validation caught errors")
    
    print("✓ Validation tests passed!")

def test_pdf_generation():
    """Test PDF generation"""
    print("\nTesting PDF generation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test matches
        matches = [
            Match(
                category=MatchCategory.PRE_SEASON_FRIENDLY,
                date="23 Oct 2025",
                opponent="Test Team 1",
                location="Test Stadium 1",
                result=MatchResult.WIN,
                score="2 - 1",
                brodie_goals=1,
                brodie_assists=0,
                minutes_played=30,
                notes="Test match 1"
            ),
            Match(
                category=MatchCategory.LEAGUE,
                date="24 Oct 2025",
                opponent="Test Team 2",
                location="Test Stadium 2",
                result=MatchResult.LOSS,
                score="1 - 2",
                brodie_goals=0,
                brodie_assists=1,
                minutes_played=45,
                notes="Test match 2"
            )
        ]
        
        settings = AppSettings()
        
        # Generate PDF
        pdf_path = generate_season_pdf(matches, settings, temp_dir)
        
        # Check that file was created
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 0
        print(f"✓ PDF generated successfully: {os.path.basename(pdf_path)}")
        
        print("✓ PDF generation tests passed!")

def main():
    """Run all tests"""
    print("FutureElite Tracker - Functionality Test")
    print("=" * 50)
    
    try:
        test_storage()
        test_validation()
        test_pdf_generation()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! FutureElite Tracker is working correctly.")
        print("\nTo run the application:")
        print("  python run.py")
        print("\nTo build executables:")
        print("  Windows: .\\build_windows.ps1")
        print("  macOS:   ./build_macos.sh")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())








