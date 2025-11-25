#!/usr/bin/env python3
"""
Test script to verify the file upload fix for PostgreSQL transaction error
"""

import requests
import json
import os
from io import BytesIO

def test_file_upload():
    """Test the file upload endpoint to verify the transaction fix"""
    
    # API configuration
    base_url = "http://localhost:5001"
    login_url = f"{base_url}/api/login"
    upload_url = f"{base_url}/api/files/upload"
    
    # Test credentials (you may need to adjust these)
    test_credentials = {
        "username": "test_user",
        "password": "test_password"
    }
    
    try:
        print("🔍 Testing PostgreSQL transaction fix for file upload...")
        
        # Step 1: Login to get token
        print("📝 Step 1: Attempting login...")
        login_response = requests.post(login_url, json=test_credentials)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
            return False
        
        login_data = login_response.json()
        token = login_data.get('token')
        
        if not token:
            print("❌ No token received from login")
            return False
        
        print("✅ Login successful, token received")
        
        # Step 2: Create a test file
        print("📄 Step 2: Creating test file...")
        test_content = b"This is a test resume content for transaction testing"
        test_filename = "test_resume.txt"
        
        # Step 3: Upload file
        print("⬆️  Step 3: Uploading test file...")
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        files = {
            'file': (test_filename, BytesIO(test_content), 'text/plain')
        }
        
        # Disable processing to avoid complex dependencies
        params = {
            'process': 'false',
            'google_drive': 'false'
        }
        
        upload_response = requests.post(
            upload_url, 
            headers=headers, 
            files=files,
            params=params
        )
        
        print(f"📊 Upload response status: {upload_response.status_code}")
        print(f"📊 Upload response: {upload_response.text[:500]}...")  # First 500 chars
        
        if upload_response.status_code == 201:
            print("✅ File upload successful! PostgreSQL transaction error appears to be fixed.")
            return True
        elif upload_response.status_code == 500:
            response_text = upload_response.text
            if "psycopg2.errors.InFailedSqlTransaction" in response_text:
                print("❌ PostgreSQL transaction error still present")
                print(f"Error details: {response_text}")
                return False
            else:
                print(f"❌ Different server error occurred: {response_text}")
                return False
        else:
            print(f"⚠️  Unexpected response: {upload_response.status_code} - {upload_response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server - is it running?")
        return False
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_file_upload()
    if success:
        print("\n🎉 Test passed: PostgreSQL transaction issue appears to be resolved!")
    else:
        print("\n💥 Test failed: More investigation needed")