#!/usr/bin/env python3
"""
Test Google Drive integration with Railway endpoint
"""

import requests
import json

def test_google_drive_upload():
    """Test file upload with Google Drive integration"""
    
    # Railway endpoint
    base_url = "https://resumemodifier-production-44a2.up.railway.app"
    
    # Test credentials
    user_data = {
        "email": "user@example.com",
        "password": "SecurePassword123!"
    }
    
    print("🔐 Testing Google Drive upload with Railway deployment")
    print("=" * 55)
    
    # Step 1: Register user first
    print("\n1️⃣  Registering test user...")
    try:
        register_response = requests.post(
            f"{base_url}/api/register",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
                "first_name": "Test",
                "last_name": "User"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if register_response.status_code in [200, 201]:
            print("✅ User registered successfully")
        elif register_response.status_code == 400 and "already exists" in register_response.text:
            print("✅ User already exists")
        else:
            print(f"⚠️  Registration response: {register_response.status_code} - {register_response.text}")
    except Exception as e:
        print(f"⚠️  Registration error: {e}")
    
    # Step 2: Login to get JWT token
    print("\n2️⃣  Logging in to get JWT token...")
    try:
        login_response = requests.post(
            f"{base_url}/api/login",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            token = login_data.get('token') or login_data.get('access_token')
            if token:
                print("✅ Login successful - JWT token obtained")
            else:
                print("❌ Login successful but no token in response")
                print(f"Response: {login_data}")
                return False
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 3: Test file upload with Google Drive
    print("\n3️⃣  Testing file upload with Google Drive integration...")
    
    # Use the existing test PDF file
    pdf_path = "test_resume.pdf"
    
    try:
        with open(pdf_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()
        
        # Upload with Google Drive parameters
        upload_response = requests.post(
            f"{base_url}/api/files/upload",
            params={
                "process": "true",
                "google_drive": "true", 
                "convert_to_doc": "true",
                "share_with_user": "true"
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
            files={
                "file": ("test_resume.pdf", pdf_content, "application/pdf")
            }
        )
        
        print(f"📤 Upload response status: {upload_response.status_code}")
        
        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            print("✅ Upload successful!")
            
            # Check for Google Drive information
            if 'google_drive' in upload_data.get('file', {}):
                google_info = upload_data['file']['google_drive']
                print("🎉 Google Drive integration working!")
                print(f"   📁 Drive File ID: {google_info.get('file_id', 'N/A')}")
                print(f"   📄 Doc ID: {google_info.get('doc_id', 'N/A')}")
                print(f"   🔗 Drive Link: {google_info.get('drive_link', 'N/A')}")
                print(f"   📝 Doc Link: {google_info.get('doc_link', 'N/A')}")
                print(f"   🤝 Shared: {google_info.get('is_shared', 'N/A')}")
                return True
            else:
                print("⚠️  Upload successful but no Google Drive info")
                if 'warnings' in upload_data:
                    print(f"   Warnings: {upload_data['warnings']}")
                print(f"   Response: {json.dumps(upload_data, indent=2)}")
                return False
        else:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"Response: {upload_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

if __name__ == "__main__":
    success = test_google_drive_upload()
    
    if success:
        print("\n🎉 Google Drive integration test passed!")
        print("Your Railway deployment now supports Google Drive uploads!")
    else:
        print("\n❌ Google Drive integration test failed!")
        print("Check the Railway logs for more details:")
        print("railway logs --tail 50")
    
    exit(0 if success else 1)