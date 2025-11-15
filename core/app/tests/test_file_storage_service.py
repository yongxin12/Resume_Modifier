"""
Comprehensive test suite for FileStorageService
Following Test-Driven Development approach
"""

import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from werkzeug.datastructures import FileStorage
from app.services.file_storage_service import FileStorageService, StorageError, StorageResult
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class TestFileStorageService:
    """Test suite for FileStorageService class"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Create temporary directory for local storage tests
        self.temp_dir = tempfile.mkdtemp()
        
        # Sample file content for testing
        self.sample_content = b"This is test file content for storage testing"
        self.sample_file = FileStorage(
            stream=BytesIO(self.sample_content),
            filename="test_resume.pdf",
            content_type="application/pdf"
        )

    def teardown_method(self):
        """Clean up after each test"""
        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_local_storage_upload_success(self):
        """Test successful file upload to local storage"""
        config = {
            'storage_type': 'local',
            'local_storage_path': self.temp_dir
        }
        
        storage_service = FileStorageService(config)
        result = storage_service.upload_file(
            file_storage=self.sample_file,
            user_id=123,
            filename="secure_filename.pdf"
        )
        
        assert result.success is True
        assert result.storage_type == 'local'
        assert result.file_path.startswith(self.temp_dir)
        assert result.file_size == len(self.sample_content)
        assert result.url is not None
        assert os.path.exists(result.file_path)
        
        # Verify file content
        with open(result.file_path, 'rb') as f:
            stored_content = f.read()
        assert stored_content == self.sample_content

    def test_local_storage_upload_directory_creation(self):
        """Test that local storage creates user directories automatically"""
        config = {
            'storage_type': 'local',
            'local_storage_path': self.temp_dir
        }
        
        storage_service = FileStorageService(config)
        result = storage_service.upload_file(
            file_storage=self.sample_file,
            user_id=456,
            filename="test_file.pdf"
        )
        
        assert result.success is True
        # Should create user-specific directory
        user_dir = os.path.join(self.temp_dir, 'users', '456')
        assert os.path.exists(user_dir)
        assert result.file_path.startswith(user_dir)

    def test_local_storage_upload_invalid_directory(self):
        """Test local storage upload fails with invalid directory"""
        config = {
            'storage_type': 'local',
            'local_storage_path': '/invalid/nonexistent/path'
        }
        
        storage_service = FileStorageService(config)
        result = storage_service.upload_file(
            file_storage=self.sample_file,
            user_id=123,
            filename="test_file.pdf"
        )
        
        assert result.success is False
        assert 'Failed to create storage directory' in result.error_message

    def test_local_storage_download_success(self):
        """Test successful file download from local storage"""
        config = {
            'storage_type': 'local',
            'local_storage_path': self.temp_dir
        }
        
        storage_service = FileStorageService(config)
        
        # First upload a file
        upload_result = storage_service.upload_file(
            file_storage=self.sample_file,
            user_id=123,
            filename="download_test.pdf"
        )
        
        # Then download it
        download_result = storage_service.download_file(upload_result.file_path)
        
        assert download_result.success is True
        assert download_result.content == self.sample_content
        assert download_result.content_type == "application/pdf"
        assert download_result.filename == "download_test.pdf"

    def test_local_storage_download_file_not_found(self):
        """Test download fails when file doesn't exist"""
        config = {
            'storage_type': 'local',
            'local_storage_path': self.temp_dir
        }
        
        storage_service = FileStorageService(config)
        result = storage_service.download_file('/nonexistent/file.pdf')
        
        assert result.success is False
        assert 'File not found' in result.error_message

    def test_local_storage_delete_success(self):
        """Test successful file deletion from local storage"""
        config = {
            'storage_type': 'local',
            'local_storage_path': self.temp_dir
        }
        
        storage_service = FileStorageService(config)
        
        # First upload a file
        upload_result = storage_service.upload_file(
            file_storage=self.sample_file,
            user_id=123,
            filename="delete_test.pdf"
        )
        
        assert os.path.exists(upload_result.file_path)
        
        # Then delete it
        delete_result = storage_service.delete_file(upload_result.file_path)
        
        assert delete_result.success is True
        assert not os.path.exists(upload_result.file_path)

    def test_local_storage_delete_file_not_found(self):
        """Test delete operation when file doesn't exist"""
        config = {
            'storage_type': 'local',
            'local_storage_path': self.temp_dir
        }
        
        storage_service = FileStorageService(config)
        result = storage_service.delete_file('/nonexistent/file.pdf')
        
        assert result.success is False
        assert 'File not found' in result.error_message

    @patch('boto3.client')
    def test_s3_storage_upload_success(self, mock_boto_client):
        """Test successful file upload to S3"""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.upload_fileobj.return_value = None
        
        config = {
            'storage_type': 's3',
            's3_bucket': 'test-bucket',
            's3_region': 'us-east-1',
            'aws_access_key_id': 'test_key',
            'aws_secret_access_key': 'test_secret'
        }
        
        storage_service = FileStorageService(config)
        result = storage_service.upload_file(
            file_storage=self.sample_file,
            user_id=123,
            filename="s3_test.pdf"
        )
        
        assert result.success is True
        assert result.storage_type == 's3'
        assert result.s3_bucket == 'test-bucket'
        assert result.s3_key.startswith('users/123/')
        assert result.file_size == len(self.sample_content)
        
        # Verify S3 client was called correctly
        mock_s3.upload_fileobj.assert_called_once()

    @patch('boto3.client')
    def test_s3_storage_upload_failure(self, mock_boto_client):
        """Test S3 upload failure handling"""
        # Mock S3 client to raise exception
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.upload_fileobj.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}},
            'upload_fileobj'
        )
        
        config = {
            'storage_type': 's3',
            's3_bucket': 'nonexistent-bucket',
            's3_region': 'us-east-1',
            'aws_access_key_id': 'test_key',
            'aws_secret_access_key': 'test_secret'
        }
        
        storage_service = FileStorageService(config)
        result = storage_service.upload_file(
            file_storage=self.sample_file,
            user_id=123,
            filename="s3_fail_test.pdf"
        )
        
        assert result.success is False
        assert 'S3 upload failed' in result.error_message

    @patch('boto3.client')
    def test_s3_storage_download_success(self, mock_boto_client):
        """Test successful file download from S3"""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        # Mock download response
        mock_response = {
            'Body': BytesIO(self.sample_content),
            'ContentType': 'application/pdf',
            'ContentLength': len(self.sample_content)
        }
        mock_s3.get_object.return_value = mock_response
        
        config = {
            'storage_type': 's3',
            's3_bucket': 'test-bucket',
            's3_region': 'us-east-1',
            'aws_access_key_id': 'test_key',
            'aws_secret_access_key': 'test_secret'
        }
        
        storage_service = FileStorageService(config)
        result = storage_service.download_file('users/123/test_file.pdf')
        
        assert result.success is True
        assert result.content == self.sample_content
        assert result.content_type == 'application/pdf'
        
        # Verify S3 client was called correctly
        mock_s3.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='users/123/test_file.pdf'
        )

    @patch('boto3.client')
    def test_s3_storage_download_not_found(self, mock_boto_client):
        """Test S3 download when file doesn't exist"""
        # Mock S3 client to raise NoSuchKey error
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.get_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
            'get_object'
        )
        
        config = {
            'storage_type': 's3',
            's3_bucket': 'test-bucket',
            's3_region': 'us-east-1',
            'aws_access_key_id': 'test_key',
            'aws_secret_access_key': 'test_secret'
        }
        
        storage_service = FileStorageService(config)
        result = storage_service.download_file('users/123/nonexistent.pdf')
        
        assert result.success is False
        assert 'File not found' in result.error_message

    @patch('boto3.client')
    def test_s3_storage_delete_success(self, mock_boto_client):
        """Test successful file deletion from S3"""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.delete_object.return_value = {}
        
        config = {
            'storage_type': 's3',
            's3_bucket': 'test-bucket',
            's3_region': 'us-east-1',
            'aws_access_key_id': 'test_key',
            'aws_secret_access_key': 'test_secret'
        }
        
        storage_service = FileStorageService(config)
        result = storage_service.delete_file('users/123/delete_test.pdf')
        
        assert result.success is True
        
        # Verify S3 client was called correctly
        mock_s3.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='users/123/delete_test.pdf'
        )

    @patch('boto3.client')
    def test_s3_storage_delete_failure(self, mock_boto_client):
        """Test S3 delete operation failure"""
        # Mock S3 client to raise exception
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.delete_object.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'delete_object'
        )
        
        config = {
            'storage_type': 's3',
            's3_bucket': 'test-bucket',
            's3_region': 'us-east-1',
            'aws_access_key_id': 'test_key',
            'aws_secret_access_key': 'test_secret'
        }
        
        storage_service = FileStorageService(config)
        result = storage_service.delete_file('users/123/test_file.pdf')
        
        assert result.success is False
        assert 'S3 delete failed' in result.error_message

    def test_storage_service_invalid_config(self):
        """Test storage service with invalid configuration"""
        config = {
            'storage_type': 'invalid_type'
        }
        
        with pytest.raises(StorageError):
            FileStorageService(config)

    def test_storage_service_missing_local_config(self):
        """Test storage service with missing local storage configuration"""
        config = {
            'storage_type': 'local'
            # Missing local_storage_path
        }
        
        with pytest.raises(StorageError):
            FileStorageService(config)

    def test_storage_service_missing_s3_config(self):
        """Test storage service with missing S3 configuration"""
        config = {
            'storage_type': 's3'
            # Missing required S3 configuration
        }
        
        with pytest.raises(StorageError):
            FileStorageService(config)

    def test_generate_storage_path_local(self):
        """Test storage path generation for local storage"""
        config = {
            'storage_type': 'local',
            'local_storage_path': self.temp_dir
        }
        
        storage_service = FileStorageService(config)
        path = storage_service._generate_storage_path(123, 'test_file.pdf')
        
        expected_path = os.path.join(self.temp_dir, 'users', '123', 'test_file.pdf')
        assert path == expected_path

    def test_generate_storage_path_s3(self):
        """Test storage path generation for S3"""
        config = {
            'storage_type': 's3',
            's3_bucket': 'test-bucket',
            's3_region': 'us-east-1',
            'aws_access_key_id': 'test_key',
            'aws_secret_access_key': 'test_secret'
        }
        
        storage_service = FileStorageService(config)
        path = storage_service._generate_storage_path(123, 'test_file.pdf')
        
        expected_path = 'users/123/test_file.pdf'
        assert path == expected_path

    def test_get_file_url_local(self):
        """Test URL generation for local files"""
        config = {
            'storage_type': 'local',
            'local_storage_path': self.temp_dir,
            'base_url': 'http://localhost:5001'
        }
        
        storage_service = FileStorageService(config)
        file_path = os.path.join(self.temp_dir, 'users', '123', 'test.pdf')
        url = storage_service._get_file_url(file_path)
        
        assert url.startswith('http://localhost:5001/api/files/')
        assert url.endswith('/download')

    @patch('boto3.client')
    def test_get_file_url_s3(self, mock_boto_client):
        """Test URL generation for S3 files"""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/signed-url'
        
        config = {
            'storage_type': 's3',
            's3_bucket': 'test-bucket',
            's3_region': 'us-east-1',
            'aws_access_key_id': 'test_key',
            'aws_secret_access_key': 'test_secret'
        }
        
        storage_service = FileStorageService(config)
        url = storage_service._get_file_url('users/123/test.pdf')
        
        assert url == 'https://s3.amazonaws.com/signed-url'
        mock_s3.generate_presigned_url.assert_called_once()

    def test_storage_result_class(self):
        """Test StorageResult class functionality"""
        # Test successful result
        result = StorageResult(
            success=True,
            storage_type='local',
            file_path='/test/path.pdf',
            file_size=1024,
            url='http://example.com/file.pdf'
        )
        
        assert result.success is True
        assert result.storage_type == 'local'
        assert result.file_path == '/test/path.pdf'
        assert result.file_size == 1024
        assert result.url == 'http://example.com/file.pdf'
        assert result.error_message is None
        
        # Test failed result
        failed_result = StorageResult(
            success=False,
            error_message='Upload failed'
        )
        
        assert failed_result.success is False
        assert failed_result.error_message == 'Upload failed'

    def test_storage_error_exception(self):
        """Test StorageError exception"""
        with pytest.raises(StorageError) as exc_info:
            raise StorageError("Test storage error")
        
        assert str(exc_info.value) == "Test storage error"

    @patch('boto3.client')
    def test_file_exists_local(self, mock_boto_client):
        """Test file existence check for local storage"""
        config = {
            'storage_type': 'local',
            'local_storage_path': self.temp_dir
        }
        
        storage_service = FileStorageService(config)
        
        # Create a test file
        test_file_path = os.path.join(self.temp_dir, 'test_exists.pdf')
        with open(test_file_path, 'wb') as f:
            f.write(self.sample_content)
        
        # Test existing file
        assert storage_service.file_exists(test_file_path) is True
        
        # Test non-existing file
        assert storage_service.file_exists('/nonexistent/file.pdf') is False

    @patch('boto3.client')
    def test_file_exists_s3(self, mock_boto_client):
        """Test file existence check for S3"""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        config = {
            'storage_type': 's3',
            's3_bucket': 'test-bucket',
            's3_region': 'us-east-1',
            'aws_access_key_id': 'test_key',
            'aws_secret_access_key': 'test_secret'
        }
        
        storage_service = FileStorageService(config)
        
        # Test existing file
        mock_s3.head_object.return_value = {}
        assert storage_service.file_exists('users/123/test.pdf') is True
        
        # Test non-existing file
        mock_s3.head_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
            'head_object'
        )
        assert storage_service.file_exists('users/123/nonexistent.pdf') is False

    def test_get_file_info_local(self):
        """Test getting file information for local storage"""
        config = {
            'storage_type': 'local',
            'local_storage_path': self.temp_dir
        }
        
        storage_service = FileStorageService(config)
        
        # Create a test file
        test_file_path = os.path.join(self.temp_dir, 'test_info.pdf')
        with open(test_file_path, 'wb') as f:
            f.write(self.sample_content)
        
        info = storage_service.get_file_info(test_file_path)
        
        assert info['exists'] is True
        assert info['size'] == len(self.sample_content)
        assert 'modified_time' in info
        assert 'content_type' in info

    @patch('boto3.client')
    def test_get_file_info_s3(self, mock_boto_client):
        """Test getting file information for S3"""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_object.return_value = {
            'ContentLength': len(self.sample_content),
            'ContentType': 'application/pdf',
            'LastModified': '2023-01-01T12:00:00Z'
        }
        
        config = {
            'storage_type': 's3',
            's3_bucket': 'test-bucket',
            's3_region': 'us-east-1',
            'aws_access_key_id': 'test_key',
            'aws_secret_access_key': 'test_secret'
        }
        
        storage_service = FileStorageService(config)
        info = storage_service.get_file_info('users/123/test.pdf')
        
        assert info['exists'] is True
        assert info['size'] == len(self.sample_content)
        assert info['content_type'] == 'application/pdf'
        assert 'modified_time' in info