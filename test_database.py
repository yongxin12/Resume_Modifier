#!/usr/bin/env python3
"""
Database Connection Test Script
Run this to verify your database setup is working correctly.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def test_database_connection():
    print("🔍 Starting database connection test...")
    
    # Load environment variables
    load_dotenv()
    print("✅ Environment variables loaded")
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        print("💡 Please check your .env file contains DATABASE_URL")
        return False
    
    # Mask sensitive information in URL for display
    masked_url = database_url
    if '@' in database_url:
        parts = database_url.split('@')
        if ':' in parts[0]:
            auth_part = parts[0].split(':')
            if len(auth_part) >= 3:  # protocol://user:password
                masked_auth = f"{auth_part[0]}:{auth_part[1]}:***"
                masked_url = f"{masked_auth}@{parts[1]}"
    
    print(f"🔍 Testing connection to: {masked_url}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        print("✅ Database engine created")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text('SELECT 1')).scalar()
            print(f"✅ Raw connection successful! Test query result: {result}")
            
            # Test database existence for PostgreSQL
            if 'postgresql' in database_url:
                try:
                    db_name = database_url.split('/')[-1]
                    db_check = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :db_name"), {"db_name": db_name}).fetchone()
                    if db_check:
                        print(f"✅ Database '{db_name}' exists")
                    else:
                        print(f"⚠️  Database '{db_name}' may not exist")
                except Exception as db_check_error:
                    print(f"⚠️  Could not verify database existence: {db_check_error}")
            
            # Test Flask app context
            try:
                print("🔍 Testing Flask app integration...")
                from app import create_app
                from app.extensions import db
                
                app = create_app()
                print("✅ Flask app created successfully")
                
                with app.app_context():
                    # Test database connection in Flask context
                    db.session.execute(text('SELECT 1'))
                    print("✅ Flask app database connection successful!")
                    
                    # Try to get table information
                    try:
                        # For SQLAlchemy 2.x compatibility
                        inspector = db.inspect(db.engine)
                        tables = inspector.get_table_names()
                        print(f"📋 Database tables found: {len(tables)}")
                        if tables:
                            print(f"   Tables: {', '.join(tables)}")
                        else:
                            print("   No tables found - you may need to run migrations")
                    except Exception as table_error:
                        print(f"⚠️  Could not list tables: {table_error}")
                    
                    # Test basic model operations if tables exist
                    try:
                        from app.models.temp import User
                        user_count = User.query.count()
                        print(f"👥 Users in database: {user_count}")
                    except Exception as model_error:
                        print(f"⚠️  Could not query User model: {model_error}")
                        print("💡 You may need to run database migrations")
                    
            except ImportError as import_error:
                print(f"❌ Flask app import failed: {import_error}")
                print("💡 Make sure you're in the correct directory and dependencies are installed")
                return False
            except Exception as flask_error:
                print(f"❌ Flask app connection failed: {flask_error}")
                print("💡 Check your Flask app configuration")
                return False
                
        print("🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        
        # Provide specific troubleshooting hints
        error_str = str(e).lower()
        if 'access denied' in error_str:
            print("💡 Troubleshooting: User authentication failed")
            print("   - Check username and password in DATABASE_URL")
            print("   - Ensure database user exists and has proper permissions")
            if 'mysql' in database_url:
                print("   - Run: sudo mysql -e \"CREATE USER 'mysql'@'localhost' IDENTIFIED BY 'password'; GRANT ALL ON *.* TO 'mysql'@'localhost';\"")
        elif 'connection refused' in error_str or 'could not connect' in error_str:
            print("💡 Troubleshooting: Database server not running")
            if 'postgresql' in database_url:
                print("   - Start PostgreSQL: docker-compose up db -d")
                print("   - Check status: docker-compose ps db")
            elif 'mysql' in database_url:
                print("   - Start MySQL: sudo systemctl start mysql")
                print("   - Check status: sudo systemctl status mysql")
        elif 'database' in error_str and 'does not exist' in error_str:
            print("💡 Troubleshooting: Database does not exist")
            print("   - Create the database first")
            if 'postgresql' in database_url:
                print("   - Run: docker-compose exec db psql -U postgres -c \"CREATE DATABASE resume_app;\"")
            elif 'mysql' in database_url:
                print("   - Run: mysql -u root -p -e \"CREATE DATABASE resume_app;\"")
        
        return False

def print_environment_info():
    """Print current environment information for debugging"""
    print("\n🔧 Environment Information:")
    print("-" * 40)
    
    # Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Current directory
    print(f"📁 Current directory: {os.getcwd()}")
    
    # Check if .env file exists
    env_file = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_file):
        print(f"✅ .env file found at: {env_file}")
    else:
        print(f"❌ .env file not found at: {env_file}")
    
    # Check key environment variables (masked)
    load_dotenv()
    important_vars = ['DATABASE_URL', 'OPENAI_API_KEY', 'FLASK_SECRET_KEY']
    for var in important_vars:
        value = os.getenv(var)
        if value:
            if any(sensitive in var.upper() for sensitive in ['KEY', 'SECRET', 'PASSWORD']):
                masked = value[:10] + '...' if len(value) > 10 else '***'
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    print("-" * 40)

def main():
    print("=" * 60)
    print("🗄️  DATABASE CONNECTION TEST")
    print("=" * 60)
    
    # Print environment info
    print_environment_info()
    
    # Run the test
    success = test_database_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 DATABASE TEST PASSED - Your setup is working correctly!")
        print("💚 You can now run 'flask run' or 'python3 -m app.server'")
    else:
        print("❌ DATABASE TEST FAILED - Please fix the issues above")
        print("📖 See DATABASE_SETUP_TROUBLESHOOTING.md for detailed solutions")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())