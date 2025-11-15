import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .models import MatchData, Match, AppSettings, PhysicalMeasurement, MatchResult, Achievement, ClubHistory, TrainingCamp, PhysicalMetrics


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
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()

    def _initialize_files(self):
        """Initialize JSON files with default data if they don't exist"""
        if not self.matches_file.exists():
            self._save_matches([])
        
        if not self.settings_file.exists():
            default_settings = AppSettings()
            self._save_settings(default_settings)
        
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

    def _save_matches(self, matches: list) -> None:
        """Save matches to JSON file"""
        try:
            with open(self.matches_file, 'w', encoding='utf-8') as f:
                json.dump(matches, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save matches: {str(e)}")

    def _save_settings(self, settings: AppSettings) -> None:
        """Save settings to JSON file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings.model_dump(), f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save settings: {str(e)}")

    def load_matches(self) -> list:
        """Load matches from JSON file"""
        try:
            with open(self.matches_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def load_settings(self) -> AppSettings:
        """Load settings from JSON file"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return AppSettings(**data)
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return AppSettings()

    def save_match(self, match: Match) -> str:
        """Save a single match and return its ID"""
        matches = self.load_matches()
        
        # Check if match with this ID already exists (for updates)
        existing_index = None
        for i, existing_match in enumerate(matches):
            if existing_match.get('id') == match.id:
                existing_index = i
                break
        
        match_dict = match.model_dump()
        
        if existing_index is not None:
            matches[existing_index] = match_dict
        else:
            matches.append(match_dict)
        
        self._save_matches(matches)
        return match.id

    def get_match(self, match_id: str) -> Optional[Match]:
        """Get a specific match by ID"""
        matches = self.load_matches()
        for match_data in matches:
            if match_data.get('id') == match_id:
                try:
                    return Match(**match_data)
                except (ValueError, TypeError, KeyError) as e:
                    # Log invalid match data but continue
                    continue
        return None

    def delete_match(self, match_id: str) -> bool:
        """Delete a match by ID"""
        matches = self.load_matches()
        original_length = len(matches)
        matches = [m for m in matches if m.get('id') != match_id]
        
        if len(matches) < original_length:
            self._save_matches(matches)
            return True
        return False

    def get_all_matches(self) -> list[Match]:
        """Get all matches as Match objects"""
        matches_data = self.load_matches()
        matches = []
        for match_data in matches_data:
            try:
                matches.append(Match(**match_data))
            except (ValueError, TypeError, KeyError):
                # Skip invalid matches
                continue
        return matches

    def get_matches_by_category(self, category: str) -> list[Match]:
        """Get matches filtered by category"""
        all_matches = self.get_all_matches()
        return [m for m in all_matches if m.category.value == category]

    def get_fixtures(self) -> list[Match]:
        """Get upcoming fixtures (matches with is_fixture=True)"""
        all_matches = self.get_all_matches()
        return [m for m in all_matches if m.is_fixture]

    def get_completed_matches(self) -> list[Match]:
        """Get completed matches (is_fixture=False)"""
        all_matches = self.get_all_matches()
        return [m for m in all_matches if not m.is_fixture]

    def save_settings(self, settings: AppSettings) -> None:
        """Save settings"""
        self._save_settings(settings)

    def export_data(self) -> Dict[str, Any]:
        """Export all data as a dictionary for backup"""
        return {
            "matches": self.load_matches(),
            "settings": self.load_settings().model_dump(),
            "physical_measurements": self.load_physical_measurements(),
            "achievements": self.load_achievements(),
            "club_history": self.load_club_history(),
            "training_camps": self.load_training_camps(),
            "physical_metrics": self.load_physical_metrics(),
            "exported_at": datetime.now().isoformat()
        }

    def import_data(self, data: Dict[str, Any]) -> bool:
        """Import data from backup dictionary"""
        try:
            if "matches" in data:
                if not isinstance(data["matches"], list):
                    return False
                self._save_matches(data["matches"])
            
            if "settings" in data:
                if not isinstance(data["settings"], dict):
                    return False
                settings = AppSettings(**data["settings"])
                self._save_settings(settings)
            
            if "physical_measurements" in data:
                if not isinstance(data["physical_measurements"], list):
                    return False
                self._save_physical_measurements(data["physical_measurements"])
            
            if "achievements" in data:
                if not isinstance(data["achievements"], list):
                    return False
                self._save_achievements(data["achievements"])
            
            if "club_history" in data:
                if not isinstance(data["club_history"], list):
                    return False
                self._save_club_history(data["club_history"])
            
            if "training_camps" in data:
                if not isinstance(data["training_camps"], list):
                    return False
                self._save_training_camps(data["training_camps"])
            
            if "physical_metrics" in data:
                if not isinstance(data["physical_metrics"], list):
                    return False
                self._save_physical_metrics(data["physical_metrics"])
            
            return True
        except (ValueError, TypeError, KeyError) as e:
            # Log error in production
            return False

    def get_season_stats(self) -> Dict[str, Any]:
        """Calculate season statistics"""
        completed_matches = self.get_completed_matches()
        
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

    def get_category_stats(self, category: str) -> Dict[str, Any]:
        """Calculate statistics for a specific category"""
        category_matches = self.get_matches_by_category(category)
        
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
    
    def load_physical_measurements(self) -> list:
        """Load physical measurements from JSON file"""
        try:
            with open(self.physical_measurements_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_physical_measurement(self, measurement: PhysicalMeasurement) -> str:
        """Save a single physical measurement and return its ID"""
        measurements = self.load_physical_measurements()
        
        # Check if measurement with this ID already exists (for updates)
        existing_index = None
        for i, existing_measurement in enumerate(measurements):
            if existing_measurement.get('id') == measurement.id:
                existing_index = i
                break
        
        measurement_dict = measurement.model_dump()
        
        if existing_index is not None:
            measurements[existing_index] = measurement_dict
        else:
            measurements.append(measurement_dict)
        
        self._save_physical_measurements(measurements)
        return measurement.id
    
    def get_physical_measurement(self, measurement_id: str) -> Optional[PhysicalMeasurement]:
        """Get a specific physical measurement by ID"""
        measurements = self.load_physical_measurements()
        for measurement_data in measurements:
            if measurement_data.get('id') == measurement_id:
                try:
                    return PhysicalMeasurement(**measurement_data)
                except (ValueError, TypeError, KeyError):
                    continue
        return None
    
    def get_all_physical_measurements(self) -> list[PhysicalMeasurement]:
        """Get all physical measurements as PhysicalMeasurement objects"""
        measurements_data = self.load_physical_measurements()
        measurements = []
        for measurement_data in measurements_data:
            try:
                measurements.append(PhysicalMeasurement(**measurement_data))
            except (ValueError, TypeError, KeyError):
                # Skip invalid measurements
                continue
        return measurements
    
    def delete_physical_measurement(self, measurement_id: str) -> bool:
        """Delete a physical measurement by ID"""
        measurements = self.load_physical_measurements()
        original_length = len(measurements)
        measurements = [m for m in measurements if m.get('id') != measurement_id]
        
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
    
    def load_achievements(self) -> list:
        """Load achievements from JSON file"""
        try:
            with open(self.achievements_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_achievement(self, achievement: Achievement) -> str:
        """Save a single achievement and return its ID"""
        achievements = self.load_achievements()
        
        # Check if achievement with this ID already exists (for updates)
        existing_index = None
        for i, existing_achievement in enumerate(achievements):
            if existing_achievement.get('id') == achievement.id:
                existing_index = i
                break
        
        achievement_dict = achievement.model_dump()
        
        if existing_index is not None:
            achievements[existing_index] = achievement_dict
        else:
            achievements.append(achievement_dict)
        
        self._save_achievements(achievements)
        return achievement.id
    
    def get_achievement(self, achievement_id: str) -> Optional[Achievement]:
        """Get a specific achievement by ID"""
        achievements = self.load_achievements()
        for achievement_data in achievements:
            if achievement_data.get('id') == achievement_id:
                try:
                    return Achievement(**achievement_data)
                except (ValueError, TypeError, KeyError):
                    continue
        return None
    
    def get_all_achievements(self) -> list[Achievement]:
        """Get all achievements as Achievement objects"""
        achievements_data = self.load_achievements()
        achievements = []
        for achievement_data in achievements_data:
            try:
                achievements.append(Achievement(**achievement_data))
            except (ValueError, TypeError, KeyError):
                # Skip invalid achievements
                continue
        return achievements
    
    def delete_achievement(self, achievement_id: str) -> bool:
        """Delete an achievement by ID"""
        achievements = self.load_achievements()
        original_length = len(achievements)
        achievements = [a for a in achievements if a.get('id') != achievement_id]
        
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
    
    def load_club_history(self) -> list:
        """Load club history from JSON file"""
        try:
            with open(self.club_history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_club_history_entry(self, club_history: ClubHistory) -> str:
        """Save a single club history entry and return its ID"""
        history = self.load_club_history()
        
        # Check if entry with this ID already exists (for updates)
        existing_index = None
        for i, existing_entry in enumerate(history):
            if existing_entry.get('id') == club_history.id:
                existing_index = i
                break
        
        entry_dict = club_history.model_dump()
        
        if existing_index is not None:
            history[existing_index] = entry_dict
        else:
            history.append(entry_dict)
        
        self._save_club_history(history)
        return club_history.id
    
    def get_club_history_entry(self, entry_id: str) -> Optional[ClubHistory]:
        """Get a specific club history entry by ID"""
        history = self.load_club_history()
        for entry_data in history:
            if entry_data.get('id') == entry_id:
                try:
                    return ClubHistory(**entry_data)
                except (ValueError, TypeError, KeyError):
                    continue
        return None
    
    def get_all_club_history(self) -> list[ClubHistory]:
        """Get all club history entries as ClubHistory objects"""
        history_data = self.load_club_history()
        history = []
        for entry_data in history_data:
            try:
                history.append(ClubHistory(**entry_data))
            except (ValueError, TypeError, KeyError):
                # Skip invalid entries
                continue
        return history
    
    def delete_club_history_entry(self, entry_id: str) -> bool:
        """Delete a club history entry by ID"""
        history = self.load_club_history()
        original_length = len(history)
        history = [h for h in history if h.get('id') != entry_id]
        
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
    
    def load_training_camps(self) -> list:
        """Load training camps from JSON file"""
        try:
            with open(self.training_camps_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_training_camp(self, training_camp: TrainingCamp) -> str:
        """Save a single training camp entry and return its ID"""
        camps = self.load_training_camps()
        
        # Check if camp with this ID already exists (for updates)
        existing_index = None
        for i, existing_camp in enumerate(camps):
            if existing_camp.get('id') == training_camp.id:
                existing_index = i
                break
        
        camp_dict = training_camp.model_dump()
        
        if existing_index is not None:
            camps[existing_index] = camp_dict
        else:
            camps.append(camp_dict)
        
        self._save_training_camps(camps)
        return training_camp.id
    
    def get_training_camp(self, camp_id: str) -> Optional[TrainingCamp]:
        """Get a specific training camp entry by ID"""
        camps = self.load_training_camps()
        for camp_data in camps:
            if camp_data.get('id') == camp_id:
                try:
                    return TrainingCamp(**camp_data)
                except (ValueError, TypeError, KeyError):
                    continue
        return None
    
    def get_all_training_camps(self) -> list[TrainingCamp]:
        """Get all training camp entries as TrainingCamp objects"""
        camps_data = self.load_training_camps()
        camps = []
        for camp_data in camps_data:
            try:
                camps.append(TrainingCamp(**camp_data))
            except (ValueError, TypeError, KeyError):
                continue
        return camps
    
    def delete_training_camp(self, camp_id: str) -> bool:
        """Delete a training camp entry by ID"""
        camps = self.load_training_camps()
        original_length = len(camps)
        camps = [c for c in camps if c.get('id') != camp_id]
        
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
    
    def load_physical_metrics(self) -> list:
        """Load physical metrics from JSON file"""
        try:
            with open(self.physical_metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_physical_metric(self, metric: PhysicalMetrics) -> str:
        """Save a single physical metric entry and return its ID"""
        metrics = self.load_physical_metrics()
        
        # Check if metric with this ID already exists (for updates)
        existing_index = None
        for i, existing_metric in enumerate(metrics):
            if existing_metric.get('id') == metric.id:
                existing_index = i
                break
        
        metric_dict = metric.model_dump()
        
        if existing_index is not None:
            metrics[existing_index] = metric_dict
        else:
            metrics.append(metric_dict)
        
        self._save_physical_metrics(metrics)
        return metric.id
    
    def get_physical_metric(self, metric_id: str) -> Optional[PhysicalMetrics]:
        """Get a specific physical metric entry by ID"""
        metrics = self.load_physical_metrics()
        for metric_data in metrics:
            if metric_data.get('id') == metric_id:
                try:
                    return PhysicalMetrics(**metric_data)
                except (ValueError, TypeError, KeyError):
                    continue
        return None
    
    def get_all_physical_metrics(self) -> list[PhysicalMetrics]:
        """Get all physical metric entries as PhysicalMetrics objects"""
        metrics_data = self.load_physical_metrics()
        metrics = []
        for metric_data in metrics_data:
            try:
                metrics.append(PhysicalMetrics(**metric_data))
            except (ValueError, TypeError, KeyError):
                continue
        return metrics
    
    def delete_physical_metric(self, metric_id: str) -> bool:
        """Delete a physical metric entry by ID"""
        metrics = self.load_physical_metrics()
        original_length = len(metrics)
        metrics = [m for m in metrics if m.get('id') != metric_id]
        
        if len(metrics) < original_length:
            self._save_physical_metrics(metrics)
            return True
        return False

