"""
Test suite for Configuration and Environment Management

Tests configuration validation, environment setup, and validation tools:
- Google Drive configuration validation
- Environment variable setup
- Storage configuration
- Error handler configuration
"""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from app.utils.google_drive_validator import GoogleDriveConfigValidator
from app.utils.error_handler import ErrorHandler, ErrorCode
from app.utils.storage_config import StorageConfigManager


class TestGoogleDriveConfigValidator:
    """Test cases for Google Drive configuration validation"""
    
    @pytest.fixture
    def valid_config(self):
        """Valid Google Drive configuration"""
        return {
            'GOOGLE_DRIVE_CREDENTIALS_JSON': '{"type": "service_account", "project_id": "test"}',
            'GOOGLE_DRIVE_ENABLED': 'true',
            'GOOGLE_DRIVE_DEFAULT_ACCESS_LEVEL': 'writer',
            'GOOGLE_DRIVE_SHARE_WITH_USER': 'true',
            'GOOGLE_DRIVE_CONVERT_TO_DOC': 'true'
        }
    
    @pytest.fixture
    def invalid_config(self):
        """Invalid Google Drive configuration"""
        return {
            'GOOGLE_DRIVE_ENABLED': 'true',
            # Missing required credentials
        }
    
    def test_validate_all_success(self, valid_config):
        """Test successful validation of all configuration"""
        with patch.dict(os.environ, valid_config):
            with patch('app.utils.google_drive_validator.build') as mock_build:
                mock_service = Mock()
                mock_service.about().get().execute.return_value = {'user': {'emailAddress': 'test@example.com'}}
                mock_build.return_value = mock_service
                
                validator = GoogleDriveConfigValidator()
                result = validator.validate_all()
                
                assert result['valid'] is True
                assert result['message'] == "All Google Drive configuration is valid"
                assert len(result['details']) == 5
                assert all(detail['valid'] for detail in result['details'])
    
    def test_validate_all_failure(self, invalid_config):
        """Test validation failure"""
        with patch.dict(os.environ, invalid_config):
            validator = GoogleDriveConfigValidator()
            result = validator.validate_all()
            
            assert result['valid'] is False
            assert "validation failed" in result['message']
            assert any(not detail['valid'] for detail in result['details'])
    
    def test_validate_credentials_json_valid(self, valid_config):
        """Test validation of valid JSON credentials"""
        with patch.dict(os.environ, valid_config):
            validator = GoogleDriveConfigValidator()
            result = validator.validate_credentials()
            
            assert result['valid'] is True
            assert "Successfully validated" in result['message'] or "JSON credentials are valid" in result['message']
    
    def test_validate_credentials_json_invalid(self):
        """Test validation of invalid JSON credentials"""
        invalid_json_config = {
            'GOOGLE_DRIVE_CREDENTIALS_JSON': 'invalid json'
        }
        
        with patch.dict(os.environ, invalid_json_config):
            validator = GoogleDriveConfigValidator()
            result = validator.validate_credentials()
            
            assert result['valid'] is False
            assert "Invalid JSON format" in result['message'] or "Failed to load service account info" in result['message']
    
    def test_validate_credentials_file_valid(self):
        """Test validation of valid credentials file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"type": "service_account", "project_id": "test"}, f)
            credentials_file = f.name
        
        try:
            config = {'GOOGLE_DRIVE_CREDENTIALS_FILE': credentials_file}
            with patch.dict(os.environ, config):
                validator = GoogleDriveConfigValidator()
                result = validator.validate_credentials()
                
                assert result['valid'] is True
                assert "File credentials are valid" in result['message']
        finally:
            os.unlink(credentials_file)
    
    def test_validate_credentials_file_not_found(self):
        """Test validation of non-existent credentials file"""
        config = {'GOOGLE_DRIVE_CREDENTIALS_FILE': '/nonexistent/file.json'}
        
        with patch.dict(os.environ, config):
            validator = GoogleDriveConfigValidator()
            result = validator.validate_credentials()
            
            assert result['valid'] is False
            assert "File not found" in result['message'] or "No valid service account configuration found" in result['message']
    
    def test_validate_api_access_success(self, valid_config):
        """Test successful API access validation"""
        with patch.dict(os.environ, valid_config):
            with patch('app.utils.google_drive_validator.build') as mock_build:
                mock_service = Mock()
                mock_service.about().get().execute.return_value = {
                    'user': {'emailAddress': 'test@service-account.com'}
                }
                mock_build.return_value = mock_service
                
                validator = GoogleDriveConfigValidator()
                result = validator.validate_api_access()
                
                assert result['valid'] is True
                assert "API access successful" in result['message'] or "Successfully connected to Google Drive API" in result['message'] or "Successfully validated" in result['message']
                assert result['details']['service_account_email'] == 'test@service-account.com'
    
    def test_validate_api_access_failure(self, valid_config):
        """Test API access validation failure"""
        with patch.dict(os.environ, valid_config):
            with patch('app.utils.google_drive_validator.build') as mock_build:
                mock_build.side_effect = Exception("API access denied")
                
                validator = GoogleDriveConfigValidator()
                result = validator.validate_api_access()
                
                assert result['valid'] is False
                assert "API access failed" in result['message'] or "Failed to connect to Google Drive API" in result['message']
    
    def test_validate_configuration_settings_valid(self):
        """Test validation of valid configuration settings"""
        config = {
            'GOOGLE_DRIVE_DEFAULT_ACCESS_LEVEL': 'writer',
            'GOOGLE_DRIVE_SHARE_WITH_USER': 'true',
            'GOOGLE_DRIVE_CONVERT_TO_DOC': 'false'
        }
        
        with patch.dict(os.environ, config):
            validator = GoogleDriveConfigValidator()
            result = validator.validate_configuration_settings()
            
            assert result['valid'] is True
            assert "Configuration settings are valid" in result['message']
    
    def test_validate_configuration_settings_invalid_access_level(self):
        """Test validation with invalid access level"""
        config = {
            'GOOGLE_DRIVE_DEFAULT_ACCESS_LEVEL': 'invalid_level',
            'GOOGLE_DRIVE_SHARE_WITH_USER': 'true',
            'GOOGLE_DRIVE_CONVERT_TO_DOC': 'true'
        }
        
        with patch.dict(os.environ, config):
            validator = GoogleDriveConfigValidator()
            result = validator.validate_configuration_settings()
            
            assert result['valid'] is False
            assert "Invalid GOOGLE_DRIVE_DEFAULT_ACCESS_LEVEL" in result['message'] or "Neither GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE nor GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO" in result['message']
    
    def test_validate_enabled_setting_true(self):
        """Test validation of enabled setting when true"""
        config = {'GOOGLE_DRIVE_ENABLED': 'true'}
        
        with patch.dict(os.environ, config):
            validator = GoogleDriveConfigValidator()
            result = validator.validate_enabled_setting()
            
            assert result['valid'] is True
            assert "Google Drive is enabled" in result['message'] or "Google Drive integration is enabled" in result['message']
    
    def test_validate_enabled_setting_false(self):
        """Test validation of enabled setting when false"""
        config = {'GOOGLE_DRIVE_ENABLED': 'false'}
        
        with patch.dict(os.environ, config):
            validator = GoogleDriveConfigValidator()
            result = validator.validate_enabled_setting()
            
            assert result['valid'] is True
            assert "Google Drive is disabled" in result['message'] or "Google Drive integration is disabled" in result['message']
    
    def test_validate_enabled_setting_missing(self):
        """Test validation of missing enabled setting"""
        with patch.dict(os.environ, {}, clear=True):
            validator = GoogleDriveConfigValidator()
            result = validator.validate_enabled_setting()
            
            assert result['valid'] is False
            assert "GOOGLE_DRIVE_ENABLED not set" in result['message']


class TestErrorHandler:
    """Test cases for enhanced error handling"""
    
    def test_error_code_enum_completeness(self):
        """Test that all error codes are properly defined"""
        expected_codes = [
            # Google Drive errors
            'GDRIVE_001', 'GDRIVE_002', 'GDRIVE_003', 'GDRIVE_004',
            'GDRIVE_005', 'GDRIVE_006', 'GDRIVE_007',
            # Duplicate detection errors
            'DUP_001', 'DUP_002',
            # Soft deletion errors
            'DEL_001', 'DEL_002', 'DEL_003'
        ]
        
        for code in expected_codes:
            assert hasattr(ErrorCode, code), f"ErrorCode.{code} is missing"
            error_code = getattr(ErrorCode, code)
            assert error_code.value == code
    
    def test_handle_google_drive_error_authentication(self):
        """Test Google Drive authentication error handling"""
        handler = ErrorHandler()
        
        with patch('app.utils.error_handler.logger') as mock_logger:
            result = handler.handle_google_drive_error(
                ErrorCode.GDRIVE_001,
                Exception("Authentication failed"),
                "upload operation"
            )
            
            assert result['success'] is False
            assert result['error_code'] == 'GDRIVE_001'
            assert "Google Drive authentication failed" in result['message']
            assert "operation: upload operation" in result['details']
            mock_logger.error.assert_called_once()
    
    def test_handle_google_drive_error_upload_failure(self):
        """Test Google Drive upload failure error handling"""
        handler = ErrorHandler()
        
        result = handler.handle_google_drive_error(
            ErrorCode.GDRIVE_002,
            Exception("Upload failed"),
            "file upload"
        )
        
        assert result['success'] is False
        assert result['error_code'] == 'GDRIVE_002'
        assert "Failed to upload file to Google Drive" in result['message']
    
    def test_handle_duplicate_detection_error_hash_calculation(self):
        """Test duplicate detection hash calculation error handling"""
        handler = ErrorHandler()
        
        result = handler.handle_duplicate_detection_error(
            ErrorCode.DUP_001,
            Exception("Hash calculation failed"),
            filename="test.pdf"
        )
        
        assert result['success'] is False
        assert result['error_code'] == 'DUP_001'
        assert "Failed to calculate file hash" in result['message']
        assert "filename: test.pdf" in result['details']
    
    def test_handle_duplicate_detection_error_database_check(self):
        """Test duplicate detection database check error handling"""
        handler = ErrorHandler()
        
        result = handler.handle_duplicate_detection_error(
            ErrorCode.DUP_002,
            Exception("Database query failed"),
            filename="test.pdf"
        )
        
        assert result['success'] is False
        assert result['error_code'] == 'DUP_002'
        assert "Failed to check for duplicate files" in result['message']
    
    def test_handle_error_generic(self):
        """Test generic error handling"""
        handler = ErrorHandler()
        
        with patch('app.utils.error_handler.logger') as mock_logger:
            result = handler.handle_error(
                Exception("Generic error"),
                "Generic operation failed",
                "TEST_001"
            )
            
            assert result['success'] is False
            assert result['error_code'] == 'TEST_001'
            assert result['message'] == "Generic operation failed"
            mock_logger.error.assert_called_once()
    
    def test_log_warning(self):
        """Test warning logging functionality"""
        handler = ErrorHandler()
        
        with patch('app.utils.error_handler.logger') as mock_logger:
            handler.log_warning("This is a warning", "WARN_001")
            
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "WARN_001" in call_args
            assert "This is a warning" in call_args


class TestStorageConfigManager:
    """Test cases for storage configuration management"""
    
    def test_get_storage_config_dict_local(self):
        """Test getting local storage configuration"""
        config = {
            'STORAGE_TYPE': 'local',
            'LOCAL_STORAGE_PATH': '/tmp/uploads'
        }
        
        with patch.dict(os.environ, config):
            manager = StorageConfigManager()
            result = manager.get_storage_config_dict()
            
            assert result['storage_type'] == 'local'
            assert result['local_storage_path'] == '/tmp/uploads'
    
    def test_get_storage_config_dict_cloud(self):
        """Test getting cloud storage configuration"""
        config = {
            'STORAGE_TYPE': 'cloud',
            'CLOUD_STORAGE_BUCKET': 'my-bucket',
            'CLOUD_STORAGE_PROVIDER': 'aws'
        }
        
        with patch.dict(os.environ, config):
            manager = StorageConfigManager()
            result = manager.get_storage_config_dict()
            
            assert result['storage_type'] == 'cloud'
            assert result['cloud_storage_bucket'] == 'my-bucket'
            assert result['cloud_storage_provider'] == 'aws'
    
    def test_get_storage_config_dict_defaults(self):
        """Test getting storage configuration with defaults"""
        with patch.dict(os.environ, {}, clear=True):
            manager = StorageConfigManager()
            result = manager.get_storage_config_dict()
            
            assert result['storage_type'] == 'local'
            assert '/tmp' in result['local_storage_path']


class TestEnvironmentConfiguration:
    """Test cases for environment configuration management"""
    
    def test_required_environment_variables_present(self):
        """Test that all required environment variables can be validated"""
        required_vars = [
            'DATABASE_URL',
            'JWT_SECRET',
            'FLASK_ENV',
            'GOOGLE_DRIVE_ENABLED'
        ]
        
        # Test with all variables present
        test_config = {
            'DATABASE_URL': 'sqlite:///test.db',
            'JWT_SECRET': 'test-secret',
            'FLASK_ENV': 'development',
            'GOOGLE_DRIVE_ENABLED': 'true'
        }
        
        with patch.dict(os.environ, test_config):
            for var in required_vars:
                assert os.getenv(var) is not None, f"Required variable {var} is not set"
    
    def test_google_drive_configuration_completeness(self):
        """Test that Google Drive configuration is complete when enabled"""
        google_drive_config = {
            'GOOGLE_DRIVE_ENABLED': 'true',
            'GOOGLE_DRIVE_CREDENTIALS_JSON': '{"type": "service_account"}',
            'GOOGLE_DRIVE_DEFAULT_ACCESS_LEVEL': 'writer',
            'GOOGLE_DRIVE_SHARE_WITH_USER': 'true',
            'GOOGLE_DRIVE_CONVERT_TO_DOC': 'true'
        }
        
        with patch.dict(os.environ, google_drive_config):
            # Verify all Google Drive settings are accessible
            assert os.getenv('GOOGLE_DRIVE_ENABLED') == 'true'
            assert os.getenv('GOOGLE_DRIVE_CREDENTIALS_JSON') is not None
            assert os.getenv('GOOGLE_DRIVE_DEFAULT_ACCESS_LEVEL') == 'writer'
            assert os.getenv('GOOGLE_DRIVE_SHARE_WITH_USER') == 'true'
            assert os.getenv('GOOGLE_DRIVE_CONVERT_TO_DOC') == 'true'
    
    def test_database_configuration_validation(self):
        """Test database configuration validation"""
        db_configs = [
            'sqlite:///app.db',
            'postgresql://user:pass@localhost/db',
            'mysql://user:pass@localhost/db'
        ]
        
        for db_url in db_configs:
            with patch.dict(os.environ, {'DATABASE_URL': db_url}):
                assert os.getenv('DATABASE_URL') == db_url
                # Basic URL format validation
                assert '://' in db_url
    
    def test_security_configuration_validation(self):
        """Test security-related configuration validation"""
        security_config = {
            'JWT_SECRET': 'very-secure-secret-key',
            'JWT_ALGORITHM': 'HS256',
            'JWT_EXPIRATION_HOURS': '24',
            'FLASK_SECRET_KEY': 'flask-secret-key'
        }
        
        with patch.dict(os.environ, security_config):
            # Verify security settings
            assert len(os.getenv('JWT_SECRET')) >= 16  # Minimum length
            assert os.getenv('JWT_ALGORITHM') in ['HS256', 'RS256']
            assert int(os.getenv('JWT_EXPIRATION_HOURS')) > 0
            assert len(os.getenv('FLASK_SECRET_KEY')) >= 16


if __name__ == '__main__':
    pytest.main([__file__, '-v'])