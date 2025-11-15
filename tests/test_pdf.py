import unittest
import tempfile
import os
from datetime import datetime

# Add the app directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.pdf import PDFGenerator, generate_season_pdf
from app.models import Match, MatchCategory, MatchResult, AppSettings


class TestPDFGenerator(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.settings = AppSettings()
        self.generator = PDFGenerator(self.settings)
        
        # Create test matches
        self.test_matches = [
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
                category=MatchCategory.PRE_SEASON_FRIENDLY,
                date="24 Oct 2025",
                opponent="Test Team 2",
                location="Test Stadium 2",
                result=MatchResult.LOSS,
                score="1 - 2",
                brodie_goals=0,
                brodie_assists=1,
                minutes_played=45,
                notes="Test match 2"
            ),
            Match(
                category=MatchCategory.LEAGUE,
                date="25 Oct 2025",
                opponent="League Team",
                location="League Stadium",
                result=MatchResult.WIN,
                score="3 - 1",
                brodie_goals=2,
                brodie_assists=1,
                minutes_played=60,
                notes="League match"
            )
        ]
    
    def test_pdf_generator_initialization(self):
        """Test PDF generator initialization"""
        self.assertIsNotNone(self.generator)
        self.assertEqual(self.generator.settings.club_name, "Al Qadsiah U12")
        self.assertEqual(self.generator.settings.player_name, "Brodie Hardy")
    
    def test_generate_pdf(self):
        """Test PDF generation (smoke test)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output.pdf")
            
            # Generate PDF
            result_path = self.generator.generate_pdf(self.test_matches, output_path)
            
            # Check that file was created
            self.assertTrue(os.path.exists(result_path))
            self.assertEqual(result_path, output_path)
            
            # Check that file is not empty
            file_size = os.path.getsize(result_path)
            self.assertGreater(file_size, 0)
    
    def test_generate_season_pdf_function(self):
        """Test the generate_season_pdf function"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate PDF using the function
            result_path = generate_season_pdf(self.test_matches, self.settings, temp_dir)
            
            # Check that file was created
            self.assertTrue(os.path.exists(result_path))
            
            # Check that file is not empty
            file_size = os.path.getsize(result_path)
            self.assertGreater(file_size, 0)
            
            # Check filename format
            filename = os.path.basename(result_path)
            self.assertTrue(filename.startswith("Al_Qadsiah_U12_Brodie_Hardy_Season_Tracker"))
            self.assertTrue(filename.endswith(".pdf"))
    
    def test_pdf_with_empty_matches(self):
        """Test PDF generation with empty match list"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "empty_test.pdf")
            
            # Generate PDF with empty matches
            result_path = self.generator.generate_pdf([], output_path)
            
            # Check that file was created
            self.assertTrue(os.path.exists(result_path))
            
            # Check that file is not empty (should still have headers and structure)
            file_size = os.path.getsize(result_path)
            self.assertGreater(file_size, 0)
    
    def test_pdf_with_fixtures(self):
        """Test PDF generation with fixtures (upcoming matches)"""
        # Add a fixture
        fixture = Match(
            category=MatchCategory.PRE_SEASON_FRIENDLY,
            date="26 Oct 2025",
            opponent="Future Team",
            location="Future Stadium",
            is_fixture=True
        )
        
        matches_with_fixture = self.test_matches + [fixture]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "fixture_test.pdf")
            
            # Generate PDF
            result_path = self.generator.generate_pdf(matches_with_fixture, output_path)
            
            # Check that file was created
            self.assertTrue(os.path.exists(result_path))
            
            # Check that file is not empty
            file_size = os.path.getsize(result_path)
            self.assertGreater(file_size, 0)
    
    def test_calculate_category_stats(self):
        """Test category statistics calculation"""
        # Test pre-season stats
        pre_season_matches = [m for m in self.test_matches if m.category == MatchCategory.PRE_SEASON_FRIENDLY]
        stats = self.generator._calculate_category_stats(pre_season_matches)
        
        self.assertEqual(stats['matches'], 2)
        self.assertEqual(stats['goals'], 1)  # 1 + 0
        self.assertEqual(stats['assists'], 1)  # 0 + 1
        self.assertEqual(stats['minutes'], 75)  # 30 + 45
        
        # Test league stats
        league_matches = [m for m in self.test_matches if m.category == MatchCategory.LEAGUE]
        stats = self.generator._calculate_category_stats(league_matches)
        
        self.assertEqual(stats['matches'], 1)
        self.assertEqual(stats['goals'], 2)
        self.assertEqual(stats['assists'], 1)
        self.assertEqual(stats['minutes'], 60)


if __name__ == '__main__':
    unittest.main()
