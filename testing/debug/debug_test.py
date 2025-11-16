#!/usr/bin/env python3

import pytest
import os
import sys

# Add core directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from app import create_app
from app.extensions import db

def test_app_direct():
    """Test app configuration directly"""
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key'
    }
    
    app = create_app(config=test_config)
    
    print(f"App config TESTING: {app.config.get('TESTING')}")
    print(f"App config DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    
    with app.app_context():
        print(f"DB engine URL: {db.engine.url}")
        try:
            db.create_all()
            print("Success: Tables created in SQLite")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    test_app_direct()