#!/bin/bash

# Railway Database Migration Script
# This script runs database migrations using Railway's public database URL

set -e  # Exit on error

echo "🚄 Railway Database Migration Tool"
echo "===================================="
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Error: Railway CLI not found"
    echo "📥 Install it with: npm i -g @railway/cli"
    echo "🔗 Or visit: https://docs.railway.app/develop/cli"
    exit 1
fi

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "❌ Error: Not logged in to Railway"
    echo "🔐 Run: railway login"
    exit 1
fi

echo "✅ Railway CLI detected"
echo ""

# Switch to Postgres service and get DATABASE_PUBLIC_URL
echo "📡 Fetching Railway database credentials..."
echo ""

# Get PUBLIC_URL from Railway - use a temporary file for cleaner parsing
TEMP_FILE=$(mktemp)
railway variables --service Postgres 2>/dev/null > "$TEMP_FILE"

# Extract the DATABASE_PUBLIC_URL value by finding the line and the next few lines
PUBLIC_URL=$(grep -A 5 "DATABASE_PUBLIC_URL" "$TEMP_FILE" | grep "postgresql://" | head -1 | sed 's/^[^p]*//; s/[│║ ]*$//' | tr -d ' \t\r\n' | sed 's/│//g; s/║//g')

# Clean up
rm -f "$TEMP_FILE"

if [ -z "$PUBLIC_URL" ]; then
    echo "❌ Error: Could not retrieve DATABASE_PUBLIC_URL"
    echo "🔍 Debugging info:"
    echo ""
    railway variables --service Postgres 2>&1 | head -10
    echo ""
    echo "Manual fix:"
    echo "1. Get the URL: railway variables --service Postgres | grep -A 3 DATABASE_PUBLIC_URL"
    echo "2. Run: DATABASE_URL=\"postgresql://...\" flask db upgrade"
    exit 1
fi

# Validate URL format
if [[ ! "$PUBLIC_URL" =~ ^postgresql:// ]]; then
    echo "❌ Error: Invalid URL format: $PUBLIC_URL"
    echo "📋 Please set DATABASE_URL manually:"
    echo "   railway variables --service Postgres | grep -A 3 DATABASE_PUBLIC_URL"
    exit 1
fi

echo "✅ Database URL retrieved"
HOST=$(echo "$PUBLIC_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
if [ ! -z "$HOST" ]; then
    echo "🔗 Host: $HOST"
fi
echo ""

# Ask for confirmation
read -p "🎯 Run database migration? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration cancelled"
    exit 0
fi

echo ""
echo "🔄 Running migration..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Export the public URL and run migration
export DATABASE_URL="$PUBLIC_URL"

# Check which migration command to run
if [ "$1" == "upgrade" ] || [ -z "$1" ]; then
    echo "⬆️  Upgrading database to latest version..."
    flask db upgrade
elif [ "$1" == "downgrade" ]; then
    echo "⬇️  Downgrading database..."
    flask db downgrade
elif [ "$1" == "current" ]; then
    echo "📍 Current database version:"
    flask db current
elif [ "$1" == "history" ]; then
    echo "📜 Migration history:"
    flask db history
elif [ "$1" == "stamp" ]; then
    echo "🏷️  Stamping database..."
    flask db stamp head
else
    echo "❌ Unknown command: $1"
    echo ""
    echo "Usage: ./scripts/railway_migrate.sh [command]"
    echo ""
    echo "Commands:"
    echo "  upgrade   - Apply pending migrations (default)"
    echo "  downgrade - Revert last migration"
    echo "  current   - Show current migration version"
    echo "  history   - Show migration history"
    echo "  stamp     - Mark database as up to date without running migrations"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Migration complete!"
echo ""
echo "💡 Tips:"
echo "   • Check migration status: ./scripts/railway_migrate.sh current"
echo "   • View history: ./scripts/railway_migrate.sh history"
echo "   • Connect to DB: railway connect postgres"
echo ""
