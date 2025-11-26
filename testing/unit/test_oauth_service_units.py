"""
OAuth Persistence Service Unit Tests
Focused unit tests for OAuth persistence service functionality

Author: Resume Modifier Backend Team
Date: November 2024
"""

import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from app.services.oauth_persistence_service import OAuthPersistenceService, SessionResult
except ImportError:
    # Fallback for test environment
    OAuthPersistenceService = None
    SessionResult = None


class TestOAuthPersistenceService(unittest.TestCase):
    """Unit tests for OAuthPersistenceService"""
    
    def setUp(self):
        """Set up test fixtures"""
        if OAuthPersistenceService is None:
            self.skipTest("OAuthPersistenceService not available")
        
        self.service = OAuthPersistenceService()
        self.service.logger = MagicMock()
    
    def test_generate_session_id(self):
        """Test session ID generation"""
        session_id = self.service._generate_session_id()
        
        # Should be a string
        self.assertIsInstance(session_id, str)
        
        # Should be reasonable length (32+ characters for security)
        self.assertGreaterEqual(len(session_id), 32)
        
        # Should be unique
        session_id2 = self.service._generate_session_id()
        self.assertNotEqual(session_id, session_id2)
    
    def test_calculate_token_expiry(self):
        """Test token expiry calculation"""
        # Test with expires_in as seconds
        expires_in = 3600  # 1 hour
        result = self.service._calculate_token_expiry(expires_in)
        
        # Should be datetime
        self.assertIsInstance(result, datetime)
        
        # Should be approximately 1 hour from now
        expected_time = datetime.utcnow() + timedelta(seconds=expires_in)
        time_diff = abs((result - expected_time).total_seconds())
        self.assertLess(time_diff, 5)  # Within 5 seconds
        
        # Test with None
        result = self.service._calculate_token_expiry(None)
        expected_time = datetime.utcnow() + timedelta(hours=1)
        time_diff = abs((result - expected_time).total_seconds())
        self.assertLess(time_diff, 5)
    
    def test_is_token_expired(self):
        """Test token expiration checking"""
        # Test expired token
        expired_time = datetime.utcnow() - timedelta(minutes=10)
        self.assertTrue(self.service._is_token_expired(expired_time))
        
        # Test valid token
        valid_time = datetime.utcnow() + timedelta(hours=1)
        self.assertFalse(self.service._is_token_expired(valid_time))
        
        # Test token expiring soon (within buffer)
        soon_time = datetime.utcnow() + timedelta(minutes=2.5)  # Less than 5 min buffer
        self.assertTrue(self.service._is_token_expired(soon_time))
        
        # Test None expiry
        self.assertTrue(self.service._is_token_expired(None))
    
    @patch('app.services.oauth_persistence_service.GoogleAuth')
    @patch('app.services.oauth_persistence_service.db')
    def test_create_persistent_session(self, mock_db, mock_google_auth):
        """Test creating a persistent OAuth session"""
        # Mock GoogleAuth record
        mock_auth = MagicMock()
        mock_auth.id = 1
        mock_auth.user_id = 123
        mock_auth.email = "test@example.com"
        mock_auth.access_token = "test_token"
        mock_auth.refresh_token = "refresh_token"
        mock_auth.token_expires_at = datetime.utcnow() + timedelta(hours=1)
        
        mock_google_auth.query.get.return_value = mock_auth
        
        # Test creating persistent session
        result = self.service.create_persistent_session(
            auth_id=1,
            enable_auto_refresh=True,
            session_duration_hours=24
        )
        
        # Verify result
        self.assertIsInstance(result, (SessionResult, dict))
        if hasattr(result, 'success'):
            self.assertTrue(result.success)
        else:
            self.assertTrue(result.get('success'))
        
        # Verify auth record updates
        self.assertTrue(mock_auth.is_persistent)
        self.assertTrue(mock_auth.auto_refresh_enabled)
        self.assertTrue(mock_auth.is_active)
        self.assertIsNotNone(mock_auth.persistent_session_id)
        
        # Verify database commit
        mock_db.session.commit.assert_called_once()
    
    @patch('app.services.oauth_persistence_service.GoogleAuth')
    def test_get_session_status(self, mock_google_auth):
        """Test getting session status"""
        # Mock active session
        mock_auth = MagicMock()
        mock_auth.id = 1
        mock_auth.user_id = 123
        mock_auth.is_persistent = True
        mock_auth.is_active = True
        mock_auth.auto_refresh_enabled = True
        mock_auth.persistent_session_id = "test_session_123"
        mock_auth.token_expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_auth.last_refresh_at = datetime.utcnow() - timedelta(minutes=30)
        mock_auth.last_activity_at = datetime.utcnow() - timedelta(minutes=5)
        
        mock_google_auth.query.get.return_value = mock_auth
        
        result = self.service.get_session_status(1)
        
        # Verify result structure
        self.assertTrue(result.get('success'))
        self.assertIn('oauth_status', result)
        self.assertIn('storage_status', result)
        
        # Verify OAuth status
        oauth_status = result['oauth_status']
        self.assertTrue(oauth_status['is_persistent'])
        self.assertTrue(oauth_status['is_active'])
        self.assertTrue(oauth_status['auto_refresh_enabled'])
        self.assertEqual(oauth_status['session_id'], "test_session_123")
        self.assertFalse(oauth_status['token_expired'])
    
    @patch('app.services.oauth_persistence_service.GoogleAuth')
    @patch('app.services.oauth_persistence_service.db')
    def test_revoke_persistent_session(self, mock_db, mock_google_auth):
        """Test revoking a persistent session"""
        # Mock active session
        mock_auth = MagicMock()
        mock_auth.id = 1
        mock_auth.is_persistent = True
        mock_auth.is_active = True
        mock_auth.persistent_session_id = "test_session_123"
        
        mock_google_auth.query.get.return_value = mock_auth
        
        result = self.service.revoke_persistent_session(1, confirmed=True)
        
        # Verify result
        self.assertTrue(result.get('success'))
        
        # Verify session deactivation
        self.assertFalse(mock_auth.is_persistent)
        self.assertFalse(mock_auth.is_active)
        self.assertFalse(mock_auth.auto_refresh_enabled)
        self.assertIsNotNone(mock_auth.deactivated_at)
        self.assertEqual(mock_auth.deactivated_reason, 'manual_revocation')
        
        # Verify database commit
        mock_db.session.commit.assert_called_once()
    
    @patch('app.services.oauth_persistence_service.GoogleAuth')
    def test_revoke_without_confirmation(self, mock_google_auth):
        """Test that revocation requires confirmation"""
        mock_auth = MagicMock()
        mock_google_auth.query.get.return_value = mock_auth
        
        result = self.service.revoke_persistent_session(1, confirmed=False)
        
        # Should fail without confirmation
        self.assertFalse(result.get('success'))
        self.assertIn('error', result)
        self.assertIn('confirmation', result['error'].lower())
    
    @patch('app.services.oauth_persistence_service.GoogleAuth')
    def test_get_all_active_sessions(self, mock_google_auth):
        """Test getting all active sessions"""
        # Mock active sessions
        mock_auth1 = MagicMock()
        mock_auth1.id = 1
        mock_auth1.user_id = 101
        mock_auth1.email = "user1@example.com"
        mock_auth1.is_active = True
        mock_auth1.is_persistent = True
        
        mock_auth2 = MagicMock()
        mock_auth2.id = 2
        mock_auth2.user_id = 102
        mock_auth2.email = "user2@example.com"
        mock_auth2.is_active = True
        mock_auth2.is_persistent = False
        
        mock_google_auth.query.filter_by.return_value.all.return_value = [
            mock_auth1, mock_auth2
        ]
        
        result = self.service.get_all_active_sessions()
        
        # Verify result structure
        self.assertTrue(result.get('success'))
        self.assertIn('sessions', result)
        self.assertIn('summary', result)
        
        # Verify session count
        sessions = result['sessions']
        self.assertEqual(len(sessions), 2)
        
        # Verify summary
        summary = result['summary']
        self.assertEqual(summary['total_active'], 2)
        self.assertEqual(summary['persistent_sessions'], 1)
        self.assertEqual(summary['temporary_sessions'], 1)
    
    def test_session_result_dataclass(self):
        """Test SessionResult dataclass functionality"""
        if SessionResult is None:
            self.skipTest("SessionResult not available")
        
        # Test successful result
        result = SessionResult(
            success=True,
            message="Session created successfully",
            session_id="test_123",
            auth_id=1,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Session created successfully")
        self.assertEqual(result.session_id, "test_123")
        self.assertEqual(result.auth_id, 1)
        self.assertIsNotNone(result.expires_at)
        
        # Test failed result
        failed_result = SessionResult(
            success=False,
            message="Session creation failed",
            error="Invalid auth ID"
        )
        
        self.assertFalse(failed_result.success)
        self.assertEqual(failed_result.error, "Invalid auth ID")


class TestTokenManagement(unittest.TestCase):
    """Unit tests for token management functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if OAuthPersistenceService is None:
            self.skipTest("OAuthPersistenceService not available")
        
        self.service = OAuthPersistenceService()
        self.service.logger = MagicMock()
    
    @patch('app.services.oauth_persistence_service.GoogleAuth')
    @patch('app.services.oauth_persistence_service.google.oauth2.credentials')
    @patch('app.services.oauth_persistence_service.Request')
    def test_refresh_token_if_needed(self, mock_request, mock_credentials, mock_google_auth):
        """Test token refresh when needed"""
        # Mock expired token
        mock_auth = MagicMock()
        mock_auth.id = 1
        mock_auth.access_token = "old_token"
        mock_auth.refresh_token = "refresh_token"
        mock_auth.token_expires_at = datetime.utcnow() - timedelta(minutes=10)
        mock_auth.refresh_attempts = 0
        mock_auth.max_refresh_failures = 3
        
        mock_google_auth.query.get.return_value = mock_auth
        
        # Mock successful refresh
        mock_creds = MagicMock()
        mock_creds.token = "new_token"
        mock_creds.refresh_token = "new_refresh_token"
        mock_creds.expiry = datetime.utcnow() + timedelta(hours=1)
        
        mock_credentials.Credentials.return_value = mock_creds
        
        result = self.service.refresh_token_if_needed(1)
        
        # Verify refresh was attempted
        mock_creds.refresh.assert_called_once()
        
        # Verify result
        self.assertTrue(result.get('success'))
        
        # Verify token updates
        self.assertEqual(mock_auth.access_token, "new_token")
        self.assertEqual(mock_auth.refresh_token, "new_refresh_token")
        self.assertIsNotNone(mock_auth.last_refresh_at)
    
    @patch('app.services.oauth_persistence_service.GoogleAuth')
    def test_refresh_token_not_needed(self, mock_google_auth):
        """Test that valid tokens are not refreshed"""
        # Mock valid token
        mock_auth = MagicMock()
        mock_auth.id = 1
        mock_auth.token_expires_at = datetime.utcnow() + timedelta(hours=1)
        
        mock_google_auth.query.get.return_value = mock_auth
        
        result = self.service.refresh_token_if_needed(1)
        
        # Should succeed without refresh
        self.assertTrue(result.get('success'))
        self.assertIn('not needed', result.get('message', '').lower())
    
    def test_token_expiry_calculations(self):
        """Test various token expiry scenarios"""
        # Test expired token
        expired_time = datetime.utcnow() - timedelta(minutes=10)
        self.assertTrue(self.service._is_token_expired(expired_time))
        
        # Test valid token
        valid_time = datetime.utcnow() + timedelta(hours=1)
        self.assertFalse(self.service._is_token_expired(valid_time))
        
        # Test token expiring within buffer (5 minutes)
        buffer_time = datetime.utcnow() + timedelta(minutes=3)
        self.assertTrue(self.service._is_token_expired(buffer_time))
        
        # Test token just outside buffer
        safe_time = datetime.utcnow() + timedelta(minutes=6)
        self.assertFalse(self.service._is_token_expired(safe_time))


class TestSessionManagement(unittest.TestCase):
    """Unit tests for session management functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if OAuthPersistenceService is None:
            self.skipTest("OAuthPersistenceService not available")
        
        self.service = OAuthPersistenceService()
        self.service.logger = MagicMock()
    
    def test_session_id_generation_uniqueness(self):
        """Test that generated session IDs are unique"""
        session_ids = set()
        
        # Generate multiple session IDs
        for _ in range(100):
            session_id = self.service._generate_session_id()
            self.assertNotIn(session_id, session_ids, "Session ID should be unique")
            session_ids.add(session_id)
        
        # Verify all are different
        self.assertEqual(len(session_ids), 100)
    
    def test_session_duration_calculations(self):
        """Test session duration calculations"""
        # Test default duration
        expires_at = self.service._calculate_session_expiry()
        now = datetime.utcnow()
        duration = expires_at - now
        
        # Should be approximately 24 hours (default)
        expected_duration = timedelta(hours=24)
        time_diff = abs(duration - expected_duration)
        self.assertLess(time_diff.total_seconds(), 60)  # Within 1 minute
        
        # Test custom duration
        custom_expires_at = self.service._calculate_session_expiry(hours=48)
        custom_duration = custom_expires_at - now
        expected_custom_duration = timedelta(hours=48)
        custom_time_diff = abs(custom_duration - expected_custom_duration)
        self.assertLess(custom_time_diff.total_seconds(), 60)
    
    @patch('app.services.oauth_persistence_service.GoogleAuth')
    def test_session_activity_tracking(self, mock_google_auth):
        """Test session activity tracking"""
        mock_auth = MagicMock()
        mock_auth.id = 1
        mock_auth.is_active = True
        mock_auth.last_activity_at = datetime.utcnow() - timedelta(hours=2)
        
        mock_google_auth.query.get.return_value = mock_auth
        
        # Update activity
        self.service._update_session_activity(1)
        
        # Verify activity timestamp was updated
        self.assertIsNotNone(mock_auth.last_activity_at)
        
        # Should be very recent
        time_diff = datetime.utcnow() - mock_auth.last_activity_at
        self.assertLess(time_diff.total_seconds(), 5)


if __name__ == '__main__':
    # Configure test runner
    unittest.main(
        verbosity=2,
        testRunner=unittest.TextTestRunner(
            stream=sys.stdout,
            verbosity=2
        )
    )