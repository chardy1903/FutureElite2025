#!/usr/bin/env python3
"""
Clear all existing matches and import new data.
"""

import sys
from pathlib import Path

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
    
    score = score.replace(' ', '')
    if '-' in score:
        parts = score.split('-')
        if len(parts) == 2:
            return f"{parts[0].strip()} - {parts[1].strip()}"
    return score

# Updated match data from your table - ALL 14 matches
# Format: (opponent, location, score, brodie_goals, brodie_assists, minutes, date, category, notes)
# All matches are Pre-season Friendly
matches_data = [
    ("Altrajz", "Al-Farabi", None, 0, 0, 15, "28 Aug 2025", MatchCategory.PRE_SEASON_FRIENDLY, ""),
    ("Faith Academy", "Al-Farabi", None, 0, 0, 20, "04 Sep 2025", MatchCategory.PRE_SEASON_FRIENDLY, ""),
    ("Ole Academy", "Al-Farabi", "3-2", 1, 0, 20, "11 Sep 2025", MatchCategory.PRE_SEASON_FRIENDLY, ""),
    ("Aspire", "Al-Farabi", None, 1, 0, 20, "18 Sep 2025", MatchCategory.PRE_SEASON_FRIENDLY, ""),
    ("Stars", "Al-Farabi", None, 0, 0, 20, "25 Sep 2025", MatchCategory.PRE_SEASON_FRIENDLY, ""),
    ("Altraji", "Al-Farabi", None, 1, 0, 25, "02 Oct 2025", MatchCategory.PRE_SEASON_FRIENDLY, "Penalty"),
    ("Al Etifaq", "Al-Farabi", "2-3", 2, 0, 35, "09 Oct 2025", MatchCategory.PRE_SEASON_FRIENDLY, "1st penalty, 2nd Long pass; beat two defenders; finished bottom-left."),
    ("Al Hilal", "Arena", "3-5", 0, 0, 25, "16 Oct 2025", MatchCategory.PRE_SEASON_FRIENDLY, ""),
    ("Al Fatah", "Al-Farabi", "2-3", 1, 0, 35, "17 Oct 2025", MatchCategory.PRE_SEASON_FRIENDLY, "Received outside box; dribbled inside defenders; top-right finish."),
    ("Dhahran", "Offside Arena", "7-5", 1, 1, 30, "23 Oct 2025", MatchCategory.PRE_SEASON_FRIENDLY, "Scored from edge of box after dribbling and losing defenders. Also provided 1 assist."),
    ("Bahrain", "Al Rakah", "6-2", 2, 1, 40, "28 Oct 2025", MatchCategory.PRE_SEASON_FRIENDLY, "1st poachers close range finish, 2nd penalty"),
    ("Winners", "Al-Farabi", "3-4", 0, 0, 30, "30 Oct 2025", MatchCategory.PRE_SEASON_FRIENDLY, ""),
    ("Safa", "Al-Farabi", "1-3", 0, 1, 30, "12 Nov 2025", MatchCategory.PRE_SEASON_FRIENDLY, "Assist - Keeper saved the shot, and winger finished the rebound"),
    ("Qadsiah Academy", "Al-Farabi", "4-3", 2, 0, 40, "13 Nov 2025", MatchCategory.PRE_SEASON_FRIENDLY, "Both goals reactive finish in crowded box"),
]

def clear_and_import():
    """Clear all existing matches and import new data"""
    print("="*70)
    print("Clear and Import Matches")
    print("="*70)
    
    # Clear all existing matches
    print("\n🗑️  Clearing all existing matches...")
    storage._save_matches([])
    existing_count = len(storage.load_matches())
    print(f"✅ Cleared. Remaining matches: {existing_count}")
    
    # Import new matches
    print(f"\n📥 Importing {len(matches_data)} new matches...\n")
    
    imported = 0
    errors = []
    
    # Build all matches first
    all_matches = []
    for opponent, location, score, goals, assists, minutes, date, category, notes in matches_data:
        try:
            formatted_score = format_score(score) if score else None
            result = determine_result(formatted_score) if formatted_score else None
            
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
                notes=notes,
                is_fixture=False
            )
            
            all_matches.append(match.dict())
            score_display = formatted_score if formatted_score else "No score"
            print(f"✅ {opponent:20s} | {date:12s} | {score_display:8s} | {goals}G {assists}A {minutes}min")
            imported += 1
            
        except Exception as e:
            error_msg = f"❌ Error importing {opponent}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
    
    # Save all matches at once
    if all_matches:
        storage._save_matches(all_matches)
        print(f"\n💾 Saved {len(all_matches)} matches to database")
    
    print(f"\n{'='*70}")
    print(f"Import complete!")
    print(f"✅ Imported: {imported} matches")
    if errors:
        print(f"❌ Errors: {len(errors)} matches")
        for error in errors:
            print(f"   {error}")
    print(f"{'='*70}")

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will DELETE all existing matches and replace them with new data!")
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Operation cancelled.")
        sys.exit(0)
    
    clear_and_import()
    
    print("\n✅ Done! Refresh your app at http://127.0.0.1:5000/matches to see the updated matches.")

