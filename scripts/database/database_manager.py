#!/usr/bin/env python3
"""
Unified Database Management Script for Resume Modifier
Handles database updates, migrations, and deployments for Railway production
"""

import os
import sys
import time
import argparse
import psycopg2
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any

class DatabaseManager:
    """Unified database management for Railway deployments"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.connection = None
        self.cursor = None
        
    def _get_database_url(self) -> str:
        """Get database URL from Railway environment with local access support"""
        # Try Railway public URL first (accessible from local machine)
        database_url = os.environ.get('DATABASE_PUBLIC_URL')
        
        if not database_url:
            # Fallback to standard DATABASE_URL (for production deployments)
            database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            raise ValueError(
                "DATABASE_URL not found in environment variables.\n"
                "For local Railway access, ensure you're running: railway run python3 database_manager.py\n"
                "For local development, set: export DATABASE_URL='postgresql://user:pass@localhost:5432/dbname'"
            )
        
        return database_url
    
    def connect(self) -> bool:
        """Connect to Railway database with retry logic"""
        import time
        
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                print(f"🔗 Connection attempt {attempt + 1}/{max_retries}...")
                
                parsed = urlparse(self.database_url)
                
                # Try different connection approaches
                connection_params = {
                    'host': parsed.hostname,
                    'port': parsed.port or 5432,
                    'database': parsed.path[1:],  # Remove leading slash
                    'user': parsed.username,
                    'password': parsed.password,
                    'sslmode': 'require',
                    'connect_timeout': 30,  # 30 second timeout
                    'application_name': 'database_manager'
                }
                
                print(f"   Connecting to {parsed.hostname}:{parsed.port}/{parsed.path[1:]}")
                
                self.connection = psycopg2.connect(**connection_params)
                self.connection.autocommit = False  # Explicit transaction control
                self.cursor = self.connection.cursor()
                
                # Test the connection with a simple query
                self.cursor.execute("SELECT 1;")
                result = self.cursor.fetchone()
                
                if result and result[0] == 1:
                    print("✅ Connected to Railway database successfully")
                    return True
                else:
                    raise Exception("Connection test query failed")
                    
            except psycopg2.OperationalError as e:
                error_msg = str(e)
                print(f"❌ Connection attempt {attempt + 1} failed: {error_msg}")
                
                if attempt < max_retries - 1:
                    print(f"   Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print("❌ All connection attempts failed")
                    
                    # Provide specific error guidance
                    if "server closed the connection unexpectedly" in error_msg:
                        print("\n🔧 Troubleshooting suggestions:")
                        print("   1. Railway database may be restarting or under maintenance")
                        print("   2. Try again in a few minutes")
                        print("   3. Check Railway dashboard for service status")
                        print("   4. Verify Railway project has sufficient resources")
                    elif "timeout" in error_msg.lower():
                        print("\n🔧 Connection timeout detected:")
                        print("   1. Check network connectivity")
                        print("   2. Railway service may be overloaded")
                        print("   3. Try railway connect postgres to test direct connection")
                    elif "authentication failed" in error_msg.lower():
                        print("\n🔧 Authentication issue:")
                        print("   1. Check DATABASE_URL environment variable")
                        print("   2. Verify Railway login: railway whoami")
                    
                    return False
                    
            except Exception as e:
                print(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print(f"   Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print("❌ All connection attempts failed")
                    return False
        
        return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get current database table information"""
        if not self.cursor:
            return {}
        
        try:
            # Get all tables
            self.cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = [row[0] for row in self.cursor.fetchall()]
            
            # Get column count for key tables
            table_info = {'tables': tables, 'columns': {}}
            
            for table in ['users', 'resume_files', 'resumes', 'job_descriptions']:
                if table in tables:
                    self.cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.columns 
                        WHERE table_name = %s;
                    """, (table,))
                    count = self.cursor.fetchone()[0]
                    table_info['columns'][table] = count
            
            return table_info
            
        except Exception as e:
            print(f"❌ Error getting table info: {e}")
            return {}
    
    def check_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s 
                    AND column_name = %s
                );
            """, (table_name, column_name))
            return self.cursor.fetchone()[0]
        except:
            return False
    
    def add_column_safely(self, table_name: str, column_name: str, column_def: str) -> bool:
        """Add a column if it doesn't exist"""
        if self.check_column_exists(table_name, column_name):
            print(f"⚪ Column {column_name} already exists in {table_name}")
            return True
        
        try:
            self.cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def};")
            print(f"✅ Added column {column_name} to {table_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to add column {column_name} to {table_name}: {e}")
            return False
    
    def create_missing_tables(self) -> bool:
        """Create missing tables based on current models"""
        try:
            # Create users table (required for foreign keys)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(200) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    first_name VARCHAR(50),
                    last_name VARCHAR(50),
                    city VARCHAR(100),
                    bio VARCHAR(200),
                    country VARCHAR(100),
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Users table ensured")
            
            # Create resume_files table with all current fields
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS resume_files (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    original_filename VARCHAR(255) NOT NULL,
                    display_filename VARCHAR(255) NOT NULL DEFAULT '',
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
                    original_file_id INTEGER REFERENCES resume_files(id),
                    
                    -- Soft Deletion and Metadata
                    is_active BOOLEAN DEFAULT TRUE,
                    deleted_at TIMESTAMP,
                    deleted_by INTEGER REFERENCES users(id),
                    tags JSON DEFAULT '[]',
                    
                    -- File Organization and Categorization Fields
                    category VARCHAR(20) NOT NULL DEFAULT 'active',
                    category_updated_at TIMESTAMP,
                    category_updated_by INTEGER REFERENCES users(id),
                    
                    -- Timestamps
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Constraints
                    CONSTRAINT check_positive_file_size CHECK (file_size > 0),
                    CONSTRAINT check_valid_storage_type CHECK (storage_type IN ('local', 's3')),
                    CONSTRAINT check_valid_processing_status CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
                    CONSTRAINT check_positive_duplicate_sequence CHECK (duplicate_sequence >= 0),
                    CONSTRAINT check_valid_category CHECK (category IN ('active', 'archived', 'draft'))
                );
            """)
            print("✅ Resume files table ensured")
            
            # Create other essential tables
            tables_sql = {
                'resumes': """
                    CREATE TABLE IF NOT EXISTS resumes (
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        serial_number INTEGER NOT NULL,
                        title VARCHAR(100) NOT NULL,
                        extracted_text VARCHAR(5000),
                        template_id INTEGER DEFAULT 1,
                        parsed_resume JSON NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        PRIMARY KEY (user_id, serial_number)
                    );
                """,
                'job_descriptions': """
                    CREATE TABLE IF NOT EXISTS job_descriptions (
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        serial_number INTEGER NOT NULL,
                        title VARCHAR(100),
                        description VARCHAR(500) NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        PRIMARY KEY (user_id, serial_number)
                    );
                """,
                'user_sites': """
                    CREATE TABLE IF NOT EXISTS user_sites (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        resume_serial INTEGER NOT NULL,
                        subdomain VARCHAR(100) NOT NULL UNIQUE,
                        html_content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT uix_user_resume UNIQUE (user_id, resume_serial)
                    );
                """,
                'resume_templates': """
                    CREATE TABLE IF NOT EXISTS resume_templates (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        description VARCHAR(500),
                        style_config JSON NOT NULL DEFAULT '{}',
                        sections JSON NOT NULL DEFAULT '{}',
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """
            }
            
            for table_name, sql in tables_sql.items():
                try:
                    self.cursor.execute(sql)
                    print(f"✅ {table_name} table ensured")
                except Exception as e:
                    print(f"⚠️  Warning creating {table_name}: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return False
    
    def update_missing_columns(self) -> bool:
        """Add any missing columns to existing tables"""
        try:
            # Resume files table column updates
            resume_file_columns = [
                ("display_filename", "VARCHAR(255) NOT NULL DEFAULT ''"),
                ("page_count", "INTEGER"),
                ("paragraph_count", "INTEGER"),
                ("language", "VARCHAR(10)"),
                ("keywords", "JSON DEFAULT '[]'::json"),
                ("processing_time", "FLOAT"),
                ("processing_metadata", "JSON DEFAULT '{}'::json"),
                ("category", "VARCHAR(20) NOT NULL DEFAULT 'active'"),
                ("category_updated_at", "TIMESTAMP"),
                ("category_updated_by", "INTEGER REFERENCES users(id)")
            ]
            
            success = True
            for column_name, column_def in resume_file_columns:
                if not self.add_column_safely('resume_files', column_name, column_def):
                    success = False
            
            return success
            
        except Exception as e:
            print(f"❌ Error updating columns: {e}")
            return False
    
    def create_indexes(self) -> bool:
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
            for index_sql in indexes:
                try:
                    self.cursor.execute(index_sql)
                except Exception as e:
                    if "already exists" not in str(e):
                        print(f"⚠️  Warning creating index: {e}")
            
            print("✅ Database indexes ensured")
            return True
            
        except Exception as e:
            print(f"❌ Error creating indexes: {e}")
            return False
    
    def validate_schema(self) -> bool:
        """Validate the current database schema"""
        try:
            print("\n🔍 Validating database schema...")
            
            # Check critical tables exist
            critical_tables = ['users', 'resume_files', 'resumes', 'job_descriptions']
            table_info = self.get_table_info()
            
            missing_tables = [t for t in critical_tables if t not in table_info.get('tables', [])]
            if missing_tables:
                print(f"❌ Missing critical tables: {missing_tables}")
                return False
            
            # Check critical columns in resume_files
            critical_columns = ['user_id', 'stored_filename', 'file_hash', 'category', 'display_filename']
            missing_columns = []
            
            for col in critical_columns:
                if not self.check_column_exists('resume_files', col):
                    missing_columns.append(col)
            
            if missing_columns:
                print(f"❌ Missing critical columns in resume_files: {missing_columns}")
                return False
            
            print("✅ Schema validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Schema validation failed: {e}")
            return False
    
    def full_update(self) -> bool:
        """Perform a complete database update"""
        try:
            print("🚀 Starting full database update...")
            
            # Step 1: Create missing tables
            print("\n📊 Creating missing tables...")
            if not self.create_missing_tables():
                return False
            
            # Step 2: Update missing columns
            print("\n📝 Adding missing columns...")
            if not self.update_missing_columns():
                return False
            
            # Step 3: Create indexes
            print("\n📈 Creating performance indexes...")
            if not self.create_indexes():
                return False
            
            # Step 4: Commit changes
            print("\n💾 Committing changes...")
            self.connection.commit()
            
            # Step 5: Validate schema
            if not self.validate_schema():
                return False
            
            # Step 6: Show final status
            table_info = self.get_table_info()
            print("\n📋 Final database status:")
            print(f"   Tables: {len(table_info.get('tables', []))}")
            for table, count in table_info.get('columns', {}).items():
                print(f"   {table}: {count} columns")
            
            print("🎉 Database update completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Full update failed: {e}")
            self.connection.rollback()
            return False

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Database Management for Resume Modifier')
    parser.add_argument('action', choices=['update', 'validate', 'info', 'columns', 'test'], 
                       help='Action to perform')
    parser.add_argument('--table', help='Specific table to work with')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    print("🔧 Resume Modifier Database Manager")
    print("=" * 50)
    
    db_manager = DatabaseManager()
    
    if not db_manager.connect():
        sys.exit(1)
    
    try:
        if args.action == 'info':
            table_info = db_manager.get_table_info()
            print(f"\n📊 Database Info:")
            print(f"   Tables: {len(table_info.get('tables', []))}")
            print(f"   Tables: {', '.join(table_info.get('tables', []))}")
            for table, count in table_info.get('columns', {}).items():
                print(f"   {table}: {count} columns")
        
        elif args.action == 'validate':
            success = db_manager.validate_schema()
            sys.exit(0 if success else 1)
        
        elif args.action == 'columns':
            if args.table:
                exists = db_manager.check_column_exists(args.table, 'category')
                print(f"Category column in {args.table}: {'EXISTS' if exists else 'MISSING'}")
            else:
                success = db_manager.update_missing_columns()
                if success:
                    db_manager.connection.commit()
                sys.exit(0 if success else 1)
        
        elif args.action == 'test':
            print("🧪 Testing database connection...")
            # Connection test is already done in db_manager.connect()
            print("✅ Connection test completed")
        
        elif args.action == 'update':
            if args.dry_run:
                print("🔍 DRY RUN - No changes will be made")
                table_info = db_manager.get_table_info()
                print(f"Current tables: {table_info.get('tables', [])}")
            else:
                success = db_manager.full_update()
                sys.exit(0 if success else 1)
    
    finally:
        db_manager.disconnect()

if __name__ == "__main__":
    main()