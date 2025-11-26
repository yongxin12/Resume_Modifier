#!/usr/bin/env python3
"""
Migration script to add missing OAuth persistence columns to google_auth_tokens table.
Fixes the 'column "is_persistent" does not exist' error.
"""

import os
import psycopg2
from dotenv import load_dotenv

def migrate_google_auth_tokens():
    """Add missing columns to google_auth_tokens table"""
    load_dotenv()
    
    # Use public database URL for external access
    database_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
    if not database_url:
        # Try Railway public URL format
        database_url = 'postgresql://postgres:IEAChRNbxjHiLfxsFfoodmTWgxFDxSmV@shinkansen.proxy.rlwy.net:52352/railway'
    
    print("🔗 Connecting to production database...")
    
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'google_auth_tokens'
            ORDER BY ordinal_position
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 Current columns: {existing_columns}")
        
        # Define columns to add with their definitions
        columns_to_add = [
            ("is_persistent", "BOOLEAN DEFAULT TRUE NOT NULL"),
            ("auto_refresh_enabled", "BOOLEAN DEFAULT TRUE NOT NULL"),
            ("last_refresh_at", "TIMESTAMP"),
            ("refresh_attempts", "INTEGER DEFAULT 0 NOT NULL"),
            ("max_refresh_failures", "INTEGER DEFAULT 5 NOT NULL"),
            ("drive_quota_total", "BIGINT"),
            ("drive_quota_used", "BIGINT"),
            ("last_quota_check", "TIMESTAMP"),
            ("quota_warning_level", "VARCHAR(20) DEFAULT 'none'"),
            ("quota_warnings_sent", "JSON DEFAULT '[]'"),
            ("persistent_session_id", "VARCHAR(128) UNIQUE"),
            ("last_activity_at", "TIMESTAMP"),
            ("is_active", "BOOLEAN DEFAULT TRUE NOT NULL"),
            ("deactivated_reason", "VARCHAR(100)"),
            ("deactivated_at", "TIMESTAMP"),
        ]
        
        added_columns = []
        for column_name, column_def in columns_to_add:
            if column_name not in existing_columns:
                try:
                    print(f"➕ Adding column: {column_name}")
                    cursor.execute(f"ALTER TABLE google_auth_tokens ADD COLUMN {column_name} {column_def}")
                    added_columns.append(column_name)
                except psycopg2.errors.DuplicateColumn:
                    print(f"  ⏩ Column {column_name} already exists")
                    conn.rollback()
                except Exception as e:
                    print(f"  ⚠️  Error adding {column_name}: {e}")
                    conn.rollback()
            else:
                print(f"  ✓ Column {column_name} already exists")
        
        # Commit all changes
        conn.commit()
        
        # Verify updated schema
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'google_auth_tokens'
            ORDER BY ordinal_position
        """)
        final_columns = [row[0] for row in cursor.fetchall()]
        
        print(f"\n✅ Migration completed!")
        print(f"📊 Final columns ({len(final_columns)}): {final_columns}")
        
        if added_columns:
            print(f"🆕 Added columns: {added_columns}")
        else:
            print("ℹ️  No new columns needed to be added")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    print("🚀 Google Auth Tokens Table Migration")
    print("=" * 50)
    
    success = migrate_google_auth_tokens()
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Retry the OAuth flow: GET /auth/google/admin")
        print("2. Complete Google authentication")
        print("3. Test file uploads to verify Drive integration")
    else:
        print("\n❗ Migration failed. Please check the error messages.")

if __name__ == "__main__":
    main()