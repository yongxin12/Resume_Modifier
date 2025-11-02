"""
Comprehensive test suite for File Upload API Endpoint
Following Test-Driven Development approach
"""

import pytest
import tempfile
import os
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock
from werkzeug.datastructures import FileStorage
from app.server import api
from app.extensions import db
from app.models.temp import User, ResumeFile


class TestFileUploadAPI:
    """Test suite for File Upload API endpoint"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Create test file contents
        self.valid_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n" + b"A" * 1000
        self.valid_docx_content = b"PK\x03\x04" + b"\x00" * 1000  # ZIP header for DOCX
        self.invalid_content = b"This is not a valid file"
        
        # Create test user
        self.test_user = {
            'id': 1,
            'email': 'testuser@example.com',
            'password_hash': 'hashed_password'
        }

    def test_upload_valid_pdf_success(self, app, client, authenticated_headers):
        """Test successful PDF file upload"""
        with app.app_context():
            # Create a mock PDF file
            pdf_file = FileStorage(
                stream=BytesIO(self.valid_pdf_content),
                filename="test_resume.pdf",
                content_type="application/pdf"
            )
            
            with patch('app.utils.file_validator.FileValidator.validate_file') as mock_validate, \
                 patch('app.services.file_storage_service.FileStorageService.upload_file') as mock_storage, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process:
                
                # Mock validator success
                mock_validate.return_value.is_valid = True
                mock_validate.return_value.sanitized_filename = "secure_test_resume.pdf"
                
                # Mock storage success
                from app.services.file_storage_service import StorageResult
                mock_storage.return_value = StorageResult(
                    success=True,
                    storage_type='local',
                    file_path='/storage/users/1/secure_test_resume.pdf',
                    file_size=len(self.valid_pdf_content),
                    url='http://localhost:5001/api/files/123/download'
                )
                
                # Mock processing success
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=True,
                    text="Sample resume text content",
                    file_type="pdf",
                    metadata={'word_count': 4, 'page_count': 1}
                )
                
                # Make authenticated request
                response = client.post(
                    '/api/files/upload',
                    data={'file': (BytesIO(self.valid_pdf_content), 'test_resume.pdf')},
                    headers=authenticated_headers,
                    content_type='multipart/form-data'
                )
                
                assert response.status_code == 201
                data = response.get_json()
                assert data['success'] is True
                assert data['message'] == 'File uploaded successfully'
                assert 'file' in data
                assert data['file']['original_filename'] == 'test_resume.pdf'
                assert data['file']['sanitized_filename'] == 'secure_test_resume.pdf'
                assert data['file']['file_size'] == len(self.valid_pdf_content)
                assert data['file']['file_type'] == 'pdf'
                assert 'file_id' in data['file']
                assert 'download_url' in data['file']

    def test_upload_valid_docx_success(self, app, client, authenticated_headers):
        """Test successful DOCX file upload"""
        with app.app_context():
            docx_file = FileStorage(
                stream=BytesIO(self.valid_docx_content),
                filename="test_resume.docx",
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
            with patch('app.utils.file_validator.FileValidator.validate_file') as mock_validate, \
                 patch('app.services.file_storage_service.FileStorageService.upload_file') as mock_storage, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process:
                
                # Mock validator success
                mock_validate.return_value.is_valid = True
                mock_validate.return_value.sanitized_filename = "secure_test_resume.docx"
                
                # Mock storage success
                from app.services.file_storage_service import StorageResult
                mock_storage.return_value = StorageResult(
                    success=True,
                    storage_type='local',
                    file_path='/storage/users/1/secure_test_resume.docx',
                    file_size=len(self.valid_docx_content),
                    url='http://localhost:5001/api/files/124/download'
                )
                
                # Mock processing success
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=True,
                    text="Sample DOCX resume content",
                    file_type="docx",
                    metadata={'word_count': 5, 'paragraph_count': 2}
                )
                
                headers = {'Authorization': f'Bearer {sample_user["token"]}'}
                response = client.post(
                    '/api/files/upload',
                    data={'file': (BytesIO(self.valid_docx_content), 'test_resume.docx')},
                    headers=headers,
                    content_type='multipart/form-data'
                )
                
                assert response.status_code == 201
                data = response.get_json()
                assert data['success'] is True
                assert data['file']['file_type'] == 'docx'

    def test_upload_no_authentication(self, app, client):
        """Test file upload without authentication"""
        with app.app_context():
            response = client.post(
                '/api/files/upload',
                data={'file': (BytesIO(self.valid_pdf_content), 'test.pdf')},
                content_type='multipart/form-data'
            )
            
            assert response.status_code == 401
            data = response.get_json()
            assert data['success'] is False
            assert 'authentication' in data['message'].lower() or 'unauthorized' in data['message'].lower()

    def test_upload_invalid_token(self, app, client):
        """Test file upload with invalid token"""
        with app.app_context():
            headers = {'Authorization': 'Bearer invalid_token'}
            response = client.post(
                '/api/files/upload',
                data={'file': (BytesIO(self.valid_pdf_content), 'test.pdf')},
                headers=headers,
                content_type='multipart/form-data'
            )
            
            assert response.status_code == 401
            data = response.get_json()
            assert data['success'] is False

    def test_upload_valid_docx_success(self, app, client, authenticated_headers):
        """Test upload request without file"""
        with app.app_context():
            headers = {'Authorization': f'Bearer {sample_user["token"]}'}
            response = client.post(
                '/api/files/upload',
                headers=headers,
                content_type='multipart/form-data'
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'no file' in data['message'].lower()

    def test_upload_valid_docx_success(self, app, client, authenticated_headers):
        """Test upload with empty filename"""
        with app.app_context():
            headers = {'Authorization': f'Bearer {sample_user["token"]}'}
            response = client.post(
                '/api/files/upload',
                data={'file': (BytesIO(self.valid_pdf_content), '')},
                headers=headers,
                content_type='multipart/form-data'
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'filename' in data['message'].lower()

    def test_upload_valid_docx_success(self, app, client, authenticated_headers):
        """Test file upload with validation failure"""
        with app.app_context():
            with patch('app.utils.file_validator.FileValidator.validate_file') as mock_validate:
                # Mock validator failure
                mock_validate.return_value.is_valid = False
                mock_validate.return_value.errors = ['Invalid file type', 'File too large']
                
                headers = {'Authorization': f'Bearer {sample_user["token"]}'}
                response = client.post(
                    '/api/files/upload',
                    data={'file': (BytesIO(self.invalid_content), 'invalid.txt')},
                    headers=headers,
                    content_type='multipart/form-data'
                )
                
                assert response.status_code == 400
                data = response.get_json()
                assert data['success'] is False
                assert 'validation failed' in data['message'].lower()
                assert 'errors' in data
                assert len(data['errors']) == 2

    def test_upload_valid_docx_success(self, app, client, authenticated_headers):
        """Test file upload with storage failure"""
        with app.app_context():
            with patch('app.utils.file_validator.FileValidator.validate_file') as mock_validate, \
                 patch('app.services.file_storage_service.FileStorageService.upload_file') as mock_storage:
                
                # Mock validator success
                mock_validate.return_value.is_valid = True
                mock_validate.return_value.sanitized_filename = "secure_test.pdf"
                
                # Mock storage failure
                from app.services.file_storage_service import StorageResult
                mock_storage.return_value = StorageResult(
                    success=False,
                    error_message="Storage service unavailable"
                )
                
                headers = {'Authorization': f'Bearer {sample_user["token"]}'}
                response = client.post(
                    '/api/files/upload',
                    data={'file': (BytesIO(self.valid_pdf_content), 'test.pdf')},
                    headers=headers,
                    content_type='multipart/form-data'
                )
                
                assert response.status_code == 500
                data = response.get_json()
                assert data['success'] is False
                assert 'storage failed' in data['message'].lower()

    def test_upload_valid_docx_success(self, app, client, authenticated_headers):
        """Test file upload with processing failure (should still succeed)"""
        with app.app_context():
            with patch('app.utils.file_validator.FileValidator.validate_file') as mock_validate, \
                 patch('app.services.file_storage_service.FileStorageService.upload_file') as mock_storage, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process:
                
                # Mock validator success
                mock_validate.return_value.is_valid = True
                mock_validate.return_value.sanitized_filename = "secure_test.pdf"
                
                # Mock storage success
                from app.services.file_storage_service import StorageResult
                mock_storage.return_value = StorageResult(
                    success=True,
                    storage_type='local',
                    file_path='/storage/users/1/secure_test.pdf',
                    file_size=len(self.valid_pdf_content),
                    url='http://localhost:5001/api/files/125/download'
                )
                
                # Mock processing failure
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=False,
                    error_message="Text extraction failed"
                )
                
                headers = {'Authorization': f'Bearer {sample_user["token"]}'}
                response = client.post(
                    '/api/files/upload',
                    data={'file': (BytesIO(self.valid_pdf_content), 'test.pdf')},
                    headers=headers,
                    content_type='multipart/form-data'
                )
                
                # Upload should still succeed even if processing fails
                assert response.status_code == 201
                data = response.get_json()
                assert data['success'] is True
                assert 'processing_warning' in data
                assert 'text extraction failed' in data['processing_warning'].lower()

    def test_upload_valid_docx_success(self, app, client, authenticated_headers):
        """Test file upload with database save failure"""
        with app.app_context():
            with patch('app.utils.file_validator.FileValidator.validate_file') as mock_validate, \
                 patch('app.services.file_storage_service.FileStorageService.upload_file') as mock_storage, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process, \
                 patch.object(db.session, 'add') as mock_add, \
                 patch.object(db.session, 'commit') as mock_commit:
                
                # Mock validator success
                mock_validate.return_value.is_valid = True
                mock_validate.return_value.sanitized_filename = "secure_test.pdf"
                
                # Mock storage success
                from app.services.file_storage_service import StorageResult
                mock_storage.return_value = StorageResult(
                    success=True,
                    storage_type='local',
                    file_path='/storage/users/1/secure_test.pdf',
                    file_size=len(self.valid_pdf_content),
                    url='http://localhost:5001/api/files/126/download'
                )
                
                # Mock processing success
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=True,
                    text="Sample text",
                    file_type="pdf"
                )
                
                # Mock database failure
                mock_commit.side_effect = Exception("Database connection error")
                
                headers = {'Authorization': f'Bearer {sample_user["token"]}'}
                response = client.post(
                    '/api/files/upload',
                    data={'file': (BytesIO(self.valid_pdf_content), 'test.pdf')},
                    headers=headers,
                    content_type='multipart/form-data'
                )
                
                assert response.status_code == 500
                data = response.get_json()
                assert data['success'] is False
                assert 'database error' in data['message'].lower()

    def test_upload_valid_docx_success(self, app, client, authenticated_headers):
        """Test rejection of files exceeding size limit"""
        with app.app_context():
            # Create a large file (mock)
            large_content = b"A" * (10 * 1024 * 1024)  # 10MB
            
            with patch('app.utils.file_validator.FileValidator.validate_file') as mock_validate:
                # Mock validator rejection due to file size
                mock_validate.return_value.is_valid = False
                mock_validate.return_value.errors = ['File size exceeds limit']
                
                headers = {'Authorization': f'Bearer {sample_user["token"]}'}
                response = client.post(
                    '/api/files/upload',
                    data={'file': (BytesIO(large_content), 'large_file.pdf')},
                    headers=headers,
                    content_type='multipart/form-data'
                )
                
                assert response.status_code == 400
                data = response.get_json()
                assert data['success'] is False
                assert 'size' in data['message'].lower()

    def test_upload_valid_docx_success(self, app, client, authenticated_headers):
        """Test rejection of unsupported file types"""
        with app.app_context():
            with patch('app.utils.file_validator.FileValidator.validate_file') as mock_validate:
                # Mock validator rejection for unsupported type
                mock_validate.return_value.is_valid = False
                mock_validate.return_value.errors = ['Unsupported file type']
                
                headers = {'Authorization': f'Bearer {sample_user["token"]}'}
                response = client.post(
                    '/api/files/upload',
                    data={'file': (BytesIO(b"image content"), 'image.jpg')},
                    headers=headers,
                    content_type='multipart/form-data'
                )
                
                assert response.status_code == 400
                data = response.get_json()
                assert data['success'] is False
                assert 'unsupported' in data['message'].lower() or 'invalid' in data['message'].lower()

    def test_upload_valid_docx_success(self, app, client, authenticated_headers):
        """Test that upload creates proper ResumeFile database record"""
        with app.app_context():
            with patch('app.utils.file_validator.FileValidator.validate_file') as mock_validate, \
                 patch('app.services.file_storage_service.FileStorageService.upload_file') as mock_storage, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process:
                
                # Mock validator success
                mock_validate.return_value.is_valid = True
                mock_validate.return_value.sanitized_filename = "secure_test.pdf"
                mock_validate.return_value.file_hash = "abc123hash"
                
                # Mock storage success
                from app.services.file_storage_service import StorageResult
                mock_storage.return_value = StorageResult(
                    success=True,
                    storage_type='local',
                    file_path='/storage/users/1/secure_test.pdf',
                    file_size=1000,
                    url='http://localhost:5001/api/files/127/download'
                )
                
                # Mock processing success
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=True,
                    text="Sample resume text",
                    file_type="pdf",
                    metadata={'word_count': 3, 'page_count': 1},
                    keywords=['resume', 'experience'],
                    language='en'
                )
                
                headers = {'Authorization': f'Bearer {sample_user["token"]}'}
                response = client.post(
                    '/api/files/upload',
                    data={'file': (BytesIO(self.valid_pdf_content), 'test_resume.pdf')},
                    headers=headers,
                    content_type='multipart/form-data'
                )
                
                assert response.status_code == 201
                data = response.get_json()
                
                # Verify response contains all expected fields
                file_data = data['file']
                assert file_data['user_id'] == sample_user['id']
                assert file_data['original_filename'] == 'test_resume.pdf'
                assert file_data['sanitized_filename'] == 'secure_test.pdf'
                assert file_data['file_size'] == 1000
                assert file_data['file_type'] == 'pdf'
                assert file_data['storage_type'] == 'local'
                assert file_data['file_hash'] == 'abc123hash'
                assert file_data['extracted_text'] == 'Sample resume text'
                assert file_data['metadata']['word_count'] == 3
                assert file_data['keywords'] == ['resume', 'experience']
                assert file_data['language'] == 'en'

    def test_upload_valid_docx_success(self, app, client, authenticated_headers):
        """Test file upload with processing disabled via parameter"""
        with app.app_context():
            with patch('app.utils.file_validator.FileValidator.validate_file') as mock_validate, \
                 patch('app.services.file_storage_service.FileStorageService.upload_file') as mock_storage, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process:
                
                # Mock validator success
                mock_validate.return_value.is_valid = True
                mock_validate.return_value.sanitized_filename = "secure_test.pdf"
                
                # Mock storage success
                from app.services.file_storage_service import StorageResult
                mock_storage.return_value = StorageResult(
                    success=True,
                    storage_type='local',
                    file_path='/storage/users/1/secure_test.pdf',
                    file_size=1000,
                    url='http://localhost:5001/api/files/128/download'
                )
                
                headers = {'Authorization': f'Bearer {sample_user["token"]}'}
                response = client.post(
                    '/api/files/upload?process=false',
                    data={'file': (BytesIO(self.valid_pdf_content), 'test.pdf')},
                    headers=headers,
                    content_type='multipart/form-data'
                )
                
                assert response.status_code == 201
                data = response.get_json()
                assert data['success'] is True
                
                # Processing should not have been called
                mock_process.assert_not_called()
                
                # Response should indicate processing was skipped
                assert data['file']['extracted_text'] is None
                assert data['file']['metadata'] == {}

    def test_upload_valid_docx_success(self, app, client, authenticated_headers):
        """Test that upload response follows expected schema"""
        with app.app_context():
            with patch('app.utils.file_validator.FileValidator.validate_file') as mock_validate, \
                 patch('app.services.file_storage_service.FileStorageService.upload_file') as mock_storage, \
                 patch('app.services.file_processing_service.FileProcessingService.process_file') as mock_process:
                
                # Mock all services for success
                mock_validate.return_value.is_valid = True
                mock_validate.return_value.sanitized_filename = "secure_test.pdf"
                
                from app.services.file_storage_service import StorageResult
                mock_storage.return_value = StorageResult(
                    success=True,
                    storage_type='local',
                    file_path='/storage/path',
                    file_size=1000,
                    url='http://localhost:5001/api/files/129/download'
                )
                
                from app.services.file_processing_service import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    success=True,
                    text="Sample text",
                    file_type="pdf"
                )
                
                headers = {'Authorization': f'Bearer {sample_user["token"]}'}
                response = client.post(
                    '/api/files/upload',
                    data={'file': (BytesIO(self.valid_pdf_content), 'test.pdf')},
                    headers=headers,
                    content_type='multipart/form-data'
                )
                
                assert response.status_code == 201
                data = response.get_json()
                
                # Verify response schema
                required_fields = ['success', 'message', 'file']
                for field in required_fields:
                    assert field in data
                
                file_fields = [
                    'file_id', 'user_id', 'original_filename', 'sanitized_filename',
                    'file_size', 'file_type', 'storage_type', 'storage_path',
                    'download_url', 'upload_date', 'extracted_text', 'metadata'
                ]
                for field in file_fields:
                    assert field in data['file']