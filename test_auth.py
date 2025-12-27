#!/usr/bin/env python3
"""
Test script to verify login/register endpoints work without CSRF errors
Run this after starting the Flask app locally
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8080"

def test_register():
    """Test register endpoint"""
    print("Testing /register endpoint...")
    url = f"{BASE_URL}/register"
    payload = {
        "username": f"testuser_{int(__import__('time').time())}",
        "password": "testpass123",
        "email": "test@example.com"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers, allow_redirects=False)
    
    print(f"  Status: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)}")
            print("  ✅ Register endpoint works!")
            return True
        except json.JSONDecodeError:
            print(f"  ❌ Response is not JSON: {response.text[:200]}")
            return False
    elif response.status_code == 400:
        try:
            data = response.json()
            if 'CSRF' in str(data).upper():
                print(f"  ❌ CSRF error: {data}")
                return False
            else:
                print(f"  Response: {json.dumps(data, indent=2)}")
                print("  ⚠️  Register returned 400 (might be validation error)")
                return True  # Not a CSRF error
        except json.JSONDecodeError:
            print(f"  ❌ Response is not JSON: {response.text[:200]}")
            return False
    else:
        print(f"  ❌ Unexpected status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        return False

def test_login():
    """Test login endpoint"""
    print("\nTesting /login endpoint...")
    url = f"{BASE_URL}/login"
    payload = {
        "username": "Brodie_Baller",
        "password": "123456"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers, allow_redirects=False)
    
    print(f"  Status: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    
    if response.status_code in [200, 401]:
        try:
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)}")
            if 'CSRF' not in str(data).upper():
                print("  ✅ Login endpoint works (returns JSON, no CSRF error)!")
                return True
            else:
                print(f"  ❌ CSRF error in response: {data}")
                return False
        except json.JSONDecodeError:
            print(f"  ❌ Response is not JSON: {response.text[:200]}")
            return False
    else:
        print(f"  ❌ Unexpected status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Auth Endpoints (CSRF Exemption Verification)")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print("\nMake sure the Flask app is running on {BASE_URL}")
    print("=" * 60)
    
    register_ok = test_register()
    login_ok = test_login()
    
    print("\n" + "=" * 60)
    if register_ok and login_ok:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

