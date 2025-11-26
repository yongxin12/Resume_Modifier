#!/usr/bin/env python3
"""
Local Database Manager Helper
Provides easy database management for local development and Railway production
"""

import os
import sys
import subprocess
import argparse

def check_railway_cli():
    """Check if Railway CLI is available"""
    try:
        result = subprocess.run(['railway', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def run_local_database_manager(action='info', local_db_url=None):
    """Run database manager with local database URL"""
    if local_db_url:
        env = os.environ.copy()
        env['DATABASE_URL'] = local_db_url
        
        cmd = ['python3', 'database_manager.py', action]
        print(f"🔧 Running locally: {' '.join(cmd)}")
        print(f"📊 Using database: {local_db_url}")
        
        result = subprocess.run(cmd, env=env)
        return result.returncode == 0
    else:
        print("❌ No local database URL provided")
        return False

def run_railway_database_manager(action='info'):
    """Run database manager with Railway's public database URL"""
    if not check_railway_cli():
        print("❌ Railway CLI not found. Install with: npm i -g @railway/cli")
        return False
    
    cmd = ['railway', 'run', '--service', 'Postgres', 'python3', 'database_manager.py', action]
    print(f"🚂 Running on Railway: {' '.join(cmd[2:])}")
    
    result = subprocess.run(cmd)
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description='Database Manager Helper')
    parser.add_argument('action', nargs='?', default='info', 
                       choices=['info', 'validate', 'update', 'columns', 'test'],
                       help='Database action to perform')
    parser.add_argument('--local', metavar='DATABASE_URL', 
                       help='Use local database (provide DATABASE_URL)')
    parser.add_argument('--railway', action='store_true', 
                       help='Use Railway database (default if no --local)')
    
    args = parser.parse_args()
    
    print("🗄️  Database Manager Helper")
    print("=" * 40)
    
    if args.local:
        # Local database mode
        print(f"🏠 Local Mode: {args.action}")
        success = run_local_database_manager(args.action, args.local)
    else:
        # Railway database mode (default)
        print(f"🚂 Railway Mode: {args.action}")
        success = run_railway_database_manager(args.action)
    
    if success:
        print("\n✅ Database operation completed successfully!")
    else:
        print("\n❌ Database operation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()