#!/usr/bin/env python3
"""
Test script to validate that the PostgreSQL transaction error is fixed
by checking the database schema and model compatibility
"""

import sys
import os
import traceback

# Add the project root to Python path
sys.path.insert(0, '/home/rex/project/resume-editor/project/Resume_Modifier/core')

def test_model_compatibility():
    """Test if the ResumeFile model can be instantiated with the fields that were causing the error"""
    
    try:
        print("🔍 Testing ResumeFile model compatibility...")
        
        # Import required modules
        from datetime import datetime
        
        # Create test data matching the original error parameters
        test_data = {
            'user_id': 8,
            'original_filename': 'Rex(Yongxin Zheng) Resume (1) (1).pdf',
            'display_filename': 'Rex(Yongxin Zheng) Resume (1) (1).pdf',  # This was the problematic field
            'stored_filename': 'user_8_1763858155770035_rexyongxin_zheng_resume_1_1.pdf',
            'file_size': 128962,
            'mime_type': 'application/pdf',
            'storage_type': 'local',
            'file_path': '/tmp/resume_files/users/8/Rex(Yongxin Zheng) Resume (1) (1).pdf',
            's3_bucket': None,
            'file_hash': '4ad80ff84f7ce0c817b893ddcf3f0a8fdcab86c1a34bd0a0560e9940652051b6',
            'google_drive_file_id': None,
            'google_doc_id': None,
            'google_drive_link': None,
            'google_doc_link': None,
            'is_shared_with_user': False,
            'is_processed': True,
            'extracted_text': "Sample extracted text...",
            'processing_status': 'completed',
            'processing_error': None,
            # These fields were missing and causing the error:
            'page_count': None,
            'paragraph_count': None,
            'language': None,
            'keywords': [],
            'processing_time': None,
            'processing_metadata': {},
            'is_duplicate': False,
            'duplicate_sequence': 0,
            'original_file_id': None,
            'has_thumbnail': False,
            'thumbnail_path': None,
            'thumbnail_status': 'pending',
            'thumbnail_generated_at': None,
            'thumbnail_error': None,
            'is_active': True,
            'deleted_at': None,
            'deleted_by': None,
            'tags': [],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        print("✅ Test data prepared successfully")
        
        # Test if we can import the model without errors
        try:
            from core.app.models.temp import ResumeFile
            print("✅ ResumeFile model imported successfully")
        except Exception as e:
            print(f"❌ Failed to import ResumeFile model: {e}")
            return False
        
        # Test if we can create a model instance
        try:
            # Create ResumeFile instance with all the fields that were in the original error
            resume_file = ResumeFile(**test_data)
            print("✅ ResumeFile instance created successfully with all Railway database fields")
            
            # Test the methods that were missing
            if hasattr(resume_file, 'set_thumbnail_completed'):
                print("✅ set_thumbnail_completed method exists")
            else:
                print("❌ set_thumbnail_completed method missing")
                return False
                
            if hasattr(resume_file, 'set_thumbnail_failed'):
                print("✅ set_thumbnail_failed method exists")
            else:
                print("❌ set_thumbnail_failed method missing")
                return False
                
            if hasattr(resume_file, 'get_display_filename'):
                display_name = resume_file.get_display_filename()
                print(f"✅ get_display_filename method works: '{display_name}'")
            else:
                print("❌ get_display_filename method missing")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create ResumeFile instance: {e}")
            traceback.print_exc()
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connection and check if the schema has been updated"""
    
    try:
        import psycopg2
        
        # Connect to the database
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='resume_app',
            user='postgres',
            password='postgres'
        )
        
        print("✅ Database connection successful")
        
        cursor = conn.cursor()
        
        # Check if the new columns exist in the resume_files table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'resume_files' 
            AND column_name IN ('display_filename', 'page_count', 'paragraph_count', 'language', 'keywords', 'processing_time', 'processing_metadata', 'has_thumbnail', 'thumbnail_path', 'thumbnail_status', 'thumbnail_generated_at', 'thumbnail_error')
            ORDER BY column_name;
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        expected_columns = [
            'display_filename', 'page_count', 'paragraph_count', 'language', 
            'keywords', 'processing_time', 'processing_metadata', 'has_thumbnail', 
            'thumbnail_path', 'thumbnail_status', 'thumbnail_generated_at', 'thumbnail_error'
        ]
        
        missing_columns = [col for col in expected_columns if col not in existing_columns]
        
        if missing_columns:
            print(f"❌ Missing columns in database: {missing_columns}")
            return False
        else:
            print("✅ All required columns exist in database")
            print(f"   Found columns: {existing_columns}")
            return True
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all tests to validate the fix"""
    
    print("🧪 Testing PostgreSQL Transaction Error Fix")
    print("=" * 50)
    
    # Test 1: Model compatibility
    model_test = test_model_compatibility()
    print()
    
    # Test 2: Database schema
    db_test = test_database_connection()
    print()
    
    if model_test and db_test:
        print("🎉 SUCCESS: PostgreSQL transaction error should be resolved!")
        print("   - ResumeFile model has all required fields")
        print("   - Database schema includes all required columns")
        print("   - Model methods are available")
        print("\n📋 Summary of the fix:")
        print("   ✅ Added display_filename column to ResumeFile model")
        print("   ✅ Added content analysis fields (page_count, paragraph_count, etc.)")
        print("   ✅ Added thumbnail fields (has_thumbnail, thumbnail_path, etc.)")
        print("   ✅ Added missing model methods (set_thumbnail_completed, set_thumbnail_failed)")
        print("   ✅ Updated database schema to match Railway database")
        return True
    else:
        print("💥 FAILURE: Issues still exist that need to be resolved")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)