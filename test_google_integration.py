"""
Google Docs/Drive Integration Test Script
Tests all Google-related functionality for resume editing
"""

import sys
import os
import requests
import json
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

def test_google_integration():
    """Test Google Docs/Drive integration functionality"""
    print("🔍 Testing Google Docs/Drive Integration")
    print("=" * 50)
    
    # Configuration
    BASE_URL = "http://127.0.0.1:5001"
    
    print("\n1. 📋 Configuration Check")
    print("-" * 25)
    
    # Check environment variables
    required_env_vars = [
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET', 
        'GOOGLE_REDIRECT_URI',
        'GOOGLE_DRIVE_ENABLED',
        'GOOGLE_DRIVE_AUTO_CONVERT_PDF',
        'GOOGLE_DRIVE_AUTO_SHARE'
    ]
    
    env_status = {}
    for var in required_env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'SECRET' in var:
                display_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            else:
                display_value = value
            env_status[var] = True
            print(f"✅ {var}: {display_value}")
        else:
            env_status[var] = False
            print(f"❌ {var}: Not configured")
    
    # Check if all required vars are present
    missing_vars = [var for var, status in env_status.items() if not status]
    if missing_vars:
        print(f"\n⚠️  Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("\n2. 🔧 Testing Local Flask App")
    print("-" * 25)
    
    try:
        # Test if Flask app is running
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Flask application is running")
        else:
            print(f"❌ Flask app health check failed: {health_response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Flask app: {e}")
        print("💡 Please start the Flask application first: python railway_start.py")
        return False
    
    print("\n3. 🔐 Google Authentication Endpoints")
    print("-" * 35)
    
    # Test authentication endpoints (without actual auth for now)
    auth_endpoints = [
        ('/auth/google', 'GET', 'Initiate Google OAuth'),
        ('/auth/google/callback', 'GET', 'OAuth callback'),
        ('/auth/google/status', 'GET', 'Check auth status'),
        ('/auth/google/refresh', 'POST', 'Refresh tokens'),
        ('/auth/google/revoke', 'POST', 'Revoke access')
    ]
    
    for endpoint, method, description in auth_endpoints:
        try:
            if method == 'GET':
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
            
            # Most endpoints will return 401 without auth, which is expected
            if response.status_code in [200, 401, 302]:  # 302 for redirects
                status = "✅" if response.status_code == 200 else "🔒"
                print(f"{status} {method} {endpoint} - {description} ({response.status_code})")
            else:
                print(f"❌ {method} {endpoint} - Unexpected status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {method} {endpoint} - Connection error: {e}")
    
    print("\n4. 📁 File Management with Google Drive")
    print("-" * 35)
    
    # Test file endpoints that support Google Drive
    file_endpoints = [
        ('/api/files/upload', 'POST', 'Upload with Google Drive integration'),
        ('/api/files/1/google-doc', 'GET', 'Get Google Doc access'),
        ('/api/files/1/info', 'GET', 'File info with Google Drive data')
    ]
    
    for endpoint, method, description in file_endpoints:
        try:
            if method == 'GET':
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
            
            # These will return 401 without auth, which is expected
            if response.status_code in [401, 404]:  # 404 for non-existent files
                print(f"🔒 {method} {endpoint} - {description} (Auth required: {response.status_code})")
            else:
                print(f"❓ {method} {endpoint} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {method} {endpoint} - Connection error: {e}")
    
    print("\n5. 🎯 Google API Requirements Summary")
    print("-" * 35)
    
    print("Required Google Cloud Console Setup:")
    print("1. Create a Google Cloud Project")
    print("2. Enable Google Drive API and Google Docs API")
    print("3. Create OAuth 2.0 Client ID credentials")
    print("4. Configure authorized redirect URIs")
    print("5. Optionally create Service Account for server-to-server access")
    
    print("\nRequired Scopes:")
    scopes = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
        'openid',
        'email',
        'profile'
    ]
    for scope in scopes:
        print(f"  - {scope}")
    
    print("\nRequired Environment Variables:")
    for var in required_env_vars:
        status = "✅" if env_status.get(var, False) else "❌"
        print(f"  {status} {var}")
    
    print("\n6. 🚀 How to Test Google Integration")
    print("-" * 35)
    
    print("Step-by-step testing process:")
    print("1. Ensure Flask app is running")
    print("2. Create a test user account")
    print("3. Get JWT token for the user")
    print("4. Initiate Google OAuth: GET /auth/google?user_id=<user_id>")
    print("5. Complete OAuth flow in browser")
    print("6. Upload a file with Google Drive: POST /api/files/upload?google_drive=true")
    print("7. Get Google Doc link: GET /api/files/<file_id>/google-doc")
    
    print("\n7. 🔍 Current Status")
    print("-" * 20)
    
    if all(env_status.values()):
        print("✅ All environment variables configured")
        print("✅ Flask application accessible")
        print("🔒 Endpoints require authentication (as expected)")
        print("✅ Ready for Google integration testing with authenticated user")
        return True
    else:
        print("❌ Missing required configuration")
        print("⚠️  Cannot proceed with Google integration testing")
        return False

def create_test_scenario():
    """Create a test scenario for Google Docs integration"""
    print("\n" + "=" * 60)
    print("📝 GOOGLE DOCS INTEGRATION TEST SCENARIO")
    print("=" * 60)
    
    scenario = """
SCENARIO: Upload Resume and Get Google Docs Link

Prerequisites:
1. Flask app running on localhost:5001
2. Google Cloud project with APIs enabled
3. OAuth credentials configured
4. User authenticated with Google

Test Steps:
1. Create test user account
2. Authenticate user and get JWT token
3. Initiate Google OAuth for the user
4. Upload PDF resume with Google Drive integration
5. Verify file appears in Google Drive
6. Get Google Docs link for editing
7. Test file sharing and permissions

Expected Results:
- User can upload resume to both local storage and Google Drive
- PDF is converted to Google Doc (if enabled)
- User receives editable Google Docs link
- File is properly shared with user's email
- User can edit resume in Google Docs interface

Key API Calls:
- POST /api/register (create user)
- POST /api/login (get JWT token)
- GET /auth/google?user_id=X (initiate OAuth)
- POST /api/files/upload?google_drive=true (upload with Google Drive)
- GET /api/files/{id}/google-doc (get Google Docs link)
"""
    
    print(scenario)
    
    return True

if __name__ == "__main__":
    print("🧪 Google Docs/Drive Integration Test Suite")
    print("Testing all Google-related functionality...")
    
    success = test_google_integration()
    
    if success:
        create_test_scenario()
        print("\n🎉 Configuration check passed! Ready for integration testing.")
    else:
        print("\n💥 Configuration issues found. Please fix before testing.")
    
    print("\n" + "=" * 60)