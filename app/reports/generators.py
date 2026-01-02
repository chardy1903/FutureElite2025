"""
Main entry point for generating all three report types.
"""

from typing import List, Optional
import os

from .types import Player
from .adapters import build_player_from_data
from .season_tracker import generate_season_tracker
from .scout_report import generate_scout_report
from .player_resume import generate_player_resume

from ..models import (
    Match as AppMatch,
    AppSettings,
    PhysicalMeasurement,
    Achievement,
    ClubHistory,
    TrainingCamp,
    PhysicalMetrics,
    Reference
)


def generate_all_reports(
    settings: AppSettings,
    matches: List[AppMatch],
    physical_measurements: Optional[List[PhysicalMeasurement]] = None,
    achievements: Optional[List[Achievement]] = None,
    club_history: Optional[List[ClubHistory]] = None,
    training_camps: Optional[List[TrainingCamp]] = None,
    physical_metrics: Optional[List[PhysicalMetrics]] = None,
    references: Optional[List[Reference]] = None,
    output_dir: str = "output"
) -> dict:
    """
    Generate all three PDF reports from app data models.
    
    Args:
        settings: AppSettings object
        matches: List of Match objects
        physical_measurements: List of PhysicalMeasurement objects
        achievements: List of Achievement objects
        club_history: List of ClubHistory objects
        training_camps: List of TrainingCamp objects
        physical_metrics: List of PhysicalMetrics objects
        references: List of Reference objects
        output_dir: Output directory for PDFs
        
    Returns:
        Dictionary with paths to generated PDFs:
        {
            'season_tracker': path,
            'scout_report': path,
            'player_resume': path
        }
    """
    # Build Player object from app data
    player = build_player_from_data(
        settings=settings,
        matches=matches,
        physical_measurements=physical_measurements,
        achievements=achievements,
        club_history=club_history,
        training_camps=training_camps,
        physical_metrics=physical_metrics,
        references=references
    )
    
    # Generate all three reports
    season_tracker_path = generate_season_tracker(player, output_dir)
    scout_report_path = generate_scout_report(player, output_dir)
    player_resume_path = generate_player_resume(player, output_dir)
    
    return {
        'season_tracker': season_tracker_path,
        'scout_report': scout_report_path,
        'player_resume': player_resume_path
    }


def generate_season_tracker_from_data(
    settings: AppSettings,
    matches: List[AppMatch],
    physical_measurements: Optional[List[PhysicalMeasurement]] = None,
    achievements: Optional[List[Achievement]] = None,
    club_history: Optional[List[ClubHistory]] = None,
    training_camps: Optional[List[TrainingCamp]] = None,
    physical_metrics: Optional[List[PhysicalMetrics]] = None,
    references: Optional[List[Reference]] = None,
    output_dir: str = "output"
) -> str:
    """Generate Season Tracker report from app data models"""
    player = build_player_from_data(
        settings=settings,
        matches=matches,
        physical_measurements=physical_measurements,
        achievements=achievements,
        club_history=club_history,
        training_camps=training_camps,
        physical_metrics=physical_metrics,
        references=references
    )
    return generate_season_tracker(player, output_dir)


def generate_scout_report_from_data(
    settings: AppSettings,
    matches: List[AppMatch],
    physical_measurements: Optional[List[PhysicalMeasurement]] = None,
    achievements: Optional[List[Achievement]] = None,
    club_history: Optional[List[ClubHistory]] = None,
    training_camps: Optional[List[TrainingCamp]] = None,
    physical_metrics: Optional[List[PhysicalMetrics]] = None,
    references: Optional[List[Reference]] = None,
    output_dir: str = "output"
) -> str:
    """Generate Scout Report from app data models"""
    player = build_player_from_data(
        settings=settings,
        matches=matches,
        physical_measurements=physical_measurements,
        achievements=achievements,
        club_history=club_history,
        training_camps=training_camps,
        physical_metrics=physical_metrics,
        references=references
    )
    return generate_scout_report(player, output_dir)


def generate_player_resume_from_data(
    settings: AppSettings,
    matches: List[AppMatch],
    physical_measurements: Optional[List[PhysicalMeasurement]] = None,
    achievements: Optional[List[Achievement]] = None,
    club_history: Optional[List[ClubHistory]] = None,
    training_camps: Optional[List[TrainingCamp]] = None,
    physical_metrics: Optional[List[PhysicalMetrics]] = None,
    references: Optional[List[Reference]] = None,
    output_dir: str = "output"
) -> str:
    """Generate Player Resume from app data models"""
    player = build_player_from_data(
        settings=settings,
        matches=matches,
        physical_measurements=physical_measurements,
        achievements=achievements,
        club_history=club_history,
        training_camps=training_camps,
        physical_metrics=physical_metrics,
        references=references
    )
    return generate_player_resume(player, output_dir)

