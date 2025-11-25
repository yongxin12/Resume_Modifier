"""
Background Storage Monitoring and Alert Service
Runs periodic checks for storage quotas and sends alerts when thresholds are exceeded

Author: Resume Modifier Backend Team
Date: November 2024
"""

import logging
import threading
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from flask import Flask
from sqlalchemy import text

from app.extensions import db
from app.models.temp import GoogleAuth
from app.services.storage_monitoring_service import storage_monitoring_service


class BackgroundStorageMonitor:
    """
    Background service that monitors storage usage for all active OAuth sessions
    and generates alerts when storage thresholds are exceeded.
    """

    def __init__(self, app: Optional[Flask] = None):
        """Initialize the background storage monitor."""
        self.app = app
        self.logger = logger = logging.getLogger(__name__)
        
        # Service configuration
        self.check_interval_minutes = 60  # Check every hour by default
        self.enabled = True
        self.running = False
        
        # Threading
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Statistics
        self.stats = {
            'service_started': None,
            'last_check': None,
            'total_checks': 0,
            'total_alerts_sent': 0,
            'last_error': None,
            'consecutive_errors': 0
        }

    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
        
        # Load configuration
        self.enabled = app.config.get('STORAGE_MONITORING_ENABLED', True)
        self.check_interval_minutes = app.config.get('STORAGE_CHECK_INTERVAL_MINUTES', 60)
        
        self.logger.info(f"Storage monitor initialized: enabled={self.enabled}, interval={self.check_interval_minutes}min")

    def start(self) -> Dict[str, Any]:
        """
        Start the background storage monitoring service.
        
        Returns:
            Dict with start result
        """
        try:
            if not self.enabled:
                return {
                    'success': False,
                    'message': 'Storage monitoring is disabled in configuration',
                    'running': False
                }
            
            if self.running:
                return {
                    'success': True,
                    'message': 'Storage monitoring service is already running',
                    'running': True,
                    'stats': self.get_stats()
                }
            
            # Start the monitoring thread
            self.stop_event.clear()
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                name='StorageMonitor',
                daemon=True
            )
            self.monitor_thread.start()
            
            self.running = True
            self.stats['service_started'] = datetime.utcnow()
            
            self.logger.info("Background storage monitoring service started")
            
            return {
                'success': True,
                'message': f'Storage monitoring service started (checking every {self.check_interval_minutes} minutes)',
                'running': True,
                'check_interval_minutes': self.check_interval_minutes,
                'stats': self.get_stats()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start storage monitoring service: {e}")
            return {
                'success': False,
                'error': str(e),
                'running': False
            }

    def stop(self) -> Dict[str, Any]:
        """
        Stop the background storage monitoring service.
        
        Returns:
            Dict with stop result
        """
        try:
            if not self.running:
                return {
                    'success': True,
                    'message': 'Storage monitoring service is not running',
                    'running': False
                }
            
            # Signal the thread to stop
            self.stop_event.set()
            
            # Wait for thread to finish (with timeout)
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=10)
                
                if self.monitor_thread.is_alive():
                    self.logger.warning("Storage monitoring thread did not stop gracefully")
            
            self.running = False
            self.monitor_thread = None
            
            self.logger.info("Background storage monitoring service stopped")
            
            return {
                'success': True,
                'message': 'Storage monitoring service stopped',
                'running': False,
                'final_stats': self.get_stats()
            }
            
        except Exception as e:
            self.logger.error(f"Error stopping storage monitoring service: {e}")
            return {
                'success': False,
                'error': str(e),
                'running': self.running
            }

    def restart(self) -> Dict[str, Any]:
        """
        Restart the background storage monitoring service.
        
        Returns:
            Dict with restart result
        """
        self.logger.info("Restarting storage monitoring service")
        
        stop_result = self.stop()
        if not stop_result['success']:
            return stop_result
        
        # Wait a moment for cleanup
        time.sleep(1)
        
        return self.start()

    def force_check_now(self) -> Dict[str, Any]:
        """
        Force an immediate storage check for all active sessions.
        
        Returns:
            Dict with check results
        """
        try:
            if not self.app:
                return {
                    'success': False,
                    'error': 'Flask app not initialized'
                }
            
            self.logger.info("Running forced storage check")
            
            with self.app.app_context():
                result = storage_monitoring_service.check_all_storage_quotas()
                
                # Update stats
                self.stats['last_check'] = datetime.utcnow()
                self.stats['total_checks'] += 1
                if result.get('alerts_generated', 0) > 0:
                    self.stats['total_alerts_sent'] += result['alerts_generated']
                
                result['forced_check'] = True
                return result
            
        except Exception as e:
            self.logger.error(f"Error during forced storage check: {e}")
            self.stats['last_error'] = str(e)
            self.stats['consecutive_errors'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'forced_check': True
            }

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the storage monitoring service.
        
        Returns:
            Dict with service status
        """
        return {
            'enabled': self.enabled,
            'running': self.running,
            'check_interval_minutes': self.check_interval_minutes,
            'thread_alive': self.monitor_thread.is_alive() if self.monitor_thread else False,
            'stats': self.get_stats(),
            'config': {
                'storage_monitoring_enabled': self.enabled,
                'check_interval_minutes': self.check_interval_minutes,
                'app_initialized': self.app is not None
            }
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        stats = self.stats.copy()
        
        # Convert datetime objects to ISO strings
        for key in ['service_started', 'last_check']:
            if stats[key]:
                stats[key] = stats[key].isoformat()
        
        # Add derived stats
        if self.stats['service_started']:
            uptime = datetime.utcnow() - self.stats['service_started']
            stats['uptime_seconds'] = int(uptime.total_seconds())
            stats['uptime_hours'] = round(uptime.total_seconds() / 3600, 1)
        
        return stats

    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread."""
        self.logger.info(f"Storage monitoring loop started (interval: {self.check_interval_minutes} minutes)")
        
        while not self.stop_event.is_set():
            try:
                # Perform storage check
                if self.app:
                    with self.app.app_context():
                        result = storage_monitoring_service.check_all_storage_quotas()
                        
                        # Update stats
                        self.stats['last_check'] = datetime.utcnow()
                        self.stats['total_checks'] += 1
                        
                        if result.get('success'):
                            self.stats['consecutive_errors'] = 0
                            alerts_generated = result.get('alerts_generated', 0)
                            if alerts_generated > 0:
                                self.stats['total_alerts_sent'] += alerts_generated
                                self.logger.info(f"Storage check completed: {alerts_generated} alerts generated")
                            else:
                                self.logger.debug("Storage check completed: no alerts needed")
                        else:
                            self.stats['last_error'] = result.get('error', 'Unknown error')
                            self.stats['consecutive_errors'] += 1
                            self.logger.error(f"Storage check failed: {result.get('error')}")
                
                # Wait for next check (or until stop signal)
                self.stop_event.wait(timeout=self.check_interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"Error in storage monitoring loop: {e}")
                self.stats['last_error'] = str(e)
                self.stats['consecutive_errors'] += 1
                
                # Wait before retrying (shorter interval on error)
                self.stop_event.wait(timeout=300)  # 5 minutes on error
        
        self.logger.info("Storage monitoring loop stopped")

    def update_config(self, check_interval_minutes: Optional[int] = None, 
                     enabled: Optional[bool] = None) -> Dict[str, Any]:
        """
        Update service configuration.
        
        Args:
            check_interval_minutes: New check interval
            enabled: Enable/disable the service
            
        Returns:
            Dict with update result
        """
        try:
            old_config = {
                'check_interval_minutes': self.check_interval_minutes,
                'enabled': self.enabled
            }
            
            needs_restart = False
            
            if check_interval_minutes is not None and check_interval_minutes != self.check_interval_minutes:
                if check_interval_minutes < 5:
                    return {
                        'success': False,
                        'error': 'Check interval must be at least 5 minutes'
                    }
                self.check_interval_minutes = check_interval_minutes
                needs_restart = True
            
            if enabled is not None and enabled != self.enabled:
                self.enabled = enabled
                needs_restart = True
            
            result = {
                'success': True,
                'message': 'Configuration updated',
                'old_config': old_config,
                'new_config': {
                    'check_interval_minutes': self.check_interval_minutes,
                    'enabled': self.enabled
                },
                'needs_restart': needs_restart
            }
            
            # Restart if needed and currently running
            if needs_restart and self.running:
                restart_result = self.restart()
                result['restart_result'] = restart_result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error updating storage monitoring config: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global service instance
background_storage_monitor = BackgroundStorageMonitor()