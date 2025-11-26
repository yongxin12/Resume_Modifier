#!/usr/bin/env python3
"""
Test Google Drive integration after OAuth authentication fixes
"""
import os
import sys
sys.path.append('/home/rex/project/resume-editor/project/Resume_Modifier')
sys.path.append('/home/rex/project/resume-editor/project/Resume_Modifier/core')
sys.path.append('/home/rex/project/resume-editor/project/Resume_Modifier/app')

from app.services.google_drive_admin_service import GoogleDriveAdminService
from app.services.google_admin_auth_fixed import GoogleAdminAuthServiceFixed

def test_google_drive_integration():
    """Test Google Drive integration with admin authentication"""
    
    print("🔍 Testing Google Drive Integration...")
    
    # Initialize services
    auth_service = GoogleAdminAuthServiceFixed()
    drive_service = GoogleDriveAdminService()
    
    # Check admin authentication status
    print("1. Checking admin authentication status...")
    auth_status = drive_service.check_admin_auth_status()
    print(f"   Auth Status: {auth_status}")
    
    if not auth_status['authenticated']:
        print("❌ Admin not authenticated - this should be working after OAuth completion")
        return False
    
    print("✅ Admin authentication detected successfully!")
    
    # Test file upload capability
    print("2. Testing file upload capability...")
    
    # Use the existing sample PDF
    test_file_path = "/home/rex/project/resume-editor/project/Resume_Modifier/testing/unit/test_data/sample_resume.pdf"
    
    if not os.path.exists(test_file_path):
        print(f"❌ Test file not found: {test_file_path}")
        return False
    
    try:
        # Read the file
        with open(test_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"   Test file: {test_file_path}")
        print(f"   File size: {len(file_content)} bytes")
        
        # Try to upload to Google Drive
        print("3. Attempting Google Drive upload...")
        
        result = drive_service.upload_file(
            file_content=file_content,
            filename="test_resume_integration.pdf",
            original_filename="sample_resume.pdf"
        )
        
        print(f"   Upload result: {result}")
        
        if result.get('success'):
            print("✅ Google Drive upload successful!")
            if 'drive_url' in result:
                print(f"   Drive URL: {result['drive_url']}")
            if 'sharing_url' in result:
                print(f"   Sharing URL: {result['sharing_url']}")
            return True
        else:
            print(f"❌ Google Drive upload failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error during upload test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_google_drive_integration()
    if success:
        print("\n🎉 Google Drive integration test PASSED!")
    else:
        print("\n💥 Google Drive integration test FAILED!")
    
    sys.exit(0 if success else 1)