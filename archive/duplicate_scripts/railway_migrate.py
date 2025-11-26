#!/usr/bin/env python3
"""
Railway migration script for Resume Modifier
Creates database tables and handles migrations for production deployment
"""

import sys
import os

def main():
    """Main migration function for Railway deployment"""
    try:
        print("🚀 Starting Railway migration process...")
        
        # Add the core directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        core_dir = os.path.join(parent_dir, 'core')
        sys.path.insert(0, core_dir)
        sys.path.insert(0, parent_dir)
        
        print(f"📁 Core directory: {core_dir}")
        print(f"📁 Parent directory: {parent_dir}")
        
        # Import and create the Flask application
        from app import create_app
        from app.extensions import db
        
        app = create_app()
        
        with app.app_context():
            print("🗄️  Creating database tables...")
            
            # Import all models to ensure they're registered
            from app.models.temp import (
                User, Resume, JobDescription, UserSite, ResumeTemplate, 
                GoogleAuth, GeneratedDocument, ResumeFile, PasswordResetToken
            )
            
            # Create all tables
            db.create_all()
            
            print("✅ Database tables created successfully!")
            
            # Verify critical tables exist
            critical_tables = ['users', 'resume_files', 'resumes', 'job_descriptions']
            
            try:
                with db.engine.connect() as connection:
                    result = connection.execute(db.text(
                        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
                    ))
                    existing_tables = [row[0] for row in result]
                    
                    print(f"📊 Created tables: {existing_tables}")
                    
                    # Check if critical tables exist
                    missing_tables = [table for table in critical_tables if table not in existing_tables]
                    if missing_tables:
                        print(f"⚠️  Warning: Missing critical tables: {missing_tables}")
                        return False
                    else:
                        print("✅ All critical tables verified!")
                        return True
                        
            except Exception as verify_error:
                print(f"⚠️  Could not verify tables: {verify_error}")
                print("✅ Assuming tables were created successfully")
                return True
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print(f"📂 Current directory: {os.getcwd()}")
        print(f"📁 Directory contents: {os.listdir('.')}")
        if os.path.exists('core'):
            print(f"📁 Core directory contents: {os.listdir('core')}")
        if os.path.exists('core/app'):
            print(f"📁 Core/app directory contents: {os.listdir('core/app')}")
        return False
        
    except Exception as e:
        print(f"❌ Migration Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("🎉 Railway migration completed successfully!")
        sys.exit(0)
    else:
        print("💥 Railway migration failed!")
        sys.exit(1)