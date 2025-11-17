#!/usr/bin/env python3
"""
Deployment validation script for Resume Modifier
Validates that all services are working correctly after deployment
"""

import requests
import json
import sys
import os
from time import sleep

def validate_deployment(base_url):
    """Validate deployment by testing critical endpoints"""
    
    print(f"🔍 Validating deployment at: {base_url}")
    
    # Test 1: Health Check
    print("\n1️⃣  Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed: {health_data.get('status', 'unknown')}")
            
            # Check database connectivity
            components = health_data.get('components', {})
            if components.get('database') == 'connected':
                print("✅ Database connection verified")
            else:
                print("⚠️  Database connection issue detected")
                
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: API Documentation
    print("\n2️⃣  Testing API documentation...")
    try:
        response = requests.get(f"{base_url}/apidocs", timeout=15)
        if response.status_code == 200:
            print("✅ API documentation accessible")
        else:
            print(f"⚠️  API documentation returned: {response.status_code}")
    except Exception as e:
        print(f"⚠️  API documentation error: {e}")
    
    # Test 3: File Upload Endpoint Structure
    print("\n3️⃣  Testing file upload endpoint availability...")
    try:
        # Test with invalid request to see if endpoint exists
        response = requests.post(f"{base_url}/api/files/upload", timeout=15)
        if response.status_code in [400, 401]:  # Expected - no auth token or file
            print("✅ File upload endpoint is accessible")
        elif response.status_code == 404:
            print("❌ File upload endpoint not found")
            return False
        else:
            print(f"⚠️  File upload endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"⚠️  File upload test error: {e}")
    
    # Test 4: User Registration (Basic)
    print("\n4️⃣  Testing user registration endpoint...")
    try:
        # Test with invalid data to check endpoint availability
        response = requests.post(
            f"{base_url}/api/register", 
            json={"test": "data"},
            timeout=15
        )
        if response.status_code in [400, 422]:  # Expected - invalid data
            print("✅ User registration endpoint is accessible")
        elif response.status_code == 404:
            print("❌ User registration endpoint not found")
            return False
        else:
            print(f"⚠️  User registration returned: {response.status_code}")
    except Exception as e:
        print(f"⚠️  User registration test error: {e}")
    
    print("\n🎉 Deployment validation completed!")
    return True

def main():
    """Main validation function"""
    
    # Get base URL from command line or environment
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        base_url = os.environ.get('RAILWAY_URL', 'http://localhost:5001')
    
    print(f"🚀 Starting deployment validation for: {base_url}")
    
    # Wait a moment for the service to be fully ready
    print("⏳ Waiting for service to be ready...")
    sleep(5)
    
    # Run validation
    success = validate_deployment(base_url)
    
    if success:
        print("\n✅ Deployment validation passed!")
        return 0
    else:
        print("\n❌ Deployment validation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())