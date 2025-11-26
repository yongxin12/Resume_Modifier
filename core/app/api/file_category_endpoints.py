"""
File Categorization API Endpoints
Handles HTTP requests for file category management
"""

from flask import Blueprint, request, jsonify, current_app
from flasgger import swag_from
from typing import Dict, Any
from app.services.file_category_service import FileCategoryService
from app.utils.error_handler import FileManagementError, handle_file_management_errors
from app.utils.jwt_utils import token_required


# Create blueprint for file categorization endpoints
file_category_bp = Blueprint('file_category', __name__)


@file_category_bp.route('/<int:file_id>/category', methods=['PUT'])
@swag_from({
    'tags': ['File Categorization'],
    'summary': 'Update file category',
    'description': 'Update the category of a single file. Valid categories are: active, archived, draft.',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Bearer token for authentication'
        },
        {
            'name': 'file_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID of the file to update'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['category'],
                'properties': {
                    'category': {
                        'type': 'string',
                        'enum': ['active', 'archived', 'draft'],
                        'description': 'New category for the file'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'File category updated successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': True},
                    'message': {'type': 'string', 'example': 'File category updated successfully'},
                    'file': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'category': {'type': 'string'},
                            'category_updated_at': {'type': 'string', 'format': 'date-time'}
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Invalid request - missing or invalid category',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': False},
                    'error': {'type': 'string'},
                    'valid_categories': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        },
        401: {'description': 'Authentication required'},
        403: {'description': 'Access denied to this file'},
        404: {'description': 'File not found'}
    }
})
@token_required
@handle_file_management_errors
def update_file_category(file_id: int) -> Dict[str, Any]:
    """
    Update category for a single file.
    
    Args:
        file_id: ID of the file to update
        
    Returns:
        JSON response with updated file information
    """
    user_id = request.user.get('user_id')
    
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
@swag_from({
    'tags': ['File Categorization'],
    'summary': 'Bulk update file categories',
    'description': 'Update the category for multiple files at once. Valid categories are: active, archived, draft.',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Bearer token for authentication'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['file_ids', 'category'],
                'properties': {
                    'file_ids': {
                        'type': 'array',
                        'items': {'type': 'integer'},
                        'description': 'Array of file IDs to update',
                        'example': [1, 2, 3]
                    },
                    'category': {
                        'type': 'string',
                        'enum': ['active', 'archived', 'draft'],
                        'description': 'New category for the files'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Bulk category update completed',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'updated_count': {'type': 'integer'},
                    'failed_count': {'type': 'integer'},
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'file_id': {'type': 'integer'},
                                'success': {'type': 'boolean'},
                                'error': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        },
        400: {'description': 'Invalid request - missing or invalid parameters'},
        401: {'description': 'Authentication required'}
    }
})
@token_required
@handle_file_management_errors
def bulk_update_categories() -> Dict[str, Any]:
    """
    Update category for multiple files.
    
    Returns:
        JSON response with update summary
    """
    user_id = request.user.get('user_id')
    
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


