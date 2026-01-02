"""
FutureElite PDF Report Generation System

This module provides three distinct PDF reports:
1. Season Tracker - detailed match-by-match log for the current season
2. Scout Report - one to two pages maximum, fastest possible scout-read, high signal only
3. Player Resume - comprehensive career document, multi-page allowed
"""

from .types import Player, Match
from .adapters import build_player_from_data
from .generators import (
    generate_all_reports,
    generate_season_tracker_from_data,
    generate_scout_report_from_data,
    generate_player_resume_from_data
)

__all__ = [
    'Player',
    'Match',
    'build_player_from_data',
    'generate_all_reports',
    'generate_season_tracker_from_data',
    'generate_scout_report_from_data',
    'generate_player_resume_from_data',
]

