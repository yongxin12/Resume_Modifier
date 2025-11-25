#!/usr/bin/env python3
"""
Test Google Drive service account authentication
"""

import json
import os
import sys

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.join(current_dir, 'core')
sys.path.insert(0, core_dir)
sys.path.insert(0, current_dir)

def test_google_drive_config():
    """Test Google Drive service account configuration"""
    print("🔍 Testing Google Drive Configuration")
    print("=" * 50)
    
    # Check if the environment variables are set
    service_account_info = os.environ.get('GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO')
    if not service_account_info:
        print("❌ GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO not found in environment")
        return False
    
    print("✅ GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO found in environment")
    
    # Try to parse the JSON
    try:
        service_account_data = json.loads(service_account_info)
        print("✅ Service account JSON is valid")
        
        # Check required fields
        required_fields = [
            'type', 'project_id', 'private_key_id', 'private_key',
            'client_email', 'client_id', 'auth_uri', 'token_uri'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in service_account_data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        print("✅ All required fields present")
        print(f"📧 Service account email: {service_account_data['client_email']}")
        print(f"🏷️  Project ID: {service_account_data['project_id']}")
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO: {e}")
        return False
    
    # Test Google Drive API initialization
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        
        print("\n🔧 Testing Google Drive API initialization...")
        
        # Create credentials
        credentials = service_account.Credentials.from_service_account_info(
            service_account_data,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        
        # Build the service
        service = build('drive', 'v3', credentials=credentials)
        
        print("✅ Google Drive service initialized successfully")
        
        # Test a simple API call
        print("\n📋 Testing Drive API call...")
        try:
            # Get user info (about the service account)
            about = service.about().get(fields='user').execute()
            print(f"✅ API call successful - Service account: {about.get('user', {}).get('emailAddress', 'Unknown')}")
            return True
            
        except Exception as api_error:
            print(f"❌ Drive API call failed: {api_error}")
            return False
            
    except ImportError as e:
        print(f"❌ Missing Google API libraries: {e}")
        print("💡 Install with: pip install google-api-python-client google-auth")
        return False
    except Exception as e:
        print(f"❌ Google Drive service initialization failed: {e}")
        return False

def test_local_environment():
    """Test the local environment setup"""
    print("\n🏠 Testing Local Environment")
    print("=" * 30)
    
    # Check if .env file exists and load it
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        print("✅ .env file found")
        
        # Simple env file parser
        with open(env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() == 'GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO':
                        os.environ[key.strip()] = value.strip()
                        print(f"✅ Loaded {key.strip()} from .env")
                        break
    else:
        print("⚠️  .env file not found")
    
    return test_google_drive_config()

if __name__ == "__main__":
    success = test_local_environment()
    
    if success:
        print("\n🎉 Google Drive configuration test passed!")
    else:
        print("\n❌ Google Drive configuration test failed!")
        print("\n🔧 Troubleshooting steps:")
        print("1. Verify your service account JSON is complete and valid")
        print("2. Ensure the Google Drive API is enabled in your GCP project")
        print("3. Check that the service account has the necessary permissions")
        print("4. Install required dependencies: pip install google-api-python-client google-auth")
    
    sys.exit(0 if success else 1)