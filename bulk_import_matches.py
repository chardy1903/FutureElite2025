#!/usr/bin/env python3
"""
Bulk import script for matches.
Run this script to quickly add multiple matches to the app.

Usage:
    python bulk_import_matches.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.storage import StorageManager
from app.models import Match, MatchCategory, MatchResult

# Initialize storage
storage = StorageManager()

def determine_result(score: str) -> MatchResult:
    """Determine match result from score"""
    if not score or score.strip() == '':
        return None
    
    try:
        # Handle both "3-2" and "3 - 2" formats
        score = score.replace(' ', '')
        if '-' in score:
            parts = score.split('-')
            if len(parts) == 2:
                our_score = int(parts[0].strip())
                their_score = int(parts[1].strip())
                
                if our_score > their_score:
                    return MatchResult.WIN
                elif our_score < their_score:
                    return MatchResult.LOSS
                else:
                    return MatchResult.DRAW
    except (ValueError, AttributeError, IndexError):
        return None

def format_score(score: str) -> str:
    """Format score to match app format (e.g., '7 - 5')"""
    if not score or score.strip() == '':
        return None
    
    # Remove spaces and split by dash
    score = score.replace(' ', '')
    if '-' in score:
        parts = score.split('-')
        if len(parts) == 2:
            return f"{parts[0].strip()} - {parts[1].strip()}"
    return score

# Match data from your table
# Format: (opponent, location, score, brodie_goals, brodie_assists, minutes, date, category)
# NOTE: Update the dates below to match your actual match dates!
# The script will skip matches that already exist (by opponent name and date)
matches_data = [
    ("Altrajz", "Al-Farabi", "3-2", 0, 0, 15, "01 Sep 2025", MatchCategory.PRE_SEASON_FRIENDLY),
    ("Faith Academy", "Al-Farabi", "2-3", 0, 0, 20, "08 Sep 2025", MatchCategory.PRE_SEASON_FRIENDLY),
    ("Ole Academy", "Al-Farabi", "3-5", 0, 0, 25, "15 Sep 2025", MatchCategory.PRE_SEASON_FRIENDLY),
    ("Aspire", "Al-Farabi", "7-5", 1, 0, 30, "22 Sep 2025", MatchCategory.PRE_SEASON_FRIENDLY),
    ("Stars", "Al-Farabi", "6-2", 2, 0, 35, "29 Sep 2025", MatchCategory.PRE_SEASON_FRIENDLY),
    ("Altraji", "Arena", "3-4", 1, 0, 40, "06 Oct 2025", MatchCategory.PRE_SEASON_FRIENDLY),
    ("Al Etifaq", "Al-Farabi", "1-3", 0, 1, 20, "13 Oct 2025", MatchCategory.PRE_SEASON_FRIENDLY),
    ("Al Hilal", "Al-Farabi", "4-3", 1, 0, 30, "20 Oct 2025", MatchCategory.PRE_SEASON_FRIENDLY),
    ("Al Fatah", "Al-Farabi", None, 0, 0, 25, "27 Oct 2025", MatchCategory.PRE_SEASON_FRIENDLY),
    ("Dhahran", "Al-Farabi", None, 0, 0, 30, "03 Nov 2025", MatchCategory.LEAGUE),
    ("Bahrain", "Al Rakah", None, 1, 0, 35, "10 Nov 2025", MatchCategory.LEAGUE),
    ("Winners", "Al-Farabi", None, 0, 1, 20, "17 Nov 2025", MatchCategory.LEAGUE),
    ("Safa", "Al-Farabi", None, 2, 0, 40, "24 Nov 2025", MatchCategory.LEAGUE),
    ("Qadsiah Academy", "Al-Farabi", None, 1, 0, 30, "01 Dec 2025", MatchCategory.LEAGUE),
]

def import_matches():
    """Import all matches from the data list"""
    existing_matches = storage.load_matches()
    
    # Create a set of existing matches by opponent+date for duplicate checking
    existing_keys = set()
    for m in existing_matches:
        opponent = m.get('opponent', '').lower()
        date = m.get('date', '')
        existing_keys.add(f"{opponent}_{date}")
    
    imported = 0
    skipped = 0
    errors = []
    
    print(f"Found {len(existing_matches)} existing matches")
    print(f"Importing {len(matches_data)} new matches...\n")
    
    for opponent, location, score, goals, assists, minutes, date, category in matches_data:
        try:
            # Check if match already exists
            match_key = f"{opponent.lower()}_{date}"
            if match_key in existing_keys:
                print(f"⚠️  Skipping {opponent} ({date}) - already exists")
                skipped += 1
                continue
            
            # Format score
            formatted_score = format_score(score) if score else None
            result = determine_result(formatted_score) if formatted_score else None
            
            # Create match
            match = Match(
                category=category,
                date=date,
                opponent=opponent,
                location=location,
                result=result,
                score=formatted_score,
                brodie_goals=goals,
                brodie_assists=assists,
                minutes_played=minutes,
                notes="",
                is_fixture=False
            )
            
            # Save match
            match_id = storage.save_match(match)
            score_display = formatted_score if formatted_score else "No score"
            print(f"✅ Imported: {opponent} ({date}) - {score_display} | {goals}G {assists}A {minutes}min")
            imported += 1
            existing_keys.add(match_key)  # Add to set to prevent duplicates in same import
            
        except Exception as e:
            error_msg = f"❌ Error importing {opponent}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
    
    print(f"\n{'='*70}")
    print(f"Import complete!")
    print(f"✅ Imported: {imported} matches")
    print(f"⚠️  Skipped: {skipped} matches (already exist)")
    if errors:
        print(f"❌ Errors: {len(errors)} matches")
        for error in errors:
            print(f"   {error}")
    print(f"{'='*70}")

if __name__ == "__main__":
    print("="*70)
    print("Bulk Match Import Script")
    print("="*70)
    print("\nThis script will import the following matches:")
    print(f"  - {len(matches_data)} matches total")
    print("\nMatches to import:")
    for i, (opponent, location, score, goals, assists, minutes, date, category) in enumerate(matches_data, 1):
        score_display = score if score else "No score"
        print(f"  {i:2d}. {opponent:20s} | {date:12s} | {score_display:8s} | {goals}G {assists}A {minutes}min")
    
    response = input("\n⚠️  This will add matches to your app. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Import cancelled.")
        sys.exit(0)
    
    print()
    import_matches()
    
    print("\n✅ Done! Refresh your app at http://127.0.0.1:5000/matches to see the new matches.")
