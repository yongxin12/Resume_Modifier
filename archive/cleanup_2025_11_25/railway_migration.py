#!/usr/bin/env python3
"""
Railway Database Migration Script
Updates the resume_files table to match the local model schema
"""

import psycopg2
import os
import sys
from datetime import datetime

def get_railway_connection():
    """Get connection to Railway database using environment variables"""
    
    # Check for Railway database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        print("Please set DATABASE_URL with your Railway database connection string")
        return None
    
    try:
        conn = psycopg2.connect(database_url)
        print("✅ Connected to Railway database")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to Railway database: {e}")
        return None

def check_existing_columns(cursor):
    """Check which columns already exist in the resume_files table"""
    
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'resume_files' 
        AND table_schema = 'public'
        ORDER BY column_name;
    """)
    
    existing_columns = [row[0] for row in cursor.fetchall()]
    print(f"📋 Existing columns in resume_files: {len(existing_columns)} columns")
    
    return existing_columns

def run_migration(cursor):
    """Run the migration to add missing columns"""
    
    print("🔄 Starting Railway database migration...")
    
    # List of columns to add with their definitions
    columns_to_add = [
        ("display_filename", "VARCHAR(255)"),
        ("page_count", "INTEGER"),
        ("paragraph_count", "INTEGER"), 
        ("language", "VARCHAR(10)"),
        ("keywords", "JSON"),
        ("processing_time", "FLOAT"),
        ("processing_metadata", "JSON"),
        ("has_thumbnail", "BOOLEAN DEFAULT FALSE"),
        ("thumbnail_path", "VARCHAR(500)"),
        ("thumbnail_status", "VARCHAR(20) DEFAULT 'pending'"),
        ("thumbnail_generated_at", "TIMESTAMP"),
        ("thumbnail_error", "TEXT"),
        ("google_drive_link", "VARCHAR(500)"),
        ("google_doc_link", "VARCHAR(500)")
    ]
    
    # Check which columns already exist
    existing_columns = check_existing_columns(cursor)
    
    added_columns = []
    skipped_columns = []
    
    # Add missing columns
    for column_name, column_def in columns_to_add:
        if column_name in existing_columns:
            skipped_columns.append(column_name)
            print(f"⏭️  Skipping {column_name} (already exists)")
        else:
            try:
                sql = f"ALTER TABLE resume_files ADD COLUMN {column_name} {column_def};"
                cursor.execute(sql)
                added_columns.append(column_name)
                print(f"✅ Added column: {column_name}")
            except Exception as e:
                print(f"❌ Failed to add {column_name}: {e}")
    
    return added_columns, skipped_columns

def add_constraints(cursor):
    """Add any missing constraints"""
    
    print("🔄 Adding database constraints...")
    
    constraints = [
        ("check_valid_thumbnail_status", 
         "ALTER TABLE resume_files ADD CONSTRAINT check_valid_thumbnail_status CHECK (thumbnail_status IN ('pending', 'generating', 'completed', 'failed'));"),
    ]
    
    for constraint_name, sql in constraints:
        try:
            cursor.execute(sql)
            print(f"✅ Added constraint: {constraint_name}")
        except psycopg2.errors.DuplicateObject:
            print(f"⏭️  Constraint {constraint_name} already exists")
        except Exception as e:
            print(f"❌ Failed to add constraint {constraint_name}: {e}")

def verify_migration(cursor):
    """Verify the migration was successful"""
    
    print("🔍 Verifying migration...")
    
    # Check all expected columns exist
    expected_columns = [
        'id', 'user_id', 'original_filename', 'display_filename', 'stored_filename',
        'file_size', 'mime_type', 'storage_type', 'file_path', 's3_bucket', 'file_hash',
        'google_drive_file_id', 'google_doc_id', 'google_drive_link', 'google_doc_link',
        'is_shared_with_user', 'is_processed', 'extracted_text', 'processing_status',
        'processing_error', 'page_count', 'paragraph_count', 'language', 'keywords',
        'processing_time', 'processing_metadata', 'is_duplicate', 'duplicate_sequence',
        'original_file_id', 'has_thumbnail', 'thumbnail_path', 'thumbnail_status',
        'thumbnail_generated_at', 'thumbnail_error', 'is_active', 'deleted_at',
        'deleted_by', 'tags', 'created_at', 'updated_at', 'category', 'category_updated_at',
        'category_updated_by'
    ]
    
    existing_columns = check_existing_columns(cursor)
    missing_columns = [col for col in expected_columns if col not in existing_columns]
    
    if missing_columns:
        print(f"⚠️  Still missing columns: {missing_columns}")
        return False
    else:
        print("✅ All expected columns are present!")
        return True

def main():
    """Main migration function"""
    
    print("🚀 Railway Database Migration Tool")
    print("=" * 50)
    
    # Get database connection
    conn = get_railway_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Run migration
        added_columns, skipped_columns = run_migration(cursor)
        
        # Add constraints
        add_constraints(cursor)
        
        # Commit changes
        conn.commit()
        print("💾 Changes committed to database")
        
        # Verify migration
        success = verify_migration(cursor)
        
        # Summary
        print("=" * 50)
        print("📊 Migration Summary:")
        print(f"   ✅ Added columns: {len(added_columns)}")
        if added_columns:
            print(f"      {', '.join(added_columns)}")
        print(f"   ⏭️  Skipped columns: {len(skipped_columns)}")
        if skipped_columns:
            print(f"      {', '.join(skipped_columns)}")
        
        if success:
            print("🎉 Migration completed successfully!")
            print("   The Railway database schema now matches your local model.")
            print("   File upload should work without PostgreSQL transaction errors.")
        else:
            print("⚠️  Migration completed with warnings")
            print("   Some columns may still be missing")
        
        return success
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)