from datetime import datetime
from typing import List, Dict, Any
import re


def format_date_for_display(date_str: str) -> str:
    """Format date string for display"""
    try:
        # Parse the date and reformat it
        dt = datetime.strptime(date_str, "%d %b %Y")
        return dt.strftime("%d %b %Y")
    except ValueError:
        return date_str


def format_date_for_input(date_str: str) -> str:
    """Format date string for HTML input (YYYY-MM-DD)"""
    try:
        dt = datetime.strptime(date_str, "%d %b %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return ""


def parse_input_date(date_input: str) -> str:
    """Parse HTML date input (YYYY-MM-DD) to our format (dd MMM yyyy)"""
    try:
        dt = datetime.strptime(date_input, "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except ValueError:
        return date_input


def validate_match_data(data: Dict[str, Any]) -> List[str]:
    """Validate match form data and return list of errors"""
    errors = []
    
    # Required fields
    if not data.get('date'):
        errors.append("Date is required")
    elif not data.get('date').strip():
        errors.append("Date cannot be empty")
    
    if not data.get('opponent'):
        errors.append("Opponent is required")
    elif not data.get('opponent').strip():
        errors.append("Opponent cannot be empty")
    
    if not data.get('location'):
        errors.append("Location is required")
    elif not data.get('location').strip():
        errors.append("Location cannot be empty")
    
    if not data.get('category'):
        errors.append("Category is required")
    
    # Validate date format if provided
    if data.get('date'):
        try:
            datetime.strptime(data['date'], "%d %b %Y")
        except ValueError:
            errors.append("Date must be in format 'dd MMM yyyy' (e.g., '23 Oct 2025')")
    
    # Validate numeric fields
    for field in ['brodie_goals', 'brodie_assists', 'minutes_played']:
        value = data.get(field, 0)
        try:
            int_val = int(value) if value else 0
            if int_val < 0:
                errors.append(f"{field.replace('_', ' ').title()} must be non-negative")
        except (ValueError, TypeError):
            errors.append(f"{field.replace('_', ' ').title()} must be a valid number")
    
    # Validate score format if provided
    if data.get('score') and data['score'].strip():
        score = data['score'].strip()
        if ' - ' not in score:
            errors.append("Score must be in format '7 - 5'")
        else:
            try:
                parts = score.split(' - ')
                if len(parts) != 2:
                    raise ValueError
                int(parts[0])
                int(parts[1])
            except (ValueError, IndexError):
                errors.append("Score must be in format '7 - 5'")
    
    return errors


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores and dots
    filename = filename.strip('_.')
    return filename


def generate_pdf_filename(settings: Any) -> str:
    """Generate PDF filename based on settings"""
    club_name = settings.club_name.replace(' ', '_')
    player_name = settings.player_name.replace(' ', '_')
    season = settings.season_year.replace('/', '_')
    # Include time for uniqueness so regenerations on same day don't overwrite
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filename = f"{club_name}_{player_name}_Season_Tracker_{season}_{date_str}.pdf"
    return sanitize_filename(filename)


def format_minutes_display(minutes: int) -> str:
    """Format minutes for display"""
    if minutes == 0:
        return "0"
    elif minutes < 60:
        return f"{minutes}m"
    else:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours}h"
        else:
            return f"{hours}h {remaining_minutes}m"


def get_match_number(matches: List[Any], category: str) -> int:
    """Get the next match number for a category"""
    category_matches = [m for m in matches if m.category.value == category and not m.is_fixture]
    return len(category_matches) + 1


def sort_matches_by_date(matches: List[Any]) -> List[Any]:
    """Sort matches by date"""
    def date_key(match):
        try:
            return datetime.strptime(match.date, "%d %b %Y")
        except ValueError:
            return datetime.min
    
    return sorted(matches, key=date_key)


def format_notes_for_display(notes: str) -> str:
    """Format notes for display, handling line breaks"""
    if not notes:
        return ""
    # Replace line breaks with HTML breaks for display
    return notes.replace('\n', '<br>')


def is_valid_emoji(text: str) -> bool:
    """Check if text contains valid emoji characters"""
    # Simple emoji detection - look for common emoji ranges
    emoji_pattern = re.compile(
        r'[\U0001F600-\U0001F64F]|'  # emoticons
        r'[\U0001F300-\U0001F5FF]|'  # symbols & pictographs
        r'[\U0001F680-\U0001F6FF]|'  # transport & map symbols
        r'[\U0001F1E0-\U0001F1FF]|'  # flags (iOS)
        r'[\U00002600-\U000026FF]|'  # miscellaneous symbols
        r'[\U00002700-\U000027BF]'   # dingbats
    )
    return bool(emoji_pattern.search(text))


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to max_length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def get_result_color(result: str) -> str:
    """Get color class for match result"""
    if result == "Win":
        return "text-green-600"
    elif result == "Draw":
        return "text-yellow-600"
    elif result == "Loss":
        return "text-red-600"
    else:
        return "text-gray-600"


def format_score_display(score: str) -> str:
    """Format score for display"""
    if not score:
        return "TBD"
    return score


def get_category_badge_color(category: str) -> str:
    """Get badge color for category"""
    if category == "Pre-Season Friendly":
        return "bg-blue-100 text-blue-800"
    elif category == "League":
        return "bg-green-100 text-green-800"
    else:
        return "bg-gray-100 text-gray-800"

