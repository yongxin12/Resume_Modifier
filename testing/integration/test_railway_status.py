#!/usr/bin/env python3
"""
Test Railway database connection and verify column existence
"""

import os
import psycopg2
from psycopg2 import sql

# Use the DATABASE_URL from the earlier session
DATABASE_URL = "postgresql://postgres:IEAChRNbxjHiLfxsFfoodmTWgxFDxSmV@shinkansen.proxy.rlwy.net:52352/railway"

def test_railway_database():
    """Test Railway database and check for required columns"""
    try:
        print("🔍 Testing Railway database connection...")
        
        # Connect to Railway database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("✅ Connected to Railway database successfully")
        
        # Check if resume_files table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'resume_files'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("❌ resume_files table does not exist")
            return False
        
        print("✅ resume_files table exists")
        
        # Check for the specific columns that were missing
        required_columns = [
            'display_filename', 'page_count', 'paragraph_count', 'language',
            'keywords', 'processing_time', 'processing_metadata',
            'has_thumbnail', 'thumbnail_path', 'thumbnail_status',
            'thumbnail_generated_at', 'thumbnail_error'
        ]
        
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'resume_files'
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 Found {len(existing_columns)} columns in resume_files table")
        
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return False
        else:
            print(f"✅ All required columns are present: {required_columns}")
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def test_file_upload_simulation():
    """Simulate the file upload database operation"""
    try:
        print("\n🧪 Testing file upload database operation...")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Try to insert a test record to see if it works
        test_insert = """
            INSERT INTO resume_files (
                user_id, original_filename, display_filename, stored_filename,
                file_path, file_size, mime_type, storage_type, file_hash,
                page_count, has_thumbnail, thumbnail_status
            ) VALUES (
                999, 'test.pdf', 'test.pdf', 'test_999_123.pdf',
                '/test/path', 1000, 'application/pdf', 'local', 'testhash123',
                1, false, 'pending'
            ) RETURNING id;
        """
        
        cursor.execute(test_insert)
        file_id = cursor.fetchone()[0]
        print(f"✅ Test insert successful, file_id: {file_id}")
        
        # Clean up test record
        cursor.execute("DELETE FROM resume_files WHERE id = %s", (file_id,))
        conn.commit()
        print("✅ Test record cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ File upload simulation failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚂 Railway Database Testing")
    print("=" * 40)
    
    db_ok = test_railway_database()
    
    if db_ok:
        upload_ok = test_file_upload_simulation()
        
        if upload_ok:
            print("\n🎉 Railway database is ready for file uploads!")
        else:
            print("\n❌ Railway database has issues with file upload operations")
    else:
        print("\n❌ Railway database is not properly configured")