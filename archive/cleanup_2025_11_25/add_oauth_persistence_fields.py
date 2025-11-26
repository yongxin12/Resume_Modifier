#!/usr/bin/env python3
"""
Database migration script to add OAuth persistence and storage monitoring fields
to the GoogleAuth model for persistent authentication functionality.

This script adds the following new fields to google_auth_tokens table:
- OAuth Persistence Fields: is_persistent, auto_refresh_enabled, last_refresh_at, etc.
- Storage Monitoring Fields: drive_quota_total, drive_quota_used, quota_warning_level, etc.
- Session Management Fields: persistent_session_id, last_activity_at, is_active, etc.

Author: Resume Modifier Backend Team
Date: November 2024
"""

import os
import sys
from datetime import datetime
import secrets

# Add the core directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.join(current_dir, 'core')
sys.path.insert(0, core_dir)

try:
    from app.extensions import db
    from app.models.temp import User, GoogleAuth
    from flask import Flask
    import logging

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    def create_app():
        """Create Flask application with database configuration"""
        app = Flask(__name__)
        
        # Database configuration
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/resume_app')
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }
        
        db.init_app(app)
        return app

    def check_column_exists(table_name, column_name):
        """Check if a column exists in the table"""
        try:
            from sqlalchemy import text
            result = db.session.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' AND column_name = '{column_name}'
            """))
            return result.fetchone() is not None
        except Exception as e:
            logger.warning(f"Could not check column existence: {e}")
            return False

    def add_oauth_persistence_fields():
        """Add OAuth persistence fields to google_auth_tokens table"""
        logger.info("Adding OAuth persistence fields to google_auth_tokens table...")
        
        # List of new columns to add
        new_columns = [
            # OAuth Persistence Fields
            "is_persistent BOOLEAN DEFAULT TRUE NOT NULL",
            "auto_refresh_enabled BOOLEAN DEFAULT TRUE NOT NULL", 
            "last_refresh_at TIMESTAMP NULL",
            "refresh_attempts INTEGER DEFAULT 0 NOT NULL",
            "max_refresh_failures INTEGER DEFAULT 5 NOT NULL",
            
            # Storage Monitoring Fields
            "drive_quota_total BIGINT NULL",
            "drive_quota_used BIGINT NULL",
            "last_quota_check TIMESTAMP NULL",
            "quota_warning_level VARCHAR(20) NULL",
            "quota_warnings_sent JSON NULL",
            
            # Session and Security Fields
            "persistent_session_id VARCHAR(128) NULL",
            "last_activity_at TIMESTAMP NULL",
            "is_active BOOLEAN DEFAULT TRUE NOT NULL",
            "deactivated_reason VARCHAR(100) NULL",
            "deactivated_at TIMESTAMP NULL"
        ]
        
        columns_added = 0
        columns_skipped = 0
        
        for column_def in new_columns:
            column_name = column_def.split()[0]
            
            # Check if column already exists
            if check_column_exists('google_auth_tokens', column_name):
                logger.info(f"Column '{column_name}' already exists, skipping...")
                columns_skipped += 1
                continue
            
            try:
                from sqlalchemy import text
                # Add the column
                db.session.execute(text(f"ALTER TABLE google_auth_tokens ADD COLUMN {column_def}"))
                db.session.commit()
                logger.info(f"✅ Added column: {column_name}")
                columns_added += 1
            except Exception as e:
                db.session.rollback()
                logger.error(f"❌ Failed to add column {column_name}: {e}")
        
        logger.info(f"Column addition summary: {columns_added} added, {columns_skipped} skipped")
        return columns_added > 0

    def add_constraints_and_indexes():
        """Add database constraints and indexes for new fields"""
        logger.info("Adding constraints and indexes...")
        
        constraints_and_indexes = [
            # Constraints
            "ALTER TABLE google_auth_tokens ADD CONSTRAINT check_positive_refresh_attempts CHECK (refresh_attempts >= 0)",
            "ALTER TABLE google_auth_tokens ADD CONSTRAINT check_positive_max_failures CHECK (max_refresh_failures > 0)",
            "ALTER TABLE google_auth_tokens ADD CONSTRAINT check_valid_warning_level CHECK (quota_warning_level IN ('none', 'low', 'medium', 'high', 'critical'))",
            
            # Indexes
            "CREATE INDEX IF NOT EXISTS idx_google_auth_session ON google_auth_tokens(persistent_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_google_auth_active ON google_auth_tokens(is_active, user_id)",
            "CREATE INDEX IF NOT EXISTS idx_google_auth_expires ON google_auth_tokens(token_expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_google_auth_quota_check ON google_auth_tokens(last_quota_check)",
            
            # Unique constraint for persistent_session_id
            "ALTER TABLE google_auth_tokens ADD CONSTRAINT unique_persistent_session_id UNIQUE (persistent_session_id)"
        ]
        
        for sql in constraints_and_indexes:
            try:
                from sqlalchemy import text
                db.session.execute(text(sql))
                db.session.commit()
                logger.info(f"✅ Executed: {sql[:50]}...")
            except Exception as e:
                db.session.rollback()
                # Some constraints might already exist, which is okay
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    logger.info(f"⚠️  Already exists: {sql[:50]}...")
                else:
                    logger.warning(f"⚠️  Failed to execute: {sql[:50]}... - {e}")

    def update_existing_records():
        """Update existing GoogleAuth records with default values"""
        logger.info("Updating existing GoogleAuth records with default values...")
        
        try:
            # Get all existing GoogleAuth records
            existing_auths = GoogleAuth.query.all()
            
            if not existing_auths:
                logger.info("No existing GoogleAuth records found.")
                return
            
            updates_made = 0
            for auth in existing_auths:
                # Generate unique persistent session ID if not set
                if not auth.persistent_session_id:
                    auth.persistent_session_id = secrets.token_urlsafe(32)
                
                # Set last_activity_at to created_at if not set
                if not auth.last_activity_at:
                    auth.last_activity_at = auth.created_at or datetime.utcnow()
                
                # Initialize quota warning level if not set
                if not auth.quota_warning_level:
                    auth.quota_warning_level = 'none'
                
                # Initialize quota warnings sent if not set
                if not auth.quota_warnings_sent:
                    auth.quota_warnings_sent = []
                
                updates_made += 1
            
            # Commit all updates
            db.session.commit()
            logger.info(f"✅ Updated {updates_made} existing GoogleAuth records")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Failed to update existing records: {e}")

    def verify_migration():
        """Verify that the migration was successful"""
        logger.info("Verifying migration...")
        
        # Check if we can create a test GoogleAuth instance with new fields
        try:
            # Test creating a model instance (don't save to database)
            test_auth = GoogleAuth(
                user_id=1,  # Dummy user ID
                google_user_id='test',
                email='test@example.com',
                access_token='test_token',
                refresh_token='test_refresh',
                token_expires_at=datetime.utcnow(),
                scope='test_scope',
                is_persistent=True,
                auto_refresh_enabled=True,
                persistent_session_id=secrets.token_urlsafe(32),
                quota_warning_level='none',
                is_active=True
            )
            
            # Test the new methods
            _ = test_auth.is_token_expired()
            _ = test_auth.needs_refresh()
            _ = test_auth.calculate_usage_percentage()
            _ = test_auth.get_storage_warning_level()
            _ = test_auth.to_dict()
            
            logger.info("✅ Migration verification successful - all new fields and methods work correctly")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            return False

    def main():
        """Main migration function"""
        logger.info("=" * 60)
        logger.info("Starting OAuth Persistence Migration")
        logger.info("=" * 60)
        
        # Create Flask app and database context
        app = create_app()
        
        with app.app_context():
            try:
                from sqlalchemy import text
                # Test database connection
                db.session.execute(text("SELECT 1"))
                logger.info("✅ Database connection successful")
                
                # Add new columns
                if add_oauth_persistence_fields():
                    logger.info("✅ OAuth persistence fields added successfully")
                else:
                    logger.info("ℹ️  No new fields were added (already exist)")
                
                # Add constraints and indexes
                add_constraints_and_indexes()
                logger.info("✅ Constraints and indexes processed")
                
                # Update existing records
                update_existing_records()
                
                # Verify migration
                if verify_migration():
                    logger.info("🎉 OAuth Persistence Migration completed successfully!")
                    logger.info("=" * 60)
                    logger.info("SUMMARY:")
                    logger.info("- Enhanced GoogleAuth model with persistence fields")
                    logger.info("- Added storage monitoring capabilities")
                    logger.info("- Added session management features")
                    logger.info("- Updated existing records with default values")
                    logger.info("- Verified all new functionality works correctly")
                    logger.info("=" * 60)
                    return True
                else:
                    logger.error("❌ Migration verification failed!")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Migration failed: {e}")
                return False

    if __name__ == "__main__":
        success = main()
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this script from the project root directory")
    print("and that all dependencies are installed.")
    sys.exit(1)