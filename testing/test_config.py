"""
Test Configuration for OAuth Persistence & Storage Monitoring
Centralizes test settings and mock configurations

Author: Resume Modifier Backend Team
Date: November 2024
"""

import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock
from typing import Dict, Any, Optional


class TestConfig:
    """Test configuration settings"""
    
    # Database settings for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    
    # OAuth test settings
    GOOGLE_CLIENT_ID = 'test_client_id'
    GOOGLE_CLIENT_SECRET = 'test_client_secret'
    GOOGLE_REDIRECT_URI = 'http://localhost:5001/auth/callback'
    
    # Storage monitoring test settings
    DEFAULT_STORAGE_QUOTA_GB = 15  # 15GB default quota
    WARNING_THRESHOLD_PERCENT = 80  # Warn at 80%
    CRITICAL_THRESHOLD_PERCENT = 90  # Critical at 90%
    
    # Test timeouts
    API_TIMEOUT_SECONDS = 30
    BACKGROUND_TASK_TIMEOUT = 60
    
    # Test data paths
    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
    TEMP_DIR = tempfile.gettempdir()


class MockGoogleAuthResponse:
    """Mock Google OAuth response for testing"""
    
    def __init__(self, success: bool = True, **kwargs):
        self.success = success
        self.data = {
            'access_token': kwargs.get('access_token', 'mock_access_token_123'),
            'refresh_token': kwargs.get('refresh_token', 'mock_refresh_token_456'),
            'expires_in': kwargs.get('expires_in', 3600),
            'token_type': kwargs.get('token_type', 'Bearer'),
            'scope': kwargs.get('scope', 'https://www.googleapis.com/auth/drive'),
            'email': kwargs.get('email', 'test@example.com'),
            'name': kwargs.get('name', 'Test User'),
            'picture': kwargs.get('picture', 'https://example.com/picture.jpg')
        }
    
    def json(self):
        if self.success:
            return self.data
        else:
            return {'error': 'invalid_grant', 'error_description': 'Token expired'}
    
    @property
    def status_code(self):
        return 200 if self.success else 400


class MockGoogleDriveResponse:
    """Mock Google Drive API response for testing"""
    
    def __init__(self, quota_used_gb: float = 5.0, quota_total_gb: float = 15.0):
        self.quota_used_gb = quota_used_gb
        self.quota_total_gb = quota_total_gb
    
    def json(self):
        return {
            'storageQuota': {
                'usage': str(int(self.quota_used_gb * 1024 * 1024 * 1024)),  # Convert to bytes
                'limit': str(int(self.quota_total_gb * 1024 * 1024 * 1024))   # Convert to bytes
            }
        }
    
    @property
    def status_code(self):
        return 200


