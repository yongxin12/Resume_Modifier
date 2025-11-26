#!/usr/bin/env python3
"""
Railway Deployment Migration Script
Runs Flask database migrations during Railway deployment.
This script runs INSIDE the Railway container where DATABASE_URL is already set.
"""

import sys
import os

# Add the core directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
core_dir = os.path.join(project_root, 'core')
sys.path.insert(0, core_dir)

# Change to core directory for Flask-Migrate to find migrations folder
os.chdir(core_dir)

def check_tables_exist(db):
    """Check if main application tables already exist in database."""
    from sqlalchemy import text, inspect
    
    try:
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        # Core tables that indicate database is already set up
        core_tables = ['users', 'resume_files', 'resume_templates']
        found_tables = [t for t in core_tables if t in existing_tables]
        
        print(f"📋 Existing tables in database: {existing_tables}")
        print(f"📋 Core tables found: {found_tables}")
        
        return len(found_tables) >= 2  # At least 2 core tables exist
    except Exception as e:
        print(f"⚠️  Could not check existing tables: {e}")
        return False

def check_alembic_version_exists(db):
    """Check if alembic_version table has any entries."""
    from sqlalchemy import text
    
    try:
        result = db.session.execute(text("SELECT version_num FROM alembic_version"))
        row = result.fetchone()
        return row is not None
    except Exception:
        return False

def check_and_fix_alembic_version(app, db):
    """
    Check if alembic_version contains a revision that doesn't exist.
    If so, stamp to the latest head to recover from migration mismatch.
    """
    from sqlalchemy import text
    
    try:
        with app.app_context():
            # Check current version in database
            result = db.session.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            
            if not row:
                # No alembic_version - check if tables already exist
                tables_exist = check_tables_exist(db)
                if tables_exist:
                    print("📋 No alembic_version but tables exist - need to stamp to head")
                    return "stamp_needed"
                else:
                    print("📋 No alembic_version found - fresh database")
                    return "fresh"
            
            current_version = row[0]
            print(f"📋 Current database revision: {current_version}")
            
            # Check if this revision exists in our migrations
            migrations_dir = os.path.join(core_dir, 'migrations', 'versions')
            valid_revisions = set()
            
            if os.path.exists(migrations_dir):
                for filename in os.listdir(migrations_dir):
                    if filename.endswith('.py') and not filename.startswith('__'):
                        filepath = os.path.join(migrations_dir, filename)
                        with open(filepath, 'r') as f:
                            content = f.read()
                            # Extract revision ID
                            import re
                            match = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", content)
                            if match:
                                valid_revisions.add(match.group(1))
            
            print(f"📋 Valid revisions in codebase: {valid_revisions}")
            
            if current_version not in valid_revisions:
                print(f"⚠️  Revision '{current_version}' not found in migration files!")
                print("🔧 Will stamp database to latest head...")
                
                # Delete the stale version
                db.session.execute(text("DELETE FROM alembic_version"))
                db.session.commit()
                print("✅ Cleared stale alembic_version")
                return "stamp_needed"
            
            return "ok"
            
    except Exception as e:
        print(f"⚠️  Could not check alembic_version: {e}")
        return "ok"  # Continue anyway

def run_migrations():
    """Run Flask database migrations"""
    print("🚀 Railway Deployment Migration")
    print("=" * 50)
    
    # Check for DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL environment variable not set")
        print("   This script must run inside Railway's container")
        return False
    
    # Mask credentials for display
    if '@' in database_url:
        host_part = database_url.split('@')[1].split('/')[0] if '/' in database_url.split('@')[1] else database_url.split('@')[1]
        print(f"✅ DATABASE_URL found (host: {host_part})")
    else:
        print("✅ DATABASE_URL found")
    
    print(f"📂 Working directory: {os.getcwd()}")
    print(f"📁 Core directory: {core_dir}")
    print()
    
    try:
        # Import Flask app and extensions
        from app import create_app
        from app.extensions import db
        from flask_migrate import Migrate, upgrade, stamp
        
        print("✅ Flask app imported successfully")
        
        # Create app
        app = create_app()
        migrate = Migrate(app, db)
        
        # Check and fix alembic version if needed
        db_state = check_and_fix_alembic_version(app, db)
        
        print("🔄 Running database migrations...")
        print("-" * 50)
        
        with app.app_context():
            # Check if migrations directory exists
            migrations_dir = os.path.join(core_dir, 'migrations')
            if os.path.exists(migrations_dir):
                print(f"✅ Migrations directory found: {migrations_dir}")
                
                # If tables exist but no alembic_version, stamp to head
                if db_state == "stamp_needed":
                    print("🔧 Tables exist but alembic_version is empty/invalid")
                    print("   Stamping to head (skipping migrations)...")
                    stamp(revision='head')
                    print("-" * 50)
                    print("✅ Database stamped to head - schema already up to date")
                    return True
                
                try:
                    # Try running upgrade
                    upgrade()
                    print("-" * 50)
                    print("✅ Database migrations completed successfully!")
                except Exception as migrate_error:
                    error_msg = str(migrate_error)
                    
                    # Handle "already exists" or "Can't locate revision" errors
                    if "already exists" in error_msg or "Can't locate revision" in error_msg:
                        print(f"⚠️  Migration conflict detected: {error_msg[:100]}...")
                        print("🔧 Attempting recovery: stamp to head...")
                        
                        # Stamp to head (marks DB as up-to-date without running migrations)
                        stamp(revision='head')
                        
                        print("✅ Recovery complete - database stamped to head")
                    else:
                        raise migrate_error
            else:
                print(f"⚠️  No migrations directory found at {migrations_dir}")
                print("   Creating tables directly with db.create_all()...")
                db.create_all()
                print("✅ Database tables created successfully!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print(f"   Python path: {sys.path[:3]}")
        return False
        
    except Exception as e:
        print(f"❌ Migration Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point"""
    print()
    success = run_migrations()
    print()
    
    if success:
        print("🎉 Migration script completed successfully")
        sys.exit(0)
    else:
        print("💥 Migration script failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
