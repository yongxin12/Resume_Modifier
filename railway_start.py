#!/usr/bin/env python3
"""
Railway deployment entry point for Resume Modifier
Handles proper Python path setup for module imports
"""

import sys
import os

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set environment variables
os.environ.setdefault('PYTHONPATH', current_dir)

if __name__ == "__main__":
    try:
        # Import and run the Flask application
        from app.server import app
        
        # Get port from environment (Railway sets this automatically)
        port = int(os.environ.get('PORT', 5001))
        host = os.environ.get('HOST', '0.0.0.0')
        
        print(f"🚀 Starting Resume Modifier on {host}:{port}")
        print(f"📍 Python Path: {sys.path[0]}")
        print(f"🔧 Working Directory: {os.getcwd()}")
        
        # Start the application
        app.run(
            host=host,
            port=port,
            debug=os.environ.get('FLASK_DEBUG', '0') == '1'
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print(f"📂 Current directory: {os.getcwd()}")
        print(f"📁 Directory contents: {os.listdir('.')}")
        if os.path.exists('app'):
            print(f"📁 App directory contents: {os.listdir('app')}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Startup Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)