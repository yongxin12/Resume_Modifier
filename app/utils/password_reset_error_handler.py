"""
Centralized error handling and logging for password reset operations
Provides structured error handling, security logging, and monitoring
"""

import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from functools import wraps
from flask import request, current_app, g
import json
import os


class PasswordResetErrorCode:
    """Standard error codes for password reset operations"""
    
    # Request errors
    INVALID_EMAIL = "INVALID_EMAIL"
    MISSING_EMAIL = "MISSING_EMAIL"
    MISSING_TOKEN = "MISSING_TOKEN"
    MISSING_PASSWORD = "MISSING_PASSWORD"
    WEAK_PASSWORD = "WEAK_PASSWORD"
    
    # Token errors
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    USED_TOKEN = "USED_TOKEN"
    TOKEN_GENERATION_FAILED = "TOKEN_GENERATION_FAILED"
    
    # Rate limiting
    RATE_LIMITED_USER = "RATE_LIMITED_USER"
    RATE_LIMITED_IP = "RATE_LIMITED_IP"
    
    # Service errors
    EMAIL_SEND_FAILED = "EMAIL_SEND_FAILED"
    DATABASE_ERROR = "DATABASE_ERROR"
    SMTP_ERROR = "SMTP_ERROR"
    
    # Security
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    BRUTE_FORCE_DETECTED = "BRUTE_FORCE_DETECTED"
    
    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class PasswordResetSecurityEvent:
    """Security event types for logging"""
    
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_TOKEN_VALIDATED = "password_reset_token_validated"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    PASSWORD_RESET_FAILED = "password_reset_failed"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN_ATTEMPT = "invalid_token_attempt"
    SUSPICIOUS_PATTERN_DETECTED = "suspicious_pattern_detected"


