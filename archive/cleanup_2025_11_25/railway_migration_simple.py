#!/usr/bin/env python3
"""
Simple Railway Migration Script - Run this on Railway
Add missing columns to resume_files table
"""

import psycopg2
import os

# Get Railway database URL
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found")
    exit(1)

try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("Connected to Railway database")
    
    # Migration SQL
    migration_sql = """
    -- Add missing columns to resume_files table
    
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS display_filename VARCHAR(255);
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS page_count INTEGER;
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS paragraph_count INTEGER;
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS language VARCHAR(10);
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS keywords JSON;
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS processing_time FLOAT;
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS processing_metadata JSON;
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS has_thumbnail BOOLEAN DEFAULT FALSE;
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS thumbnail_path VARCHAR(500);
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS thumbnail_status VARCHAR(20) DEFAULT 'pending';
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS thumbnail_generated_at TIMESTAMP;
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS thumbnail_error TEXT;
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS google_drive_link VARCHAR(500);
    ALTER TABLE resume_files ADD COLUMN IF NOT EXISTS google_doc_link VARCHAR(500);
    
    -- Add constraint for thumbnail_status
    DO $$ 
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.check_constraints 
            WHERE constraint_name = 'check_valid_thumbnail_status'
        ) THEN
            ALTER TABLE resume_files ADD CONSTRAINT check_valid_thumbnail_status 
            CHECK (thumbnail_status IN ('pending', 'generating', 'completed', 'failed'));
        END IF;
    END $$;
    """
    
    # Execute migration
    cursor.execute(migration_sql)
    conn.commit()
    
    print("✅ Migration completed successfully!")
    
    # Verify columns exist
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'resume_files' 
        AND column_name IN ('display_filename', 'page_count', 'has_thumbnail', 'thumbnail_status')
        ORDER BY column_name;
    """)
    
    added_columns = [row[0] for row in cursor.fetchall()]
    print(f"✅ Verified columns: {', '.join(added_columns)}")
    
    cursor.close()
    conn.close()
    
    print("🎉 Railway database migration successful!")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    exit(1)