#!/usr/bin/env python3
"""
WSGI entry point for the Resume Modifier application.
This file is used to run the Flask application in production.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app factory
from core.app import create_app

# Create the Flask application instance
app = create_app()

if __name__ == "__main__":
    # Development server
    with app.app_context():
        from core.app.extensions import db
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)