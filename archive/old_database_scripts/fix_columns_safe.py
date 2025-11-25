#!/usr/bin/env python3
"""
Fix Railway database resume_files table by adding missing columns one by one
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def get_database_url():
    """Get database URL from Railway environment"""
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

def add_column_safely(cursor, table_name, column_name, column_def):
    """Add a column if it doesn't exist"""
    if not check_column_exists(cursor, table_name, column_name):
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def};")
            print(f"✅ Added column: {column_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to add column {column_name}: {e}")
            return False
    else:
        print(f"⚪ Column {column_name} already exists")
        return True

def main():
    """Main function to fix Railway database"""
    try:
        print("🔧 Fixing Railway database resume_files table...")
        
        # Get database URL
        database_url = get_database_url()
        parsed = urlparse(database_url)
        
        # List of missing columns
        columns_to_add = [
            ("display_filename", "VARCHAR(255) NOT NULL DEFAULT ''"),
            ("page_count", "INTEGER"),
            ("paragraph_count", "INTEGER"),
            ("language", "VARCHAR(10)"),
            ("keywords", "JSON DEFAULT '[]'::json"),
            ("processing_time", "FLOAT"),
            ("processing_metadata", "JSON DEFAULT '{}'::json"),
            ("category", "VARCHAR(20) NOT NULL DEFAULT 'active'"),
            ("category_updated_at", "TIMESTAMP"),
            ("category_updated_by", "INTEGER")
        ]
        
        # Connect to database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
            sslmode='require'
        )
        
        print("✅ Connected to Railway database")
        
        # Add each column in a separate transaction
        for column_name, column_def in columns_to_add:
            try:
                cursor = conn.cursor()
                add_column_safely(cursor, 'resume_files', column_name, column_def)
                conn.commit()
                cursor.close()
            except Exception as e:
                print(f"❌ Error adding {column_name}: {e}")
                conn.rollback()
        
        # Final verification
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'resume_files';
        """)
        count = cursor.fetchone()[0]
        print(f"✅ resume_files table now has {count} columns")
        
        # Check key columns
        key_cols = ['category', 'display_filename', 'keywords']
        for col in key_cols:
            exists = check_column_exists(cursor, 'resume_files', col)
            print(f"  - {col}: {'EXISTS' if exists else 'MISSING'}")
        
        cursor.close()
        conn.close()
        
        print("🎉 Database fix completed!")
        return True
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)