@file_category_bp.route('/list', methods=['GET'])
@swag_from({
    'tags': ['File Categorization'],
    'summary': 'List files by category',
    'description': 'List files with optional category filtering and pagination. This is an enhanced version of the standard file listing endpoint with category support.',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Bearer token for authentication'
        },
        {
            'name': 'category',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['active', 'archived', 'draft', 'all'],
            'description': "Filter by category. Use 'all' or omit to show all categories."
        },
        {
            'name': 'page',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 1,
            'description': 'Page number for pagination (1-based)'
        },
        {
            'name': 'per_page',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 20,
            'description': 'Items per page (max 100)'
        },
        {
            'name': 'sort_by',
            'in': 'query',
            'type': 'string',
            'required': False,
            'default': 'created_at',
            'enum': ['created_at', 'updated_at', 'original_filename', 'file_size', 'category'],
            'description': 'Field to sort by'
        },
        {
            'name': 'sort_order',
            'in': 'query',
            'type': 'string',
            'required': False,
            'default': 'desc',
            'enum': ['asc', 'desc'],
            'description': 'Sort order'
        },
        {
            'name': 'search',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Search term for filename filtering'
        }
    ],
    'responses': {
        200: {
            'description': 'Files retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'files': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'original_filename': {'type': 'string'},
                                'display_filename': {'type': 'string'},
                                'category': {'type': 'string'},
                                'file_size': {'type': 'integer'},
                                'mime_type': {'type': 'string'},
                                'created_at': {'type': 'string', 'format': 'date-time'},
                                'updated_at': {'type': 'string', 'format': 'date-time'}
                            }
                        }
                    },
                    'pagination': {
                        'type': 'object',
                        'properties': {
                            'page': {'type': 'integer'},
                            'per_page': {'type': 'integer'},
                            'total': {'type': 'integer'},
                            'pages': {'type': 'integer'},
                            'has_next': {'type': 'boolean'},
                            'has_prev': {'type': 'boolean'}
                        }
                    }
                }
            }
        },
        401: {'description': 'Authentication required'}
    }
})
@token_required
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
    user_id = request.user.get('user_id')
    
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
@swag_from({
    'tags': ['File Categorization'],
    'summary': 'Get file category statistics',
    'description': 'Get counts and statistics for each file category for the current user.',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Bearer token for authentication'
        }
    ],
    'responses': {
        200: {
            'description': 'Category statistics retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': True},
                    'statistics': {
                        'type': 'object',
                        'properties': {
                            'total_files': {'type': 'integer', 'example': 25},
                            'by_category': {
                                'type': 'object',
                                'properties': {
                                    'active': {
                                        'type': 'object',
                                        'properties': {
                                            'count': {'type': 'integer', 'example': 15},
                                            'percentage': {'type': 'number', 'example': 60.0}
                                        }
                                    },
                                    'archived': {
                                        'type': 'object',
                                        'properties': {
                                            'count': {'type': 'integer', 'example': 7},
                                            'percentage': {'type': 'number', 'example': 28.0}
                                        }
                                    },
                                    'draft': {
                                        'type': 'object',
                                        'properties': {
                                            'count': {'type': 'integer', 'example': 3},
                                            'percentage': {'type': 'number', 'example': 12.0}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        401: {'description': 'Authentication required'}
    }
})
@token_required
@handle_file_management_errors
def get_category_statistics() -> Dict[str, Any]:
    """
    Get file category statistics for the current user.
    
    Returns:
        JSON response with category counts and percentages
    """
    user_id = request.user.get('user_id')
    
    result = FileCategoryService.get_category_statistics(user_id)
    
    return jsonify(result), 200


@file_category_bp.route('/categories', methods=['GET'])
@swag_from({
    'tags': ['File Categorization'],
    'summary': 'Get available categories',
    'description': 'Get list of all available file categories with their descriptions.',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Bearer token for authentication'
        }
    ],
    'responses': {
        200: {
            'description': 'Available categories retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': True},
                    'categories': {
                        'type': 'object',
                        'properties': {
                            'active': {
                                'type': 'object',
                                'properties': {
                                    'name': {'type': 'string', 'example': 'active'},
                                    'display_name': {'type': 'string', 'example': 'Active'},
                                    'description': {'type': 'string'},
                                    'is_default': {'type': 'boolean', 'example': True}
                                }
                            },
                            'archived': {
                                'type': 'object',
                                'properties': {
                                    'name': {'type': 'string', 'example': 'archived'},
                                    'display_name': {'type': 'string', 'example': 'Archived'},
                                    'description': {'type': 'string'},
                                    'is_default': {'type': 'boolean', 'example': False}
                                }
                            },
                            'draft': {
                                'type': 'object',
                                'properties': {
                                    'name': {'type': 'string', 'example': 'draft'},
                                    'display_name': {'type': 'string', 'example': 'Draft'},
                                    'description': {'type': 'string'},
                                    'is_default': {'type': 'boolean', 'example': False}
                                }
                            }
                        }
                    },
                    'valid_categories': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'example': ['active', 'archived', 'draft']
                    },
                    'default_category': {'type': 'string', 'example': 'active'}
                }
            }
        },
        401: {'description': 'Authentication required'}
    }
})
@token_required
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