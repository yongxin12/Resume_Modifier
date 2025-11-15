"""
Performance Optimization for Enhanced File Management System

This module provides optimizations for:
1. File hash calculations with chunked reading
2. Database queries with proper indexing
3. Google Drive API calls with batching and caching
4. Memory usage optimization for large files
"""

import os
import hashlib
import asyncio
import threading
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import time
import logging

logger = logging.getLogger(__name__)


class OptimizedHashCalculator:
    """Optimized file hash calculation with chunked reading and threading"""
    
    DEFAULT_CHUNK_SIZE = 64 * 1024  # 64KB chunks
    MAX_WORKERS = 4  # Maximum number of worker threads
    
    @staticmethod
    def calculate_hash_chunked(file_content, chunk_size=None, algorithm='sha256'):
        """
        Calculate file hash using chunked reading for memory efficiency
        
        Args:
            file_content: File content (bytes, BytesIO, or file-like object)
            chunk_size: Size of chunks to read (default: 64KB)
            algorithm: Hash algorithm to use (default: sha256)
            
        Returns:
            Hexadecimal hash string
        """
        chunk_size = chunk_size or OptimizedHashCalculator.DEFAULT_CHUNK_SIZE
        
        if algorithm == 'sha256':
            hasher = hashlib.sha256()
        elif algorithm == 'md5':
            hasher = hashlib.md5()
        else:
            hasher = hashlib.new(algorithm)
        
        # Handle different input types
        if hasattr(file_content, 'read'):
            # File-like object
            original_position = file_content.tell() if hasattr(file_content, 'tell') else 0
            
            if hasattr(file_content, 'seek'):
                file_content.seek(0)
            
            while True:
                chunk = file_content.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
            
            # Restore original position
            if hasattr(file_content, 'seek'):
                file_content.seek(original_position)
                
        else:
            # Direct bytes content - process in chunks for consistency
            for i in range(0, len(file_content), chunk_size):
                chunk = file_content[i:i + chunk_size]
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    @classmethod
    def calculate_multiple_hashes(cls, file_contents: List[Tuple[Any, str]], chunk_size=None):
        """
        Calculate hashes for multiple files using thread pool
        
        Args:
            file_contents: List of (file_content, identifier) tuples
            chunk_size: Size of chunks to read
            
        Returns:
            Dict mapping identifiers to hash values
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=cls.MAX_WORKERS) as executor:
            # Submit all hash calculation tasks
            future_to_id = {
                executor.submit(cls.calculate_hash_chunked, content, chunk_size): identifier
                for content, identifier in file_contents
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_id):
                identifier = future_to_id[future]
                try:
                    hash_value = future.result()
                    results[identifier] = hash_value
                except Exception as e:
                    logger.error(f"Hash calculation failed for {identifier}: {e}")
                    results[identifier] = None
        
        return results


class OptimizedDatabaseQueries:
    """Optimized database queries for duplicate detection and file management"""
    
    @staticmethod
    def build_file_query_with_indexes(user_id: int, include_deleted: bool = False, 
                                     file_hash: Optional[str] = None):
        """
        Build optimized query for file operations using proper indexes
        
        Args:
            user_id: ID of the user
            include_deleted: Whether to include soft-deleted files
            file_hash: Optional hash for duplicate detection
            
        Returns:
            SQLAlchemy query object
        """
        from app.models.temp import ResumeFile
        from app.extensions import db
        
        # Start with base query using indexed user_id
        query = db.session.query(ResumeFile).filter(ResumeFile.user_id == user_id)
        
        # Add hash filter if provided (uses hash index)
        if file_hash:
            query = query.filter(ResumeFile.file_hash == file_hash)
        
        # Filter deleted files (uses deleted_at index)
        if not include_deleted:
            query = query.filter(ResumeFile.deleted_at.is_(None))
        
        return query
    
    @staticmethod
    def batch_duplicate_check(user_id: int, file_hashes: List[str]) -> Dict[str, List[dict]]:
        """
        Check for duplicates of multiple files in a single query
        
        Args:
            user_id: ID of the user
            file_hashes: List of file hashes to check
            
        Returns:
            Dict mapping hashes to lists of duplicate file info
        """
        from app.models.temp import ResumeFile
        from app.extensions import db
        
        # Single query to check all hashes at once
        existing_files = db.session.query(
            ResumeFile.file_hash,
            ResumeFile.id,
            ResumeFile.original_filename,
            ResumeFile.display_filename,
            ResumeFile.uploaded_at
        ).filter(
            ResumeFile.user_id == user_id,
            ResumeFile.file_hash.in_(file_hashes),
            ResumeFile.deleted_at.is_(None)
        ).all()
        
        # Group results by hash
        results = {hash_val: [] for hash_val in file_hashes}
        
        for file_info in existing_files:
            results[file_info.file_hash].append({
                'id': file_info.id,
                'original_filename': file_info.original_filename,
                'display_filename': file_info.display_filename,
                'uploaded_at': file_info.uploaded_at.isoformat() if file_info.uploaded_at else None
            })
        
        return results
    
    @staticmethod
    def get_duplicate_sequence_batch(user_id: int, filename_patterns: List[str]) -> Dict[str, int]:
        """
        Get duplicate sequence numbers for multiple filename patterns
        
        Args:
            user_id: ID of the user
            filename_patterns: List of filename patterns to check
            
        Returns:
            Dict mapping patterns to highest sequence numbers
        """
        from app.models.temp import ResumeFile
        from app.extensions import db
        from sqlalchemy import func, or_
        
        # Build conditions for all patterns
        conditions = []
        for pattern in filename_patterns:
            base_name = pattern.split('.')[0]  # Remove extension
            like_pattern = f"{base_name} (%"
            conditions.append(ResumeFile.display_filename.like(like_pattern))
        
        # Single query to get all matching files
        if conditions:
            existing_files = db.session.query(
                ResumeFile.display_filename
            ).filter(
                ResumeFile.user_id == user_id,
                ResumeFile.deleted_at.is_(None),
                or_(*conditions)
            ).all()
            
            # Extract sequence numbers for each pattern
            results = {}
            for pattern in filename_patterns:
                base_name = pattern.split('.')[0]
                max_sequence = 0
                
                for file_info in existing_files:
                    filename = file_info.display_filename
                    if filename.startswith(base_name + ' (') and filename.endswith(')'):
                        try:
                            # Extract sequence number from filename like "resume (2).pdf"
                            seq_part = filename[len(base_name) + 2:-1]  # Extract number
                            if seq_part.endswith(').' + pattern.split('.')[-1]):
                                seq_part = seq_part[:-len('.' + pattern.split('.')[-1])]
                            sequence = int(seq_part)
                            max_sequence = max(max_sequence, sequence)
                        except (ValueError, IndexError):
                            continue
                
                results[pattern] = max_sequence
            
            return results
        
        return {pattern: 0 for pattern in filename_patterns}


class GoogleDriveAPIOptimizer:
    """Optimizations for Google Drive API calls"""
    
    def __init__(self, cache_ttl=300):  # 5-minute cache TTL
        """
        Initialize with caching configuration
        
        Args:
            cache_ttl: Cache time-to-live in seconds
        """
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_timestamps = {}
    
    @lru_cache(maxsize=128)
    def _get_cached_service_info(self, credentials_hash: str):
        """Cache Google Drive service information"""
        # This would cache service account information
        # to avoid repeated authentication overhead
        pass
    
    def batch_upload_files(self, files_data: List[Dict[str, Any]], 
                          drive_service) -> List[Dict[str, Any]]:
        """
        Upload multiple files to Google Drive using batch requests
        
        Args:
            files_data: List of file data dictionaries
            drive_service: Google Drive service instance
            
        Returns:
            List of upload results
        """
        from googleapiclient.http import BatchHttpRequest
        
        results = []
        batch_size = 10  # Process in batches of 10
        
        for i in range(0, len(files_data), batch_size):
            batch = files_data[i:i + batch_size]
            batch_results = self._process_batch_upload(batch, drive_service)
            results.extend(batch_results)
            
            # Small delay between batches to respect rate limits
            if i + batch_size < len(files_data):
                time.sleep(0.1)
        
        return results
    
    def _process_batch_upload(self, batch_files: List[Dict[str, Any]], 
                             drive_service) -> List[Dict[str, Any]]:
        """Process a batch of file uploads"""
        from googleapiclient.http import BatchHttpRequest
        
        def callback(request_id, response, exception):
            """Callback for batch request completion"""
            if exception:
                logger.error(f"Batch upload failed for {request_id}: {exception}")
                batch_results[request_id] = {'success': False, 'error': str(exception)}
            else:
                batch_results[request_id] = {'success': True, 'response': response}
        
        batch_results = {}
        batch_request = BatchHttpRequest(callback=callback)
        
        # Add all uploads to the batch
        for idx, file_data in enumerate(batch_files):
            try:
                from googleapiclient.http import MediaIoBaseUpload
                from io import BytesIO
                
                media = MediaIoBaseUpload(
                    BytesIO(file_data['content']),
                    mimetype=file_data['mime_type'],
                    resumable=True
                )
                
                body = {
                    'name': file_data['filename'],
                    'parents': file_data.get('parents', [])
                }
                
                request = drive_service.files().create(
                    body=body,
                    media_body=media,
                    fields='id, name, mimeType, size, webViewLink'
                )
                
                batch_request.add(request, request_id=str(idx))
                
            except Exception as e:
                logger.error(f"Failed to add file {file_data['filename']} to batch: {e}")
                batch_results[str(idx)] = {'success': False, 'error': str(e)}
        
        # Execute the batch request
        try:
            batch_request.execute()
        except Exception as e:
            logger.error(f"Batch request execution failed: {e}")
        
        return [batch_results.get(str(i), {'success': False, 'error': 'Unknown error'}) 
                for i in range(len(batch_files))]
    
    def cache_file_permissions(self, file_id: str, permissions: Dict[str, Any]):
        """Cache file permissions to avoid repeated API calls"""
        cache_key = f"permissions_{file_id}"
        self._cache[cache_key] = permissions
        self._cache_timestamps[cache_key] = time.time()
    
    def get_cached_permissions(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get cached file permissions if still valid"""
        cache_key = f"permissions_{file_id}"
        
        if cache_key in self._cache:
            cache_time = self._cache_timestamps.get(cache_key, 0)
            if time.time() - cache_time < self.cache_ttl:
                return self._cache[cache_key]
            else:
                # Cache expired, remove it
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]
        
        return None


