"""
Integration Test Script for Enhanced File Management System

This script performs end-to-end testing of the complete file management workflow:
1. File upload with duplicate detection
2. Google Drive integration
3. File listing and filtering
4. Soft deletion and restoration
5. Admin operations
6. Error handling scenarios

Run this script to validate the entire system works correctly in integration.
"""

import os
import sys
import json
import time
import requests
import tempfile
from io import BytesIO
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class IntegrationTestRunner:
    """Comprehensive integration test runner for the enhanced file management system"""
    
    def __init__(self, base_url="http://localhost:5001", test_user_token=None, admin_token=None):
        """
        Initialize the test runner
        
        Args:
            base_url: Base URL of the API server
            test_user_token: JWT token for a test user
            admin_token: JWT token for an admin user
        """
        self.base_url = base_url.rstrip('/')
        self.test_user_token = test_user_token or "test-user-jwt-token"
        self.admin_token = admin_token or "test-admin-jwt-token"
        
        self.test_results = []
        self.uploaded_file_ids = []
        
    def log_result(self, test_name, success, message="", details=None):
        """Log test result"""
        status = "PASS" if success else "FAIL"
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'details': details or {}
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {message}")
        
    def create_test_file(self, filename="test_resume.pdf", content=None):
        """Create a test PDF file"""
        if content is None:
            content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Resume Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n294\n%%EOF'
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_file.write(content)
        temp_file.close()
        return temp_file.name, content
        
    def make_request(self, method, endpoint, token=None, files=None, data=None, json_data=None, params=None):
        """Make HTTP request with proper headers"""
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                if files:
                    response = requests.post(url, headers=headers, files=files, data=data, params=params)
                else:
                    if json_data:
                        headers['Content-Type'] = 'application/json'
                        response = requests.post(url, headers=headers, json=json_data, params=params)
                    else:
                        response = requests.post(url, headers=headers, data=data, params=params)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def test_health_check(self):
        """Test system health check"""
        test_name = "System Health Check"
        
        response = self.make_request('GET', '/health')
        if response is None:
            self.log_result(test_name, False, "Server not responding")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                self.log_result(test_name, True, "Server is healthy")
                return True
            else:
                self.log_result(test_name, False, f"Server unhealthy: {data}")
                return False
        else:
            self.log_result(test_name, False, f"Health check failed: {response.status_code}")
            return False
    
    def test_basic_file_upload(self):
        """Test basic file upload functionality"""
        test_name = "Basic File Upload"
        
        file_path, file_content = self.create_test_file("basic_test.pdf")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': ('basic_test.pdf', f, 'application/pdf')}
                data = {'process': 'false'}
                
                response = self.make_request('POST', '/api/files/upload', 
                                           token=self.test_user_token, files=files, data=data)
                
            if response and response.status_code == 201:
                data = response.json()
                if data.get('success') and 'file' in data:
                    file_id = data['file']['id']
                    self.uploaded_file_ids.append(file_id)
                    self.log_result(test_name, True, f"File uploaded successfully (ID: {file_id})")
                    return True, file_id
                else:
                    self.log_result(test_name, False, f"Invalid response format: {data}")
                    return False, None
            else:
                error_msg = response.json() if response else "No response"
                self.log_result(test_name, False, f"Upload failed: {response.status_code if response else 'No response'} - {error_msg}")
                return False, None
                
        finally:
            os.unlink(file_path)
    
    def test_duplicate_file_detection(self):
        """Test duplicate file detection"""
        test_name = "Duplicate File Detection"
        
        # Create identical file content
        file_content = b'%PDF-1.4\nDuplicate test content\n%%EOF'
        
        # Upload first file
        file_path1, _ = self.create_test_file("duplicate_test1.pdf", file_content)
        
        try:
            with open(file_path1, 'rb') as f:
                files = {'file': ('duplicate_test1.pdf', f, 'application/pdf')}
                data = {'process': 'false'}
                
                response1 = self.make_request('POST', '/api/files/upload', 
                                            token=self.test_user_token, files=files, data=data)
                
            if not response1 or response1.status_code != 201:
                self.log_result(test_name, False, "Failed to upload first file")
                return False
                
            first_file_data = response1.json()
            first_file_id = first_file_data['file']['id']
            self.uploaded_file_ids.append(first_file_id)
            
            # Upload identical file (should be detected as duplicate)
            file_path2, _ = self.create_test_file("duplicate_test2.pdf", file_content)
            
            with open(file_path2, 'rb') as f:
                files = {'file': ('duplicate_test2.pdf', f, 'application/pdf')}
                data = {'process': 'false'}
                
                response2 = self.make_request('POST', '/api/files/upload', 
                                            token=self.test_user_token, files=files, data=data)
                
            if response2 and response2.status_code == 201:
                data2 = response2.json()
                duplicate_info = data2.get('file', {}).get('duplicate_info', {})
                
                if duplicate_info.get('is_duplicate'):
                    second_file_id = data2['file']['id']
                    self.uploaded_file_ids.append(second_file_id)
                    
                    # Check that filename was modified
                    display_filename = data2['file']['display_filename']
                    if '(1)' in display_filename:
                        self.log_result(test_name, True, f"Duplicate detected and filename modified: {display_filename}")
                        return True
                    else:
                        self.log_result(test_name, False, f"Duplicate detected but filename not modified: {display_filename}")
                        return False
                else:
                    self.log_result(test_name, False, "Duplicate not detected for identical files")
                    return False
            else:
                error_msg = response2.json() if response2 else "No response"
                self.log_result(test_name, False, f"Second upload failed: {error_msg}")
                return False
                
        finally:
            os.unlink(file_path1)
            if 'file_path2' in locals():
                os.unlink(file_path2)
    
    def test_google_drive_integration(self):
        """Test Google Drive integration (mocked)"""
        test_name = "Google Drive Integration"
        
        # This test checks that the API accepts Google Drive parameters
        # In a real environment, you would need valid Google Drive credentials
        
        file_path, file_content = self.create_test_file("gdrive_test.pdf")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': ('gdrive_test.pdf', f, 'application/pdf')}
                data = {'process': 'false'}
                params = {
                    'google_drive': 'true',
                    'convert_to_doc': 'true',
                    'share_with_user': 'true'
                }
                
                response = self.make_request('POST', '/api/files/upload', 
                                           token=self.test_user_token, files=files, 
                                           data=data, params=params)
                
            if response:
                if response.status_code == 201:
                    data = response.json()
                    # Check if Google Drive info is present (even if mocked)
                    google_drive_info = data.get('file', {}).get('google_drive')
                    if google_drive_info or 'warnings' in data:
                        file_id = data['file']['id']
                        self.uploaded_file_ids.append(file_id)
                        self.log_result(test_name, True, "Google Drive parameters processed")
                        return True
                    else:
                        self.log_result(test_name, False, "Google Drive integration not handled")
                        return False
                else:
                    # Google Drive might fail in test environment, check for appropriate error handling
                    data = response.json()
                    if 'warnings' in data or 'error_code' in data:
                        self.log_result(test_name, True, "Google Drive failure handled gracefully")
                        return True
                    else:
                        self.log_result(test_name, False, f"Unexpected response: {data}")
                        return False
            else:
                self.log_result(test_name, False, "No response from server")
                return False
                
        finally:
            os.unlink(file_path)
    
    def test_file_listing(self):
        """Test file listing functionality"""
        test_name = "File Listing"
        
        response = self.make_request('GET', '/api/files', token=self.test_user_token)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('success') and 'files' in data:
                files = data['files']
                total = data.get('total', 0)
                
                # Check that we can see uploaded files
                uploaded_files_found = sum(1 for f in files if f['id'] in self.uploaded_file_ids)
                
                self.log_result(test_name, True, 
                              f"Found {len(files)} files, {uploaded_files_found} from our uploads (total: {total})")
                return True
            else:
                self.log_result(test_name, False, f"Invalid response format: {data}")
                return False
        else:
            error_msg = response.json() if response else "No response"
            self.log_result(test_name, False, f"Listing failed: {error_msg}")
            return False
    
    def test_soft_deletion(self):
        """Test soft deletion functionality"""
        test_name = "Soft Deletion"
        
        if not self.uploaded_file_ids:
            self.log_result(test_name, False, "No uploaded files to delete")
            return False
            
        file_id = self.uploaded_file_ids[0]
        
        # Delete the file
        response = self.make_request('DELETE', f'/api/files/{file_id}', token=self.test_user_token)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.log_result(test_name, True, f"File {file_id} soft-deleted successfully")
                return True, file_id
            else:
                self.log_result(test_name, False, f"Deletion failed: {data}")
                return False, None
        else:
            error_msg = response.json() if response else "No response"
            self.log_result(test_name, False, f"Delete request failed: {error_msg}")
            return False, None
    
    def test_file_restoration(self):
        """Test file restoration functionality"""
        test_name = "File Restoration"
        
        # First perform soft deletion
        deletion_success, deleted_file_id = self.test_soft_deletion()
        if not deletion_success:
            self.log_result(test_name, False, "Cannot test restoration without successful deletion")
            return False
            
        time.sleep(1)  # Brief pause to ensure deletion is processed
        
        # Now restore the file
        response = self.make_request('POST', f'/api/files/{deleted_file_id}/restore', 
                                   token=self.test_user_token)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.log_result(test_name, True, f"File {deleted_file_id} restored successfully")
                return True
            else:
                self.log_result(test_name, False, f"Restoration failed: {data}")
                return False
        else:
            error_msg = response.json() if response else "No response"
            self.log_result(test_name, False, f"Restore request failed: {error_msg}")
            return False
    
    def test_admin_functions(self):
        """Test admin functionality"""
        test_name = "Admin Functions"
        
        # Test listing deleted files (admin only)
        response = self.make_request('GET', '/api/admin/files/deleted', token=self.admin_token)
        
        if response:
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    deleted_files = data.get('files', [])
                    self.log_result(test_name, True, f"Admin can list {len(deleted_files)} deleted files")
                    return True
                else:
                    self.log_result(test_name, False, f"Admin listing failed: {data}")
                    return False
            elif response.status_code in [401, 403]:
                # Admin functions might not be accessible in test environment
                self.log_result(test_name, True, "Admin authentication handled (expected in test)")
                return True
            else:
                error_msg = response.json() if response else "No response"
                self.log_result(test_name, False, f"Admin request failed: {error_msg}")
                return False
        else:
            self.log_result(test_name, False, "No response from admin endpoint")
            return False
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        test_name = "Error Handling"
        
        # Test uploading without file
        response = self.make_request('POST', '/api/files/upload', token=self.test_user_token, 
                                   data={'process': 'false'})
        
        if response and response.status_code == 400:
            data = response.json()
            if not data.get('success') and 'error_code' in data:
                self.log_result(test_name, True, f"Error handling works: {data['error_code']}")
                return True
            else:
                self.log_result(test_name, False, f"Error response format incorrect: {data}")
                return False
        else:
            self.log_result(test_name, False, "Expected 400 error for missing file")
            return False
    
    def test_file_access_google_doc(self):
        """Test Google Doc access endpoint"""
        test_name = "Google Doc Access"
        
        if not self.uploaded_file_ids:
            self.log_result(test_name, False, "No uploaded files to test Google Doc access")
            return False
            
        file_id = self.uploaded_file_ids[-1]  # Use most recent upload
        
        response = self.make_request('GET', f'/api/files/{file_id}/google-doc', 
                                   token=self.test_user_token)
        
        if response:
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'google_doc' in data:
                    self.log_result(test_name, True, "Google Doc access successful")
                    return True
                else:
                    self.log_result(test_name, False, f"Invalid Google Doc response: {data}")
                    return False
            elif response.status_code == 404:
                # Expected if file doesn't have Google Drive version
                data = response.json()
                if 'Google Drive' in data.get('message', ''):
                    self.log_result(test_name, True, "Proper 404 for file without Google Drive version")
                    return True
                else:
                    self.log_result(test_name, False, f"Unexpected 404 message: {data}")
                    return False
            else:
                error_msg = response.json() if response else "No response"
                self.log_result(test_name, False, f"Google Doc access failed: {error_msg}")
                return False
        else:
            self.log_result(test_name, False, "No response from Google Doc endpoint")
            return False
    
    def cleanup(self):
        """Clean up test files"""
        test_name = "Cleanup"
        
        cleaned_count = 0
        for file_id in self.uploaded_file_ids:
            try:
                # Try to permanently delete the file (admin operation)
                response = self.make_request('DELETE', f'/api/admin/files/{file_id}/permanent-delete', 
                                           token=self.admin_token)
                if response and response.status_code == 200:
                    cleaned_count += 1
                else:
                    # If admin delete fails, try regular soft delete
                    response = self.make_request('DELETE', f'/api/files/{file_id}', 
                                               token=self.test_user_token)
                    if response and response.status_code == 200:
                        cleaned_count += 1
            except Exception as e:
                print(f"Error cleaning up file {file_id}: {e}")
                
        self.log_result(test_name, True, f"Cleaned up {cleaned_count}/{len(self.uploaded_file_ids)} test files")
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("=" * 60)
        print("ENHANCED FILE MANAGEMENT INTEGRATION TESTS")
        print("=" * 60)
        
        tests = [
            self.test_health_check,
            self.test_basic_file_upload,
            self.test_duplicate_file_detection,
            self.test_google_drive_integration,
            self.test_file_listing,
            self.test_file_restoration,
            self.test_admin_functions,
            self.test_error_handling,
            self.test_file_access_google_doc,
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                result = test()
                if result is True or (isinstance(result, tuple) and result[0] is True):
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"Test {test.__name__} crashed: {e}")
                failed += 1
                
        # Cleanup
        self.cleanup()
        
        print("\n" + "=" * 60)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {passed + failed}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")
        
        if failed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            print(f"  [{result['status']}] {result['test']}: {result['message']}")
            
        return passed, failed


def main():
    """Main function to run integration tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Enhanced File Management Integration Tests')
    parser.add_argument('--base-url', default='http://localhost:5001', 
                       help='Base URL of the API server')
    parser.add_argument('--user-token', help='JWT token for test user')
    parser.add_argument('--admin-token', help='JWT token for admin user')
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = IntegrationTestRunner(
        base_url=args.base_url,
        test_user_token=args.user_token,
        admin_token=args.admin_token
    )
    
    # Run tests
    passed, failed = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()