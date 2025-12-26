#!/usr/bin/env python3
"""
WSGI Entry Point for Production Deployment
Use with: gunicorn wsgi:app
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')

# Import application factory
from app.main import create_app

# Create application instance
app = create_app()

if __name__ == '__main__':
    # This should not be used in production - use gunicorn instead
    # Kept for development/testing only
    app.run(host='0.0.0.0', port=8080, debug=False)

