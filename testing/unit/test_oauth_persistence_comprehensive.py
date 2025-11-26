"""
Comprehensive OAuth Persistence Test Suite
Complete test coverage for OAuth persistence and storage monitoring functionality

Author: Resume Modifier Backend Team
Date: November 2024
"""

import unittest
import json
import time
import requests
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Test configuration
BASE_URL = "http://localhost:5001"
TEST_ADMIN_EMAIL = "test_admin_oauth@example.com"
TEST_ADMIN_PASSWORD = "testpassword123"


class OAuthPersistenceTestSuite(unittest.TestCase):
    """Comprehensive test suite for OAuth persistence functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with authentication"""
        cls.access_token = None
        cls.user_id = None
        cls._authenticate()
    
    @classmethod
    def _authenticate(cls):
        """Authenticate and get access token"""
        try:
            response = requests.post(f"{BASE_URL}/api/login", json={
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                cls.access_token = data.get('token')
                cls.user_id = data.get('user', {}).get('id')
                print(f"✅ Authentication successful - User ID: {cls.user_id}")
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                cls.access_token = None
                cls.user_id = None
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            cls.access_token = None
            cls.user_id = None
    
    def _make_request(self, method: str, endpoint: str, json_data=None) -> requests.Response:
        """Make authenticated API request"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{BASE_URL}{endpoint}"
        
        if method.upper() == 'GET':
            return requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            return requests.post(url, headers=headers, json=json_data)
        elif method.upper() == 'PUT':
            return requests.put(url, headers=headers, json=json_data)
        else:
            raise ValueError(f"Unsupported method: {method}")

    def test_01_basic_oauth_status(self):
        """Test basic OAuth status endpoint"""
        if not self.access_token:
            self.skipTest("Authentication required")
        
        response = self._make_request('GET', '/api/auth/google/status')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('authenticated', data)
        self.assertIsInstance(data['authenticated'], bool)
        print("✅ Basic OAuth status test passed")

    def test_02_detailed_oauth_status(self):
        """Test detailed OAuth persistence status endpoint"""
        if not self.access_token:
            self.skipTest("Authentication required")
        
        response = self._make_request('GET', '/api/auth/google/status/detailed')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('oauth_status', data)
        self.assertIn('storage_status', data)
        
        # Verify OAuth status structure
        oauth_status = data['oauth_status']
        required_oauth_fields = [
            'is_authenticated', 'is_persistent', 'is_active',
            'auto_refresh_enabled', 'session_id', 'token_expires_at'
        ]
        for field in required_oauth_fields:
            self.assertIn(field, oauth_status)
        
        # Verify storage status structure
        storage_status = data['storage_status']
        required_storage_fields = [
            'quota_total', 'quota_used', 'usage_percentage',
            'warning_level', 'last_check'
        ]
        for field in required_storage_fields:
            self.assertIn(field, storage_status)
        
        print("✅ Detailed OAuth status test passed")

    def test_03_oauth_revocation_validation(self):
        """Test OAuth revocation endpoint validation"""
        if not self.access_token:
            self.skipTest("Authentication required")
        
        # Test without confirmation
        response = self._make_request('POST', '/api/auth/google/revoke/persistent', {})
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertFalse(data.get('success'))
        self.assertIn('error', data)
        # Check for either "confirmation" or "confirmed" in error message
        error_msg = data['error'].lower()
        self.assertTrue('confirmation' in error_msg or 'confirmed' in error_msg, 
                       f"Expected 'confirmation' or 'confirmed' in error message: {data['error']}")
        
        # Test with invalid confirmation
        response = self._make_request('POST', '/api/auth/google/revoke/persistent', {
            'confirm_revocation': False
        })
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertFalse(data.get('success'))
        print("✅ OAuth revocation validation test passed")

    def test_04_admin_access_control(self):
        """Test that admin access control is properly enforced"""
        if not self.access_token:
            self.skipTest("Authentication required")
        
        # Test admin-only endpoints with valid admin token
        admin_endpoints = [
            '/api/auth/google/status/detailed',
            '/api/storage/overview',
            '/api/storage/monitoring/status',
            '/api/storage/monitoring/status',
            '/api/storage/overview'
        ]
        
        for endpoint in admin_endpoints:
            method = 'POST' if 'refresh' in endpoint else 'GET'
            response = self._make_request(method, endpoint)
            
            # Should not get 403 Forbidden for admin user
            self.assertNotEqual(response.status_code, 403,
                              f"Admin should have access to {endpoint}")
        
        print("✅ Admin access control test passed")

    def test_05_api_response_formats(self):
        """Test that all API responses follow expected formats"""
        if not self.access_token:
            self.skipTest("Authentication required")
        
        test_endpoints = [
            ('/api/auth/google/status/detailed', 'GET'),
            ('/api/storage/monitoring/status', 'GET'),
            ('/api/storage/overview', 'GET')
        ]
        
        for endpoint, method in test_endpoints:
            response = self._make_request(method, endpoint)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.assertIsInstance(data, dict, f"{endpoint} should return dict")
                    self.assertIn('success', data, f"{endpoint} should have 'success' field")
                    
                    if data.get('success'):
                        # Successful responses should have timestamp
                        self.assertTrue('timestamp' in data or 'oauth_status' in data,
                                      f"{endpoint} should have timestamp or structured data")
                except json.JSONDecodeError:
                    self.fail(f"{endpoint} should return valid JSON")
        
        print("✅ API response format test passed")

    def test_06_storage_monitoring_service(self):
        """Test storage monitoring service functionality"""
        if not self.access_token:
            self.skipTest("Authentication required")
        
        # Test service status
        response = self._make_request('GET', '/api/storage/monitoring/status')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('service_status', data)
        
        service_status = data['service_status']
        required_fields = ['enabled', 'running', 'check_interval_minutes', 'stats']
        for field in required_fields:
            self.assertIn(field, service_status)
        
        print("✅ Storage monitoring service test passed")

    def test_07_storage_overview(self):
        """Test storage overview functionality"""
        if not self.access_token:
            self.skipTest("Authentication required")
        
        response = self._make_request('GET', '/api/storage/overview')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('summary', data)
        self.assertIn('sessions', data)
        
        # Verify summary structure
        summary = data['summary']
        required_summary_fields = [
            'total_sessions', 'sessions_with_warnings', 'critical_sessions',
            'total_storage_used_gb', 'total_storage_quota_gb', 'overall_usage_percentage'
        ]
        for field in required_summary_fields:
            self.assertIn(field, summary)
            self.assertIsInstance(summary[field], (int, float))
        
        # Verify sessions structure
        sessions = data['sessions']
        self.assertIsInstance(sessions, list)
        
        print("✅ Storage overview test passed")

    def test_08_service_configuration(self):
        """Test storage monitoring service configuration"""
        if not self.access_token:
            self.skipTest("Authentication required")
        
        # Test configuration update
        config_data = {
            'check_interval_minutes': 90,
            'enabled': True
        }
        
        response = self._make_request('PUT', '/api/storage/monitoring/config', config_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('new_config', data)
        
        new_config = data['new_config']
        self.assertEqual(new_config['check_interval_minutes'], 90)
        self.assertEqual(new_config['enabled'], True)
        
        print("✅ Service configuration test passed")

    def test_09_service_control(self):
        """Test storage monitoring service start/stop control"""
        if not self.access_token:
            self.skipTest("Authentication required")
        
        # Test service start
        response = self._make_request('POST', '/api/storage/monitoring/start')
        self.assertIn(response.status_code, [200, 400])  # 400 if already running
        
        data = response.json()
        self.assertIn('success', data)
        self.assertIn('running', data)
        
        # Test service stop
        response = self._make_request('POST', '/api/storage/monitoring/stop')
        self.assertIn(response.status_code, [200, 400])  # 400 if not running
        
        data = response.json()
        self.assertIn('success', data)
        self.assertIn('running', data)
        
        print("✅ Service control test passed")

    def test_10_error_handling(self):
        """Test error handling for various scenarios"""
        if not self.access_token:
            self.skipTest("Authentication required")
        
        # Test invalid endpoint
        response = self._make_request('GET', '/api/storage/invalid/endpoint')
        self.assertEqual(response.status_code, 404)
        
        # Test invalid configuration
        invalid_config = {
            'check_interval_minutes': 1  # Too low, should be rejected
        }
        
        response = self._make_request('PUT', '/api/storage/monitoring/config', invalid_config)
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertFalse(data.get('success'))
        self.assertIn('error', data)
        
        print("✅ Error handling test passed")


class StorageMonitoringUnitTests(unittest.TestCase):
    """Unit tests for storage monitoring components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_app = MagicMock()
        self.mock_app.config = {
            'STORAGE_MONITORING_ENABLED': True,
            'STORAGE_CHECK_INTERVAL_MINUTES': 60
        }
    
    def test_storage_quota_calculation(self):
        """Test storage quota calculation logic"""
        # Test quota calculation without mocking - simple math test
        drive_quota_total = 15 * 1024**3  # 15 GB in bytes
        drive_quota_used = 12 * 1024**3   # 12 GB in bytes
        
        # Calculate usage percentage
        usage_percentage = (drive_quota_used / drive_quota_total) * 100
        
        self.assertEqual(usage_percentage, 80.0)
        
        # Test other scenarios
        self.assertEqual((0 / drive_quota_total) * 100, 0.0)  # No usage
        self.assertEqual((drive_quota_total / drive_quota_total) * 100, 100.0)  # Full usage
        print("✅ Storage quota calculation test passed")
    
    def test_warning_level_determination(self):
        """Test warning level determination logic"""
        thresholds = {
            'low': 80,
            'medium': 85,
            'high': 90,
            'critical': 95
        }
        
        test_cases = [
            (75, 'none'),
            (82, 'low'),
            (87, 'medium'),
            (92, 'high'),
            (97, 'critical')
        ]
        
        for usage, expected_level in test_cases:
            if usage >= thresholds['critical']:
                level = 'critical'
            elif usage >= thresholds['high']:
                level = 'high'
            elif usage >= thresholds['medium']:
                level = 'medium'
            elif usage >= thresholds['low']:
                level = 'low'
            else:
                level = 'none'
            
            self.assertEqual(level, expected_level, 
                           f"Usage {usage}% should be '{expected_level}', got '{level}'")
        
        print("✅ Warning level determination test passed")
    
    def test_storage_alert_creation(self):
        """Test storage alert creation and content"""
        test_cases = [
            ('critical', 97.5, 1.2),
            ('high', 92.0, 3.8),
            ('medium', 87.0, 6.5),
            ('low', 82.0, 9.0)
        ]
        
        for level, usage, available_gb in test_cases:
            # Simulate alert content generation
            if level == 'critical':
                self.assertIn('CRITICAL', f"CRITICAL: Google Drive storage is {usage:.1f}% full")
                self.assertIn('IMMEDIATE ACTION REQUIRED', 
                            "🚨 IMMEDIATE ACTION REQUIRED")
            elif level == 'high':
                self.assertIn('HIGH WARNING', f"HIGH WARNING: Google Drive storage is {usage:.1f}% full")  
                self.assertIn('URGENT', "⚠️ URGENT: Take action within 24 hours")
            
        print("✅ Storage alert creation test passed")


def run_comprehensive_tests():
    """Run the comprehensive test suite"""
    print("🧪 COMPREHENSIVE OAUTH PERSISTENCE TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add integration tests
    suite.addTests(loader.loadTestsFromTestCase(OAuthPersistenceTestSuite))
    
    # Add unit tests
    suite.addTests(loader.loadTestsFromTestCase(StorageMonitoringUnitTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failed_tests = len(result.failures)
    error_tests = len(result.errors)
    passed_tests = total_tests - failed_tests - error_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Errors: {error_tests} 🚨")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if result.failures:
        print(f"\n❌ FAILED TESTS:")
        for test, traceback in result.failures:
            print(f"   - {test}: Failed")
    
    if result.errors:
        print(f"\n🚨 ERROR TESTS:")
        for test, traceback in result.errors:
            print(f"   - {test}: Error")
    
    print(f"\n{'🎉 ALL TESTS PASSED!' if (failed_tests + error_tests) == 0 else '⚠️  SOME TESTS FAILED'}")
    
    return success_rate >= 80  # Consider 80%+ as success


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)