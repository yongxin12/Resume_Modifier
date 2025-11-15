"""
Performance Monitoring Integration for Google Drive Service

This module integrates performance monitoring into the Google Drive service
to track API call performance, identify bottlenecks, and optimize operations.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from functools import wraps

logger = logging.getLogger(__name__)


def monitor_google_drive_operation(operation_name: str):
    """
    Decorator to monitor Google Drive operations
    
    Args:
        operation_name: Name of the operation being monitored
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from app.utils.performance_optimizer import performance_monitor
            
            start_time = time.time()
            operation_id = f"google_drive_{operation_name}"
            
            try:
                with performance_monitor.time_operation(operation_id):
                    result = func(*args, **kwargs)
                
                # Log successful operation
                duration = (time.time() - start_time) * 1000
                logger.debug(f"Google Drive {operation_name} completed in {duration:.2f}ms")
                
                return result
                
            except Exception as e:
                # Log failed operation
                duration = (time.time() - start_time) * 1000
                logger.error(f"Google Drive {operation_name} failed after {duration:.2f}ms: {e}")
                
                # Record failure metric
                performance_monitor.record_metric(
                    f"{operation_id}_failures", 
                    duration, 
                    'ms'
                )
                
                raise
        
        return wrapper
    return decorator


class GoogleDrivePerformanceTracker:
    """Track performance metrics for Google Drive operations"""
    
    def __init__(self):
        self.operation_counts = {}
        self.rate_limit_hits = 0
        self.last_rate_limit_time = None
        
    def record_operation(self, operation_type: str, duration_ms: float, success: bool = True):
        """Record a Google Drive operation"""
        if operation_type not in self.operation_counts:
            self.operation_counts[operation_type] = {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'total_duration': 0,
                'avg_duration': 0
            }
        
        stats = self.operation_counts[operation_type]
        stats['total'] += 1
        stats['total_duration'] += duration_ms
        stats['avg_duration'] = stats['total_duration'] / stats['total']
        
        if success:
            stats['successful'] += 1
        else:
            stats['failed'] += 1
    
    def record_rate_limit_hit(self):
        """Record when we hit a rate limit"""
        self.rate_limit_hits += 1
        self.last_rate_limit_time = time.time()
        
        from app.utils.performance_optimizer import performance_monitor
        performance_monitor.record_metric("google_drive_rate_limits", 1, 'count')
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for Google Drive operations"""
        return {
            'operations': dict(self.operation_counts),
            'rate_limit_hits': self.rate_limit_hits,
            'last_rate_limit': self.last_rate_limit_time,
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Check for frequent rate limiting
        if self.rate_limit_hits > 10:
            recommendations.append(
                "High rate limit hits detected. Consider implementing exponential backoff."
            )
        
        # Check for slow operations
        for op_type, stats in self.operation_counts.items():
            if stats['avg_duration'] > 5000:  # 5 seconds
                recommendations.append(
                    f"Slow {op_type} operations detected (avg: {stats['avg_duration']:.0f}ms). "
                    f"Consider optimizing or using batch operations."
                )
        
        # Check for high failure rates
        for op_type, stats in self.operation_counts.items():
            failure_rate = stats['failed'] / stats['total'] if stats['total'] > 0 else 0
            if failure_rate > 0.1:  # 10% failure rate
                recommendations.append(
                    f"High failure rate for {op_type} operations ({failure_rate:.1%}). "
                    f"Review error handling and retry logic."
                )
        
        return recommendations


# Global performance tracker instance
gdrive_performance_tracker = GoogleDrivePerformanceTracker()


class OptimizedGoogleDriveServiceMixin:
    """
    Mixin class to add performance optimizations to GoogleDriveService
    
    This can be mixed into the existing GoogleDriveService class to add
    performance monitoring and optimization features.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performance_tracker = gdrive_performance_tracker
        self._operation_cache = {}
        self._last_cache_clear = time.time()
        
    @monitor_google_drive_operation("file_upload")
    def optimized_upload_file_to_drive(self, file_content: bytes, filename: str, 
                                     mime_type: str, user_id: int, 
                                     parent_folder_id: Optional[str] = None,
                                     credentials=None) -> Dict[str, Any]:
        """
        Optimized file upload with performance monitoring
        
        This method wraps the original upload with performance tracking
        and optimization features like retry logic and caching.
        """
        from app.utils.performance_optimizer import MemoryOptimizer
        
        # Optimize file operations
        file_info = MemoryOptimizer.optimize_file_operations(
            file_content, 
            ['size', 'type_check']
        )
        
        # Use original upload method with monitoring
        return self.upload_file_to_drive(
            file_content=file_content,
            filename=filename,
            mime_type=mime_type,
            user_id=user_id,
            parent_folder_id=parent_folder_id,
            credentials=credentials
        )
    
    def batch_share_files(self, file_operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Share multiple files in batch to reduce API calls
        
        Args:
            file_operations: List of share operation dictionaries
            
        Returns:
            List of sharing results
        """
        from app.utils.performance_optimizer import GoogleDriveAPIOptimizer
        
        optimizer = GoogleDriveAPIOptimizer()
        
        # Group operations by file_id to avoid duplicate API calls
        grouped_operations = {}
        for op in file_operations:
            file_id = op['file_id']
            if file_id not in grouped_operations:
                grouped_operations[file_id] = []
            grouped_operations[file_id].append(op)
        
        results = []
        for file_id, ops in grouped_operations.items():
            # Check cache first
            cached_permissions = optimizer.get_cached_permissions(file_id)
            
            if cached_permissions:
                # Use cached permissions
                for op in ops:
                    results.append({
                        'file_id': file_id,
                        'success': True,
                        'cached': True,
                        'permissions': cached_permissions
                    })
            else:
                # Make API call and cache result
                try:
                    permissions = self._share_file_batch(file_id, ops)
                    optimizer.cache_file_permissions(file_id, permissions)
                    
                    for op in ops:
                        results.append({
                            'file_id': file_id,
                            'success': True,
                            'cached': False,
                            'permissions': permissions
                        })
                        
                except Exception as e:
                    for op in ops:
                        results.append({
                            'file_id': file_id,
                            'success': False,
                            'error': str(e)
                        })
        
        return results
    
    def _share_file_batch(self, file_id: str, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch sharing operations for a single file"""
        # Implementation would depend on the specific sharing operations needed
        # This is a placeholder for the actual batch sharing logic
        pass
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this service instance"""
        from app.utils.performance_optimizer import performance_monitor
        
        return {
            'google_drive_operations': self.performance_tracker.get_performance_summary(),
            'general_metrics': {
                'upload_time_avg': performance_monitor.get_average_metric('google_drive_file_upload'),
                'conversion_time_avg': performance_monitor.get_average_metric('google_drive_conversion'),
                'sharing_time_avg': performance_monitor.get_average_metric('google_drive_sharing')
            }
        }
    
    def optimize_for_performance(self):
        """Apply performance optimizations based on current metrics"""
        metrics = self.get_performance_metrics()
        
        # Implement dynamic optimizations based on performance data
        # For example, adjust batch sizes, implement circuit breakers, etc.
        
        recommendations = metrics['google_drive_operations']['recommendations']
        for recommendation in recommendations:
            logger.info(f"Performance recommendation: {recommendation}")


# Utility functions for performance optimization

def optimize_google_drive_batch_size(operation_type: str, recent_performance: List[float]) -> int:
    """
    Dynamically optimize batch size based on recent performance
    
    Args:
        operation_type: Type of operation (upload, share, convert)
        recent_performance: List of recent operation times in milliseconds
        
    Returns:
        Optimized batch size
    """
    if not recent_performance:
        return 5  # Default batch size
    
    avg_time = sum(recent_performance) / len(recent_performance)
    
    # Adjust batch size based on average operation time
    if avg_time < 1000:  # Fast operations
        return min(20, 10)
    elif avg_time < 3000:  # Medium operations
        return min(10, 5)
    else:  # Slow operations
        return min(5, 3)


def implement_exponential_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """
    Implement exponential backoff for Google Drive API calls
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        
    Returns:
        Result of the function call
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries:
                    raise
                
                # Check if it's a rate limit error
                if hasattr(e, 'resp') and hasattr(e.resp, 'status'):
                    if e.resp.status == 429:  # Rate limit exceeded
                        gdrive_performance_tracker.record_rate_limit_hit()
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1})")
                        time.sleep(delay)
                        continue
                
                # For other errors, still retry with backoff
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Operation failed, retrying in {delay}s: {e}")
                time.sleep(delay)
    
    return wrapper