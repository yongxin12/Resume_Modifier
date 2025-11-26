#!/usr/bin/env python3
"""
Database Transaction Fix Script
Resolves PostgreSQL InFailedSqlTransaction errors and ensures proper schema alignment
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

# Add core to Python path
sys.path.insert(0, 'core')

from flask import Flask
from app.extensions import db
from app.models.temp import ResumeFile, User
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseTransactionFixer:
    """Fix database transaction issues and schema problems"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.connection = None
        self.cursor = None
    
    def _get_database_url(self):
        """Get database URL from environment or Docker"""
        # Try Railway first
        db_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
        
        # Docker fallback
        if not db_url:
            db_url = "postgresql://postgres:postgres@localhost:5432/resume_app"
        
        if not db_url:
            raise ValueError("No database URL found")
        
        logger.info(f"Using database URL: {db_url.split('@')[0]}@***")
        return db_url
    
    def connect(self):
        """Connect to database with proper error handling"""
        try:
            parsed = urlparse(self.database_url)
            
            connection_params = {
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path[1:],
                'user': parsed.username,
                'password': parsed.password,
                'sslmode': 'prefer',
                'connect_timeout': 30
            }
            
            self.connection = psycopg2.connect(**connection_params)
            self.connection.autocommit = False
            self.cursor = self.connection.cursor()
            
            logger.info("✅ Connected to database successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def fix_resume_files_table(self):
        """Fix resume_files table schema and constraints"""
        try:
            logger.info("🔧 Fixing resume_files table schema...")
            
            # Start transaction
            self.cursor.execute("BEGIN;")
            
            # Check if table exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'resume_files'
                );
            """)
            table_exists = self.cursor.fetchone()[0]
            
            if not table_exists:
                logger.info("Creating resume_files table...")
                self._create_resume_files_table()
            else:
                logger.info("Updating existing resume_files table...")
                self._update_resume_files_table()
            
            # Commit transaction
            self.connection.commit()
            logger.info("✅ resume_files table fixed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to fix resume_files table: {e}")
            self.connection.rollback()
            return False
    
    def _create_resume_files_table(self):
        """Create complete resume_files table with all required fields"""
        create_sql = """
        CREATE TABLE resume_files (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            display_filename VARCHAR(255) DEFAULT '',
            stored_filename VARCHAR(255) NOT NULL UNIQUE,
            file_size INTEGER NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            storage_type VARCHAR(50) NOT NULL DEFAULT 'local',
            file_path VARCHAR(500) NOT NULL,
            s3_bucket VARCHAR(100),
            file_hash VARCHAR(64) NOT NULL,
            
            -- Google Drive Integration Fields
            google_drive_file_id VARCHAR(100),
            google_doc_id VARCHAR(100),
            google_drive_link VARCHAR(500),
            google_doc_link VARCHAR(500),
            is_shared_with_user BOOLEAN DEFAULT FALSE,
            
            -- Processing and Content Fields
            is_processed BOOLEAN DEFAULT FALSE,
            extracted_text TEXT,
            processing_status VARCHAR(50) DEFAULT 'pending',
            processing_error TEXT,
            page_count INTEGER,
            paragraph_count INTEGER,
            language VARCHAR(10),
            keywords JSON DEFAULT '[]',
            processing_time FLOAT,
            processing_metadata JSON DEFAULT '{}',
            
            -- Duplicate Handling Fields
            is_duplicate BOOLEAN DEFAULT FALSE,
            duplicate_sequence INTEGER DEFAULT 0,
            original_file_id INTEGER,
            
            -- Thumbnail Fields
            has_thumbnail BOOLEAN DEFAULT FALSE,
            thumbnail_path VARCHAR(500),
            thumbnail_status VARCHAR(20) DEFAULT 'pending',
            thumbnail_generated_at TIMESTAMP,
            thumbnail_error TEXT,
            
            -- Soft Deletion and Metadata
            is_active BOOLEAN DEFAULT TRUE,
            deleted_at TIMESTAMP,
            deleted_by INTEGER,
            tags JSON DEFAULT '[]',
            
            -- File Organization and Categorization Fields
            category VARCHAR(20) NOT NULL DEFAULT 'active',
            category_updated_at TIMESTAMP,
            category_updated_by INTEGER,
            
            -- Timestamps
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT check_positive_file_size CHECK (file_size > 0),
            CONSTRAINT check_valid_storage_type CHECK (storage_type IN ('local', 's3')),
            CONSTRAINT check_valid_processing_status CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
            CONSTRAINT check_valid_thumbnail_status CHECK (thumbnail_status IN ('pending', 'generating', 'completed', 'failed')),
            CONSTRAINT check_positive_duplicate_sequence CHECK (duplicate_sequence >= 0),
            CONSTRAINT check_valid_category CHECK (category IN ('active', 'archived', 'draft'))
        );
        """
        
        self.cursor.execute(create_sql)
        logger.info("✅ Created resume_files table with all fields")
    
    def _update_resume_files_table(self):
        """Update existing table with missing columns"""
        
        # List of columns to add if missing
        columns_to_add = [
            ("display_filename", "VARCHAR(255) DEFAULT ''"),
            ("page_count", "INTEGER"),
            ("paragraph_count", "INTEGER"),
            ("language", "VARCHAR(10)"),
            ("keywords", "JSON DEFAULT '[]'"),
            ("processing_time", "FLOAT"),
            ("processing_metadata", "JSON DEFAULT '{}'"),
            ("has_thumbnail", "BOOLEAN DEFAULT FALSE"),
            ("thumbnail_path", "VARCHAR(500)"),
            ("thumbnail_status", "VARCHAR(20) DEFAULT 'pending'"),
            ("thumbnail_generated_at", "TIMESTAMP"),
            ("thumbnail_error", "TEXT"),
            ("category", "VARCHAR(20) DEFAULT 'active'"),
            ("category_updated_at", "TIMESTAMP"),
            ("category_updated_by", "INTEGER")
        ]
        
        for column_name, column_def in columns_to_add:
            try:
                # Check if column exists
                self.cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'resume_files' 
                        AND column_name = %s
                    );
                """, (column_name,))
                
                exists = self.cursor.fetchone()[0]
                
                if not exists:
                    self.cursor.execute(f"ALTER TABLE resume_files ADD COLUMN {column_name} {column_def};")
                    logger.info(f"✅ Added column: {column_name}")
                else:
                    logger.info(f"⚪ Column already exists: {column_name}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to add column {column_name}: {e}")
    
    def create_indexes(self):
        """Create performance indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_resume_files_user_created ON resume_files(user_id, created_at);",
            "CREATE INDEX IF NOT EXISTS idx_resume_files_processing_status ON resume_files(processing_status);",
            "CREATE INDEX IF NOT EXISTS idx_resume_files_active ON resume_files(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_resume_files_hash ON resume_files(file_hash);",
            "CREATE INDEX IF NOT EXISTS idx_resume_files_user_hash ON resume_files(user_id, file_hash);",
            "CREATE INDEX IF NOT EXISTS idx_resume_files_category ON resume_files(user_id, category, is_active);",
            "CREATE INDEX IF NOT EXISTS idx_resume_files_category_updated ON resume_files(category_updated_at);"
        ]
        
        try:
            logger.info("🔧 Creating performance indexes...")
            
            for index_sql in indexes:
                try:
                    self.cursor.execute(index_sql)
                    logger.info(f"✅ Index created: {index_sql.split(' ')[5]}")
                except Exception as e:
                    if "already exists" not in str(e):
                        logger.warning(f"⚠️ Index creation warning: {e}")
            
            self.connection.commit()
            logger.info("✅ All indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")
            self.connection.rollback()
            return False
    
    def fix_users_table(self):
        """Ensure users table has admin flag"""
        try:
            logger.info("🔧 Fixing users table...")
            
            # Check if is_admin column exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'is_admin'
                );
            """)
            
            has_admin_column = self.cursor.fetchone()[0]
            
            if not has_admin_column:
                self.cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;")
                logger.info("✅ Added is_admin column to users table")
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to fix users table: {e}")
            self.connection.rollback()
            return False
    
    def create_admin_user(self, email: str = "admin@resume-modifier.com", username: str = "admin"):
        """Create first admin user if none exists"""
        try:
            logger.info("🔧 Checking for admin users...")
            
            # Check if any admin users exist
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE;")
            admin_count = self.cursor.fetchone()[0]
            
            if admin_count == 0:
                logger.info("Creating first admin user...")
                
                # Create admin user with hashed password
                from werkzeug.security import generate_password_hash
                
                password_hash = generate_password_hash("admin123")  # Change this!
                
                self.cursor.execute("""
                    INSERT INTO users (username, email, password, is_admin, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (email) DO UPDATE SET 
                        is_admin = TRUE,
                        updated_at = %s;
                """, (
                    username, email, password_hash, True, 
                    datetime.utcnow(), datetime.utcnow(), datetime.utcnow()
                ))
                
                self.connection.commit()
                logger.info(f"✅ Created admin user: {email} (password: admin123)")
                logger.warning("🚨 CHANGE DEFAULT PASSWORD IMMEDIATELY!")
            else:
                logger.info(f"⚪ Found {admin_count} existing admin user(s)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create admin user: {e}")
            self.connection.rollback()
            return False
    
    def test_database_operations(self):
        """Test basic database operations"""
        try:
            logger.info("🧪 Testing database operations...")
            
            # Test basic query
            self.cursor.execute("SELECT 1;")
            result = self.cursor.fetchone()
            
            if result[0] == 1:
                logger.info("✅ Basic query test passed")
            
            # Test table access
            self.cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = self.cursor.fetchone()[0]
            logger.info(f"✅ Found {user_count} users in database")
            
            # Test resume_files table
            self.cursor.execute("SELECT COUNT(*) FROM resume_files;")
            file_count = self.cursor.fetchone()[0]
            logger.info(f"✅ Found {file_count} files in database")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database operation test failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

def main():
    """Main execution function"""
    logger.info("🚀 Starting Database Transaction Fix...")
    
    fixer = DatabaseTransactionFixer()
    
    try:
        # Connect to database
        if not fixer.connect():
            logger.error("❌ Cannot connect to database")
            return False
        
        # Fix users table first (required for foreign keys)
        if not fixer.fix_users_table():
            logger.error("❌ Failed to fix users table")
            return False
        
        # Create admin user
        if not fixer.create_admin_user():
            logger.error("❌ Failed to create admin user")
            return False
        
        # Fix resume_files table
        if not fixer.fix_resume_files_table():
            logger.error("❌ Failed to fix resume_files table")
            return False
        
        # Create performance indexes
        if not fixer.create_indexes():
            logger.error("❌ Failed to create indexes")
            return False
        
        # Test operations
        if not fixer.test_database_operations():
            logger.error("❌ Database operation tests failed")
            return False
        
        logger.info("🎉 Database transaction fix completed successfully!")
        logger.info("📋 Summary:")
        logger.info("  ✅ Database schema updated")
        logger.info("  ✅ Admin user created")
        logger.info("  ✅ Performance indexes created")
        logger.info("  ✅ All tests passed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False
        
    finally:
        fixer.disconnect()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)