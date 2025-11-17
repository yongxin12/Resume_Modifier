"""
File Category Service
Handles all file categorization business logic and validation
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from flask import current_app
from app.models.temp import ResumeFile, db
from app.utils.error_handler import FileManagementError, ErrorCode


class FileCategoryService:
    """Service for managing file categorization operations."""
    
    VALID_CATEGORIES = ['active', 'archived', 'draft']
    DEFAULT_CATEGORY = 'active'
    
    @classmethod
    def validate_category(cls, category: str) -> bool:
        """
        Validate if category is one of the allowed values.
        
        Args:
            category: Category string to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return category in cls.VALID_CATEGORIES
    
    @classmethod
    def update_file_category(cls, file_id: int, user_id: int, new_category: str) -> Dict[str, Any]:
        """
        Update category for a single file.
        
        Args:
            file_id: ID of the file to update
            user_id: ID of the user making the request
            new_category: New category to assign
            
        Returns:
            dict: Updated file information or error details
            
        Raises:
            FileManagementError: If validation fails or file not found
        """
        # Validate category
        if not cls.validate_category(new_category):
            raise FileManagementError(
                error_code=ErrorCode.INVALID_INPUT,
                message=f"Invalid category '{new_category}'. Must be one of: {', '.join(cls.VALID_CATEGORIES)}",
                details={'valid_categories': cls.VALID_CATEGORIES}
            )
        
        # Get the file
        file_obj = ResumeFile.query.filter_by(
            id=file_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not file_obj:
            raise FileManagementError(
                error_code=ErrorCode.FILE_NOT_FOUND,
                message=f"File with ID {file_id} not found or access denied",
                details={'file_id': file_id}
            )
        
        # Update category
        success = file_obj.update_category(new_category, user_id)
        if not success:
            raise FileManagementError(
                error_code=ErrorCode.INVALID_INPUT,
                message="Failed to update file category",
                details={'file_id': file_id, 'category': new_category}
            )
        
        try:
            db.session.commit()
            current_app.logger.info(f"Updated file {file_id} category to '{new_category}' for user {user_id}")
            
            return {
                'success': True,
                'message': 'File category updated successfully',
                'file': file_obj.to_dict(include_google_drive=False, include_duplicates=False)
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error updating file category: {str(e)}")
            raise FileManagementError(
                error_code=ErrorCode.DATABASE_ERROR,
                message="Failed to save category update",
                details={'error': str(e)}
            )
    
    @classmethod
    def bulk_update_categories(cls, file_ids: List[int], user_id: int, new_category: str) -> Dict[str, Any]:
        """
        Update category for multiple files.
        
        Args:
            file_ids: List of file IDs to update
            user_id: ID of the user making the request
            new_category: New category to assign
            
        Returns:
            dict: Summary of successful and failed updates
            
        Raises:
            FileManagementError: If validation fails
        """
        # Validate inputs
        if not file_ids:
            raise FileManagementError(
                error_code=ErrorCode.INVALID_INPUT,
                message="No file IDs provided",
                details={'file_ids': file_ids}
            )
        
        if not cls.validate_category(new_category):
            raise FileManagementError(
                error_code=ErrorCode.INVALID_INPUT,
                message=f"Invalid category '{new_category}'. Must be one of: {', '.join(cls.VALID_CATEGORIES)}",
                details={'valid_categories': cls.VALID_CATEGORIES}
            )
        
        try:
            # Use the model's bulk update method
            result = ResumeFile.bulk_update_category(user_id, file_ids, new_category, user_id)
            
            if result.get('error'):
                raise FileManagementError(
                    error_code=ErrorCode.INVALID_INPUT,
                    message=result['error'],
                    details={'file_ids': file_ids}
                )
            
            # Commit the transaction
            db.session.commit()
            
            current_app.logger.info(
                f"Bulk category update: {result['successful_updates']} successful, "
                f"{result['failed_updates']} failed for user {user_id}"
            )
            
            return {
                'success': True,
                'message': 'Bulk category update completed',
                'summary': {
                    'total_requested': len(file_ids),
                    'successful_updates': result['successful_updates'],
                    'failed_updates': result['failed_updates'],
                    'category': new_category
                },
                'updated_files': result['updated_files'],
                'failed_files': result['failed_files']
            }
            
        except FileManagementError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in bulk category update: {str(e)}")
            raise FileManagementError(
                error_code=ErrorCode.DATABASE_ERROR,
                message="Failed to perform bulk category update",
                details={'error': str(e)}
            )
    
    @classmethod
    def get_files_by_category(cls, user_id: int, category: Optional[str] = None, 
                            page: int = 1, per_page: int = 20, 
                            sort_by: str = 'created_at', sort_order: str = 'desc',
                            search: Optional[str] = None) -> Dict[str, Any]:
        """
        Get files filtered by category with pagination and search.
        
        Args:
            user_id: ID of the user
            category: Category to filter by ('active', 'archived', 'draft', 'all', or None)
            page: Page number for pagination
            per_page: Items per page
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            search: Search term for filename filtering
            
        Returns:
            dict: Paginated list of files with metadata
        """
        # Validate category if provided
        if category and category != 'all' and not cls.validate_category(category):
            raise FileManagementError(
                error_code=ErrorCode.INVALID_INPUT,
                message=f"Invalid category '{category}'. Must be one of: {', '.join(cls.VALID_CATEGORIES + ['all'])}",
                details={'valid_categories': cls.VALID_CATEGORIES + ['all']}
            )
        
        # Build base query
        query = ResumeFile.get_files_by_category(user_id, category)
        
        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(ResumeFile.original_filename.ilike(search_term))
        
        # Apply sorting
        valid_sort_fields = ['created_at', 'updated_at', 'original_filename', 'file_size', 'category']
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'
        
        sort_column = getattr(ResumeFile, sort_by)
        if sort_order.lower() == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Apply pagination
        try:
            paginated_files = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            files_data = [
                file.to_dict(include_google_drive=False, include_duplicates=False)
                for file in paginated_files.items
            ]
            
            return {
                'success': True,
                'data': {
                    'files': files_data,
                    'pagination': {
                        'page': paginated_files.page,
                        'per_page': paginated_files.per_page,
                        'total': paginated_files.total,
                        'total_pages': paginated_files.pages,
                        'has_next': paginated_files.has_next,
                        'has_prev': paginated_files.has_prev
                    },
                    'filter': {
                        'category': category,
                        'search': search,
                        'sort_by': sort_by,
                        'sort_order': sort_order
                    }
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Error querying files by category: {str(e)}")
            raise FileManagementError(
                error_code=ErrorCode.DATABASE_ERROR,
                message="Failed to retrieve files",
                details={'error': str(e)}
            )
    
    @classmethod
    def get_category_statistics(cls, user_id: int) -> Dict[str, Any]:
        """
        Get file category statistics for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            dict: Statistics including counts and percentages by category
        """
        try:
            stats = ResumeFile.get_category_statistics(user_id)
            
            return {
                'success': True,
                'statistics': stats
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting category statistics: {str(e)}")
            raise FileManagementError(
                error_code=ErrorCode.DATABASE_ERROR,
                message="Failed to retrieve category statistics",
                details={'error': str(e)}
            )
    
    @classmethod
    def set_default_category_for_upload(cls, file_obj: ResumeFile, user_id: int) -> None:
        """
        Set default category for newly uploaded file.
        
        Args:
            file_obj: ResumeFile instance
            user_id: ID of the uploading user
        """
        if not file_obj.category:
            file_obj.category = cls.DEFAULT_CATEGORY
            file_obj.category_updated_at = datetime.utcnow()
            file_obj.category_updated_by = user_id
    
    @classmethod
    def validate_category_access(cls, file_id: int, user_id: int) -> bool:
        """
        Validate that user has access to modify file category.
        
        Args:
            file_id: ID of the file
            user_id: ID of the user
            
        Returns:
            bool: True if user has access, False otherwise
        """
        file_obj = ResumeFile.query.filter_by(
            id=file_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        return file_obj is not None