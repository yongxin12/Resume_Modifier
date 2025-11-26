"""
Simple OAuth Session Validation
Quick check that the OAuth session fixes are properly installed
"""

import sys
import logging

sys.path.append('/home/rex/project/resume-editor/project/Resume_Modifier')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def validate_oauth_fixes():
    """Validate that OAuth session fixes are properly installed."""
    
    checks_passed = []
    
    # Check 1: Can import fixed services
    try:
        from app.services.google_admin_auth_fixed import GoogleAdminAuthServiceFixed
        from app.services.flask_session_config import configure_flask_sessions_for_docker
        checks_passed.append("✅ OAuth fixed services imported successfully")
    except ImportError as e:
        checks_passed.append(f"❌ Import error: {e}")
        return checks_passed
    
    # Check 2: Can create Flask app with session config
    try:
        from flask import Flask
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'
        
        session_config = configure_flask_sessions_for_docker(app)
        checks_passed.append(f"✅ Session configuration applied ({len(session_config)} settings)")
    except Exception as e:
        checks_passed.append(f"❌ Session configuration failed: {e}")
    
    # Check 3: Required files exist
    import os
    required_files = [
        '/home/rex/project/resume-editor/project/Resume_Modifier/app/services/google_admin_auth_fixed.py',
        '/home/rex/project/resume-editor/project/Resume_Modifier/app/services/flask_session_config.py',
        '/home/rex/project/resume-editor/project/Resume_Modifier/app/extensions.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            checks_passed.append(f"✅ Required file exists: {os.path.basename(file_path)}")
        else:
            checks_passed.append(f"❌ Missing file: {file_path}")
    
    return checks_passed

def main():
    print("🔍 OAuth Session Fix Validation")
    print("=" * 40)
    
    checks = validate_oauth_fixes()
    
    for check in checks:
        print(check)
    
    failed_checks = [c for c in checks if c.startswith("❌")]
    
    print("=" * 40)
    if failed_checks:
        print(f"❌ {len(failed_checks)} issues found")
        print("🔧 Please address the issues above before proceeding")
        return False
    else:
        print("✅ All OAuth session fixes are properly installed!")
        print("🚀 Ready to restart Flask application and test OAuth flow")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)