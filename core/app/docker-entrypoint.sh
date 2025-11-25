#!/bin/bash
set -e

# Wait for the database to be ready
echo "🔄 Waiting for database to be ready..."
while ! nc -z $DB_HOST 5432; do
    echo "Database not ready, waiting..."
    sleep 2
done
echo "✅ Database is ready!"

# Run database setup
echo "🔄 Setting up database..."
cd /app
export PYTHONPATH="/app/core:$PYTHONPATH"
export FLASK_APP=core.app.server

# Simple database setup - just create tables directly
python -c "
import sys
import os
sys.path.insert(0, '/app/core')

from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    try:
        print('Creating database tables...')
        db.create_all()
        print('✅ Database tables created successfully')
    except Exception as e:
        print(f'Database setup error: {e}')
        # Try to continue anyway
"

echo "🚀 Starting Flask application..."
exec "$@"