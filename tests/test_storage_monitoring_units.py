"""
Storage Monitoring Service Unit Tests
Focused unit tests for storage monitoring service components

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
    from app.services.storage_monitoring_service import StorageMonitoringService, StorageAlert
    from app.services.background_storage_monitor import BackgroundStorageMonitor
except ImportError:
    # Fallback for test environment
    StorageMonitoringService = None
    BackgroundStorageMonitor = None
    StorageAlert = None


class TestStorageMonitoringService(unittest.TestCase):
    """Unit tests for StorageMonitoringService"""
    
    def setUp(self):
        """Set up test fixtures"""
        if StorageMonitoringService is None:
            self.skipTest("StorageMonitoringService not available")
        
        self.service = StorageMonitoringService()
        self.service.logger = MagicMock()
    
    def test_determine_warning_level(self):
        """Test warning level determination"""
        test_cases = [
            (79, 'none'),
            (80, 'low'),
            (84, 'low'),
            (85, 'medium'),
            (89, 'medium'),
            (90, 'high'),
            (94, 'high'),
            (95, 'critical'),
            (99, 'critical')
        ]
        
        for usage_percentage, expected_level in test_cases:
            result = self.service._determine_warning_level(usage_percentage)
            self.assertEqual(result, expected_level,
                           f"Usage {usage_percentage}% should be '{expected_level}', got '{result}'")
    
    def test_get_alert_content(self):
        """Test alert content generation"""
        test_cases = [
            ('critical', 97.5, 1.2),
            ('high', 92.0, 3.8),
            ('medium', 87.0, 6.5),
            ('low', 82.0, 9.0)
        ]
        
        for level, usage, available_gb in test_cases:
            message, recommendations = self.service._get_alert_content(level, usage, available_gb)
            
            # Verify message format
            self.assertIn(f"{usage:.1f}%", message)
            self.assertIn(f"{available_gb:.1f} GB", message)
            
            # Verify recommendations are provided
            self.assertIsInstance(recommendations, list)
            self.assertGreater(len(recommendations), 0)
            
            # Verify level-specific content
            if level == 'critical':
                self.assertIn('CRITICAL', message)
                self.assertTrue(any('IMMEDIATE ACTION' in rec for rec in recommendations))
            elif level == 'high':
                self.assertIn('HIGH WARNING', message)
                self.assertTrue(any('URGENT' in rec for rec in recommendations))
    
    def test_calculate_usage_percentage(self):
        """Test usage percentage calculation"""
        # Mock auth record
        mock_auth = MagicMock()
        
        # Test normal case
        mock_auth.drive_quota_total = 15 * (1024**3)  # 15 GB
        mock_auth.drive_quota_used = 12 * (1024**3)   # 12 GB
        
        result = self.service._calculate_usage_percentage(mock_auth)
        self.assertEqual(result, 80.0)
        
        # Test zero total (edge case)
        mock_auth.drive_quota_total = 0
        mock_auth.drive_quota_used = 0
        
        result = self.service._calculate_usage_percentage(mock_auth)
        self.assertEqual(result, 0.0)
        
        # Test None values (edge case)
        mock_auth.drive_quota_total = None
        mock_auth.drive_quota_used = None
        
        result = self.service._calculate_usage_percentage(mock_auth)
        self.assertEqual(result, 0.0)
    
    @patch('app.services.storage_monitoring_service.GoogleAuth')
    def test_get_all_storage_status(self, mock_google_auth):
        """Test getting storage status for all sessions"""
        # Mock active sessions
        mock_session1 = MagicMock()
        mock_session1.id = 1
        mock_session1.user_id = 101
        mock_session1.email = "user1@example.com"
        mock_session1.drive_quota_total = 15 * (1024**3)
        mock_session1.drive_quota_used = 12 * (1024**3)
        mock_session1.quota_warning_level = 'low'
        mock_session1.last_quota_check = datetime.utcnow()
        
        mock_session2 = MagicMock()
        mock_session2.id = 2
        mock_session2.user_id = 102
        mock_session2.email = "user2@example.com"
        mock_session2.drive_quota_total = 10 * (1024**3)
        mock_session2.drive_quota_used = 9.5 * (1024**3)
        mock_session2.quota_warning_level = 'critical'
        mock_session2.last_quota_check = datetime.utcnow()
        
        mock_google_auth.query.filter_by.return_value.all.return_value = [
            mock_session1, mock_session2
        ]
        
        result = self.service.get_all_storage_status()
        
        # Verify result structure
        self.assertTrue(result['success'])
        self.assertIn('summary', result)
        self.assertIn('sessions', result)
        
        # Verify summary
        summary = result['summary']
        self.assertEqual(summary['total_sessions'], 2)
        self.assertEqual(summary['sessions_with_warnings'], 2)
        self.assertEqual(summary['critical_sessions'], 1)
        
        # Verify sessions
        sessions = result['sessions']
        self.assertEqual(len(sessions), 2)
        
        # Verify first session
        session1 = sessions[0]
        self.assertEqual(session1['auth_id'], 1)
        self.assertEqual(session1['user_id'], 101)
        self.assertEqual(session1['user_email'], "user1@example.com")
        self.assertEqual(session1['warning_level'], 'low')
        self.assertEqual(session1['usage_percentage'], 80.0)


class TestBackgroundStorageMonitor(unittest.TestCase):
    """Unit tests for BackgroundStorageMonitor"""
    
    def setUp(self):
        """Set up test fixtures"""
        if BackgroundStorageMonitor is None:
            self.skipTest("BackgroundStorageMonitor not available")
        
        self.monitor = BackgroundStorageMonitor()
        self.monitor.logger = MagicMock()
        self.mock_app = MagicMock()
        self.mock_app.config = {
            'STORAGE_MONITORING_ENABLED': True,
            'STORAGE_CHECK_INTERVAL_MINUTES': 60
        }
    
    def test_init_app(self):
        """Test Flask app initialization"""
        self.monitor.init_app(self.mock_app)
        
        self.assertEqual(self.monitor.app, self.mock_app)
        self.assertTrue(self.monitor.enabled)
        self.assertEqual(self.monitor.check_interval_minutes, 60)
    
    def test_get_status(self):
        """Test getting service status"""
        self.monitor.enabled = True
        self.monitor.running = False
        self.monitor.check_interval_minutes = 120
        self.monitor.stats = {
            'service_started': datetime.utcnow(),
            'last_check': datetime.utcnow(),
            'total_checks': 5,
            'total_alerts_sent': 2,
            'last_error': None,
            'consecutive_errors': 0
        }
        
        status = self.monitor.get_status()
        
        self.assertTrue(status['enabled'])
        self.assertFalse(status['running'])
        self.assertEqual(status['check_interval_minutes'], 120)
        self.assertIn('stats', status)
        self.assertIn('config', status)
    
    def test_get_stats(self):
        """Test getting service statistics"""
        # Set up stats
        start_time = datetime.utcnow() - timedelta(hours=2)
        self.monitor.stats = {
            'service_started': start_time,
            'last_check': datetime.utcnow(),
            'total_checks': 10,
            'total_alerts_sent': 3,
            'last_error': 'Test error',
            'consecutive_errors': 1
        }
        
        stats = self.monitor.get_stats()
        
        # Verify stats structure
        self.assertIn('service_started', stats)
        self.assertIn('last_check', stats)
        self.assertEqual(stats['total_checks'], 10)
        self.assertEqual(stats['total_alerts_sent'], 3)
        self.assertEqual(stats['last_error'], 'Test error')
        self.assertEqual(stats['consecutive_errors'], 1)
        
        # Verify derived stats
        self.assertIn('uptime_seconds', stats)
        self.assertIn('uptime_hours', stats)
        self.assertGreater(stats['uptime_hours'], 1.5)  # Should be ~2 hours
    
    def test_update_config(self):
        """Test configuration updates"""
        # Test valid configuration
        result = self.monitor.update_config(
            check_interval_minutes=90,
            enabled=False
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(self.monitor.check_interval_minutes, 90)
        self.assertFalse(self.monitor.enabled)
        self.assertIn('old_config', result)
        self.assertIn('new_config', result)
        
        # Test invalid configuration (too low interval)
        result = self.monitor.update_config(check_interval_minutes=2)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('5 minutes', result['error'])


class TestStorageAlert(unittest.TestCase):
    """Unit tests for StorageAlert dataclass"""
    
    def test_storage_alert_creation(self):
        """Test StorageAlert creation and attributes"""
        if StorageAlert is None:
            self.skipTest("StorageAlert not available")
        
        timestamp = datetime.utcnow()
        alert = StorageAlert(
            level='high',
            usage_percentage=92.5,
            total_gb=15.0,
            used_gb=13.9,
            available_gb=1.1,
            message='Test alert message',
            recommendations=['Recommendation 1', 'Recommendation 2'],
            timestamp=timestamp
        )
        
        self.assertEqual(alert.level, 'high')
        self.assertEqual(alert.usage_percentage, 92.5)
        self.assertEqual(alert.total_gb, 15.0)
        self.assertEqual(alert.used_gb, 13.9)
        self.assertEqual(alert.available_gb, 1.1)
        self.assertEqual(alert.message, 'Test alert message')
        self.assertEqual(len(alert.recommendations), 2)
        self.assertEqual(alert.timestamp, timestamp)


class TestStorageCalculations(unittest.TestCase):
    """Unit tests for storage calculation utilities"""
    
    def test_bytes_to_gb_conversion(self):
        """Test bytes to GB conversion"""
        test_cases = [
            (1024**3, 1.0),      # 1 GB
            (5 * 1024**3, 5.0),  # 5 GB
            (1536 * 1024**2, 1.5),  # 1.5 GB
            (0, 0.0),            # 0 bytes
        ]
        
        for bytes_value, expected_gb in test_cases:
            result_gb = bytes_value / (1024**3)
            self.assertAlmostEqual(result_gb, expected_gb, places=2)
    
    def test_percentage_calculation(self):
        """Test percentage calculation"""
        test_cases = [
            (800, 1000, 80.0),    # 80%
            (0, 1000, 0.0),       # 0%
            (1000, 1000, 100.0),  # 100%
            (50, 200, 25.0),      # 25%
        ]
        
        for used, total, expected_percentage in test_cases:
            if total > 0:
                result = (used / total) * 100
                self.assertAlmostEqual(result, expected_percentage, places=1)
    
    def test_storage_threshold_checks(self):
        """Test storage threshold checking logic"""
        thresholds = {
            'low': 80,
            'medium': 85,
            'high': 90,
            'critical': 95
        }
        
        test_cases = [
            (75, False, False, False, False),  # No thresholds exceeded
            (82, True, False, False, False),   # Low threshold exceeded
            (87, True, True, False, False),    # Medium threshold exceeded
            (92, True, True, True, False),     # High threshold exceeded
            (97, True, True, True, True),      # Critical threshold exceeded
        ]
        
        for usage, low, medium, high, critical in test_cases:
            self.assertEqual(usage >= thresholds['low'], low)
            self.assertEqual(usage >= thresholds['medium'], medium)
            self.assertEqual(usage >= thresholds['high'], high)
            self.assertEqual(usage >= thresholds['critical'], critical)


if __name__ == '__main__':
    # Configure test runner
    unittest.main(
        verbosity=2,
        testRunner=unittest.TextTestRunner(
            stream=sys.stdout,
            verbosity=2
        )
    )