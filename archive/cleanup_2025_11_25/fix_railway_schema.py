#!/usr/bin/env python3
"""
Fix Railway database schema issues with proper timestamps
"""

import os
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Use the DATABASE_URL from the earlier session
DATABASE_URL = "postgresql://postgres:IEAChRNbxjHiLfxsFfoodmTWgxFDxSmV@shinkansen.proxy.rlwy.net:52352/railway"

def fix_railway_schema_timestamps():
    """Fix any missing default values or constraints in Railway database"""
    try:
        print("🔧 Fixing Railway database schema...")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if created_at and updated_at have proper defaults
        cursor.execute("""
            SELECT column_name, column_default, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'resume_files' 
            AND column_name IN ('created_at', 'updated_at')
            ORDER BY column_name;
        """)
        
        timestamp_columns = cursor.fetchall()
        print(f"📋 Current timestamp columns: {timestamp_columns}")
        
        # Fix created_at if it doesn't have a default
        cursor.execute("""
            ALTER TABLE resume_files 
            ALTER COLUMN created_at SET DEFAULT NOW()
        """)
        print("✅ Set default for created_at column")
        
        # Fix updated_at if it doesn't have a default
        cursor.execute("""
            ALTER TABLE resume_files 
            ALTER COLUMN updated_at SET DEFAULT NOW()
        """)
        print("✅ Set default for updated_at column")
        
        conn.commit()
        
        # Test the fix
        print("\n🧪 Testing fixed schema...")
        test_insert = """
            INSERT INTO resume_files (
                user_id, original_filename, display_filename, stored_filename,
                file_path, file_size, mime_type, storage_type, file_hash,
                page_count, has_thumbnail, thumbnail_status
            ) VALUES (
                999, 'test.pdf', 'test.pdf', 'test_999_123.pdf',
                '/test/path', 1000, 'application/pdf', 'local', 'testhash123',
                1, false, 'pending'
            ) RETURNING id, created_at, updated_at;
        """
        
        cursor.execute(test_insert)
        result = cursor.fetchone()
        file_id, created_at, updated_at = result
        print(f"✅ Test insert successful!")
        print(f"   file_id: {file_id}")
        print(f"   created_at: {created_at}")
        print(f"   updated_at: {updated_at}")
        
        # Clean up test record
        cursor.execute("DELETE FROM resume_files WHERE id = %s", (file_id,))
        conn.commit()
        print("✅ Test record cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema fix failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_user_table():
    """Check if user table exists and has required structure"""
    try:
        print("\n👤 Checking users table...")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("❌ users table does not exist - this is a problem!")
            return False
        
        print("✅ users table exists")
        
        # Check for required columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users'
        """)
        
        user_columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 Users table columns: {user_columns}")
        
        required_user_columns = ['id', 'username', 'email', 'password']
        missing_user_columns = [col for col in required_user_columns if col not in user_columns]
        
        if missing_user_columns:
            print(f"❌ Missing user columns: {missing_user_columns}")
            return False
        
        print("✅ Users table has required columns")
        return True
        
    except Exception as e:
        print(f"❌ User table check failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚂 Railway Database Schema Fix")
    print("=" * 40)
    
    # Check users table first
    users_ok = check_user_table()
    
    if users_ok:
        # Fix schema issues
        schema_fixed = fix_railway_schema_timestamps()
        
        if schema_fixed:
            print("\n🎉 Railway database schema is now fixed!")
            print("File upload should work correctly now.")
        else:
            print("\n❌ Railway database schema fix failed")
    else:
        print("\n❌ Users table issues need to be resolved first")