import unittest
from datetime import datetime

# Add the app directory to the path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.utils import (
    format_date_for_display,
    format_date_for_input,
    parse_input_date,
    validate_match_data,
    sanitize_filename,
    format_minutes_display,
    get_result_color,
    get_category_badge_color,
    is_valid_emoji,
    truncate_text
)


class TestUtils(unittest.TestCase):
    def test_format_date_for_display(self):
        """Test date formatting for display"""
        # Valid date
        result = format_date_for_display("23 Oct 2025")
        self.assertEqual(result, "23 Oct 2025")
        
        # Invalid date (should return as-is)
        result = format_date_for_display("invalid date")
        self.assertEqual(result, "invalid date")
    
    def test_format_date_for_input(self):
        """Test date formatting for HTML input"""
        # Valid date
        result = format_date_for_input("23 Oct 2025")
        self.assertEqual(result, "2025-10-23")
        
        # Invalid date (should return empty string)
        result = format_date_for_input("invalid date")
        self.assertEqual(result, "")
    
    def test_parse_input_date(self):
        """Test parsing HTML date input"""
        # Valid date
        result = parse_input_date("2025-10-23")
        self.assertEqual(result, "23 Oct 2025")
        
        # Invalid date (should return as-is)
        result = parse_input_date("invalid date")
        self.assertEqual(result, "invalid date")
    
    def test_validate_match_data(self):
        """Test match data validation"""
        # Valid data
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
        self.assertEqual(len(errors), 0)
        
        # Missing required fields
        invalid_data = {
            'date': '',
            'opponent': '',
            'location': '',
            'category': ''
        }
        errors = validate_match_data(invalid_data)
        self.assertGreater(len(errors), 0)
        self.assertIn("Date is required", errors)
        self.assertIn("Opponent is required", errors)
        self.assertIn("Location is required", errors)
        self.assertIn("Category is required", errors)
        
        # Invalid date format
        invalid_date_data = {
            'date': '2025-10-23',  # Wrong format
            'opponent': 'Test Team',
            'location': 'Test Stadium',
            'category': 'Pre-Season Friendly'
        }
        errors = validate_match_data(invalid_date_data)
        self.assertIn("Date must be in format 'dd MMM yyyy' (e.g., '23 Oct 2025')", errors)
        
        # Invalid score format
        invalid_score_data = {
            'date': '23 Oct 2025',
            'opponent': 'Test Team',
            'location': 'Test Stadium',
            'category': 'Pre-Season Friendly',
            'score': '2-1'  # Missing spaces around dash
        }
        errors = validate_match_data(invalid_score_data)
        self.assertIn("Score must be in format '7 - 5'", errors)
        
        # Negative numeric values
        negative_data = {
            'date': '23 Oct 2025',
            'opponent': 'Test Team',
            'location': 'Test Stadium',
            'category': 'Pre-Season Friendly',
            'brodie_goals': '-1'
        }
        errors = validate_match_data(negative_data)
        self.assertIn("Brodie Goals must be non-negative", errors)
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Normal filename
        result = sanitize_filename("test_file.pdf")
        self.assertEqual(result, "test_file.pdf")
        
        # Filename with invalid characters
        result = sanitize_filename("test<file>.pdf")
        self.assertEqual(result, "test_file_.pdf")
        
        # Filename with multiple underscores
        result = sanitize_filename("test___file.pdf")
        self.assertEqual(result, "test_file.pdf")
        
        # Filename starting with dots
        result = sanitize_filename("...test.pdf")
        self.assertEqual(result, "test.pdf")
    
    def test_format_minutes_display(self):
        """Test minutes formatting for display"""
        # Zero minutes
        result = format_minutes_display(0)
        self.assertEqual(result, "0")
        
        # Less than 60 minutes
        result = format_minutes_display(30)
        self.assertEqual(result, "30m")
        
        # Exactly 60 minutes
        result = format_minutes_display(60)
        self.assertEqual(result, "1h")
        
        # More than 60 minutes
        result = format_minutes_display(90)
        self.assertEqual(result, "1h 30m")
        
        # Multiple hours
        result = format_minutes_display(150)
        self.assertEqual(result, "2h 30m")
    
    def test_get_result_color(self):
        """Test result color classes"""
        self.assertEqual(get_result_color("Win"), "text-green-600")
        self.assertEqual(get_result_color("Draw"), "text-yellow-600")
        self.assertEqual(get_result_color("Loss"), "text-red-600")
        self.assertEqual(get_result_color("Unknown"), "text-gray-600")
    
    def test_get_category_badge_color(self):
        """Test category badge color classes"""
        self.assertEqual(get_category_badge_color("Pre-Season Friendly"), "bg-blue-100 text-blue-800")
        self.assertEqual(get_category_badge_color("League"), "bg-green-100 text-green-800")
        self.assertEqual(get_category_badge_color("Unknown"), "bg-gray-100 text-gray-800")
    
    def test_is_valid_emoji(self):
        """Test emoji validation"""
        # Text with emoji
        self.assertTrue(is_valid_emoji("Hello 🌟 World"))
        self.assertTrue(is_valid_emoji("Team 🇧🇭"))
        self.assertTrue(is_valid_emoji("❤️💛"))
        
        # Text without emoji
        self.assertFalse(is_valid_emoji("Hello World"))
        self.assertFalse(is_valid_emoji("Team ABC"))
        self.assertFalse(is_valid_emoji(""))
    
    def test_truncate_text(self):
        """Test text truncation"""
        # Short text
        result = truncate_text("Short", 10)
        self.assertEqual(result, "Short")
        
        # Long text
        result = truncate_text("This is a very long text that should be truncated", 20)
        self.assertEqual(result, "This is a very lo...")
        
        # Empty text
        result = truncate_text("", 10)
        self.assertEqual(result, "")


if __name__ == '__main__':
    unittest.main()
