#!/usr/bin/env python3
"""
Verify that the password_reset_tokens table was created successfully
"""
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_table():
    """Verify the PasswordResetToken table and test basic operations."""
    from app import create_app
    from app.extensions import db
    from app.models.temp import PasswordResetToken, User
    
    app = create_app()
    
    with app.app_context():
        # Check if table exists by inspecting
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        print("Available tables:")
        for table in tables:
            print(f"  - {table}")
        
        if 'password_reset_tokens' in tables:
            print("\n✓ password_reset_tokens table exists!")
            
            # Get table info
            columns = inspector.get_columns('password_reset_tokens')
            print("\nTable columns:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            
            # Get indexes
            indexes = inspector.get_indexes('password_reset_tokens')
            print("\nTable indexes:")
            for idx in indexes:
                print(f"  - {idx['name']}: {idx['column_names']}")
            
            # Test token creation (without saving to DB)
            token_instance, raw_token = PasswordResetToken.create_token(
                user_id=1, 
                ip_address='127.0.0.1', 
                user_agent='Test User Agent'
            )
            
            print(f"\n✓ Token creation test successful!")
            print(f"  - Token length: {len(raw_token)}")
            print(f"  - Hash length: {len(token_instance.token_hash)}")
            print(f"  - Expires at: {token_instance.expires_at}")
            print(f"  - Is valid: {token_instance.is_valid()}")
            
        else:
            print("\n❌ password_reset_tokens table not found!")
            return False
    
    return True

if __name__ == "__main__":
    try:
        if verify_table():
            print("\n🎉 Database verification successful!")
        else:
            print("\n❌ Database verification failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)