#!/usr/bin/env python3
"""
Migration script to assign existing data to Brodie_Baller user
Run this once to migrate existing data to the new user-based system
"""

import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.storage import StorageManager
from app.models import User
from werkzeug.security import generate_password_hash


def migrate_data():
    """Migrate existing data to Brodie_Baller user"""
    print("Starting migration...")
    
    storage = StorageManager()
    
    # Check if Brodie_Baller user already exists
    existing_user = storage.get_user_by_username("Brodie_Baller")
    if existing_user:
        print("User Brodie_Baller already exists. Skipping user creation.")
        user_id = existing_user.id
    else:
        # Create Brodie_Baller user
        print("Creating user: Brodie_Baller")
        user = storage.create_user("Brodie_Baller", "123456", None)
        if not user:
            print("ERROR: Failed to create user Brodie_Baller")
            return False
        user_id = user.id
        print(f"User created with ID: {user_id}")
    
    # Migrate matches
    print("\nMigrating matches...")
    matches = storage.load_matches()  # Load all matches (no user filter)
    migrated_matches = 0
    for match in matches:
        if not match.get('user_id'):
            match['user_id'] = user_id
            migrated_matches += 1
    if migrated_matches > 0:
        storage._save_matches(matches)
        print(f"Migrated {migrated_matches} matches")
    else:
        print("No matches to migrate")
    
    # Migrate settings
    print("\nMigrating settings...")
    try:
        # Try to load old format settings
        old_settings_file = storage.settings_file
        if old_settings_file.exists():
            import json
            with open(old_settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Check if it's old format (dict with settings) or new format (dict with user_ids)
                if isinstance(data, dict) and 'season_year' in data:
                    # Old format - migrate to new format
                    from app.models import AppSettings
                    settings = AppSettings(**data)
                    storage.save_settings(settings, user_id)
                    print("Migrated settings")
                else:
                    print("Settings already in new format")
    except Exception as e:
        print(f"Settings migration skipped: {e}")
    
    # Migrate physical measurements
    print("\nMigrating physical measurements...")
    measurements = storage.load_physical_measurements()  # Load all
    migrated_measurements = 0
    for measurement in measurements:
        if not measurement.get('user_id'):
            measurement['user_id'] = user_id
            migrated_measurements += 1
    if migrated_measurements > 0:
        storage._save_physical_measurements(measurements)
        print(f"Migrated {migrated_measurements} physical measurements")
    else:
        print("No physical measurements to migrate")
    
    # Migrate achievements
    print("\nMigrating achievements...")
    achievements = storage.load_achievements()  # Load all
    migrated_achievements = 0
    for achievement in achievements:
        if not achievement.get('user_id'):
            achievement['user_id'] = user_id
            migrated_achievements += 1
    if migrated_achievements > 0:
        storage._save_achievements(achievements)
        print(f"Migrated {migrated_achievements} achievements")
    else:
        print("No achievements to migrate")
    
    # Migrate club history
    print("\nMigrating club history...")
    club_history = storage.load_club_history()  # Load all
    migrated_history = 0
    for entry in club_history:
        if not entry.get('user_id'):
            entry['user_id'] = user_id
            migrated_history += 1
    if migrated_history > 0:
        storage._save_club_history(club_history)
        print(f"Migrated {migrated_history} club history entries")
    else:
        print("No club history to migrate")
    
    # Migrate training camps
    print("\nMigrating training camps...")
    training_camps = storage.load_training_camps()  # Load all
    migrated_camps = 0
    for camp in training_camps:
        if not camp.get('user_id'):
            camp['user_id'] = user_id
            migrated_camps += 1
    if migrated_camps > 0:
        storage._save_training_camps(training_camps)
        print(f"Migrated {migrated_camps} training camps")
    else:
        print("No training camps to migrate")
    
    # Migrate physical metrics
    print("\nMigrating physical metrics...")
    metrics = storage.load_physical_metrics()  # Load all
    migrated_metrics = 0
    for metric in metrics:
        if not metric.get('user_id'):
            metric['user_id'] = user_id
            migrated_metrics += 1
    if migrated_metrics > 0:
        storage._save_physical_metrics(metrics)
        print(f"Migrated {migrated_metrics} physical metrics")
    else:
        print("No physical metrics to migrate")
    
    print("\n" + "="*50)
    print("Migration completed successfully!")
    print(f"All data has been assigned to user: Brodie_Baller (ID: {user_id})")
    print("Login credentials:")
    print("  Username: Brodie_Baller")
    print("  Password: 123456")
    print("="*50)
    
    return True


if __name__ == '__main__':
    try:
        migrate_data()
    except Exception as e:
        print(f"\nERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

