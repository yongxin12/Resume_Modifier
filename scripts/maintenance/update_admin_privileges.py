#!/usr/bin/env python3
"""
Update admin user privileges in production database
"""

import os
import psycopg2
from dotenv import load_dotenv

def update_admin_privileges():
    """Update admin user to have admin privileges"""
    # Load environment variables
    load_dotenv()
    
    # Get Railway database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    try:
        # Connect to database
        print("🔗 Connecting to production database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # First check current status
        cursor.execute("""
            SELECT id, email, is_admin, created_at 
            FROM users 
            WHERE email = %s
        """, ('admin@resumemodifier.com',))
        
        result = cursor.fetchone()
        
        if not result:
            print("❌ Admin user not found")
            return False
            
        user_id, email, is_admin, created_at = result
        print(f"📋 Current admin user status:")
        print(f"   ID: {user_id}")
        print(f"   Email: {email}")
        print(f"   is_admin: {is_admin}")
        print(f"   Created: {created_at}")
        
        if is_admin:
            print("✅ Admin privileges already enabled!")
            return True
        
        # Update admin privileges
        print("🔧 Updating admin privileges...")
        cursor.execute("""
            UPDATE users 
            SET is_admin = true 
            WHERE email = %s
        """, ('admin@resumemodifier.com',))
        
        # Commit the change
        conn.commit()
        
        # Verify the update
        cursor.execute("""
            SELECT is_admin 
            FROM users 
            WHERE email = %s
        """, ('admin@resumemodifier.com',))
        
        updated_result = cursor.fetchone()
        
        if updated_result and updated_result[0]:
            print("✅ Admin privileges successfully enabled!")
            print("🎉 admin@resumemodifier.com now has admin access")
            return True
        else:
            print("❌ Failed to update admin privileges")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = update_admin_privileges()
    exit(0 if success else 1)