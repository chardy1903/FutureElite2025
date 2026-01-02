"""
Adapters to convert from existing app models to the new Player data contract.

This module bridges the gap between the existing data models and the standardized
report generation system.
"""

from typing import List, Optional
from datetime import datetime

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
from ..phv_calculator import calculate_phv, calculate_predicted_adult_height
from .types import (
    Player,
    Match,
    PHVData,
    GrowthHistoryEntry,
    ClubHistoryEntry,
    Award,
    TrainingCamp as ReportTrainingCamp,
    SocialLink,
    Reference as ReportReference
)
from .formatters import format_date_display_to_iso


def convert_match(app_match: AppMatch) -> Match:
    """
    Convert an AppMatch to a report Match.
    
    Args:
        app_match: Match from app models
        
    Returns:
        Match for report generation
    """
    # Parse score string "7 - 5" to scoreFor and scoreAgainst
    score_for = None
    score_against = None
    if app_match.score:
        try:
            parts = app_match.score.split(' - ')
            if len(parts) == 2:
                score_for = int(parts[0].strip())
                score_against = int(parts[1].strip())
        except (ValueError, IndexError):
            pass
    
    # Convert date from "dd MMM yyyy" to ISO format
    iso_date = format_date_display_to_iso(app_match.date)
    
    # Extract match day from category if possible (this is optional)
    match_day = None
    # Could parse from notes or other fields if needed
    
    return Match(
        matchDay=match_day,
        date=iso_date,
        opponent=app_match.opponent,
        location=app_match.location if app_match.location else None,
        category=app_match.category.value if app_match.category else None,
        scoreFor=score_for,
        scoreAgainst=score_against,
        minutesPlayed=app_match.minutes_played,
        goals=app_match.brodie_goals,
        assists=app_match.brodie_assists,
        notes=app_match.notes if app_match.notes else None
    )


