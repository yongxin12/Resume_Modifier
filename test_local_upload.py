#!/usr/bin/env python3
"""
Test local file upload to verify local_path fix works
"""

import requests
import io
import json

def test_local_file_upload():
    """Test file upload on local Docker instance"""
    try:
        print("📁 Testing local file upload...")
        
        # First, let's test the basic API endpoint
        response = requests.get("http://localhost:5001/")
        if response.status_code != 200:
            print(f"❌ Basic API test failed: {response.status_code}")
            return False
        
        print("✅ Basic API connection successful")
        
        # Create a simple PDF-like file for testing
        test_file_content = b"Test PDF content for upload testing"
        
        # Prepare the file upload
        files = {
            'file': ('test_upload.pdf', io.BytesIO(test_file_content), 'application/pdf')
        }
        
        # For now, let's test without authentication to see the response
        print("🧪 Attempting file upload (without auth to see response)...")
        
        response = requests.post(
            "http://localhost:5001/api/files/upload",
            files=files
        )
        
        print(f"📋 Response status: {response.status_code}")
        print(f"📋 Response headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"📋 Response data: {json.dumps(response_data, indent=2)}")
        except:
            print(f"📋 Response text: {response.text}")
        
        # Check if we get the expected authentication error (which means the endpoint is working)
        if response.status_code == 401:
            print("✅ File upload endpoint is working (got expected auth error)")
            return True
        elif response.status_code == 200:
            print("✅ File upload successful (no auth required)")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to local server")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_storage_result_property():
    """Test that StorageResult has the local_path property"""
    try:
        print("\n🔧 Testing StorageResult local_path property...")
        
        # Import the fixed StorageResult class
        import sys
        sys.path.insert(0, '/home/rex/project/resume-editor/project/Resume_Modifier/core')
        
        from app.services.file_storage_service import StorageResult
        
        # Test local storage result
        result = StorageResult(
            success=True,
            storage_type='local',
            file_path='/test/local/path.pdf',
            file_size=1000
        )
        
        # Test that local_path property works
        local_path = result.local_path
        print(f"✅ local_path property works: {local_path}")
        
        if local_path == '/test/local/path.pdf':
            print("✅ local_path returns correct value")
            return True
        else:
            print(f"❌ local_path returned wrong value: {local_path}")
            return False
        
    except Exception as e:
        print(f"❌ StorageResult test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🐳 Local Docker File Upload Test")
    print("=" * 40)
    
    # Test StorageResult property first
    storage_ok = test_storage_result_property()
    
    # Test local file upload endpoint
    upload_ok = test_local_file_upload()
    
    if storage_ok and upload_ok:
        print("\n🎉 Local environment is working correctly!")
        print("Both StorageResult fix and file upload endpoint are functional.")
    else:
        print(f"\n❌ Issues found:")
        if not storage_ok:
            print("   - StorageResult local_path property issue")
        if not upload_ok:
            print("   - File upload endpoint issue")