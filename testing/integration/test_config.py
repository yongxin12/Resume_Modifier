#!/usr/bin/env python3

import os
import sys

# Add core directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from app import create_app

def test_config():
    """Test if configuration works correctly"""
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key'
    }
    
    app = create_app(config=test_config)
    
    with app.app_context():
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Testing: {app.config['TESTING']}")
        
        # Try to create db tables
        from app.extensions import db
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating tables: {e}")

if __name__ == '__main__':
    test_config()