def build_player_from_data(
    settings: AppSettings,
    matches: List[AppMatch],
    physical_measurements: Optional[List[PhysicalMeasurement]] = None,
    achievements: Optional[List[Achievement]] = None,
    club_history: Optional[List[ClubHistory]] = None,
    training_camps: Optional[List[TrainingCamp]] = None,
    physical_metrics: Optional[List[PhysicalMetrics]] = None,
    references: Optional[List[Reference]] = None
) -> Player:
    """
    Build a Player object from existing app data models.
    
    Args:
        settings: AppSettings object
        matches: List of Match objects
        physical_measurements: List of PhysicalMeasurement objects
        achievements: List of Achievement objects
        club_history: List of ClubHistory objects
        training_camps: List of TrainingCamp objects
        physical_metrics: List of PhysicalMetrics objects
        references: List of Reference objects
        
    Returns:
        Player object for report generation
    """
    # Convert date of birth from "dd MMM yyyy" to ISO
    dob_iso = None
    if settings.date_of_birth:
        dob_iso = format_date_display_to_iso(settings.date_of_birth)
    
    # Convert matches
    report_matches = [convert_match(m) for m in matches if not m.is_fixture and m.include_in_report]
    
    # Build PHV data
    phv_data = None
    if physical_measurements and settings.date_of_birth:
        phv_result = calculate_phv(physical_measurements, settings.date_of_birth)
        if phv_result:
            # Determine PHV status based on current age
            phv_status = None
            current_age_for_phv = None
            if phv_result.get('phv_age') is not None and dob_iso:
                from .formatters import calculate_age
                current_age_for_phv = calculate_age(dob_iso)
                phv_age = phv_result.get('phv_age')
                
                if current_age_for_phv and phv_age:
                    age_diff = current_age_for_phv - phv_age
                    if age_diff < -0.5:
                        phv_status = "Pre-PHV"
                    elif age_diff <= 0.5:
                        phv_status = "Circa-PHV"
                    else:
                        phv_status = "Post-PHV"
            
            # Get predicted adult height
            current_age = None
            if dob_iso:
                from .formatters import calculate_age
                current_age = calculate_age(dob_iso)
            
            predicted_height_result = calculate_predicted_adult_height(
                physical_measurements,
                settings.date_of_birth,
                current_age=current_age_for_phv,
                phv_result=phv_result
            )
            
            predicted_height_cm = None
            predicted_confidence = None
            if predicted_height_result:
                predicted_height_cm = predicted_height_result.get('predicted_adult_height_cm')
                predicted_confidence = predicted_height_result.get('confidence', 'Medium').capitalize()
            
            phv_date_iso = None
            if phv_result.get('phv_date'):
                phv_date_iso = format_date_display_to_iso(phv_result['phv_date'])
            
            phv_data = PHVData(
                phvDate=phv_date_iso,
                phvAgeYears=phv_result.get('phv_age'),
                status=phv_status,
                peakGrowthVelocityCmPerYear=phv_result.get('phv_velocity_cm_per_year'),
                predictedAdultHeightCm=predicted_height_cm,
                predictedAdultHeightConfidence=predicted_confidence
            )
    
    # Build growth history
    growth_history = None
    if physical_measurements:
        growth_history = []
        for pm in physical_measurements:
            if pm.include_in_report:
                iso_date = format_date_display_to_iso(pm.date)
                growth_history.append(GrowthHistoryEntry(
                    date=iso_date,
                    heightCm=pm.height_cm,
                    weightKg=pm.weight_kg,
                    notes=pm.notes if pm.notes else None
                ))
    
    # Build club history
    club_history_list = None
    if club_history:
        club_history_list = []
        for ch in club_history:
            club_history_list.append(ClubHistoryEntry(
                clubName=ch.club_name,
                season=ch.season,
                ageGroup=ch.age_group,
                position=ch.position,
                achievements=ch.achievements
            ))
    
    # Build awards
    awards_list = None
    if achievements:
        awards_list = []
        for ach in achievements:
            iso_date = format_date_display_to_iso(ach.date)
            awards_list.append(Award(
                date=iso_date,
                title=ach.title,
                category=ach.category,
                description=ach.description
            ))
    
    # Build training camps
    camps_list = None
    if training_camps:
        camps_list = []
        for camp in training_camps:
            start_iso = format_date_display_to_iso(camp.start_date)
            end_iso = format_date_display_to_iso(camp.end_date) if camp.end_date else start_iso
            camps_list.append(ReportTrainingCamp(
                name=camp.camp_name,
                organizer=camp.organizer,
                location=camp.location,
                startDate=start_iso,
                endDate=end_iso,
                ageGroup=camp.age_group,
                focusArea=camp.focus_area
            ))
    
    # Build social links
    social_links = None
    if settings.social_media_links:
        social_links = []
        for platform, url in settings.social_media_links.items():
            if url:
                social_links.append(SocialLink(platform=platform, url=url))
    
    # Build references
    references_list = None
    if references:
        references_list = []
        for ref in references:
            references_list.append(ReportReference(
                name=ref.name,
                role=ref.position,  # Map position to role
                club=ref.organization,  # Map organization to club
                email=ref.email,
                phone=ref.phone,
                notes=ref.notes
            ))
    
    # Get latest height and weight from physical measurements (most accurate)
    latest_height = None
    latest_weight = None
    if physical_measurements:
        # Get the most recent measurement with height/weight
        valid_measurements = [m for m in physical_measurements if m.height_cm is not None or m.weight_kg is not None]
        if valid_measurements:
            from datetime import datetime
            latest_measurement = max(valid_measurements, key=lambda m: datetime.strptime(m.date, "%d %b %Y"))
            latest_height = latest_measurement.height_cm
            latest_weight = latest_measurement.weight_kg
    
    # Fall back to settings if no measurements available
    if latest_height is None:
        latest_height = settings.height_cm
    if latest_weight is None:
        latest_weight = settings.weight_kg
    
    # Calculate BMI if height and weight available
    bmi = None
    if latest_height and latest_weight:
        bmi = round(latest_weight / ((latest_height / 100) ** 2), 1)
    
    # Parse position secondary if it's a comma-separated string
    position_secondary = None
    if settings.position:
        # Could parse from notes or other fields if secondary positions are stored
        # For now, leave as None unless we have a specific field
    
    return Player(
        fullName=settings.player_name,
        dob=dob_iso or "2000-01-01",  # Default fallback
        nationality=None,  # Not in current model
        positionPrimary=settings.position or "Not specified",
        positionSecondary=position_secondary,
        dominantFoot=settings.dominant_foot,
        currentClub=settings.club_name,
        team=settings.club_name,  # Use club_name as team
        seasonLabel=settings.season_year,
        contactEmail=settings.contact_email,
        socialLinks=social_links,
        heightCm=latest_height,
        weightKg=latest_weight,
        bmi=bmi,
        phv=phv_data,
        growthHistory=growth_history,
        clubHistory=club_history_list,
        awards=awards_list,
        camps=camps_list,
        highlightReelUrl=settings.highlight_reel_urls[0] if settings.highlight_reel_urls else None,
        references=references_list,
        matches=report_matches
    )

