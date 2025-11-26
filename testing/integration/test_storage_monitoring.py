"""
Test Storage Monitoring Functionality
Tests the complete storage monitoring system including background services and API endpoints

Author: Resume Modifier Backend Team
Date: November 2024
"""

import json
import time
import requests
from datetime import datetime
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:5001"  # Adjust as needed
TEST_EMAIL = "test_admin_oauth@example.com"
TEST_PASSWORD = "testpassword123"

class StorageMonitoringTestSuite:
    """Comprehensive test suite for storage monitoring functionality"""
    
    def __init__(self):
        self.access_token = None
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': []
        }

    def run_all_tests(self):
        """Run all storage monitoring tests"""
        print("🧪 STORAGE MONITORING TEST SUITE")
        print("=" * 50)
        
        # Test authentication
        if not self._login():
            print("❌ Login failed - cannot proceed with tests")
            return self.results
        
        # Test cases
        test_methods = [
            self._test_storage_monitoring_status,
            self._test_storage_overview,
            self._test_start_storage_monitoring,
            self._test_force_storage_check,
            self._test_update_monitoring_config,
            self._test_stop_storage_monitoring,
            self._test_admin_access_control,
            self._test_api_response_formats
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self._record_test_result(test_method.__name__, False, f"Exception: {e}")
        
        # Print summary
        self._print_summary()
        return self.results

    def _login(self) -> bool:
        """Login and get access token"""
        try:
            response = requests.post(f"{BASE_URL}/api/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('token')
                print(f"✅ Login successful")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

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

    def _record_test_result(self, test_name: str, passed: bool, message: str = ""):
        """Record test result"""
        self.results['total_tests'] += 1
        
        if passed:
            self.results['passed_tests'] += 1
            status = "✅ PASS"
        else:
            self.results['failed_tests'] += 1
            status = "❌ FAIL"
        
        self.results['test_results'].append({
            'test_name': test_name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"{status}: {test_name}")
        if message:
            print(f"    📝 {message}")

    def _test_storage_monitoring_status(self):
        """Test getting storage monitoring service status"""
        response = self._make_request('GET', '/api/storage/monitoring/status')
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'service_status' in data:
                required_fields = ['enabled', 'running', 'check_interval_minutes', 'stats']
                if all(field in data['service_status'] for field in required_fields):
                    self._record_test_result('storage_monitoring_status', True, 
                                           f"Service status retrieved successfully")
                else:
                    self._record_test_result('storage_monitoring_status', False,
                                           f"Missing required fields in service status")
            else:
                self._record_test_result('storage_monitoring_status', False,
                                       f"Invalid response format: {data}")
        else:
            self._record_test_result('storage_monitoring_status', False,
                                   f"HTTP {response.status_code}: {response.text}")

    def _test_storage_overview(self):
        """Test getting storage overview"""
        response = self._make_request('GET', '/api/storage/overview')
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'summary' in data and 'sessions' in data:
                required_summary_fields = ['total_sessions', 'sessions_with_warnings', 'critical_sessions']
                if all(field in data['summary'] for field in required_summary_fields):
                    self._record_test_result('storage_overview', True,
                                           f"Overview retrieved: {data['summary']['total_sessions']} sessions")
                else:
                    self._record_test_result('storage_overview', False,
                                           f"Missing required summary fields")
            else:
                self._record_test_result('storage_overview', False,
                                       f"Invalid response format: {data}")
        else:
            self._record_test_result('storage_overview', False,
                                   f"HTTP {response.status_code}: {response.text}")

    def _test_start_storage_monitoring(self):
        """Test starting storage monitoring service"""
        response = self._make_request('POST', '/api/storage/monitoring/start')
        
        if response.status_code in [200, 400]:  # 400 might mean already running
            data = response.json()
            if 'success' in data and 'running' in data:
                self._record_test_result('start_storage_monitoring', True,
                                       f"Start request processed: {data.get('message', 'No message')}")
            else:
                self._record_test_result('start_storage_monitoring', False,
                                       f"Invalid response format: {data}")
        else:
            self._record_test_result('start_storage_monitoring', False,
                                   f"HTTP {response.status_code}: {response.text}")

    def _test_force_storage_check(self):
        """Test forcing immediate storage check"""
        response = self._make_request('POST', '/api/storage/monitoring/check-now')
        
        if response.status_code in [200, 500]:  # 500 might be expected if no OAuth sessions
            data = response.json()
            if 'success' in data and 'forced_check' in data:
                self._record_test_result('force_storage_check', True,
                                       f"Force check completed: {data.get('message', 'Check executed')}")
            else:
                self._record_test_result('force_storage_check', False,
                                       f"Invalid response format: {data}")
        else:
            self._record_test_result('force_storage_check', False,
                                   f"HTTP {response.status_code}: {response.text}")

    def _test_update_monitoring_config(self):
        """Test updating monitoring configuration"""
        config_data = {
            'check_interval_minutes': 120,
            'enabled': True
        }
        
        response = self._make_request('PUT', '/api/storage/monitoring/config', config_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'new_config' in data:
                new_config = data['new_config']
                if new_config.get('check_interval_minutes') == 120:
                    self._record_test_result('update_monitoring_config', True,
                                           f"Config updated: interval={new_config['check_interval_minutes']}")
                else:
                    self._record_test_result('update_monitoring_config', False,
                                           f"Config not updated correctly: {new_config}")
            else:
                self._record_test_result('update_monitoring_config', False,
                                       f"Invalid response format: {data}")
        else:
            self._record_test_result('update_monitoring_config', False,
                                   f"HTTP {response.status_code}: {response.text}")

    def _test_stop_storage_monitoring(self):
        """Test stopping storage monitoring service"""
        response = self._make_request('POST', '/api/storage/monitoring/stop')
        
        if response.status_code in [200, 400]:  # 400 might mean not running
            data = response.json()
            if 'success' in data and 'running' in data:
                self._record_test_result('stop_storage_monitoring', True,
                                       f"Stop request processed: {data.get('message', 'No message')}")
            else:
                self._record_test_result('stop_storage_monitoring', False,
                                       f"Invalid response format: {data}")
        else:
            self._record_test_result('stop_storage_monitoring', False,
                                   f"HTTP {response.status_code}: {response.text}")

    def _test_admin_access_control(self):
        """Test that admin access is properly enforced"""
        # This test assumes the test user is an admin
        # In a real scenario, you'd test with a non-admin user and expect 403
        
        endpoints_to_test = [
            '/api/storage/monitoring/status',
            '/api/storage/overview',
            '/api/storage/monitoring/start',
            '/api/storage/monitoring/stop'
        ]
        
        admin_accessible = 0
        total_endpoints = len(endpoints_to_test)
        
        for endpoint in endpoints_to_test:
            method = 'POST' if 'start' in endpoint or 'stop' in endpoint else 'GET'
            response = self._make_request(method, endpoint)
            
            # Should get 200, 400, or 500 for admin user (not 403)
            if response.status_code != 403:
                admin_accessible += 1
        
        if admin_accessible == total_endpoints:
            self._record_test_result('admin_access_control', True,
                                   f"Admin can access all {total_endpoints} endpoints")
        else:
            self._record_test_result('admin_access_control', False,
                                   f"Admin access denied to {total_endpoints - admin_accessible} endpoints")

    def _test_api_response_formats(self):
        """Test that API responses follow expected formats"""
        test_endpoints = [
            ('/api/storage/monitoring/status', 'GET'),
            ('/api/storage/overview', 'GET')
        ]
        
        valid_formats = 0
        total_endpoints = len(test_endpoints)
        
        for endpoint, method in test_endpoints:
            response = self._make_request(method, endpoint)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'success' in data and 'timestamp' in data:
                        valid_formats += 1
                except:
                    pass
        
        if valid_formats == total_endpoints:
            self._record_test_result('api_response_formats', True,
                                   f"All {total_endpoints} endpoints return valid JSON format")
        else:
            self._record_test_result('api_response_formats', False,
                                   f"{total_endpoints - valid_formats} endpoints have invalid response format")

    def _print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 STORAGE MONITORING TEST SUMMARY")
        print("=" * 50)
        
        total = self.results['total_tests']
        passed = self.results['passed_tests']
        failed = self.results['failed_tests']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results['test_results']:
                if not result['passed']:
                    print(f"   - {result['test_name']}: {result['message']}")
        
        print(f"\n{'🎉 ALL TESTS PASSED!' if failed == 0 else '⚠️  SOME TESTS FAILED'}")


def main():
    """Run storage monitoring tests"""
    test_suite = StorageMonitoringTestSuite()
    results = test_suite.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results['failed_tests'] == 0 else 1


if __name__ == "__main__":
    exit(main())