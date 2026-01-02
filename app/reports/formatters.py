"""
Formatting utilities for dates, numbers, and units.

All formatting must be consistent across reports.
"""

from datetime import datetime
from typing import Optional


def format_date_iso_to_display(iso_date: str) -> str:
    """
    Convert ISO date string (YYYY-MM-DD) to display format (DD MMM YYYY).
    
    Args:
        iso_date: ISO format date string (e.g., "2025-10-23")
        
    Returns:
        Formatted date string (e.g., "23 Oct 2025")
    """
    try:
        # Handle ISO format with or without time
        date_str = iso_date.split('T')[0]  # Remove time if present
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%d %b %Y")
    except (ValueError, AttributeError):
        # If parsing fails, try to return as-is or return "Invalid date"
        return iso_date if iso_date else "Not recorded"


def format_date_display_to_iso(display_date: str) -> str:
    """
    Convert display date (DD MMM YYYY) to ISO format (YYYY-MM-DD).
    
    Args:
        display_date: Display format date string (e.g., "23 Oct 2025")
        
    Returns:
        ISO format date string (e.g., "2025-10-23")
    """
    try:
        dt = datetime.strptime(display_date, "%d %b %Y")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return display_date


def format_per_60(value: float) -> str:
    """
    Format per-60 metric to 2 decimal places.
    
    Args:
        value: Per-60 metric value
        
    Returns:
        Formatted string with 2 decimals
    """
    return f"{value:.2f}"


def format_per_match(value: float) -> str:
    """
    Format per-match metric to 2 decimal places.
    
    Args:
        value: Per-match metric value
        
    Returns:
        Formatted string with 2 decimals
    """
    return f"{value:.2f}"


def format_minutes_per(value: Optional[int]) -> str:
    """
    Format minutes per goal/contribution to nearest whole minute.
    
    Args:
        value: Minutes per metric (or None for N/A)
        
    Returns:
        Formatted string or "N/A"
    """
    if value is None:
        return "N/A"
    return str(int(value))


def format_percentage(value: float) -> str:
    """
    Format percentage to 1 decimal place.
    
    Args:
        value: Percentage value (0-100)
        
    Returns:
        Formatted string with 1 decimal
    """
    return f"{value:.1f}%"


def format_height_cm(value: Optional[float]) -> str:
    """
    Format height in cm to 1 decimal place.
    
    Args:
        value: Height in centimeters
        
    Returns:
        Formatted string or "Not recorded"
    """
    if value is None:
        return "Not recorded"
    return f"{value:.1f} cm"


def format_weight_kg(value: Optional[float]) -> str:
    """
    Format weight in kg to 1 decimal place.
    
    Args:
        value: Weight in kilograms
        
    Returns:
        Formatted string or "Not recorded"
    """
    if value is None:
        return "Not recorded"
    return f"{value:.1f} kg"


def format_bmi(value: Optional[float]) -> str:
    """
    Format BMI to 1 decimal place.
    
    Args:
        value: BMI value
        
    Returns:
        Formatted string or "Not recorded"
    """
    if value is None:
        return "Not recorded"
    return f"{value:.1f}"


def format_predicted_height_cm(value: Optional[float]) -> str:
    """
    Format predicted adult height in cm and feet/inches.
    
    Args:
        value: Predicted height in centimeters
        
    Returns:
        Formatted string with cm and feet/inches, or "Not recorded"
    """
    if value is None:
        return "Not recorded"
    
    # Convert cm to feet and inches
    total_inches = value / 2.54
    feet = int(total_inches // 12)
    inches = int(total_inches % 12)
    
    return f"{value:.1f} cm ({feet}'{inches}\")"


def format_score(score_for: Optional[int], score_against: Optional[int]) -> str:
    """
    Format match score.
    
    Args:
        score_for: Goals scored by player's team
        score_against: Goals scored by opponent
        
    Returns:
        Formatted score string or "Not recorded"
    """
    if score_for is None or score_against is None:
        return "Not recorded"
    return f"{score_for} - {score_against}"


def truncate_text(text: Optional[str], max_length: int = 50) -> str:
    """
    Truncate text to max_length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def calculate_age(dob_iso: str, reference_date_iso: Optional[str] = None) -> Optional[float]:
    """
    Calculate age in years from date of birth.
    
    Args:
        dob_iso: Date of birth in ISO format
        reference_date_iso: Reference date in ISO format (defaults to today)
        
    Returns:
        Age in years as float, or None if calculation fails
    """
    try:
        dob = datetime.fromisoformat(dob_iso.split('T')[0])
        if reference_date_iso:
            ref_date = datetime.fromisoformat(reference_date_iso.split('T')[0])
        else:
            ref_date = datetime.now()
        
        age_delta = ref_date - dob
        age_years = age_delta.days / 365.25
        return round(age_years, 1)
    except (ValueError, AttributeError):
        return None


def get_report_generation_date() -> str:
    """
    Get current date formatted for report footer.
    
    Returns:
        Formatted date string (DD MMM YYYY)
    """
    return datetime.now().strftime("%d %b %Y")

