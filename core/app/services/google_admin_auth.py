"""
Google Admin Authentication Service

This service handles OAuth 2.0 authentication for admin users to access
their personal Google Drive, meeting functional requirements API-05f, API-12, and API-12a.

The service provides:
- Admin-only OAuth authentication flow
- Persistent token management with auto-refresh
- Secure credential storage and retrieval
- Session management for long-term authentication
"""

import os
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from flask import current_app, session, request, redirect, url_for
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.models.temp import User, GoogleAuth
from app.extensions import db
import logging

logger = logging.getLogger(__name__)

class GoogleAdminAuthService:
    """
    Service for managing Google OAuth authentication for admin users.
    
    This service ensures only admin users can authenticate with Google Drive
    and maintains persistent authentication sessions per API-12a requirements.
    """
    
    def __init__(self):
        """Initialize the Google Admin Auth Service with OAuth configuration."""
        self.client_id = current_app.config.get('GOOGLE_ADMIN_OAUTH_CLIENT_ID')
        self.client_secret = current_app.config.get('GOOGLE_ADMIN_OAUTH_CLIENT_SECRET')
        self.redirect_uri = current_app.config.get('GOOGLE_ADMIN_OAUTH_REDIRECT_URI')
        
        # Required OAuth scopes for Google Drive and Docs access
        self.scopes = [
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/documents',
            'https://www.googleapis.com/auth/drive.metadata.readonly'
        ]
        
        # Validate configuration
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.error("Google OAuth configuration incomplete. Check environment variables.")
    
    def initiate_admin_oauth_flow(self, admin_user_id: int) -> str:
        """
        Initiate OAuth flow for admin user.
        
        Args:
            admin_user_id: ID of the admin user requesting authentication
            
        Returns:
            str: Authorization URL for user to visit
            
        Raises:
            ValueError: If user is not admin or configuration is invalid
        """
        # Validate admin privileges
        if not self._is_admin_user(admin_user_id):
            raise ValueError("Only admin users can authenticate with Google Drive")
        
        # Validate OAuth configuration
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Google OAuth configuration not properly set")
        
        try:
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            # Generate authorization URL with offline access for refresh tokens
            authorization_url, state = flow.authorization_url(
                access_type='offline',        # Request refresh token
                include_granted_scopes='true', # Incremental auth
                prompt='consent'              # Force consent to ensure refresh token
            )
            
            # Store state and user ID in session for verification
            session['oauth_state'] = state
            session['admin_user_id'] = admin_user_id
            session['oauth_initiated_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"Initiated OAuth flow for admin user {admin_user_id}")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Failed to initiate OAuth flow for user {admin_user_id}: {str(e)}")
            raise ValueError(f"Failed to initiate Google authentication: {str(e)}")
    
    def handle_oauth_callback(self, authorization_code: str, state: str) -> Credentials:
        """
        Handle OAuth callback and store credentials.
        
        Args:
            authorization_code: Authorization code from Google
            state: State parameter for CSRF protection
            
        Returns:
            Credentials: Google OAuth credentials
            
        Raises:
            ValueError: If callback handling fails or state is invalid
        """
        try:
            # Verify state parameter for CSRF protection
            if session.get('oauth_state') != state:
                raise ValueError("Invalid OAuth state - possible CSRF attack")
            
            # Get admin user ID from session
            admin_user_id = session.get('admin_user_id')
            if not admin_user_id or not self._is_admin_user(admin_user_id):
                raise ValueError("Invalid admin user session")
            
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            # Exchange authorization code for credentials
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Get user info from Google
            user_info = self._get_google_user_info(credentials)
            
            # Store credentials in database
            self._store_admin_credentials(admin_user_id, credentials, user_info)
            
            # Clear session data
            session.pop('oauth_state', None)
            session.pop('admin_user_id', None)
            session.pop('oauth_initiated_at', None)
            
            logger.info(f"Successfully stored OAuth credentials for admin user {admin_user_id}")
            return credentials
            
        except Exception as e:
            logger.error(f"OAuth callback failed: {str(e)}")
            raise ValueError(f"Authentication failed: {str(e)}")
    
    def get_admin_credentials(self, user_id: int = None) -> Optional[Credentials]:
        """
        Get valid admin credentials with automatic refresh.
        
        Args:
            user_id: Specific admin user ID (optional, uses first admin if not provided)
            
        Returns:
            Credentials or None: Valid Google OAuth credentials or None if not available
        """
        try:
            # Get the admin user
            if user_id:
                admin_user = User.query.filter_by(id=user_id, is_admin=True).first()
            else:
                admin_user = self._get_admin_user()
            
            if not admin_user:
                logger.warning(f"No admin user found for ID: {user_id}")
                return None
            
            # Get Google auth record
            google_auth = GoogleAuth.query.filter_by(
                user_id=admin_user.id,
                is_active=True
            ).first()
            
            if not google_auth:
                logger.warning(f"No active Google auth found for admin user {admin_user.id}")
                return None
            
            # Create credentials object
            credentials = Credentials(
                token=google_auth.access_token,
                refresh_token=google_auth.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=google_auth.scope.split(',') if google_auth.scope else self.scopes
            )
            
            # Check if token needs refresh
            if google_auth.is_token_expired():
                logger.info(f"Token expired for admin user {admin_user.id}, attempting refresh...")
                
                if self._refresh_credentials(google_auth, credentials):
                    logger.info(f"Successfully refreshed token for admin user {admin_user.id}")
                else:
                    logger.error(f"Failed to refresh token for admin user {admin_user.id}")
                    return None
            
            # Update activity timestamp
            google_auth.update_activity()
            db.session.commit()
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to get admin credentials: {str(e)}")
            return None
    
    def get_auth_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get authentication status for admin user.
        
        Args:
            user_id: ID of the admin user
            
        Returns:
            dict: Authentication status information
        """
        try:
            # Validate admin user
            if not self._is_admin_user(user_id):
                return {
                    'authenticated': False,
                    'error': 'Admin privileges required'
                }
            
            # Get Google auth record
            google_auth = GoogleAuth.query.filter_by(
                user_id=user_id,
                is_active=True
            ).first()
            
            if not google_auth:
                return {
                    'authenticated': False,
                    'message': 'Google Drive authentication required',
                    'auth_url_endpoint': '/auth/google/admin'
                }
            
            # Get credentials and check validity
            credentials = self.get_admin_credentials(user_id)
            
            if credentials and not credentials.expired:
                return {
                    'authenticated': True,
                    'message': 'Google Drive authentication is active',
                    'oauth_status': google_auth.to_dict(include_tokens=False),
                    'scopes': credentials.scopes
                }
            else:
                return {
                    'authenticated': False,
                    'message': 'Google Drive authentication expired',
                    'auth_url_endpoint': '/auth/google/admin',
                    'oauth_status': google_auth.to_dict(include_tokens=False)
                }
                
        except Exception as e:
            logger.error(f"Failed to get auth status for user {user_id}: {str(e)}")
            return {
                'authenticated': False,
                'error': 'Failed to check authentication status'
            }
    
    def revoke_admin_auth(self, user_id: int, reason: str = "Manual revocation") -> bool:
        """
        Revoke admin Google authentication.
        
        Args:
            user_id: ID of the admin user
            reason: Reason for revocation
            
        Returns:
            bool: True if revocation successful
        """
        try:
            # Validate admin user
            if not self._is_admin_user(user_id):
                logger.warning(f"Attempted to revoke auth for non-admin user {user_id}")
                return False
            
            # Get Google auth record
            google_auth = GoogleAuth.query.filter_by(
                user_id=user_id,
                is_active=True
            ).first()
            
            if not google_auth:
                logger.info(f"No active Google auth found for user {user_id}")
                return True  # Already revoked
            
            # Try to revoke with Google (optional, may fail if already expired)
            try:
                credentials = Credentials(
                    token=google_auth.access_token,
                    refresh_token=google_auth.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                credentials.revoke(Request())
                logger.info(f"Successfully revoked Google credentials for user {user_id}")
            except Exception as revoke_error:
                logger.warning(f"Failed to revoke with Google (proceeding anyway): {revoke_error}")
            
            # Deactivate in database
            google_auth.deactivate(reason)
            db.session.commit()
            
            logger.info(f"Deactivated Google auth for admin user {user_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke admin auth for user {user_id}: {str(e)}")
            return False
    
    def _is_admin_user(self, user_id: int) -> bool:
        """Check if user has admin privileges."""
        user = User.query.get(user_id)
        return user and user.is_admin
    
    def _get_admin_user(self) -> Optional[User]:
        """Get first active admin user with Google auth."""
        return User.query.filter_by(is_admin=True).first()
    
    def _get_google_user_info(self, credentials: Credentials) -> Dict[str, Any]:
        """
        Get user information from Google using OAuth credentials.
        
        Args:
            credentials: Google OAuth credentials
            
        Returns:
            dict: User information from Google
        """
        try:
            # Build People API service
            service = build('people', 'v1', credentials=credentials)
            
            # Get user's profile information
            profile = service.people().get(
                resourceName='people/me',
                personFields='names,emailAddresses,photos'
            ).execute()
            
            # Extract relevant information
            user_info = {
                'google_user_id': profile.get('resourceName', '').replace('people/', ''),
                'email': None,
                'name': None,
                'picture': None
            }
            
            # Get email
            emails = profile.get('emailAddresses', [])
            if emails:
                user_info['email'] = emails[0].get('value')
            
            # Get name
            names = profile.get('names', [])
            if names:
                user_info['name'] = names[0].get('displayName')
            
            # Get profile picture
            photos = profile.get('photos', [])
            if photos:
                user_info['picture'] = photos[0].get('url')
            
            return user_info
            
        except Exception as e:
            logger.warning(f"Failed to get Google user info: {str(e)}")
            return {
                'google_user_id': None,
                'email': None,
                'name': None,
                'picture': None
            }
    
    def _store_admin_credentials(self, user_id: int, credentials: Credentials, user_info: Dict[str, Any]):
        """
        Store admin credentials in database with enhanced persistence features.
        
        Args:
            user_id: ID of the admin user
            credentials: Google OAuth credentials
            user_info: User information from Google
        """
        try:
            # Remove existing Google auth for this admin
            GoogleAuth.query.filter_by(user_id=user_id).delete()
            
            # Generate persistent session ID
            persistent_session_id = secrets.token_urlsafe(32)
            
            # Calculate token expiration (Google tokens typically expire in 1 hour)
            expires_at = datetime.utcnow() + timedelta(seconds=3600)
            if credentials.expiry:
                expires_at = credentials.expiry.replace(tzinfo=None)
            
            # Create new Google auth record with persistence features
            google_auth = GoogleAuth(
                user_id=user_id,
                google_user_id=user_info.get('google_user_id'),
                email=user_info.get('email'),
                name=user_info.get('name'),
                picture=user_info.get('picture'),
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_expires_at=expires_at,
                scope=','.join(credentials.scopes or self.scopes),
                
                # Persistence settings (API-12a compliance)
                is_persistent=True,
                auto_refresh_enabled=True,
                persistent_session_id=persistent_session_id,
                last_refresh_at=None,
                refresh_attempts=0,
                max_refresh_failures=5,
                
                # Activity tracking
                last_activity_at=datetime.utcnow(),
                is_active=True,
                
                # Storage monitoring (will be updated by background services)
                drive_quota_total=None,
                drive_quota_used=None,
                last_quota_check=None,
                quota_warning_level='none',
                quota_warnings_sent=[],
                
                # Timestamps
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(google_auth)
            db.session.commit()
            
            logger.info(f"Stored persistent Google credentials for admin user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to store admin credentials: {str(e)}")
            db.session.rollback()
            raise ValueError(f"Failed to store authentication: {str(e)}")
    
    def _refresh_credentials(self, google_auth: GoogleAuth, credentials: Credentials) -> bool:
        """
        Refresh OAuth credentials and update database.
        
        Args:
            google_auth: GoogleAuth database record
            credentials: Current credentials object
            
        Returns:
            bool: True if refresh successful
        """
        try:
            # Check if we have a refresh token
            if not google_auth.refresh_token:
                logger.error(f"No refresh token available for user {google_auth.user_id}")
                google_auth.deactivate("No refresh token available")
                db.session.commit()
                return False
            
            # Attempt refresh
            request_obj = Request()
            credentials.refresh(request_obj)
            
            # Update stored tokens
            google_auth.access_token = credentials.token
            if credentials.expiry:
                google_auth.token_expires_at = credentials.expiry.replace(tzinfo=None)
            else:
                google_auth.token_expires_at = datetime.utcnow() + timedelta(seconds=3600)
            
            # Update refresh tracking
            google_auth.last_refresh_at = datetime.utcnow()
            google_auth.refresh_attempts = 0  # Reset on success
            google_auth.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Successfully refreshed credentials for user {google_auth.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh credentials for user {google_auth.user_id}: {str(e)}")
            
            # Update failure tracking
            google_auth.refresh_attempts += 1
            google_auth.updated_at = datetime.utcnow()
            
            # Deactivate if too many failures
            if google_auth.refresh_attempts >= google_auth.max_refresh_failures:
                google_auth.deactivate(f"Too many refresh failures: {str(e)}")
                logger.warning(f"Deactivated Google auth for user {google_auth.user_id} due to repeated refresh failures")
            
            db.session.commit()
            return False
    
    def get_storage_info(self, user_id: int) -> Dict[str, Any]:
        """
        Get Google Drive storage information for admin user.
        
        Args:
            user_id: ID of the admin user
            
        Returns:
            dict: Storage information and usage statistics
        """
        try:
            credentials = self.get_admin_credentials(user_id)
            if not credentials:
                return {'error': 'Authentication required'}
            
            # Build Drive API service
            service = build('drive', 'v3', credentials=credentials)
            
            # Get storage quota information
            about = service.about().get(fields='storageQuota').execute()
            quota = about.get('storageQuota', {})
            
            # Update database with current quota info
            google_auth = GoogleAuth.query.filter_by(
                user_id=user_id,
                is_active=True
            ).first()
            
            if google_auth:
                google_auth.drive_quota_total = int(quota.get('limit', 0))
                google_auth.drive_quota_used = int(quota.get('usage', 0))
                google_auth.last_quota_check = datetime.utcnow()
                google_auth.quota_warning_level = google_auth.get_storage_warning_level()
                db.session.commit()
            
            # Format response
            total_bytes = int(quota.get('limit', 0))
            used_bytes = int(quota.get('usage', 0))
            usage_percentage = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0
            
            return {
                'quota_total': total_bytes,
                'quota_used': used_bytes,
                'quota_available': total_bytes - used_bytes,
                'usage_percentage': round(usage_percentage, 2),
                'warning_level': google_auth.get_storage_warning_level() if google_auth else 'none',
                'formatted_quota': {
                    'total': self._format_bytes(total_bytes),
                    'used': self._format_bytes(used_bytes),
                    'available': self._format_bytes(total_bytes - used_bytes)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage info for user {user_id}: {str(e)}")
            return {'error': f'Failed to get storage information: {str(e)}'}
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes value in human-readable format."""
        if bytes_value == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                if unit == 'B':
                    return f"{int(bytes_value)} {unit}"
                else:
                    return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"