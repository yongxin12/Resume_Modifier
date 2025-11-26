#!/usr/bin/env python3
"""
Add missing columns to Railway database resume_files table
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

def add_missing_columns(cursor):
    """Add missing columns to resume_files table"""
    
    # List of missing columns with their definitions
    missing_columns = [
        ("display_filename", "VARCHAR(255) NOT NULL DEFAULT ''"),
        ("page_count", "INTEGER"),
        ("paragraph_count", "INTEGER"),
        ("language", "VARCHAR(10)"),
        ("keywords", "JSON DEFAULT '[]'"),
        ("processing_time", "FLOAT"),
        ("processing_metadata", "JSON DEFAULT '{}'"),
        ("category", "VARCHAR(20) NOT NULL DEFAULT 'active'"),
        ("category_updated_at", "TIMESTAMP"),
        ("category_updated_by", "INTEGER REFERENCES users(id)")
    ]
    
    for column_name, column_def in missing_columns:
        if not check_column_exists(cursor, 'resume_files', column_name):
            try:
                print(f"Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE resume_files ADD COLUMN {column_name} {column_def};")
            except Exception as e:
                print(f"Warning: Could not add column {column_name}: {e}")
        else:
            print(f"Column {column_name} already exists")

def add_constraints(cursor):
    """Add missing constraints to resume_files table"""
    
    constraints = [
        ("check_positive_file_size", "CHECK (file_size > 0)"),
        ("check_valid_storage_type", "CHECK (storage_type IN ('local', 's3'))"),
        ("check_valid_processing_status", "CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))"),
        ("check_positive_duplicate_sequence", "CHECK (duplicate_sequence >= 0)"),
        ("check_valid_category", "CHECK (category IN ('active', 'archived', 'draft'))")
    ]
    
    for constraint_name, constraint_def in constraints:
        try:
            cursor.execute(f"ALTER TABLE resume_files ADD CONSTRAINT {constraint_name} {constraint_def};")
            print(f"Added constraint: {constraint_name}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"Constraint {constraint_name} already exists")
            else:
                print(f"Warning: Could not add constraint {constraint_name}: {e}")

def create_indexes(cursor):
    """Create missing indexes"""
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
            print(f"Created index: {index_sql.split(' ')[5]}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"Index already exists")
            else:
                print(f"Warning: Could not create index: {e}")

def main():
    """Main function to add missing columns"""
    try:
        print("🔧 Adding missing columns to Railway database...")
        
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
        
        # Add missing columns
        print("📊 Adding missing columns...")
        add_missing_columns(cursor)
        
        # Add constraints
        print("🔒 Adding constraints...")
        add_constraints(cursor)
        
        # Create indexes
        print("📈 Creating indexes...")
        create_indexes(cursor)
        
        # Commit changes
        conn.commit()
        
        # Verify columns were added
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'resume_files' 
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"✅ resume_files table now has {len(columns)} columns")
        
        cursor.close()
        conn.close()
        
        print("🎉 Database update completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database update failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)