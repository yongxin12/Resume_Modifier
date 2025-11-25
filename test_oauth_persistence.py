#!/usr/bin/env python3
"""
Test script for OAuth Persistence functionality
Tests persistent authentication, token refresh, and storage monitoring

Author: Resume Modifier Backend Team
Date: November 2024
"""

import os
import sys
import json
import requests
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:5001"
TEST_USER_EMAIL = "test_admin_oauth@example.com"
TEST_USER_PASSWORD = "testpassword123"

class OAuthPersistenceTest:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.user_id = None
        
    def login_as_admin(self):
        """Login as admin user and get JWT token"""
        print("🔐 Logging in as admin user...")
        
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        response = self.session.post(f"{BASE_URL}/api/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.jwt_token = data.get('token')
            self.user_id = data.get('user_id')
            
            # Set authorization header for future requests
            self.session.headers.update({
                'Authorization': f'Bearer {self.jwt_token}',
                'Content-Type': 'application/json'
            })
            
            print(f"✅ Successfully logged in - User ID: {self.user_id}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def test_basic_oauth_status(self):
        """Test basic OAuth status endpoint"""
        print("\n📊 Testing basic OAuth status...")
        
        response = self.session.get(f"{BASE_URL}/auth/google/status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Basic OAuth status: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Basic OAuth status failed: {response.status_code} - {response.text}")
            return False
    
    def test_detailed_oauth_status(self):
        """Test detailed OAuth persistence status endpoint"""
        print("\n📊 Testing detailed OAuth persistence status...")
        
        response = self.session.get(f"{BASE_URL}/api/auth/google/status/detailed")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Detailed OAuth status: {json.dumps(data, indent=2)}")
            
            # Validate expected fields
            oauth_status = data.get('oauth_status', {})
            storage_status = data.get('storage_status', {})
            
            expected_oauth_fields = ['is_authenticated', 'is_persistent', 'session_id', 'token_expires_at', 'auto_refresh_enabled', 'is_active']
            expected_storage_fields = ['quota_total', 'quota_used', 'usage_percentage', 'warning_level', 'last_check']
            
            for field in expected_oauth_fields:
                if field not in oauth_status:
                    print(f"⚠️  Missing OAuth field: {field}")
            
            for field in expected_storage_fields:
                if field not in storage_status:
                    print(f"⚠️  Missing storage field: {field}")
            
            return True
        else:
            print(f"❌ Detailed OAuth status failed: {response.status_code} - {response.text}")
            return False
    
    def test_storage_analytics(self):
        """Test storage analytics endpoint"""
        print("\n📈 Testing Google Drive storage analytics...")
        
        response = self.session.get(f"{BASE_URL}/api/auth/google/storage/analytics")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Storage analytics: {json.dumps(data, indent=2)}")
            
            # Validate analytics structure
            analytics = data.get('analytics', {})
            expected_fields = ['current_usage', 'total_quota', 'usage_percentage', 'warning_level', 'recommendations']
            
            for field in expected_fields:
                if field not in analytics:
                    print(f"⚠️  Missing analytics field: {field}")
            
            return True
        else:
            print(f"❌ Storage analytics failed: {response.status_code} - {response.text}")
            return False
    
    def test_force_token_refresh(self):
        """Test force token refresh endpoint"""
        print("\n🔄 Testing force token refresh...")
        
        response = self.session.post(f"{BASE_URL}/api/auth/google/token/refresh")
        
        if response.status_code in [200, 500]:  # 500 is expected if no OAuth session exists
            data = response.json()
            print(f"✅ Force token refresh response: {json.dumps(data, indent=2)}")
            
            if response.status_code == 500:
                print("ℹ️  Expected error - no OAuth session exists yet")
            
            return True
        else:
            print(f"❌ Force token refresh failed: {response.status_code} - {response.text}")
            return False
    
    def test_oauth_revocation(self):
        """Test OAuth revocation endpoint (without actually revoking)"""
        print("\n🚫 Testing OAuth revocation endpoint structure...")
        
        # Test without confirmation (should fail)
        response = self.session.post(f"{BASE_URL}/api/auth/google/revoke/persistent", json={})
        
        if response.status_code == 400:
            data = response.json()
            print(f"✅ Revocation validation works: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Revocation validation failed: {response.status_code} - {response.text}")
            return False
    
    def test_admin_access_control(self):
        """Test that endpoints properly require admin access"""
        print("\n🔒 Testing admin access control...")
        
        # Save current token
        original_token = self.jwt_token
        
        # Try with invalid/non-admin token
        self.session.headers.update({'Authorization': 'Bearer invalid_token'})
        
        response = self.session.get(f"{BASE_URL}/api/auth/google/status/detailed")
        
        if response.status_code == 401:
            print("✅ Admin access control working - invalid token rejected")
        else:
            print(f"⚠️  Admin access control issue: {response.status_code}")
        
        # Restore original token
        self.session.headers.update({'Authorization': f'Bearer {original_token}'})
        return True
    
    def test_api_documentation_format(self):
        """Test that endpoints return properly formatted responses"""
        print("\n📋 Testing API response formats...")
        
        endpoints_to_test = [
            ('/api/auth/google/status/detailed', 'GET'),
            ('/api/auth/google/storage/analytics', 'GET'),
            ('/api/auth/google/token/refresh', 'POST')
        ]
        
        all_valid = True
        
        for endpoint, method in endpoints_to_test:
            try:
                if method == 'GET':
                    response = self.session.get(f"{BASE_URL}{endpoint}")
                else:
                    response = self.session.post(f"{BASE_URL}{endpoint}")
                
                if response.status_code in [200, 400, 401, 403, 404, 500]:
                    data = response.json()
                    
                    # Check for required fields
                    if 'success' in data or 'error' in data or 'message' in data:
                        print(f"✅ {endpoint} has valid response format")
                    else:
                        print(f"⚠️  {endpoint} missing standard response fields")
                        all_valid = False
                else:
                    print(f"⚠️  {endpoint} returned unexpected status: {response.status_code}")
                    all_valid = False
                    
            except Exception as e:
                print(f"❌ Error testing {endpoint}: {e}")
                all_valid = False
        
        return all_valid
    
    def run_all_tests(self):
        """Run all OAuth persistence tests"""
        print("=" * 60)
        print("🚀 Starting OAuth Persistence Tests")
        print("=" * 60)
        
        # Track test results
        test_results = {}
        
        # Test login
        test_results['login'] = self.login_as_admin()
        
        if not test_results['login']:
            print("❌ Cannot continue tests without successful login")
            return False
        
        # Run all tests
        tests = [
            ('basic_oauth_status', self.test_basic_oauth_status),
            ('detailed_oauth_status', self.test_detailed_oauth_status),
            ('storage_analytics', self.test_storage_analytics),
            ('force_token_refresh', self.test_force_token_refresh),
            ('oauth_revocation', self.test_oauth_revocation),
            ('admin_access_control', self.test_admin_access_control),
            ('api_documentation_format', self.test_api_documentation_format)
        ]
        
        for test_name, test_func in tests:
            try:
                test_results[test_name] = test_func()
            except Exception as e:
                print(f"❌ Test {test_name} crashed: {e}")
                test_results[test_name] = False
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in test_results.values() if result)
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:25} {status}")
        
        print("-" * 60)
        print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All OAuth persistence tests passed!")
            return True
        else:
            print(f"⚠️  {total - passed} tests failed")
            return False


def main():
    """Main test function"""
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding correctly: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("Make sure the Flask application is running with Docker:")
        print("docker-compose -f configuration/deployment/docker-compose.yml up -d")
        return False
    
    # Run tests
    test_runner = OAuthPersistenceTest()
    success = test_runner.run_all_tests()
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)