"""
Enhanced File Upload Service with Proper Transaction Management
Fixes PostgreSQL InFailedSqlTransaction errors and improves error handling
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.temp import ResumeFile, User
from app.services.file_storage_service import FileStorageService
from app.services.file_processing_service import FileProcessingService
from app.services.duplicate_file_handler import DuplicateFileHandler
from app.utils.file_validator import FileValidator
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import os
import time

logger = logging.getLogger(__name__)

class TransactionSafeFileUploadService:
    """
    File upload service with proper transaction management and error handling.
    Prevents PostgreSQL InFailedSqlTransaction errors through proper isolation.
    """
    
    def __init__(self):
        """Initialize the service with required components."""
        self.file_validator = FileValidator()
        self.duplicate_handler = DuplicateFileHandler()
        self.file_storage_service = None
        self.file_processor = FileProcessingService()
    
    def upload_file(
        self,
        uploaded_file,
        user_id: int,
        user_email: str = None,
        process_content: bool = True,
        upload_to_google_drive: bool = True,
        convert_to_doc: bool = True,
        share_with_user: bool = True
    ) -> Dict[str, Any]:
        """
        Upload file with proper transaction isolation and error handling.
        
        Args:
            uploaded_file: Flask file upload object
            user_id: ID of the user uploading the file
            user_email: User's email for Google Drive sharing
            process_content: Whether to extract text content
            upload_to_google_drive: Whether to upload to admin's Google Drive
            convert_to_doc: Whether to convert to Google Doc
            share_with_user: Whether to share with user
            
        Returns:
            dict: Upload result with file information and status
        """
        logger.info(f"Starting file upload for user {user_id}: {uploaded_file.filename}")
        
        # Step 1: Validate file (no database operations)
        validation_result = self._validate_file(uploaded_file)
        if not validation_result['success']:
            return validation_result
        
        # Step 2: Process duplicate detection (read-only database operations)
        duplicate_result = self._process_duplicates(uploaded_file, user_id)
        if not duplicate_result['success']:
            return duplicate_result
        
        # Step 3: Upload to storage (no database operations)
        storage_result = self._upload_to_storage(uploaded_file, user_id, duplicate_result['display_filename'])
        if not storage_result['success']:
            return storage_result
        
        # Step 4: Process file content (no database operations)
        processing_result = self._process_file_content(uploaded_file, process_content)
        
        # Step 5: Handle Google Drive upload (isolated, no database transaction)
        google_drive_result = self._handle_google_drive_upload(
            uploaded_file, user_id, user_email, duplicate_result['display_filename'],
            upload_to_google_drive, convert_to_doc, share_with_user
        )
        
        # Step 6: Save to database (isolated transaction)
        database_result = self._save_to_database(
            uploaded_file, user_id, validation_result, duplicate_result,
            storage_result, processing_result, google_drive_result
        )
        
        if not database_result['success']:
            # Clean up storage if database save failed
            self._cleanup_storage(storage_result)
            return database_result
        
        # Step 7: Generate response
        return self._generate_response(
            database_result['file_record'], duplicate_result, storage_result,
            processing_result, google_drive_result
        )
    
    def _validate_file(self, uploaded_file) -> Dict[str, Any]:
        """Validate uploaded file without database operations."""
        try:
            validation_result = self.file_validator.validate_file(uploaded_file)
            
            if not validation_result.is_valid:
                return {
                    'success': False,
                    'message': 'File validation failed',
                    'errors': validation_result.errors
                }
            
            return {
                'success': True,
                'validation': validation_result
            }
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return {
                'success': False,
                'message': 'File validation failed',
                'error': str(e)
            }
    
    def _process_duplicates(self, uploaded_file, user_id: int) -> Dict[str, Any]:
        """Process duplicate detection with read-only database operations."""
        try:
            uploaded_file.seek(0)
            file_content = uploaded_file.read()
            file_hash = self.duplicate_handler.calculate_file_hash(file_content)
            
            duplicate_result = self.duplicate_handler.process_duplicate_file(
                user_id, uploaded_file.filename, file_hash, file_content
            )
            
            return {
                'success': True,
                'is_duplicate': duplicate_result['is_duplicate'],
                'display_filename': duplicate_result['display_filename'],
                'file_hash': duplicate_result['file_hash'],
                'notification_message': duplicate_result.get('notification_message'),
                'duplicate_sequence': duplicate_result.get('duplicate_sequence'),
                'original_file_id': duplicate_result.get('original_file_id')
            }
            
        except Exception as e:
            logger.error(f"Duplicate processing error: {e}")
            # Fallback: use original filename
            uploaded_file.seek(0)
            try:
                file_content = uploaded_file.read()
                file_hash = self.duplicate_handler.calculate_file_hash(file_content)
            except:
                file_hash = f"fallback_{int(time.time())}"
            
            return {
                'success': True,
                'is_duplicate': False,
                'display_filename': uploaded_file.filename,
                'file_hash': file_hash,
                'notification_message': None,
                'duplicate_sequence': 0,
                'original_file_id': None
            }
    
    def _upload_to_storage(self, uploaded_file, user_id: int, display_filename: str) -> Dict[str, Any]:
        """Upload file to storage without database operations."""
        try:
            # Initialize storage service
            if not self.file_storage_service:
                from app.utils.storage_config import StorageConfigManager
                storage_config = StorageConfigManager.get_storage_config_dict()
                self.file_storage_service = FileStorageService(storage_config)
            
            uploaded_file.seek(0)
            storage_result = self.file_storage_service.upload_file(
                file_storage=uploaded_file,
                user_id=user_id,
                filename=display_filename
            )
            
            if not storage_result.success:
                return {
                    'success': False,
                    'message': 'File storage failed',
                    'error': storage_result.error_message
                }
            
            return {
                'success': True,
                'storage_result': storage_result
            }
            
        except Exception as e:
            logger.error(f"Storage upload error: {e}")
            return {
                'success': False,
                'message': 'File storage failed',
                'error': str(e)
            }
    
    def _process_file_content(self, uploaded_file, process_content: bool) -> Dict[str, Any]:
        """Process file content without database operations."""
        if not process_content:
            return {'success': True, 'processed': False}
        
        try:
            uploaded_file.seek(0)
            processing_result = self.file_processor.process_file(uploaded_file)
            
            return {
                'success': True,
                'processed': processing_result.success,
                'extracted_text': processing_result.text if processing_result.success else None,
                'processing_error': processing_result.error_message if not processing_result.success else None,
                'metadata': processing_result.metadata or {},
                'keywords': processing_result.keywords or [],
                'language': processing_result.language,
                'page_count': processing_result.page_count,
                'paragraph_count': processing_result.paragraph_count
            }
            
        except Exception as e:
            logger.error(f"File processing error: {e}")
            return {
                'success': True,
                'processed': False,
                'processing_error': str(e)
            }
    
    def _handle_google_drive_upload(
        self, uploaded_file, user_id: int, user_email: str, display_filename: str,
        upload_to_google_drive: bool, convert_to_doc: bool, share_with_user: bool
    ) -> Dict[str, Any]:
        """Handle Google Drive upload without database transactions."""
        if not upload_to_google_drive:
            return {'success': True, 'uploaded': False}
        
        try:
            from app.services.google_drive_admin_service import GoogleDriveAdminService
            google_drive_service = GoogleDriveAdminService()
            
            # Check admin authentication
            auth_status = google_drive_service.check_admin_auth_status()
            if not auth_status.get('authenticated'):
                logger.warning("Google Drive admin authentication not available")
                return {
                    'success': True,
                    'uploaded': False,
                    'warning': f"Google Drive admin authentication required. {auth_status.get('message', '')}"
                }
            
            # Upload to Google Drive
            uploaded_file.seek(0)
            file_content = uploaded_file.read()
            mime_type = uploaded_file.content_type or 'application/octet-stream'
            
            # Get user information
            user = User.query.get(user_id)
            user_email = user_email or (user.email if user else None)
            
            drive_result = google_drive_service.upload_file_to_admin_drive(
                file_content=file_content,
                filename=display_filename,
                mime_type=mime_type,
                user_id=user_id,
                user_email=user_email,
                convert_to_doc=convert_to_doc,
                share_with_user=share_with_user
            )
            
            if drive_result.get('success'):
                return {
                    'success': True,
                    'uploaded': True,
                    'drive_result': drive_result
                }
            else:
                logger.warning(f"Google Drive upload failed: {drive_result.get('error')}")
                return {
                    'success': True,
                    'uploaded': False,
                    'warning': f"Google Drive upload failed: {drive_result.get('error')}"
                }
                
        except Exception as e:
            logger.error(f"Google Drive upload error: {e}")
            return {
                'success': True,
                'uploaded': False,
                'warning': f"Google Drive temporarily unavailable: {str(e)}"
            }
    
    def _save_to_database(
        self, uploaded_file, user_id: int, validation_result: Dict,
        duplicate_result: Dict, storage_result: Dict, processing_result: Dict,
        google_drive_result: Dict
    ) -> Dict[str, Any]:
        """Save file record to database with proper transaction handling."""
        
        # Start a new, isolated transaction
        try:
            # Generate unique stored filename
            timestamp = int(time.time() * 1000000)  # Microsecond precision
            file_extension = os.path.splitext(uploaded_file.filename)[1].lower()
            sanitized_name = validation_result['validation'].sanitized_filename
            unique_stored_filename = f"user_{user_id}_{timestamp}_{sanitized_name}{file_extension if not sanitized_name.endswith(file_extension) else ''}"
            
            # Extract Google Drive information
            google_drive_file_id = None
            google_doc_id = None
            google_drive_link = None
            google_doc_link = None
            is_shared_with_user = False
            
            if google_drive_result.get('uploaded') and google_drive_result.get('drive_result'):
                drive_data = google_drive_result['drive_result']
                google_drive_file_id = drive_data.get('file_id')
                google_doc_id = drive_data.get('doc_id')
                google_drive_link = drive_data.get('drive_link')
                google_doc_link = drive_data.get('doc_link')
                is_shared_with_user = drive_data.get('sharing_successful', False)
            
            # Create ResumeFile record
            resume_file = ResumeFile(
                user_id=user_id,
                original_filename=uploaded_file.filename,
                display_filename=duplicate_result['display_filename'],
                stored_filename=unique_stored_filename,
                file_path=storage_result['storage_result'].file_path if storage_result['storage_result'].storage_type == 'local' else storage_result['storage_result'].s3_key,
                file_size=storage_result['storage_result'].file_size,
                mime_type=uploaded_file.content_type or 'application/octet-stream',
                storage_type=storage_result['storage_result'].storage_type,
                s3_bucket=getattr(storage_result['storage_result'], 's3_bucket', None),
                file_hash=duplicate_result['file_hash'],
                
                # Processing fields
                extracted_text=processing_result.get('extracted_text'),
                is_processed=processing_result.get('processed', False),
                processing_status='completed' if processing_result.get('processed') else ('failed' if processing_result.get('processing_error') else 'pending'),
                processing_error=processing_result.get('processing_error'),
                page_count=processing_result.get('page_count'),
                paragraph_count=processing_result.get('paragraph_count'),
                language=processing_result.get('language'),
                keywords=processing_result.get('keywords', []),
                processing_time=processing_result.get('metadata', {}).get('processing_time'),
                processing_metadata=processing_result.get('metadata', {}),
                
                # Duplicate fields
                is_duplicate=duplicate_result['is_duplicate'],
                duplicate_sequence=duplicate_result.get('duplicate_sequence', 0),
                original_file_id=duplicate_result.get('original_file_id'),
                
                # Google Drive fields
                google_drive_file_id=google_drive_file_id,
                google_doc_id=google_doc_id,
                google_drive_link=google_drive_link,
                google_doc_link=google_doc_link,
                is_shared_with_user=is_shared_with_user,
                
                # Thumbnail fields (defaults)
                has_thumbnail=False,
                thumbnail_path=None,
                thumbnail_status='pending',
                thumbnail_generated_at=None,
                thumbnail_error=None,
                
                # Metadata fields
                is_active=True,
                deleted_at=None,
                deleted_by=None,
                tags=[],
                category='active',
                category_updated_at=None,
                category_updated_by=None,
                
                # Timestamps
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Use enhanced transaction management
            from app.utils.transaction_manager import safe_database_transaction, reset_database_connection
            
            # Reset connection state first
            reset_database_connection()
            
            try:
                # Use explicit transaction with proper error handling
                with db.session.begin():
                    db.session.add(resume_file)
                    db.session.flush()  # Get the ID without committing
                    
                    # Transaction will auto-commit at end of with block
                
                logger.info(f"✅ File record saved to database: ID {resume_file.id}")
                
                # Handle thumbnail generation (separate operation, after commit)
                try:
                    self._generate_thumbnail_async(resume_file, storage_result['storage_result'])
                except Exception as thumb_error:
                    logger.warning(f"Thumbnail generation failed: {thumb_error}")
                
                return {
                    'success': True,
                    'file_record': resume_file
                }
                
            except IntegrityError as db_error:
                logger.error(f"Database integrity error: {db_error}")
                
                # Handle specific constraint violations
                if "unique constraint" in str(db_error).lower():
                    return {
                        'success': False,
                        'message': 'File with this name already exists',
                        'error': 'DUPLICATE_FILENAME',
                        'error_type': 'integrity_error'
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Database constraint violation',
                        'error': str(db_error),
                        'error_type': 'integrity_error'
                    }
                    
            except SQLAlchemyError as db_error:
                logger.error(f"Database error saving file record: {db_error}")
                return {
                    'success': False,
                    'message': 'Database error occurred while saving file record',
                    'error': str(db_error),
                    'error_type': 'database_error'
                }
                
        except Exception as e:
            # Ensure rollback on any error
            try:
                db.session.rollback()
            except:
                pass
            
            logger.error(f"Unexpected error saving to database: {e}")
            return {
                'success': False,
                'message': 'Database error occurred while saving file record',
                'error': str(e)
            }
    
    def _generate_thumbnail_async(self, resume_file: ResumeFile, storage_result):
        """Generate thumbnail asynchronously without affecting main transaction."""
        if resume_file.mime_type != 'application/pdf':
            return
        
        try:
            from app.services.thumbnail_service import ThumbnailService
            
            # Ensure thumbnail directory exists
            ThumbnailService.ensure_thumbnail_directory()
            
            # Generate thumbnail
            thumbnail_path = ThumbnailService.get_thumbnail_path(resume_file.id)
            thumbnail_success = ThumbnailService.generate_thumbnail(
                storage_result.file_path,
                thumbnail_path
            )
            
            if thumbnail_success:
                resume_file.set_thumbnail_completed(thumbnail_path)
            else:
                resume_file.set_thumbnail_failed("Thumbnail generation failed")
                
        except Exception as e:
            logger.warning(f"Thumbnail generation failed for file {resume_file.id}: {e}")
            resume_file.set_thumbnail_failed(f"Thumbnail generation error: {str(e)}")
    
    def _cleanup_storage(self, storage_result: Dict):
        """Clean up storage if database save failed."""
        try:
            if storage_result.get('success') and storage_result.get('storage_result'):
                result = storage_result['storage_result']
                if hasattr(result, 'file_path') and result.file_path:
                    if os.path.exists(result.file_path):
                        os.remove(result.file_path)
                        logger.info(f"Cleaned up storage file: {result.file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up storage: {e}")
    
    def _generate_response(
        self, file_record: ResumeFile, duplicate_result: Dict, storage_result: Dict,
        processing_result: Dict, google_drive_result: Dict
    ) -> Dict[str, Any]:
        """Generate comprehensive response."""
        
        response = {
            'success': True,
            'message': 'File uploaded successfully',
            'file': {
                'file_id': file_record.id,
                'user_id': file_record.user_id,
                'original_filename': file_record.original_filename,
                'display_filename': file_record.display_filename,
                'stored_filename': file_record.stored_filename,
                'file_size': file_record.file_size,
                'mime_type': file_record.mime_type,
                'storage_type': file_record.storage_type,
                'download_url': storage_result['storage_result'].url,
                'upload_date': file_record.created_at.isoformat(),
                'extracted_text': file_record.extracted_text,
                'processing_status': file_record.processing_status,
                'is_processed': file_record.is_processed,
                'file_hash': file_record.file_hash,
                'storage_path': file_record.file_path,
                'duplicate_info': {
                    'is_duplicate': file_record.is_duplicate,
                    'duplicate_sequence': file_record.duplicate_sequence,
                    'original_file_id': file_record.original_file_id
                }
            }
        }
        
        # Add duplicate notification
        if duplicate_result['is_duplicate'] and duplicate_result.get('notification_message'):
            response['duplicate_notification'] = duplicate_result['notification_message']
        
        # Add Google Drive information
        if google_drive_result.get('uploaded') and google_drive_result.get('drive_result'):
            drive_data = google_drive_result['drive_result']
            response['file']['google_drive'] = {
                'file_id': drive_data.get('file_id'),
                'doc_id': drive_data.get('doc_id'),
                'drive_link': drive_data.get('drive_link'),
                'doc_link': drive_data.get('doc_link'),
                'is_shared': drive_data.get('sharing_successful', False),
                'shared_with': drive_data.get('shared_with'),
                'permissions': drive_data.get('permissions', 'writer'),
                'folder_id': drive_data.get('folder_id')
            }
        
        # Add warnings
        warnings = []
        if processing_result.get('processing_error'):
            warnings.append(f"Text extraction warning: {processing_result['processing_error']}")
        if google_drive_result.get('warning'):
            warnings.append(google_drive_result['warning'])
        
        if warnings:
            response['warnings'] = warnings
        
        return response