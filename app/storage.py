import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from .models import MatchData, Match, AppSettings, PhysicalMeasurement, MatchResult, Achievement, ClubHistory, TrainingCamp, PhysicalMetrics, User, Subscription, SubscriptionStatus, Reference


class StorageManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.matches_file = self.data_dir / "matches.json"
        self.settings_file = self.data_dir / "settings.json"
        self.physical_measurements_file = self.data_dir / "physical_measurements.json"
        self.achievements_file = self.data_dir / "achievements.json"
        self.club_history_file = self.data_dir / "club_history.json"
        self.training_camps_file = self.data_dir / "training_camps.json"
        self.physical_metrics_file = self.data_dir / "physical_metrics.json"
        self.users_file = self.data_dir / "users.json"
        self.subscriptions_file = self.data_dir / "subscriptions.json"
        self.references_file = self.data_dir / "references.json"
        self.reset_tokens_file = self.data_dir / "reset_tokens.json"
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()

    def _initialize_files(self):
        """Initialize JSON files with default data if they don't exist"""
        if not self.matches_file.exists():
            self._save_matches([])
        
        if not self.settings_file.exists():
            # Settings will be created per user
            self._save_user_settings({})
        
        if not self.physical_measurements_file.exists():
            self._save_physical_measurements([])
        
        if not self.achievements_file.exists():
            self._save_achievements([])
        
        if not self.club_history_file.exists():
            self._save_club_history([])
        
        if not self.training_camps_file.exists():
            self._save_training_camps([])
        
        if not self.physical_metrics_file.exists():
            self._save_physical_metrics([])
        
        if not self.users_file.exists():
            self._save_users([])
        
        if not self.references_file.exists():
            self._save_references([])

    def _save_matches(self, matches: list) -> None:
        """Save matches to JSON file"""
        try:
            with open(self.matches_file, 'w', encoding='utf-8') as f:
                json.dump(matches, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save matches: {str(e)}")

    def _save_settings(self, settings: AppSettings, user_id: str) -> None:
        """Save settings to JSON file for a specific user"""
        try:
            user_settings = self._load_user_settings()
            user_settings[user_id] = settings.model_dump()
            self._save_user_settings(user_settings)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save settings: {str(e)}")
    
    def _save_user_settings(self, user_settings: Dict[str, Any]) -> None:
        """Save user settings dictionary"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(user_settings, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save user settings: {str(e)}")
    
    def _load_user_settings(self) -> Dict[str, Any]:
        """Load user settings dictionary"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def load_matches(self, user_id: Optional[str] = None) -> list:
        """Load matches from JSON file, optionally filtered by user_id"""
        try:
            with open(self.matches_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                matches = data if isinstance(data, list) else []
                if user_id:
                    matches = [m for m in matches if m.get('user_id') == user_id]
                return matches
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def load_settings(self, user_id: Optional[str] = None) -> AppSettings:
        """Load settings from JSON file for a specific user"""
        if not user_id:
            return AppSettings()
        try:
            user_settings = self._load_user_settings()
            if user_id in user_settings:
                return AppSettings(**user_settings[user_id])
            return AppSettings()
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return AppSettings()

    def save_match(self, match: Match, user_id: str) -> str:
        """Save a single match and return its ID"""
        matches = self.load_matches()  # Load all matches
        
        # Check if match with this ID already exists (for updates)
        existing_index = None
        for i, existing_match in enumerate(matches):
            if existing_match.get('id') == match.id and existing_match.get('user_id') == user_id:
                existing_index = i
                break
        
        match_dict = match.model_dump()
        match_dict['user_id'] = user_id  # Add user_id to match
        
        if existing_index is not None:
            matches[existing_index] = match_dict
        else:
            matches.append(match_dict)
        
        self._save_matches(matches)
        return match.id

    def get_match(self, match_id: str, user_id: str) -> Optional[Match]:
        """Get a specific match by ID for a user"""
        matches = self.load_matches(user_id)
        for match_data in matches:
            if match_data.get('id') == match_id:
                try:
                    # Remove user_id before creating Match object
                    match_dict = {k: v for k, v in match_data.items() if k != 'user_id'}
                    return Match(**match_dict)
                except (ValueError, TypeError, KeyError) as e:
                    # Log invalid match data but continue
                    continue
        return None

    def delete_match(self, match_id: str, user_id: str) -> bool:
        """Delete a match by ID for a user"""
        matches = self.load_matches()  # Load all matches
        original_length = len(matches)
        matches = [m for m in matches if not (m.get('id') == match_id and m.get('user_id') == user_id)]
        
        if len(matches) < original_length:
            self._save_matches(matches)
            return True
        return False

    def get_all_matches(self, user_id: Optional[str] = None) -> list[Match]:
        """Get all matches as Match objects, optionally filtered by user_id"""
        matches_data = self.load_matches(user_id)
        matches = []
        for match_data in matches_data:
            try:
                # Remove user_id before creating Match object
                match_dict = {k: v for k, v in match_data.items() if k != 'user_id'}
                matches.append(Match(**match_dict))
            except (ValueError, TypeError, KeyError):
                # Skip invalid matches
                continue
        return matches

    def get_matches_by_category(self, category: str, user_id: Optional[str] = None) -> list[Match]:
        """Get matches filtered by category"""
        all_matches = self.get_all_matches(user_id)
        return [m for m in all_matches if m.category.value == category]

    def get_fixtures(self, user_id: Optional[str] = None) -> list[Match]:
        """Get upcoming fixtures (matches with is_fixture=True)"""
        all_matches = self.get_all_matches(user_id)
        return [m for m in all_matches if m.is_fixture]

    def get_completed_matches(self, user_id: Optional[str] = None) -> list[Match]:
        """Get completed matches (is_fixture=False)"""
        all_matches = self.get_all_matches(user_id)
        return [m for m in all_matches if not m.is_fixture]

    def save_settings(self, settings: AppSettings, user_id: str) -> None:
        """Save settings for a user"""
        self._save_settings(settings, user_id)

    def export_data(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Export all data as a dictionary for backup, optionally filtered by user_id"""
        return {
            "matches": self.load_matches(user_id),
            "settings": self.load_settings(user_id).model_dump() if user_id else {},
            "physical_measurements": self.load_physical_measurements(user_id),
            "achievements": self.load_achievements(user_id),
            "club_history": self.load_club_history(user_id),
            "training_camps": self.load_training_camps(user_id),
            "physical_metrics": self.load_physical_metrics(user_id),
            "exported_at": datetime.now().isoformat()
        }

    def import_data(self, data: Dict[str, Any], user_id: str) -> bool:
        """Import data from backup dictionary and assign to user"""
        try:
            if "matches" in data:
                if not isinstance(data["matches"], list):
                    return False
                # Assign user_id to all matches
                for match in data["matches"]:
                    match['user_id'] = user_id
                # Load existing matches and merge (don't overwrite)
                existing_matches = self.load_matches()
                existing_ids = {m.get('id') for m in existing_matches if m.get('user_id') == user_id}
                # Only add matches that don't already exist for this user
                new_matches = [m for m in data["matches"] if m.get('id') not in existing_ids]
                all_matches = existing_matches + new_matches
                self._save_matches(all_matches)
            
            if "settings" in data:
                if not isinstance(data["settings"], dict):
                    return False
                settings = AppSettings(**data["settings"])
                self._save_settings(settings, user_id)
            
            if "physical_measurements" in data:
                if not isinstance(data["physical_measurements"], list):
                    return False
                # Assign user_id to all measurements
                for measurement in data["physical_measurements"]:
                    measurement['user_id'] = user_id
                # Load existing measurements and merge
                existing_measurements = self.load_physical_measurements()
                existing_ids = {m.get('id') for m in existing_measurements if m.get('user_id') == user_id}
                new_measurements = [m for m in data["physical_measurements"] if m.get('id') not in existing_ids]
                all_measurements = existing_measurements + new_measurements
                self._save_physical_measurements(all_measurements)
            
            if "achievements" in data:
                if not isinstance(data["achievements"], list):
                    return False
                # Assign user_id to all achievements
                for achievement in data["achievements"]:
                    achievement['user_id'] = user_id
                # Load existing achievements and merge
                existing_achievements = self.load_achievements()
                existing_ids = {a.get('id') for a in existing_achievements if a.get('user_id') == user_id}
                new_achievements = [a for a in data["achievements"] if a.get('id') not in existing_ids]
                all_achievements = existing_achievements + new_achievements
                self._save_achievements(all_achievements)
            
            if "club_history" in data:
                if not isinstance(data["club_history"], list):
                    return False
                # Assign user_id to all club history entries
                for entry in data["club_history"]:
                    entry['user_id'] = user_id
                # Load existing club history and merge
                existing_history = self.load_club_history()
                existing_ids = {h.get('id') for h in existing_history if h.get('user_id') == user_id}
                new_history = [h for h in data["club_history"] if h.get('id') not in existing_ids]
                all_history = existing_history + new_history
                self._save_club_history(all_history)
            
            if "training_camps" in data:
                if not isinstance(data["training_camps"], list):
                    return False
                # Assign user_id to all training camps
                for camp in data["training_camps"]:
                    camp['user_id'] = user_id
                # Load existing training camps and merge
                existing_camps = self.load_training_camps()
                existing_ids = {c.get('id') for c in existing_camps if c.get('user_id') == user_id}
                new_camps = [c for c in data["training_camps"] if c.get('id') not in existing_ids]
                all_camps = existing_camps + new_camps
                self._save_training_camps(all_camps)
            
            if "physical_metrics" in data:
                if not isinstance(data["physical_metrics"], list):
                    return False
                # Assign user_id to all physical metrics
                for metric in data["physical_metrics"]:
                    metric['user_id'] = user_id
                # Load existing physical metrics and merge
                existing_metrics = self.load_physical_metrics()
                existing_ids = {m.get('id') for m in existing_metrics if m.get('user_id') == user_id}
                new_metrics = [m for m in data["physical_metrics"] if m.get('id') not in existing_ids]
                all_metrics = existing_metrics + new_metrics
                self._save_physical_metrics(all_metrics)
            
            return True
        except (ValueError, TypeError, KeyError) as e:
            # Log error in production
            return False

    def get_season_stats(self, user_id: Optional[str] = None, period: Optional[str] = None) -> Dict[str, Any]:
        """Calculate season statistics, optionally filtered by time period
        
        Args:
            user_id: User ID to filter matches
            period: Time period filter ('all_time', 'season', '12_months', '6_months', '3_months', 'last_month')
        """
        completed_matches = self.get_completed_matches(user_id)
        
        # Filter by period if specified
        if period and period != 'all_time':
            from .utils import filter_matches_by_period
            settings = self.load_settings(user_id) if user_id else None
            season_year = settings.season_year if settings else None
            completed_matches = filter_matches_by_period(completed_matches, period, season_year)
        
        stats = {
            "total_matches": len(completed_matches),
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals": 0,
            "assists": 0,
            "minutes": 0
        }
        
        for match in completed_matches:
            if match.result:
                if match.result == MatchResult.WIN:
                    stats["wins"] += 1
                elif match.result == MatchResult.DRAW:
                    stats["draws"] += 1
                elif match.result == MatchResult.LOSS:
                    stats["losses"] += 1
            
            stats["goals"] += match.brodie_goals
            stats["assists"] += match.brodie_assists
            stats["minutes"] += match.minutes_played
        
        return stats

    def get_category_stats(self, category: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculate statistics for a specific category"""
        category_matches = self.get_matches_by_category(category, user_id)
        
        stats = {
            "matches": len(category_matches),
            "goals": 0,
            "assists": 0,
            "minutes": 0
        }
        
        for match in category_matches:
            stats["goals"] += match.brodie_goals
            stats["assists"] += match.brodie_assists
            stats["minutes"] += match.minutes_played
        
        return stats
    
    # Physical Measurements methods
    def _save_physical_measurements(self, measurements: list) -> None:
        """Save physical measurements to JSON file"""
        try:
            with open(self.physical_measurements_file, 'w', encoding='utf-8') as f:
                json.dump(measurements, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save physical measurements: {str(e)}")
    
    def load_physical_measurements(self, user_id: Optional[str] = None) -> list:
        """Load physical measurements from JSON file, optionally filtered by user_id"""
        try:
            with open(self.physical_measurements_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                measurements = data if isinstance(data, list) else []
                if user_id:
                    measurements = [m for m in measurements if m.get('user_id') == user_id]
                return measurements
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_physical_measurement(self, measurement: PhysicalMeasurement, user_id: str) -> str:
        """Save a single physical measurement and return its ID"""
        measurements = self.load_physical_measurements()  # Load all
        
        # Check if measurement with this ID already exists (for updates)
        existing_index = None
        for i, existing_measurement in enumerate(measurements):
            if existing_measurement.get('id') == measurement.id and existing_measurement.get('user_id') == user_id:
                existing_index = i
                break
        
        measurement_dict = measurement.model_dump()
        measurement_dict['user_id'] = user_id
        
        if existing_index is not None:
            measurements[existing_index] = measurement_dict
        else:
            measurements.append(measurement_dict)
        
        self._save_physical_measurements(measurements)
        return measurement.id
    
    def get_physical_measurement(self, measurement_id: str, user_id: str) -> Optional[PhysicalMeasurement]:
        """Get a specific physical measurement by ID for a user"""
        measurements = self.load_physical_measurements(user_id)
        for measurement_data in measurements:
            if measurement_data.get('id') == measurement_id:
                try:
                    # Remove user_id before creating PhysicalMeasurement object
                    measurement_dict = {k: v for k, v in measurement_data.items() if k != 'user_id'}
                    return PhysicalMeasurement(**measurement_dict)
                except (ValueError, TypeError, KeyError):
                    continue
        return None
    
    def get_all_physical_measurements(self, user_id: Optional[str] = None) -> list[PhysicalMeasurement]:
        """Get all physical measurements as PhysicalMeasurement objects, optionally filtered by user_id"""
        measurements_data = self.load_physical_measurements(user_id)
        measurements = []
        for measurement_data in measurements_data:
            try:
                # Remove user_id before creating PhysicalMeasurement object
                measurement_dict = {k: v for k, v in measurement_data.items() if k != 'user_id'}
                measurements.append(PhysicalMeasurement(**measurement_dict))
            except (ValueError, TypeError, KeyError):
                # Skip invalid measurements
                continue
        return measurements
    
    def delete_physical_measurement(self, measurement_id: str, user_id: str) -> bool:
        """Delete a physical measurement by ID for a user"""
        measurements = self.load_physical_measurements()  # Load all
        original_length = len(measurements)
        measurements = [m for m in measurements if not (m.get('id') == measurement_id and m.get('user_id') == user_id)]
        
        if len(measurements) < original_length:
            self._save_physical_measurements(measurements)
            return True
        return False
    
    # Achievements methods
    def _save_achievements(self, achievements: list) -> None:
        """Save achievements to JSON file"""
        try:
            with open(self.achievements_file, 'w', encoding='utf-8') as f:
                json.dump(achievements, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save achievements: {str(e)}")
    
    def load_achievements(self, user_id: Optional[str] = None) -> list:
        """Load achievements from JSON file, optionally filtered by user_id"""
        try:
            with open(self.achievements_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                achievements = data if isinstance(data, list) else []
                if user_id:
                    achievements = [a for a in achievements if a.get('user_id') == user_id]
                return achievements
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_achievement(self, achievement: Achievement, user_id: str) -> str:
        """Save a single achievement and return its ID"""
        achievements = self.load_achievements()  # Load all
        
        # Check if achievement with this ID already exists (for updates)
        existing_index = None
        for i, existing_achievement in enumerate(achievements):
            if existing_achievement.get('id') == achievement.id and existing_achievement.get('user_id') == user_id:
                existing_index = i
                break
        
        achievement_dict = achievement.model_dump()
        achievement_dict['user_id'] = user_id
        
        if existing_index is not None:
            achievements[existing_index] = achievement_dict
        else:
            achievements.append(achievement_dict)
        
        self._save_achievements(achievements)
        return achievement.id
    
    def get_achievement(self, achievement_id: str, user_id: str) -> Optional[Achievement]:
        """Get a specific achievement by ID for a user"""
        achievements = self.load_achievements(user_id)
        for achievement_data in achievements:
            if achievement_data.get('id') == achievement_id:
                try:
                    # Remove user_id before creating Achievement object
                    achievement_dict = {k: v for k, v in achievement_data.items() if k != 'user_id'}
                    return Achievement(**achievement_dict)
                except (ValueError, TypeError, KeyError):
                    continue
        return None
    
    def get_all_achievements(self, user_id: Optional[str] = None) -> list[Achievement]:
        """Get all achievements as Achievement objects, optionally filtered by user_id"""
        achievements_data = self.load_achievements(user_id)
        achievements = []
        for achievement_data in achievements_data:
            try:
                # Remove user_id before creating Achievement object
                achievement_dict = {k: v for k, v in achievement_data.items() if k != 'user_id'}
                achievements.append(Achievement(**achievement_dict))
            except (ValueError, TypeError, KeyError):
                # Skip invalid achievements
                continue
        return achievements
    
    def delete_achievement(self, achievement_id: str, user_id: str) -> bool:
        """Delete an achievement by ID for a user"""
        achievements = self.load_achievements()  # Load all
        original_length = len(achievements)
        achievements = [a for a in achievements if not (a.get('id') == achievement_id and a.get('user_id') == user_id)]
        
        if len(achievements) < original_length:
            self._save_achievements(achievements)
            return True
        return False
    
    # Club History methods
    def _save_club_history(self, club_history: list) -> None:
        """Save club history to JSON file"""
        try:
            with open(self.club_history_file, 'w', encoding='utf-8') as f:
                json.dump(club_history, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save club history: {str(e)}")
    
    def load_club_history(self, user_id: Optional[str] = None) -> list:
        """Load club history from JSON file, optionally filtered by user_id"""
        try:
            with open(self.club_history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                history = data if isinstance(data, list) else []
                if user_id:
                    history = [h for h in history if h.get('user_id') == user_id]
                return history
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_club_history_entry(self, club_history: ClubHistory, user_id: str) -> str:
        """Save a single club history entry and return its ID"""
        history = self.load_club_history()  # Load all
        
        # Check if entry with this ID already exists (for updates)
        existing_index = None
        for i, existing_entry in enumerate(history):
            if existing_entry.get('id') == club_history.id and existing_entry.get('user_id') == user_id:
                existing_index = i
                break
        
        entry_dict = club_history.model_dump()
        entry_dict['user_id'] = user_id
        
        if existing_index is not None:
            history[existing_index] = entry_dict
        else:
            history.append(entry_dict)
        
        self._save_club_history(history)
        return club_history.id
    
    def get_club_history_entry(self, entry_id: str, user_id: str) -> Optional[ClubHistory]:
        """Get a specific club history entry by ID for a user"""
        history = self.load_club_history(user_id)
        for entry_data in history:
            if entry_data.get('id') == entry_id:
                try:
                    # Remove user_id before creating ClubHistory object
                    entry_dict = {k: v for k, v in entry_data.items() if k != 'user_id'}
                    return ClubHistory(**entry_dict)
                except (ValueError, TypeError, KeyError):
                    continue
        return None
    
    def get_all_club_history(self, user_id: Optional[str] = None) -> list[ClubHistory]:
        """Get all club history entries as ClubHistory objects, optionally filtered by user_id"""
        history_data = self.load_club_history(user_id)
        history = []
        for entry_data in history_data:
            try:
                # Remove user_id before creating ClubHistory object
                entry_dict = {k: v for k, v in entry_data.items() if k != 'user_id'}
                history.append(ClubHistory(**entry_dict))
            except (ValueError, TypeError, KeyError):
                # Skip invalid entries
                continue
        return history
    
    def delete_club_history_entry(self, entry_id: str, user_id: str) -> bool:
        """Delete a club history entry by ID for a user"""
        history = self.load_club_history()  # Load all
        original_length = len(history)
        history = [h for h in history if not (h.get('id') == entry_id and h.get('user_id') == user_id)]
        
        if len(history) < original_length:
            self._save_club_history(history)
            return True
        return False
    
    # Training Camp methods
    def _save_training_camps(self, training_camps: list) -> None:
        """Save training camps to JSON file"""
        try:
            with open(self.training_camps_file, 'w', encoding='utf-8') as f:
                json.dump(training_camps, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save training camps: {str(e)}")
    
    def load_training_camps(self, user_id: Optional[str] = None) -> list:
        """Load training camps from JSON file, optionally filtered by user_id"""
        try:
            with open(self.training_camps_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                camps = data if isinstance(data, list) else []
                if user_id:
                    camps = [c for c in camps if c.get('user_id') == user_id]
                return camps
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_training_camp(self, training_camp: TrainingCamp, user_id: str) -> str:
        """Save a single training camp entry and return its ID"""
        camps = self.load_training_camps()  # Load all
        
        # Check if camp with this ID already exists (for updates)
        existing_index = None
        for i, existing_camp in enumerate(camps):
            if existing_camp.get('id') == training_camp.id and existing_camp.get('user_id') == user_id:
                existing_index = i
                break
        
        camp_dict = training_camp.model_dump()
        camp_dict['user_id'] = user_id
        
        if existing_index is not None:
            camps[existing_index] = camp_dict
        else:
            camps.append(camp_dict)
        
        self._save_training_camps(camps)
        return training_camp.id
    
    def get_training_camp(self, camp_id: str, user_id: str) -> Optional[TrainingCamp]:
        """Get a specific training camp entry by ID for a user"""
        camps = self.load_training_camps(user_id)
        for camp_data in camps:
            if camp_data.get('id') == camp_id:
                try:
                    # Remove user_id before creating TrainingCamp object
                    camp_dict = {k: v for k, v in camp_data.items() if k != 'user_id'}
                    return TrainingCamp(**camp_dict)
                except (ValueError, TypeError, KeyError):
                    continue
        return None
    
    def get_all_training_camps(self, user_id: Optional[str] = None) -> list[TrainingCamp]:
        """Get all training camp entries as TrainingCamp objects, optionally filtered by user_id"""
        camps_data = self.load_training_camps(user_id)
        camps = []
        for camp_data in camps_data:
            try:
                # Remove user_id before creating TrainingCamp object
                camp_dict = {k: v for k, v in camp_data.items() if k != 'user_id'}
                camps.append(TrainingCamp(**camp_dict))
            except (ValueError, TypeError, KeyError):
                continue
        return camps
    
    def delete_training_camp(self, camp_id: str, user_id: str) -> bool:
        """Delete a training camp entry by ID for a user"""
        camps = self.load_training_camps()  # Load all
        original_length = len(camps)
        camps = [c for c in camps if not (c.get('id') == camp_id and c.get('user_id') == user_id)]
        
        if len(camps) < original_length:
            self._save_training_camps(camps)
            return True
        return False
    
    # Physical Metrics methods
    def _save_physical_metrics(self, metrics: list) -> None:
        """Save physical metrics to JSON file"""
        try:
            with open(self.physical_metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save physical metrics: {str(e)}")
    
    def load_physical_metrics(self, user_id: Optional[str] = None) -> list:
        """Load physical metrics from JSON file, optionally filtered by user_id"""
        try:
            with open(self.physical_metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                metrics = data if isinstance(data, list) else []
                if user_id:
                    metrics = [m for m in metrics if m.get('user_id') == user_id]
                return metrics
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_physical_metric(self, metric: PhysicalMetrics, user_id: str) -> str:
        """Save a single physical metric entry and return its ID"""
        metrics = self.load_physical_metrics()  # Load all
        
        # Check if metric with this ID already exists (for updates)
        existing_index = None
        for i, existing_metric in enumerate(metrics):
            if existing_metric.get('id') == metric.id and existing_metric.get('user_id') == user_id:
                existing_index = i
                break
        
        metric_dict = metric.model_dump()
        metric_dict['user_id'] = user_id
        
        if existing_index is not None:
            metrics[existing_index] = metric_dict
        else:
            metrics.append(metric_dict)
        
        self._save_physical_metrics(metrics)
        return metric.id
    
    def get_physical_metric(self, metric_id: str, user_id: str) -> Optional[PhysicalMetrics]:
        """Get a specific physical metric entry by ID for a user"""
        metrics = self.load_physical_metrics(user_id)
        for metric_data in metrics:
            if metric_data.get('id') == metric_id:
                try:
                    # Remove user_id before creating PhysicalMetrics object
                    metric_dict = {k: v for k, v in metric_data.items() if k != 'user_id'}
                    return PhysicalMetrics(**metric_dict)
                except (ValueError, TypeError, KeyError):
                    continue
        return None
    
    def get_all_physical_metrics(self, user_id: Optional[str] = None) -> list[PhysicalMetrics]:
        """Get all physical metric entries as PhysicalMetrics objects, optionally filtered by user_id"""
        metrics_data = self.load_physical_metrics(user_id)
        metrics = []
        for metric_data in metrics_data:
            try:
                # Remove user_id before creating PhysicalMetrics object
                metric_dict = {k: v for k, v in metric_data.items() if k != 'user_id'}
                metrics.append(PhysicalMetrics(**metric_dict))
            except (ValueError, TypeError, KeyError):
                continue
        return metrics
    
    def delete_physical_metric(self, metric_id: str, user_id: str) -> bool:
        """Delete a physical metric entry by ID for a user"""
        metrics = self.load_physical_metrics()  # Load all
        original_length = len(metrics)
        metrics = [m for m in metrics if not (m.get('id') == metric_id and m.get('user_id') == user_id)]
        
        if len(metrics) < original_length:
            self._save_physical_metrics(metrics)
            return True
        return False
    
    # User management methods
    def _save_users(self, users: list) -> None:
        """Save users to JSON file"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save users: {str(e)}")
    
    def load_users(self) -> list:
        """Load users from JSON file"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def create_user(self, username: str, password: str, email: Optional[str] = None) -> Optional[User]:
        """Create a new user"""
        # Check if username already exists
        users = self.load_users()
        for user_data in users:
            if user_data.get('username') == username:
                return None  # Username already exists
        
        # Create new user
        password_hash = generate_password_hash(password)
        user = User(
            username=username,
            password_hash=password_hash,
            email=email
        )
        
        # Save user
        users.append(user.model_dump())
        self._save_users(users)
        
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username (case-sensitive exact match)"""
        if not username:
            return None
        username = username.strip()
        users = self.load_users()
        for user_data in users:
            # Exact match (case-sensitive)
            if user_data.get('username', '').strip() == username:
                try:
                    return User(**user_data)
                except (ValueError, TypeError, KeyError):
                    continue
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        users = self.load_users()
        for user_data in users:
            if user_data.get('id') == user_id:
                try:
                    return User(**user_data)
                except (ValueError, TypeError, KeyError):
                    continue
        return None
    
    def get_all_users(self) -> list[User]:
        """Get all users as User objects"""
        users = self.load_users()
        result = []
        for user_data in users:
            try:
                result.append(User(**user_data))
            except (ValueError, TypeError, KeyError):
                continue
        return result
    
    def verify_password(self, user: User, password: str) -> bool:
        """Verify a user's password"""
        try:
            if not user.password_hash:
                return False
            return check_password_hash(user.password_hash, password)
        except ValueError:
            # Invalid hash format - treat as authentication failure
            return False
    
    # Subscription management methods
    def _save_subscriptions(self, subscriptions: list) -> None:
        """Save subscriptions to JSON file"""
        try:
            with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
                json.dump(subscriptions, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save subscriptions: {str(e)}")
    
    def load_subscriptions(self) -> list:
        """Load subscriptions from JSON file"""
        try:
            with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def get_subscription_by_user_id(self, user_id: str) -> Optional[Subscription]:
        """Get subscription for a user - tries multiple user ID formats"""
        subscriptions = self.load_subscriptions()
        
        # Try exact match first
        for sub_data in subscriptions:
            if sub_data.get('user_id') == user_id:
                try:
                    # Ensure status is properly converted to enum
                    if 'status' in sub_data and isinstance(sub_data['status'], str):
                        try:
                            from .models import SubscriptionStatus
                            sub_data['status'] = SubscriptionStatus(sub_data['status'].lower())
                        except (ValueError, AttributeError):
                            pass  # Will use default from model
                    return Subscription(**sub_data)
                except (ValueError, TypeError, KeyError) as e:
                    import traceback
                    print(f"Error loading subscription for user {user_id}: {e}")
                    traceback.print_exc()
                    continue
        
        # If no exact match, try to find subscription by Stripe customer ID
        # This handles cases where user_id format changed
        # First, try to get user by ID to see if we can find a match
        user = self.get_user_by_id(user_id)
        if user:
            # Check if any subscription might belong to this user
            # (e.g., by username or email if stored in metadata)
            # For now, return None if no exact match
            pass
        
        return None
    
    def get_subscription_by_stripe_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID"""
        subscriptions = self.load_subscriptions()
        for sub_data in subscriptions:
            if sub_data.get('stripe_subscription_id') == stripe_subscription_id:
                try:
                    return Subscription(**sub_data)
                except (ValueError, TypeError, KeyError):
                    continue
        return None
    
    def save_subscription(self, subscription: Subscription) -> Subscription:
        """Save or update a subscription"""
        subscriptions = self.load_subscriptions()
        
        # Find existing subscription
        found = False
        for idx, sub_data in enumerate(subscriptions):
            if sub_data.get('user_id') == subscription.user_id:
                subscriptions[idx] = subscription.model_dump()
                found = True
                break
        
        if not found:
            subscriptions.append(subscription.model_dump())
        
        self._save_subscriptions(subscriptions)
        return subscription
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user and all their associated data"""
        try:
            # Load users
            users = self.load_users()
            
            # Find and remove user
            user_found = False
            updated_users = []
            for user_data in users:
                if user_data.get('id') == user_id:
                    user_found = True
                    # Don't add this user to updated_users (effectively deleting it)
                    continue
                updated_users.append(user_data)
            
            if not user_found:
                return False
            
            # Save updated users list
            self._save_users(updated_users)
            
            # Delete all user-associated data
            # Delete matches
            matches = self.load_matches()
            updated_matches = [m for m in matches if m.get('user_id') != user_id]
            if len(updated_matches) != len(matches):
                self._save_matches(updated_matches)
            
            # Delete settings
            try:
                settings_file = self.data_dir / f"settings_{user_id}.json"
                if settings_file.exists():
                    settings_file.unlink()
            except Exception:
                pass
            
            # Delete physical measurements
            measurements = self.load_physical_measurements()
            updated_measurements = [m for m in measurements if m.get('user_id') != user_id]
            if len(updated_measurements) != len(measurements):
                self._save_physical_measurements(updated_measurements)
            
            # Delete achievements
            achievements = self.load_achievements()
            updated_achievements = [a for a in achievements if a.get('user_id') != user_id]
            if len(updated_achievements) != len(achievements):
                self._save_achievements(updated_achievements)
            
            # Delete club history
            club_history = self.load_club_history()
            updated_club_history = [c for c in club_history if c.get('user_id') != user_id]
            if len(updated_club_history) != len(club_history):
                self._save_club_history(updated_club_history)
            
            # Delete training camps
            training_camps = self.load_training_camps()
            updated_training_camps = [t for t in training_camps if t.get('user_id') != user_id]
            if len(updated_training_camps) != len(training_camps):
                self._save_training_camps(updated_training_camps)
            
            # Delete physical metrics
            physical_metrics = self.load_physical_metrics()
            updated_physical_metrics = [p for p in physical_metrics if p.get('user_id') != user_id]
            if len(updated_physical_metrics) != len(physical_metrics):
                self._save_physical_metrics(updated_physical_metrics)
            
            # Delete subscription
            self.delete_subscription(user_id)
            
            # Delete references
            references = self.load_references()
            updated_references = [r for r in references if r.get('user_id') != user_id]
            if len(updated_references) != len(references):
                self._save_references(updated_references)
            
            # Delete reset tokens (if any exist for this user)
            try:
                reset_tokens = self._load_reset_tokens()
                updated_tokens = []
                for token_data in reset_tokens:
                    # Check if token belongs to this user
                    token_user_id = token_data.get('user_id', '')
                    if token_user_id == user_id:
                        continue  # Skip this token
                    updated_tokens.append(token_data)
                if len(updated_tokens) != len(reset_tokens):
                    self._save_reset_tokens(updated_tokens)
            except Exception as e:
                # Reset tokens deletion is optional, don't fail if it errors
                import traceback
                traceback.print_exc()
                pass
            
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    
    def delete_subscription(self, user_id: str) -> bool:
        """Delete a subscription"""
        subscriptions = self.load_subscriptions()
        original_count = len(subscriptions)
        subscriptions = [s for s in subscriptions if s.get('user_id') != user_id]
        
        if len(subscriptions) < original_count:
            self._save_subscriptions(subscriptions)
            return True
        return False
    
    # ========== References ==========
    def _save_references(self, references: list) -> None:
        """Save references to JSON file"""
        try:
            with open(self.references_file, 'w', encoding='utf-8') as f:
                json.dump(references, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving references: {e}")
    
    def load_references(self, user_id: Optional[str] = None) -> list:
        """Load references, optionally filtered by user_id"""
        try:
            if not self.references_file.exists():
                return []
            with open(self.references_file, 'r', encoding='utf-8') as f:
                references = json.load(f)
                if user_id:
                    references = [r for r in references if r.get('user_id') == user_id]
                return references
        except Exception as e:
            print(f"Error loading references: {e}")
            return []
    
    def get_reference(self, reference_id: str, user_id: Optional[str] = None) -> Optional[Reference]:
        """Get a reference by ID"""
        references = self.load_references(user_id)
        for ref_data in references:
            if ref_data.get('id') == reference_id:
                return Reference(**ref_data)
        return None
    
    def save_reference(self, reference: Reference) -> Reference:
        """Save or update a reference"""
        references = self.load_references()
        # Find existing reference
        existing_index = None
        for i, ref_data in enumerate(references):
            if ref_data.get('id') == reference.id:
                existing_index = i
                break
        
        # Update or add
        ref_dict = reference.dict()
        if existing_index is not None:
            references[existing_index] = ref_dict
        else:
            references.append(ref_dict)
        
        self._save_references(references)
        return reference
    
    def delete_reference(self, reference_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a reference"""
        references = self.load_references(user_id)
        original_count = len(references)
        references = [r for r in references if r.get('id') != reference_id]
        
        if len(references) < original_count:
            self._save_references(references)
            return True
        return False
    
    # Password reset token management
    def _load_reset_tokens(self) -> list:
        """Load reset tokens from JSON file"""
        try:
            if not self.reset_tokens_file.exists():
                return []
            with open(self.reset_tokens_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_reset_tokens(self, tokens: list) -> None:
        """Save reset tokens to JSON file"""
        try:
            with open(self.reset_tokens_file, 'w', encoding='utf-8') as f:
                json.dump(tokens, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save reset tokens: {str(e)}")
    
    def create_reset_token(self, user_id: str, token: str, expires_at: str) -> bool:
        """Create a password reset token"""
        tokens = self._load_reset_tokens()
        # Remove any existing tokens for this user
        tokens = [t for t in tokens if t.get('user_id') != user_id]
        # Add new token
        tokens.append({
            'user_id': user_id,
            'token': token,
            'expires_at': expires_at,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self._save_reset_tokens(tokens)
        return True
    
    def get_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get reset token info if valid"""
        tokens = self._load_reset_tokens()
        for token_data in tokens:
            if token_data.get('token') == token:
                # Check if expired
                try:
                    expires_at = datetime.strptime(token_data['expires_at'], "%Y-%m-%d %H:%M:%S")
                    if datetime.now() < expires_at:
                        return token_data
                    else:
                        # Token expired, remove it
                        tokens.remove(token_data)
                        self._save_reset_tokens(tokens)
                except (ValueError, KeyError):
                    # Invalid date format, remove token
                    tokens.remove(token_data)
                    self._save_reset_tokens(tokens)
        return None
    
    def delete_reset_token(self, token: str) -> bool:
        """Delete a reset token (after use)"""
        tokens = self._load_reset_tokens()
        original_count = len(tokens)
        tokens = [t for t in tokens if t.get('token') != token]
        if len(tokens) < original_count:
            self._save_reset_tokens(tokens)
            return True
        return False
    
    def update_user_password(self, user_id: str, new_password: str) -> bool:
        """Update a user's password"""
        users = self.load_users()
        for user_data in users:
            if user_data.get('id') == user_id:
                user_data['password_hash'] = generate_password_hash(new_password)
                self._save_users(users)
                return True
        return False
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address"""
        if not email:
            return None
        users = self.load_users()
        for user_data in users:
            if user_data.get('email') and user_data.get('email').lower() == email.lower():
                try:
                    return User(**user_data)
                except (ValueError, TypeError, KeyError):
                    continue
        return None

