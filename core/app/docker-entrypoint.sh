#!/bin/bash
set -e

# Wait for the database to be ready
echo "🔄 Waiting for database to be ready..."
while ! nc -z $DB_HOST 5432; do
    echo "Database not ready, waiting..."
    sleep 2
done
echo "✅ Database is ready!"

# Run database migrations
echo "🔄 Running database migrations..."
python -c "
from app import create_app
from flask_migrate import upgrade
from app.extensions import db

app = create_app()
with app.app_context():
    try:
        print('Running migrations...')
        upgrade()
        print('✅ Migrations completed successfully')
    except Exception as e:
        print(f'Migration error: {e}')
        print('Creating tables directly...')
        db.create_all()
        print('✅ Tables created via SQLAlchemy')
"

echo "🚀 Starting Flask application..."
exec "$@"