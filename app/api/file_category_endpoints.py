"""
File Categorization API Endpoints
Handles HTTP requests for file category management
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import Dict, Any
from app.services.file_category_service import FileCategoryService
from app.utils.error_handler import FileManagementError, handle_file_management_errors


# Create blueprint for file categorization endpoints
file_category_bp = Blueprint('file_category', __name__, url_prefix='/files')


@file_category_bp.route('/<int:file_id>/category', methods=['PUT'])
@jwt_required()
@handle_file_management_errors
def update_file_category(file_id: int) -> Dict[str, Any]:
    """
    Update category for a single file.
    
    Args:
        file_id: ID of the file to update
        
    Returns:
        JSON response with updated file information
    """
    user_id = get_jwt_identity()
    
    # Validate request body
    if not request.is_json:
        return jsonify({
            'success': False,
            'error': 'Request must be JSON',
            'message': 'Content-Type must be application/json'
        }), 400
    
    data = request.get_json()
    new_category = data.get('category')
    
    if not new_category:
        return jsonify({
            'success': False,
            'error': 'Missing category',
            'message': 'Category field is required',
            'valid_categories': FileCategoryService.VALID_CATEGORIES
        }), 400
    
    # Update file category
    result = FileCategoryService.update_file_category(file_id, user_id, new_category)
    
    return jsonify(result), 200


@file_category_bp.route('/category', methods=['PUT'])
@jwt_required()
@handle_file_management_errors
def bulk_update_categories() -> Dict[str, Any]:
    """
    Update category for multiple files.
    
    Returns:
        JSON response with update summary
    """
    user_id = get_jwt_identity()
    
    # Validate request body
    if not request.is_json:
        return jsonify({
            'success': False,
            'error': 'Request must be JSON',
            'message': 'Content-Type must be application/json'
        }), 400
    
    data = request.get_json()
    file_ids = data.get('file_ids', [])
    new_category = data.get('category')
    
    # Validation
    if not file_ids or not isinstance(file_ids, list):
        return jsonify({
            'success': False,
            'error': 'Invalid file_ids',
            'message': 'file_ids must be a non-empty array of integers'
        }), 400
    
    if not new_category:
        return jsonify({
            'success': False,
            'error': 'Missing category',
            'message': 'Category field is required',
            'valid_categories': FileCategoryService.VALID_CATEGORIES
        }), 400
    
    # Validate file_ids are integers
    try:
        file_ids = [int(fid) for fid in file_ids]
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'error': 'Invalid file_ids format',
            'message': 'All file_ids must be valid integers'
        }), 400
    
    # Perform bulk update
    result = FileCategoryService.bulk_update_categories(file_ids, user_id, new_category)
    
    return jsonify(result), 200


@file_category_bp.route('', methods=['GET'])
@jwt_required()
@handle_file_management_errors
def list_files_by_category() -> Dict[str, Any]:
    """
    List files with optional category filtering.
    Enhanced version of the standard file listing endpoint.
    
    Query Parameters:
        - category: Filter by category ('active', 'archived', 'draft', 'all')
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
        - sort_by: Sort field (default: 'created_at')
        - sort_order: Sort order ('asc' or 'desc', default: 'desc')
        - search: Search term for filename filtering
        
    Returns:
        JSON response with paginated file list
    """
    user_id = get_jwt_identity()
    
    # Extract query parameters
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    search = request.args.get('search')
    
    # Validate page parameters
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20
    
    # Get files with filtering
    result = FileCategoryService.get_files_by_category(
        user_id=user_id,
        category=category,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search
    )
    
    return jsonify(result), 200


@file_category_bp.route('/categories/stats', methods=['GET'])
@jwt_required()
@handle_file_management_errors
def get_category_statistics() -> Dict[str, Any]:
    """
    Get file category statistics for the current user.
    
    Returns:
        JSON response with category counts and percentages
    """
    user_id = get_jwt_identity()
    
    result = FileCategoryService.get_category_statistics(user_id)
    
    return jsonify(result), 200


@file_category_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_available_categories() -> Dict[str, Any]:
    """
    Get list of available file categories.
    
    Returns:
        JSON response with available categories and descriptions
    """
    categories = {
        'active': {
            'name': 'active',
            'display_name': 'Active',
            'description': 'Frequently used files, ready for immediate use',
            'is_default': True
        },
        'archived': {
            'name': 'archived',
            'display_name': 'Archived',
            'description': 'Infrequently used files, stored for reference',
            'is_default': False
        },
        'draft': {
            'name': 'draft',
            'display_name': 'Draft',
            'description': 'Work-in-progress files, not yet finalized',
            'is_default': False
        }
    }
    
    return jsonify({
        'success': True,
        'categories': categories,
        'valid_categories': FileCategoryService.VALID_CATEGORIES,
        'default_category': FileCategoryService.DEFAULT_CATEGORY
    }), 200


# Error handlers for the blueprint
@file_category_bp.errorhandler(FileManagementError)
def handle_file_management_error(error: FileManagementError):
    """Handle FileManagementError exceptions."""
    response = {
        'success': False,
        'error': error.error_code.value,
        'message': error.message
    }
    
    if error.details:
        response['details'] = error.details
    
    # Map error codes to HTTP status codes
    status_code_map = {
        'FILE_NOT_FOUND': 404,
        'PERMISSION_DENIED': 403,
        'INVALID_INPUT': 400,
        'TIMEOUT': 408,
        'DATABASE_ERROR': 500,
        'UNKNOWN': 500
    }
    
    status_code = status_code_map.get(error.error_code.value, 500)
    
    current_app.logger.error(f"File management error: {error.message} - Details: {error.details}")
    
    return jsonify(response), status_code


@file_category_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'NOT_FOUND',
        'message': 'The requested resource was not found'
    }), 404


@file_category_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'success': False,
        'error': 'METHOD_NOT_ALLOWED',
        'message': 'The requested method is not allowed for this resource'
    }), 405


@file_category_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    current_app.logger.error(f"Internal server error in file category API: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'INTERNAL_SERVER_ERROR',
        'message': 'An internal server error occurred'
    }), 500