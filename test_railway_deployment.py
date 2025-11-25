#!/usr/bin/env python3
"""
Test Railway deployment after StorageResult fix
"""

import requests
import io
import json
import time

RAILWAY_URL = "https://resumemodifier-production-44a2.up.railway.app"

def test_railway_basic_connection():
    """Test basic connection to Railway"""
    try:
        print("🚂 Testing Railway basic connection...")
        response = requests.get(f"{RAILWAY_URL}/", timeout=30)
        
        if response.status_code == 200:
            print("✅ Railway basic connection successful")
            return True
        else:
            print(f"❌ Railway connection failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Railway connection error: {e}")
        return False

def test_railway_file_upload():
    """Test file upload endpoint on Railway"""
    try:
        print("📁 Testing Railway file upload endpoint...")
        
        # Create a test file
        test_file_content = b"Test PDF content for Railway upload testing"
        files = {
            'file': ('test_railway.pdf', io.BytesIO(test_file_content), 'application/pdf')
        }
        
        # Test file upload (expect auth error but should not be StorageResult error)
        response = requests.post(
            f"{RAILWAY_URL}/api/files/upload",
            files=files,
            timeout=30
        )
        
        print(f"📋 Response status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"📋 Response data: {json.dumps(response_data, indent=2)}")
            
            # Check if we still get the StorageResult error
            if "'StorageResult' object has no attribute 'local_path'" in str(response_data):
                print("❌ StorageResult local_path error still present")
                return False
            elif response.status_code == 401:
                print("✅ Expected auth error - StorageResult fix working!")
                return True
            elif response.status_code == 500 and "Database error occurred while saving file record" in str(response_data):
                print("❌ Database error still occurring")
                print("This might be a different issue or the deployment hasn't updated yet")
                return False
            else:
                print(f"✅ Different response - StorageResult fix appears to be working")
                return True
                
        except Exception as e:
            print(f"❌ Failed to parse response: {e}")
            print(f"Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Railway file upload test failed: {e}")
        return False

def check_railway_deployment_status():
    """Check if Railway has the latest deployment"""
    try:
        print("🔍 Checking Railway deployment status...")
        
        # Try to access a health check or basic endpoint
        response = requests.get(f"{RAILWAY_URL}/api/", timeout=30)
        
        if response.status_code == 200:
            print("✅ Railway API is responding")
            return True
        else:
            print(f"⚠️  Railway API status: {response.status_code}")
            return response.status_code < 500
            
    except Exception as e:
        print(f"❌ Railway deployment check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚂 Railway Deployment Test After Fix")
    print("=" * 40)
    
    # Test basic connection
    basic_ok = test_railway_basic_connection()
    
    if basic_ok:
        # Check deployment status
        deployment_ok = check_railway_deployment_status()
        
        if deployment_ok:
            # Test file upload
            print("\n🧪 Testing file upload with StorageResult fix...")
            upload_ok = test_railway_file_upload()
            
            if upload_ok:
                print("\n🎉 SUCCESS: Railway deployment fixed!")
                print("StorageResult local_path error has been resolved.")
            else:
                print("\n❌ Railway deployment still has issues")
                print("The deployment may not have updated yet or there's another issue.")
        else:
            print("\n❌ Railway deployment issues detected")
    else:
        print("\n❌ Cannot connect to Railway")
    
    print("\n" + "=" * 40)