class MemoryOptimizer:
    """Memory usage optimization for large file operations"""
    
    @staticmethod
    def process_large_file_streaming(file_content, chunk_size=8192, max_memory=100*1024*1024):
        """
        Process large files using streaming to minimize memory usage
        
        Args:
            file_content: File content (file-like object)
            chunk_size: Size of chunks to process
            max_memory: Maximum memory usage threshold in bytes
            
        Yields:
            Chunks of file content
        """
        total_read = 0
        
        while True:
            # Check memory usage threshold
            if total_read > max_memory:
                logger.warning(f"File size ({total_read} bytes) exceeds memory threshold")
                break
            
            chunk = file_content.read(chunk_size)
            if not chunk:
                break
                
            total_read += len(chunk)
            yield chunk
    
    @staticmethod
    def optimize_file_operations(file_data: bytes, operations: List[str]) -> Dict[str, Any]:
        """
        Optimize multiple file operations to minimize memory copies
        
        Args:
            file_data: File content as bytes
            operations: List of operations to perform ('hash', 'size', 'type_check')
            
        Returns:
            Dict with results of all operations
        """
        results = {}
        
        # Single pass through the file data for multiple operations
        if 'size' in operations:
            results['size'] = len(file_data)
        
        if 'hash' in operations:
            results['hash'] = OptimizedHashCalculator.calculate_hash_chunked(file_data)
        
        if 'type_check' in operations:
            # Check file type from first few bytes
            file_signature = file_data[:20] if len(file_data) >= 20 else file_data
            results['mime_type'] = MemoryOptimizer._detect_mime_type(file_signature)
        
        return results
    
    @staticmethod
    def _detect_mime_type(signature: bytes) -> str:
        """Detect MIME type from file signature"""
        if signature.startswith(b'%PDF'):
            return 'application/pdf'
        elif signature.startswith(b'PK\x03\x04') or signature.startswith(b'PK\x05\x06'):
            # ZIP-based formats (including DOCX)
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            return 'application/octet-stream'


