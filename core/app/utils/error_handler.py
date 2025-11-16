"""
Error Handling Utilities for File Management System
Provides centralized error handling, logging, and user-friendly error messages

Author: Resume Modifier Backend Team
Date: October 2024
"""

import logging
import traceback
from typing import Dict, Any, Optional, Tuple, List
from flask import jsonify, Response
from functools import wraps
from dataclasses import dataclass
from enum import Enum

# Module-level logger
logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standardized error codes for file management operations"""
    
    # Authentication & Authorization
    AUTH_MISSING = "AUTH_001"
    AUTH_INVALID = "AUTH_002"
    AUTH_EXPIRED = "AUTH_003"
    ACCESS_DENIED = "AUTH_004"
    
    # File Validation
    FILE_NOT_PROVIDED = "FILE_001"
    FILE_SIZE_EXCEEDED = "FILE_002"
    FILE_TYPE_INVALID = "FILE_003"
    FILE_FORMAT_INVALID = "FILE_004"
    FILE_CORRUPTED = "FILE_005"
    FILENAME_INVALID = "FILE_006"
    
    # Storage
    STORAGE_CONFIG_ERROR = "STORAGE_001"
    STORAGE_UPLOAD_FAILED = "STORAGE_002"
    STORAGE_DOWNLOAD_FAILED = "STORAGE_003"
    STORAGE_DELETE_FAILED = "STORAGE_004"
    STORAGE_SPACE_FULL = "STORAGE_005"
    
    # Processing
    PROCESSING_FAILED = "PROCESS_001"
    PROCESSING_TIMEOUT = "PROCESS_002"
    PROCESSING_UNSUPPORTED_FORMAT = "PROCESS_003"
    TEXT_EXTRACTION_FAILED = "PROCESS_004"
    
    # Database
    DATABASE_ERROR = "DB_001"
    RECORD_NOT_FOUND = "DB_002"
    RECORD_ALREADY_EXISTS = "DB_003"
    DATABASE_CONNECTION_ERROR = "DB_004"
    
    # Google Drive Integration
    GOOGLE_DRIVE_CONFIG_ERROR = "GDRIVE_001"
    GOOGLE_DRIVE_AUTH_FAILED = "GDRIVE_002"
    GOOGLE_DRIVE_QUOTA_EXCEEDED = "GDRIVE_003"
    GOOGLE_DRIVE_UPLOAD_FAILED = "GDRIVE_004"
    GOOGLE_DRIVE_SHARING_FAILED = "GDRIVE_005"
    GOOGLE_DRIVE_CONVERSION_FAILED = "GDRIVE_006"
    GOOGLE_DRIVE_SERVICE_UNAVAILABLE = "GDRIVE_007"
    
    # Duplicate Detection
    DUPLICATE_DETECTION_FAILED = "DUP_001"
    DUPLICATE_HASH_COLLISION = "DUP_002"
    
    # Soft Deletion
    FILE_ALREADY_DELETED = "DEL_001"
    FILE_NOT_DELETED = "DEL_002"
    RESTORE_FAILED = "DEL_003"
    
    # General
    INVALID_REQUEST = "GEN_001"
    INTERNAL_ERROR = "GEN_002"
    RATE_LIMIT_EXCEEDED = "GEN_003"
    SERVICE_UNAVAILABLE = "GEN_004"
    
    # Aliases for backward compatibility and test consistency
    GDRIVE_001 = "GDRIVE_001"  # Same as GOOGLE_DRIVE_CONFIG_ERROR
    GDRIVE_002 = "GDRIVE_002"  # Same as GOOGLE_DRIVE_AUTH_FAILED
    GDRIVE_003 = "GDRIVE_003"  # Same as GOOGLE_DRIVE_QUOTA_EXCEEDED
    GDRIVE_004 = "GDRIVE_004"  # Same as GOOGLE_DRIVE_UPLOAD_FAILED
    GDRIVE_005 = "GDRIVE_005"  # Same as GOOGLE_DRIVE_SHARING_FAILED
    GDRIVE_006 = "GDRIVE_006"  # Same as GOOGLE_DRIVE_CONVERSION_FAILED
    GDRIVE_007 = "GDRIVE_007"  # Same as GOOGLE_DRIVE_SERVICE_UNAVAILABLE
    DUP_001 = "DUP_001"  # Same as DUPLICATE_DETECTION_FAILED
    DUP_002 = "DUP_002"  # Same as DUPLICATE_HASH_COLLISION
    DEL_001 = "DEL_001"  # Same as FILE_ALREADY_DELETED
    DEL_002 = "DEL_002"  # Same as FILE_NOT_DELETED
    DEL_003 = "DEL_003"  # Same as RESTORE_FAILED


@dataclass
class ErrorDetail:
    """Detailed error information"""
    code: ErrorCode
    message: str
    user_message: str
    http_status: int
    log_level: str = "ERROR"
    context: Optional[Dict[str, Any]] = None


class FileManagementError(Exception):
    """Custom exception for file management operations"""
    
    def __init__(self, error_detail: ErrorDetail, original_exception: Optional[Exception] = None):
        self.error_detail = error_detail
        self.original_exception = original_exception
        super().__init__(error_detail.message)


class ErrorHandler:
    """Centralized error handling and logging"""
    
    # Error message mappings
    ERROR_DEFINITIONS = {
        ErrorCode.AUTH_MISSING: ErrorDetail(
            code=ErrorCode.AUTH_MISSING,
            message="Authentication token is missing",
            user_message="Please log in to access this feature",
            http_status=401
        ),
        ErrorCode.AUTH_INVALID: ErrorDetail(
            code=ErrorCode.AUTH_INVALID,
            message="Authentication token is invalid",
            user_message="Please log in again to continue",
            http_status=401
        ),
        ErrorCode.AUTH_EXPIRED: ErrorDetail(
            code=ErrorCode.AUTH_EXPIRED,
            message="Authentication token has expired",
            user_message="Your session has expired. Please log in again",
            http_status=401
        ),
        ErrorCode.ACCESS_DENIED: ErrorDetail(
            code=ErrorCode.ACCESS_DENIED,
            message="Access denied to requested resource",
            user_message="You don't have permission to access this file",
            http_status=403
        ),
        ErrorCode.FILE_NOT_PROVIDED: ErrorDetail(
            code=ErrorCode.FILE_NOT_PROVIDED,
            message="No file provided in request",
            user_message="Please select a file to upload",
            http_status=400
        ),
        ErrorCode.FILE_SIZE_EXCEEDED: ErrorDetail(
            code=ErrorCode.FILE_SIZE_EXCEEDED,
            message="File size exceeds maximum allowed size",
            user_message="File is too large. Please upload a file smaller than {max_size}MB",
            http_status=400
        ),
        ErrorCode.FILE_TYPE_INVALID: ErrorDetail(
            code=ErrorCode.FILE_TYPE_INVALID,
            message="File type not supported",
            user_message="Please upload a PDF or Word document (.pdf, .docx)",
            http_status=400
        ),
        ErrorCode.FILE_FORMAT_INVALID: ErrorDetail(
            code=ErrorCode.FILE_FORMAT_INVALID,
            message="File format validation failed",
            user_message="The file appears to be corrupted or has an invalid format",
            http_status=400
        ),
        ErrorCode.STORAGE_CONFIG_ERROR: ErrorDetail(
            code=ErrorCode.STORAGE_CONFIG_ERROR,
            message="Storage configuration error",
            user_message="There's a temporary issue with file storage. Please try again later",
            http_status=500,
            log_level="CRITICAL"
        ),
        ErrorCode.STORAGE_UPLOAD_FAILED: ErrorDetail(
            code=ErrorCode.STORAGE_UPLOAD_FAILED,
            message="File upload to storage failed",
            user_message="Failed to save your file. Please try uploading again",
            http_status=500
        ),
        ErrorCode.PROCESSING_FAILED: ErrorDetail(
            code=ErrorCode.PROCESSING_FAILED,
            message="File processing failed",
            user_message="Unable to process your file. The file may be corrupted or password-protected",
            http_status=500
        ),
        ErrorCode.PROCESSING_TIMEOUT: ErrorDetail(
            code=ErrorCode.PROCESSING_TIMEOUT,
            message="File processing timed out",
            user_message="Your file is taking too long to process. Please try with a smaller file",
            http_status=408
        ),
        ErrorCode.RECORD_NOT_FOUND: ErrorDetail(
            code=ErrorCode.RECORD_NOT_FOUND,
            message="Requested file not found",
            user_message="The file you're looking for doesn't exist or has been deleted",
            http_status=404
        ),
        ErrorCode.DATABASE_ERROR: ErrorDetail(
            code=ErrorCode.DATABASE_ERROR,
            message="Database operation failed",
            user_message="There's a temporary issue with our database. Please try again later",
            http_status=500,
            log_level="CRITICAL"
        ),
        ErrorCode.INTERNAL_ERROR: ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR,
            message="Internal server error",
            user_message="Something went wrong on our end. Please try again later",
            http_status=500,
            log_level="CRITICAL"
        ),
        ErrorCode.INVALID_REQUEST: ErrorDetail(
            code=ErrorCode.INVALID_REQUEST,
            message="Invalid request parameters",
            user_message="The request contains invalid data. Please check your input and try again",
            http_status=400
        ),
        
        # Google Drive Integration Errors
        ErrorCode.GOOGLE_DRIVE_CONFIG_ERROR: ErrorDetail(
            code=ErrorCode.GOOGLE_DRIVE_CONFIG_ERROR,
            message="Google Drive configuration error",
            user_message="Google Drive integration is not properly configured. Your file has been saved locally.",
            http_status=500,
            log_level="CRITICAL"
        ),
        ErrorCode.GOOGLE_DRIVE_AUTH_FAILED: ErrorDetail(
            code=ErrorCode.GOOGLE_DRIVE_AUTH_FAILED,
            message="Google Drive authentication failed",
            user_message="Unable to connect to Google Drive. Your file has been saved locally.",
            http_status=503
        ),
        ErrorCode.GOOGLE_DRIVE_QUOTA_EXCEEDED: ErrorDetail(
            code=ErrorCode.GOOGLE_DRIVE_QUOTA_EXCEEDED,
            message="Google Drive API quota exceeded",
            user_message="Google Drive is temporarily unavailable due to high usage. Your file has been saved locally.",
            http_status=503
        ),
        ErrorCode.GOOGLE_DRIVE_UPLOAD_FAILED: ErrorDetail(
            code=ErrorCode.GOOGLE_DRIVE_UPLOAD_FAILED,
            message="Failed to upload file to Google Drive",
            user_message="Couldn't upload to Google Drive, but your file has been saved locally.",
            http_status=500
        ),
        ErrorCode.GOOGLE_DRIVE_SHARING_FAILED: ErrorDetail(
            code=ErrorCode.GOOGLE_DRIVE_SHARING_FAILED,
            message="Failed to share Google Drive file with user",
            user_message="Your file was uploaded to Google Drive but couldn't be shared automatically. You can access it from your file dashboard.",
            http_status=500
        ),
        ErrorCode.GOOGLE_DRIVE_CONVERSION_FAILED: ErrorDetail(
            code=ErrorCode.GOOGLE_DRIVE_CONVERSION_FAILED,
            message="Failed to convert file to Google Docs format",
            user_message="Your file was uploaded to Google Drive but couldn't be converted to an editable document.",
            http_status=500
        ),
        ErrorCode.GOOGLE_DRIVE_SERVICE_UNAVAILABLE: ErrorDetail(
            code=ErrorCode.GOOGLE_DRIVE_SERVICE_UNAVAILABLE,
            message="Google Drive service is temporarily unavailable",
            user_message="Google Drive is temporarily unavailable. Your file has been saved locally and will be synced when the service is restored.",
            http_status=503
        ),
        
        # Duplicate Detection Errors
        ErrorCode.DUPLICATE_DETECTION_FAILED: ErrorDetail(
            code=ErrorCode.DUPLICATE_DETECTION_FAILED,
            message="Duplicate detection service failed",
            user_message="Unable to check for duplicate files. Your file has been uploaded successfully.",
            http_status=500
        ),
        ErrorCode.DUPLICATE_HASH_COLLISION: ErrorDetail(
            code=ErrorCode.DUPLICATE_HASH_COLLISION,
            message="Hash collision detected during duplicate processing",
            user_message="There was an issue processing your file for duplicates. Your file has been saved with a unique name.",
            http_status=500
        ),
        
        # Soft Deletion Errors
        ErrorCode.FILE_ALREADY_DELETED: ErrorDetail(
            code=ErrorCode.FILE_ALREADY_DELETED,
            message="File is already deleted",
            user_message="This file has already been deleted.",
            http_status=400
        ),
        ErrorCode.FILE_NOT_DELETED: ErrorDetail(
            code=ErrorCode.FILE_NOT_DELETED,
            message="File is not in deleted state",
            user_message="This file is not deleted and cannot be restored.",
            http_status=400
        ),
        ErrorCode.RESTORE_FAILED: ErrorDetail(
            code=ErrorCode.RESTORE_FAILED,
            message="Failed to restore deleted file",
            user_message="Unable to restore the file. Please try again or contact support.",
            http_status=500
        ),
    }
    
    def __init__(self, logger_name: str = __name__):
        """Initialize error handler with logger"""
        self.logger = logging.getLogger(logger_name)
    
    def create_error_response(self, error_code: ErrorCode, context: Optional[Dict[str, Any]] = None,
                            custom_message: Optional[str] = None) -> Tuple[Response, int]:
        """
        Create standardized error response
        
        Args:
            error_code: ErrorCode enum value
            context: Additional context information
            custom_message: Custom user message to override default
            
        Returns:
            Tuple of (Flask Response, HTTP status code)
        """
        error_detail = self.ERROR_DEFINITIONS.get(error_code, self.ERROR_DEFINITIONS[ErrorCode.INTERNAL_ERROR])
        
        # Apply context to user message if provided
        user_message = custom_message or error_detail.user_message
        if context and "{" in user_message:
            try:
                user_message = user_message.format(**context)
            except (KeyError, ValueError):
                # If formatting fails, use original message
                pass
        
        # Log the error
        log_message = f"Error {error_code.value}: {error_detail.message}"
        if context:
            log_message += f" | Context: {context}"
        
        if error_detail.log_level == "CRITICAL":
            self.logger.critical(log_message)
        elif error_detail.log_level == "ERROR":
            self.logger.error(log_message)
        else:
            self.logger.warning(log_message)
        
        # Create response
        response_data = {
            'success': False,
            'error_code': error_code.value,
            'message': user_message,
            'timestamp': self._get_timestamp()
        }
        
        if context and context.get('include_details', False):
            response_data['details'] = context
        
        return jsonify(response_data), error_detail.http_status
    
    def handle_exception(self, e: Exception, error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
                        context: Optional[Dict[str, Any]] = None) -> Tuple[Response, int]:
        """
        Handle unexpected exceptions with proper logging
        
        Args:
            e: Exception that occurred
            error_code: ErrorCode to use for response
            context: Additional context information
            
        Returns:
            Tuple of (Flask Response, HTTP status code)
        """
        # Log the full exception with traceback
        self.logger.error(
            f"Exception occurred: {str(e)}\n"
            f"Type: {type(e).__name__}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        # Add exception info to context
        if context is None:
            context = {}
        context['exception_type'] = type(e).__name__
        
        return self.create_error_response(error_code, context)
    
    def handle_google_drive_error(self, exception: Exception, operation: str = "unknown", 
                                  context: Optional[Dict[str, Any]] = None) -> Tuple[Response, int]:
        """
        Handle Google Drive specific errors with appropriate mapping
        
        Args:
            exception: The Google Drive exception
            operation: The operation that failed (upload, share, convert, etc.)
            context: Additional context information
            
        Returns:
            Tuple of (Flask Response, HTTP status code)
        """
        if context is None:
            context = {}
        context['operation'] = operation
        
        # Map Google Drive exceptions to error codes
        error_code = ErrorCode.GOOGLE_DRIVE_SERVICE_UNAVAILABLE
        
        if hasattr(exception, 'resp') and hasattr(exception.resp, 'status'):
            status = exception.resp.status
            if status == 403:
                error_code = ErrorCode.GOOGLE_DRIVE_AUTH_FAILED
            elif status == 429:
                error_code = ErrorCode.GOOGLE_DRIVE_QUOTA_EXCEEDED
            elif status == 404:
                error_code = ErrorCode.GOOGLE_DRIVE_SERVICE_UNAVAILABLE
        elif "quota" in str(exception).lower():
            error_code = ErrorCode.GOOGLE_DRIVE_QUOTA_EXCEEDED
        elif "auth" in str(exception).lower() or "permission" in str(exception).lower():
            error_code = ErrorCode.GOOGLE_DRIVE_AUTH_FAILED
        elif "upload" in operation.lower():
            error_code = ErrorCode.GOOGLE_DRIVE_UPLOAD_FAILED
        elif "share" in operation.lower():
            error_code = ErrorCode.GOOGLE_DRIVE_SHARING_FAILED
        elif "convert" in operation.lower():
            error_code = ErrorCode.GOOGLE_DRIVE_CONVERSION_FAILED
        
        return self.handle_exception(exception, error_code, context)
    
    def handle_duplicate_detection_error(self, exception: Exception, 
                                       context: Optional[Dict[str, Any]] = None) -> Tuple[Response, int]:
        """
        Handle duplicate detection errors
        
        Args:
            exception: The duplicate detection exception
            context: Additional context information
            
        Returns:
            Tuple of (Flask Response, HTTP status code)
        """
        error_code = ErrorCode.DUPLICATE_DETECTION_FAILED
        
        if "hash" in str(exception).lower() and "collision" in str(exception).lower():
            error_code = ErrorCode.DUPLICATE_HASH_COLLISION
        
        return self.handle_exception(exception, error_code, context)
    
    def create_success_response_with_warnings(self, message: str, data: Optional[Dict[str, Any]] = None,
                                            warnings: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a success response that includes warnings for partial failures
        
        Args:
            message: Success message
            data: Response data
            warnings: List of warning messages
            
        Returns:
            Success response dictionary with warnings
        """
        response = {
            'success': True,
            'message': message,
            'timestamp': self._get_timestamp()
        }
        
        if data:
            response.update(data)
        
        if warnings:
            response['warnings'] = warnings
        
        return response
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for error responses"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
    
    def handle_google_drive_error(self, error_code: ErrorCode, exception: Exception, 
                                 operation: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle Google Drive specific errors with appropriate mapping
        
        Args:
            error_code: The error code enum
            exception: The Google Drive exception
            operation: The operation that failed (upload, share, convert, etc.)
            context: Additional context information
            
        Returns:
            Dictionary with error response structure
        """
        if context is None:
            context = {}
            
        # Log the error
        logger.error(f"Google Drive error [{error_code.value}]: {str(exception)} during {operation}")
        
        # Map error codes to user messages
        if error_code == ErrorCode.GDRIVE_001:
            message = "Google Drive authentication failed"
        elif error_code == ErrorCode.GDRIVE_002:
            message = "Failed to upload file to Google Drive"
        elif error_code == ErrorCode.GOOGLE_DRIVE_AUTH_FAILED:
            message = "Google Drive authentication failed"
        elif error_code == ErrorCode.GOOGLE_DRIVE_UPLOAD_FAILED:
            message = "Failed to upload file to Google Drive"
        elif error_code == ErrorCode.GOOGLE_DRIVE_SHARING_FAILED:
            message = "Failed to share file on Google Drive"
        elif error_code == ErrorCode.GOOGLE_DRIVE_CONVERSION_FAILED:
            message = "Failed to convert file on Google Drive"
        else:
            message = "Google Drive operation failed"
        
        return {
            'success': False,
            'error_code': error_code.value,
            'message': message,
            'details': f"operation: {operation}",
            'context': context
        }
    
    def handle_duplicate_detection_error(self, error_code: ErrorCode, exception: Exception,
                                       context: Optional[Dict[str, Any]] = None, filename: str = None) -> Dict[str, Any]:
        """
        Handle duplicate detection errors
        
        Args:
            error_code: The error code enum
            exception: The duplicate detection exception
            context: Additional context information
            filename: The filename involved in the duplicate detection
            
        Returns:
            Dictionary with error response structure
        """
        if context is None:
            context = {}
            
        # Log the error
        logger.error(f"Duplicate detection error [{error_code.value}]: {str(exception)}")
        
        # Map error codes to user messages
        if error_code == ErrorCode.DUP_001:
            message = "Failed to calculate file hash"
        elif error_code == ErrorCode.DUP_002:
            message = "Failed to check for duplicate files"
        else:
            message = "Duplicate detection failed"
        
        # Build details string
        details = str(exception)
        if filename:
            details = f"filename: {filename}, error: {details}"
        
        return {
            'success': False,
            'error_code': error_code.value,
            'message': message,
            'details': details,
            'context': context
        }
    
    def handle_error(self, exception: Exception, message: str, error_code: str,
                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle generic errors
        
        Args:
            exception: The exception that occurred
            message: User-friendly error message
            error_code: Error code string
            context: Additional context information
            
        Returns:
            Dictionary with error response structure
        """
        if context is None:
            context = {}
            
        # Log the error
        logger.error(f"Generic error [{error_code}]: {str(exception)}")
        
        return {
            'success': False,
            'error_code': error_code,
            'message': message,
            'details': str(exception),
            'context': context
        }
    
    def log_warning(self, message: str, warning_code: str,
                   context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log warning messages
        
        Args:
            message: Warning message
            warning_code: Warning code string
            context: Additional context information
        """
        if context is None:
            context = {}
            
        # Log the warning
        logger.warning(f"Warning [{warning_code}]: {message}")



def handle_file_management_errors(f):
    """
    Decorator for handling file management errors in API endpoints
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        error_handler = ErrorHandler()
        
        try:
            return f(*args, **kwargs)
        except FileManagementError as e:
            # Handle known file management errors
            return error_handler.create_error_response(
                error_code=e.error_detail.code,
                context=None,  # FileManagementError doesn't have context attribute
                custom_message=e.error_detail.user_message
            )
        except ValueError as e:
            # Handle storage configuration errors
            return error_handler.handle_exception(
                e, ErrorCode.STORAGE_CONFIG_ERROR, 
                context={'operation': 'file_management', 'error_type': 'ValueError'}
            )
        except FileNotFoundError as e:
            # Handle file not found errors
            return error_handler.handle_exception(
                e, ErrorCode.RECORD_NOT_FOUND,  # Use existing error code
                context={'operation': 'file_management', 'error_type': 'FileNotFoundError'}
            )
        except PermissionError as e:
            # Handle permission errors
            return error_handler.handle_exception(
                e, ErrorCode.ACCESS_DENIED,  # Use existing error code
                context={'operation': 'file_management', 'error_type': 'PermissionError'}
            )
        except TimeoutError as e:
            # Handle timeout errors
            return error_handler.handle_exception(
                e, ErrorCode.PROCESSING_TIMEOUT,
                context={'operation': 'file_management', 'error_type': 'TimeoutError'}
            )
        except Exception as e:
            # Handle unexpected errors
            return error_handler.handle_exception(
                e, ErrorCode.INTERNAL_ERROR,  # Use existing error code
                context={'operation': 'file_management', 'error_type': 'Exception'}
            )
    
    return decorated_function
