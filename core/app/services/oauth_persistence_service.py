"""
OAuth Persistence Service for managing persistent Google OAuth authentication
Handles automatic token refresh, session management, and storage monitoring

Author: Resume Modifier Backend Team
Date: November 2024
"""

import logging
import secrets
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from flask import current_app, request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from app.extensions import db
from app.models.temp import User, GoogleAuth
import google.oauth2.credentials
import google.auth.transport.requests
from googleapiclient.discovery import build


class OAuthPersistenceError(Exception):
    """Custom exception for OAuth persistence related errors"""
    pass


@dataclass
class TokenRefreshResult:
    """Result object for token refresh operations"""
    success: bool
    message: str
    new_access_token: Optional[str] = None
    new_expires_at: Optional[datetime] = None
    refresh_attempts: int = 0
    error_code: Optional[str] = None


@dataclass
class StorageQuotaInfo:
    """Result object for storage quota information"""
    total_quota: int
    used_quota: int
    usage_percentage: float
    warning_level: str
    last_check: Optional[datetime] = None


class OAuthPersistenceService:
    """
    Service for managing persistent OAuth authentication with automatic token refresh
    and storage monitoring capabilities.
    """

    def __init__(self):
        """Initialize the OAuth persistence service."""
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.token_refresh_interval = 900  # 15 minutes
        self.token_expiry_threshold = 300   # 5 minutes
        self.max_refresh_failures = 5
        self.storage_check_interval = 21600  # 6 hours
        
        # Storage warning thresholds
        self.storage_thresholds = {
            'low': 80,
            'medium': 85,
            'high': 90,
            'critical': 95
        }

    def create_persistent_session(self, user_id: int, google_auth_data: Dict[str, Any]) -> GoogleAuth:
        """
        Create a new persistent OAuth session for an admin user.
        
        Args:
            user_id: ID of the admin user
            google_auth_data: Dictionary containing OAuth data from Google
            
        Returns:
            GoogleAuth: Created authentication record
            
        Raises:
            OAuthPersistenceError: If user is not admin or creation fails
        """
        try:
            # Verify user is admin
            user = User.query.get(user_id)
            if not user or not user.is_admin:
                raise OAuthPersistenceError("Only admin users can create persistent OAuth sessions")
            
            # Check if user already has a GoogleAuth record
            existing_auth = GoogleAuth.query.filter_by(user_id=user_id).first()
            if existing_auth:
                # Update existing record instead of creating new one
                return self.update_persistent_session(existing_auth.id, google_auth_data)
            
            # Generate unique persistent session ID
            persistent_session_id = secrets.token_urlsafe(32)
            
            # Create new GoogleAuth record with persistence enabled
            auth = GoogleAuth(
                user_id=user_id,
                google_user_id=google_auth_data.get('google_user_id'),
                email=google_auth_data.get('email'),
                name=google_auth_data.get('name'),
                picture=google_auth_data.get('picture'),
                access_token=google_auth_data.get('access_token'),
                refresh_token=google_auth_data.get('refresh_token'),
                token_expires_at=google_auth_data.get('token_expires_at'),
                scope=google_auth_data.get('scope', ''),
                persistent_session_id=persistent_session_id,
                last_activity_at=datetime.utcnow(),
                quota_warning_level='none'
            )
            
            db.session.add(auth)
            db.session.commit()
            
            self.logger.info(f"Created persistent OAuth session for admin user {user_id}")
            
            # Initial storage quota check
            self.check_storage_quota(auth.id)
            
            return auth
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to create persistent session: {e}")
            raise OAuthPersistenceError(f"Failed to create persistent session: {e}")

    def update_persistent_session(self, auth_id: int, google_auth_data: Dict[str, Any]) -> GoogleAuth:
        """
        Update an existing persistent OAuth session with new token data.
        
        Args:
            auth_id: ID of the GoogleAuth record
            google_auth_data: Updated OAuth data from Google
            
        Returns:
            GoogleAuth: Updated authentication record
        """
        try:
            auth = GoogleAuth.query.get(auth_id)
            if not auth:
                raise OAuthPersistenceError("OAuth session not found")
            
            # Update token information
            auth.access_token = google_auth_data.get('access_token', auth.access_token)
            auth.refresh_token = google_auth_data.get('refresh_token', auth.refresh_token)
            auth.token_expires_at = google_auth_data.get('token_expires_at', auth.token_expires_at)
            auth.scope = google_auth_data.get('scope', auth.scope)
            
            # Update user information if provided
            if 'email' in google_auth_data:
                auth.email = google_auth_data['email']
            if 'name' in google_auth_data:
                auth.name = google_auth_data['name']
            if 'picture' in google_auth_data:
                auth.picture = google_auth_data['picture']
            
            # Reset failure counters and reactivate if needed
            auth.refresh_attempts = 0
            auth.is_active = True
            auth.deactivated_reason = None
            auth.deactivated_at = None
            auth.last_activity_at = datetime.utcnow()
            
            # Generate new session ID if not present
            if not auth.persistent_session_id:
                auth.persistent_session_id = secrets.token_urlsafe(32)
            
            db.session.commit()
            
            self.logger.info(f"Updated persistent OAuth session {auth_id}")
            return auth
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to update persistent session: {e}")
            raise OAuthPersistenceError(f"Failed to update persistent session: {e}")

    def refresh_token_if_needed(self, auth_id: int) -> TokenRefreshResult:
        """
        Refresh OAuth token if it's expired or expiring soon.
        
        Args:
            auth_id: ID of the GoogleAuth record
            
        Returns:
            TokenRefreshResult: Result of the refresh operation
        """
        try:
            auth = GoogleAuth.query.get(auth_id)
            if not auth:
                return TokenRefreshResult(
                    success=False,
                    message="OAuth session not found",
                    error_code="SESSION_NOT_FOUND"
                )
            
            if not auth.is_active:
                return TokenRefreshResult(
                    success=False,
                    message="OAuth session is deactivated",
                    error_code="SESSION_DEACTIVATED"
                )
            
            # Check if token needs refresh
            needs_refresh = (
                auth.token_expires_at and 
                auth.token_expires_at <= (datetime.utcnow() + timedelta(seconds=self.token_expiry_threshold))
            )
            
            if not needs_refresh:
                return TokenRefreshResult(
                    success=True,
                    message="Token refresh not needed",
                    refresh_attempts=auth.refresh_attempts
                )
            
            # Attempt token refresh
            return self._perform_token_refresh(auth)
            
        except Exception as e:
            self.logger.error(f"Error checking token refresh for auth {auth_id}: {e}")
            return TokenRefreshResult(
                success=False,
                message=f"Error during token refresh check: {e}",
                error_code="REFRESH_CHECK_ERROR"
            )

    def _perform_token_refresh(self, auth: GoogleAuth) -> TokenRefreshResult:
        """
        Perform the actual token refresh using Google OAuth2 library.
        
        Args:
            auth: GoogleAuth record to refresh
            
        Returns:
            TokenRefreshResult: Result of the refresh operation
        """
        try:
            # Create credentials object
            credentials = google.oauth2.credentials.Credentials(
                token=auth.access_token,
                refresh_token=auth.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=current_app.config.get('GOOGLE_CLIENT_ID'),
                client_secret=current_app.config.get('GOOGLE_CLIENT_SECRET'),
                scopes=auth.scope.split(' ') if auth.scope else []
            )
            
            # Perform refresh
            request_obj = google.auth.transport.requests.Request()
            credentials.refresh(request_obj)
            
            # Update database record
            auth.access_token = credentials.token
            auth.token_expires_at = credentials.expiry
            auth.last_refresh_at = datetime.utcnow()
            auth.refresh_attempts = 0  # Reset on successful refresh
            auth.last_activity_at = datetime.utcnow()
            
            db.session.commit()
            
            self.logger.info(f"Successfully refreshed token for auth {auth.id}")
            
            return TokenRefreshResult(
                success=True,
                message="Token refreshed successfully",
                new_access_token=credentials.token,
                new_expires_at=credentials.expiry,
                refresh_attempts=0
            )
            
        except Exception as e:
            # Handle refresh failure
            auth.refresh_attempts += 1
            auth.last_refresh_at = datetime.utcnow()
            
            # Deactivate if too many failures
            if auth.refresh_attempts >= self.max_refresh_failures:
                auth.is_active = False
                auth.deactivated_reason = f"Too many refresh failures ({auth.refresh_attempts})"
                auth.deactivated_at = datetime.utcnow()
                
                self.logger.error(f"Deactivated auth {auth.id} due to refresh failures")
            
            db.session.commit()
            
            self.logger.error(f"Failed to refresh token for auth {auth.id}: {e}")
            
            return TokenRefreshResult(
                success=False,
                message=f"Token refresh failed: {e}",
                refresh_attempts=auth.refresh_attempts,
                error_code="REFRESH_FAILED"
            )

    def check_storage_quota(self, auth_id: int) -> Optional[StorageQuotaInfo]:
        """
        Check Google Drive storage quota for the authenticated user.
        
        Args:
            auth_id: ID of the GoogleAuth record
            
        Returns:
            StorageQuotaInfo: Storage quota information or None if failed
        """
        try:
            auth = GoogleAuth.query.get(auth_id)
            if not auth or not auth.is_active:
                return None
            
            # Check if we need to refresh token first
            if auth.token_expires_at <= datetime.utcnow():
                refresh_result = self.refresh_token_if_needed(auth_id)
                if not refresh_result.success:
                    self.logger.error(f"Cannot check storage quota: token refresh failed")
                    return None
                # Reload auth record after refresh
                auth = GoogleAuth.query.get(auth_id)
            
            # Build Google Drive service
            credentials = google.oauth2.credentials.Credentials(
                token=auth.access_token,
                refresh_token=auth.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=current_app.config.get('GOOGLE_CLIENT_ID'),
                client_secret=current_app.config.get('GOOGLE_CLIENT_SECRET'),
                scopes=auth.scope.split(' ') if auth.scope else []
            )
            
            service = build('drive', 'v3', credentials=credentials)
            
            # Get storage quota information
            about = service.about().get(fields='storageQuota').execute()
            quota = about.get('storageQuota', {})
            
            total_quota = int(quota.get('limit', 0))
            used_quota = int(quota.get('usage', 0))
            usage_percentage = (used_quota / total_quota * 100) if total_quota > 0 else 0
            warning_level = self._determine_warning_level(usage_percentage)
            
            # Update database record
            auth.drive_quota_total = total_quota
            auth.drive_quota_used = used_quota
            auth.last_quota_check = datetime.utcnow()
            
            # Update warning level if changed
            if warning_level != auth.quota_warning_level:
                self._handle_warning_level_change(auth, warning_level)
            
            db.session.commit()
            
            quota_info = StorageQuotaInfo(
                total_quota=total_quota,
                used_quota=used_quota,
                usage_percentage=round(usage_percentage, 2),
                warning_level=warning_level,
                last_check=auth.last_quota_check
            )
            
            self.logger.info(f"Updated storage quota for auth {auth_id}: {usage_percentage:.1f}% used")
            return quota_info
            
        except Exception as e:
            self.logger.error(f"Failed to check storage quota for auth {auth_id}: {e}")
            return None

    def _determine_warning_level(self, usage_percentage: float) -> str:
        """Determine storage warning level based on usage percentage."""
        if usage_percentage >= self.storage_thresholds['critical']:
            return 'critical'
        elif usage_percentage >= self.storage_thresholds['high']:
            return 'high'
        elif usage_percentage >= self.storage_thresholds['medium']:
            return 'medium'
        elif usage_percentage >= self.storage_thresholds['low']:
            return 'low'
        else:
            return 'none'

    def _handle_warning_level_change(self, auth: GoogleAuth, new_warning_level: str):
        """Handle storage warning level changes."""
        old_level = auth.quota_warning_level
        auth.quota_warning_level = new_warning_level
        
        # Add warning to history
        if not auth.quota_warnings_sent:
            auth.quota_warnings_sent = []
        
        warning_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'old_level': old_level,
            'new_level': new_warning_level,
            'usage_percentage': auth.calculate_usage_percentage() if hasattr(auth, 'calculate_usage_percentage') else 0
        }
        
        auth.quota_warnings_sent.append(warning_entry)
        
        # Keep only last 10 warnings
        if len(auth.quota_warnings_sent) > 10:
            auth.quota_warnings_sent = auth.quota_warnings_sent[-10:]
        
        self.logger.warning(f"Storage warning level changed from {old_level} to {new_warning_level} for auth {auth.id}")

    def get_active_sessions(self) -> List[GoogleAuth]:
        """Get all active persistent OAuth sessions."""
        try:
            return GoogleAuth.query.filter_by(is_active=True).all()
        except Exception as e:
            self.logger.error(f"Failed to get active sessions: {e}")
            return []

    def deactivate_session(self, auth_id: int, reason: str) -> bool:
        """
        Deactivate a persistent OAuth session.
        
        Args:
            auth_id: ID of the GoogleAuth record
            reason: Reason for deactivation
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            auth = GoogleAuth.query.get(auth_id)
            if not auth:
                return False
            
            auth.is_active = False
            auth.deactivated_reason = reason
            auth.deactivated_at = datetime.utcnow()
            
            db.session.commit()
            
            self.logger.info(f"Deactivated OAuth session {auth_id}: {reason}")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to deactivate session {auth_id}: {e}")
            return False

    def get_session_status(self, auth_id: int) -> Dict[str, Any]:
        """
        Get comprehensive status information for an OAuth session.
        
        Args:
            auth_id: ID of the GoogleAuth record
            
        Returns:
            Dict: Session status information
        """
        try:
            auth = GoogleAuth.query.get(auth_id)
            if not auth:
                return {'error': 'Session not found'}
            
            # Calculate time until token expiry
            time_until_expiry = None
            if auth.token_expires_at:
                delta = auth.token_expires_at - datetime.utcnow()
                time_until_expiry = delta.total_seconds() if delta.total_seconds() > 0 else 0
            
            return {
                'auth_id': auth.id,
                'user_id': auth.user_id,
                'is_active': auth.is_active,
                'is_persistent': getattr(auth, 'is_persistent', True),
                'auto_refresh_enabled': getattr(auth, 'auto_refresh_enabled', True),
                'persistent_session_id': getattr(auth, 'persistent_session_id', None),
                'token_expires_at': auth.token_expires_at.isoformat() if auth.token_expires_at else None,
                'time_until_expiry_seconds': time_until_expiry,
                'last_refresh_at': getattr(auth, 'last_refresh_at', None),
                'refresh_attempts': getattr(auth, 'refresh_attempts', 0),
                'last_activity_at': getattr(auth, 'last_activity_at', None),
                'storage': {
                    'quota_total': getattr(auth, 'drive_quota_total', None),
                    'quota_used': getattr(auth, 'drive_quota_used', None),
                    'usage_percentage': getattr(auth, 'calculate_usage_percentage', lambda: 0)(),
                    'warning_level': getattr(auth, 'quota_warning_level', 'none'),
                    'last_quota_check': getattr(auth, 'last_quota_check', None)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get session status for auth {auth_id}: {e}")
            return {'error': str(e)}


# Global service instance
oauth_persistence_service = OAuthPersistenceService()