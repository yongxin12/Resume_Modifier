#!/usr/bin/env python3
"""
Check admin user status in production database
"""

import os
import psycopg2
from dotenv import load_dotenv

def check_admin_status():
    """Check if admin user exists and has admin privileges"""
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
        
        # Check admin user
        cursor.execute("""
            SELECT id, email, is_admin, created_at 
            FROM users 
            WHERE email = %s
        """, ('admin@resumemodifier.com',))
        
        result = cursor.fetchone()
        
        if result:
            user_id, email, is_admin, created_at = result
            print(f"✅ Admin user found:")
            print(f"   ID: {user_id}")
            print(f"   Email: {email}")
            print(f"   is_admin: {is_admin}")
            print(f"   Created: {created_at}")
            
            if is_admin:
                print("✅ Admin privileges: ENABLED")
                return True
            else:
                print("❌ Admin privileges: DISABLED")
                print("   Need to run: UPDATE users SET is_admin = true WHERE email = 'admin@resumemodifier.com';")
                return False
        else:
            print("❌ Admin user not found")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_admin_status()