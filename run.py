#!/usr/bin/env python3
"""
FutureElite - Main Entry Point
Privacy-First Youth Football Match Tracker for Brodie Hardy (Al Qadsiah U12)

Copyright (c) 2025 [Your Name]. All Rights Reserved.
This software is proprietary and confidential. Unauthorized copying, modification,
distribution, or use of this software, via any medium, is strictly prohibited.
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.main import main

if __name__ == '__main__':
    main()








