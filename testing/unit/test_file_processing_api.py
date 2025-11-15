"""
Tests for file processing API endpoint
"""

import pytest
import os
from unittest.mock import patch, Mock
from flask import Flask
from app.extensions import db


class TestFileProcessingAPI:
    """Test suite for file processing API endpoint"""

    def setup_method(self):
        """Set up test environment before each test"""
        from datetime import datetime
        # Mock ResumeFile record for processing
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
            'is_active': True,
            'created_at': datetime(2024, 1, 1, 10, 0, 0),
            'updated_at': datetime(2024, 1, 1, 10, 0, 0),
            'processing_status': 'pending',
            'extracted_text': None,
            'page_count': None
        }

    def test_process_file_success(self, app, client, authenticated_headers):
        """Test successful file processing with authentication"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch.object(db.session, 'commit') as mock_commit:
                
                # Mock database query - need to chain filter_by().filter().first()
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_file
                
                # Mock storage service download
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    content=b"Mock PDF content for processing",
                    content_type="application/pdf"
                )
                
                # Mock processing service success
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=True,
                    text="This is extracted resume text content with skills and experience.",
                    page_count=2,
                    language='en',
                    metadata={'author': 'John Doe', 'creation_date': '2024-01-01'}
                )

                response = client.post(
                    '/api/files/123/process',
                    headers=authenticated_headers
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert 'processed successfully' in data['message'].lower()
                
                # Verify file processing status updated
                assert mock_file.processing_status == 'completed'
                assert mock_file.extracted_text is not None
                assert mock_file.page_count == 2
                assert mock_commit.call_count == 2  # Called twice: once to set processing, once after completion

    def test_process_file_not_found(self, app, client, authenticated_headers):
        """Test processing request for non-existent file"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                # Mock database query returning None
                mock_query.filter_by.return_value.filter.return_value.first.return_value = None
                
                response = client.post(
                    '/api/files/999/process',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 404
                data = response.get_json()
                assert data['success'] is False
                assert 'not found' in data['message'].lower()

    def test_process_file_unauthorized_access(self, app, client, authenticated_headers):
        """Test processing request for file owned by another user"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                # Mock no file found (file owned by different user gets filtered out)
                mock_query.filter_by.return_value.filter.return_value.first.return_value = None
                
                response = client.post(
                    '/api/files/123/process',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 404
                data = response.get_json()
                assert data['success'] is False
                assert 'file not found' in data['message'].lower()

    def test_process_file_no_authentication(self, app, client):
        """Test processing request without authentication"""
        with app.app_context():
            response = client.post('/api/files/123/process')
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'authentication' in data['error'].lower() or 'token' in data['error'].lower()

    def test_process_file_invalid_token(self, app, client):
        """Test processing request with invalid authentication token"""
        with app.app_context():
            headers = {'Authorization': 'Bearer invalid_token'}
            response = client.post('/api/files/123/process', headers=headers)
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'invalid' in data['error'].lower() or 'token' in data['error'].lower()

    def test_process_file_already_processed(self, app, client, authenticated_headers):
        """Test processing request for already processed file"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                # Mock file that's already processed
                mock_file = Mock()
                test_record = self.test_file_record.copy()
                test_record['processing_status'] = 'completed'
                test_record['extracted_text'] = 'Already extracted text'
                for key, value in test_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_file
                
                response = client.post(
                    '/api/files/123/process',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 400
                data = response.get_json()
                assert data['success'] is False
                assert 'already been processed' in data['message'].lower()

    def test_process_file_currently_processing(self, app, client, authenticated_headers):
        """Test processing request for file that's currently being processed"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                # Mock file that's currently being processed
                mock_file = Mock()
                test_record = self.test_file_record.copy()
                test_record['processing_status'] = 'processing'
                for key, value in test_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_file
                
                response = client.post(
                    '/api/files/123/process',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 400
                data = response.get_json()
                assert data['success'] is False
                assert 'already being processed' in data['message'].lower()

    def test_process_file_processing_service_failure(self, app, client, authenticated_headers):
        """Test processing when FileProcessingService fails"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch.object(db.session, 'commit') as mock_commit:

                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_file

                # Mock storage service download
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    content=b"Mock PDF content for processing",
                    content_type="application/pdf"
                )

                # Mock processing service failure
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=False,
                    error_message="Failed to extract text from PDF"
                )

                response = client.post(
                    '/api/files/123/process',
                    headers=authenticated_headers
                )

                assert response.status_code == 500
                data = response.get_json()
                assert data['success'] is False
                assert 'file processing failed' in data['message'].lower()
                
                # Verify file status set to failed
                assert mock_file.processing_status == 'failed'

    def test_process_file_invalid_file_id_format(self, app, client, authenticated_headers):
        """Test processing with invalid file ID format"""
        with app.app_context():
            response = client.post(
                '/api/files/invalid_id/process',
                headers=authenticated_headers
            )
            
            assert response.status_code == 404  # Flask returns 404 for invalid int in route

    def test_process_file_database_failure(self, app, client, authenticated_headers):
        """Test processing when database commit fails"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process, \
                 patch.object(db.session, 'commit') as mock_commit:

                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_file

                # Mock processing service success
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=True,
                    text="Extracted text",
                    page_count=1
                )

                # Mock database commit failure
                mock_commit.side_effect = Exception("Database connection lost")

                response = client.post(
                    '/api/files/123/process',
                    headers=authenticated_headers
                )

                assert response.status_code == 500
                data = response.get_json()
                assert data['success'] is False
                assert 'error' in data['message'].lower()

    def test_process_file_docx_format(self, app, client, authenticated_headers):
        """Test successful processing of DOCX file"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch.object(db.session, 'commit') as mock_commit:

                # Mock DOCX file record
                mock_file = Mock()
                docx_record = self.test_file_record.copy()
                docx_record['original_filename'] = 'resume.docx'
                docx_record['mime_type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                for key, value in docx_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_file

                # Mock storage service download
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    content=b"Mock DOCX content for processing",
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

                # Mock processing service success for DOCX
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=True,
                    text="DOCX content with formatting preserved",
                    page_count=3,
                    language='en'
                )

                response = client.post(
                    '/api/files/123/process',
                    headers=authenticated_headers
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert mock_file.processing_status == 'completed'
                assert mock_file.page_count == 3

    def test_process_file_logging_and_audit(self, app, client, authenticated_headers):
        """Test that successful processing is logged for audit purposes"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch.object(db.session, 'commit') as mock_commit, \
                 patch('logging.getLogger') as mock_logger:

                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_file

                # Mock storage service download
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    content=b"Mock content for processing",
                    content_type="application/pdf"
                )

                # Mock processing service success
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=True,
                    text="Processed content",
                    page_count=1
                )

                # Mock logger
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance

                response = client.post(
                    '/api/files/123/process',
                    headers=authenticated_headers
                )

                assert response.status_code == 200
                # Verify logging was called
                mock_logger_instance.info.assert_called()

    def test_process_file_response_schema(self, app, client, authenticated_headers):
        """Test that processing response follows expected schema"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch.object(db.session, 'commit') as mock_commit:

                # Mock all services for success
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_file

                # Mock storage service download
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    content=b"Mock content for processing",
                    content_type="application/pdf"
                )

                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=True,
                    text="Sample text",
                    page_count=2,
                    language='en',
                    metadata={'author': 'Test User'}
                )

                response = client.post(
                    '/api/files/123/process',
                    headers=authenticated_headers
                )

                assert response.status_code == 200
                data = response.get_json()
                
                # Validate response schema
                required_fields = ['success', 'message', 'processing_result']
                for field in required_fields:
                    assert field in data

    def test_process_file_with_force_reprocess(self, app, client, authenticated_headers):
        """Test processing with force parameter to reprocess completed files"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch.object(db.session, 'commit') as mock_commit:

                # Mock file that's already processed
                mock_file = Mock()
                test_record = self.test_file_record.copy()
                test_record['processing_status'] = 'completed'
                test_record['extracted_text'] = 'Old extracted text'
                for key, value in test_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_file

                # Mock storage service download
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    content=b"Mock content for reprocessing",
                    content_type="application/pdf"
                )

                # Mock processing service success
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=True,
                    text="New extracted text content",
                    page_count=3
                )

                response = client.post(
                    '/api/files/123/process?force=true',
                    headers=authenticated_headers
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert 'processed successfully' in data['message'].lower()
                
                # Verify file was reprocessed
                assert mock_file.extracted_text == "New extracted text content"
                assert mock_file.page_count == 3

    def test_process_file_unsupported_format(self, app, client, authenticated_headers):
        """Test processing request for unsupported file format"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch.object(db.session, 'commit') as mock_commit:
                
                # Mock unsupported file format
                mock_file = Mock()
                unsupported_record = self.test_file_record.copy()
                unsupported_record['mime_type'] = 'image/jpeg'
                unsupported_record['original_filename'] = 'photo.jpg'
                for key, value in unsupported_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_file

                # Mock storage service download
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    content=b"JPEG image content",
                    content_type="image/jpeg"
                )

                # Mock processing service failure for unsupported format
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=False,
                    error_message="Unsupported file format: image/jpeg"
                )
                
                response = client.post(
                    '/api/files/123/process',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 500  # Processing service failure returns 500
                data = response.get_json()
                assert data['success'] is False
                assert 'unsupported' in data['message'].lower() or 'format' in data['message'].lower()

    def test_process_file_storage_service_integration(self, app, client, authenticated_headers):
        """Test processing integrates with storage service for file retrieval"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process, \
                 patch('app.services.file_storage_service.FileStorageService.download_file') as mock_download, \
                 patch.object(db.session, 'commit') as mock_commit:

                # Mock database query
                mock_file = Mock()
                for key, value in self.test_file_record.items():
                    setattr(mock_file, key, value)
                mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_file

                # Mock storage service download
                from app.services.file_storage_service import StorageResult
                mock_download.return_value = StorageResult(
                    success=True,
                    content=b"Storage integrated content",
                    content_type="application/pdf"
                )
                
                # Mock processing service success
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=True,
                    text="Integrated processing result",
                    page_count=1
                )

                response = client.post(
                    '/api/files/123/process',
                    headers=authenticated_headers
                )

                assert response.status_code == 200
                # Verify storage service was called
                mock_download.assert_called_once()