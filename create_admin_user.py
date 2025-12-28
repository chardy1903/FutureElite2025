#!/usr/bin/env python3
"""
Script to create or update the admin user
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.storage import StorageManager
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create or update the admin user"""
    storage = StorageManager()
    
    admin_username = "Admin_Chris1903_FutureElite"
    admin_password = "bBrodie@x2027"
    
    # Check if admin user already exists
    existing_user = storage.get_user_by_username(admin_username)
    
    if existing_user:
        # Update password
        print(f"Admin user '{admin_username}' already exists. Updating password...")
        if storage.update_user_password(existing_user.id, admin_password):
            print(f"✓ Password updated successfully for admin user '{admin_username}'")
        else:
            print(f"✗ Failed to update password for admin user")
            return False
    else:
        # Create new admin user
        print(f"Creating admin user '{admin_username}'...")
        user = storage.create_user(admin_username, admin_password, email=None)
        if user:
            print(f"✓ Admin user '{admin_username}' created successfully")
            print(f"  User ID: {user.id}")
        else:
            print(f"✗ Failed to create admin user")
            return False
    
    # Set ADMIN_USERNAME in .env file (or create it)
    env_file = Path(".env")
    env_content = ""
    if env_file.exists():
        env_content = env_file.read_text()
    
    # Check if ADMIN_USERNAME is already set
    if "ADMIN_USERNAME" in env_content:
        # Update existing ADMIN_USERNAME
        lines = env_content.split('\n')
        updated_lines = []
        for line in lines:
            if line.startswith("ADMIN_USERNAME="):
                updated_lines.append(f"ADMIN_USERNAME={admin_username}")
            else:
                updated_lines.append(line)
        env_content = '\n'.join(updated_lines)
    else:
        # Add ADMIN_USERNAME
        if env_content and not env_content.endswith('\n'):
            env_content += '\n'
        env_content += f"\n# Admin username for admin page access\nADMIN_USERNAME={admin_username}\n"
    
    env_file.write_text(env_content)
    print(f"✓ Updated .env file with ADMIN_USERNAME={admin_username}")
    
    print("\n" + "="*60)
    print("Admin user setup complete!")
    print("="*60)
    print(f"Username: {admin_username}")
    print(f"Password: {admin_password}")
    print(f"\nYou can now:")
    print(f"  1. Log in at /login with the above credentials")
    print(f"  2. Access the admin page at /admin/users")
    print("="*60)
    
    return True

if __name__ == "__main__":
    try:
        create_admin_user()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

