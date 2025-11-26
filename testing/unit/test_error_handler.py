"""
Test Error Handling Utilities
Tests the centralized error handling system

Author: Resume Modifier Backend Team
Date: October 2024
"""

import pytest
from unittest.mock import Mock, patch
from app.utils.error_handler import (
    ErrorHandler, ErrorCode, ErrorDetail, FileManagementError,
    handle_file_management_errors
)


class TestErrorHandler:
    """Test cases for ErrorHandler"""
    
    def test_create_error_response_basic(self, app):
        """Test basic error response creation"""
        with app.app_context():
            handler = ErrorHandler()
            response, status_code = handler.create_error_response(ErrorCode.FILE_NOT_PROVIDED)
            
            assert status_code == 400
            response_data = response.get_json()
            assert response_data['success'] is False
            assert response_data['error_code'] == 'FILE_001'
            assert 'Please select a file' in response_data['message']
            assert 'timestamp' in response_data
    
    def test_create_error_response_with_context(self, app):
        """Test error response with context formatting"""
        with app.app_context():
            handler = ErrorHandler()
            context = {'max_size': 10}
            response, status_code = handler.create_error_response(
                ErrorCode.FILE_SIZE_EXCEEDED, 
                context=context
            )
            
            assert status_code == 400
            response_data = response.get_json()
            assert '10MB' in response_data['message']
    
    def test_create_error_response_custom_message(self, app):
        """Test error response with custom message"""
        with app.app_context():
            handler = ErrorHandler()
            custom_message = "Custom error message for user"
            response, status_code = handler.create_error_response(
                ErrorCode.FILE_NOT_PROVIDED,
                custom_message=custom_message
            )
            
            response_data = response.get_json()
            assert response_data['message'] == custom_message
    
    def test_handle_exception(self, app):
        """Test exception handling with logging"""
        with app.app_context():
            handler = ErrorHandler()
            test_exception = ValueError("Test error")
            
            with patch.object(handler.logger, 'error') as mock_logger:
                response, status_code = handler.handle_exception(
                    test_exception, 
                    ErrorCode.INVALID_REQUEST
                )
                
                assert status_code == 400
                # Should be called twice: once for exception, once for error response
                assert mock_logger.call_count == 2
                
                response_data = response.get_json()
                assert response_data['success'] is False
                assert 'ValueError' in str(mock_logger.call_args_list)
    
    def test_error_code_definitions(self):
        """Test that all error codes have proper definitions"""
        handler = ErrorHandler()
        
        # Test a few key error codes
        auth_error = handler.ERROR_DEFINITIONS[ErrorCode.AUTH_MISSING]
        assert auth_error.http_status == 401
        assert 'log in' in auth_error.user_message.lower()
        
        file_error = handler.ERROR_DEFINITIONS[ErrorCode.FILE_TYPE_INVALID]
        assert file_error.http_status == 400
        assert 'pdf' in file_error.user_message.lower()
        
        storage_error = handler.ERROR_DEFINITIONS[ErrorCode.STORAGE_CONFIG_ERROR]
        assert storage_error.http_status == 500
        assert storage_error.log_level == "CRITICAL"


class TestFileManagementError:
    """Test cases for FileManagementError exception"""
    
    def test_file_management_error_creation(self):
        """Test creating FileManagementError"""
        error_detail = ErrorDetail(
            code=ErrorCode.FILE_NOT_PROVIDED,
            message="Test message",
            user_message="Test user message",
            http_status=400
        )
        
        error = FileManagementError(error_detail)
        assert error.error_detail.code == ErrorCode.FILE_NOT_PROVIDED
        assert str(error) == "Test message"
    
    def test_file_management_error_with_original_exception(self):
        """Test FileManagementError with original exception"""
        original = ValueError("Original error")
        error_detail = ErrorDetail(
            code=ErrorCode.PROCESSING_FAILED,
            message="Processing failed",
            user_message="Cannot process file",
            http_status=500
        )
        
        error = FileManagementError(error_detail, original)
        assert error.original_exception == original


