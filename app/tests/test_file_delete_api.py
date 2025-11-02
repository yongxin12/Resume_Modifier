"""
Tests for file delete API endpoint
"""

import pytest
import os
from unittest.mock import patch, Mock
from flask import Flask
from app.extensions import db


class TestFileDeleteAPI:
    """Test suite for file delete API endpoint"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Mock ResumeFile record
        self.test_file_record = {
            'id': 123,
            'user_id': 1,
            'original_filename': 'test_resume.pdf',
            'stored_filename': 'secure_test_resume.pdf',
            'file_path': '/storage/users/1/secure_test_resume.pdf',
            'file_size': 1024,
            'mime_type': 'application/pdf',
            'storage_type': 'local',
            's3_bucket': None,
            'is_active': True
        }

    def test_delete_valid_file_success(self, app, client, authenticated_headers):
        """Test successful file deletion with authentication"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.delete_file') as mock_delete, \
                 patch.object(db.session, 'commit') as mock_commit:

                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file

                # Mock storage service success
                from app.services.file_storage_service import StorageResult
                mock_delete.return_value = StorageResult(
                    success=True
                )
                
                response = client.delete(
                    '/api/files/123',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert 'deleted successfully' in data['message'].lower()
                
                # Verify file was marked as inactive
                assert mock_file.is_active is False
                mock_commit.assert_called_once()

    def test_delete_file_not_found(self, app, client, authenticated_headers):
        """Test delete request for non-existent file"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                # Mock database query returning None
                mock_query.filter_by.return_value.first.return_value = None
                
                response = client.delete(
                    '/api/files/999',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 404
                data = response.get_json()
                assert data['success'] is False
                assert 'not found' in data['message'].lower()

    def test_delete_unauthorized_access(self, app, client, authenticated_headers):
        """Test delete request for file owned by another user"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                # Mock file owned by different user
                mock_file = Mock()
                test_record = self.test_file_record.copy()
                test_record['user_id'] = 999  # Different user
                for key, value in test_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file
                
                response = client.delete(
                    '/api/files/123',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 403
                data = response.get_json()
                assert data['success'] is False
                assert 'access denied' in data['message'].lower() or 'forbidden' in data['message'].lower()

    def test_delete_no_authentication(self, app, client):
        """Test delete request without authentication"""
        with app.app_context():
            response = client.delete('/api/files/123')
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'authentication' in data['error'].lower() or 'token' in data['error'].lower()

    def test_delete_invalid_token(self, app, client):
        """Test delete request with invalid authentication token"""
        with app.app_context():
            headers = {'Authorization': 'Bearer invalid_token'}
            response = client.delete('/api/files/123', headers=headers)
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'invalid' in data['error'].lower() or 'token' in data['error'].lower()

    def test_delete_already_deleted_file(self, app, client, authenticated_headers):
        """Test delete request for already inactive file"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                # Mock query to return None (inactive files are filtered out)
                mock_query.filter_by.return_value.first.return_value = None
                
                response = client.delete(
                    '/api/files/123',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 404
                data = response.get_json()
                assert data['success'] is False
                assert 'not found' in data['message'].lower()

    def test_delete_storage_failure(self, app, client, authenticated_headers):
        """Test delete when storage service fails"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.server.FileStorageService') as mock_storage_class:

                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file

                # Mock storage service instance and failure
                mock_storage_instance = Mock()
                mock_storage_class.return_value = mock_storage_instance
                
                from app.services.file_storage_service import StorageResult
                mock_storage_instance.delete_file.return_value = StorageResult(
                    success=False,
                    error_message="Storage service unavailable"
                )

                response = client.delete(
                    '/api/files/123?force=true',
                    headers=authenticated_headers
                )

                assert response.status_code == 500
                data = response.get_json()
                assert data['success'] is False
                assert 'storage' in data['message'].lower()

    def test_delete_s3_file_success(self, app, client, authenticated_headers):
        """Test successful deletion of S3-stored file"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.delete_file') as mock_delete, \
                 patch.object(db.session, 'commit') as mock_commit:

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
                mock_delete.return_value = StorageResult(
                    success=True
                )

                response = client.delete(
                    '/api/files/123',
                    headers=authenticated_headers
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['delete_type'] == 'soft'

    def test_delete_invalid_file_id_format(self, app, client, authenticated_headers):
        """Test delete with invalid file ID format"""
        with app.app_context():
            response = client.delete(
                '/api/files/invalid_id',
                headers=authenticated_headers
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'invalid' in data['message'].lower()

    def test_delete_database_failure(self, app, client, authenticated_headers):
        """Test delete when database commit fails"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.delete_file') as mock_delete, \
                 patch.object(db.session, 'commit') as mock_commit:

                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file

                # Mock storage service success
                from app.services.file_storage_service import StorageResult
                mock_delete.return_value = StorageResult(
                    success=True
                )

                # Mock database commit failure
                mock_commit.side_effect = Exception("Database connection lost")

                response = client.delete(
                    '/api/files/123',
                    headers=authenticated_headers
                )

                assert response.status_code == 500
                data = response.get_json()
                assert data['success'] is False
                assert 'error' in data['message'].lower()

    def test_delete_soft_delete_behavior(self, app, client, authenticated_headers):
        """Test that delete is soft delete (marks as inactive) not hard delete"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.delete_file') as mock_delete, \
                 patch.object(db.session, 'commit') as mock_commit:

                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file

                # Mock storage service success
                from app.services.file_storage_service import StorageResult
                mock_delete.return_value = StorageResult(
                    success=True
                )
                
                response = client.delete(
                    '/api/files/123',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['delete_type'] == 'soft'
                
                # Verify file was marked as inactive (soft delete)
                assert mock_file.is_active is False
                assert hasattr(mock_file, 'updated_at')

    def test_delete_logging_and_audit(self, app, client, authenticated_headers):
        """Test that successful deletions are logged for audit purposes"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.delete_file') as mock_delete, \
                 patch.object(db.session, 'commit') as mock_commit, \
                 patch('logging.getLogger') as mock_logger:

                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file

                # Mock storage service success
                from app.services.file_storage_service import StorageResult
                mock_delete.return_value = StorageResult(
                    success=True
                )

                # Mock logger
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance

                response = client.delete(
                    '/api/files/123',
                    headers=authenticated_headers
                )

                assert response.status_code == 200
                # Verify logging was called
                mock_logger_instance.info.assert_called()

    def test_delete_response_schema(self, app, client, authenticated_headers):
        """Test that delete response follows expected schema"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.delete_file') as mock_delete, \
                 patch.object(db.session, 'commit') as mock_commit:

                # Mock all services for success
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file

                from app.services.file_storage_service import StorageResult
                mock_delete.return_value = StorageResult(
                    success=True
                )

                response = client.delete(
                    '/api/files/123',
                    headers=authenticated_headers
                )

                assert response.status_code == 200
                data = response.get_json()
                
                # Validate response schema
                assert 'success' in data
                assert 'message' in data
                assert 'file_id' in data
                assert 'delete_type' in data
                assert data['file_id'] == 123
                assert data['delete_type'] in ['soft', 'hard']

    def test_delete_concurrent_requests(self, app, client, authenticated_headers):
        """Test that delete handles concurrent requests safely"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_storage_service.FileStorageService.delete_file') as mock_delete, \
                 patch.object(db.session, 'commit') as mock_commit:

                # Mock database query for first request
                mock_file1 = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file1, key, value)

                # Mock database query for second request (file already deleted)
                mock_query.filter_by.return_value.first.side_effect = [mock_file1, None]

                # Mock storage service success
                from app.services.file_storage_service import StorageResult
                mock_delete.return_value = StorageResult(
                    success=True
                )

                # First request should succeed
                response1 = client.delete(
                    '/api/files/123',
                    headers=authenticated_headers
                )
                assert response1.status_code == 200

                # Second request should fail (file already deleted)
                response2 = client.delete(
                    '/api/files/123',
                    headers=authenticated_headers
                )
                assert response2.status_code == 404

    def test_delete_with_force_parameter(self, app, client, authenticated_headers):
        """Test delete with force parameter for hard delete"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.server.FileStorageService') as mock_storage_class, \
                 patch.object(db.session, 'delete') as mock_db_delete, \
                 patch.object(db.session, 'commit') as mock_commit:

                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.first.return_value = mock_file

                # Mock storage service instance and method
                mock_storage_instance = Mock()
                mock_storage_class.return_value = mock_storage_instance
                
                from app.services.file_storage_service import StorageResult
                mock_storage_instance.delete_file.return_value = StorageResult(
                    success=True
                )

                response = client.delete(
                    '/api/files/123?force=true',
                    headers=authenticated_headers
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['delete_type'] == 'hard'
                
                # Verify hard delete (db.session.delete called)
                mock_db_delete.assert_called_once_with(mock_file)
                mock_commit.assert_called_once()