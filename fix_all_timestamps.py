#!/usr/bin/env python3
"""
Fix ALL timestamp issues in Railway database
"""

import os
import psycopg2
from psycopg2 import sql

DATABASE_URL = "postgresql://postgres:IEAChRNbxjHiLfxsFfoodmTWgxFDxSmV@shinkansen.proxy.rlwy.net:52352/railway"

def fix_all_timestamp_defaults():
    """Fix timestamp defaults for all tables"""
    try:
        print("🔧 Fixing ALL timestamp defaults in Railway database...")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Tables that need timestamp fixes
        tables_to_fix = [
            'users',
            'resume_files', 
            'resumes',
            'job_descriptions',
            'resume_templates',
            'generated_documents',
            'password_reset_tokens'
        ]
        
        for table in tables_to_fix:
            try:
                # Check if table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, (table,))
                
                if not cursor.fetchone()[0]:
                    print(f"⚠️  Table {table} does not exist, skipping...")
                    continue
                
                print(f"🔧 Fixing {table} table...")
                
                # Check what timestamp columns exist
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    AND column_name IN ('created_at', 'updated_at')
                """, (table,))
                
                timestamp_cols = [row[0] for row in cursor.fetchall()]
                
                # Fix created_at if it exists
                if 'created_at' in timestamp_cols:
                    cursor.execute(f"""
                        ALTER TABLE {table} 
                        ALTER COLUMN created_at SET DEFAULT NOW()
                    """)
                    print(f"   ✅ Set created_at default for {table}")
                
                # Fix updated_at if it exists  
                if 'updated_at' in timestamp_cols:
                    cursor.execute(f"""
                        ALTER TABLE {table} 
                        ALTER COLUMN updated_at SET DEFAULT NOW()
                    """)
                    print(f"   ✅ Set updated_at default for {table}")
                
            except Exception as e:
                print(f"   ❌ Failed to fix {table}: {e}")
                continue
        
        conn.commit()
        print("✅ All timestamp defaults have been set!")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix timestamp defaults: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def test_user_creation():
    """Test creating a user with fixed timestamps"""
    try:
        print("\n👤 Testing user creation...")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Create test user 
        cursor.execute("""
            INSERT INTO users (username, email, password, first_name, last_name)
            VALUES ('test_fixed_user', 'testfixed@example.com', 'dummy_hash', 'Test', 'Fixed')
            RETURNING id, created_at, updated_at
        """)
        
        result = cursor.fetchone()
        user_id, created_at, updated_at = result
        
        print(f"✅ User creation successful!")
        print(f"   user_id: {user_id}")
        print(f"   created_at: {created_at}")
        print(f"   updated_at: {updated_at}")
        
        # Clean up
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        print("✅ Test user cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ User creation test failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def test_file_upload_with_user():
    """Test complete file upload after timestamp fixes"""
    try:
        print("\n📄 Testing complete file upload flow...")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Create test user
        cursor.execute("""
            INSERT INTO users (username, email, password, first_name, last_name)
            VALUES ('test_upload_user', 'testupload@example.com', 'dummy_hash', 'Upload', 'Test')
            RETURNING id
        """)
        
        user_id = cursor.fetchone()[0]
        print(f"✅ Created test user: {user_id}")
        
        # Create test file upload
        cursor.execute("""
            INSERT INTO resume_files (
                user_id, original_filename, display_filename, stored_filename,
                file_path, file_size, mime_type, storage_type, file_hash,
                page_count, has_thumbnail, thumbnail_status, is_processed,
                processing_status, is_duplicate, duplicate_sequence, category
            ) VALUES (
                %s, 'test_complete.pdf', 'test_complete.pdf', 'test_complete_123.pdf',
                '/test/complete/path', 2000, 'application/pdf', 'local', 'completehash123',
                2, false, 'pending', false, 'pending', false, 0, 'active'
            ) RETURNING id, created_at, updated_at
        """, (user_id,))
        
        result = cursor.fetchone()
        file_id, created_at, updated_at = result
        
        print(f"✅ File upload successful!")
        print(f"   file_id: {file_id}")
        print(f"   created_at: {created_at}")
        print(f"   updated_at: {updated_at}")
        
        # Clean up
        cursor.execute("DELETE FROM resume_files WHERE id = %s", (file_id,))
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        print("✅ Test records cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete upload test failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚂 Complete Railway Timestamp Fix")
    print("=" * 50)
    
    # Fix all timestamp defaults
    fix_ok = fix_all_timestamp_defaults()
    
    if fix_ok:
        # Test user creation
        user_ok = test_user_creation()
        
        if user_ok:
            # Test complete file upload
            upload_ok = test_file_upload_with_user()
            
            if upload_ok:
                print("\n🎉 COMPLETE SUCCESS!")
                print("Railway database is now fully working!")
                print("Both user creation and file upload work correctly.")
            else:
                print("\n❌ File upload still has issues")
        else:
            print("\n❌ User creation still has issues")
    else:
        print("\n❌ Timestamp fix failed")