class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    def time_operation(self, operation_name: str):
        """Context manager to time operations"""
        return OperationTimer(operation_name, self)
    
    def record_metric(self, name: str, value: float, unit: str = 'ms'):
        """Record a performance metric"""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            'value': value,
            'unit': unit,
            'timestamp': time.time()
        })
        
        # Keep only recent metrics (last 100 entries)
        if len(self.metrics[name]) > 100:
            self.metrics[name] = self.metrics[name][-100:]
    
    def get_average_metric(self, name: str, recent_count: int = 10) -> Optional[float]:
        """Get average value for a metric"""
        if name not in self.metrics or not self.metrics[name]:
            return None
        
        recent_values = [m['value'] for m in self.metrics[name][-recent_count:]]
        return sum(recent_values) / len(recent_values)
    
    def log_performance_summary(self):
        """Log performance summary"""
        logger.info("Performance Metrics Summary:")
        for name, values in self.metrics.items():
            if values:
                avg = self.get_average_metric(name)
                recent_value = values[-1]['value']
                unit = values[-1]['unit']
                logger.info(f"  {name}: {recent_value:.2f}{unit} (avg: {avg:.2f}{unit})")


class OperationTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str, monitor: PerformanceMonitor):
        self.operation_name = operation_name
        self.monitor = monitor
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (time.time() - self.start_time) * 1000  # Convert to milliseconds
            self.monitor.record_metric(self.operation_name, duration, 'ms')


# Global performance monitor instance
performance_monitor = PerformanceMonitor()