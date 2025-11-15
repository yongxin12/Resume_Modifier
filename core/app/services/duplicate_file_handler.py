"""
Duplicate File Handler Service

This service handles duplicate file detection, filename generation,
and manages the relationship between original files and their duplicates.
"""

import os
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from app.extensions import db
from app.models.temp import ResumeFile, User
from flask import current_app
import logging

# Set up logging
logger = logging.getLogger(__name__)


class DuplicateFileHandler:
    """Service for handling duplicate file detection and management."""
    
    @staticmethod
    def calculate_file_hash(file_content) -> str:
        """
        Calculate SHA-256 hash of file content using optimized chunked reading.
        
        Args:
            file_content: Binary content of the file (bytes, BytesIO, or file-like object)
            
        Returns:
            String representation of the file hash
        """
        from app.utils.performance_optimizer import OptimizedHashCalculator, performance_monitor
        
        with performance_monitor.time_operation("file_hash_calculation"):
            return OptimizedHashCalculator.calculate_hash_chunked(file_content)
    
    @staticmethod
    def find_existing_files(user_id: int, file_hash: str) -> List[ResumeFile]:
        """
        Find existing files with the same hash for a user using optimized query.
        
        Args:
            user_id: ID of the user
            file_hash: SHA-256 hash of the file
            
        Returns:
            List of existing ResumeFile instances with the same hash
        """
        from app.utils.performance_optimizer import OptimizedDatabaseQueries, performance_monitor
        
        try:
            with performance_monitor.time_operation("duplicate_file_query"):
                query = OptimizedDatabaseQueries.build_file_query_with_indexes(
                    user_id=user_id,
                    include_deleted=False,
                    file_hash=file_hash
                )
                existing_files = query.order_by(ResumeFile.duplicate_sequence.asc()).all()
            
            logger.info(f"Found {len(existing_files)} existing files with hash {file_hash[:16]}... for user {user_id}")
            return existing_files
            
        except Exception as e:
            logger.error(f"Error finding existing files: {str(e)}")
            return []
    
    @staticmethod
    def generate_duplicate_filename(original_filename: str, sequence: int) -> str:
        """
        Generate a filename for duplicate files with sequence number.
        
        Args:
            original_filename: Original filename
            sequence: Duplicate sequence number
            
        Returns:
            New filename with duplicate notation
            
        Examples:
            - "Resume.pdf" -> "Resume (1).pdf"
            - "Resume (1).pdf" -> "Resume (2).pdf"
            - "My Resume.docx" -> "My Resume (1).docx"
        """
        if sequence == 0:
            return original_filename
        
        # Split filename and extension
        name, ext = os.path.splitext(original_filename)
        
        # Remove existing duplicate notation if present
        # Handle cases like "Resume (1)" -> "Resume"
        import re
        duplicate_pattern = r'\s*\(\d+\)$'
        name_without_duplicate = re.sub(duplicate_pattern, '', name)
        
        # Generate new filename with sequence
        new_filename = f"{name_without_duplicate} ({sequence}){ext}"
        
        logger.debug(f"Generated duplicate filename: {original_filename} -> {new_filename}")
        return new_filename
    
    @staticmethod
    def get_next_duplicate_sequence(existing_files: List[ResumeFile]) -> int:
        """
        Get the next available duplicate sequence number.
        
        Args:
            existing_files: List of existing files with the same hash
            
        Returns:
            Next available sequence number
        """
        if not existing_files:
            return 0  # First file (original)
        
        # Find the highest sequence number
        max_sequence = max(file.duplicate_sequence for file in existing_files)
        next_sequence = max_sequence + 1
        
        logger.debug(f"Next duplicate sequence: {next_sequence}")
        return next_sequence
    
    @staticmethod
    def process_duplicate_file(
        user_id: int,
        original_filename: str,
        file_hash: str,
        file_content: bytes
    ) -> Dict[str, Any]:
        """
        Process a potentially duplicate file and generate appropriate metadata.
        
        Args:
            user_id: ID of the user uploading the file
            original_filename: Original filename from the upload
            file_hash: SHA-256 hash of the file content
            file_content: Binary content of the file
            
        Returns:
            Dictionary containing duplicate processing information:
            {
                'is_duplicate': bool,
                'display_filename': str,
                'duplicate_sequence': int,
                'original_file_id': int or None,
                'notification_message': str or None,
                'existing_files_count': int
            }
        """
        try:
            # Find existing files with the same hash
            existing_files = DuplicateFileHandler.find_existing_files(user_id, file_hash)
            
            result = {
                'is_duplicate': len(existing_files) > 0,
                'existing_files_count': len(existing_files),
                'file_hash': file_hash  # Add file_hash to the result
            }
            
            if not existing_files:
                # This is the original file
                result.update({
                    'display_filename': original_filename,
                    'duplicate_sequence': 0,
                    'original_file_id': None,
                    'notification_message': None
                })
                logger.info(f"Processing original file: {original_filename}")
                
            else:
                # This is a duplicate file
                next_sequence = DuplicateFileHandler.get_next_duplicate_sequence(existing_files)
                display_filename = DuplicateFileHandler.generate_duplicate_filename(
                    original_filename, next_sequence
                )
                
                # Find the original file (sequence 0) or the first file if no original
                original_file = next(
                    (f for f in existing_files if f.duplicate_sequence == 0), 
                    existing_files[0]
                )
                
                result.update({
                    'display_filename': display_filename,
                    'duplicate_sequence': next_sequence,
                    'original_file_id': original_file.id,
                    'notification_message': (
                        f"Duplicate file detected. This file already exists. "
                        f"Saved as '{display_filename}' to avoid conflicts."
                    )
                })
                
                logger.info(f"Processing duplicate file: {original_filename} -> {display_filename}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing duplicate file: {str(e)}")
            # Return safe defaults in case of error
            return {
                'is_duplicate': False,
                'display_filename': original_filename,
                'duplicate_sequence': 0,
                'original_file_id': None,
                'notification_message': None,
                'existing_files_count': 0,
                'error': str(e)
            }
    
    @staticmethod
    def get_duplicate_family(file_id: int) -> Dict[str, Any]:
        """
        Get all files in the same duplicate family (original + all duplicates).
        
        Args:
            file_id: ID of any file in the duplicate family
            
        Returns:
            Dictionary containing the duplicate family information
        """
        try:
            file = ResumeFile.query.get(file_id)
            if not file:
                return {'error': 'File not found'}
            
            # Find the original file
            if file.is_duplicate and file.original_file_id:
                original_file = ResumeFile.query.get(file.original_file_id)
            else:
                original_file = file
            
            if not original_file:
                return {'error': 'Original file not found'}
            
            # Get all files with the same hash and user
            family_files = ResumeFile.query.filter_by(
                user_id=original_file.user_id,
                file_hash=original_file.file_hash,
                is_active=True
            ).order_by(ResumeFile.duplicate_sequence.asc()).all()
            
            result = {
                'original_file': original_file.to_dict(),
                'duplicates': [f.to_dict() for f in family_files if f.is_duplicate],
                'total_files': len(family_files),
                'file_hash': original_file.file_hash
            }
            
            logger.info(f"Retrieved duplicate family for file {file_id}: {len(family_files)} files")
            return result
            
        except Exception as e:
            logger.error(f"Error getting duplicate family: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def remove_duplicate_from_family(file_id: int, permanent: bool = False) -> Dict[str, Any]:
        """
        Remove a file from its duplicate family.
        
        Args:
            file_id: ID of the file to remove
            permanent: Whether to permanently delete or soft delete
            
        Returns:
            Dictionary containing removal result information
        """
        try:
            file = ResumeFile.query.get(file_id)
            if not file:
                return {'error': 'File not found', 'success': False}
            
            # Get family information before removal
            family_info = DuplicateFileHandler.get_duplicate_family(file_id)
            
            if permanent:
                # Permanently delete the file
                db.session.delete(file)
                action = 'permanently deleted'
            else:
                # Soft delete the file
                file.soft_delete(file.user_id)  # Assuming current user is the owner
                action = 'soft deleted'
            
            db.session.commit()
            
            result = {
                'success': True,
                'action': action,
                'file_id': file_id,
                'was_duplicate': file.is_duplicate,
                'duplicate_sequence': file.duplicate_sequence,
                'remaining_files': family_info.get('total_files', 1) - 1
            }
            
            logger.info(f"File {file_id} {action} from duplicate family")
            return result
            
        except Exception as e:
            logger.error(f"Error removing file from duplicate family: {str(e)}")
            db.session.rollback()
            return {'error': str(e), 'success': False}
    
    @staticmethod
    def get_duplicate_statistics(user_id: int) -> Dict[str, Any]:
        """
        Get statistics about duplicate files for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary containing duplicate statistics
        """
        try:
            # Get all active files for the user
            user_files = ResumeFile.query.filter_by(
                user_id=user_id,
                is_active=True
            ).all()
            
            # Count duplicates
            total_files = len(user_files)
            duplicate_files = sum(1 for f in user_files if f.is_duplicate)
            original_files = total_files - duplicate_files
            
            # Count unique file families (by hash)
            unique_hashes = set(f.file_hash for f in user_files)
            unique_file_families = len(unique_hashes)
            
            # Find files with the most duplicates
            hash_counts = {}
            for file in user_files:
                hash_counts[file.file_hash] = hash_counts.get(file.file_hash, 0) + 1
            
            most_duplicated_count = max(hash_counts.values()) if hash_counts else 0
            
            result = {
                'total_files': total_files,
                'original_files': original_files,
                'duplicate_files': duplicate_files,
                'unique_file_families': unique_file_families,
                'most_duplicates_count': most_duplicated_count - 1,  # Subtract 1 for original
                'storage_saved_by_deduplication': 0  # Would need file sizes to calculate
            }
            
            logger.info(f"Generated duplicate statistics for user {user_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating duplicate statistics: {str(e)}")
            return {'error': str(e)}


class DuplicateFileError(Exception):
    """Custom exception for duplicate file handling errors."""
    pass