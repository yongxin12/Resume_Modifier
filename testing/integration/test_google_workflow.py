#!/usr/bin/env python3
"""
Practical Google Docs Integration Test Script

This script tests the Google Docs/Drive integration functionality step by step.
Run this after starting the Flask application.

Usage:
    python3 test_google_workflow.py
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:5001"

def print_step(step_num, description):
    """Print formatted step information"""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {description}")
    print('='*60)

def print_result(success, message, data=None):
    """Print formatted result"""
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"{status}: {message}")
    if data:
        print(f"Response: {json.dumps(data, indent=2)}")

def test_app_health():
    """Test if Flask app is running"""
    print_step(1, "Testing Flask Application Health")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_result(True, "Flask application is running")
            return True
        else:
            print_result(False, f"Health check failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_result(False, f"Cannot connect to Flask app: {e}")
        print("💡 Please start the Flask application first:")
        print("   cd /path/to/Resume_Modifier")
        print("   source venv/bin/activate") 
        print("   python3 railway_start.py")
        return False

def test_user_registration():
    """Test user registration"""
    print_step(2, "Testing User Registration")
    
    user_data = {
        "email": "test_google@example.com",
        "password": "testpass123",
        "full_name": "Google Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/register", json=user_data)
        
        if response.status_code == 201:
            print_result(True, "User registered successfully")
            return True, user_data
        elif response.status_code == 400:
            # User might already exist
            print_result(True, "User already exists (continuing with login)")
            return True, user_data
        else:
            print_result(False, f"Registration failed with status {response.status_code}")
            return False, user_data
    except requests.exceptions.RequestException as e:
        print_result(False, f"Registration request failed: {e}")
        return False, user_data

def test_user_login(user_data):
    """Test user login and get JWT token"""
    print_step(3, "Testing User Login")
    
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/login", json=login_data)
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            user_id = response.json().get('user_id')
            print_result(True, f"Login successful, User ID: {user_id}")
            return True, token, user_id
        else:
            print_result(False, f"Login failed with status {response.status_code}", response.json())
            return False, None, None
    except requests.exceptions.RequestException as e:
        print_result(False, f"Login request failed: {e}")
        return False, None, None

def test_google_auth_status(token):
    """Check Google authentication status"""
    print_step(4, "Checking Google Authentication Status")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/auth/google/status", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            is_authenticated = data.get('google_authenticated', False)
            if is_authenticated:
                print_result(True, "User is already authenticated with Google")
            else:
                print_result(True, "User is not yet authenticated with Google")
            return True, is_authenticated
        else:
            print_result(False, f"Status check failed with status {response.status_code}")
            return False, False
    except requests.exceptions.RequestException as e:
        print_result(False, f"Status check request failed: {e}")
        return False, False

def get_google_oauth_url(user_id):
    """Get Google OAuth URL for manual authentication"""
    print_step(5, "Google OAuth Authentication")
    
    oauth_url = f"{BASE_URL}/auth/google?user_id={user_id}"
    
    print("🔗 Google OAuth URL:")
    print(f"   {oauth_url}")
    print()
    print("📋 Manual Steps:")
    print("1. Copy the URL above and open it in your browser")
    print("2. Sign in with your Google account")
    print("3. Grant permissions for Google Drive and Docs access")
    print("4. You'll be redirected back to the application")
    print("5. Once completed, press Enter to continue testing...")
    
    input("\nPress Enter after completing Google OAuth...")
    
    return oauth_url

def test_file_upload(token):
    """Test file upload with Google Drive integration"""
    print_step(6, "Testing File Upload with Google Drive")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a sample PDF content for testing
    sample_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF"
    
    files = {
        'file': ('test_resume.pdf', sample_pdf_content, 'application/pdf')
    }
    
    try:
        # Upload with Google Drive integration enabled
        response = requests.post(
            f"{BASE_URL}/api/files/upload?google_drive=true",
            headers=headers,
            files=files
        )
        
        if response.status_code == 201:
            data = response.json()
            file_id = data.get('file_id')
            print_result(True, f"File uploaded successfully, File ID: {file_id}")
            return True, file_id
        else:
            print_result(False, f"File upload failed with status {response.status_code}", response.json())
            return False, None
    except requests.exceptions.RequestException as e:
        print_result(False, f"File upload request failed: {e}")
        return False, None

def test_google_doc_access(token, file_id):
    """Test getting Google Docs access link"""
    print_step(7, "Testing Google Docs Access Link")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/files/{file_id}/google-doc", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            google_doc_link = data.get('google_doc_link')
            google_drive_link = data.get('google_drive_link')
            
            print_result(True, "Google Docs access granted")
            print(f"📝 Google Docs Link: {google_doc_link}")
            print(f"📁 Google Drive Link: {google_drive_link}")
            
            return True, google_doc_link, google_drive_link
        else:
            print_result(False, f"Google Docs access failed with status {response.status_code}", response.json())
            return False, None, None
    except requests.exceptions.RequestException as e:
        print_result(False, f"Google Docs access request failed: {e}")
        return False, None, None

def test_file_info(token, file_id):
    """Test file info endpoint with Google data"""
    print_step(8, "Testing File Info with Google Data")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/files/{file_id}/info", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "File info retrieved successfully")
            
            # Display relevant Google integration data
            google_data = {
                'google_drive_file_id': data.get('google_drive_file_id'),
                'google_doc_id': data.get('google_doc_id'),
                'google_drive_link': data.get('google_drive_link'),
                'google_doc_link': data.get('google_doc_link'),
                'has_thumbnail': data.get('thumbnail_path') is not None
            }
            
            print("🔗 Google Integration Data:")
            for key, value in google_data.items():
                print(f"   {key}: {value}")
            
            return True, data
        else:
            print_result(False, f"File info failed with status {response.status_code}")
            return False, None
    except requests.exceptions.RequestException as e:
        print_result(False, f"File info request failed: {e}")
        return False, None

def print_summary(results):
    """Print test summary"""
    print(f"\n{'='*60}")
    print("🎯 GOOGLE INTEGRATION TEST SUMMARY")
    print('='*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results if result['success'])
    
    print(f"📊 Results: {passed_tests}/{total_tests} tests passed")
    print()
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test']}")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Google integration is working correctly.")
        print("\n📋 Next Steps:")
        print("1. Users can now upload resumes and get Google Docs links")
        print("2. Files are automatically synced to Google Drive")
        print("3. Users can edit resumes directly in Google Docs")
        print("4. Changes are automatically saved to Google Drive")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please review the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure Google OAuth credentials are correctly configured")
        print("2. Verify Google Drive and Docs APIs are enabled")
        print("3. Check that redirect URI matches Google Console settings")
        print("4. Ensure Flask application has proper permissions")

def main():
    """Run the complete Google integration test suite"""
    print("🧪 Google Docs/Drive Integration Test Suite")
    print("Testing all Google-related functionality...")
    
    results = []
    
    # Test 1: App Health
    success = test_app_health()
    results.append({"test": "Flask Application Health", "success": success})
    if not success:
        print_summary(results)
        return
    
    # Test 2: User Registration
    success, user_data = test_user_registration()
    results.append({"test": "User Registration", "success": success})
    if not success:
        print_summary(results)
        return
    
    # Test 3: User Login
    success, token, user_id = test_user_login(user_data)
    results.append({"test": "User Login", "success": success})
    if not success:
        print_summary(results)
        return
    
    # Test 4: Google Auth Status
    success, is_authenticated = test_google_auth_status(token)
    results.append({"test": "Google Auth Status Check", "success": success})
    
    # Test 5: Google OAuth (if not already authenticated)
    if not is_authenticated:
        oauth_url = get_google_oauth_url(user_id)
        # Re-check authentication status after OAuth
        success, is_authenticated = test_google_auth_status(token)
        results.append({"test": "Google OAuth Flow", "success": is_authenticated})
    
    if not is_authenticated:
        print("⚠️  Google authentication is required for the remaining tests.")
        print_summary(results)
        return
    
    # Test 6: File Upload
    success, file_id = test_file_upload(token)
    results.append({"test": "File Upload with Google Drive", "success": success})
    if not success:
        print_summary(results)
        return
    
    # Test 7: Google Docs Access
    success, google_doc_link, google_drive_link = test_google_doc_access(token, file_id)
    results.append({"test": "Google Docs Access Link", "success": success})
    
    # Test 8: File Info
    success, file_data = test_file_info(token, file_id)
    results.append({"test": "File Info with Google Data", "success": success})
    
    # Print final summary
    print_summary(results)

if __name__ == "__main__":
    main()