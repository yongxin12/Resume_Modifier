#!/usr/bin/env python3
"""
Admin Google Drive Setup Script
Sets up admin OAuth authentication and configures Google Drive integration
"""

import os
import sys
import json
from typing import Dict, Any

# Add core to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'core'))

from flask import Flask
from app.extensions import db
from app.models.temp import User, GoogleAuth
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdminGoogleDriveSetup:
    """Setup admin Google Drive integration"""
    
    def __init__(self):
        """Initialize the setup with Flask app context"""
        self.app = self._create_app()
        
    def _create_app(self):
        """Create minimal Flask app for database operations"""
        app = Flask(__name__)
        
        # Database configuration
        database_url = self._get_database_url()
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Google OAuth configuration
        app.config.update({
            'GOOGLE_ADMIN_OAUTH_CLIENT_ID': os.getenv('GOOGLE_CLIENT_ID'),
            'GOOGLE_ADMIN_OAUTH_CLIENT_SECRET': os.getenv('GOOGLE_CLIENT_SECRET'),
            'GOOGLE_ADMIN_OAUTH_REDIRECT_URI': os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5001/auth/google/admin/callback'),
            'GOOGLE_ADMIN_DRIVE_FOLDER_NAME': os.getenv('GOOGLE_DRIVE_FOLDER_NAME', 'Resume_Modifier_Files'),
            'GOOGLE_DRIVE_ENABLE_SHARING': os.getenv('GOOGLE_DRIVE_ENABLE_SHARING', 'true').lower() == 'true',
            'GOOGLE_DRIVE_DEFAULT_PERMISSIONS': os.getenv('GOOGLE_DRIVE_DEFAULT_PERMISSIONS', 'writer')
        })
        
        # Initialize extensions
        db.init_app(app)
        
        return app
    
    def _get_database_url(self):
        """Get database URL from environment"""
        db_url = (
            os.getenv('DATABASE_PUBLIC_URL') or 
            os.getenv('DATABASE_URL') or 
            'postgresql://postgres:postgres@localhost:5432/resume_app'
        )
        
        logger.info(f"Using database: {db_url.split('@')[0]}@***")
        return db_url
    
    def setup_admin_users(self) -> bool:
        """Ensure admin users exist and are properly configured"""
        try:
            with self.app.app_context():
                logger.info("🔧 Setting up admin users...")
                
                # Check for existing admin users
                admin_users = User.query.filter_by(is_admin=True).all()
                
                if not admin_users:
                    logger.info("Creating default admin user...")
                    self._create_default_admin()
                else:
                    logger.info(f"✅ Found {len(admin_users)} existing admin user(s)")
                    for admin in admin_users:
                        logger.info(f"  - Admin: {admin.email} (ID: {admin.id})")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to setup admin users: {e}")
            return False
    
    def _create_default_admin(self):
        """Create default admin user"""
        from werkzeug.security import generate_password_hash
        
        default_email = "admin@resume-modifier.com"
        default_password = "admin123"  # CHANGE THIS!
        
        # Check if user with this email already exists
        existing_user = User.query.filter_by(email=default_email).first()
        
        if existing_user:
            # Make existing user an admin
            existing_user.is_admin = True
            existing_user.updated_at = datetime.utcnow()
            db.session.commit()
            logger.info(f"✅ Made existing user {default_email} an admin")
        else:
            # Create new admin user
            admin_user = User(
                username="admin",
                email=default_email,
                password=generate_password_hash(default_password),
                is_admin=True,
                first_name="System",
                last_name="Administrator",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(admin_user)
            db.session.commit()
            logger.info(f"✅ Created admin user: {default_email}")
        
        logger.warning("🚨 SECURITY WARNING: Default admin password is 'admin123'")
        logger.warning("🚨 Change this password immediately after first login!")
    
    def check_oauth_configuration(self) -> Dict[str, Any]:
        """Check Google OAuth configuration"""
        logger.info("🔧 Checking Google OAuth configuration...")
        
        config_status = {
            'client_id': bool(os.getenv('GOOGLE_CLIENT_ID')),
            'client_secret': bool(os.getenv('GOOGLE_CLIENT_SECRET')),
            'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5001/auth/google/admin/callback'),
            'drive_folder_name': os.getenv('GOOGLE_DRIVE_FOLDER_NAME', 'Resume_Modifier_Files'),
            'sharing_enabled': os.getenv('GOOGLE_DRIVE_ENABLE_SHARING', 'true').lower() == 'true',
            'default_permissions': os.getenv('GOOGLE_DRIVE_DEFAULT_PERMISSIONS', 'writer')
        }
        
        # Check configuration completeness
        required_config = ['client_id', 'client_secret']
        missing_config = [key for key in required_config if not config_status[key]]
        
        if missing_config:
            logger.error(f"❌ Missing required OAuth configuration: {missing_config}")
            logger.info("📋 Required environment variables:")
            logger.info("  - GOOGLE_CLIENT_ID: OAuth 2.0 Client ID from Google Cloud Console")
            logger.info("  - GOOGLE_CLIENT_SECRET: OAuth 2.0 Client Secret from Google Cloud Console")
            logger.info("  - GOOGLE_REDIRECT_URI (optional): OAuth callback URL")
            config_status['configured'] = False
        else:
            logger.info("✅ Google OAuth configuration is complete")
            config_status['configured'] = True
        
        # Display current configuration
        logger.info("📋 Current OAuth Configuration:")
        logger.info(f"  - Client ID: {'✅ Set' if config_status['client_id'] else '❌ Missing'}")
        logger.info(f"  - Client Secret: {'✅ Set' if config_status['client_secret'] else '❌ Missing'}")
        logger.info(f"  - Redirect URI: {config_status['redirect_uri']}")
        logger.info(f"  - Drive Folder: {config_status['drive_folder_name']}")
        logger.info(f"  - Sharing Enabled: {config_status['sharing_enabled']}")
        logger.info(f"  - Default Permissions: {config_status['default_permissions']}")
        
        return config_status
    
    def check_admin_auth_status(self) -> Dict[str, Any]:
        """Check current admin authentication status"""
        try:
            with self.app.app_context():
                logger.info("🔧 Checking admin authentication status...")
                
                # Get admin users
                admin_users = User.query.filter_by(is_admin=True).all()
                
                if not admin_users:
                    return {
                        'status': 'no_admin_users',
                        'message': 'No admin users found'
                    }
                
                # Check Google auth status for each admin
                auth_status = []
                for admin in admin_users:
                    google_auth = GoogleAuth.query.filter_by(
                        user_id=admin.id,
                        is_active=True
                    ).first()
                    
                    if google_auth:
                        auth_status.append({
                            'user_id': admin.id,
                            'email': admin.email,
                            'authenticated': True,
                            'token_expired': google_auth.is_token_expired(),
                            'needs_refresh': google_auth.needs_refresh(),
                            'last_activity': google_auth.last_activity_at.isoformat() if google_auth.last_activity_at else None
                        })
                    else:
                        auth_status.append({
                            'user_id': admin.id,
                            'email': admin.email,
                            'authenticated': False,
                            'auth_required': True
                        })
                
                # Summary
                authenticated_count = sum(1 for status in auth_status if status['authenticated'])
                
                logger.info(f"📋 Admin Authentication Status:")
                logger.info(f"  - Total admin users: {len(admin_users)}")
                logger.info(f"  - Authenticated: {authenticated_count}")
                logger.info(f"  - Need authentication: {len(admin_users) - authenticated_count}")
                
                for status in auth_status:
                    if status['authenticated']:
                        expired_status = " (EXPIRED)" if status.get('token_expired') else ""
                        logger.info(f"  ✅ {status['email']}: Authenticated{expired_status}")
                    else:
                        logger.info(f"  ❌ {status['email']}: Needs authentication")
                
                return {
                    'status': 'checked',
                    'total_admins': len(admin_users),
                    'authenticated_admins': authenticated_count,
                    'admin_status': auth_status
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to check admin auth status: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def display_setup_instructions(self):
        """Display setup instructions for admin"""
        logger.info("")
        logger.info("🚀 Google Drive Admin Setup Instructions")
        logger.info("=" * 50)
        logger.info("")
        logger.info("1. 📋 GOOGLE CLOUD CONSOLE SETUP:")
        logger.info("   a. Go to https://console.cloud.google.com/")
        logger.info("   b. Create a new project or select existing project")
        logger.info("   c. Enable Google Drive API and Google Docs API")
        logger.info("   d. Go to 'Credentials' → 'Create Credentials' → 'OAuth 2.0 Client IDs'")
        logger.info("   e. Set application type to 'Web application'")
        logger.info("   f. Add authorized redirect URI: http://localhost:5001/auth/google/admin/callback")
        logger.info("   g. Copy Client ID and Client Secret")
        logger.info("")
        logger.info("2. 🔧 ENVIRONMENT CONFIGURATION:")
        logger.info("   Add these variables to your .env file:")
        logger.info("   GOOGLE_CLIENT_ID=your_client_id_here")
        logger.info("   GOOGLE_CLIENT_SECRET=your_client_secret_here")
        logger.info("   GOOGLE_REDIRECT_URI=http://localhost:5001/auth/google/admin/callback")
        logger.info("")
        logger.info("3. 🔐 ADMIN AUTHENTICATION:")
        logger.info("   a. Start your Flask application")
        logger.info("   b. Login as admin user (admin@resume-modifier.com / admin123)")
        logger.info("   c. Visit: http://localhost:5001/auth/google/admin")
        logger.info("   d. Complete Google OAuth flow")
        logger.info("   e. Grant permissions for Google Drive and Docs access")
        logger.info("")
        logger.info("4. ✅ VERIFICATION:")
        logger.info("   a. Check authentication status: /admin/google/status")
        logger.info("   b. Test file upload with Google Drive integration")
        logger.info("   c. Verify files appear in admin's Google Drive")
        logger.info("")
        logger.info("🚨 SECURITY REMINDERS:")
        logger.info("   - Change default admin password immediately!")
        logger.info("   - Keep OAuth credentials secure")
        logger.info("   - Monitor Google Drive storage usage")
        logger.info("   - Regularly review file permissions")
        logger.info("")
    
    def run_setup(self):
        """Run complete admin setup process"""
        logger.info("🚀 Starting Admin Google Drive Setup...")
        logger.info("=" * 50)
        
        # Step 1: Setup admin users
        if not self.setup_admin_users():
            logger.error("❌ Admin user setup failed")
            return False
        
        # Step 2: Check OAuth configuration
        oauth_config = self.check_oauth_configuration()
        
        # Step 3: Check authentication status
        auth_status = self.check_admin_auth_status()
        
        # Step 4: Display instructions
        self.display_setup_instructions()
        
        # Summary
        logger.info("📋 SETUP SUMMARY:")
        logger.info(f"  ✅ Admin users: Ready")
        logger.info(f"  {'✅' if oauth_config['configured'] else '❌'} OAuth config: {'Complete' if oauth_config['configured'] else 'Incomplete'}")
        logger.info(f"  {'✅' if auth_status.get('authenticated_admins', 0) > 0 else '❌'} Admin auth: {'Active' if auth_status.get('authenticated_admins', 0) > 0 else 'Required'}")
        
        if oauth_config['configured'] and auth_status.get('authenticated_admins', 0) > 0:
            logger.info("🎉 Setup complete! Google Drive integration is ready.")
        else:
            logger.info("⚠️  Setup incomplete. Follow the instructions above to complete setup.")
        
        return True

def main():
    """Main setup function"""
    try:
        setup = AdminGoogleDriveSetup()
        success = setup.run_setup()
        return success
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)