class TestErrorHandlerDecorator:
    """Test cases for error handler decorator"""
    
    def test_decorator_normal_execution(self):
        """Test decorator with normal function execution"""
        @handle_file_management_errors
        def test_function():
            return {"success": True}, 200
        
        result = test_function()
        assert result == ({"success": True}, 200)
    
    def test_decorator_file_management_error(self, app):
        """Test decorator handling FileManagementError"""
        with app.app_context():
            error_detail = ErrorDetail(
                code=ErrorCode.FILE_NOT_PROVIDED,
                message="Test error",
                user_message="Test user error",
                http_status=400
            )
            
            @handle_file_management_errors
            def test_function():
                raise FileManagementError(error_detail)
            
            response, status_code = test_function()
            assert status_code == 400
            
            response_data = response.get_json()
            assert response_data['success'] is False
            assert response_data['error_code'] == 'FILE_001'
    
    def test_decorator_value_error_storage(self):
        """Test decorator handling ValueError with storage configuration"""
        @handle_file_management_errors
        def test_function():
            raise ValueError("Storage configuration error")
        
        with patch('app.utils.error_handler.ErrorHandler.handle_exception') as mock_handle:
            mock_handle.return_value = (Mock(), 500)
            test_function()
            mock_handle.assert_called_once()
            args, kwargs = mock_handle.call_args
            assert args[1] == ErrorCode.STORAGE_CONFIG_ERROR
    
    def test_decorator_file_not_found_error(self):
        """Test decorator handling FileNotFoundError"""
        @handle_file_management_errors
        def test_function():
            raise FileNotFoundError("File not found")
        
        with patch('app.utils.error_handler.ErrorHandler.handle_exception') as mock_handle:
            mock_handle.return_value = (Mock(), 404)
            test_function()
            mock_handle.assert_called_once()
            args, kwargs = mock_handle.call_args
            assert args[1] == ErrorCode.RECORD_NOT_FOUND
    
    def test_decorator_permission_error(self):
        """Test decorator handling PermissionError"""
        @handle_file_management_errors
        def test_function():
            raise PermissionError("Access denied")
        
        with patch('app.utils.error_handler.ErrorHandler.handle_exception') as mock_handle:
            mock_handle.return_value = (Mock(), 403)
            test_function()
            mock_handle.assert_called_once()
            args, kwargs = mock_handle.call_args
            assert args[1] == ErrorCode.ACCESS_DENIED
    
    def test_decorator_timeout_error(self):
        """Test decorator handling TimeoutError"""
        @handle_file_management_errors
        def test_function():
            raise TimeoutError("Operation timed out")
        
        with patch('app.utils.error_handler.ErrorHandler.handle_exception') as mock_handle:
            mock_handle.return_value = (Mock(), 408)
            test_function()
            mock_handle.assert_called_once()
            args, kwargs = mock_handle.call_args
            assert args[1] == ErrorCode.PROCESSING_TIMEOUT
    
    def test_decorator_generic_exception(self):
        """Test decorator handling generic Exception"""
        @handle_file_management_errors
        def test_function():
            raise Exception("Generic error")
        
        with patch('app.utils.error_handler.ErrorHandler.handle_exception') as mock_handle:
            mock_handle.return_value = (Mock(), 500)
            test_function()
            mock_handle.assert_called_once()
            args, kwargs = mock_handle.call_args
            assert args[1] == ErrorCode.INTERNAL_ERROR


class TestErrorCode:
    """Test ErrorCode enum"""
    
    def test_error_code_values(self):
        """Test error code enum values"""
        assert ErrorCode.AUTH_MISSING.value == "AUTH_001"
        assert ErrorCode.FILE_NOT_PROVIDED.value == "FILE_001"
        assert ErrorCode.STORAGE_CONFIG_ERROR.value == "STORAGE_001"
        assert ErrorCode.PROCESSING_FAILED.value == "PROCESS_001"
        assert ErrorCode.DATABASE_ERROR.value == "DB_001"
        assert ErrorCode.INTERNAL_ERROR.value == "GEN_002"