class TestDataFactory:
    """Factory for creating test data objects"""
    
    @staticmethod
    def create_google_auth_data(**overrides) -> Dict[str, Any]:
        """Create GoogleAuth model test data"""
        base_data = {
            'id': 1,
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/picture.jpg',
            'access_token': 'mock_access_token_123',
            'refresh_token': 'mock_refresh_token_456',
            'token_expires_at': datetime.utcnow() + timedelta(hours=1),
            'is_active': True,
            'last_login': datetime.utcnow(),
            'created_at': datetime.utcnow() - timedelta(days=1),
            'updated_at': datetime.utcnow(),
            
            # OAuth persistence fields
            'persistent_auth_enabled': True,
            'auth_session_token': 'session_token_789',
            'session_expires_at': datetime.utcnow() + timedelta(days=30),
            'last_activity_at': datetime.utcnow(),
            'auto_refresh_enabled': True,
            'refresh_failure_count': 0,
            'storage_quota_gb': 15.0,
            'storage_used_gb': 5.0,
            'storage_warning_level': 'normal',
            'last_storage_check': datetime.utcnow(),
            'storage_alert_enabled': True,
            'storage_alert_threshold': 80.0,
            'last_storage_alert': None,
            'auth_preferences': {'theme': 'light', 'notifications': True},
            'compliance_flags': {'gdpr_consent': True, 'data_retention': 'standard'}
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_storage_alert_data(**overrides) -> Dict[str, Any]:
        """Create storage alert test data"""
        base_data = {
            'user_id': 1,
            'alert_type': 'warning',
            'storage_used_gb': 12.0,
            'storage_quota_gb': 15.0,
            'usage_percentage': 80.0,
            'message': 'Storage usage is at 80% capacity',
            'created_at': datetime.utcnow(),
            'acknowledged': False
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_oauth_session_data(**overrides) -> Dict[str, Any]:
        """Create OAuth session test data"""
        base_data = {
            'session_token': 'session_token_789',
            'user_id': 1,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(days=30),
            'last_activity': datetime.utcnow(),
            'is_active': True,
            'refresh_count': 0,
            'device_info': 'Test Browser 1.0'
        }
        base_data.update(overrides)
        return base_data


class MockServices:
    """Collection of mock services for testing"""
    
    @staticmethod
    def create_mock_requests():
        """Create mock requests module"""
        mock_requests = Mock()
        
        # Mock successful OAuth token exchange
        mock_requests.post.return_value = MockGoogleAuthResponse(success=True)
        
        # Mock successful Drive API calls
        mock_requests.get.return_value = MockGoogleDriveResponse()
        
        return mock_requests
    
    @staticmethod
    def create_mock_email_service():
        """Create mock email service"""
        mock_email = Mock()
        mock_email.send_storage_alert.return_value = True
        mock_email.send_auth_notification.return_value = True
        return mock_email
    
    @staticmethod
    def create_mock_background_scheduler():
        """Create mock background task scheduler"""
        mock_scheduler = Mock()
        mock_scheduler.add_job.return_value = True
        mock_scheduler.remove_job.return_value = True
        mock_scheduler.get_jobs.return_value = []
        return mock_scheduler
    
    @staticmethod
    def create_mock_flask_app():
        """Create mock Flask application"""
        from flask import Flask
        
        app = Flask(__name__)
        app.config.from_object(TestConfig)
        
        # Add test routes
        @app.route('/api/health')
        def health_check():
            return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
        
        return app


class TestUtilities:
    """Utility functions for testing"""
    
    @staticmethod
    def assert_dict_contains(actual: Dict[str, Any], expected: Dict[str, Any], message: str = ""):
        """Assert that actual dict contains all key-value pairs from expected dict"""
        for key, expected_value in expected.items():
            assert key in actual, f"{message}: Missing key '{key}' in actual dict"
            assert actual[key] == expected_value, f"{message}: Key '{key}' has value '{actual[key]}', expected '{expected_value}'"
    
    @staticmethod
    def create_temp_file(content: str, suffix: str = '.txt') -> str:
        """Create a temporary file with given content"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            return f.name
    
    @staticmethod
    def cleanup_temp_file(filepath: str):
        """Clean up temporary file"""
        try:
            os.unlink(filepath)
        except (OSError, FileNotFoundError):
            pass  # File already deleted or doesn't exist
    
    @staticmethod
    def mock_datetime_now(fixed_time: Optional[datetime] = None) -> datetime:
        """Return a fixed datetime for consistent testing"""
        if fixed_time:
            return fixed_time
        return datetime(2024, 11, 15, 10, 30, 0)  # Fixed test time
    
    @staticmethod
    def calculate_expected_storage_percentage(used_gb: float, total_gb: float) -> float:
        """Calculate expected storage percentage for testing"""
        if total_gb <= 0:
            return 0.0
        return min(100.0, (used_gb / total_gb) * 100.0)
    
    @staticmethod
    def generate_test_token(prefix: str = 'test_token', length: int = 32) -> str:
        """Generate a test token for OAuth testing"""
        import secrets
        import string
        
        suffix = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length - len(prefix) - 1))
        return f"{prefix}_{suffix}"


# Export commonly used test objects
__all__ = [
    'TestConfig',
    'MockGoogleAuthResponse', 
    'MockGoogleDriveResponse',
    'TestDataFactory',
    'MockServices',
    'TestUtilities'
]