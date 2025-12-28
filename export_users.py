#!/usr/bin/env python3
"""
Export all registered users to a JSON file
Usage: python export_users.py [output_file.json]
"""

import json
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.storage import StorageManager

def export_users(output_file='users_export.json'):
    """Export all users to a JSON file"""
    storage = StorageManager()
    users = storage.get_all_users()
    
    # Remove password hashes for security
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at,
            'is_active': user.is_active
        })
    
    # Sort by creation date (newest first)
    users_data.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=2, ensure_ascii=False)
    
    print(f"Exported {len(users_data)} users to {output_file}")
    print(f"\nUsers:")
    for user in users_data:
        email = user['email'] or 'No email'
        print(f"  - {user['username']} ({email}) - Registered: {user['created_at']}")
    
    return users_data

if __name__ == '__main__':
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'users_export.json'
    export_users(output_file)

