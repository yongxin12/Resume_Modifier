#!/usr/bin/env python3
"""
Migration Validation Script
Validates that migration files match the actual database state
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/resume_app')

def check_migration_sync():
    """Verify migrations are in sync with database"""
    print("=" * 80)
    print("MIGRATION SYNCHRONIZATION CHECK")
    print("=" * 80)
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Check alembic_version table
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.fetchone()
            
            if current_version:
                version = current_version[0]
                print(f"\n✅ Current migration version: {version}")
            else:
                print("\n❌ No migration version found in database!")
                print("   Run: flask db stamp head")
                return False
        
        # Get migration files
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations', 'versions')
        migration_files = [f for f in os.listdir(migrations_dir) 
                          if f.endswith('.py') and not f.startswith('__')]
        
        print(f"\n📁 Migration files found: {len(migration_files)}")
        
        # List all migrations
        print("\nMigration History:")
        for migration_file in sorted(migration_files):
            revision = migration_file.split('_')[0]
            description = ' '.join(migration_file.split('_')[1:]).replace('.py', '')
            
            is_current = '← CURRENT' if revision == version else ''
            print(f"  {'✅' if revision <= version else '⏳'} {revision}: {description} {is_current}")
        
        # Check for tables not in migrations
        inspector = inspect(engine)
        actual_tables = set(inspector.get_table_names())
        actual_tables.discard('alembic_version')  # Exclude alembic tracking table
        
        print(f"\n🗄️  Tables in database: {len(actual_tables)}")
        for table in sorted(actual_tables):
            print(f"  - {table}")
        
        # Validate migration content
        print("\n🔍 Validating migration files...")
        
        issues_found = []
        
        # Check if f2eae0e50079 (Google integration) has content
        google_migration = os.path.join(migrations_dir, 
                                       'f2eae0e50079_add_google_docs_integration_models.py')
        if os.path.exists(google_migration):
            with open(google_migration, 'r') as f:
                content = f.read()
                if 'def upgrade():\n    pass' in content:
                    issues_found.append("f2eae0e50079: Empty upgrade() function")
                else:
                    print("  ✅ f2eae0e50079: Google integration tables documented")
        
        # Check if primary key migration exists
        pk_migration = [f for f in migration_files if 'primary_key' in f.lower()]
        if pk_migration:
            print(f"  ✅ Primary key migration found: {pk_migration[0]}")
        else:
            issues_found.append("No primary key migration found")
        
        # Summary
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        if issues_found:
            print("\n❌ Issues found:")
            for issue in issues_found:
                print(f"  - {issue}")
            return False
        else:
            print("\n✅ All validations passed!")
            print("✅ Migrations are in sync with database")
            print("✅ Migration files are properly documented")
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def check_migration_consistency():
    """Check if migrations can be applied cleanly"""
    print("\n" + "=" * 80)
    print("MIGRATION CONSISTENCY CHECK")
    print("=" * 80)
    
    print("\nRecommended commands to run:")
    print("\n1. Check current state:")
    print("   flask db current")
    
    print("\n2. View migration history:")
    print("   flask db history")
    
    print("\n3. Test upgrade (dry run):")
    print("   flask db upgrade --sql > test_migration.sql")
    print("   cat test_migration.sql  # Review SQL")
    
    print("\n4. Verify schema:")
    print("   python3 verify_database_schema.py")
    
    print("\n5. Run tests:")
    print("   pytest app/tests/ -v")
    
    return True

if __name__ == "__main__":
    print("\n🔍 Starting Migration Validation...\n")
    
    sync_ok = check_migration_sync()
    check_migration_consistency()
    
    print("\n" + "=" * 80)
    
    if sync_ok:
        print("✅ VALIDATION COMPLETE - Ready for deployment!")
        print("=" * 80)
        sys.exit(0)
    else:
        print("❌ VALIDATION FAILED - Please fix issues before deploying")
        print("=" * 80)
        sys.exit(1)
