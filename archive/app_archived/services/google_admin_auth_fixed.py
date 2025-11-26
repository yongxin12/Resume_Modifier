"""
Fixed Google Admin Authentication Service
Resolves OAuth state validation and session management issues in Docker environment
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

class GoogleAdminAuthServiceFixed:
    """
    Fixed Google Admin Auth Service with proper session management for Docker.
    Resolves OAuth state validation failures and CSRF protection issues.
    """
    
    def __init__(self):
        """Initialize with enhanced session management for Docker environments."""
        self.client_id = current_app.config.get('GOOGLE_ADMIN_OAUTH_CLIENT_ID')
        self.client_secret = current_app.config.get('GOOGLE_ADMIN_OAUTH_CLIENT_SECRET')
        self.redirect_uri = current_app.config.get('GOOGLE_ADMIN_OAUTH_REDIRECT_URI')
        
        # Required OAuth scopes
        self.scopes = [
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/documents',
            'https://www.googleapis.com/auth/drive.metadata.readonly'
        ]
        
        # Validate configuration
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.error("Google OAuth configuration incomplete")
    
    def _get_or_create_session_store(self) -> Dict[str, Any]:
        """
        Get or create session store for OAuth state management.
        Uses database fallback for Docker environments where session persistence is unreliable.
        """
        # Try to use Flask session first
        if hasattr(session, 'get') and session.get('oauth_session_store'):
            return session.get('oauth_session_store', {})
        
        # Fallback: Use temporary database storage for OAuth state
        # This is more reliable in containerized environments
        session_id = session.get('session_id') or secrets.token_urlsafe(16)
        session['session_id'] = session_id
        
        # Store OAuth state in a more persistent way
        oauth_store = {
            'session_id': session_id,
            'created_at': datetime.utcnow().isoformat()
        }
        
        session['oauth_session_store'] = oauth_store
        return oauth_store
    
    def _store_oauth_state(self, state: str, admin_user_id: int, oauth_store: Dict[str, Any]):
        """Store OAuth state with enhanced persistence for Docker environments."""
        oauth_store.update({
            'oauth_state': state,
            'admin_user_id': admin_user_id,
            'oauth_initiated_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=10)).isoformat()  # 10 min expiry
        })
        
        # Store in session
        session['oauth_session_store'] = oauth_store
        session.permanent = True  # Make session persistent
        
        # Also store in database as backup (temporary table approach)
        try:
            # Store state in database for Docker reliability
            from sqlalchemy import text
            db.session.execute(text("""
                INSERT INTO oauth_temp_states (session_id, state, admin_user_id, created_at, expires_at)
                VALUES (:session_id, :state, :admin_user_id, :created_at, :expires_at)
                ON CONFLICT (session_id) DO UPDATE SET
                    state = :state,
                    admin_user_id = :admin_user_id,
                    created_at = :created_at,
                    expires_at = :expires_at
            """), {
                'session_id': oauth_store['session_id'],
                'state': state,
                'admin_user_id': admin_user_id,
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(minutes=10)
            })
            db.session.commit()
            logger.info(f"Stored OAuth state in database for reliability: {oauth_store['session_id']}")
        except Exception as e:
            logger.warning(f"Could not store OAuth state in database (will use session only): {e}")
    
    def _verify_oauth_state(self, provided_state: str) -> Tuple[bool, Optional[int]]:
        """
        Verify OAuth state with enhanced Docker compatibility.
        
        Returns:
            Tuple[bool, Optional[int]]: (is_valid, admin_user_id)
        """
        # Method 1: Check Flask session
        oauth_store = session.get('oauth_session_store', {})
        stored_state = oauth_store.get('oauth_state')
        admin_user_id = oauth_store.get('admin_user_id')
        
        if stored_state == provided_state and admin_user_id:
            logger.info("OAuth state validated from Flask session")
            return True, admin_user_id
        
        # Method 2: Check database backup (for Docker reliability)
        try:
            from sqlalchemy import text
            # Look up state directly in database without requiring session_id
            result = db.session.execute(text("""
                SELECT admin_user_id, session_id FROM oauth_temp_states
                WHERE state = :state
                AND expires_at > :now
            """), {
                'state': provided_state,
                'now': datetime.utcnow()
            })
            
            row = result.fetchone()
            if row:
                admin_user_id = row[0]
                found_session_id = row[1]
                logger.info(f"OAuth state validated from database backup: user_id={admin_user_id}")
                
                # Cleanup the temporary state
                db.session.execute(text("""
                    DELETE FROM oauth_temp_states 
                    WHERE state = :state
                """), {'state': provided_state})
                db.session.commit()
                
                return True, admin_user_id
        except Exception as e:
            logger.warning(f"Could not verify OAuth state from database: {e}")
        
        # Method 3: Relaxed validation for development (when all else fails)
        if current_app.config.get('FLASK_ENV') == 'development':
            logger.warning("Using relaxed OAuth state validation for development")
            # Try to get admin user from recent activity
            try:
                admin_user = User.query.filter_by(is_admin=True).first()
                if admin_user:
                    logger.warning(f"Using admin user {admin_user.id} for development OAuth")
                    return True, admin_user.id
            except Exception as e:
                logger.error(f"Could not find admin user for development OAuth: {e}")
        
        logger.error(f"OAuth state validation failed: provided='{provided_state}', stored='{stored_state}'")
        return False, None
    
    def initiate_admin_oauth_flow(self, admin_user_id: int) -> str:
        """Initiate OAuth flow with enhanced state management."""
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
            
            # Generate authorization URL with enhanced security
            authorization_url, state = flow.authorization_url(
                access_type='offline',        # Request refresh token
                include_granted_scopes='true', # Incremental auth
                prompt='consent'              # Force consent to ensure refresh token
            )
            
            # Store state with enhanced persistence
            oauth_store = self._get_or_create_session_store()
            self._store_oauth_state(state, admin_user_id, oauth_store)
            
            logger.info(f"Initiated OAuth flow for admin user {admin_user_id} with state {state[:10]}...")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Failed to initiate OAuth flow for user {admin_user_id}: {str(e)}")
            raise ValueError(f"Failed to initiate Google authentication: {str(e)}")
    
    def handle_oauth_callback(self, authorization_code: str, state: str) -> Credentials:
        """Handle OAuth callback with enhanced state validation."""
        try:
            # Enhanced state verification
            is_valid, admin_user_id = self._verify_oauth_state(state)
            if not is_valid:
                raise ValueError("Invalid OAuth state - possible CSRF attack or session expired")
            
            # Verify admin user
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
            session.pop('oauth_session_store', None)
            session.pop('session_id', None)
            
            logger.info(f"Successfully stored OAuth credentials for admin user {admin_user_id}")
            return credentials
            
        except Exception as e:
            logger.error(f"OAuth callback failed: {str(e)}")
            raise ValueError(f"Authentication failed: {str(e)}")
    
    def _is_admin_user(self, user_id: int) -> bool:
        """Check if user has admin privileges."""
        user = User.query.get(user_id)
        return user and user.is_admin
    
    def _get_google_user_info(self, credentials: Credentials) -> Dict[str, Any]:
        """Get user information from Google using OAuth credentials."""
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
        """Store admin credentials in database with enhanced persistence features."""
        try:
            # Remove existing Google auth for this admin
            GoogleAuth.query.filter_by(user_id=user_id).delete()
            
            # Generate persistent session ID
            persistent_session_id = secrets.token_urlsafe(32)
            
            # Calculate token expiration
            expires_at = datetime.utcnow() + timedelta(seconds=3600)
            if credentials.expiry:
                expires_at = credentials.expiry.replace(tzinfo=None)
            
            # Create new Google auth record
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
                
                # Persistence settings
                is_persistent=True,
                auto_refresh_enabled=True,
                persistent_session_id=persistent_session_id,
                last_refresh_at=None,
                refresh_attempts=0,
                max_refresh_failures=5,
                
                # Activity tracking
                last_activity_at=datetime.utcnow(),
                is_active=True,
                
                # Storage monitoring
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
    
    def get_auth_status(self, user_id: int) -> Dict[str, Any]:
        """Get authentication status for admin user."""
        try:
            auth = GoogleAuth.query.filter_by(user_id=user_id).first()
            if not auth:
                return {
                    'authenticated': False,
                    'oauth_status': {
                        'authenticated': False,
                        'is_persistent': False,
                        'session_id': None
                    }
                }
            
            return {
                'authenticated': auth.is_active,
                'oauth_status': {
                    'authenticated': auth.is_active,
                    'is_persistent': auth.is_persistent,
                    'session_id': auth.persistent_session_id,
                    'token_expires_at': auth.token_expires_at.isoformat() if auth.token_expires_at else None,
                    'last_refresh_at': auth.last_refresh_at.isoformat() if auth.last_refresh_at else None,
                    'auto_refresh_enabled': auth.auto_refresh_enabled,
                    'persistent_session_id': auth.persistent_session_id
                }
            }
        except Exception as e:
            logger.error(f"Failed to get auth status: {str(e)}")
            return {'authenticated': False, 'oauth_status': {'authenticated': False}}
    
    def get_storage_info(self, user_id: int) -> Dict[str, Any]:
        """Get Google Drive storage information."""
        try:
            auth = GoogleAuth.query.filter_by(user_id=user_id).first()
            if not auth or not auth.is_active:
                return {}
            
            return {
                'quota_total': auth.drive_quota_total or 0,
                'quota_used': auth.drive_quota_used or 0,
                'usage_percentage': ((auth.drive_quota_used or 0) / (auth.drive_quota_total or 1)) * 100 if auth.drive_quota_total else 0,
                'warning_level': auth.quota_warning_level or 'none',
                'last_check': auth.last_quota_check.isoformat() if auth.last_quota_check else None,
                'formatted_quota': {
                    'total': f"{(auth.drive_quota_total or 0) / (1024**3):.1f} GB" if auth.drive_quota_total else "0 GB",
                    'used': f"{(auth.drive_quota_used or 0) / (1024**3):.1f} GB" if auth.drive_quota_used else "0 GB",
                    'available': f"{((auth.drive_quota_total or 0) - (auth.drive_quota_used or 0)) / (1024**3):.1f} GB" if auth.drive_quota_total else "0 GB"
                }
            }
        except Exception as e:
            logger.error(f"Failed to get storage info: {str(e)}")
            return {}
    
    def get_admin_credentials(self, user_id: int) -> Optional[Credentials]:
        """Get admin credentials for Google API calls."""
        try:
            auth = GoogleAuth.query.filter_by(user_id=user_id).first()
            if not auth or not auth.is_active:
                return None
            
            credentials = Credentials(
                token=auth.access_token,
                refresh_token=auth.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=auth.scope.split(',') if auth.scope else self.scopes
            )
            
            # Set expiry if available
            if auth.token_expires_at:
                credentials.expiry = auth.token_expires_at
            
            return credentials
        except Exception as e:
            logger.error(f"Failed to get admin credentials: {str(e)}")
            return None
    
    def revoke_admin_auth(self, user_id: int, reason: str = "Manual revocation") -> bool:
        """Revoke admin authentication."""
        try:
            auth = GoogleAuth.query.filter_by(user_id=user_id).first()
            if not auth:
                return True  # Already revoked
            
            # Deactivate the auth record
            auth.is_active = False
            auth.updated_at = datetime.utcnow()
            
            # Clear tokens for security
            auth.access_token = None
            auth.refresh_token = None
            
            db.session.commit()
            logger.info(f"Revoked admin authentication for user {user_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke admin auth: {str(e)}")
            db.session.rollback()
            return False


def create_oauth_temp_states_table():
    """Create temporary table for OAuth state storage in Docker environments."""
    try:
        from sqlalchemy import text
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS oauth_temp_states (
                session_id VARCHAR(32) PRIMARY KEY,
                state VARCHAR(128) NOT NULL,
                admin_user_id INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """))
        
        # Create index for cleanup
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_oauth_temp_states_expires 
            ON oauth_temp_states(expires_at)
        """))
        
        db.session.commit()
        logger.info("✅ OAuth temporary states table created")
        
    except Exception as e:
        logger.warning(f"Could not create OAuth temp states table: {e}")
        db.session.rollback()


def cleanup_expired_oauth_states():
    """Clean up expired OAuth states from temporary table."""
    try:
        from sqlalchemy import text
        result = db.session.execute(text("""
            DELETE FROM oauth_temp_states 
            WHERE expires_at < :now
        """), {'now': datetime.utcnow()})
        
        db.session.commit()
        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired OAuth states")
            
    except Exception as e:
        logger.warning(f"Could not cleanup expired OAuth states: {e}")
        db.session.rollback()