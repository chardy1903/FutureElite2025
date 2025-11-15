import unittest
import tempfile
import os
import json
from datetime import datetime

# Add the app directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.storage import StorageManager
from app.models import Match, MatchCategory, MatchResult, AppSettings


class TestStorageManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = StorageManager(data_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialize_files(self):
        """Test that files are initialized on first run"""
        # Check that files exist
        self.assertTrue(os.path.exists(self.storage.matches_file))
        self.assertTrue(os.path.exists(self.storage.settings_file))
        
        # Check that matches file contains empty list
        with open(self.storage.matches_file, 'r') as f:
            matches = json.load(f)
        self.assertEqual(matches, [])
        
        # Check that settings file contains default settings
        with open(self.storage.settings_file, 'r') as f:
            settings_data = json.load(f)
        self.assertIn('club_name', settings_data)
        self.assertEqual(settings_data['club_name'], 'Al Qadsiah U12')
    
    def test_save_and_load_match(self):
        """Test saving and loading a match"""
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
        
        # Save match
        match_id = self.storage.save_match(match)
        self.assertIsNotNone(match_id)
        
        # Load match
        loaded_match = self.storage.get_match(match_id)
        self.assertIsNotNone(loaded_match)
        self.assertEqual(loaded_match.opponent, "Test Team")
        self.assertEqual(loaded_match.brodie_goals, 1)
    
    def test_get_all_matches(self):
        """Test getting all matches"""
        # Add multiple matches with unique IDs
        import time
        match1 = Match(
            id=f"test_{int(time.time() * 1000000)}_1",
            category=MatchCategory.PRE_SEASON_FRIENDLY,
            date="23 Oct 2025",
            opponent="Team 1",
            location="Stadium 1",
            result=MatchResult.WIN,
            score="2 - 1",
            brodie_goals=1,
            brodie_assists=0,
            minutes_played=30,
            notes="Match 1"
        )
        
        match2 = Match(
            id=f"test_{int(time.time() * 1000000)}_2",
            category=MatchCategory.LEAGUE,
            date="24 Oct 2025",
            opponent="Team 2",
            location="Stadium 2",
            result=MatchResult.LOSS,
            score="1 - 2",
            brodie_goals=0,
            brodie_assists=1,
            minutes_played=45,
            notes="Match 2"
        )
        
        self.storage.save_match(match1)
        self.storage.save_match(match2)
        
        # Get all matches
        all_matches = self.storage.get_all_matches()
        self.assertEqual(len(all_matches), 2)
    
    def test_get_matches_by_category(self):
        """Test filtering matches by category"""
        # Add matches of different categories with unique IDs
        import time
        match1 = Match(
            id=f"test_{int(time.time() * 1000000)}_1",
            category=MatchCategory.PRE_SEASON_FRIENDLY,
            date="23 Oct 2025",
            opponent="Team 1",
            location="Stadium 1",
            result=MatchResult.WIN,
            score="2 - 1",
            brodie_goals=1,
            brodie_assists=0,
            minutes_played=30,
            notes="Pre-season match"
        )
        
        match2 = Match(
            id=f"test_{int(time.time() * 1000000)}_2",
            category=MatchCategory.LEAGUE,
            date="24 Oct 2025",
            opponent="Team 2",
            location="Stadium 2",
            result=MatchResult.LOSS,
            score="1 - 2",
            brodie_goals=0,
            brodie_assists=1,
            minutes_played=45,
            notes="League match"
        )
        
        self.storage.save_match(match1)
        self.storage.save_match(match2)
        
        # Get pre-season matches
        pre_season_matches = self.storage.get_matches_by_category("Pre-Season Friendly")
        self.assertEqual(len(pre_season_matches), 1)
        self.assertEqual(pre_season_matches[0].opponent, "Team 1")
        
        # Get league matches
        league_matches = self.storage.get_matches_by_category("League")
        self.assertEqual(len(league_matches), 1)
        self.assertEqual(league_matches[0].opponent, "Team 2")
    
    def test_delete_match(self):
        """Test deleting a match"""
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
        
        # Save match
        match_id = self.storage.save_match(match)
        
        # Verify match exists
        self.assertIsNotNone(self.storage.get_match(match_id))
        
        # Delete match
        success = self.storage.delete_match(match_id)
        self.assertTrue(success)
        
        # Verify match is deleted
        self.assertIsNone(self.storage.get_match(match_id))
    
    def test_season_stats(self):
        """Test calculating season statistics"""
        # Add matches with different results and unique IDs
        import time
        match1 = Match(
            id=f"test_{int(time.time() * 1000000)}_1",
            category=MatchCategory.PRE_SEASON_FRIENDLY,
            date="23 Oct 2025",
            opponent="Team 1",
            location="Stadium 1",
            result=MatchResult.WIN,
            score="2 - 1",
            brodie_goals=2,
            brodie_assists=1,
            minutes_played=30,
            notes="Win"
        )
        
        match2 = Match(
            id=f"test_{int(time.time() * 1000000)}_2",
            category=MatchCategory.LEAGUE,
            date="24 Oct 2025",
            opponent="Team 2",
            location="Stadium 2",
            result=MatchResult.LOSS,
            score="1 - 2",
            brodie_goals=1,
            brodie_assists=0,
            minutes_played=45,
            notes="Loss"
        )
        
        self.storage.save_match(match1)
        self.storage.save_match(match2)
        
        # Get season stats
        stats = self.storage.get_season_stats()
        self.assertEqual(stats['total_matches'], 2)
        self.assertEqual(stats['wins'], 1)
        self.assertEqual(stats['losses'], 1)
        self.assertEqual(stats['goals'], 3)
        self.assertEqual(stats['assists'], 1)
        self.assertEqual(stats['minutes'], 75)
    
    def test_export_import_data(self):
        """Test exporting and importing data"""
        # Add a match
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
        self.storage.save_match(match)
        
        # Export data
        export_data = self.storage.export_data()
        self.assertIn('matches', export_data)
        self.assertIn('settings', export_data)
        self.assertEqual(len(export_data['matches']), 1)
        
        # Create new storage instance and import data
        new_storage = StorageManager(data_dir=tempfile.mkdtemp())
        success = new_storage.import_data(export_data)
        self.assertTrue(success)
        
        # Verify data was imported
        imported_matches = new_storage.get_all_matches()
        self.assertEqual(len(imported_matches), 1)
        self.assertEqual(imported_matches[0].opponent, "Test Team")


if __name__ == '__main__':
    unittest.main()
