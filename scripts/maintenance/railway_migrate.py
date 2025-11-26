#!/usr/bin/env python3
"""
Railway Database Migration Helper (LOCAL DEVELOPMENT TOOL)

This script is for LOCAL development use only - it requires Railway CLI.
For Railway deployment, use: scripts/deployment/railway_deploy_migrate.py

Usage (from your local machine):
    ./scripts/maintenance/railway_migrate.py upgrade   # Apply migrations
    ./scripts/maintenance/railway_migrate.py current   # Show current version
    ./scripts/maintenance/railway_migrate.py history   # Show history

Prerequisites:
    - Railway CLI: npm i -g @railway/cli
    - Logged in: railway login
"""

import subprocess
import sys
import os
import re

def run_command(cmd, capture=True):
    """Run a shell command and return output"""
    try:
        if capture:
            result = subprocess.run(
                cmd, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True
            )
            return result.stdout
        else:
            subprocess.run(cmd, shell=True, check=True)
            return None
    except subprocess.CalledProcessError as e:
        return None

def check_prerequisites():
    """Check if Railway CLI is installed and user is logged in"""
    print("🚄 Railway Database Migration Tool")
    print("=" * 50)
    print()
    
    # Check Railway CLI
    if run_command("railway --version") is None:
        print("❌ Error: Railway CLI not found")
        print("📥 Install it with: npm i -g @railway/cli")
        return False
    
    # Check if logged in
    if run_command("railway whoami") is None:
        print("❌ Error: Not logged in to Railway")
        print("🔐 Run: railway login")
        return False
    
    print("✅ Railway CLI detected")
    print()
    return True

def get_database_url():
    """Get Railway's public database URL"""
    print("📡 Fetching Railway database credentials...")
    print()
    
    # First check if DATABASE_URL is already in environment
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        print(f"✅ Using DATABASE_URL from environment: {database_url[:30]}...")
        return database_url
    
    # Get variables from Postgres service
    output = run_command("railway variables --service Postgres 2>&1")
    
    if not output:
        print("❌ Error: Could not fetch Railway variables")
        print("🔍 Make sure you have a Postgres service")
        return None
    
    # Find DATABASE_PUBLIC_URL
    lines = output.split('\n')
    collecting = False
    url_parts = []
    
    for line in lines:
        if 'DATABASE_PUBLIC_URL' in line:
            collecting = True
            continue
        
        if collecting:
            # Stop at the next separator line
            if '──────' in line or '══════' in line:
                break
            
            # Extract URL part (remove table borders)
            cleaned = re.sub(r'[│║]', '', line).strip()
            if cleaned and 'postgresql://' in cleaned:
                url_parts.append(cleaned)
            elif cleaned and url_parts:  # Continue collecting multiline URL
                url_parts.append(cleaned)
    
    if not url_parts:
        print("❌ Error: Could not find DATABASE_PUBLIC_URL")
        print("🔍 Make sure your Railway project has a Postgres service")
        print()
        print("Manual steps:")
        print("1. railway variables --service Postgres")
        print("2. Copy the DATABASE_PUBLIC_URL value")
        print("3. DATABASE_URL=\"<url>\" flask db <command>")
        return None
    
    # Join all parts and extract just the URL
    full_text = ''.join(url_parts)
    match = re.search(r'(postgresql://[^\s│║]+)', full_text)
    
    if not match:
        print(f"❌ Error: Could not parse URL from: {full_text}")
        return None
    
    url = match.group(1)
    
    # Extract host for display
    host_match = re.search(r'@([^:]+):', url)
    host = host_match.group(1) if host_match else "unknown"
    
    print("✅ Database URL retrieved")
    print(f"🔗 Host: {host}")
    print()
    
    return url

def run_migration(command, database_url):
    """Run Flask migration command with the database URL"""
    # Map command names
    valid_commands = {
        'upgrade': 'Apply pending migrations',
        'downgrade': 'Revert last migration',
        'current': 'Show current version',
        'history': 'Show migration history',
        'stamp': 'Mark database as up to date'
    }
    
    if command not in valid_commands:
        print(f"❌ Unknown command: {command}")
        print()
        print("Valid commands:")
        for cmd, desc in valid_commands.items():
            print(f"  {cmd:12} - {desc}")
        return False
    
    # Confirm action
    if command in ['upgrade', 'downgrade', 'stamp']:
        response = input(f"🎯 {valid_commands[command]}? (y/n) ")
        print()
        if response.lower() != 'y':
            print("❌ Migration cancelled")
            return False
    
    print("🔄 Running migration...")
    print("━" * 50)
    print()
    
    # Set environment variable and run Flask command from core directory
    env = os.environ.copy()
    env['DATABASE_URL'] = database_url
    env['PYTHONPATH'] = os.path.join(os.getcwd(), 'core')
    
    try:
        # Change to core directory where migrations are located
        result = subprocess.run(
            f"cd core && flask db {command}",
            shell=True,
            env=env
        )
        
        print()
        print("━" * 50)
        
        if result.returncode == 0:
            print("✅ Migration complete!")
        else:
            print("❌ Migration failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print()
    print("💡 Tips:")
    print("   • Check status: ./scripts/railway_migrate.py current")
    print("   • View history: ./scripts/railway_migrate.py history")
    print("   • Connect to DB: railway connect postgres")
    print()
    
    return True

def main():
    """Main entry point"""
    # Get command from arguments (default to 'upgrade')
    command = sys.argv[1] if len(sys.argv) > 1 else 'upgrade'
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Get database URL
    database_url = get_database_url()
    if not database_url:
        sys.exit(1)
    
    # Run migration
    success = run_migration(command, database_url)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
