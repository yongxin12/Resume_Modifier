"""
Improved File Upload Endpoint with Transaction Safety
Replaces the problematic upload endpoint with proper error handling
"""

from flask import request, jsonify, current_app
from flasgger import swag_from
from app.utils.jwt_utils import token_required
from core.app.services.transaction_safe_file_upload import TransactionSafeFileUploadService
import logging

logger = logging.getLogger(__name__)

@swag_from({
    'tags': ['File Management'],
    'summary': 'Upload a resume file with Google Drive integration',
    'description': 'Upload PDF or DOCX file with duplicate detection, text processing, and admin Google Drive storage',
    'consumes': ['multipart/form-data'],
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'required': True,
            'type': 'string',
            'description': 'Bearer token for authentication'
        },
        {
            'name': 'file',
            'in': 'formData',
            'required': True,
            'type': 'file',
            'description': 'Resume file to upload (PDF or DOCX)'
        },
        {
            'name': 'process',
            'in': 'query',
            'required': False,
            'type': 'boolean',
            'default': True,
            'description': 'Whether to process file content (extract text)'
        },
        {
            'name': 'google_drive',
            'in': 'query',
            'required': False,
            'type': 'boolean',
            'default': True,
            'description': 'Whether to upload to admin Google Drive'
        },
        {
            'name': 'convert_to_doc',
            'in': 'query',
            'required': False,
            'type': 'boolean',
            'default': True,
            'description': 'Whether to convert to Google Doc (requires google_drive=true)'
        },
        {
            'name': 'share_with_user',
            'in': 'query',
            'required': False,
            'type': 'boolean',
            'default': True,
            'description': 'Whether to share Google Drive files with user (requires google_drive=true)'
        }
    ],
    'responses': {
        201: {
            'description': 'File uploaded successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': True},
                    'message': {'type': 'string', 'example': 'File uploaded successfully'},
                    'file': {
                        'type': 'object',
                        'properties': {
                            'file_id': {'type': 'integer', 'example': 123},
                            'original_filename': {'type': 'string', 'example': 'resume.pdf'},
                            'display_filename': {'type': 'string', 'example': 'Resume (1).pdf'},
                            'file_size': {'type': 'integer', 'example': 245760},
                            'mime_type': {'type': 'string', 'example': 'application/pdf'},
                            'upload_date': {'type': 'string', 'format': 'date-time'},
                            'processing_status': {'type': 'string', 'example': 'completed'},
                            'google_drive': {
                                'type': 'object',
                                'properties': {
                                    'file_id': {'type': 'string'},
                                    'doc_id': {'type': 'string'},
                                    'drive_link': {'type': 'string'},
                                    'doc_link': {'type': 'string'},
                                    'is_shared': {'type': 'boolean'}
                                }
                            }
                        }
                    },
                    'duplicate_notification': {'type': 'string'},
                    'warnings': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        },
        400: {
            'description': 'Invalid request or validation failed',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': False},
                    'message': {'type': 'string', 'example': 'File validation failed'},
                    'errors': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        },
        401: {
            'description': 'Authentication required',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'example': 'Authentication required'}
                }
            }
        },
        500: {
            'description': 'Upload failed',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': False},
                    'message': {'type': 'string', 'example': 'File upload failed'},
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
@token_required
def upload_file_improved():
    """
    Improved file upload endpoint with transaction safety and proper error handling.
    This endpoint replaces the problematic original upload_file function.
    """
    try:
        # Get current user from token
        current_user_id = request.user['user_id']
        current_user_email = request.user.get('email', '')
        
        # Validate file upload
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400
        
        uploaded_file = request.files['file']
        
        if uploaded_file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No filename provided'
            }), 400
        
        # Parse query parameters
        process_content = request.args.get('process', 'true').lower() == 'true'
        upload_to_google_drive = request.args.get('google_drive', 'true').lower() == 'true'
        convert_to_doc = request.args.get('convert_to_doc', 'true').lower() == 'true'
        share_with_user = request.args.get('share_with_user', 'true').lower() == 'true'
        
        # Initialize transaction-safe upload service
        upload_service = TransactionSafeFileUploadService()
        
        # Process upload with transaction safety
        result = upload_service.upload_file(
            uploaded_file=uploaded_file,
            user_id=current_user_id,
            user_email=current_user_email,
            process_content=process_content,
            upload_to_google_drive=upload_to_google_drive,
            convert_to_doc=convert_to_doc,
            share_with_user=share_with_user
        )
        
        # Return result with appropriate status code
        if result['success']:
            logger.info(f"✅ File uploaded successfully for user {current_user_id}: {uploaded_file.filename}")
            return jsonify(result), 201
        else:
            logger.warning(f"⚠️ File upload failed for user {current_user_id}: {result.get('message')}")
            
            # Determine appropriate error status code
            if 'validation' in result.get('message', '').lower():
                status_code = 400
            elif 'authentication' in result.get('message', '').lower():
                status_code = 401
            elif 'duplicate' in result.get('error', '').lower():
                status_code = 409  # Conflict
            else:
                status_code = 500
            
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in file upload: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'File upload failed due to unexpected error',
            'error': str(e)
        }), 500