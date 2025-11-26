#!/usr/bin/env python3
"""
Test Google Drive file upload functionality directly
"""
import sys
sys.path.append('/app/core')
sys.path.append('/app')
import os
os.environ.setdefault('FLASK_APP', 'app')

from flask import Flask
from core.app import create_app

app = create_app()

def test_google_drive_upload():
    """Test the Google Drive upload functionality"""
    
    with app.app_context():
        from app.services.google_drive_admin_service import GoogleDriveAdminService
        
        print("🔍 Testing Google Drive File Upload...")
        
        # Initialize service
        service = GoogleDriveAdminService()
        
        # Check authentication status
        print("1. Checking admin authentication...")
        auth_status = service.check_admin_auth_status()
        print(f"   Auth Status: {auth_status}")
        
        if not auth_status.get('authenticated'):
            print("❌ Admin not authenticated")
            return False
        
        print("✅ Admin authenticated!")
        
        # Test file upload
        print("2. Testing file upload to Google Drive...")
        
        # Read test file
        test_file_path = "/app/testing/unit/test_data/sample_resume.pdf"
        if not os.path.exists(test_file_path):
            print(f"❌ Test file not found: {test_file_path}")
            return False
        
        with open(test_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"   Test file size: {len(file_content)} bytes")
        
        try:
            # Upload to Google Drive
            result = service.upload_file_to_admin_drive(
                file_content=file_content,
                filename="test_resume_upload.pdf",
                mime_type="application/pdf",
                user_id=3,  # Test user ID
                user_email="test@example.com",
                convert_to_doc=True,
                share_with_user=True
            )
            
            print(f"   Upload result: {result}")
            
            if result.get('success'):
                print("✅ Google Drive upload SUCCESS!")
                print(f"   File ID: {result.get('file_id')}")
                print(f"   Drive Link: {result.get('drive_link')}")
                print(f"   Sharing: {'✅' if result.get('sharing_successful') else '❌'}")
                if result.get('doc_id'):
                    print(f"   Google Doc ID: {result.get('doc_id')}")
                return True
            else:
                print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during upload: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_google_drive_upload()
    if success:
        print("\n🎉 Google Drive upload test PASSED!")
        print("File uploads should now work with Google Drive integration!")
    else:
        print("\n💥 Google Drive upload test FAILED!")
    
    exit(0 if success else 1)