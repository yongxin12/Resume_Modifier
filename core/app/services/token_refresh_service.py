"""
Token Refresh Background Service for OAuth Persistence
Automatically refreshes OAuth tokens and monitors storage quota

Author: Resume Modifier Backend Team  
Date: November 2024
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from contextlib import contextmanager

from flask import Flask
from app.extensions import db
from app.models.temp import GoogleAuth
from app.services.oauth_persistence_service import oauth_persistence_service, TokenRefreshResult


class TokenRefreshBackgroundService:
    """
    Background service that automatically refreshes OAuth tokens and monitors storage quota
    to maintain persistent authentication without user intervention.
    """

    def __init__(self, app: Flask = None):
        """Initialize the background service."""
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.thread = None
        self.stop_event = threading.Event()
        
        # Configuration
        self.refresh_check_interval = 900  # 15 minutes
        self.storage_check_interval = 21600  # 6 hours
        self.token_expiry_threshold = 300  # 5 minutes
        
        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
        
        # Load configuration from app config
        self.refresh_check_interval = app.config.get('OAUTH_REFRESH_CHECK_INTERVAL', 900)
        self.storage_check_interval = app.config.get('STORAGE_CHECK_INTERVAL', 21600)
        self.token_expiry_threshold = app.config.get('OAUTH_TOKEN_EXPIRY_THRESHOLD', 300)
        
        self.logger.info(f"Token refresh service configured - refresh every {self.refresh_check_interval}s")

    @contextmanager
    def app_context(self):
        """Create application context for database operations."""
        if self.app:
            with self.app.app_context():
                yield
        else:
            yield

    def start(self):
        """Start the background service."""
        if self.is_running:
            self.logger.warning("Token refresh service is already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_service, daemon=True)
        self.thread.start()
        
        self.logger.info("Token refresh background service started")

    def stop(self):
        """Stop the background service."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping token refresh background service...")
        self.is_running = False
        self.stop_event.set()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
        
        self.logger.info("Token refresh background service stopped")

    def _run_service(self):
        """Main service loop that runs in background thread."""
        last_storage_check = datetime.utcnow() - timedelta(hours=7)  # Force initial check
        
        while self.is_running and not self.stop_event.is_set():
            try:
                with self.app_context():
                    # Check and refresh tokens
                    self._check_and_refresh_tokens()
                    
                    # Check storage quota if enough time has passed
                    now = datetime.utcnow()
                    if (now - last_storage_check).total_seconds() >= self.storage_check_interval:
                        self._check_storage_quotas()
                        last_storage_check = now
                
                # Wait for next cycle or stop event
                self.stop_event.wait(self.refresh_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in token refresh service loop: {e}")
                # Wait a bit before retrying on error
                self.stop_event.wait(60)

    def _check_and_refresh_tokens(self):
        """Check all active OAuth sessions and refresh tokens if needed."""
        try:
            # Find sessions that need token refresh
            expiring_soon = datetime.utcnow() + timedelta(seconds=self.token_expiry_threshold)
            
            sessions_to_refresh = db.session.query(GoogleAuth).filter(
                GoogleAuth.is_active == True,
                GoogleAuth.token_expires_at <= expiring_soon
            ).all()
            
            if not sessions_to_refresh:
                self.logger.debug("No tokens need refreshing")
                return
            
            self.logger.info(f"Found {len(sessions_to_refresh)} tokens that need refreshing")
            
            refresh_results = []
            for auth in sessions_to_refresh:
                try:
                    result = oauth_persistence_service.refresh_token_if_needed(auth.id)
                    refresh_results.append({
                        'auth_id': auth.id,
                        'user_id': auth.user_id,
                        'success': result.success,
                        'message': result.message,
                        'attempts': result.refresh_attempts
                    })
                    
                    if result.success:
                        self.logger.info(f"✅ Refreshed token for auth {auth.id}")
                    else:
                        self.logger.error(f"❌ Failed to refresh token for auth {auth.id}: {result.message}")
                        
                except Exception as e:
                    self.logger.error(f"Error refreshing token for auth {auth.id}: {e}")
                    refresh_results.append({
                        'auth_id': auth.id,
                        'user_id': auth.user_id,
                        'success': False,
                        'message': str(e),
                        'attempts': getattr(auth, 'refresh_attempts', 0)
                    })
            
            # Log summary
            successful = sum(1 for r in refresh_results if r['success'])
            failed = len(refresh_results) - successful
            
            if failed > 0:
                self.logger.warning(f"Token refresh summary: {successful} successful, {failed} failed")
            else:
                self.logger.info(f"Token refresh summary: {successful} successful, {failed} failed")
                
        except Exception as e:
            self.logger.error(f"Error during token refresh check: {e}")

    def _check_storage_quotas(self):
        """Check storage quotas for all active OAuth sessions."""
        try:
            active_sessions = oauth_persistence_service.get_active_sessions()
            
            if not active_sessions:
                self.logger.debug("No active OAuth sessions to check storage for")
                return
            
            self.logger.info(f"Checking storage quotas for {len(active_sessions)} active sessions")
            
            quota_results = []
            for auth in active_sessions:
                try:
                    quota_info = oauth_persistence_service.check_storage_quota(auth.id)
                    
                    if quota_info:
                        quota_results.append({
                            'auth_id': auth.id,
                            'user_id': auth.user_id,
                            'usage_percentage': quota_info.usage_percentage,
                            'warning_level': quota_info.warning_level,
                            'success': True
                        })
                        
                        self.logger.info(f"Storage quota for auth {auth.id}: {quota_info.usage_percentage:.1f}% ({quota_info.warning_level})")
                        
                        # Log warnings for high usage
                        if quota_info.warning_level in ['high', 'critical']:
                            self.logger.warning(f"⚠️  High storage usage for auth {auth.id}: {quota_info.usage_percentage:.1f}%")
                            
                    else:
                        quota_results.append({
                            'auth_id': auth.id,
                            'user_id': auth.user_id,
                            'success': False,
                            'error': 'Failed to retrieve quota info'
                        })
                        
                except Exception as e:
                    self.logger.error(f"Error checking storage quota for auth {auth.id}: {e}")
                    quota_results.append({
                        'auth_id': auth.id,
                        'user_id': auth.user_id,
                        'success': False,
                        'error': str(e)
                    })
            
            # Log summary
            successful = sum(1 for r in quota_results if r.get('success'))
            failed = len(quota_results) - successful
            high_usage = sum(1 for r in quota_results if r.get('warning_level') in ['high', 'critical'])
            
            summary_msg = f"Storage quota check summary: {successful} successful, {failed} failed"
            if high_usage > 0:
                summary_msg += f", {high_usage} with high usage warnings"
            
            if failed > 0 or high_usage > 0:
                self.logger.warning(summary_msg)
            else:
                self.logger.info(summary_msg)
                
        except Exception as e:
            self.logger.error(f"Error during storage quota check: {e}")

    def force_refresh_all(self) -> Dict[str, Any]:
        """
        Force refresh all active tokens immediately (for manual triggering).
        
        Returns:
            Dict: Summary of refresh results
        """
        try:
            with self.app_context():
                active_sessions = oauth_persistence_service.get_active_sessions()
                
                if not active_sessions:
                    return {
                        'success': True,
                        'message': 'No active sessions to refresh',
                        'total_sessions': 0,
                        'successful_refreshes': 0,
                        'failed_refreshes': 0,
                        'results': []
                    }
                
                self.logger.info(f"Force refreshing {len(active_sessions)} active OAuth sessions")
                
                results = []
                successful = 0
                failed = 0
                
                for auth in active_sessions:
                    try:
                        refresh_result = oauth_persistence_service.refresh_token_if_needed(auth.id)
                        
                        result_data = {
                            'auth_id': auth.id,
                            'user_id': auth.user_id,
                            'success': refresh_result.success,
                            'message': refresh_result.message,
                            'refresh_attempts': refresh_result.refresh_attempts
                        }
                        
                        results.append(result_data)
                        
                        if refresh_result.success:
                            successful += 1
                        else:
                            failed += 1
                            
                    except Exception as e:
                        failed += 1
                        results.append({
                            'auth_id': auth.id,
                            'user_id': auth.user_id,
                            'success': False,
                            'message': str(e),
                            'refresh_attempts': getattr(auth, 'refresh_attempts', 0)
                        })
                
                summary = {
                    'success': True,
                    'message': f'Force refresh completed: {successful} successful, {failed} failed',
                    'total_sessions': len(active_sessions),
                    'successful_refreshes': successful,
                    'failed_refreshes': failed,
                    'results': results
                }
                
                self.logger.info(summary['message'])
                return summary
                
        except Exception as e:
            error_msg = f"Error during force refresh: {e}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'error': str(e)
            }

    def get_service_status(self) -> Dict[str, Any]:
        """
        Get current service status information.
        
        Returns:
            Dict: Service status information
        """
        try:
            with self.app_context():
                active_sessions = oauth_persistence_service.get_active_sessions()
                
                # Count sessions by status
                total_sessions = len(active_sessions)
                tokens_expiring_soon = 0
                high_storage_usage = 0
                
                expiring_threshold = datetime.utcnow() + timedelta(seconds=self.token_expiry_threshold)
                
                for auth in active_sessions:
                    # Check expiring tokens
                    if auth.token_expires_at and auth.token_expires_at <= expiring_threshold:
                        tokens_expiring_soon += 1
                    
                    # Check high storage usage
                    if hasattr(auth, 'quota_warning_level') and auth.quota_warning_level in ['high', 'critical']:
                        high_storage_usage += 1
                
                return {
                    'service_running': self.is_running,
                    'thread_alive': self.thread.is_alive() if self.thread else False,
                    'configuration': {
                        'refresh_check_interval': self.refresh_check_interval,
                        'storage_check_interval': self.storage_check_interval,
                        'token_expiry_threshold': self.token_expiry_threshold
                    },
                    'sessions': {
                        'total_active': total_sessions,
                        'tokens_expiring_soon': tokens_expiring_soon,
                        'high_storage_usage': high_storage_usage
                    },
                    'last_update': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                'service_running': self.is_running,
                'error': str(e),
                'last_update': datetime.utcnow().isoformat()
            }


# Global service instance
token_refresh_service = TokenRefreshBackgroundService()