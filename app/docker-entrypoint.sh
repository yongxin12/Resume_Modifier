#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database is ready!"

# Set up the environment
cd /app
export PYTHONPATH=/app

# Run database migrations
echo "Running database migrations..."
python -c "
import sys
sys.path.insert(0, '/app')

# Import directly from the Flask app factory
from core.app import create_app
app = create_app()

with app.app_context():
    from core.app.extensions import db
    db.create_all()
    print('Database tables created successfully!')
"

# Start the application
echo "Starting Flask application..."
exec "$@"