#!/usr/bin/env python3
"""
Create Admin User Script
Creates or updates a user to have admin privileges
"""

import os
import sys
from datetime import datetime

# Add core to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.join(current_dir, 'core')
sys.path.insert(0, core_dir)

from flask import Flask
from app.extensions import db
from app.models.temp import User
from werkzeug.security import generate_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create Flask app with database configuration"""
    app = Flask(__name__)
    
    # Database configuration
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/resume_app')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def create_admin_user(email, password, username=None):
    """Create or update user to be admin"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            
            if existing_user:
                # Make existing user admin
                existing_user.is_admin = True
                existing_user.updated_at = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"✅ Made existing user '{email}' an admin")
                return existing_user
            else:
                # Create new admin user
                admin_user = User(
                    username=username or email.split('@')[0],
                    email=email,
                    password=generate_password_hash(password),
                    is_admin=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.session.add(admin_user)
                db.session.commit()
                
                logger.info(f"✅ Created new admin user: {email}")
                return admin_user
                
        except Exception as e:
            logger.error(f"❌ Failed to create admin user: {e}")
            db.session.rollback()
            return None

def list_admin_users():
    """List all admin users"""
    app = create_app()
    
    with app.app_context():
        try:
            admin_users = User.query.filter_by(is_admin=True).all()
            
            logger.info(f"📋 Found {len(admin_users)} admin user(s):")
            for admin in admin_users:
                logger.info(f"  - ID: {admin.id}, Email: {admin.email}, Username: {admin.username}")
            
            return admin_users
            
        except Exception as e:
            logger.error(f"❌ Failed to list admin users: {e}")
            return []

def main():
    """Main function with interactive options"""
    logger.info("🔐 Admin User Management")
    logger.info("=" * 40)
    
    # List current admin users
    logger.info("Current admin users:")
    list_admin_users()
    
    print("\nOptions:")
    print("1. Create new admin user")
    print("2. Make existing user admin")
    print("3. List admin users only")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        email = input("Enter email for new admin: ").strip()
        password = input("Enter password: ").strip()
        username = input("Enter username (optional): ").strip() or None
        
        if email and password:
            create_admin_user(email, password, username)
        else:
            logger.error("Email and password are required")
    
    elif choice == "2":
        email = input("Enter email of existing user to make admin: ").strip()
        
        if email:
            create_admin_user(email, "dummy_password")  # Won't change password
        else:
            logger.error("Email is required")
    
    elif choice == "3":
        list_admin_users()
    
    else:
        logger.info("Invalid choice")

if __name__ == "__main__":
    main()