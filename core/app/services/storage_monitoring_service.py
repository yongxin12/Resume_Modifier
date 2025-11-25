"""
Google Drive Storage Monitoring Service
Monitors storage usage, sends warnings, and provides cleanup recommendations

Author: Resume Modifier Backend Team
Date: November 2024
"""

import logging
import smtplib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import current_app
from sqlalchemy import text
from googleapiclient.discovery import build
import google.oauth2.credentials

from app.extensions import db
from app.models.temp import GoogleAuth
from app.services.oauth_persistence_service import oauth_persistence_service


@dataclass
class StorageAlert:
    """Storage alert information"""
    level: str  # low, medium, high, critical
    usage_percentage: float
    total_gb: float
    used_gb: float
    available_gb: float
    message: str
    recommendations: List[str]
    timestamp: datetime


@dataclass
class FileAnalytics:
    """File analytics information"""
    file_id: str
    name: str
    size: int
    mime_type: str
    created_time: datetime
    modified_time: datetime
    is_large_file: bool = False
    is_old_file: bool = False


class StorageMonitoringService:
    """
    Service for monitoring Google Drive storage usage, sending alerts,
    and providing storage optimization recommendations.
    """

    def __init__(self):
        """Initialize the storage monitoring service."""
        self.logger = logging.getLogger(__name__)
        
        # Storage thresholds (percentages)
        self.thresholds = {
            'low': 80,      # First warning
            'medium': 85,   # Second warning
            'high': 90,     # Urgent warning
            'critical': 95  # Emergency warning
        }
        
        # File size thresholds
        self.large_file_threshold = 50 * 1024 * 1024  # 50 MB
        self.old_file_threshold_days = 365  # 1 year
        
        # Email configuration
        self.email_enabled = current_app.config.get('STORAGE_WARNING_EMAIL_ENABLED', False) if current_app else False
        self.email_from = current_app.config.get('STORAGE_WARNING_EMAIL_FROM', 'admin@resumemodifier.com') if current_app else 'admin@resumemodifier.com'
        self.email_to = current_app.config.get('STORAGE_WARNING_EMAIL_TO', 'admin@resumemodifier.com') if current_app else 'admin@resumemodifier.com'

    def check_all_storage_quotas(self) -> Dict[str, Any]:
        """
        Check storage quotas for all active OAuth sessions.
        
        Returns:
            Dict containing summary of all checks
        """
        try:
            active_sessions = GoogleAuth.query.filter_by(is_active=True).all()
            
            if not active_sessions:
                return {
                    'success': True,
                    'message': 'No active OAuth sessions to monitor',
                    'sessions_checked': 0,
                    'alerts_generated': 0,
                    'results': []
                }
            
            self.logger.info(f"Checking storage for {len(active_sessions)} active sessions")
            
            results = []
            alerts_generated = 0
            
            for auth in active_sessions:
                try:
                    result = self.check_storage_quota(auth.id)
                    results.append(result)
                    
                    if result.get('alert_generated'):
                        alerts_generated += 1
                        
                except Exception as e:
                    self.logger.error(f"Failed to check storage for auth {auth.id}: {e}")
                    results.append({
                        'auth_id': auth.id,
                        'user_id': auth.user_id,
                        'success': False,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'message': f'Checked storage for {len(active_sessions)} sessions',
                'sessions_checked': len(active_sessions),
                'alerts_generated': alerts_generated,
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error checking all storage quotas: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def check_storage_quota(self, auth_id: int) -> Dict[str, Any]:
        """
        Check storage quota for a specific OAuth session and generate alerts if needed.
        
        Args:
            auth_id: ID of the GoogleAuth record
            
        Returns:
            Dict containing quota information and alert status
        """
        try:
            auth = GoogleAuth.query.get(auth_id)
            if not auth or not auth.is_active:
                return {
                    'auth_id': auth_id,
                    'success': False,
                    'error': 'OAuth session not found or inactive'
                }
            
            # Get storage quota from Google Drive API
            quota_info = self._fetch_drive_quota(auth)
            if not quota_info:
                return {
                    'auth_id': auth_id,
                    'user_id': auth.user_id,
                    'success': False,
                    'error': 'Failed to fetch storage quota from Google Drive'
                }
            
            # Update database record
            auth.drive_quota_total = quota_info['total']
            auth.drive_quota_used = quota_info['used']
            auth.last_quota_check = datetime.utcnow()
            
            # Calculate usage percentage
            usage_percentage = (quota_info['used'] / quota_info['total'] * 100) if quota_info['total'] > 0 else 0
            
            # Determine warning level
            old_warning_level = auth.quota_warning_level
            new_warning_level = self._determine_warning_level(usage_percentage)
            
            # Generate alert if warning level changed or escalated
            alert_generated = False
            if new_warning_level != old_warning_level and new_warning_level != 'none':
                alert = self._create_storage_alert(auth, quota_info, usage_percentage, new_warning_level)
                self._process_storage_alert(auth, alert)
                alert_generated = True
            
            # Update warning level and history
            auth.quota_warning_level = new_warning_level
            self._update_warning_history(auth, old_warning_level, new_warning_level, usage_percentage)
            
            db.session.commit()
            
            result = {
                'auth_id': auth_id,
                'user_id': auth.user_id,
                'success': True,
                'quota': {
                    'total_bytes': quota_info['total'],
                    'used_bytes': quota_info['used'],
                    'available_bytes': quota_info['total'] - quota_info['used'],
                    'total_gb': round(quota_info['total'] / (1024**3), 2),
                    'used_gb': round(quota_info['used'] / (1024**3), 2),
                    'available_gb': round((quota_info['total'] - quota_info['used']) / (1024**3), 2),
                    'usage_percentage': round(usage_percentage, 2)
                },
                'warning_level': new_warning_level,
                'warning_level_changed': new_warning_level != old_warning_level,
                'alert_generated': alert_generated,
                'last_check': auth.last_quota_check.isoformat()
            }
            
            self.logger.info(f"Storage check for auth {auth_id}: {usage_percentage:.1f}% used ({new_warning_level})")
            return result
            
        except Exception as e:
            self.logger.error(f"Error checking storage quota for auth {auth_id}: {e}")
            return {
                'auth_id': auth_id,
                'success': False,
                'error': str(e)
            }

    def _fetch_drive_quota(self, auth: GoogleAuth) -> Optional[Dict[str, int]]:
        """
        Fetch storage quota information from Google Drive API.
        
        Args:
            auth: GoogleAuth record
            
        Returns:
            Dict with 'total' and 'used' quota in bytes, or None if failed
        """
        try:
            # Ensure token is valid
            if auth.token_expires_at <= datetime.utcnow():
                refresh_result = oauth_persistence_service.refresh_token_if_needed(auth.id)
                if not refresh_result.success:
                    self.logger.error(f"Cannot fetch quota: token refresh failed for auth {auth.id}")
                    return None
                # Reload auth record after refresh
                auth = GoogleAuth.query.get(auth.id)
            
            # Build credentials
            credentials = google.oauth2.credentials.Credentials(
                token=auth.access_token,
                refresh_token=auth.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=current_app.config.get('GOOGLE_CLIENT_ID'),
                client_secret=current_app.config.get('GOOGLE_CLIENT_SECRET'),
                scopes=auth.scope.split(' ') if auth.scope else []
            )
            
            # Build Drive service
            service = build('drive', 'v3', credentials=credentials)
            
            # Get storage quota
            about = service.about().get(fields='storageQuota').execute()
            quota = about.get('storageQuota', {})
            
            total_quota = int(quota.get('limit', 0))
            used_quota = int(quota.get('usage', 0))
            
            if total_quota == 0:
                self.logger.warning(f"Got zero quota limit for auth {auth.id}")
                return None
            
            return {
                'total': total_quota,
                'used': used_quota
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching Drive quota for auth {auth.id}: {e}")
            return None

    def _determine_warning_level(self, usage_percentage: float) -> str:
        """Determine warning level based on usage percentage."""
        if usage_percentage >= self.thresholds['critical']:
            return 'critical'
        elif usage_percentage >= self.thresholds['high']:
            return 'high'
        elif usage_percentage >= self.thresholds['medium']:
            return 'medium'
        elif usage_percentage >= self.thresholds['low']:
            return 'low'
        else:
            return 'none'

    def _create_storage_alert(self, auth: GoogleAuth, quota_info: Dict[str, int], 
                            usage_percentage: float, warning_level: str) -> StorageAlert:
        """Create a storage alert object."""
        total_gb = quota_info['total'] / (1024**3)
        used_gb = quota_info['used'] / (1024**3)
        available_gb = (quota_info['total'] - quota_info['used']) / (1024**3)
        
        # Generate appropriate message and recommendations
        message, recommendations = self._get_alert_content(warning_level, usage_percentage, available_gb)
        
        return StorageAlert(
            level=warning_level,
            usage_percentage=usage_percentage,
            total_gb=total_gb,
            used_gb=used_gb,
            available_gb=available_gb,
            message=message,
            recommendations=recommendations,
            timestamp=datetime.utcnow()
        )

    def _get_alert_content(self, warning_level: str, usage_percentage: float, 
                          available_gb: float) -> Tuple[str, List[str]]:
        """Get alert message and recommendations based on warning level."""
        if warning_level == 'critical':
            message = f"CRITICAL: Google Drive storage is {usage_percentage:.1f}% full. Only {available_gb:.1f} GB remaining."
            recommendations = [
                "🚨 IMMEDIATE ACTION REQUIRED",
                "Delete unnecessary files immediately",
                "Archive old files to free up space",
                "Consider upgrading Google Drive storage plan",
                "New file uploads may be disabled automatically"
            ]
        elif warning_level == 'high':
            message = f"HIGH WARNING: Google Drive storage is {usage_percentage:.1f}% full. Only {available_gb:.1f} GB remaining."
            recommendations = [
                "⚠️ URGENT: Take action within 24 hours",
                "Review and delete large files",
                "Archive files older than 6 months",
                "Empty trash to free up space",
                "Consider upgrading storage plan"
            ]
        elif warning_level == 'medium':
            message = f"MEDIUM WARNING: Google Drive storage is {usage_percentage:.1f}% full. {available_gb:.1f} GB remaining."
            recommendations = [
                "⚠️ Action recommended within one week",
                "Review and organize files",
                "Delete duplicate files",
                "Archive old project files",
                "Monitor storage usage more frequently"
            ]
        else:  # low
            message = f"Low warning: Google Drive storage is {usage_percentage:.1f}% full. {available_gb:.1f} GB remaining."
            recommendations = [
                "ℹ️ No immediate action required",
                "Start planning storage cleanup",
                "Review file organization",
                "Consider archiving old files",
                "Monitor storage growth trends"
            ]
        
        return message, recommendations

    def _process_storage_alert(self, auth: GoogleAuth, alert: StorageAlert):
        """Process a storage alert by logging and optionally sending emails."""
        # Log the alert
        log_level = logging.CRITICAL if alert.level == 'critical' else logging.WARNING
        self.logger.log(log_level, f"Storage alert for auth {auth.id}: {alert.message}")
        
        # Send email alert if enabled
        if self.email_enabled:
            try:
                self._send_email_alert(auth, alert)
            except Exception as e:
                self.logger.error(f"Failed to send email alert: {e}")

    def _send_email_alert(self, auth: GoogleAuth, alert: StorageAlert):
        """Send email alert for storage warning."""
        subject = f"Google Drive Storage Alert - {alert.level.upper()}"
        
        # Create email body
        body = f"""
Google Drive Storage Alert

User: {auth.email} (ID: {auth.user_id})
Alert Level: {alert.level.upper()}
Usage: {alert.usage_percentage:.1f}% ({alert.used_gb:.1f} GB / {alert.total_gb:.1f} GB)
Available Space: {alert.available_gb:.1f} GB
Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

{alert.message}

Recommendations:
"""
        
        for i, rec in enumerate(alert.recommendations, 1):
            body += f"{i}. {rec}\n"
        
        body += f"""

This alert was generated automatically by the Resume Modifier system.
Please take appropriate action to manage storage usage.

---
Resume Modifier Storage Monitoring System
"""
        
        # Send email (basic implementation - would need proper SMTP configuration)
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            
            # Note: This would need proper SMTP server configuration
            self.logger.info(f"Email alert prepared: {subject}")
            # In production, would actually send via SMTP
            
        except Exception as e:
            self.logger.error(f"Failed to prepare email alert: {e}")

    def _update_warning_history(self, auth: GoogleAuth, old_level: str, 
                               new_level: str, usage_percentage: float):
        """Update warning history for the auth record."""
        if not auth.quota_warnings_sent:
            auth.quota_warnings_sent = []
        
        # Add new entry to history
        warning_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'old_level': old_level,
            'new_level': new_level,
            'usage_percentage': round(usage_percentage, 2),
            'alert_sent': new_level != 'none' and new_level != old_level
        }
        
        auth.quota_warnings_sent.append(warning_entry)
        
        # Keep only last 20 warnings
        if len(auth.quota_warnings_sent) > 20:
            auth.quota_warnings_sent = auth.quota_warnings_sent[-20:]

    def get_storage_analytics(self, auth_id: int) -> Dict[str, Any]:
        """
        Get detailed storage analytics for an OAuth session.
        
        Args:
            auth_id: ID of the GoogleAuth record
            
        Returns:
            Dict containing detailed analytics
        """
        try:
            auth = GoogleAuth.query.get(auth_id)
            if not auth or not auth.is_active:
                return {
                    'success': False,
                    'error': 'OAuth session not found or inactive'
                }
            
            # Get file analytics from Google Drive
            file_analytics = self._analyze_drive_files(auth)
            
            # Calculate storage trends (would need historical data)
            storage_trend = self._calculate_storage_trend(auth)
            
            # Generate cleanup recommendations
            cleanup_recommendations = self._generate_cleanup_recommendations(file_analytics, auth)
            
            return {
                'success': True,
                'auth_id': auth_id,
                'user_id': auth.user_id,
                'current_usage': {
                    'total_bytes': auth.drive_quota_total or 0,
                    'used_bytes': auth.drive_quota_used or 0,
                    'usage_percentage': self._calculate_usage_percentage(auth),
                    'warning_level': auth.quota_warning_level or 'none'
                },
                'file_analytics': file_analytics,
                'storage_trend': storage_trend,
                'cleanup_recommendations': cleanup_recommendations,
                'warning_history': auth.quota_warnings_sent or [],
                'last_check': auth.last_quota_check.isoformat() if auth.last_quota_check else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting storage analytics for auth {auth_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _analyze_drive_files(self, auth: GoogleAuth) -> Dict[str, Any]:
        """Analyze files in Google Drive for storage optimization."""
        try:
            # This would require Google Drive API calls to list and analyze files
            # For now, return basic structure
            return {
                'total_files': 0,
                'large_files': [],
                'old_files': [],
                'file_types': {},
                'duplicate_candidates': []
            }
        except Exception as e:
            self.logger.error(f"Error analyzing Drive files for auth {auth.id}: {e}")
            return {
                'total_files': 0,
                'large_files': [],
                'old_files': [],
                'file_types': {},
                'duplicate_candidates': [],
                'error': str(e)
            }

    def _calculate_storage_trend(self, auth: GoogleAuth) -> Dict[str, Any]:
        """Calculate storage usage trend."""
        # Would need historical data to calculate actual trends
        # For now, return basic structure
        return {
            'trend': 'stable',
            'growth_rate_gb_per_month': 0.0,
            'projected_full_date': None,
            'data_points': []
        }

    def _generate_cleanup_recommendations(self, file_analytics: Dict[str, Any], 
                                        auth: GoogleAuth) -> List[str]:
        """Generate cleanup recommendations based on analytics."""
        recommendations = []
        
        usage_percentage = self._calculate_usage_percentage(auth)
        
        if usage_percentage > 90:
            recommendations.extend([
                "🚨 URGENT: Delete large files immediately",
                "🗑️ Empty Google Drive trash",
                "📦 Archive files older than 6 months",
                "🔄 Review and delete duplicate files"
            ])
        elif usage_percentage > 80:
            recommendations.extend([
                "📋 Review files larger than 50MB",
                "📅 Archive files older than 1 year",
                "🗂️ Organize files into folders",
                "🧹 Clean up duplicate files"
            ])
        else:
            recommendations.extend([
                "📊 Monitor storage usage monthly",
                "🗃️ Consider archiving old projects",
                "📱 Use selective sync if available"
            ])
        
        return recommendations

    def _calculate_usage_percentage(self, auth: GoogleAuth) -> float:
        """Calculate storage usage percentage."""
        if not auth.drive_quota_total or auth.drive_quota_total == 0:
            return 0.0
        return (auth.drive_quota_used or 0) / auth.drive_quota_total * 100

    def get_all_storage_status(self) -> Dict[str, Any]:
        """Get storage status summary for all active OAuth sessions."""
        try:
            active_sessions = GoogleAuth.query.filter_by(is_active=True).all()
            
            total_sessions = len(active_sessions)
            sessions_with_warnings = 0
            critical_sessions = 0
            total_storage_used = 0
            total_storage_quota = 0
            
            session_summaries = []
            
            for auth in active_sessions:
                usage_percentage = self._calculate_usage_percentage(auth)
                warning_level = auth.quota_warning_level or 'none'
                
                if warning_level != 'none':
                    sessions_with_warnings += 1
                
                if warning_level == 'critical':
                    critical_sessions += 1
                
                if auth.drive_quota_used:
                    total_storage_used += auth.drive_quota_used
                
                if auth.drive_quota_total:
                    total_storage_quota += auth.drive_quota_total
                
                session_summaries.append({
                    'auth_id': auth.id,
                    'user_id': auth.user_id,
                    'user_email': auth.email,
                    'usage_percentage': round(usage_percentage, 1),
                    'warning_level': warning_level,
                    'last_check': auth.last_quota_check.isoformat() if auth.last_quota_check else None
                })
            
            return {
                'success': True,
                'summary': {
                    'total_sessions': total_sessions,
                    'sessions_with_warnings': sessions_with_warnings,
                    'critical_sessions': critical_sessions,
                    'total_storage_used_gb': round(total_storage_used / (1024**3), 2) if total_storage_used else 0,
                    'total_storage_quota_gb': round(total_storage_quota / (1024**3), 2) if total_storage_quota else 0,
                    'overall_usage_percentage': round((total_storage_used / total_storage_quota * 100), 1) if total_storage_quota else 0
                },
                'sessions': session_summaries,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting all storage status: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Global service instance
storage_monitoring_service = StorageMonitoringService()