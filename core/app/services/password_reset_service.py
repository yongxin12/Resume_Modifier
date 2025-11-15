"""
Password Reset Service for handling secure password reset operations
Manages token generation, validation, rate limiting, and security measures

Author: Resume Modifier Backend Team
Date: November 2024
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from flask import current_app, request
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.temp import User, PasswordResetToken
from app.services.email_service import email_service, EmailResult
from app.utils.password_reset_error_handler import (
    password_reset_error_handler_instance,
    password_reset_error_handler,
    PasswordResetErrorCode,
    PasswordResetSecurityEvent
)


class PasswordResetError(Exception):
    """Custom exception for password reset related errors"""
    pass


@dataclass
class PasswordResetResult:
    """Result object for password reset operations"""
    success: bool
    message: str
    token_id: Optional[int] = None
    user_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    email_sent: bool = False
    rate_limited: bool = False
    error_code: Optional[str] = None


class PasswordResetService:
    """
    Service for handling password reset operations with enhanced security.
    Includes rate limiting, token management, and email integration.
    """

    def __init__(self):
        """Initialize the password reset service."""
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting configuration (can be overridden by app config)
        self.max_requests_per_hour = 5  # Max password reset requests per user per hour
        self.max_requests_per_ip_per_hour = 10  # Max requests per IP per hour
        self.token_expiry_hours = 1  # Token expiry time in hours
        self.cleanup_interval_hours = 24  # How often to cleanup expired tokens

    def _convert_error_to_result(self, error_dict: Dict[str, Any]) -> PasswordResetResult:
        """Convert error handler dict to PasswordResetResult"""
        return PasswordResetResult(
            success=error_dict.get('status') == 'success',
            message=error_dict.get('message', 'Unknown error'),
            error_code=error_dict.get('error_code')
        )

    def _get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User instance if found, None otherwise
        """
        try:
            return User.query.filter_by(email=email.lower().strip()).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while finding user by email: {e}")
            return None

    def _check_rate_limits(self, user_id: int, ip_address: str) -> Tuple[bool, str]:
        """
        Check rate limits for password reset requests.
        
        Args:
            user_id: ID of the user requesting reset
            ip_address: IP address of the request
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        try:
            current_time = datetime.utcnow()
            hour_ago = current_time - timedelta(hours=1)
            
            # Check user-specific rate limit
            user_requests = PasswordResetToken.query.filter(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.created_at > hour_ago
            ).count()
            
            if user_requests >= self.max_requests_per_hour:
                return False, f"Too many password reset requests. Please wait before trying again."
            
            # Check IP-specific rate limit
            ip_requests = PasswordResetToken.query.filter(
                PasswordResetToken.ip_address == ip_address,
                PasswordResetToken.created_at > hour_ago
            ).count()
            
            if ip_requests >= self.max_requests_per_ip_per_hour:
                return False, f"Too many password reset requests from this location. Please wait before trying again."
            
            return True, "Rate limit check passed"
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error during rate limit check: {e}")
            # In case of database error, allow the request but log it
            return True, "Rate limit check failed - allowing request"

    def _revoke_existing_tokens(self, user_id: int) -> int:
        """
        Revoke all existing active tokens for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Number of tokens revoked
        """
        try:
            revoked_count = PasswordResetToken.revoke_all_user_tokens(user_id)
            if revoked_count > 0:
                db.session.commit()
                self.logger.info(f"Revoked {revoked_count} existing tokens for user {user_id}")
            return revoked_count
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while revoking tokens: {e}")
            db.session.rollback()
            return 0

    def _get_request_metadata(self) -> Dict[str, str]:
        """
        Extract request metadata for security logging.
        
        Returns:
            Dictionary with IP address and user agent
        """
        if request:
            # Handle X-Forwarded-For header for proxy/load balancer setups
            forwarded_ips = request.headers.get('X-Forwarded-For')
            if forwarded_ips:
                ip_address = forwarded_ips.split(',')[0].strip()
            else:
                ip_address = request.remote_addr or 'Unknown'
            
            user_agent = request.headers.get('User-Agent', 'Unknown')
        else:
            ip_address = 'Unknown'
            user_agent = 'Unknown'
        
        return {
            'ip_address': ip_address,
            'user_agent': user_agent
        }

    @password_reset_error_handler('password_reset_request')
    def request_password_reset(self, email: str, frontend_url: Optional[str] = None) -> PasswordResetResult:
        """
        Request a password reset for a user.
        
        Args:
            email: User's email address
            frontend_url: Custom frontend URL for reset link (optional)
            
        Returns:
            PasswordResetResult with operation details
        """
        try:
            email = email.lower().strip()
            self.logger.info(f"Password reset requested for email: {email}")
            
            # Get request metadata
            metadata = self._get_request_metadata()
            ip_address = metadata['ip_address']
            user_agent = metadata['user_agent']
            
            # Find user by email
            user = self._get_user_by_email(email)
            if not user:
                # Return success message even for non-existent users (security best practice)
                password_reset_error_handler_instance.logger.log_security_event(
                    event_type=PasswordResetSecurityEvent.PASSWORD_RESET_REQUESTED,
                    email=email,
                    error_code=PasswordResetErrorCode.INVALID_EMAIL,
                    additional_data={'reason': 'non_existent_user'}
                )
                return PasswordResetResult(
                    success=True,
                    message="If an account with this email exists, you will receive a password reset link.",
                    email_sent=False
                )
            
            # Check rate limits
            rate_allowed, rate_message = self._check_rate_limits(user.id, ip_address)
            if not rate_allowed:
                return PasswordResetResult(
                    success=False,
                    message=rate_message,
                    user_id=user.id,
                    rate_limited=True,
                    error_code=PasswordResetErrorCode.RATE_LIMITED_USER
                )
            
            # Revoke existing tokens
            self._revoke_existing_tokens(user.id)
            
            # Create new password reset token
            token_instance, raw_token = PasswordResetToken.create_token(
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                expiry_hours=self.token_expiry_hours
            )
            
            # Save token to database
            db.session.add(token_instance)
            db.session.commit()
            
            self.logger.info(f"Created password reset token {token_instance.id} for user {user.id}")
            
            # Send email
            email_result = email_service.send_password_reset_email(
                user_email=email,
                reset_token=raw_token,
                user_ip=ip_address,
                expiry_hours=self.token_expiry_hours
            )
            
            if email_result.success:
                self.logger.info(f"Password reset email sent successfully to {email}")
                return PasswordResetResult(
                    success=True,
                    message="If an account with this email exists, you will receive a password reset link.",
                    token_id=token_instance.id,
                    user_id=user.id,
                    expires_at=token_instance.expires_at,
                    email_sent=True
                )
            else:
                # Email failed - revoke the token since it's useless
                token_instance.mark_used()
                db.session.commit()
                
                password_reset_error_handler_instance.logger.log_security_event(
                    event_type=PasswordResetSecurityEvent.PASSWORD_RESET_FAILED,
                    user_id=user.id,
                    email=email,
                    token_id=token_instance.id,
                    error_code=PasswordResetErrorCode.EMAIL_SEND_FAILED,
                    additional_data={'email_error': email_result.error_message}
                )
                
                return PasswordResetResult(
                    success=False,
                    message="Failed to send password reset email. Please try again later.",
                    user_id=user.id,
                    email_sent=False,
                    error_code=PasswordResetErrorCode.EMAIL_SEND_FAILED
                )
                
        except Exception as e:
            error_result = password_reset_error_handler_instance.handle_service_error(
                error=e,
                operation="password_reset_request",
                user_id=user.id if 'user' in locals() else None,
                email=email,
                error_code=PasswordResetErrorCode.INTERNAL_ERROR
            )
            return self._convert_error_to_result(error_result)

    @password_reset_error_handler('password_reset_validate')
    def validate_reset_token(self, token: str) -> PasswordResetResult:
        """
        Validate a password reset token without consuming it.
        
        Args:
            token: Raw password reset token
            
        Returns:
            PasswordResetResult with validation details
        """
        try:
            self.logger.info("Validating password reset token")
            
            if not token:
                error_result = password_reset_error_handler_instance.handle_validation_error(
                    error_code=PasswordResetErrorCode.MISSING_TOKEN,
                    message="Invalid or missing token.",
                    operation="token_validation"
                )
                return self._convert_error_to_result(error_result)
            
            # Verify token
            token_instance = PasswordResetToken.verify_token(token)
            if not token_instance:
                error_result = password_reset_error_handler_instance.handle_token_error(
                    error_code=PasswordResetErrorCode.INVALID_TOKEN,
                    message="Invalid or expired token."
                )
                return self._convert_error_to_result(error_result)
            
            # Get user
            user = User.query.get(token_instance.user_id)
            if not user:
                self.logger.error(f"Token {token_instance.id} references non-existent user {token_instance.user_id}")
                return PasswordResetResult(
                    success=False,
                    message="Invalid token.",
                    error_code="INVALID_TOKEN"
                )
            
            return PasswordResetResult(
                success=True,
                message="Token is valid.",
                token_id=token_instance.id,
                user_id=user.id,
                expires_at=token_instance.expires_at
            )
            
        except Exception as e:
            error_result = password_reset_error_handler_instance.handle_service_error(
                error=e,
                operation="token_validation",
                error_code=PasswordResetErrorCode.INTERNAL_ERROR
            )
            return self._convert_error_to_result(error_result)

    @password_reset_error_handler('password_reset_verify')
    def reset_password(self, token: str, new_password: str) -> PasswordResetResult:
        """
        Reset user password using a valid token.
        
        Args:
            token: Raw password reset token
            new_password: New password for the user
            
        Returns:
            PasswordResetResult with operation details
        """
        try:
            self.logger.info("Processing password reset")
            
            # Validate inputs
            if not token or not new_password:
                error_result = password_reset_error_handler_instance.handle_validation_error(
                    error_code=PasswordResetErrorCode.MISSING_TOKEN if not token else PasswordResetErrorCode.MISSING_PASSWORD,
                    message="Invalid token or password.",
                    operation="password_reset_verify"
                )
                return self._convert_error_to_result(error_result)
            
            if len(new_password) < 8:
                error_result = password_reset_error_handler_instance.handle_validation_error(
                    error_code=PasswordResetErrorCode.WEAK_PASSWORD,
                    message="Password must be at least 8 characters long.",
                    operation="password_reset_verify"
                )
                return self._convert_error_to_result(error_result)
            
            # Verify and consume token
            token_instance = PasswordResetToken.verify_token(token)
            if not token_instance:
                error_result = password_reset_error_handler_instance.handle_token_error(
                    error_code=PasswordResetErrorCode.INVALID_TOKEN,
                    message="Invalid or expired token."
                )
                return self._convert_error_to_result(error_result)
            
            # Get user
            user = User.query.get(token_instance.user_id)
            if not user:
                self.logger.error(f"Token {token_instance.id} references non-existent user {token_instance.user_id}")
                return PasswordResetResult(
                    success=False,
                    message="Invalid token.",
                    error_code="INVALID_TOKEN"
                )
            
            # Update password
            user.set_password(new_password)
            
            # Mark token as used
            token_instance.mark_used()
            
            # Revoke all other tokens for this user
            revoked_count = PasswordResetToken.revoke_all_user_tokens(user.id)
            
            # Commit changes
            db.session.commit()
            
            self.logger.info(f"Password reset successful for user {user.id}")
            self.logger.info(f"Revoked {revoked_count} other tokens for user {user.id}")
            
            return PasswordResetResult(
                success=True,
                message="Password has been reset successfully.",
                user_id=user.id,
                token_id=token_instance.id
            )
            
        except Exception as e:
            db.session.rollback()
            error_result = password_reset_error_handler_instance.handle_service_error(
                error=e,
                operation="password_reset_verify",
                user_id=user.id if 'user' in locals() else None,
                error_code=PasswordResetErrorCode.INTERNAL_ERROR
            )
            return self._convert_error_to_result(error_result)

    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired password reset tokens.
        
        Returns:
            Number of tokens cleaned up
        """
        try:
            count = PasswordResetToken.cleanup_expired_tokens()
            if count > 0:
                db.session.commit()
                self.logger.info(f"Cleaned up {count} expired password reset tokens")
            return count
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error during token cleanup: {e}")
            return 0

    def get_user_token_info(self, user_id: int) -> Dict[str, Any]:
        """
        Get information about active tokens for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with token information
        """
        try:
            active_tokens = PasswordResetToken.get_active_tokens_for_user(user_id)
            
            return {
                'user_id': user_id,
                'active_token_count': len(active_tokens),
                'tokens': [
                    {
                        'id': token.id,
                        'created_at': token.created_at.isoformat(),
                        'expires_at': token.expires_at.isoformat(),
                        'ip_address': token.ip_address,
                        'is_valid': token.is_valid()
                    }
                    for token in active_tokens
                ]
            }
        except Exception as e:
            self.logger.error(f"Error getting user token info: {e}")
            return {
                'user_id': user_id,
                'active_token_count': 0,
                'tokens': [],
                'error': str(e)
            }

    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get service statistics and health information.
        
        Returns:
            Dictionary with service statistics
        """
        try:
            current_time = datetime.utcnow()
            hour_ago = current_time - timedelta(hours=1)
            day_ago = current_time - timedelta(days=1)
            
            # Query statistics
            total_tokens = PasswordResetToken.query.count()
            active_tokens = PasswordResetToken.query.filter(
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > current_time
            ).count()
            
            recent_requests = PasswordResetToken.query.filter(
                PasswordResetToken.created_at > hour_ago
            ).count()
            
            daily_requests = PasswordResetToken.query.filter(
                PasswordResetToken.created_at > day_ago
            ).count()
            
            expired_tokens = PasswordResetToken.query.filter(
                PasswordResetToken.expires_at < current_time
            ).count()
            
            return {
                'service': 'PasswordResetService',
                'timestamp': current_time.isoformat(),
                'statistics': {
                    'total_tokens_created': total_tokens,
                    'active_tokens': active_tokens,
                    'expired_tokens': expired_tokens,
                    'requests_last_hour': recent_requests,
                    'requests_last_24h': daily_requests
                },
                'configuration': {
                    'max_requests_per_hour': self.max_requests_per_hour,
                    'max_requests_per_ip_per_hour': self.max_requests_per_ip_per_hour,
                    'token_expiry_hours': self.token_expiry_hours
                },
                'email_service_status': email_service.get_configuration_status()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting service stats: {e}")
            return {
                'service': 'PasswordResetService',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Global instance
password_reset_service = PasswordResetService()