class PasswordResetLogger:
    """Specialized logger for password reset operations"""
    
    def __init__(self):
        self.logger = logging.getLogger('password_reset')
        self.security_logger = logging.getLogger('password_reset.security')
        
        # Configure formatters if not already configured
        if not self.logger.handlers:
            self._configure_logging()
    
    def _configure_logging(self):
        """Configure logging for password reset operations"""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '[%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s'
        )
        
        security_formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        
        # Console handler for general logging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(detailed_formatter)
        console_handler.setLevel(logging.INFO)
        
        # File handler for security events (if configured)
        security_log_file = os.getenv('SECURITY_LOG_FILE')
        if security_log_file:
            try:
                security_handler = logging.FileHandler(security_log_file)
                security_handler.setFormatter(security_formatter)
                security_handler.setLevel(logging.WARNING)
                self.security_logger.addHandler(security_handler)
            except Exception as e:
                self.logger.warning(f"Could not create security log file handler: {e}")
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)
        self.security_logger.setLevel(logging.WARNING)
    
    def _get_request_context(self) -> Dict[str, Any]:
        """Extract request context for logging"""
        context = {
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': 'unknown',
            'user_agent': 'unknown',
            'endpoint': 'unknown',
            'method': 'unknown'
        }
        
        if request:
            # Get real IP address considering proxies
            forwarded_ips = request.headers.get('X-Forwarded-For')
            if forwarded_ips:
                context['ip_address'] = forwarded_ips.split(',')[0].strip()
            else:
                context['ip_address'] = request.remote_addr or 'unknown'
            
            context.update({
                'user_agent': request.headers.get('User-Agent', 'unknown'),
                'endpoint': request.endpoint or 'unknown',
                'method': request.method,
                'url': request.url
            })
        
        return context
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        token_id: Optional[int] = None,
        error_code: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Log security-related events"""
        context = self._get_request_context()
        
        log_data = {
            'event_type': event_type,
            'user_id': user_id,
            'email': email,
            'token_id': token_id,
            'error_code': error_code,
            **context
        }
        
        if additional_data:
            log_data.update(additional_data)
        
        # Sanitize sensitive data
        if 'password' in log_data:
            log_data['password'] = '***REDACTED***'
        if 'token' in log_data:
            log_data['token'] = '***REDACTED***'
        
        message = f"{event_type.upper()}: {json.dumps(log_data, default=str)}"
        
        if error_code:
            self.security_logger.warning(message)
        else:
            self.security_logger.info(message)
    
    def log_operation(
        self,
        operation: str,
        success: bool,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        error_code: Optional[str] = None,
        execution_time: Optional[float] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Log password reset operations"""
        context = self._get_request_context()
        
        log_data = {
            'operation': operation,
            'success': success,
            'user_id': user_id,
            'email': email,
            'error_code': error_code,
            'execution_time_ms': round(execution_time * 1000, 2) if execution_time else None,
            **context
        }
        
        if additional_data:
            log_data.update(additional_data)
        
        message = f"PASSWORD_RESET_OPERATION: {json.dumps(log_data, default=str)}"
        
        if success:
            self.logger.info(message)
        else:
            self.logger.error(message)
    
    def log_error(
        self,
        operation: str,
        error: Exception,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        """Log errors with full context"""
        context = self._get_request_context()
        
        error_data = {
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'user_id': user_id,
            'email': email,
            'error_code': error_code,
            'traceback': traceback.format_exc(),
            **context
        }
        
        message = f"PASSWORD_RESET_ERROR: {json.dumps(error_data, default=str)}"
        self.logger.error(message)


class PasswordResetErrorHandler:
    """Centralized error handling for password reset operations"""
    
    def __init__(self):
        self.logger = PasswordResetLogger()
    
    def handle_validation_error(
        self,
        error_code: str,
        message: str,
        operation: str = "validation",
        user_id: Optional[int] = None,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle validation errors"""
        self.logger.log_security_event(
            event_type=PasswordResetSecurityEvent.PASSWORD_RESET_FAILED,
            user_id=user_id,
            email=email,
            error_code=error_code,
            additional_data={'validation_message': message}
        )
        
        return {
            'status': 'error',
            'message': message,
            'error_code': error_code
        }
    
    def handle_rate_limit_error(
        self,
        error_code: str,
        message: str,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        current_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """Handle rate limiting errors"""
        self.logger.log_security_event(
            event_type=PasswordResetSecurityEvent.RATE_LIMIT_EXCEEDED,
            user_id=user_id,
            email=email,
            error_code=error_code,
            additional_data={
                'current_count': current_count,
                'limit_message': message
            }
        )
        
        return {
            'status': 'error',
            'message': message,
            'error_code': error_code
        }
    
    def handle_token_error(
        self,
        error_code: str,
        message: str,
        token_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Handle token-related errors"""
        self.logger.log_security_event(
            event_type=PasswordResetSecurityEvent.INVALID_TOKEN_ATTEMPT,
            user_id=user_id,
            token_id=token_id,
            error_code=error_code
        )
        
        return {
            'status': 'error',
            'message': message,
            'error_code': error_code
        }
    
    def handle_service_error(
        self,
        error: Exception,
        operation: str,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        error_code: str = PasswordResetErrorCode.INTERNAL_ERROR
    ) -> Dict[str, Any]:
        """Handle service errors"""
        self.logger.log_error(
            operation=operation,
            error=error,
            user_id=user_id,
            email=email,
            error_code=error_code
        )
        
        # Don't expose internal error details to clients
        if current_app and current_app.debug:
            message = f"Service error in {operation}: {str(error)}"
        else:
            message = "An internal error occurred. Please try again later."
        
        return {
            'status': 'error',
            'message': message,
            'error_code': error_code
        }
    
    def log_success(
        self,
        operation: str,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        token_id: Optional[int] = None,
        execution_time: Optional[float] = None
    ):
        """Log successful operations"""
        event_map = {
            'password_reset_request': PasswordResetSecurityEvent.PASSWORD_RESET_REQUESTED,
            'password_reset_validate': PasswordResetSecurityEvent.PASSWORD_RESET_TOKEN_VALIDATED,
            'password_reset_verify': PasswordResetSecurityEvent.PASSWORD_RESET_COMPLETED
        }
        
        event_type = event_map.get(operation, operation)
        
        self.logger.log_security_event(
            event_type=event_type,
            user_id=user_id,
            email=email,
            token_id=token_id
        )
        
        self.logger.log_operation(
            operation=operation,
            success=True,
            user_id=user_id,
            email=email,
            execution_time=execution_time
        )


def password_reset_error_handler(operation: str):
    """Decorator for handling password reset operation errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            error_handler = PasswordResetErrorHandler()
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful operations
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Extract user info from result if available
                user_id = getattr(result, 'user_id', None) if hasattr(result, 'user_id') else None
                token_id = getattr(result, 'token_id', None) if hasattr(result, 'token_id') else None
                
                if hasattr(result, 'success') and result.success:
                    error_handler.log_success(
                        operation=operation,
                        user_id=user_id,
                        token_id=token_id,
                        execution_time=execution_time
                    )
                
                return result
                
            except Exception as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                error_handler.logger.log_operation(
                    operation=operation,
                    success=False,
                    error_code=PasswordResetErrorCode.INTERNAL_ERROR,
                    execution_time=execution_time
                )
                
                # Re-raise the exception to be handled by the calling code
                raise
        
        return wrapper
    return decorator


# Global error handler instance
password_reset_error_handler_instance = PasswordResetErrorHandler()
password_reset_logger = PasswordResetLogger()