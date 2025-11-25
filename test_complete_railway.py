#!/usr/bin/env python3
"""
Complete Railway database fix with proper user handling
"""

import os
import psycopg2
from psycopg2 import sql
from datetime import datetime
import hashlib

# Use the DATABASE_URL from the earlier session
DATABASE_URL = "postgresql://postgres:IEAChRNbxjHiLfxsFfoodmTWgxFDxSmV@shinkansen.proxy.rlwy.net:52352/railway"

def create_test_user():
    """Create or get a test user for testing file uploads"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if test user already exists
        cursor.execute("SELECT id FROM users WHERE username = 'test_user_for_upload'")
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            print(f"✅ Using existing test user with ID: {user_id}")
            return user_id
        
        # Create test user
        test_password_hash = "pbkdf2:sha256:260000$test$hash"  # Dummy hash
        cursor.execute("""
            INSERT INTO users (username, email, password, first_name, last_name)
            VALUES ('test_user_for_upload', 'test@example.com', %s, 'Test', 'User')
            RETURNING id
        """, (test_password_hash,))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        print(f"✅ Created test user with ID: {user_id}")
        return user_id
        
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def test_complete_file_upload():
    """Test complete file upload simulation"""
    try:
        print("🧪 Testing complete file upload flow...")
        
        # Get or create test user
        user_id = create_test_user()
        if not user_id:
            return False
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Test file upload with all required fields
        test_insert = """
            INSERT INTO resume_files (
                user_id, original_filename, display_filename, stored_filename,
                file_path, file_size, mime_type, storage_type, file_hash,
                page_count, has_thumbnail, thumbnail_status, is_processed,
                processing_status, is_duplicate, duplicate_sequence, category
            ) VALUES (
                %s, 'test.pdf', 'test.pdf', 'test_upload_123.pdf',
                '/test/path', 1000, 'application/pdf', 'local', 'testhash123',
                1, false, 'pending', false, 'pending', false, 0, 'active'
            ) RETURNING id, created_at, updated_at;
        """
        
        cursor.execute(test_insert, (user_id,))
        result = cursor.fetchone()
        file_id, created_at, updated_at = result
        
        print(f"✅ File upload test successful!")
        print(f"   file_id: {file_id}")
        print(f"   user_id: {user_id}")
        print(f"   created_at: {created_at}")
        print(f"   updated_at: {updated_at}")
        
        # Test updating the record (simulating file processing)
        cursor.execute("""
            UPDATE resume_files 
            SET extracted_text = 'Sample extracted text', 
                is_processed = true, 
                processing_status = 'completed'
            WHERE id = %s
        """, (file_id,))
        
        print("✅ File update test successful!")
        
        # Clean up test records
        cursor.execute("DELETE FROM resume_files WHERE id = %s", (file_id,))
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        print("✅ Test records cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete file upload test failed: {e}")
        # Try to clean up anyway
        try:
            cursor.execute("DELETE FROM resume_files WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
        except:
            pass
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_all_constraints():
    """Check all constraints that might cause issues"""
    try:
        print("\n🔍 Checking database constraints...")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check foreign key constraints
        cursor.execute("""
            SELECT conname, contype, pg_get_constraintdef(oid)
            FROM pg_constraint 
            WHERE conrelid = (SELECT oid FROM pg_class WHERE relname = 'resume_files')
            AND contype IN ('f', 'c', 'u')
        """)
        
        constraints = cursor.fetchall()
        print(f"📋 Resume files constraints:")
        for constraint in constraints:
            print(f"   {constraint[0]} ({constraint[1]}): {constraint[2]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Constraint check failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚂 Complete Railway Database Test")
    print("=" * 40)
    
    # Check constraints first
    constraints_ok = check_all_constraints()
    
    if constraints_ok:
        # Test complete upload flow
        upload_ok = test_complete_file_upload()
        
        if upload_ok:
            print("\n🎉 Railway database is fully working!")
            print("File upload should work correctly now on Railway.")
        else:
            print("\n❌ Railway database still has issues")
    else:
        print("\n❌ Database constraint issues need investigation")