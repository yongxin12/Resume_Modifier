"""
Test Configuration Management for File Services
Tests the centralized storage configuration manager

Author: Resume Modifier Backend Team
Date: October 2024
"""

import os
import pytest
from unittest.mock import patch, Mock
from app.utils.storage_config import StorageConfigManager, StorageConfiguration


class TestStorageConfigManager:
    """Test cases for StorageConfigManager"""
    
    def test_local_storage_config_valid(self):
        """Test valid local storage configuration"""
        with patch.dict(os.environ, {
            'FILE_STORAGE_TYPE': 'local',
            'LOCAL_STORAGE_PATH': '/tmp/test_files',
            'BASE_URL': 'http://localhost:5001'
        }):
            config = StorageConfigManager.get_storage_config()
            
            assert config.storage_type == 'local'
            assert config.local_storage_path == '/tmp/test_files'
            assert config.base_url == 'http://localhost:5001'
    
    def test_s3_storage_config_valid(self):
        """Test valid S3 storage configuration"""
        with patch.dict(os.environ, {
            'FILE_STORAGE_TYPE': 's3',
            'AWS_S3_BUCKET': 'test-bucket',
            'AWS_S3_REGION': 'us-west-2',
            'AWS_ACCESS_KEY_ID': 'test-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret'
        }):
            config = StorageConfigManager.get_storage_config()
            
            assert config.storage_type == 's3'
            assert config.s3_bucket == 'test-bucket'
            assert config.s3_region == 'us-west-2'
            assert config.aws_access_key_id == 'test-key'
            assert config.aws_secret_access_key == 'test-secret'
    
    def test_invalid_storage_type(self):
        """Test invalid storage type raises ValueError"""
        with patch.dict(os.environ, {
            'FILE_STORAGE_TYPE': 'invalid',
        }):
            with pytest.raises(ValueError, match="Invalid storage type"):
                StorageConfigManager.get_storage_config()
    
    def test_missing_s3_config(self):
        """Test missing S3 configuration raises ValueError"""
        with patch.dict(os.environ, {
            'FILE_STORAGE_TYPE': 's3',
            'AWS_S3_BUCKET': 'test-bucket',
            # Missing AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
        }, clear=True):
            with pytest.raises(ValueError, match="Missing required S3 configuration"):
                StorageConfigManager.get_storage_config()
    
    def test_config_to_dict(self):
        """Test configuration conversion to dictionary"""
        with patch.dict(os.environ, {
            'FILE_STORAGE_TYPE': 'local',
            'LOCAL_STORAGE_PATH': '/tmp/test_files',
            'BASE_URL': 'http://localhost:5001'
        }):
            config_dict = StorageConfigManager.get_storage_config_dict()
            
            expected_keys = [
                'storage_type', 'local_storage_path', 'base_url',
                's3_bucket', 's3_region', 'aws_access_key_id', 'aws_secret_access_key'
            ]
            
            for key in expected_keys:
                assert key in config_dict
            
            assert config_dict['storage_type'] == 'local'
            assert config_dict['local_storage_path'] == '/tmp/test_files'
    
    def test_validate_storage_config_valid(self):
        """Test storage configuration validation - valid config"""
        with patch.dict(os.environ, {
            'FILE_STORAGE_TYPE': 'local',
            'LOCAL_STORAGE_PATH': '/tmp/test_files'
        }):
            assert StorageConfigManager.validate_storage_config() is True
    
    def test_validate_storage_config_invalid(self):
        """Test storage configuration validation - invalid config"""
        with patch.dict(os.environ, {
            'FILE_STORAGE_TYPE': 'invalid'
        }):
            assert StorageConfigManager.validate_storage_config() is False
    
    def test_upload_limits_config(self):
        """Test upload limits configuration"""
        with patch.dict(os.environ, {
            'MAX_FILE_SIZE': '20971520',  # 20MB
            'ALLOWED_MIME_TYPES': 'application/pdf,text/plain',
            'MAX_FILES_PER_USER': '50',
            'UPLOAD_TIMEOUT_SECONDS': '600'
        }):
            limits = StorageConfigManager.get_upload_limits()
            
            assert limits['max_file_size'] == 20971520
            assert limits['allowed_mime_types'] == ['application/pdf', 'text/plain']
            assert limits['max_files_per_user'] == 50
            assert limits['upload_timeout'] == 600
    
    def test_upload_limits_defaults(self):
        """Test upload limits with default values"""
        with patch.dict(os.environ, {}, clear=True):
            limits = StorageConfigManager.get_upload_limits()
            
            assert limits['max_file_size'] == 10485760  # 10MB default
            assert 'application/pdf' in limits['allowed_mime_types']
            assert limits['max_files_per_user'] == 100
            assert limits['upload_timeout'] == 300
    
    def test_processing_config(self):
        """Test processing configuration"""
        with patch.dict(os.environ, {
            'MAX_EXTRACTED_TEXT_LENGTH': '50000',
            'PROCESSING_TIMEOUT_SECONDS': '120',
            'ENABLE_OCR': 'true',
            'ENABLE_LANGUAGE_DETECTION': 'false'
        }):
            processing_config = StorageConfigManager.get_processing_config()
            
            assert processing_config['max_text_length'] == 50000
            assert processing_config['processing_timeout'] == 120
            assert processing_config['enable_ocr'] is True
            assert processing_config['enable_language_detection'] is False
    
    def test_processing_config_defaults(self):
        """Test processing configuration with defaults"""
        with patch.dict(os.environ, {}, clear=True):
            processing_config = StorageConfigManager.get_processing_config()
            
            assert processing_config['max_text_length'] == 100000
            assert processing_config['processing_timeout'] == 60
            assert processing_config['enable_ocr'] is False
            assert processing_config['enable_language_detection'] is True


class TestStorageConfiguration:
    """Test cases for StorageConfiguration data class"""
    
    def test_storage_configuration_creation(self):
        """Test creating StorageConfiguration instance"""
        config = StorageConfiguration(
            storage_type='local',
            local_storage_path='/tmp/files',
            base_url='http://localhost:5001',
            s3_bucket='',
            s3_region='us-east-1',
            aws_access_key_id='',
            aws_secret_access_key=''
        )
        
        assert config.storage_type == 'local'
        assert config.local_storage_path == '/tmp/files'
    
    def test_storage_configuration_to_dict(self):
        """Test converting StorageConfiguration to dictionary"""
        config = StorageConfiguration(
            storage_type='s3',
            local_storage_path='',
            base_url='',
            s3_bucket='test-bucket',
            s3_region='us-west-2',
            aws_access_key_id='test-key',
            aws_secret_access_key='test-secret'
        )
        
        config_dict = config.to_dict()
        
        assert config_dict['storage_type'] == 's3'
        assert config_dict['s3_bucket'] == 'test-bucket'
        assert config_dict['aws_access_key_id'] == 'test-key'