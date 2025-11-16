#!/usr/bin/env python3
"""
Installation script for FutureElite
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing FutureElite dependencies...")
    print("=" * 50)
    
    try:
        # Install requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Main installation function"""
    print("FutureElite - Installation")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        print(f"Current version: {sys.version}")
        return 1
    
    print(f"✓ Python version: {sys.version}")
    
    # Install dependencies
    if not install_requirements():
        return 1
    
    print("\n" + "=" * 50)
    print("🎉 Installation complete!")
    print("\nNext steps:")
    print("1. Run the application: python run.py")
    print("2. Or run tests: python test_app.py")
    print("3. Build executables:")
    print("   - Windows: .\\build_windows.ps1")
    print("   - macOS:   ./build_macos.sh")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())









