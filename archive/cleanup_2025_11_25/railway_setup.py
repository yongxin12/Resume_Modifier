#!/usr/bin/env python3
"""
Railway Database Migration Setup Script
=====================================

This script helps set up the DATABASE_URL for Railway migration.

Usage:
1. Get your DATABASE_URL from Railway dashboard
2. Run: python railway_setup.py "postgresql://user:pass@host:port/db"
3. Or set as environment variable: export DATABASE_URL="postgresql://..."

Then run the migration:
python railway_migration_simple.py
"""

import os
import sys

def setup_railway_database_url():
    """Setup DATABASE_URL for Railway migration"""
    
    print("🚂 Railway Database Migration Setup")
    print("=" * 40)
    
    # Check if DATABASE_URL is already set
    current_url = os.environ.get('DATABASE_URL')
    if current_url:
        print(f"✅ DATABASE_URL is already set: {current_url[:30]}...")
        return current_url
    
    # Check command line argument
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
        os.environ['DATABASE_URL'] = database_url
        print(f"✅ DATABASE_URL set from command line: {database_url[:30]}...")
        return database_url
    
    # Interactive input
    print("\n📋 To get your DATABASE_URL from Railway:")
    print("1. Go to your Railway project dashboard")
    print("2. Click on your PostgreSQL database service")
    print("3. Go to 'Variables' tab")
    print("4. Copy the DATABASE_URL value")
    print()
    
    database_url = input("🔗 Enter your Railway DATABASE_URL: ").strip()
    
    if not database_url:
        print("❌ No DATABASE_URL provided!")
        return None
    
    # Validate URL format
    if not database_url.startswith('postgresql://'):
        print("⚠️  Warning: URL should start with 'postgresql://'")
    
    # Set environment variable
    os.environ['DATABASE_URL'] = database_url
    print(f"✅ DATABASE_URL set: {database_url[:30]}...")
    
    return database_url

def run_migration():
    """Run the Railway migration script"""
    import subprocess
    
    print("\n🔄 Running Railway migration...")
    try:
        result = subprocess.run(['python', 'railway_migration_simple.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration completed successfully!")
            print(result.stdout)
        else:
            print("❌ Migration failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚂 Railway Database Migration Helper")
    print("=" * 40)
    
    # Setup DATABASE_URL
    url = setup_railway_database_url()
    
    if not url:
        print("\n❌ Cannot proceed without DATABASE_URL")
        sys.exit(1)
    
    # Ask if user wants to run migration now
    run_now = input("\n🚀 Run migration now? (y/n): ").strip().lower()
    
    if run_now in ['y', 'yes']:
        success = run_migration()
        if success:
            print("\n🎉 Railway database migration completed!")
            print("You can now test file upload on Railway.")
        else:
            print("\n❌ Migration failed. Check the error messages above.")
    else:
        print("\n📋 To run migration later:")
        print("python railway_migration_simple.py")
        
    print("\n" + "=" * 40)