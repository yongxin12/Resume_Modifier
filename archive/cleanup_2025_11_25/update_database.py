#!/usr/bin/env python3
"""
Update database with admin field for Google Drive restriction
"""

import sys
import os

# Add paths for Railway environment
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.join(current_dir, 'core')
sys.path.insert(0, core_dir)
sys.path.insert(0, current_dir)

# Set DATABASE_URL for Railway
os.environ.setdefault('DATABASE_URL', "postgresql://postgres:IEAChRNbxjHiLfxsFfoodmTWgxFDxSmV@shinkansen.proxy.rlwy.net:52352/railway")

from app import create_app
from app.extensions import db
from app.models.temp import User

def update_database():
    """Add is_admin column to users table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Add the new column to the existing table
            print("Adding is_admin column to users table...")
            
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('users')]
            
            if 'is_admin' not in columns:
                # Add the column using raw SQL with new SQLAlchemy syntax
                with db.engine.connect() as conn:
                    conn.execute(db.text(
                        "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE NOT NULL"
                    ))
                    conn.commit()
                print("✅ Added is_admin column successfully")
                
                # Create first admin user if no users exist with admin privileges
                admin_count = User.query.filter_by(is_admin=True).count()
                if admin_count == 0:
                    # Find first user and make them admin, or create one
                    first_user = User.query.first()
                    if first_user:
                        first_user.is_admin = True
                        db.session.commit()
                        print(f"✅ Made user '{first_user.email}' an admin")
                    else:
                        print("⚠️  No users found. Please register a user and manually set is_admin=True")
            else:
                print("✅ is_admin column already exists")
                
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            return False
            
        return True

if __name__ == "__main__":
    if update_database():
        print("🎉 Database update completed successfully")
    else:
        print("💥 Database update failed")
        sys.exit(1)