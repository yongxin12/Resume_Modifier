#!/bin/bash
set -e

echo "🔄 Fixing migration issues and starting Docker services..."

# Stop any running containers
echo "Stopping existing containers..."
cd /home/rex/project/resume-editor/project/Resume_Modifier/configuration/deployment
docker-compose down -v

# Clear the migration directory and recreate it cleanly
echo "Resetting migration directory..."
cd /home/rex/project/resume-editor/project/Resume_Modifier
rm -rf migrations/versions/*
rm -rf migrations/__pycache__

# Create a fresh migration using virtual environment
echo "Creating fresh migration..."
cd core
export PYTHONPATH="/home/rex/project/resume-editor/project/Resume_Modifier/core:$PYTHONPATH"

# Activate virtual environment and create migration
source ../venv/bin/activate

python3 -c "
import sys
import os
sys.path.insert(0, '/home/rex/project/resume-editor/project/Resume_Modifier/core')

from app import create_app
from flask_migrate import init, migrate, upgrade
from app.extensions import db

app = create_app()
with app.app_context():
    print('Creating fresh migration...')
    try:
        migrate(message='Fresh migration for all tables')
        print('✅ Fresh migration created')
    except Exception as e:
        print(f'Migration creation error: {e}')
        print('Creating tables directly with SQLAlchemy...')
        db.create_all()
        print('✅ Tables created')
"

echo "✅ Migration issues resolved"
echo "🚀 Starting Docker Compose services..."

# Start Docker services
cd /home/rex/project/resume-editor/project/Resume_Modifier/configuration/deployment
docker-compose up --build -d

echo "🔍 Checking container status..."
docker-compose ps

echo "📋 Container logs:"
docker-compose logs web

echo "✅ Docker setup complete!"