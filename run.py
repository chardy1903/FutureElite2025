#!/usr/bin/env python3
"""
FutureElite Tracker - Main Entry Point
Privacy-First Youth Football Match Tracker for Brodie Hardy (Al Qadsiah U12)
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.main import main

if __name__ == '__main__':
    main()








