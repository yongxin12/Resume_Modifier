#!/usr/bin/env python3
"""
Direct Railway database fix script
Creates missing tables and columns in Railway PostgreSQL database
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def get_database_url():
    """Get database URL from Railway environment"""
    # Use public URL for external connections
    database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment")
    return database_url

def check_table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, (table_name,))
    return cursor.fetchone()[0]

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = %s 
            AND column_name = %s
        );
    """, (table_name, column_name))
    return cursor.fetchone()[0]

def create_users_table(cursor):
    """Create users table if it doesn't exist"""
    cursor.execute("""
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

def create_resume_files_table(cursor):
    """Create resume_files table with all required columns"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume_files (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            original_filename VARCHAR(255) NOT NULL,
            display_filename VARCHAR(255) NOT NULL,
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

def create_other_tables(cursor):
    """Create other required tables"""
    
    # Resume templates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume_templates (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description VARCHAR(500),
            style_config JSON NOT NULL,
            sections JSON NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Resumes table  
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            user_id INTEGER NOT NULL REFERENCES users(id),
            serial_number INTEGER NOT NULL,
            title VARCHAR(100) NOT NULL,
            extracted_text VARCHAR(5000),
            template_id INTEGER REFERENCES resume_templates(id),
            parsed_resume JSON NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP NOT NULL,
            PRIMARY KEY (user_id, serial_number)
        );
    """)
    
    # Job descriptions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_descriptions (
            user_id INTEGER NOT NULL REFERENCES users(id),
            serial_number INTEGER NOT NULL,
            title VARCHAR(100),
            description VARCHAR(500) NOT NULL,
            created_at TIMESTAMP NOT NULL,
            PRIMARY KEY (user_id, serial_number)
        );
    """)
    
    # User sites table
    cursor.execute("""
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
    """)

def create_indexes(cursor):
    """Create necessary indexes"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_resume_files_user_created ON resume_files(user_id, created_at);",
        "CREATE INDEX IF NOT EXISTS idx_resume_files_processing_status ON resume_files(processing_status);",
        "CREATE INDEX IF NOT EXISTS idx_resume_files_active ON resume_files(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_resume_files_hash ON resume_files(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_resume_files_user_hash ON resume_files(user_id, file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_resume_files_category ON resume_files(user_id, category, is_active);",
        "CREATE INDEX IF NOT EXISTS idx_resume_files_category_updated ON resume_files(category_updated_at);"
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
        except Exception as e:
            print(f"Warning: Could not create index: {e}")

def main():
    """Main function to fix Railway database"""
    try:
        print("🔧 Starting Railway database fix...")
        
        # Get database URL
        database_url = get_database_url()
        print(f"🔗 Connecting to database...")
        
        # Parse database URL
        parsed = urlparse(database_url)
        
        # Connect to database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password,
            sslmode='require'
        )
        
        cursor = conn.cursor()
        
        print("✅ Connected to Railway database")
        
        # Check current tables
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Existing tables: {existing_tables}")
        
        # Create users table first (required for foreign keys)
        print("👥 Creating users table...")
        create_users_table(cursor)
        
        # Create resume_files table
        print("📁 Creating resume_files table...")
        create_resume_files_table(cursor)
        
        # Create other tables
        print("📊 Creating other required tables...")
        create_other_tables(cursor)
        
        # Create indexes
        print("📈 Creating indexes...")
        create_indexes(cursor)
        
        # Commit changes
        conn.commit()
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        final_tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Final tables: {final_tables}")
        
        # Check resume_files table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'resume_files' 
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"📋 resume_files columns: {len(columns)} columns created")
        
        cursor.close()
        conn.close()
        
        print("🎉 Railway database fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)