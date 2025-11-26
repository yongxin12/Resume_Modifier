#!/usr/bin/env python3

"""Debug script for file management integration test issue"""

import sys
import os
sys.path.append('core')

from unittest.mock import Mock, patch
import pytest

# Import test class
from testing.unit.test_file_management_integration import TestFileManagementIntegration

# Run a minimal version to see the error
def debug_download_error():
    """Debug the 500 error in file download"""
    
    # Set up test environment
    os.environ['TESTING'] = 'true'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    
    from app import create_app
    from app.extensions import db
    
    app = create_app({'TESTING': True})
    
    # Test instance
    test_instance = TestFileManagementIntegration()
    
    with app.app_context():
        with app.test_client() as client:
            # Create JWT token
            import jwt
            from datetime import datetime, timedelta
            
            token_payload = {
                'user_id': 1,
                'email': 'test@test.com',
                'exp': datetime.utcnow() + timedelta(hours=1)
            }
            token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
            
            authenticated_headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Mock JWT authentication
            with patch('app.utils.jwt_utils.verify_token') as mock_verify_token:
                mock_verify_token.return_value = {'user_id': 1, 'email': 'test@example.com'}
                
                # Mock storage configuration
                with patch('app.utils.storage_config.StorageConfigManager') as mock_storage_config:
                    mock_storage_config.get_storage_config_dict.return_value = {
                        'storage_type': 'local',
                        'local_storage_path': '/tmp'
                    }
                    
                    file_id = 456
                    
                    # Mock file data
                    mock_file_data = {
                        'id': file_id,
                        'user_id': 1,
                        'original_filename': 'test_resume.pdf',
                        'stored_filename': 'test_resume_456.pdf',
                        'file_path': '/storage/users/1/test_resume_456.pdf',
                        'storage_path': '/storage/users/1/test_resume_456.pdf',
                        'mime_type': 'application/pdf',
                        'file_size': 1024,
                        'processing_status': 'completed',
                        'extracted_text': 'Processed text content',
                        'is_active': True
                    }
                    
                    # Test download with mocking
                    with patch('app.models.temp.ResumeFile.query') as mock_query, \
                         patch('app.server.FileStorageService') as mock_storage_class:
                    
                        # Mock file record query - use proper values to avoid Mock objects
                        class MockFile:
                            def __init__(self, data):
                                for key, value in data.items():
                                    setattr(self, key, value)
                        
                        mock_file = MockFile(mock_file_data)
                        print(f"Mock file attributes: {[attr for attr in dir(mock_file) if not attr.startswith('_')]}")
                        print(f"file_path: {getattr(mock_file, 'file_path', 'NOT SET')}")
                        print(f"storage_path: {getattr(mock_file, 'storage_path', 'NOT SET')}")
                        mock_query.filter_by.return_value.first.return_value = mock_file
                    
                        # Mock storage service instance
                        mock_storage_instance = Mock()
                        mock_storage_class.return_value = mock_storage_instance
                        
                        from app.services.file_storage_service import StorageResult
                        success_result = StorageResult(
                            success=True,
                            file_path='/tmp/test_resume.pdf',
                            content_type="application/pdf",
                            filename="test_resume.pdf",
                            error_message=None
                        )
                        mock_storage_instance.download_file.return_value = success_result
                        print(f"Success result properties: success={success_result.success}, error={success_result.error_message}")
                        
                        print(f"Mocked storage service: {mock_storage_class}")
                        print(f"Mock instance: {mock_storage_instance}")
                        print(f"Download return: {mock_storage_instance.download_file.return_value}")
                        
                        # Mock send_file to avoid actual file operations
                        with patch('app.server.send_file') as mock_send_file:
                            mock_send_file.return_value = b'mocked_file_content'
                            
                            print("Making download request...")
                            download_response = client.get(
                                f'/api/files/{file_id}/download',
                                headers=authenticated_headers
                            )
                            
                            print(f"Response status: {download_response.status_code}")
                            print(f"Response data: {download_response.get_data(as_text=True)}")
                            
                            if download_response.status_code != 200:
                                try:
                                    error_data = download_response.get_json()
                                    print(f"Error JSON: {error_data}")
                                except:
                                    print("No JSON in response")

if __name__ == '__main__':
    debug_download_error()