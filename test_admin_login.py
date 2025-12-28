#!/usr/bin/env python3
"""
Test script to verify admin login credentials
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.storage import StorageManager
from werkzeug.security import check_password_hash

def test_admin_login():
    """Test admin login credentials"""
    storage = StorageManager()
    
    username = "Admin_Chris1903_FutureElite"
    password = "bBrodie@x2027"
    
    print("Testing Admin Login Credentials")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Password: {password}")
    print("=" * 60)
    
    # Test username lookup
    user = storage.get_user_by_username(username)
    
    if not user:
        print("\n❌ ERROR: User not found!")
        print(f"   Searched for: '{username}'")
        print("\n   Available users:")
        all_users = storage.get_all_users()
        for u in all_users:
            if 'Admin' in u.username or 'admin' in u.username.lower():
                print(f"   - '{u.username}' (ID: {u.id})")
        return False
    
    print(f"\n✓ User found: {user.username}")
    print(f"  User ID: {user.id}")
    print(f"  Email: {user.email or 'None'}")
    print(f"  Active: {user.is_active}")
    
    # Test password
    if not user.password_hash:
        print("\n❌ ERROR: User has no password hash!")
        return False
    
    print(f"\n✓ Password hash exists")
    print(f"  Hash type: {user.password_hash.split(':')[0]}")
    
    # Verify password
    password_valid = check_password_hash(user.password_hash, password)
    
    if password_valid:
        print(f"\n✓ Password verification: SUCCESS")
        print("\n" + "=" * 60)
        print("✅ Admin credentials are CORRECT!")
        print("=" * 60)
        print("\nIf login still fails:")
        print("  1. Restart your Flask server")
        print("  2. Clear browser cache/cookies")
        print("  3. Try in incognito/private mode")
        print("  4. Check browser console for errors")
        return True
    else:
        print(f"\n❌ Password verification: FAILED")
        print("\n" + "=" * 60)
        print("❌ Password is INCORRECT!")
        print("=" * 60)
        print("\nThe password hash doesn't match the provided password.")
        print("Run: python create_admin_user.py to reset the password.")
        return False

if __name__ == "__main__":
    try:
        success = test_admin_login()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

