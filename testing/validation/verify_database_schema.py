#!/usr/bin/env python3
"""
Database Schema Verification Script
Checks if the actual database schema matches the model definitions
"""

import os
import sys
from sqlalchemy import create_engine, inspect, MetaData
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/resume_app')

def verify_database_schema():
    """Verify database schema against expected structure"""
    print("=" * 80)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 80)
    print(f"\nConnecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
    
    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        # Expected tables
        expected_tables = {
            'users': ['id', 'username', 'password', 'email', 'first_name', 'last_name', 'city', 'bio', 'country', 'updated_at', 'created_at'],
            'resumes': ['user_id', 'serial_number', 'title', 'extracted_text', 'template_id', 'parsed_resume', 'updated_at', 'created_at'],
            'job_descriptions': ['user_id', 'serial_number', 'title', 'description', 'created_at'],
            'user_sites': ['id', 'user_id', 'resume_serial', 'subdomain', 'html_content', 'created_at', 'updated_at'],
            'resume_templates': ['id', 'name', 'description', 'style_config', 'sections', 'is_active', 'created_at', 'updated_at'],
            'google_auth_tokens': ['id', 'user_id', 'google_user_id', 'email', 'name', 'picture', 'access_token', 'refresh_token', 'token_expires_at', 'scope', 'created_at', 'updated_at'],
            'generated_documents': ['id', 'user_id', 'resume_id', 'template_id', 'google_doc_id', 'google_doc_url', 'document_title', 'job_description_used', 'generation_status', 'created_at', 'updated_at']
        }
        
        # Get actual tables
        actual_tables = inspector.get_table_names()
        print(f"\n✅ Database connected successfully!")
        print(f"\nActual tables in database: {len(actual_tables)}")
        
        all_tables_exist = True
        all_columns_match = True
        pk_issues = []
        
        for table_name in expected_tables:
            print(f"\n{'=' * 80}")
            print(f"Table: {table_name}")
            print(f"{'=' * 80}")
            
            if table_name not in actual_tables:
                print(f"❌ Table '{table_name}' MISSING from database!")
                all_tables_exist = False
                continue
            
            print(f"✅ Table exists")
            
            # Check columns
            actual_columns = [col['name'] for col in inspector.get_columns(table_name)]
            expected_columns = expected_tables[table_name]
            
            print(f"\nExpected columns: {len(expected_columns)}")
            print(f"Actual columns: {len(actual_columns)}")
            
            missing_columns = set(expected_columns) - set(actual_columns)
            extra_columns = set(actual_columns) - set(expected_columns)
            
            if missing_columns:
                print(f"❌ Missing columns: {missing_columns}")
                all_columns_match = False
            
            if extra_columns:
                print(f"⚠️  Extra columns: {extra_columns}")
            
            if not missing_columns and not extra_columns:
                print(f"✅ All columns match!")
            
            # Check primary keys
            pk = inspector.get_pk_constraint(table_name)
            if pk and pk['constrained_columns']:
                print(f"✅ Primary Key: {pk['constrained_columns']}")
            else:
                print(f"❌ NO PRIMARY KEY DEFINED!")
                pk_issues.append(table_name)
            
            # Check foreign keys
            fks = inspector.get_foreign_keys(table_name)
            if fks:
                print(f"Foreign Keys:")
                for fk in fks:
                    print(f"  - {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")
        
        # Summary
        print(f"\n{'=' * 80}")
        print("VERIFICATION SUMMARY")
        print(f"{'=' * 80}")
        
        if all_tables_exist:
            print("✅ All expected tables exist")
        else:
            print("❌ Some tables are missing")
        
        if all_columns_match:
            print("✅ All columns match expected schema")
        else:
            print("❌ Some columns don't match")
        
        if pk_issues:
            print(f"❌ Tables missing primary keys: {pk_issues}")
        else:
            print("✅ All tables have primary keys defined")
        
        # Check migration version
        try:
            with engine.connect() as conn:
                result = conn.execute("SELECT version_num FROM alembic_version")
                version = result.fetchone()[0]
                print(f"\n📊 Current migration version: {version}")
        except Exception as e:
            print(f"\n⚠️  Could not read migration version: {e}")
        
        print(f"\n{'=' * 80}")
        return all_tables_exist and all_columns_match and not pk_issues
        
    except Exception as e:
        print(f"\n❌ Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    success = verify_database_schema()
    sys.exit(0 if success else 1)
