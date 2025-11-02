"""
Comprehensive test suite for File Download API Endpoint
Following Test-Driven Development approach
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from flask import send_file
from app.server import api
from app.extensions import db
from app.models.temp import User, ResumeFile


class TestFileDownloadAPI:
    """Test suite for File Download API endpoint"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Test file content
        self.test_file_content = b"This is test resume content"
        
        # Mock ResumeFile record
        self.test_file_record = {
            'id': 123,
            'user_id': 1,
            'original_filename': 'test_resume.pdf',
            'stored_filename': 'secure_test_resume.pdf',
            'file_path': '/storage/users/1/secure_test_resume.pdf',
            'file_size': len(self.test_file_content),
            'mime_type': 'application/pdf',
            'storage_type': 'local',
            's3_bucket': None,
            'is_active': True
        }

    def test_download_valid_file_success(self, app, client, authenticated_headers):
        """Test successful file download with authentication"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch('app.server.send_file') as mock_send_file:
                
                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file
                
                # Mock storage service success
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    file_path='/tmp/downloaded_file.pdf',
                    file_size=len(self.test_file_content)
                )
                
                # Mock flask send_file
                mock_send_file.return_value = "File content response"
                
                response = client.get(
                    '/api/files/123/download',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 200
                mock_send_file.assert_called_once()
                
                # Verify proper headers and filename
                call_args = mock_send_file.call_args
                assert 'as_attachment' in call_args.kwargs
                assert call_args.kwargs['as_attachment'] is True
                assert 'download_name' in call_args.kwargs
                assert call_args.kwargs['download_name'] == 'test_resume.pdf'

    def test_download_file_not_found(self, app, client, authenticated_headers):
        """Test download request for non-existent file"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                # Mock database query returning None
                mock_query.filter_by.return_value.first.return_value = None
                
                response = client.get(
                    '/api/files/999/download',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 404
                data = response.get_json()
                assert data['success'] is False
                assert 'not found' in data['message'].lower()

    def test_download_unauthorized_access(self, app, client, authenticated_headers):
        """Test download request for file owned by another user"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                # Mock file owned by different user
                mock_file = Mock()
                test_record = self.test_file_record.copy()
                test_record['user_id'] = 999  # Different user
                for key, value in test_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file
                
                response = client.get(
                    '/api/files/123/download',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 403
                data = response.get_json()
                assert data['success'] is False
                assert 'access denied' in data['message'].lower() or 'forbidden' in data['message'].lower()

    def test_download_no_authentication(self, app, client):
        """Test download request without authentication"""
        with app.app_context():
            response = client.get('/api/files/123/download')
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'authentication' in data.get('error', data.get('message', '')).lower() or 'unauthorized' in data.get('error', data.get('message', '')).lower()

    def test_download_invalid_token(self, app, client):
        """Test download request with invalid authentication token"""
        with app.app_context():
            headers = {'Authorization': 'Bearer invalid_token'}
            response = client.get('/api/files/123/download', headers=headers)
            
            assert response.status_code == 401
            data = response.get_json()
            error_msg = data.get('error', data.get('message', '')).lower()
            assert any(word in error_msg for word in ['authentication', 'unauthorized', 'invalid', 'token'])

    def test_download_inactive_file(self, app, client, authenticated_headers):
        """Test download request for deactivated file"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                # Mock query to return None (inactive files are filtered out)
                mock_query.filter_by.return_value.first.return_value = None
                
                response = client.get(
                    '/api/files/123/download',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 404
                data = response.get_json()
                assert data['success'] is False
                assert 'not found' in data['message'].lower()

    def test_download_storage_failure(self, app, client, authenticated_headers):
        """Test download when storage service fails"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download:
                
                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file
                
                # Mock storage service failure
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=False,
                    error_message="File not found in storage"
                )
                
                response = client.get(
                    '/api/files/123/download',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 500
                data = response.get_json()
                assert data['success'] is False
                assert 'download failed' in data['message'].lower()

    def test_download_s3_file_success(self, app, client, authenticated_headers):
        """Test successful download of S3-stored file"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch('app.server.send_file') as mock_send_file:
                
                # Mock S3 file record
                mock_file = Mock()
                s3_record = self.test_file_record.copy()
                s3_record['storage_type'] = 's3'
                s3_record['s3_bucket'] = 'test-bucket'
                s3_record['file_path'] = 'users/1/secure_test_resume.pdf'
                for key, value in s3_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file
                
                # Mock storage service success for S3
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    file_path='/tmp/s3_downloaded_file.pdf',
                    file_size=len(self.test_file_content)
                )
                
                mock_send_file.return_value = "S3 File content response"
                
                response = client.get(
                    '/api/files/123/download',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 200
                mock_send_file.assert_called_once()

    def test_download_invalid_file_id_format(self, app, client, authenticated_headers):
        """Test download with invalid file ID format"""
        with app.app_context():
            response = client.get(
                '/api/files/invalid_id/download',
                headers=authenticated_headers
            )
            
            # Flask route <int:file_id> automatically rejects non-integers with 404
            assert response.status_code == 404

    def test_download_with_inline_parameter(self, app, client, authenticated_headers):
        """Test download with inline parameter for viewing in browser"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch('app.server.send_file') as mock_send_file:
                
                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file
                
                # Mock storage service success
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    file_path='/tmp/downloaded_file.pdf',
                    file_size=len(self.test_file_content)
                )
                
                mock_send_file.return_value = "Inline file response"
                
                response = client.get(
                    '/api/files/123/download?inline=true',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 200
                mock_send_file.assert_called_once()
                
                # Verify inline parameter affects as_attachment
                call_args = mock_send_file.call_args
                assert call_args.kwargs['as_attachment'] is False

    def test_download_response_headers(self, app, client, authenticated_headers):
        """Test that download sets appropriate response headers"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch('app.server.send_file') as mock_send_file:
                
                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file
                
                # Mock storage service success
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    file_path='/tmp/downloaded_file.pdf',
                    file_size=len(self.test_file_content)
                )
                
                mock_send_file.return_value = "File response"
                
                response = client.get(
                    '/api/files/123/download',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 200
                
                # Verify send_file called with correct parameters
                call_args = mock_send_file.call_args
                assert 'mimetype' in call_args.kwargs
                assert call_args.kwargs['mimetype'] == 'application/pdf'

    def test_download_logging_and_audit(self, app, client, authenticated_headers):
        """Test that successful downloads are logged for audit purposes"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch('app.server.send_file') as mock_send_file, \
                 patch('logging.getLogger') as mock_logger:
                
                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file
                
                # Mock storage service success
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    file_path='/tmp/downloaded_file.pdf',
                    file_size=len(self.test_file_content)
                )
                
                mock_send_file.return_value = "File response"
                
                response = client.get(
                    '/api/files/123/download',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 200
                
                # Verify logging was called
                mock_logger.assert_called()

    def test_download_file_size_validation(self, app, client, authenticated_headers):
        """Test download handles files with large sizes appropriately"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch('app.server.send_file') as mock_send_file:
                
                # Mock large file record
                mock_file = Mock()
                large_file_record = self.test_file_record.copy()
                large_file_record['file_size'] = 50 * 1024 * 1024  # 50MB
                for key, value in large_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file
                
                # Mock storage service success
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    file_path='/tmp/large_file.pdf',
                    file_size=50 * 1024 * 1024
                )
                
                mock_send_file.return_value = "Large file response"
                
                response = client.get(
                    '/api/files/123/download',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 200
                mock_send_file.assert_called_once()

    def test_download_concurrent_requests(self, app, client, authenticated_headers):
        """Test that download handles concurrent requests safely"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch('app.server.send_file') as mock_send_file:
                
                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file
                
                # Mock storage service success
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    file_path='/tmp/downloaded_file.pdf',
                    file_size=len(self.test_file_content)
                )
                
                mock_send_file.return_value = "File response"
                
                # Make concurrent requests (simulated)
                response1 = client.get('/api/files/123/download', headers=authenticated_headers)
                response2 = client.get('/api/files/123/download', headers=authenticated_headers)
                
                assert response1.status_code == 200
                assert response2.status_code == 200
                assert mock_send_file.call_count == 2