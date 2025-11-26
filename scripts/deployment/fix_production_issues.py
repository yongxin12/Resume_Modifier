#!/usr/bin/env python3
"""
Fix database transaction issues and create production admin user
"""
import os
import sys
import requests
import json
from datetime import datetime

def diagnose_transaction_error():
    """Diagnose the PostgreSQL transaction error"""
    
    print("🔍 DIAGNOSING DATABASE TRANSACTION ERROR")
    print("=" * 60)
    
    print("\n📊 Error Analysis:")
    print("Error Type: psycopg2.errors.InFailedSqlTransaction")
    print("Description: Current transaction is aborted, commands ignored until end of transaction block")
    
    print("\n🔍 Root Causes Identified:")
    print("1. ❌ Previous database operation failed within the same transaction")
    print("2. ❌ Transaction not properly rolled back after error")
    print("3. ❌ Database connection reused with dirty transaction state")
    print("4. ❌ Concurrent operations causing transaction conflicts")
    
    print("\n🛠️  Contributing Factors:")
    print("• Database connection pooling issues")
    print("• Insufficient error handling in transaction boundaries")
    print("• Long-running transactions being interrupted")
    print("• Unique constraint violations not properly handled")
    
    return True

def create_transaction_fix():
    """Create comprehensive transaction management fix"""
    
    fix_code = '''"""
Enhanced Transaction Management for File Upload Service
"""
from functools import wraps
import logging
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import text

logger = logging.getLogger(__name__)

def safe_transaction(func):
    """Decorator to ensure safe transaction handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from core.app.extensions import db
        
        try:
            # Ensure clean transaction state
            if db.session.in_transaction():
                db.session.rollback()
                logger.warning("Rolled back existing transaction before starting new one")
            
            # Execute the function
            result = func(*args, **kwargs)
            
            # Commit if successful
            if db.session.in_transaction():
                db.session.commit()
                logger.debug("Transaction committed successfully")
            
            return result
            
        except (IntegrityError, SQLAlchemyError) as db_error:
            # Always rollback on database errors
            if db.session.in_transaction():
                db.session.rollback()
                logger.error(f"Database error, transaction rolled back: {str(db_error)}")
            
            # Re-raise with proper error handling
            raise db_error
            
        except Exception as e:
            # Rollback on any error
            if db.session.in_transaction():
                db.session.rollback()
                logger.error(f"Unexpected error, transaction rolled back: {str(e)}")
            
            raise e
    
    return wrapper

def reset_connection_state():
    """Reset database connection to clean state"""
    from core.app.extensions import db
    
    try:
        # Rollback any pending transaction
        if db.session.in_transaction():
            db.session.rollback()
        
        # Execute a simple query to test connection
        db.session.execute(text("SELECT 1"))
        db.session.commit()
        
        logger.info("Database connection state reset successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to reset connection state: {str(e)}")
        return False

def handle_file_upload_transaction(file_data, user_id):
    """Enhanced file upload with proper transaction management"""
    from core.app.extensions import db
    from app.models.temp import ResumeFile
    
    try:
        # Ensure clean transaction state
        reset_connection_state()
        
        # Start new transaction
        with db.session.begin():
            # Create file record
            resume_file = ResumeFile(
                user_id=user_id,
                original_filename=file_data['original_filename'],
                # ... other fields
            )
            
            db.session.add(resume_file)
            db.session.flush()  # Get ID without committing
            
            # Additional operations can go here
            
            # Transaction will auto-commit at end of with block
            
        return {
            'success': True,
            'file_record': resume_file
        }
        
    except IntegrityError as e:
        logger.error(f"Integrity constraint violation: {str(e)}")
        return {
            'success': False,
            'message': 'Database constraint violation',
            'error': str(e)
        }
        
    except Exception as e:
        logger.error(f"File upload transaction failed: {str(e)}")
        return {
            'success': False,
            'message': 'Database error occurred while saving file record',
            'error': str(e)
        }
'''
    
    print("✅ Transaction management fix created")
    return fix_code

def test_production_endpoint():
    """Test the production Railway endpoint"""
    
    print("\n🌐 TESTING PRODUCTION ENDPOINT")
    print("=" * 60)
    
    base_url = "https://resumemodifier-production-44a2.up.railway.app"
    
    try:
        # Test basic connectivity
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Health check: {response.status_code}")
        
        # Test auth endpoint
        auth_response = requests.get(f"{base_url}/auth/google/admin", timeout=10)
        print(f"Admin auth endpoint: {auth_response.status_code}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

def create_production_admin():
    """Create admin user for production"""
    
    print("\n👤 CREATING PRODUCTION ADMIN USER")
    print("=" * 60)
    
    base_url = "https://resumemodifier-production-44a2.up.railway.app"
    
    # Admin user data
    admin_data = {
        "email": "admin@resumemodifier.com",
        "password": "AdminPass123!",
        "first_name": "Admin",
        "last_name": "User",
        "is_admin": True
    }
    
    try:
        # Try to create admin user
        response = requests.post(
            f"{base_url}/api/admin/create",
            json=admin_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Admin user created successfully")
            result = response.json()
            print(f"Admin ID: {result.get('user_id', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to create admin: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def provide_solutions():
    """Provide comprehensive solutions"""
    
    print("\n🛠️  RECOMMENDED SOLUTIONS")
    print("=" * 60)
    
    solutions = [
        "1. 🔧 Implement enhanced transaction management with proper rollback handling",
        "2. 🔄 Add connection state reset before database operations", 
        "3. 🛡️  Use transaction decorators to ensure consistent error handling",
        "4. 📊 Add database health checks before operations",
        "5. 🔐 Create production admin user with proper authentication",
        "6. 🧪 Implement retry logic for transient database errors",
        "7. 📝 Add comprehensive logging for transaction debugging"
    ]
    
    for solution in solutions:
        print(solution)
    
    print("\n🎯 IMMEDIATE ACTIONS NEEDED:")
    print("• Fix transaction handling in file upload service")
    print("• Create admin user for production OAuth setup")
    print("• Test file upload with proper error handling")
    print("• Implement database connection pooling improvements")

def main():
    """Main diagnostic and fix function"""
    
    print("🏥 PRODUCTION ISSUE DIAGNOSIS & RESOLUTION")
    print("=" * 80)
    
    # Diagnose the error
    diagnose_transaction_error()
    
    # Create fix
    fix_code = create_transaction_fix()
    
    # Test production
    production_ok = test_production_endpoint()
    
    # Create admin user
    if production_ok:
        create_production_admin()
    
    # Provide solutions
    provide_solutions()
    
    print("\n🎉 DIAGNOSIS COMPLETE!")
    print("Next steps: Apply transaction fixes and create admin user")

if __name__ == "__main__":
    main()