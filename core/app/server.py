from flask import Blueprint, request, jsonify, redirect, session, current_app, send_file
from flasgger import swag_from
import os
from app.extensions import db
from app.utils.pdf_validator import PDFValidator
from app.utils.job_validator import JobValidator
from app.utils.parse_pdf import parse_pdf_file
from app.services.resume_ai import ResumeAI
from app.services.resume_generator import ResumeGenerator
from app.services.template_service import TemplateService
from app.services.google_auth import GoogleAuthService
from app.services.google_docs_service import GoogleDocsService
from app.services.google_drive_service import GoogleDriveService
from app.services.duplicate_file_handler import DuplicateFileHandler
from app.services.pdf_generator import PDFGenerator
from app.utils.error_handler import ErrorHandler, ErrorCode
from app.response_template.resume_schema import RESUME_TEMPLATE
from app.models.temp import User, Resume, JobDescription, GoogleAuth, ResumeTemplate, GeneratedDocument, ResumeFile
from app.utils.feedback_validator import FeedbackValidator
from app.utils.jwt_utils import generate_token, token_required
from app.utils.profile_validator import ProfileValidator
from app.utils.file_validator import FileValidator
from app.services.file_storage_service import FileStorageService
from app.services.file_processing_service import FileProcessingService
from app.services.thumbnail_service import ThumbnailService

# Enhanced OAuth and Session Management
from app.services.google_admin_auth_fixed import GoogleAdminAuthServiceFixed, create_oauth_temp_states_table, cleanup_expired_oauth_states
from app.services.flask_session_config import configure_flask_sessions_for_docker, setup_oauth_session_support, validate_session_configuration
import secrets
from datetime import datetime, timedelta

from googleapiclient.errors import HttpError
from datetime import datetime
import logging
import io
import os
from io import BytesIO

# Create blueprint
api = Blueprint('api', __name__)

@api.route('/')
@swag_from({
    'tags': ['System'],
    'summary': 'API root endpoint',
    'description': 'Simple endpoint to verify the API is running',
    'responses': {
        200: {
            'description': 'API is running',
            'schema': {
                'type': 'string',
                'example': 'Flask App is Running!'
            }
        }
    }
})
def index():
    return "Flask App is Running!"

@api.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify service status
    ---
    tags:
      - System
    responses:
      200:
        description: Service is healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: healthy
            service:
              type: string
              example: Resume Editor API
            timestamp:
              type: string
              format: date-time
            components:
              type: object
              properties:
                database:
                  type: string
                  example: connected
                openai:
                  type: string
                  example: configured
      503:
        description: Service is unhealthy
    """
    health_status = {
        "status": "healthy",
        "service": "Resume Editor API",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    try:
        # Check database connectivity
        db.session.execute(db.text('SELECT 1'))
        health_status["components"]["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = f"disconnected: {str(e)}"
    
    # Check OpenAI API key configuration
    import os
    if os.getenv('OPENAI_API_KEY'):
        health_status["components"]["openai"] = "configured"
    else:
        health_status["components"]["openai"] = "not configured"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code

@api.route('/api/pdfupload', methods=['POST'])
def upload_pdf():
    """
    Upload PDF and process resume
    ---
    tags:
      - Resume Processing
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: PDF file containing the resume
    responses:
      200:
        description: Resume successfully parsed
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            data:
              type: object
              description: Parsed resume data structure
      400:
        description: Invalid request or file format
      500:
        description: Resume processing failed
    """
    
    # Validate request
    error, status_code = PDFValidator.validate_upload_request(request)
    if error:
        return jsonify({"error": error}), status_code
    
    # Get file
    pdf_file = request.files['file']
    
    try:
        # Parse PDF to text
        extracted_text = parse_pdf_file(pdf_file)
        
        # Process with ResumeAI - only parse
        resume_processor = ResumeAI(extracted_text)
        parsed_resume = resume_processor.parse()
        
        return jsonify({
            "status": 200,
            "data": parsed_resume
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Resume processing failed", 
            "details": str(e)
        }), 500


@api.route('/api/templates', methods=['GET'])
def get_templates():
    """
    Get all available resume templates
    ---
    tags:
      - Templates
    responses:
      200:
        description: Templates retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  name:
                    type: string
                    example: "Professional Modern"
                  description:
                    type: string
                    example: "Clean, modern design with blue accents"
                  style_config:
                    type: object
                    description: Template styling configuration
                  sections:
                    type: array
                    items:
                      type: string
                    example: ["header", "summary", "experience", "education", "skills"]
                  created_at:
                    type: string
                    format: date-time
      500:
        description: Failed to retrieve templates
    """
    try:
        templates = TemplateService.get_all_templates()
        
        return jsonify({
            "status": 200,
            "data": templates
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to retrieve templates",
            "details": str(e)
        }), 500


@api.route('/api/templates/<int:template_id>', methods=['GET'])
def get_template(template_id):
    """
    Get a specific template by ID
    ---
    tags:
      - Templates
    parameters:
      - name: template_id
        in: path
        type: integer
        required: true
        description: Template ID to retrieve
    responses:
      200:
        description: Template retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            data:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
                description:
                  type: string
                style_config:
                  type: object
                sections:
                  type: array
                  items:
                    type: string
      404:
        description: Template not found
      500:
        description: Failed to retrieve template
    """
    try:
        template = TemplateService.get_template_by_id(template_id)
        
        if not template:
            return jsonify({
                "error": "Template not found"
            }), 404
        
        return jsonify({
            "status": 200,
            "data": template
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to retrieve template",
            "details": str(e)
        }), 500


@api.route('/api/templates/seed', methods=['POST'])
def seed_templates():
    """
    Seed default templates (development/admin endpoint)
    ---
    tags:
      - Templates
    responses:
      200:
        description: Templates seeded successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            message:
              type: string
              example: "Default templates seeded successfully"
      500:
        description: Failed to seed templates
    """
    try:
        TemplateService.seed_default_templates()
        
        return jsonify({
            "status": 200,
            "message": "Default templates seeded successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to seed templates",
            "details": str(e)
        }), 500


@api.route('/api/job_description_upload', methods=['POST'])
def analyze_with_job():
    """
    Analyze resume against job description
    ---
    tags:
      - Resume Analysis
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - updated_resume
            - job_description
          properties:
            updated_resume:
              type: object
              description: Parsed resume data structure
            job_description:
              type: string
              description: Job description text to analyze against
    responses:
      200:
        description: Analysis completed successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            data:
              type: object
              description: Detailed analysis with scores and recommendations
      400:
        description: Invalid request data
      500:
        description: Analysis failed
    """
    try:
        # Validate request
        error_response, status_code, data = JobValidator.validate_request(request)
        if error_response:
            return error_response, status_code
        
        # Process with ResumeAI
        resume_processor = ResumeAI("")  # Empty string as we're using provided resume
        resume_processor.parsed_resume = data['updated_resume']
        analysis = resume_processor.analyze(data['job_description'])

        return jsonify({
            "status": 200,
            "data": analysis
        }), 200
        
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"Job description analysis failed: {str(e)}")
        return jsonify({
            "error": "Analysis failed",
            "details": str(e)
        }), 500

@api.route('/api/feedback', methods=['PUT'])
@swag_from({
    'tags': ['Resume Processing'],
    'summary': 'Process feedback and updated resume data',
    'description': 'Process user feedback on resume sections and update resume content based on feedback',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['section', 'updated_resume'],
                'properties': {
                    'section': {
                        'type': 'object',
                        'required': ['section type'],
                        'properties': {
                            'section type': {
                                'type': 'string',
                                'description': 'Type of section being updated'
                            }
                        }
                    },
                    'updated_resume': {
                        'type': 'object',
                        'description': 'Updated resume content'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Feedback processed successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'updated_resume': {'type': 'object'}
                }
            }
        },
        400: {
            'description': 'Bad request',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        401: {
            'description': 'Unauthorized',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def process_feedback():
    """Process feedback and updated resume data."""
    # Validate request
    validation_result = FeedbackValidator.validate_request(request)
    if len(validation_result) == 2:
        # Error case: (error_response, status_code)
        return validation_result
    else:
        # Success case: (None, None, data)
        _, _, data = validation_result
    
    try:
        # Extract fields from validated data
        section = data['section']
        feedback = data.get('feedback', '')
        updated_resume = data['updated_resume']
        
        # Process with ResumeAI
        resume_processor = ResumeAI("")  # Empty string as we're using provided resume
        resume_processor.parsed_resume = updated_resume
        
        # Process feedback for the specific section
        analysis = resume_processor.process_section_feedback(
            section=section['section type'],
            subsection_data=section,
            feedback=feedback
        )
        
        return jsonify({
            "status": 200,
            "data": analysis
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to process feedback",
            "details": str(e)
        }), 500

@api.route('/api/files/upload', methods=['POST'])
@token_required
def upload_file():
    """
    Upload a resume file (PDF or DOCX) with duplicate detection and Google Drive integration
    ---
    tags:
      - File Management
    consumes:
      - multipart/form-data
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: Bearer token for authentication
      - name: file
        in: formData
        required: true
        type: file
        description: Resume file to upload (PDF or DOCX)
      - name: process
        in: query
        required: false
        type: boolean
        default: true
        description: Whether to process file content (extract text)
      - name: google_drive
        in: query
        required: false
        type: boolean
        default: true
        description: Whether to upload to Google Drive
      - name: convert_to_doc
        in: query
        required: false
        type: boolean
        default: true
        description: Whether to convert to Google Doc (requires google_drive=true)
      - name: share_with_user
        in: query
        required: false
        type: boolean
        default: true
        description: Whether to share Google Drive files with user (requires google_drive=true)
    responses:
      201:
        description: File uploaded successfully with duplicate and Google Drive information
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "File uploaded successfully"
            duplicate_notification:
              type: string
              example: "Duplicate file detected. Saved as 'Resume (1).pdf' to avoid conflicts."
            file:
              type: object
              properties:
                file_id:
                  type: integer
                  example: 123
                user_id:
                  type: integer
                  example: 1
                original_filename:
                  type: string
                  example: "resume.pdf"
                display_filename:
                  type: string
                  example: "Resume (1).pdf"
                stored_filename:
                  type: string
                  example: "secure_resume_20241025.pdf"
                file_size:
                  type: integer
                  example: 245760
                mime_type:
                  type: string
                  example: "application/pdf"
                storage_type:
                  type: string
                  example: "local"
                download_url:
                  type: string
                  example: "http://localhost:5001/api/files/123/download"
                upload_date:
                  type: string
                  format: date-time
                extracted_text:
                  type: string
                  example: "Resume content..."
                processing_status:
                  type: string
                  example: "completed"
                duplicate_info:
                  type: object
                  properties:
                    is_duplicate:
                      type: boolean
                      example: true
                    duplicate_sequence:
                      type: integer
                      example: 1
                    original_file_id:
                      type: integer
                      example: 122
                google_drive:
                  type: object
                  properties:
                    file_id:
                      type: string
                      example: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                    doc_id:
                      type: string
                      example: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                    drive_link:
                      type: string 
                      example: "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view"
                    doc_link:
                      type: string
                      example: "https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
                    is_shared:
                      type: boolean
                      example: true
      400:
        description: Invalid request or validation failed
      401:
        description: Authentication required
      500:
        description: Upload failed
    """
    try:
        # Get current user from token
        current_user_id = request.user['user_id']
        current_user_email = request.user.get('email', '')
        
        # Get Google Drive options from query parameters
        upload_to_google_drive = request.args.get('google_drive', 'false').lower() == 'true'
        convert_to_doc = request.args.get('convert_to_doc', 'true').lower() == 'true'
        share_with_user = request.args.get('share_with_user', 'true').lower() == 'true'
        
        # Check if file is provided
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400
        
        uploaded_file = request.files['file']
        
        # Check if filename is provided
        if uploaded_file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No filename provided'
            }), 400
        
        # Check if processing is requested (default: true)
        should_process = request.args.get('process', 'true').lower() == 'true'
        
        # Initialize services
        file_validator = FileValidator()
        duplicate_handler = DuplicateFileHandler()
        
        # Get centralized storage configuration
        from app.utils.storage_config import StorageConfigManager
        try:
            storage_config = StorageConfigManager.get_storage_config_dict()
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': f'Storage configuration error: {str(e)}'
            }), 500
        
        file_storage_service = FileStorageService(storage_config)
        
        # Validate file
        validation_result = file_validator.validate_file(uploaded_file)
        
        if not validation_result.is_valid:
            # If multiple errors, use generic message; if single error, use specific message
            if len(validation_result.errors) > 1:
                main_message = 'File validation failed'
            else:
                main_message = validation_result.errors[0] if validation_result.errors else 'File validation failed'
            
            return jsonify({
                'success': False,
                'message': main_message,
                'errors': validation_result.errors
            }), 400
        
        # Process duplicate file detection
        duplicate_result = None
        try:
            uploaded_file.seek(0)  # Reset file pointer
            file_content = uploaded_file.read()
            # Use validator's file_hash if available, otherwise calculate it
            file_hash = getattr(validation_result, 'file_hash', None) or duplicate_handler.calculate_file_hash(file_content)
            
            duplicate_result = duplicate_handler.process_duplicate_file(
                current_user_id,
                uploaded_file.filename,
                file_hash,
                file_content
            )
        except Exception as e:
            error_handler = ErrorHandler()
            current_app.logger.warning(f"Duplicate detection failed: {str(e)}")
            # Fallback: use original filename without duplicate detection
            uploaded_file.seek(0)  # Reset file pointer for fallback hash calculation
            try:
                file_content = uploaded_file.read()
                file_hash = duplicate_handler.calculate_file_hash(file_content)
            except:
                file_hash = 'fallback_hash'
            
            duplicate_result = {
                'is_duplicate': False,
                'display_filename': uploaded_file.filename,
                'file_hash': file_hash,
                'notification_message': None,
                'duplicate_sequence': None,
                'original_file_id': None
            }
        
        # Upload file to storage using the display filename from duplicate processing
        uploaded_file.seek(0)  # Reset file pointer
        storage_result = file_storage_service.upload_file(
            file_storage=uploaded_file,
            user_id=current_user_id,
            filename=duplicate_result['display_filename']
        )
        
        if not storage_result.success:
            return jsonify({
                'success': False,
                'message': 'File storage failed',
                'error': storage_result.error_message
            }), 500
        
        # Initialize Google Drive variables
        google_drive_file_id = None
        google_doc_id = None
        google_drive_info = None
        
        # Get mime type from uploaded file
        mime_type = uploaded_file.content_type or 'application/octet-stream'
        
        # Handle Google Drive upload if requested (using Admin OAuth)
        google_drive_warnings = []
        if upload_to_google_drive:
            try:
                from app.services.google_drive_admin_service import GoogleDriveAdminService
                google_drive_service = GoogleDriveAdminService()
                
                # Check admin authentication status first
                auth_status = google_drive_service.check_admin_auth_status()
                
                if not auth_status.get('authenticated'):
                    google_drive_warnings.append(
                        f"Google Drive admin authentication required. {auth_status.get('message', 'Please authenticate at /auth/google/admin')}"
                    )
                else:
                    # Upload to admin's Google Drive
                    uploaded_file.seek(0)  # Reset file pointer
                    file_content = uploaded_file.read()
                    
                    # Get user information for sharing
                    user = User.query.get(current_user_id)
                    user_email = current_user_email or (user.email if user else None)
                    
                    drive_result = google_drive_service.upload_file_to_admin_drive(
                        file_content=file_content,
                        filename=duplicate_result['display_filename'],
                        mime_type=mime_type,
                        user_id=current_user_id,
                        user_email=user_email,
                        convert_to_doc=convert_to_doc,
                        share_with_user=share_with_user
                    )
                    
                    if drive_result.get('success'):
                        google_drive_file_id = drive_result.get('file_id')
                        google_doc_id = drive_result.get('doc_id')
                        
                        # Prepare Google Drive info for response
                        google_drive_info = {
                            'file_id': google_drive_file_id,
                            'drive_link': drive_result.get('drive_link'),
                            'is_shared': drive_result.get('sharing_successful', False),
                            'shared_with': drive_result.get('shared_with'),
                            'permissions': drive_result.get('permissions', 'writer'),
                            'folder_id': drive_result.get('folder_id')
                        }
                        
                        if google_doc_id:
                            google_drive_info.update({
                                'doc_id': google_doc_id,
                                'doc_link': drive_result.get('doc_link')
                            })
                        
                        # Add any sharing warnings
                        if drive_result.get('sharing_errors'):
                            google_drive_warnings.append("File uploaded to Google Drive but some sharing operations failed")
                        
                        # Add document conversion warnings if any
                        if drive_result.get('doc_conversion_error'):
                            google_drive_warnings.append(f"Document conversion failed: {drive_result.get('doc_conversion_error')}")
                    else:
                        google_drive_warnings.append(f"Google Drive upload failed: {drive_result.get('error', 'Unknown error')}")
                        
            except Exception as e:
                error_handler = ErrorHandler()
                current_app.logger.warning(f"Google Drive admin upload failed: {str(e)}")
                google_drive_warnings.append("Google Drive temporarily unavailable - file saved locally")
        
        # Initialize processing variables
        extracted_text = None
        metadata = {}
        keywords = []
        language = None
        processing_warning = None
        
        # Process file content if requested
        if should_process:
            try:
                file_processor = FileProcessingService()
                
                # Reset file pointer for processing
                uploaded_file.seek(0)
                
                processing_result = file_processor.process_file(uploaded_file)
                
                if processing_result.success:
                    extracted_text = processing_result.text
                    metadata = processing_result.metadata or {}
                    keywords = processing_result.keywords or []
                    language = processing_result.language
                else:
                    processing_warning = f"Text extraction failed: {processing_result.error_message}"
                    
            except Exception as e:
                processing_warning = f"File processing error: {str(e)}"
        
        # Create database record with enhanced fields
        try:
            # Generate a truly unique stored_filename to avoid cross-user conflicts
            import time
            timestamp = int(time.time() * 1000000)  # Microsecond precision
            file_extension = os.path.splitext(uploaded_file.filename)[1].lower()
            unique_stored_filename = f"user_{current_user_id}_{timestamp}_{validation_result.sanitized_filename}{file_extension if not validation_result.sanitized_filename.endswith(file_extension) else ''}"
            
            resume_file = ResumeFile(
                user_id=current_user_id,
                original_filename=uploaded_file.filename,  # Keep actual original filename
                display_filename=duplicate_result['display_filename'],  # Display name from duplicate handler
                stored_filename=unique_stored_filename,
                file_path=storage_result.file_path if storage_result.storage_type == 'local' else storage_result.s3_key,
                file_size=storage_result.file_size,
                mime_type=uploaded_file.content_type or 'application/octet-stream',
                storage_type=storage_result.storage_type,
                s3_bucket=getattr(storage_result, 's3_bucket', None),
                file_hash=duplicate_result['file_hash'],
                extracted_text=extracted_text,
                is_processed=should_process and extracted_text is not None,
                processing_status='completed' if extracted_text else 'pending',
                processing_error=processing_warning,
                # Additional content analysis fields (initialize as empty/default)
                page_count=None,
                paragraph_count=None,
                language=None,
                keywords=[],
                processing_time=None,
                processing_metadata={},
                # Thumbnail fields (initialize with defaults)
                has_thumbnail=False,
                thumbnail_path=None,
                thumbnail_status='pending',
                thumbnail_generated_at=None,
                thumbnail_error=None,
                tags=[],
                # Duplicate handling fields
                is_duplicate=duplicate_result['is_duplicate'],
                duplicate_sequence=duplicate_result.get('duplicate_sequence'),
                original_file_id=duplicate_result.get('original_file_id'),
                # Google Drive fields
                google_drive_file_id=google_drive_file_id,
                google_doc_id=google_doc_id
            )
            
            db.session.add(resume_file)
            db.session.commit()
            
            # Generate thumbnail for PDF files
            if resume_file.mime_type == 'application/pdf' and storage_result.file_path:
                try:
                    logger = logging.getLogger(__name__)
                    
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
                    
                    # Update database with thumbnail status
                    db.session.commit()
                    
                except Exception as e:
                    # Don't fail the entire upload if thumbnail generation fails
                    resume_file.set_thumbnail_failed(f"Thumbnail generation error: {str(e)}")
                    db.session.commit()
                    logger.warning(f"Thumbnail generation failed for file {resume_file.id}: {str(e)}")
            
            # Prepare enhanced response
            response_data = {
                'success': True,
                'message': 'File uploaded successfully',
                'file': {
                    'file_id': resume_file.id,
                    'user_id': resume_file.user_id,
                    'original_filename': resume_file.original_filename,
                    'display_filename': duplicate_result['display_filename'],
                    'stored_filename': resume_file.stored_filename,
                    'file_size': resume_file.file_size,
                    'mime_type': resume_file.mime_type,
                    'storage_type': resume_file.storage_type,
                    'download_url': storage_result.url,
                    'upload_date': resume_file.created_at.isoformat(),
                    'extracted_text': resume_file.extracted_text,
                    'processing_status': resume_file.processing_status,
                    'is_processed': resume_file.is_processed,
                    'file_hash': resume_file.file_hash,
                    'storage_path': resume_file.file_path,
                    'duplicate_info': {
                        'is_duplicate': resume_file.is_duplicate,
                        'duplicate_sequence': resume_file.duplicate_sequence,
                        'original_file_id': resume_file.original_file_id
                    }
                }
            }
            
            # Add duplicate notification if applicable
            if duplicate_result['is_duplicate']:
                response_data['duplicate_notification'] = duplicate_result['notification_message']
            
            # Add Google Drive information if available
            if google_drive_info:
                response_data['file']['google_drive'] = google_drive_info
            
            # Add warnings if any
            warnings = []
            if processing_warning:
                warnings.append(processing_warning)
                # Also add as top-level key for backward compatibility
                response_data['processing_warning'] = processing_warning
            if google_drive_warnings:
                warnings.extend(google_drive_warnings)
            
            if warnings:
                response_data['warnings'] = warnings
            
            return jsonify(response_data), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Database error occurred while saving file record',
                'error': str(e)
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'File upload failed',
            'error': str(e)
        }), 500


@api.route('/api/files/<int:file_id>/download', methods=['GET'])
@token_required
def download_file(file_id):
    """
    Download a file by ID
    ---
    tags:
      - File Management
    parameters:
      - name: file_id
        in: path
        required: true
        type: integer
        description: The ID of the file to download
      - name: inline
        in: query
        type: boolean
        default: false
        description: If true, display file inline instead of download
    responses:
      200:
        description: File downloaded successfully
        content:
          application/octet-stream:
            schema:
              type: string
              format: binary
      400:
        description: Invalid file ID format
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: Invalid file ID format
      401:
        description: Authentication required
        schema:
          type: object
          properties:
            message:
              type: string
              example: Authentication required
      403:
        description: Access denied
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: Access denied to this file
      404:
        description: File not found
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: File not found
      500:
        description: Server error during download
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: File download failed
    """
    try:
        # Validate file ID format
        try:
            file_id = int(file_id)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Invalid file ID format'
            }), 400
        
        # Get current user ID from JWT
        current_user_id = request.user.get('user_id')
        
        # Find the file record in database (exclude soft-deleted files)
        resume_file = ResumeFile.query.filter_by(
            id=file_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not resume_file:
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
        
        # Check if user owns the file (additional security check)
        if resume_file.user_id != current_user_id:
            return jsonify({
                'success': False,
                'message': 'Access denied to this file'
            }), 403
        
        # Initialize storage service with centralized configuration
        from app.utils.storage_config import StorageConfigManager
        try:
            storage_config = StorageConfigManager.get_storage_config_dict()
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': f'Storage configuration error: {str(e)}'
            }), 500
        
        storage_service = FileStorageService(storage_config)
        
        # Download file from storage
        try:
            download_result = storage_service.download_file(
                file_path=resume_file.file_path
            )
            
            if not download_result.success:
                return jsonify({
                    'success': False,
                    'message': f'File download failed: {download_result.error_message}'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Storage service error: {str(e)}'
            }), 500
        
        # Check if inline parameter is set
        inline = request.args.get('inline', 'false').lower() == 'true'
        
        # Log the download for audit purposes
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"File download: user_id={current_user_id}, file_id={file_id}, filename={resume_file.original_filename}")
        
        # Send the file
        try:
            # Use the stored MIME type from database, fallback to download result, then default
            mime_type = resume_file.mime_type or download_result.content_type or 'application/octet-stream'
            
            return send_file(
                BytesIO(download_result.content),
                as_attachment=not inline,
                download_name=resume_file.original_filename,
                mimetype=mime_type
            )
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error sending file: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Unexpected error during file download: {str(e)}'
        }), 500


@api.route('/api/files/<int:file_id>/info', methods=['GET'])
@token_required
def get_file_info(file_id):
    """
    Get detailed file information including metadata and text preview
    ---
    tags:
      - File Management
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: Bearer token for authentication
      - name: file_id
        in: path
        required: true
        type: integer
        description: ID of the file to get info for
      - name: include_text_preview
        in: query
        required: false
        type: boolean
        default: true
        description: Whether to include extracted text preview (first 500 chars)
    responses:
      200:
        description: File information retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            file:
              type: object
              properties:
                id:
                  type: integer
                  example: 42
                original_filename:
                  type: string
                  example: "Resume_2024.pdf"
                file_size:
                  type: integer
                  example: 524288
                file_size_formatted:
                  type: string
                  example: "512 KB"
                mime_type:
                  type: string
                  example: "application/pdf"
                storage_type:
                  type: string
                  example: "local"
                processing_status:
                  type: string
                  example: "completed"
                is_processed:
                  type: boolean
                  example: true
                extracted_text_length:
                  type: integer
                  example: 2104
                extracted_text_preview:
                  type: string
                  example: "John Doe\\nSoftware Engineer with 5+ years..."
                tags:
                  type: array
                  items:
                    type: string
                  example: ["resume", "tech"]
                created_at:
                  type: string
                  example: "2025-11-01T10:30:00Z"
                updated_at:
                  type: string
                  example: "2025-11-01T10:30:00Z"
      401:
        description: Authentication required
      403:
        description: Access denied to this file
      404:
        description: File not found
      500:
        description: Server error
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get current user ID
        current_user_id = request.user.get('user_id')
        
        # Convert file_id to integer if it's a string
        try:
            file_id = int(file_id)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Invalid file ID format'
            }), 400
        
        # Get include_text_preview parameter
        include_text_preview = request.args.get('include_text_preview', 'true').lower() == 'true'
        
        # Get file from database (exclude soft-deleted files)
        resume_file = ResumeFile.query.filter_by(
            id=file_id,
            user_id=current_user_id
        ).filter(ResumeFile.deleted_at.is_(None)).first()
        
        if not resume_file:
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
        
        # Prepare file info
        file_info = {
            'id': resume_file.id,
            'original_filename': resume_file.original_filename,
            'stored_filename': resume_file.stored_filename,
            'file_size': resume_file.file_size,
            'file_size_formatted': resume_file.format_file_size(),
            'mime_type': resume_file.mime_type,
            'storage_type': resume_file.storage_type,
            'file_path': resume_file.file_path,
            's3_bucket': resume_file.s3_bucket,
            'file_hash': resume_file.file_hash,
            'processing_status': resume_file.processing_status,
            'is_processed': resume_file.is_processed,
            'processing_error': resume_file.processing_error,
            'tags': resume_file.tags or [],
            'is_active': resume_file.is_active,
            'created_at': resume_file.created_at.isoformat() if resume_file.created_at else None,
            'updated_at': resume_file.updated_at.isoformat() if resume_file.updated_at else None
        }
        
        # Add thumbnail information
        file_info['thumbnail'] = {
            'has_thumbnail': resume_file.has_thumbnail,
            'thumbnail_url': resume_file.get_thumbnail_url() if resume_file.has_thumbnail else None,
            'thumbnail_status': resume_file.thumbnail_status,
            'thumbnail_generated_at': resume_file.thumbnail_generated_at.isoformat() if resume_file.thumbnail_generated_at else None
        }
        
        # Add extracted text info
        if resume_file.extracted_text:
            file_info['extracted_text_length'] = len(resume_file.extracted_text)
            if include_text_preview:
                # Include first 500 characters as preview
                preview_length = 500
                file_info['extracted_text_preview'] = resume_file.extracted_text[:preview_length]
                if len(resume_file.extracted_text) > preview_length:
                    file_info['extracted_text_preview'] += "..."
                file_info['has_more_text'] = len(resume_file.extracted_text) > preview_length
            else:
                file_info['extracted_text_preview'] = None
        else:
            file_info['extracted_text_length'] = 0
            file_info['extracted_text_preview'] = None
            file_info['has_more_text'] = False
        
        return jsonify({
            'success': True,
            'file': file_info
        }), 200
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Unexpected error during file info retrieval: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving file information: {str(e)}'
        }), 500


@api.route('/api/files/<int:file_id>/thumbnail', methods=['GET'])
@token_required
def get_file_thumbnail(file_id):
    """
    Get thumbnail image for a file
    ---
    tags:
      - File Management
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: Bearer token for authentication
      - name: file_id
        in: path
        required: true
        type: integer
        description: ID of the file to get thumbnail for
    responses:
      200:
        description: Thumbnail image
        content:
          image/jpeg:
            schema:
              type: string
              format: binary
        headers:
          Cache-Control:
            description: Cache control header
            type: string
            example: "public, max-age=86400"
          Content-Type:
            description: MIME type of the image
            type: string
            example: "image/jpeg"
      401:
        description: Authentication required
      403:
        description: Access denied to this file
      404:
        description: File or thumbnail not found
      500:
        description: Server error
    """
    import logging
    from flask import send_file, current_app
    from app.services.thumbnail_service import ThumbnailService
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get current user ID
        current_user_id = request.user.get('user_id')
        
        # Convert file_id to integer if it's a string
        try:
            file_id = int(file_id)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Invalid file ID format'
            }), 400
        
        # Get file from database (exclude soft-deleted files)
        resume_file = ResumeFile.query.filter_by(
            id=file_id,
            user_id=current_user_id
        ).filter(ResumeFile.deleted_at.is_(None)).first()
        
        if not resume_file:
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
        
        # Check if file has thumbnail
        if not resume_file.has_thumbnail or resume_file.thumbnail_status != 'completed':
            # Return default placeholder thumbnail
            default_thumbnail = ThumbnailService.get_default_thumbnail()
            if os.path.exists(default_thumbnail):
                return send_file(
                    default_thumbnail,
                    mimetype='image/jpeg',
                    as_attachment=False,
                    download_name=None,
                    max_age=86400  # Cache for 24 hours
                )
            else:
                return jsonify({
                    'success': False,
                    'message': 'Thumbnail not available'
                }), 404
        
        # Get thumbnail path
        thumbnail_path = resume_file.get_thumbnail_path()
        
        if not thumbnail_path or not os.path.exists(thumbnail_path):
            # Try default thumbnail again
            default_thumbnail = ThumbnailService.get_default_thumbnail()
            if os.path.exists(default_thumbnail):
                return send_file(
                    default_thumbnail,
                    mimetype='image/jpeg',
                    as_attachment=False,
                    download_name=None,
                    max_age=86400
                )
            else:
                return jsonify({
                    'success': False,
                    'message': 'Thumbnail file not found'
                }), 404
        
        # Serve the thumbnail with caching headers
        return send_file(
            thumbnail_path,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=None,
            max_age=86400  # Cache for 24 hours
        )
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Unexpected error during thumbnail retrieval: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving thumbnail: {str(e)}'
        }), 500


@api.route('/api/files/<int:file_id>/google-doc', methods=['GET'])
@token_required
def get_google_doc_access(file_id):
    """
    Get Google Doc access information for a file
    ---
    tags:
      - File Management
      - Google Drive Integration
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: Bearer token for authentication
      - name: file_id
        in: path
        required: true
        type: integer
        description: ID of the file to get Google Doc access for
      - name: ensure_sharing
        in: query
        required: false
        type: boolean
        default: true
        description: Whether to ensure the user has edit access to the Google Doc
    responses:
      200:
        description: Google Doc access information retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Google Doc access information retrieved successfully"
            google_doc:
              type: object
              properties:
                file_id:
                  type: string
                  example: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                doc_id:
                  type: string
                  example: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                drive_link:
                  type: string
                  example: "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view"
                doc_link:
                  type: string
                  example: "https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
                has_doc_version:
                  type: boolean
                  example: true
                is_shared:
                  type: boolean
                  example: true
                last_updated:
                  type: string
                  format: date-time
                  example: "2024-10-25T10:30:00Z"
      400:
        description: Invalid file ID format
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Invalid file ID format"
      401:
        description: Authentication required
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Authentication required"
      403:
        description: Access denied to this file
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Access denied to this file"
      404:
        description: File not found or no Google Drive integration
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "File not found or no Google Drive version available"
      500:
        description: Server error
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Error retrieving Google Doc access information"
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get current user from token
        current_user_id = request.user.get('user_id')
        current_user_email = request.user.get('email', '')
        
        # Get ensure_sharing parameter
        ensure_sharing = request.args.get('ensure_sharing', 'true').lower() == 'true'
        
        # Convert file_id to integer if it's a string
        try:
            file_id = int(file_id)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Invalid file ID format'
            }), 400
        
        # Get file from database
        resume_file = ResumeFile.query.filter_by(
            id=file_id,
            user_id=current_user_id,
            is_active=True  # Only show non-deleted files
        ).first()
        
        if not resume_file:
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
        
        # Check if file has Google Drive integration
        if not resume_file.google_drive_file_id:
            return jsonify({
                'success': False,
                'message': 'No Google Drive version available for this file'
            }), 404
        
        # Prepare Google Doc information
        google_doc_info = {
            'file_id': resume_file.google_drive_file_id,
            'drive_link': f"https://drive.google.com/file/d/{resume_file.google_drive_file_id}/view",
            'has_doc_version': resume_file.google_doc_id is not None,
            'last_updated': resume_file.updated_at.isoformat() if resume_file.updated_at else None
        }
        
        # Add Google Doc specific information if available
        if resume_file.google_doc_id:
            google_doc_info.update({
                'doc_id': resume_file.google_doc_id,
                'doc_link': f"https://docs.google.com/document/d/{resume_file.google_doc_id}/edit"
            })
        
        # Ensure user has access if requested and email is available
        if ensure_sharing and current_user_email:
            try:
                google_drive_service = GoogleDriveService()
                
                # Share the main file
                google_drive_service.share_file_with_user(
                    resume_file.google_drive_file_id,
                    current_user_email,
                    'writer'
                )
                
                # Share the Google Doc if available
                if resume_file.google_doc_id:
                    google_drive_service.share_file_with_user(
                        resume_file.google_doc_id,
                        current_user_email,
                        'writer'
                    )
                
                google_doc_info['is_shared'] = True
                
            except Exception as sharing_error:
                logger.warning(f"Failed to ensure sharing for file {file_id}: {str(sharing_error)}")
                google_doc_info['is_shared'] = False
                google_doc_info['sharing_warning'] = "Could not verify or update sharing permissions"
        else:
            google_doc_info['is_shared'] = None  # Unknown status
        
        return jsonify({
            'success': True,
            'message': 'Google Doc access information retrieved successfully',
            'google_doc': google_doc_info
        }), 200
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Unexpected error during Google Doc access retrieval: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving Google Doc access information: {str(e)}'
        }), 500


@api.route('/api/files/<file_id>', methods=['DELETE'])
@token_required
def delete_file(file_id):
    """
    Delete a file by ID
    ---
    tags:
      - File Management
    parameters:
      - name: file_id
        in: path
        required: true
        type: integer
        description: The ID of the file to delete
      - name: force
        in: query
        type: boolean
        default: false
        description: If true, permanently delete from storage (hard delete). If false, only mark as inactive (soft delete)
    responses:
      200:
        description: File deleted successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: File deleted successfully
            file_id:
              type: integer
              example: 123
            delete_type:
              type: string
              enum: [soft, hard]
              example: soft
      400:
        description: Invalid file ID format
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: Invalid file ID format
      401:
        description: Authentication required
        schema:
          type: object
          properties:
            message:
              type: string
              example: Authentication required
      403:
        description: Access denied
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: Access denied to this file
      404:
        description: File not found
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: File not found
      500:
        description: Server error during deletion
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: File deletion failed
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Validate file ID format
        try:
            file_id = int(file_id)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Invalid file ID format'
            }), 400
        
        # Get current user ID from JWT
        current_user_id = request.user.get('user_id')
        
        # Check for force parameter
        force_delete = request.args.get('force', 'false').lower() == 'true'
        
        # Find the file record in database (exclude soft-deleted files unless force deleting)
        if force_delete:
            # For force delete, allow access to soft-deleted files to hard delete them
            resume_file = ResumeFile.query.filter_by(
                id=file_id,
                user_id=current_user_id
            ).first()
        else:
            # For soft delete, only allow access to non-deleted files
            resume_file = ResumeFile.query.filter_by(
                id=file_id,
                user_id=current_user_id,
                is_active=True
            ).first()
        
        if not resume_file:
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
        
        # Check if user owns the file (additional security check)
        if resume_file.user_id != current_user_id:
            return jsonify({
                'success': False,
                'message': 'Access denied to this file'
            }), 403
        
        # Perform storage deletion if force delete and file has a path
        if force_delete and resume_file.file_path:
            # Initialize storage service with centralized configuration
            from app.utils.storage_config import StorageConfigManager
            try:
                storage_config = StorageConfigManager.get_storage_config_dict()
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'message': f'Storage configuration error: {str(e)}'
                }), 500
            
            storage_service = FileStorageService(storage_config)
            
            # Hard delete: remove from storage
            delete_result = storage_service.delete_file(
                file_path=resume_file.file_path,
                storage_type=resume_file.storage_type,
                s3_bucket=resume_file.s3_bucket
            )
            
            if not delete_result.success:
                logging.getLogger(__name__).error(f"Storage deletion failed for file {file_id}: {delete_result.error_message}")
                return jsonify({
                    'success': False,
                    'message': f'Failed to delete file from storage: {delete_result.error_message}'
                }), 500
            
            # Remove from database completely
            db.session.delete(resume_file)
            delete_type = 'hard'
            
        else:
            # Soft delete: mark as deleted with timestamp and set is_active=False
            resume_file.is_active = False
            resume_file.deleted_at = datetime.utcnow()
            resume_file.deleted_by = current_user_id
            resume_file.updated_at = datetime.utcnow()
            delete_type = 'soft'
        
        # Commit the database changes
        db.session.commit()
        
        # Log the deletion for audit purposes
        logger.info(f"File {file_id} {delete_type} deleted by user {current_user_id}")
        
        return jsonify({
            'success': True,
            'message': f'File {"permanently" if delete_type == "hard" else ""} deleted successfully',
            'file_id': file_id,
            'delete_type': delete_type
        }), 200
        
    except Exception as e:
        # Rollback any database changes
        db.session.rollback()
        logging.getLogger(__name__).error(f"Unexpected error during file deletion: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Unexpected error during file deletion: {str(e)}'
        }), 500


@api.route('/api/files', methods=['GET'])
@token_required
def list_files():
    """
    List files for the authenticated user
    ---
    tags:
      - File Management
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number for pagination (1-based)
      - name: limit
        in: query
        type: integer
        default: 10
        description: Number of files per page (max 100)
      - name: sort_by
        in: query
        type: string
        enum: [created_at, updated_at, file_size, original_filename]
        default: created_at
        description: Field to sort by
      - name: sort_order
        in: query
        type: string
        enum: [asc, desc]
        default: desc
        description: Sort order
      - name: mime_type
        in: query
        type: string
        description: Filter by MIME type (e.g., application/pdf)
      - name: processing_status
        in: query
        type: string
        enum: [pending, processing, completed, failed]
        description: Filter by processing status
      - name: search
        in: query
        type: string
        description: Search in filenames (case-insensitive)
      - name: include_deleted
        in: query
        type: boolean
        default: false
        description: Include soft-deleted files in results (admin feature)
    responses:
      200:
        description: Files listed successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            files:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 123
                  original_filename:
                    type: string
                    example: resume.pdf
                  file_size:
                    type: integer
                    example: 1024
                  mime_type:
                    type: string
                    example: application/pdf
                  storage_type:
                    type: string
                    example: local
                  created_at:
                    type: string
                    format: date-time
                    example: "2024-01-01T10:00:00Z"
                  updated_at:
                    type: string
                    format: date-time
                    example: "2024-01-01T10:00:00Z"
                  processing_status:
                    type: string
                    example: completed
                  page_count:
                    type: integer
                    example: 2
            total:
              type: integer
              example: 25
            page:
              type: integer
              example: 1
            limit:
              type: integer
              example: 10
            has_next:
              type: boolean
              example: true
            has_prev:
              type: boolean
              example: false
      400:
        description: Invalid query parameters
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: Invalid pagination parameters
      401:
        description: Authentication required
        schema:
          type: object
          properties:
            error:
              type: string
              example: Authentication required
      500:
        description: Server error during listing
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: Error retrieving files
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get current user ID from JWT
        current_user_id = request.user.get('user_id')
        
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        mime_type = request.args.get('mime_type')
        processing_status = request.args.get('processing_status')
        search = request.args.get('search')
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
        
        # Validate pagination parameters
        if page < 1:
            return jsonify({
                'success': False,
                'message': 'Page number must be 1 or greater'
            }), 400
            
        if limit < 1 or limit > 100:
            return jsonify({
                'success': False,
                'message': 'Limit must be between 1 and 100'
            }), 400
        
        # Validate sort parameters
        valid_sort_fields = ['created_at', 'updated_at', 'file_size', 'original_filename']
        if sort_by not in valid_sort_fields:
            return jsonify({
                'success': False,
                'message': f'Invalid sort field. Must be one of: {", ".join(valid_sort_fields)}'
            }), 400
            
        valid_sort_orders = ['asc', 'desc']
        if sort_order not in valid_sort_orders:
            return jsonify({
                'success': False,
                'message': 'Invalid sort order. Must be "asc" or "desc"'
            }), 400
        
        # Validate processing status
        if processing_status:
            valid_statuses = ['pending', 'processing', 'completed', 'failed']
            if processing_status not in valid_statuses:
                return jsonify({
                    'success': False,
                    'message': f'Invalid processing status. Must be one of: {", ".join(valid_statuses)}'
                }), 400
        
        # Build query - filter out soft-deleted files by default
        query = ResumeFile.query.filter_by(user_id=current_user_id)
        
        # Filter out soft-deleted files unless explicitly requested (admin feature)
        if not include_deleted:
            query = query.filter(ResumeFile.is_active == True)
        
        # Apply filters
        if mime_type:
            query = query.filter(ResumeFile.mime_type == mime_type)
            
        if processing_status:
            query = query.filter(ResumeFile.processing_status == processing_status)
            
        if search:
            query = query.filter(ResumeFile.original_filename.ilike(f'%{search}%'))
        
        # Apply sorting
        sort_column = getattr(ResumeFile, sort_by)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        files = query.offset(offset).limit(limit).all()
        
        # Calculate pagination info
        has_next = total_count > (page * limit)
        has_prev = page > 1
        
        # Helper function to safely get attributes, avoiding Mock objects
        def safe_get_attr(obj, attr, default=None):
            """Safely get attribute value, avoiding Mock objects"""
            try:
                val = getattr(obj, attr, default)
                # Check if it's a Mock object or other non-serializable type
                if hasattr(val, '_mock_name'):
                    return default
                return val
            except:
                return default
        
        # Format response
        files_data = []
        for file in files:
            # Handle datetime fields safely
            created_at = safe_get_attr(file, 'created_at', None)
            updated_at = safe_get_attr(file, 'updated_at', None)
            deleted_at = safe_get_attr(file, 'deleted_at', None)
            
            file_data = {
                'id': safe_get_attr(file, 'id', None),
                'original_filename': safe_get_attr(file, 'original_filename', ''),
                'display_filename': safe_get_attr(file, 'display_filename', safe_get_attr(file, 'original_filename', '')),
                'file_size': safe_get_attr(file, 'file_size', 0),
                'mime_type': safe_get_attr(file, 'mime_type', ''),
                'storage_type': safe_get_attr(file, 'storage_type', 'local'),
                'created_at': created_at.isoformat() if created_at and hasattr(created_at, 'isoformat') else None,
                'updated_at': updated_at.isoformat() if updated_at and hasattr(updated_at, 'isoformat') else None,
                'processing_status': safe_get_attr(file, 'processing_status', 'pending'),
                'is_deleted': deleted_at is not None,
                'deleted_at': deleted_at.isoformat() if deleted_at and hasattr(deleted_at, 'isoformat') else None,
                'is_duplicate': safe_get_attr(file, 'is_duplicate', False),
                'duplicate_sequence': safe_get_attr(file, 'duplicate_sequence', None)
            }
            
            # Add Google Drive information if available
            google_drive_file_id = safe_get_attr(file, 'google_drive_file_id', None)
            if google_drive_file_id:
                google_doc_id = safe_get_attr(file, 'google_doc_id', None)
                file_data['google_drive'] = {
                    'file_id': google_drive_file_id,
                    'doc_id': google_doc_id,
                    'drive_link': f"https://drive.google.com/file/d/{google_drive_file_id}/view"
                }
                if google_doc_id:
                    file_data['google_drive']['doc_link'] = f"https://docs.google.com/document/d/{google_doc_id}/edit"
            
            files_data.append(file_data)
        
        return jsonify({
            'success': True,
            'files': files_data,
            'total': total_count,
            'page': page,
            'limit': limit,
            'has_next': has_next,
            'has_prev': has_prev
        }), 200
        
    except Exception as e:
        # Log the error
        logging.getLogger(__name__).error(f"Unexpected error during file listing: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving files: {str(e)}'
        }), 500


@api.route('/api/files/<int:file_id>/restore', methods=['POST'])
@token_required
def restore_file(file_id):
    """
    Restore a soft-deleted file
    ---
    tags:
      - File Management
      - Admin
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: Bearer token for authentication
      - name: file_id
        in: path
        required: true
        type: integer
        description: ID of the file to restore
    responses:
      200:
        description: File restored successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "File restored successfully"
            file:
              type: object
              properties:
                file_id:
                  type: integer
                  example: 123
                original_filename:
                  type: string
                  example: "resume.pdf"
                restored_at:
                  type: string
                  format: date-time
                  example: "2024-10-25T10:30:00Z"
                restored_by:
                  type: integer
                  example: 1
      400:
        description: Invalid file ID format or file not deleted
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "File is not deleted or invalid file ID"
      401:
        description: Authentication required
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Authentication required"
      403:
        description: Access denied - user doesn't own the file
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Access denied to this file"
      404:
        description: File not found
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "File not found"
      500:
        description: Server error during restoration
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "File restoration failed"
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get current user ID from JWT
        current_user_id = request.user.get('user_id')
        
        # Convert file_id to integer if it's a string
        try:
            file_id = int(file_id)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Invalid file ID format'
            }), 400
        
        # Find the soft-deleted file
        resume_file = ResumeFile.query.filter_by(
            id=file_id,
            user_id=current_user_id
        ).filter(ResumeFile.deleted_at.is_not(None)).first()
        
        if not resume_file:
            return jsonify({
                'success': False,
                'message': 'File not found or not deleted'
            }), 404
        
        # Check if user owns the file (additional security check)
        if resume_file.user_id != current_user_id:
            return jsonify({
                'success': False,
                'message': 'Access denied to this file'
            }), 403
        
        # Restore the file
        resume_file.deleted_at = None
        resume_file.deleted_by = None
        resume_file.updated_at = datetime.utcnow()
        
        # Commit the database changes
        db.session.commit()
        
        # Log the restoration for audit purposes
        logger.info(f"File {file_id} restored by user {current_user_id}")
        
        return jsonify({
            'success': True,
            'message': 'File restored successfully',
            'file': {
                'file_id': resume_file.id,
                'original_filename': resume_file.original_filename,
                'display_filename': getattr(resume_file, 'display_filename', resume_file.original_filename),
                'restored_at': resume_file.updated_at.isoformat(),
                'restored_by': current_user_id
            }
        }), 200
        
    except Exception as e:
        # Rollback any database changes
        db.session.rollback()
        logging.getLogger(__name__).error(f"Unexpected error during file restoration: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'File restoration failed: {str(e)}'
        }), 500


@api.route('/api/admin/files/deleted', methods=['GET'])
@token_required
def list_deleted_files():
    """
    List soft-deleted files for admin review
    ---
    tags:
      - File Management
      - Admin
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: Bearer token for authentication (admin required)
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number for pagination (1-based)
      - name: limit
        in: query
        type: integer
        default: 10
        description: Number of files per page (max 100)
      - name: user_id
        in: query
        type: integer
        description: Filter by specific user ID
      - name: sort_by
        in: query
        type: string
        enum: [deleted_at, created_at, file_size, original_filename]
        default: deleted_at
        description: Field to sort by
      - name: sort_order
        in: query
        type: string
        enum: [asc, desc]
        default: desc
        description: Sort order
    responses:
      200:
        description: Deleted files listed successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            files:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 123
                  user_id:
                    type: integer
                    example: 1
                  original_filename:
                    type: string
                    example: "resume.pdf"
                  display_filename:
                    type: string
                    example: "Resume (1).pdf"
                  file_size:
                    type: integer
                    example: 1024
                  created_at:
                    type: string
                    format: date-time
                    example: "2024-01-01T10:00:00Z"
                  deleted_at:
                    type: string
                    format: date-time
                    example: "2024-01-02T10:00:00Z"
                  deleted_by:
                    type: integer
                    example: 1
            total:
              type: integer
              example: 25
            page:
              type: integer
              example: 1
            limit:
              type: integer
              example: 10
      401:
        description: Authentication required
      403:
        description: Admin access required
      500:
        description: Server error
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get current user from JWT
        current_user_id = request.user.get('user_id')
        
        # TODO: Add proper admin role checking
        # For now, just log the admin access attempt
        logger.info(f"Admin deleted files access attempted by user {current_user_id}")
        
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        user_id_filter = request.args.get('user_id', type=int)
        sort_by = request.args.get('sort_by', 'deleted_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Validate pagination parameters
        if page < 1:
            return jsonify({
                'success': False,
                'message': 'Page number must be 1 or greater'
            }), 400
            
        if limit < 1 or limit > 100:
            return jsonify({
                'success': False,
                'message': 'Limit must be between 1 and 100'
            }), 400
        
        # Validate sort parameters
        valid_sort_fields = ['deleted_at', 'created_at', 'file_size', 'original_filename']
        if sort_by not in valid_sort_fields:
            return jsonify({
                'success': False,
                'message': f'Invalid sort field. Must be one of: {", ".join(valid_sort_fields)}'
            }), 400
            
        valid_sort_orders = ['asc', 'desc']
        if sort_order not in valid_sort_orders:
            return jsonify({
                'success': False,
                'message': 'Invalid sort order. Must be "asc" or "desc"'
            }), 400
        
        # Build query for soft-deleted files only
        query = ResumeFile.query.filter(ResumeFile.deleted_at.is_not(None))
        
        # Apply user filter if specified
        if user_id_filter:
            query = query.filter(ResumeFile.user_id == user_id_filter)
        
        # Apply sorting
        sort_column = getattr(ResumeFile, sort_by)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        files = query.offset(offset).limit(limit).all()
        
        # Calculate pagination info
        has_next = total_count > (page * limit)
        has_prev = page > 1
        
        # Format response
        files_data = []
        for file in files:
            files_data.append({
                'id': file.id,
                'user_id': file.user_id,
                'original_filename': file.original_filename,
                'display_filename': getattr(file, 'display_filename', file.original_filename),
                'file_size': file.file_size,
                'mime_type': file.mime_type,
                'created_at': file.created_at.isoformat() if file.created_at else None,
                'deleted_at': file.deleted_at.isoformat() if file.deleted_at else None,
                'deleted_by': file.deleted_by,
                'is_duplicate': getattr(file, 'is_duplicate', False),
                'google_drive_file_id': getattr(file, 'google_drive_file_id', None)
            })
        
        return jsonify({
            'success': True,
            'files': files_data,
            'total': total_count,
            'page': page,
            'limit': limit,
            'has_next': has_next,
            'has_prev': has_prev
        }), 200
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Unexpected error during deleted files listing: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving deleted files: {str(e)}'
        }), 500


@api.route('/api/admin/files/<int:file_id>/restore', methods=['POST'])
@token_required  
def admin_restore_file(file_id):
    """
    Admin restore a soft-deleted file for any user
    ---
    tags:
      - File Management
      - Admin
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: Bearer token for authentication (admin required)
      - name: file_id
        in: path
        required: true
        type: integer
        description: ID of the file to restore
    responses:
      200:
        description: File restored successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "File restored successfully"
            file:
              type: object
              properties:
                file_id:
                  type: integer
                  example: 123
                user_id:
                  type: integer
                  example: 1
                original_filename:
                  type: string
                  example: "resume.pdf"
                restored_at:
                  type: string
                  format: date-time
                  example: "2024-10-25T10:30:00Z"
                restored_by:
                  type: integer
                  example: 2
      400:
        description: Invalid file ID format or file not deleted
      401:
        description: Authentication required
      403:
        description: Admin access required
      404:
        description: File not found
      500:
        description: Server error during restoration
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get current user from JWT
        current_user_id = request.user.get('user_id')
        
        # TODO: Add proper admin role checking
        logger.info(f"Admin file restoration attempted by user {current_user_id} for file {file_id}")
        
        # Convert file_id to integer if it's a string
        try:
            file_id = int(file_id)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Invalid file ID format'
            }), 400
        
        # Find the soft-deleted file (any user's file)
        resume_file = ResumeFile.query.filter_by(id=file_id).filter(
            ResumeFile.deleted_at.is_not(None)
        ).first()
        
        if not resume_file:
            return jsonify({
                'success': False,
                'message': 'File not found or not deleted'
            }), 404
        
        # Restore the file
        resume_file.deleted_at = None
        resume_file.deleted_by = None
        resume_file.updated_at = datetime.utcnow()
        
        # Commit the database changes
        db.session.commit()
        
        # Log the restoration for audit purposes
        logger.info(f"File {file_id} (user {resume_file.user_id}) restored by admin {current_user_id}")
        
        return jsonify({
            'success': True,
            'message': 'File restored successfully',
            'file': {
                'file_id': resume_file.id,
                'user_id': resume_file.user_id,
                'original_filename': resume_file.original_filename,
                'display_filename': getattr(resume_file, 'display_filename', resume_file.original_filename),
                'restored_at': resume_file.updated_at.isoformat(),
                'restored_by': current_user_id
            }
        }), 200
        
    except Exception as e:
        # Rollback any database changes
        db.session.rollback()
        logging.getLogger(__name__).error(f"Unexpected error during admin file restoration: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'File restoration failed: {str(e)}'
        }), 500


@api.route('/api/admin/files/<int:file_id>/permanent-delete', methods=['DELETE'])
@token_required
def admin_permanent_delete(file_id):
    """
    Admin permanently delete a soft-deleted file (hard delete)
    ---
    tags:
      - File Management
      - Admin
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: Bearer token for authentication (admin required)
      - name: file_id
        in: path
        required: true
        type: integer
        description: ID of the file to permanently delete
    responses:
      200:
        description: File permanently deleted successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "File permanently deleted"
            file_id:
              type: integer
              example: 123
      400:
        description: Invalid file ID format
      401:
        description: Authentication required
      403:
        description: Admin access required
      404:
        description: File not found or not deleted
      500:
        description: Server error during permanent deletion
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get current user from JWT
        current_user_id = request.user.get('user_id')
        
        # TODO: Add proper admin role checking
        logger.warning(f"Admin permanent deletion attempted by user {current_user_id} for file {file_id}")
        
        # Convert file_id to integer if it's a string
        try:
            file_id = int(file_id)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Invalid file ID format'
            }), 400
        
        # Find the soft-deleted file (any user's file)
        resume_file = ResumeFile.query.filter_by(id=file_id).filter(
            ResumeFile.deleted_at.is_not(None)
        ).first()
        
        if not resume_file:
            return jsonify({
                'success': False,
                'message': 'File not found or not deleted'
            }), 404
        
        # Get file information for logging before deletion
        original_filename = resume_file.original_filename
        file_user_id = resume_file.user_id
        
        # Delete from storage if file has a path
        if resume_file.file_path:
            try:
                # Initialize storage service with centralized configuration
                from app.utils.storage_config import StorageConfigManager
                storage_config = StorageConfigManager.get_storage_config_dict()
                storage_service = FileStorageService(storage_config)
                
                # Hard delete: remove from storage
                delete_result = storage_service.delete_file(
                    file_path=resume_file.file_path,
                    storage_type=resume_file.storage_type,
                    s3_bucket=resume_file.s3_bucket
                )
                
                if not delete_result.success:
                    logging.getLogger(__name__).error(f"Storage deletion failed for file {file_id}: {delete_result.error_message}")
                    # Continue with database deletion even if storage deletion fails
                    
            except Exception as storage_error:
                logging.getLogger(__name__).error(f"Error deleting file from storage: {str(storage_error)}")
                # Continue with database deletion even if storage deletion fails
        
        # Remove from database completely
        db.session.delete(resume_file)
        db.session.commit()
        
        # Log the permanent deletion for audit purposes
        logger.warning(f"File {file_id} ({original_filename}) for user {file_user_id} permanently deleted by admin {current_user_id}")
        
        return jsonify({
            'success': True,
            'message': 'File permanently deleted',
            'file_id': file_id
        }), 200
        
    except Exception as e:
        # Rollback any database changes
        db.session.rollback()
        logging.getLogger(__name__).error(f"Unexpected error during admin permanent deletion: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Permanent deletion failed: {str(e)}'
        }), 500


@api.route('/api/files', methods=['DELETE'])
@token_required
def bulk_delete_files():
    """
    Bulk delete multiple files by their IDs
    ---
    tags:
      - File Management
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: Bearer token for authentication
      - in: body
        name: file_ids
        required: true
        schema:
          type: object
          properties:
            file_ids:
              type: array
              items:
                type: integer
              example: [1, 2, 3, 4]
              description: Array of file IDs to delete
            force:
              type: boolean
              default: false
              description: If true, permanently delete from storage (hard delete). If false, only mark as inactive (soft delete)
    responses:
      200:
        description: Bulk delete completed (may include partial failures)
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Bulk delete completed"
            deleted_count:
              type: integer
              example: 3
            failed_count:
              type: integer
              example: 1
            total_requested:
              type: integer
              example: 4
            failed_files:
              type: array
              items:
                type: object
                properties:
                  file_id:
                    type: integer
                  error:
                    type: string
              example: [{"file_id": 4, "error": "File not found"}]
      400:
        description: Invalid request format or missing file_ids
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "file_ids array is required"
      401:
        description: Authentication required
      500:
        description: Server error during bulk deletion
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get current user ID
        current_user_id = request.user.get('user_id')
        
        # Get request data
        data = request.get_json()
        if not data or 'file_ids' not in data:
            return jsonify({
                'success': False,
                'message': 'file_ids array is required'
            }), 400
        
        file_ids = data.get('file_ids', [])
        force_delete = data.get('force', False)
        
        if not isinstance(file_ids, list) or len(file_ids) == 0:
            return jsonify({
                'success': False,
                'message': 'file_ids must be a non-empty array'
            }), 400
        
        # Validate file_ids are integers
        try:
            file_ids = [int(fid) for fid in file_ids]
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'All file_ids must be valid integers'
            }), 400
        
        deleted_count = 0
        failed_count = 0
        failed_files = []
        
        # Initialize storage service
        storage_service = FileStorageService({
            'storage_type': os.environ.get('FILE_STORAGE_TYPE', 'local'),
            'local_storage_path': os.environ.get('FILE_STORAGE_PATH', '/app/storage'),
            'aws_access_key_id': os.environ.get('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
            's3_bucket_name': os.environ.get('AWS_S3_BUCKET_NAME'),
            'base_url': request.host_url.rstrip('/')
        })
        
        # Process each file
        for file_id in file_ids:
            try:
                # Get file from database (must belong to current user)
                if force_delete:
                    # For force delete, allow access to soft-deleted files to hard delete them
                    resume_file = ResumeFile.query.filter_by(
                        id=file_id,
                        user_id=current_user_id
                    ).first()
                else:
                    # For soft delete, only allow access to non-deleted files
                    resume_file = ResumeFile.query.filter_by(
                        id=file_id,
                        user_id=current_user_id
                    ).filter(ResumeFile.deleted_at.is_(None)).first()
                
                if not resume_file:
                    failed_files.append({
                        'file_id': file_id,
                        'error': 'File not found or access denied'
                    })
                    failed_count += 1
                    continue
                
                # Delete from storage if force delete or if file exists
                if force_delete:
                    # Hard delete - remove from storage
                    try:
                        delete_result = storage_service.delete_file(
                            resume_file.file_path,
                            resume_file.storage_type,
                            resume_file.s3_bucket
                        )
                        
                        if not delete_result.success:
                            logger.warning(f"Failed to delete file from storage: {delete_result.error_message}")
                            # Continue with database deletion even if storage deletion fails
                    except Exception as storage_error:
                        logging.getLogger(__name__).error(f"Error deleting file from storage: {str(storage_error)}")
                        # Continue with database deletion even if storage deletion fails
                    
                    # Remove from database
                    db.session.delete(resume_file)
                else:
                    # Soft delete - mark as deleted with timestamp
                    resume_file.deleted_at = datetime.utcnow()
                    resume_file.deleted_by = current_user_id
                    resume_file.updated_at = datetime.utcnow()
                
                db.session.commit()
                deleted_count += 1
                
            except Exception as e:
                logging.getLogger(__name__).error(f"Error deleting file {file_id}: {str(e)}")
                failed_files.append({
                    'file_id': file_id,
                    'error': str(e)
                })
                failed_count += 1
                # Rollback the transaction for this file
                db.session.rollback()
        
        # Determine overall success
        total_requested = len(file_ids)
        success = failed_count == 0
        
        message = f"Bulk delete completed. {deleted_count} deleted"
        if failed_count > 0:
            message += f", {failed_count} failed"
        
        response_data = {
            'success': success,
            'message': message,
            'deleted_count': deleted_count,
            'failed_count': failed_count,
            'total_requested': total_requested
        }
        
        # Include failed files info if there were failures
        if failed_files:
            response_data['failed_files'] = failed_files
        
        # Return 200 even with partial failures (bulk operations often do this)
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Unexpected error during bulk file deletion: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error during bulk deletion: {str(e)}'
        }), 500


@api.route('/api/files/<int:file_id>/process', methods=['POST'])
@token_required
def process_file(file_id):
    """
    Process a resume file to extract text content and metadata
    ---
    tags:
      - File Management
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: Bearer token for authentication
      - name: file_id
        in: path
        required: true
        type: integer
        description: ID of the file to process
      - name: force
        in: query
        required: false
        type: boolean
        default: false
        description: Force reprocessing of already processed files
    responses:
      200:
        description: File processed successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "File processed successfully"
            processing_result:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                text:
                  type: string
                  example: "Extracted resume text content..."
                file_type:
                  type: string
                  example: "pdf"
                metadata:
                  type: object
                  example: {"author": "John Doe", "creation_date": "2024-01-01"}
                processing_time:
                  type: number
                  example: 1.23
                page_count:
                  type: integer
                  example: 2
                paragraph_count:
                  type: integer
                  example: 15
                keywords:
                  type: array
                  items:
                    type: string
                  example: ["Python", "Machine Learning", "Data Science"]
                language:
                  type: string
                  example: "en"
      400:
        description: Bad request (invalid file format, missing parameters, etc.)
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "File is already being processed"
      401:
        description: Unauthorized access
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Token is missing or invalid"
      403:
        description: Forbidden - user doesn't own the file
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Access denied. You don't have permission to process this file."
      404:
        description: File not found
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "File not found"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Error processing file"
    """
    try:
        # Import logging
        import logging
        logger = logging.getLogger(__name__)
        
        # Get current user from token
        current_user_id = request.user.get('user_id')
        
        # Get force parameter
        force = request.args.get('force', 'false').lower() == 'true'
        
        # Validate file_id format
        if not isinstance(file_id, int) or file_id <= 0:
            return jsonify({
                'success': False,
                'message': 'Invalid file ID format'
            }), 400
        
        # Find the file (exclude soft-deleted files)
        file_record = ResumeFile.query.filter_by(
            id=file_id,
            user_id=current_user_id
        ).filter(ResumeFile.deleted_at.is_(None)).first()
        
        if not file_record:
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
        
        # Check if file is already processed (unless forcing)
        if not force and file_record.processing_status == 'completed':
            return jsonify({
                'success': False,
                'message': 'File has already been processed. Use force=true to reprocess.'
            }), 400
        
        # Check if file is currently being processed
        if file_record.processing_status == 'processing':
            return jsonify({
                'success': False,
                'message': 'File is already being processed'
            }), 400
        
        # Update status to processing
        file_record.processing_status = 'processing'
        db.session.commit()
        
        try:
            # Initialize storage service with centralized configuration
            from app.utils.storage_config import StorageConfigManager
            try:
                storage_config = StorageConfigManager.get_storage_config_dict()
            except ValueError as e:
                file_record.processing_status = 'failed'
                file_record.error_message = f'Storage configuration error: {str(e)}'
                db.session.commit()
                return jsonify({
                    'success': False,
                    'message': f'Storage configuration error: {str(e)}'
                }), 500
            
            # Download the file from storage
            storage_service = FileStorageService(storage_config)
            
            download_result = storage_service.download_file(file_record.file_path)
            
            if not download_result.success:
                file_record.processing_status = 'failed'
                file_record.error_message = f"Failed to download file: {download_result.error_message}"
                db.session.commit()
                
                logging.getLogger(__name__).error(f"Failed to download file {file_id} for processing: {download_result.error_message}")
                
                return jsonify({
                    'success': False,
                    'message': f'Failed to download file for processing: {download_result.error_message}'
                }), 500
            
            # Create file-like object from downloaded content
            import io
            file_like_obj = io.BytesIO(download_result.content)
            file_like_obj.filename = file_record.original_filename
            file_like_obj.content_type = file_record.mime_type
            
            # Process the file using FileProcessingService
            processing_service = FileProcessingService()
            processing_result = processing_service.process_file(file_like_obj)
            
            if processing_result.success:
                # Update file record with processing results
                file_record.processing_status = 'completed'
                file_record.extracted_text = processing_result.text
                file_record.is_processed = True
                file_record.processing_error = None  # Clear any previous errors
                
                # Store processing metadata
                file_record.page_count = processing_result.page_count
                file_record.paragraph_count = processing_result.paragraph_count
                file_record.language = processing_result.language
                file_record.keywords = processing_result.keywords or []
                file_record.processing_time = processing_result.processing_time
                file_record.processing_metadata = processing_result.metadata or {}
                
                # Log successful processing
                logger.info(f"File {file_id} processed successfully for user {current_user_id}")
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'File processed successfully',
                    'processing_result': {
                        'success': processing_result.success,
                        'text': processing_result.text,
                        'file_type': processing_result.file_type,
                        'metadata': processing_result.metadata or {},
                        'processing_time': processing_result.processing_time,
                        'page_count': processing_result.page_count,
                        'paragraph_count': processing_result.paragraph_count,
                        'keywords': processing_result.keywords or [],
                        'language': processing_result.language
                    }
                }), 200
            else:
                # Processing failed
                file_record.processing_status = 'failed'
                file_record.error_message = processing_result.error_message
                
                # Log processing failure
                logging.getLogger(__name__).error(f"File {file_id} processing failed for user {current_user_id}: {processing_result.error_message}")
                
                db.session.commit()
                
                return jsonify({
                    'success': False,
                    'message': f'File processing failed: {processing_result.error_message}'
                }), 500
                
        except Exception as processing_error:
            # Update status to failed on processing error
            file_record.processing_status = 'failed'
            file_record.error_message = str(processing_error)
            db.session.commit()
            
            # Log processing error
            logging.getLogger(__name__).error(f"Error processing file {file_id} for user {current_user_id}: {str(processing_error)}")
            
            return jsonify({
                'success': False,
                'message': f'Error processing file: {str(processing_error)}'
            }), 500
            
    except Exception as e:
        # Log the error
        logging.getLogger(__name__).error(f"Unexpected error during file processing: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error processing file: {str(e)}'
        }), 500


@api.route('/api/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              format: email
              example: user@example.com
            password:
              type: string
              format: password
              example: SecurePassword123!
    responses:
      201:
        description: User registered successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 201
            user:
              type: object
              properties:
                email:
                  type: string
      400:
        description: Invalid input or email already registered
      500:
        description: Registration failed
    """
    data = request.get_json()
    
    # Validate input
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password required"}), 400
        
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 400
    
    # Create new user
    user = User(
        email=data['email'],
        username=data['email'],  # Use email as username if not provided
        updated_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    user.set_password(data['password'])
    
    try:
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            "status": 201,
            "user": {"email": user.email}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Registration failed"}), 500

@api.route('/api/login', methods=['POST'])
def login():
    """
    User login
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              format: email
              example: user@example.com
            password:
              type: string
              format: password
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                email:
                  type: string
            token:
              type: string
              description: JWT authentication token
      400:
        description: Missing credentials
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    
    # Validate input
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password required"}), 400
        
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Generate token
    token = generate_token(user.id, user.email)
    
    return jsonify({
        "status": "success",
        "user": {
            "id": user.id,
            "email": user.email
        },
        "token": token
    }), 200


# Password Reset Routes
@api.route('/api/auth/password-reset/request', methods=['POST'])
def request_password_reset():
    """
    Request password reset via email
    ---
    tags:
      - Authentication
    summary: Request a password reset token
    description: |
      Send a password reset email to the user if the email exists in the system.
      For security reasons, the response will be the same whether the email exists or not.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              format: email
              description: Email address of the user requesting password reset
              example: user@example.com
    responses:
      200:
        description: Password reset request processed
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: If an account with this email exists, you will receive a password reset link.
      400:
        description: Invalid request data
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: Email is required
      429:
        description: Rate limit exceeded
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: Too many password reset requests. Please wait before trying again.
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: An error occurred. Please try again later.
    """
    from app.services.password_reset_service import password_reset_service
    
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'email' not in data:
            return jsonify({
                "status": "error",
                "message": "Email is required"
            }), 400
        
        email = data['email'].strip()
        if not email:
            return jsonify({
                "status": "error",
                "message": "Email is required"
            }), 400
        
        # Process password reset request
        result = password_reset_service.request_password_reset(email)
        
        if result.rate_limited:
            return jsonify({
                "status": "error",
                "message": result.message
            }), 429
        
        if not result.success and result.error_code == "EMAIL_SEND_FAILED":
            return jsonify({
                "status": "error",
                "message": result.message
            }), 500
        
        # Always return success response for security
        return jsonify({
            "status": "success",
            "message": result.message
        }), 200
        
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"Password reset request error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An error occurred. Please try again later."
        }), 500


@api.route('/api/auth/password-reset/verify', methods=['POST'])
def verify_password_reset():
    """
    Reset password using a valid token
    ---
    tags:
      - Authentication
    summary: Reset user password with token
    description: |
      Reset the user's password using a valid password reset token.
      The token will be invalidated after successful password reset.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - token
            - password
          properties:
            token:
              type: string
              description: Password reset token received via email
              example: abc123def456
            password:
              type: string
              format: password
              description: New password (minimum 8 characters)
              example: newPassword123
    responses:
      200:
        description: Password reset successful
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Password has been reset successfully.
      400:
        description: Invalid request data or weak password
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: Password must be at least 8 characters long.
      401:
        description: Invalid or expired token
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: Invalid or expired token.
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: An error occurred during password reset.
    """
    from app.services.password_reset_service import password_reset_service
    
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'token' not in data or 'password' not in data:
            return jsonify({
                "status": "error",
                "message": "Token and password are required"
            }), 400
        
        token = data['token'].strip()
        password = data['password']
        
        if not token or not password:
            return jsonify({
                "status": "error",
                "message": "Token and password are required"
            }), 400
        
        # Process password reset
        result = password_reset_service.reset_password(token, password)
        
        if result.error_code == "INVALID_TOKEN":
            return jsonify({
                "status": "error",
                "message": result.message
            }), 401
        
        if result.error_code == "WEAK_PASSWORD":
            return jsonify({
                "status": "error",
                "message": result.message
            }), 400
        
        if not result.success:
            return jsonify({
                "status": "error",
                "message": result.message
            }), 500
        
        return jsonify({
            "status": "success",
            "message": result.message
        }), 200
        
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"Password reset verify error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An error occurred during password reset."
        }), 500


@api.route('/api/auth/password-reset/validate', methods=['GET'])
def validate_password_reset_token():
    """
    Validate a password reset token
    ---
    tags:
      - Authentication
    summary: Check if a password reset token is valid
    description: |
      Validate a password reset token without consuming it.
      This can be used to check if a token is valid before showing the password reset form.
    parameters:
      - name: token
        in: query
        type: string
        required: true
        description: Password reset token to validate
        example: abc123def456
    responses:
      200:
        description: Token validation result
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Token is valid.
            valid:
              type: boolean
              example: true
            expires_at:
              type: string
              format: date-time
              example: 2024-11-03T09:00:00Z
      400:
        description: Missing token parameter
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: Token parameter is required
            valid:
              type: boolean
              example: false
      401:
        description: Invalid or expired token
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: Invalid or expired token.
            valid:
              type: boolean
              example: false
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: An error occurred during validation.
            valid:
              type: boolean
              example: false
    """
    from app.services.password_reset_service import password_reset_service
    
    try:
        token = request.args.get('token')
        
        if not token:
            return jsonify({
                "status": "error",
                "message": "Token parameter is required",
                "valid": False
            }), 400
        
        # Validate token
        result = password_reset_service.validate_reset_token(token)
        
        if result.error_code == "INVALID_TOKEN":
            return jsonify({
                "status": "error",
                "message": result.message,
                "valid": False
            }), 401
        
        if not result.success:
            return jsonify({
                "status": "error",
                "message": result.message,
                "valid": False
            }), 500
        
        return jsonify({
            "status": "success",
            "message": result.message,
            "valid": True,
            "expires_at": result.expires_at.isoformat() if result.expires_at else None
        }), 200
        
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"Password reset validate error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An error occurred during validation.",
            "valid": False
        }), 500


# Google OAuth Routes
@api.route('/auth/google', methods=['GET'])
def google_auth():
    """
    Initiate Google OAuth flow for Google Docs/Drive integration
    ---
    tags:
      - Google Authentication
    parameters:
      - name: user_id
        in: query
        type: integer
        description: User ID for authentication (testing only)
        example: 1
    responses:
      302:
        description: Redirect to Google OAuth authorization URL
      400:
        description: Missing user ID or invalid parameters
      500:
        description: Server error during OAuth initiation
    """
    try:
        # Get user_id from query parameter (for testing) or from token (for production)
        user_id = request.args.get('user_id')
        
        # Handle string "None" and empty values
        if user_id == 'None' or user_id == '' or user_id is None:
            user_id = None
        
        if not user_id:
            # Try to get from authentication token if provided
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                try:
                    from app.utils.jwt_utils import decode_token
                    token = auth_header.split(' ')[1]
                    payload = decode_token(token)
                    user_id = payload.get('user_id')
                except Exception:
                    pass
        
        if not user_id:
            # For tests that don't provide user_id, use a default test user
            if current_app.config.get('TESTING'):
                user_id = 1  # Default test user ID
            else:
                return jsonify({"error": "User ID required"}), 400
        
        # Validate user_id can be converted to integer
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid user ID format"}), 400
        
        # Check if user exists and is an admin (admin-only restriction)
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Admin-only restriction for Google authentication
        if not user.is_admin:
            return jsonify({
                "error": "Google authentication is restricted to administrators only",
                "message": "Only administrators can connect Google Drive for file management"
            }), 403
                
        google_auth_service = GoogleAuthService()
        
        # Get authorization URL
        auth_url = google_auth_service.get_authorization_url(int(user_id))
        
        return redirect(auth_url)
        
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"Google OAuth initiation error: {str(e)}")
        return jsonify({"error": "Failed to initiate Google authentication"}), 500


@api.route('/auth/google/callback', methods=['GET'])
def google_auth_callback():
    """
    Handle Google OAuth callback and exchange code for tokens
    ---
    tags:
      - Google Authentication
    parameters:
      - name: code
        in: query
        type: string
        required: true
        description: Authorization code from Google
      - name: state
        in: query
        type: string
        description: State parameter for CSRF protection
    responses:
      200:
        description: Authentication successful
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Google authentication successful"
            user_id:
              type: integer
              example: 1
      400:
        description: Authentication failed or invalid parameters
      500:
        description: Server error during authentication
    """
    try:
        # Get authorization code and state from query parameters
        authorization_code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return jsonify({"error": f"Google OAuth error: {error}"}), 400
            
        if not authorization_code:
            return jsonify({"error": "Missing authorization code"}), 400
            
        google_auth_service = GoogleAuthService()
        
        # Handle the callback
        success, message, google_auth = google_auth_service.handle_callback(
            authorization_code, state
        )
        
        if success:
            return jsonify({
                "status": "success",
                "message": message,
                "google_user": {
                    "email": google_auth.email,
                    "name": google_auth.name,
                    "picture": google_auth.picture
                }
            }), 200
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"Google OAuth callback error: {str(e)}")
        return jsonify({"error": "Failed to process Google authentication"}), 500


@api.route('/auth/google/status', methods=['GET'])
@swag_from({
    'tags': ['Google Integration'],
    'summary': 'Check Google authentication status',
    'description': 'Check if the user has authenticated with Google and can access Google services',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Authentication status retrieved',
            'schema': {
                'type': 'object',
                'properties': {
                    'authenticated': {'type': 'boolean'},
                    'email': {'type': 'string', 'description': 'Google account email (if authenticated)'},
                    'scopes': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Granted Google API scopes'
                    }
                }
            }
        },
        401: {
            'description': 'Unauthorized',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Internal server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
@token_required
def google_auth_status():
    """Check Google authentication status"""
    try:
        user_id = request.user.get('user_id')
        google_auth_service = GoogleAuthService()
        
        is_authenticated = google_auth_service.is_authenticated(user_id)
        
        if is_authenticated:
            # Get user's Google auth info
            from app.models.temp import GoogleAuth
            google_auth = GoogleAuth.query.filter_by(user_id=user_id).first()
            
            # Include persistence information
            persistence_info = {}
            if hasattr(google_auth, 'is_persistent'):
                persistence_info = {
                    'is_persistent': google_auth.is_persistent,
                    'auto_refresh_enabled': getattr(google_auth, 'auto_refresh_enabled', True),
                    'session_id': getattr(google_auth, 'persistent_session_id', None),
                    'last_activity': getattr(google_auth, 'last_activity_at', None),
                    'token_expires_at': google_auth.token_expires_at.isoformat() if google_auth.token_expires_at else None
                }
            
            return jsonify({
                "authenticated": True,
                "google_user": {
                    "email": google_auth.email,
                    "name": google_auth.name,
                    "picture": google_auth.picture
                },
                "persistence": persistence_info
            }), 200
        else:
            return jsonify({"authenticated": False}), 200
            
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"Google auth status error: {str(e)}")
        return jsonify({"error": "Failed to check authentication status"}), 500


@api.route('/auth/google/revoke', methods=['POST'])
@swag_from({
    'tags': ['Google Integration'],
    'summary': 'Revoke Google authentication',
    'description': 'Revoke user\'s Google authentication and remove stored credentials',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Google authentication revoked successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'}
                }
            }
        },
        401: {
            'description': 'Unauthorized',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Internal server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
@token_required
def google_auth_revoke():
    """Revoke Google authentication"""
    try:
        user_id = request.user.get('user_id')
        google_auth_service = GoogleAuthService()
        
        success = google_auth_service.revoke_authentication(user_id)
        
        if success:
            return jsonify({"message": "Google authentication revoked successfully"}), 200
        else:
            return jsonify({"error": "Failed to revoke authentication"}), 500
            
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"Google auth revoke error: {str(e)}")
        return jsonify({"error": "Failed to revoke authentication"}), 500


@api.route('/auth/google/store', methods=['POST'])
@swag_from({
    'tags': ['Google Integration'],
    'summary': 'Store Google authentication tokens manually',
    'description': 'Manually store Google OAuth tokens for a user account',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['access_token'],
                'properties': {
                    'access_token': {
                        'type': 'string',
                        'description': 'Google OAuth access token'
                    },
                    'refresh_token': {
                        'type': 'string',
                        'description': 'Google OAuth refresh token'
                    },
                    'scope': {
                        'type': 'string',
                        'description': 'OAuth scope permissions'
                    },
                    'expires_at': {
                        'type': 'string',
                        'format': 'date-time',
                        'description': 'Token expiration timestamp'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Tokens stored successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'stored_at': {'type': 'string', 'format': 'date-time'}
                }
            }
        },
        400: {
            'description': 'Bad request',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        401: {
            'description': 'Unauthorized',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Failed to store tokens',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
@token_required
def google_auth_store():
    """Store Google authentication tokens manually"""
    try:
        user_id = request.user.get('user_id')
        data = request.get_json()
        
        if not data or 'access_token' not in data:
            return jsonify({"error": "Missing access token"}), 400
        
        google_auth_service = GoogleAuthService()
        
        # Store tokens in database
        success = google_auth_service.store_tokens(
            user_id,
            data['access_token'],
            data.get('refresh_token'),
            data.get('expires_in', 3600)
        )
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Google authentication tokens stored successfully"
            }), 200
        else:
            return jsonify({"error": "Failed to store tokens"}), 500
            
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"Google auth store error: {str(e)}")
        return jsonify({"error": "Failed to store authentication tokens"}), 500


@api.route('/auth/google/refresh', methods=['POST'])
@swag_from({
    'tags': ['Google Integration'],
    'summary': 'Refresh Google authentication tokens',
    'description': 'Refresh expired Google authentication tokens to maintain access to Google services',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Tokens refreshed successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'expires_at': {'type': 'string', 'format': 'date-time'}
                }
            }
        },
        401: {
            'description': 'Unauthorized',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Failed to refresh tokens',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
@token_required  
def google_auth_refresh():
    """Refresh expired Google authentication tokens"""
    try:
        user_id = request.user.get('user_id')
        google_auth_service = GoogleAuthService()
        
        # Refresh tokens
        success = google_auth_service.refresh_tokens(user_id)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Google authentication tokens refreshed successfully"
            }), 200
        else:
            return jsonify({"error": "Failed to refresh tokens"}), 401
            
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"Google auth refresh error: {str(e)}")
        return jsonify({"error": "Failed to refresh authentication tokens"}), 500


# OAuth Persistence Enhanced Endpoints

@api.route('/api/auth/google/status', methods=['GET'])
@swag_from({
    'tags': ['OAuth Persistence'],
    'summary': 'Get basic OAuth authentication status',
    'description': 'Get basic OAuth authentication status for current user',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'OAuth status retrieved',
            'schema': {
                'type': 'object',
                'properties': {
                    'authenticated': {'type': 'boolean'},
                    'user_email': {'type': 'string'},
                    'status': {'type': 'string', 'enum': ['active', 'inactive', 'expired']},
                    'persistent_auth_enabled': {'type': 'boolean'}
                }
            }
        },
        401: {'description': 'Authentication required'},
        500: {'description': 'Internal server error'}
    }
})
@token_required
def get_basic_oauth_status():
    """Get basic OAuth authentication status"""
    try:
        from app.models.temp import GoogleAuth
        
        user_id = request.user.get('user_id')
        
        # Get Google auth record
        auth = GoogleAuth.query.filter_by(id=user_id, is_active=True).first()
        
        if not auth:
            return jsonify({
                'authenticated': False,
                'status': 'inactive',
                'user_email': None,
                'persistent_auth_enabled': False
            }), 200
        
        # Check if session is expired
        now = datetime.utcnow()
        is_expired = auth.session_expires_at and auth.session_expires_at < now
        
        status = 'expired' if is_expired else ('active' if auth.is_active else 'inactive')
        
        return jsonify({
            'authenticated': auth.is_active and not is_expired,
            'status': status,
            'user_email': auth.email,
            'persistent_auth_enabled': getattr(auth, 'persistent_auth_enabled', False)
        }), 200
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Basic OAuth status error: {str(e)}")
        return jsonify({
            'authenticated': False,
            'status': 'error',
            'error': 'Failed to retrieve OAuth status'
        }), 500


@api.route('/api/auth/google/status/detailed', methods=['GET'])
@swag_from({
    'tags': ['OAuth Persistence'],
    'summary': 'Get detailed OAuth persistence status',
    'description': 'Get comprehensive OAuth authentication status including persistence and storage information',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Detailed OAuth status retrieved',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'oauth_status': {
                        'type': 'object',
                        'properties': {
                            'is_authenticated': {'type': 'boolean'},
                            'is_persistent': {'type': 'boolean'},
                            'session_id': {'type': 'string'},
                            'token_expires_at': {'type': 'string'},
                            'last_refresh_at': {'type': 'string'},
                            'auto_refresh_enabled': {'type': 'boolean'},
                            'is_active': {'type': 'boolean'}
                        }
                    },
                    'storage_status': {
                        'type': 'object',
                        'properties': {
                            'quota_total': {'type': 'integer'},
                            'quota_used': {'type': 'integer'},
                            'usage_percentage': {'type': 'number'},
                            'warning_level': {'type': 'string'},
                            'last_check': {'type': 'string'}
                        }
                    }
                }
            }
        },
        401: {'description': 'Unauthorized'},
        403: {'description': 'Admin access required'},
        500: {'description': 'Internal server error'}
    }
})
@token_required
def get_detailed_oauth_status():
    """Get detailed OAuth persistence status for admin users"""
    try:
        from app.services.oauth_persistence_service import oauth_persistence_service
        from app.models.temp import User, GoogleAuth
        
        user_id = request.user.get('user_id')
        
        # Verify admin privileges
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required for detailed OAuth status'
            }), 403
        
        # Get OAuth authentication record
        auth = GoogleAuth.query.filter_by(user_id=user_id).first()
        if not auth:
            return jsonify({
                'success': True,
                'oauth_status': {
                    'is_authenticated': False,
                    'is_persistent': False,
                    'session_id': None,
                    'token_expires_at': None,
                    'auto_refresh_enabled': False,
                    'is_active': False
                },
                'storage_status': {
                    'quota_total': None,
                    'quota_used': None,
                    'usage_percentage': 0.0,
                    'warning_level': 'none',
                    'last_check': None
                }
            }), 200
        
        # Get comprehensive session status
        session_status = oauth_persistence_service.get_session_status(auth.id)
        
        # Check storage quota
        quota_info = oauth_persistence_service.check_storage_quota(auth.id)
        
        return jsonify({
            'success': True,
            'oauth_status': {
                'is_authenticated': auth.is_active,
                'is_persistent': getattr(auth, 'is_persistent', True),
                'session_id': getattr(auth, 'persistent_session_id', None),
                'token_expires_at': auth.token_expires_at.isoformat() if auth.token_expires_at else None,
                'last_refresh_at': getattr(auth, 'last_refresh_at', None),
                'auto_refresh_enabled': getattr(auth, 'auto_refresh_enabled', True),
                'is_active': auth.is_active
            },
            'storage_status': {
                'quota_total': quota_info.total_quota if quota_info else None,
                'quota_used': quota_info.used_quota if quota_info else None,
                'usage_percentage': quota_info.usage_percentage if quota_info else 0.0,
                'warning_level': quota_info.warning_level if quota_info else 'none',
                'last_check': quota_info.last_check.isoformat() if quota_info and quota_info.last_check else None,
                'formatted_quota': {
                    'total': f"{quota_info.total_quota / (1024**3):.1f} GB" if quota_info and quota_info.total_quota else None,
                    'used': f"{quota_info.used_quota / (1024**3):.1f} GB" if quota_info and quota_info.used_quota else None,
                    'available': f"{(quota_info.total_quota - quota_info.used_quota) / (1024**3):.1f} GB" if quota_info and quota_info.total_quota and quota_info.used_quota else None
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"Detailed OAuth status error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve detailed OAuth status'
        }), 500


@api.route('/api/auth/google/storage/analytics', methods=['GET'])
@swag_from({
    'tags': ['OAuth Persistence'],
    'summary': 'Get Google Drive storage analytics',
    'description': 'Get detailed storage usage analytics and cleanup recommendations',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Storage analytics retrieved',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'analytics': {
                        'type': 'object',
                        'properties': {
                            'usage_by_type': {'type': 'object'},
                            'large_files': {'type': 'array'},
                            'recommendations': {'type': 'array'},
                            'projected_full_date': {'type': 'string'}
                        }
                    }
                }
            }
        },
        401: {'description': 'Unauthorized'},
        403: {'description': 'Admin access required'},
        500: {'description': 'Internal server error'}
    }
})
@token_required
def get_storage_analytics():
    """Get Google Drive storage analytics for admin users"""
    try:
        from app.models.temp import User, GoogleAuth
        
        user_id = request.user.get('user_id')
        
        # Verify admin privileges
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required for storage analytics'
            }), 403
        
        # Get OAuth authentication record
        auth = GoogleAuth.query.filter_by(user_id=user_id).first()
        if not auth or not auth.is_active:
            return jsonify({
                'success': False,
                'error': 'Active Google authentication required'
            }), 401
        
        # For now, return basic analytics
        # In a full implementation, this would analyze Google Drive files
        current_usage = getattr(auth, 'drive_quota_used', 0) or 0
        total_quota = getattr(auth, 'drive_quota_total', 0) or 0
        usage_percentage = (current_usage / total_quota * 100) if total_quota > 0 else 0
        
        # Generate recommendations based on usage
        recommendations = []
        if usage_percentage > 90:
            recommendations.extend([
                "Urgent: Delete unnecessary files immediately",
                "Archive old files to free up space",
                "Consider upgrading Google Drive storage plan"
            ])
        elif usage_percentage > 80:
            recommendations.extend([
                "Consider archiving files older than 1 year",
                "Review and delete duplicate files",
                "Compress large files to reduce storage usage"
            ])
        elif usage_percentage > 60:
            recommendations.append("Monitor storage usage regularly")
        
        return jsonify({
            'success': True,
            'analytics': {
                'current_usage': {
                    'bytes': current_usage,
                    'formatted': f"{current_usage / (1024**3):.2f} GB" if current_usage else "0 GB"
                },
                'total_quota': {
                    'bytes': total_quota,
                    'formatted': f"{total_quota / (1024**3):.1f} GB" if total_quota else "0 GB"
                },
                'usage_percentage': round(usage_percentage, 2),
                'warning_level': getattr(auth, 'quota_warning_level', 'none'),
                'recommendations': recommendations,
                'last_check': getattr(auth, 'last_quota_check').isoformat() if hasattr(auth, 'last_quota_check') and auth.last_quota_check else None,
                'storage_trend': 'stable'  # Could be calculated from historical data
            }
        }), 200
        
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"Storage analytics error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve storage analytics'
        }), 500


@api.route('/api/auth/google/revoke/persistent', methods=['POST'])
@swag_from({
    'tags': ['OAuth Persistence'],
    'summary': 'Revoke persistent OAuth authentication',
    'description': 'Manually revoke persistent OAuth authentication and deactivate session',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'confirm_revocation': {'type': 'boolean', 'description': 'Confirmation flag'},
                    'reason': {'type': 'string', 'description': 'Reason for revocation'}
                },
                'required': ['confirm_revocation']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'OAuth authentication revoked successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'}
                }
            }
        },
        400: {'description': 'Invalid request'},
        401: {'description': 'Unauthorized'},
        403: {'description': 'Admin access required'},
        500: {'description': 'Internal server error'}
    }
})
@token_required
def revoke_persistent_oauth():
    """Revoke persistent OAuth authentication for admin users"""
    try:
        from app.services.oauth_persistence_service import oauth_persistence_service
        from app.models.temp import User, GoogleAuth
        
        user_id = request.user.get('user_id')
        
        # Verify admin privileges
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required for OAuth revocation'
            }), 403
        
        # Parse request data
        data = request.get_json()
        if not data or not data.get('confirm_revocation'):
            return jsonify({
                'success': False,
                'error': 'Revocation requires confirmation'
            }), 400
        
        reason = data.get('reason', 'Manual admin revocation')
        
        # Get OAuth authentication record
        auth = GoogleAuth.query.filter_by(user_id=user_id).first()
        if not auth:
            return jsonify({
                'success': False,
                'error': 'No OAuth session found to revoke'
            }), 404
        
        # Deactivate the session
        success = oauth_persistence_service.deactivate_session(auth.id, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'OAuth authentication revoked successfully',
                'revoked_at': datetime.utcnow().isoformat(),
                'reason': reason
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to revoke OAuth authentication'
            }), 500
        
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"OAuth revocation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to revoke OAuth authentication'
        }), 500


@api.route('/api/auth/google/token/refresh', methods=['POST'])
@swag_from({
    'tags': ['OAuth Persistence'],
    'summary': 'Force refresh OAuth tokens',
    'description': 'Manually trigger OAuth token refresh for testing or immediate refresh',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Token refresh completed',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'token_expires_at': {'type': 'string'},
                    'refresh_attempts': {'type': 'integer'}
                }
            }
        },
        401: {'description': 'Unauthorized'},
        403: {'description': 'Admin access required'},
        500: {'description': 'Internal server error'}
    }
})
@token_required
def force_token_refresh():
    """Force refresh OAuth tokens for admin users"""
    try:
        from app.services.oauth_persistence_service import oauth_persistence_service
        from app.models.temp import User, GoogleAuth
        
        user_id = request.user.get('user_id')
        
        # Verify admin privileges
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required for token refresh'
            }), 403
        
        # Get OAuth authentication record
        auth = GoogleAuth.query.filter_by(user_id=user_id).first()
        if not auth:
            return jsonify({
                'success': False,
                'error': 'No OAuth session found'
            }), 404
        
        # Force token refresh
        refresh_result = oauth_persistence_service.refresh_token_if_needed(auth.id)
        
        return jsonify({
            'success': refresh_result.success,
            'message': refresh_result.message,
            'token_expires_at': refresh_result.new_expires_at.isoformat() if refresh_result.new_expires_at else None,
            'refresh_attempts': refresh_result.refresh_attempts,
            'error_code': refresh_result.error_code
        }), 200 if refresh_result.success else 500
        
    except Exception as e:
        current_app.logging.getLogger(__name__).error(f"Force token refresh error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to refresh tokens'
        }), 500


@api.route('/api/save_resume', methods=['PUT'])
@token_required
def save_resume():
    """
    Save or update a resume for the authenticated user
    ---
    tags:
      - Resume Management
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - updated_resume
            - resume_title
          properties:
            updated_resume:
              type: object
              description: Complete resume data structure
            resume_title:
              type: string
              description: Title for the resume
              example: "Software Engineer Resume"
    responses:
      200:
        description: Resume saved successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Resume saved successfully"
            resume_id:
              type: integer
              example: 1
      400:
        description: Missing required data
      401:
        description: Unauthorized - Invalid or missing token
      500:
        description: Server error during save operation
    """
    # Get user ID from token
    user_id = request.user.get('user_id')
    
    # Get and validate JSON data
    data = request.get_json()
    if not data or 'updated_resume' not in data:
        return jsonify({"error": "Missing resume data"}), 400
        
    # Get resume title from root level
    resume_title = data.get('resume_title')
    if not resume_title:
        return jsonify({"error": "Resume title is required"}), 400
    
    # Get template ID (required field)
    # template = data.get('template')
    # if template is None:
    #     return jsonify({"error": "Template ID is required"}), 400
    
    resume_data = data['updated_resume']
    
    try:
        # Check if resume with same title exists for this user
        existing_resume = Resume.query.filter_by(
            user_id=user_id,
            title=resume_title
        ).first()
        
        if existing_resume:
            # Update existing resume
            existing_resume.parsed_resume = resume_data
            # existing_resume.template = template
            existing_resume.template_id = 1
            db.session.commit()
        else:
            # Create new resume entry
            # Get the next serial number for this user
            existing_count = Resume.query.filter_by(user_id=user_id).count()
            now = datetime.utcnow()  # Using standard utcnow() method
            
            resume = Resume(
                user_id=user_id,
                serial_number=existing_count + 1,  # Increment from existing count
                title=resume_title,
                parsed_resume=resume_data,
                # template=template,
                template_id=1,
                updated_at=now,
                created_at=now
            )
            db.session.add(resume)
            db.session.commit()
        
        return jsonify({
            "status": 200,
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to save resume",
            "details": str(e)
        }), 500

@api.route('/api/get_resume_list', methods=['GET'])
@token_required
def get_resume_list():
    """
    Get list of all resumes for the authenticated user
    ---
    tags:
      - Resume Management
    security:
      - Bearer: []
    responses:
      200:
        description: Resume list retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            data:
              type: array
              items:
                type: object
                properties:
                  resume_id:
                    type: integer
                    description: Unique resume identifier
                    example: 1
                  resume_title:
                    type: string
                    description: Resume title
                    example: "Software Engineer Resume"
                  created_at:
                    type: string
                    format: date-time
                    description: Creation timestamp
                    example: "2025-10-16T12:00:00"
      401:
        description: Unauthorized - Invalid or missing token
      500:
        description: Server error during retrieval
    """
    user_id = request.user.get('user_id')
    
    try:
        # Query resumes for this user
        resumes = Resume.query.filter_by(user_id=user_id).all()
        
        # Format response
        resume_list = [{
            "resume_id": resume.serial_number,
            "resume_title": resume.title,
            "created_at": resume.created_at.isoformat()
        } for resume in resumes]
        
        return jsonify({
            "status": 200,
            "data": resume_list
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to fetch resume list",
            "details": str(e)
        }), 500

@api.route('/api/get_resume/<int:resume_id>', methods=['GET'])
@token_required
def get_resume(resume_id):
    """
    Get a specific resume by ID for the authenticated user
    ---
    tags:
      - Resume Management
    security:
      - Bearer: []
    parameters:
      - name: resume_id
        in: path
        type: integer
        required: true
        description: Resume ID to retrieve
        example: 1
    responses:
      200:
        description: Resume retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            data:
              type: object
              properties:
                resume_id:
                  type: integer
                  example: 1
                resume_title:
                  type: string
                  example: "Software Engineer Resume"
                parsed_resume:
                  type: object
                  description: Complete resume data structure
                created_at:
                  type: string
                  format: date-time
      404:
        description: Resume not found
      401:
        description: Unauthorized - Invalid or missing token
      500:
        description: Server error during retrieval
    """
    user_id = request.user.get('user_id')
    
    try:
        # Query resume and verify ownership
        resume = Resume.query.filter_by(
            serial_number=resume_id,
            user_id=user_id
        ).first()
        
        if not resume:
            return jsonify({
                "error": "Resume not found or access denied"
            }), 404
        
        return jsonify({
            "status": 200,
            "data": {
                "resume": resume.parsed_resume,
                "resume_title": resume.title
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to fetch resume",
            "details": str(e)
        }), 500

@api.route('/api/put_profile', methods=['PUT'])
@swag_from({
    'tags': ['User Management'],
    'summary': 'Update user profile',
    'description': 'Update user profile information including name, email, location, and bio',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'first_name': {
                        'type': 'string',
                        'description': 'User first name'
                    },
                    'last_name': {
                        'type': 'string',
                        'description': 'User last name'
                    },
                    'email': {
                        'type': 'string',
                        'format': 'email',
                        'description': 'User email address'
                    },
                    'city': {
                        'type': 'string',
                        'description': 'User city'
                    },
                    'country': {
                        'type': 'string',
                        'description': 'User country'
                    },
                    'bio': {
                        'type': 'string',
                        'description': 'User biography'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Profile updated successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'profile': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'first_name': {'type': 'string'},
                            'last_name': {'type': 'string'},
                            'email': {'type': 'string'},
                            'city': {'type': 'string'},
                            'country': {'type': 'string'},
                            'bio': {'type': 'string'}
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad request',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        401: {
            'description': 'Unauthorized',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'User not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
@token_required
def put_profile():
    """Update user profile"""
    user_id = request.user.get('user_id')
    
    # Validate request data
    valid, message, status_code = ProfileValidator.validate_profile_data(
        request.get_json(), 
        user_id
    )
    if not valid:
        return jsonify({"error": message}), status_code
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Update allowed fields
        fields = ['first_name', 'last_name', 'email', 'city', 'country', 'bio']
        for field in fields:
            if field in message:  # message contains validated data
                setattr(user, field, message[field])
            
        db.session.commit()
        return jsonify({
            "status": 200,
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to update profile",
            "details": str(e)
        }), 500
    

@api.route('/api/get_profile', methods=['GET'])
@token_required
def get_profile():
    """
    Get user profile information
    ---
    tags:
      - User Profile
    security:
      - Bearer: []
    responses:
      200:
        description: User profile retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            data:
              type: object
              properties:
                profile:
                  type: object
                  properties:
                    first_name:
                      type: string
                      example: "John"
                    last_name:
                      type: string
                      example: "Doe"
                    email:
                      type: string
                      example: "john@example.com"
                    city:
                      type: string
                      example: "New York"
                    country:
                      type: string
                      example: "USA"
                    bio:
                      type: string
                      example: "Software Engineer"
      404:
        description: User not found
      401:
        description: Unauthorized - Invalid or missing token
    """
    user_id = request.user.get('user_id')
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "status": 200,
            "data": {
                "profile": {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "city": user.city,
                    "country": user.country,
                    "bio": user.bio
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to fetch profile",
            "details": str(e)
        }), 500

@api.route('/api/resume/score', methods=['POST'])
def score_resume():
    """
    Score resume with AI-powered analysis
    ---
    tags:
      - Resume Scoring
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - resume
          properties:
            resume:
              type: object
              description: Parsed resume data structure
            job_description:
              type: string
              description: Optional job description to score against
    responses:
      200:
        description: Resume scored successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            data:
              type: object
              properties:
                overall_score:
                  type: number
                  example: 85.5
                scores:
                  type: object
                  properties:
                    keyword_matching:
                      type: object
                      properties:
                        score:
                          type: number
                        weight:
                          type: number
                        details:
                          type: object
                    language_expression:
                      type: object
                      properties:
                        score:
                          type: number
                        weight:
                          type: number
                        details:
                          type: object
                    ats_readability:
                      type: object
                      properties:
                        score:
                          type: number
                        weight:
                          type: number
                        details:
                          type: object
                recommendations:
                  type: array
                  items:
                    type: string
                strengths:
                  type: array
                  items:
                    type: string
                weaknesses:
                  type: array
                  items:
                    type: string
      400:
        description: Invalid request data
      500:
        description: Scoring failed
    """
    data = request.get_json()
    
    # Validate input
    if not data or 'resume' not in data:
        return jsonify({"error": "Resume data is required"}), 400
    
    try:
        # Get optional job description
        job_description = data.get('job_description', '')
        
        # Create ResumeAI instance with existing parsed resume
        resume_processor = ResumeAI("")
        resume_processor.parsed_resume = data['resume']
        
        # Score the resume
        scoring_result = resume_processor.score_resume(job_description)
        
        return jsonify({
            "status": 200,
            "data": scoring_result
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to score resume",
            "details": str(e)
        }), 500


# ===== GOOGLE DOCS EXPORT ENDPOINTS =====

@api.route('/api/resume/export/gdocs', methods=['POST'])
@swag_from({
    'tags': ['Document Export'],
    'summary': 'Export resume to Google Docs',
    'description': 'Export a resume to Google Docs using a specified template',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['resume_id', 'template_id'],
                'properties': {
                    'resume_id': {
                        'type': 'integer',
                        'description': 'Resume ID to export'
                    },
                    'template_id': {
                        'type': 'integer',
                        'description': 'Template ID to apply'
                    },
                    'document_title': {
                        'type': 'string',
                        'description': 'Optional document title'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Resume exported successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'document_id': {'type': 'string'},
                    'document_url': {'type': 'string'},
                    'message': {'type': 'string'}
                }
            }
        },
        400: {
            'description': 'Bad request',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        401: {
            'description': 'Unauthorized',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        403: {
            'description': 'Google authentication required',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'Resume or template not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
@token_required
def export_resume_to_google_docs():
    """Export resume to Google Docs"""
    data = request.get_json()
    user_id = request.user.get('user_id')
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    # Validate input
    if not data or 'resume_id' not in data or 'template_id' not in data:
        return jsonify({"error": "resume_id and template_id are required"}), 400
    
    # Check if user has Google auth
    google_auth = GoogleAuth.query.filter_by(user_id=current_user.id).first()
    if not google_auth:
        return jsonify({"error": "google_auth_required"}), 401
    
    # Verify Google auth has required scopes
    required_scopes = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
    if not google_auth.scope or not all(scope in google_auth.scope for scope in required_scopes):
        return jsonify({"error": "insufficient_scope"}), 403
    
    try:
        # Get resume and template
        resume = Resume.query.filter_by(
            serial_number=data['resume_id'],
            user_id=current_user.id
        ).first()
        
        if not resume:
            return jsonify({"error": "resume_not_found"}), 404
        
        template = ResumeTemplate.query.get(data['template_id'])
        if not template:
            return jsonify({"error": "template_not_found"}), 404
        
        # Get Google credentials
        google_auth_service = GoogleAuthService()
        credentials = google_auth_service.get_credentials(current_user.id)
        
        # Create Google Docs document
        docs_service = GoogleDocsService()
        document_data = {
            'title': data.get('document_title', f"Resume - {resume.title}"),
            'content': resume.parsed_resume
        }
        
        doc_result = docs_service.create_document(document_data, credentials)
        
        # Apply template styling
        if template:
            docs_service.apply_template_styling(
                doc_result['document_id'], 
                template, 
                credentials
            )
        
        # Create shareable link
        drive_service = GoogleDriveService()
        share_result = drive_service.create_shareable_link(
            doc_result['document_id'], 
            credentials
        )
        
        # Track in database
        generated_doc = GeneratedDocument(
            user_id=current_user.id,
            resume_id=data['resume_id'],
            template_id=data['template_id'],
            google_doc_id=doc_result['document_id'],
            google_doc_url=share_result['shareable_url'],
            document_title=document_data['title'],
            generation_status='created',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(generated_doc)
        db.session.commit()
        
        return jsonify({
            "status": 200,
            "data": {
                "document_id": doc_result['document_id'],
                "shareable_url": share_result['shareable_url'],
                "generated_document_id": generated_doc.id
            }
        }), 200
        
    except HttpError as e:
        # Handle specific Google API errors
        if e.resp.status == 429:
            return jsonify({
                "error": "quota_exceeded",
                "message": "Google API quota exceeded"
            }), 429
        elif e.resp.status == 401:
            return jsonify({
                "error": "authentication_error", 
                "message": "Invalid Google credentials"
            }), 401
        elif e.resp.status == 403:
            return jsonify({
                "error": "permission_denied",
                "message": "Insufficient permissions"
            }), 403
        else:
            return jsonify({
                "error": "google_api_error",
                "message": f"Google API error: {e.resp.status}"
            }), e.resp.status
    except Exception as e:
        # Handle network errors
        import requests
        if isinstance(e, requests.exceptions.ConnectionError) or 'ConnectionError' in str(type(e)):
            return jsonify({
                "error": "network_error",
                "message": "Network connection failed"
            }), 503
        
        # Generic error fallback
        return jsonify({
            "error": "Failed to export to Google Docs",
            "details": str(e)
        }), 500


@api.route('/api/resume/generate', methods=['POST'])
@swag_from({
    'tags': ['Resume Processing'],
    'summary': 'Generate optimized resume content using AI',
    'description': 'Generate optimized resume content using AI based on user data and job description',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['resume_id', 'job_description_id'],
                'properties': {
                    'resume_id': {
                        'type': 'integer',
                        'description': 'Resume ID to optimize'
                    },
                    'job_description_id': {
                        'type': 'integer',
                        'description': 'Job description ID for optimization'
                    },
                    'template_id': {
                        'type': 'integer',
                        'description': 'Template ID to apply'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Resume generated successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'resume': {'type': 'object'},
                    'generated_content': {'type': 'object'}
                }
            }
        },
        400: {
            'description': 'Bad request',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        401: {
            'description': 'Unauthorized',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'Resume or job description not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
@token_required
def generate_resume():
    """
    Generate optimized resume content using AI based on user data and job description
    """
    data = request.get_json()
    user_id = request.user.get('user_id')
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    # Validate required fields - support both API formats
    if not data:
        return jsonify({
            "error": "Missing required_fields: user_data, job_description, template_id"
        }), 400
    
    # Check for new API format (resume_id, job_description_id) or legacy format (user_data, job_description, template_id)
    has_new_format = all(key in data for key in ['resume_id', 'job_description_id'])
    has_legacy_format = all(key in data for key in ['user_data', 'job_description', 'template_id'])
    
    if not has_new_format and not has_legacy_format:
        return jsonify({
            "error": "Missing required_fields: user_data, job_description, template_id or resume_id, job_description_id"
        }), 400
    
    try:
        # Initialize resume generator
        generator = ResumeGenerator()
        
        # Generate optimized content
        result = generator.generate_content(
            user_data=data['user_data'],
            job_description=data['job_description'],
            template_id=data['template_id']
        )
        
        return jsonify({
            "status": 200,
            "data": {
                "generated_resume": result.get('optimized_content', ''),
                "optimizations_applied": result.get('improvements', []),
                "ats_score": result.get('ats_score', 0),
                "keywords_matched": result.get('keywords_matched', []),
                "template_applied": result.get('template_applied', '')
            }
        }), 200
        
    except ValueError as e:
        # Check if it's a template not found error
        if "Template" in str(e) and "not found" in str(e):
            return jsonify({
                "error": "template_not_found",
                "details": str(e)
            }), 404
        
        return jsonify({
            "error": "Invalid request data",
            "details": str(e)
        }), 400
        
    except Exception as e:
        return jsonify({
            "error": "Failed to generate resume",
            "details": str(e)
        }), 500


@api.route('/api/resume/export/pdf/<document_id>', methods=['GET'])
@swag_from({
    'tags': ['Document Export'],
    'summary': 'Export Google Docs document as PDF',
    'description': 'Export a previously created Google Docs document as a PDF file',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'document_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'Google Docs document ID'
        }
    ],
    'responses': {
        200: {
            'description': 'PDF file',
            'schema': {
                'type': 'file'
            }
        },
        401: {
            'description': 'Unauthorized',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        403: {
            'description': 'Access denied',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'Document not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
@token_required
def export_google_docs_as_pdf(document_id):
    """
    Export Google Docs document as PDF
    """
    user_id = request.user.get('user_id')
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        # Check if user has access to this document
        generated_doc = GeneratedDocument.query.filter_by(
            google_doc_id=document_id,
            user_id=current_user.id
        ).first()
        
        if not generated_doc:
            return jsonify({"error": "document_not_found"}), 404
        
        # Get Google credentials
        google_auth_service = GoogleAuthService()
        credentials = google_auth_service.get_credentials(current_user.id)
        
        # Export as PDF
        drive_service = GoogleDriveService()
        pdf_result = drive_service.export_as_pdf(document_id, credentials)
        
        # Clean up temporary file if exists
        if pdf_result.get('temp_file_path'):
            try:
                os.remove(pdf_result['temp_file_path'])
            except:
                pass
        
        return send_file(
            io.BytesIO(pdf_result['pdf_content']),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=pdf_result['filename']
        )
        
    except Exception as e:
        return jsonify({
            "error": "Failed to export PDF",
            "details": str(e)
        }), 500


@api.route('/api/resume/export/docx/<document_id>', methods=['GET'])
@swag_from({
    'tags': ['Document Export'],
    'summary': 'Export Google Docs document as DOCX',
    'description': 'Export a previously created Google Docs document as a DOCX file',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'document_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'Google Docs document ID'
        }
    ],
    'responses': {
        200: {
            'description': 'DOCX file',
            'schema': {
                'type': 'file'
            }
        },
        401: {
            'description': 'Unauthorized',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        403: {
            'description': 'Access denied',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'Document not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
@token_required
def export_google_docs_as_docx(document_id):
    """
    Export Google Docs document as DOCX
    """
    user_id = request.user.get('user_id')
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        # Check if user has access to this document
        generated_doc = GeneratedDocument.query.filter_by(
            google_doc_id=document_id,
            user_id=current_user.id
        ).first()
        
        if not generated_doc:
            return jsonify({"error": "document_not_found"}), 404
        
        # Get Google credentials
        google_auth_service = GoogleAuthService()
        credentials = google_auth_service.get_credentials(current_user.id)
        
        # Export as DOCX
        drive_service = GoogleDriveService()
        docx_result = drive_service.export_as_docx(document_id, credentials)
        
        return send_file(
            io.BytesIO(docx_result['docx_content']),
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=docx_result['filename']
        )
        
    except Exception as e:
        return jsonify({
            "error": "Failed to export DOCX",
            "details": str(e)
        }), 500


@api.route('/api/documents', methods=['GET'])
@swag_from({
    'tags': ['Document Management'],
    'summary': 'List user generated documents',
    'description': 'Get list of all documents generated by the user',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'List of user documents',
            'schema': {
                'type': 'object',
                'properties': {
                    'documents': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'google_doc_id': {'type': 'string'},
                                'document_title': {'type': 'string'},
                                'shareable_url': {'type': 'string'},
                                'created_at': {'type': 'string', 'format': 'date-time'}
                            }
                        }
                    }
                }
            }
        },
        401: {
            'description': 'Unauthorized',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'User not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
@token_required
def list_user_generated_documents():
    """
    List user's generated documents
    """
    user_id = request.user.get('user_id')
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        documents = GeneratedDocument.query.filter_by(
            user_id=current_user.id
        ).order_by(GeneratedDocument.created_at.desc()).all()
        
        result = []
        for doc in documents:
            result.append({
                "id": doc.id,
                "document_title": doc.document_title,
                "google_doc_id": doc.google_doc_id,
                "google_doc_url": doc.google_doc_url,
                "resume_id": doc.resume_id,
                "template_id": doc.template_id,
                "generation_status": doc.generation_status,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat()
            })
        
        return jsonify({
            "status": 200,
            "data": result
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to list documents",
            "details": str(e)
        }), 500


@api.route('/api/documents/<int:document_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Document Management'],
    'summary': 'Delete a generated document',
    'description': 'Delete a generated document from both the database and Google Drive',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'document_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'ID of the document to delete'
        }
    ],
    'responses': {
        200: {
            'description': 'Document deleted successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'}
                }
            }
        },
        401: {
            'description': 'Unauthorized',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        403: {
            'description': 'Access denied',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'Document not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
@token_required
def delete_generated_document(document_id):
    """
    Delete a generated document
    """
    user_id = request.user.get('user_id')
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        # Find the document
        doc = GeneratedDocument.query.filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()
        
        if not doc:
            return jsonify({"error": "document_not_found"}), 404
        
        # Delete from Google Drive
        try:
            google_auth_service = GoogleAuthService()
            credentials = google_auth_service.get_credentials(current_user.id)
            
            drive_service = GoogleDriveService()
            drive_service.delete_document(doc.google_doc_id, credentials)
        except:
            # Continue even if Google deletion fails
            pass
        
        # Delete from database
        db.session.delete(doc)
        db.session.commit()
        
        return jsonify({
            "status": 200,
            "message": "Document deleted successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to delete document",
            "details": str(e)
        }), 500


@api.route('/api/documents/<int:document_id>/sharing', methods=['PUT'])
@swag_from({
    'tags': ['Document Management'],
    'summary': 'Update document sharing permissions',
    'description': 'Update sharing permissions for a generated Google Docs document',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'document_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'ID of the document to update sharing for'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['sharing_settings'],
                'properties': {
                    'sharing_settings': {
                        'type': 'object',
                        'properties': {
                            'type': {
                                'type': 'string',
                                'enum': ['user', 'domain', 'anyone'],
                                'description': 'Type of sharing permission'
                            },
                            'role': {
                                'type': 'string',
                                'enum': ['reader', 'writer', 'commenter'],
                                'description': 'Access role for the shared document'
                            },
                            'emailAddress': {
                                'type': 'string',
                                'description': 'Email address (required for user type)'
                            }
                        }
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Sharing settings updated successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'sharing_settings': {'type': 'object'}
                }
            }
        },
        400: {
            'description': 'Bad request',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        401: {
            'description': 'Unauthorized',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        403: {
            'description': 'Access denied',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'Document not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
@token_required
def update_document_sharing(document_id):
    """
    Update document sharing permissions
    """
    user_id = request.user.get('user_id')
    current_user = User.query.get(user_id)
    data = request.get_json()
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        # Find the document
        doc = GeneratedDocument.query.filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()
        
        if not doc:
            return jsonify({"error": "document_not_found"}), 404
        
        # Update Google Drive permissions
        google_auth_service = GoogleAuthService()
        credentials = google_auth_service.get_credentials(current_user.id)
        
        drive_service = GoogleDriveService()
        success = drive_service.update_permissions(
            doc.google_doc_id, 
            data, 
            credentials
        )
        
        return jsonify({
            "status": 200,
            "permissions_updated": success
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to update sharing",
            "details": str(e)
        }), 500


# =============================================================================
# STORAGE MONITORING API ENDPOINTS
# =============================================================================

@api.route('/api/storage/monitoring/status', methods=['GET'])
@token_required
def get_storage_monitoring_status():
    """
    Get status of the background storage monitoring service
    ---
    tags:
      - Storage Monitoring
    security:
      - Bearer: []
    description: |
      Get the current status of the background storage monitoring service,
      including configuration, statistics, and service health.
      
      **Admin Access Only**: This endpoint requires admin privileges.
    responses:
      200:
        description: Storage monitoring status retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            service_status:
              type: object
              properties:
                enabled:
                  type: boolean
                  example: true
                running:
                  type: boolean  
                  example: true
                check_interval_minutes:
                  type: integer
                  example: 60
                thread_alive:
                  type: boolean
                  example: true
                stats:
                  type: object
                  properties:
                    service_started:
                      type: string
                      format: datetime
                      example: "2024-11-25T10:30:00"
                    last_check:
                      type: string
                      format: datetime
                      example: "2024-11-25T11:30:00"
                    total_checks:
                      type: integer
                      example: 15
                    total_alerts_sent:
                      type: integer
                      example: 3
                    uptime_hours:
                      type: number
                      example: 2.5
      401:
        description: Authentication required
      403:
        description: Admin access required
      500:
        description: Server error
    """
    # Verify admin access
    try:
        # Get user from token and check admin status
        user = User.query.get(request.user.get('user_id'))
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        from app.services.background_storage_monitor import background_storage_monitor
        
        status = background_storage_monitor.get_status()
        
        return jsonify({
            'success': True,
            'service_status': status,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error getting storage monitoring status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/api/storage/monitoring/start', methods=['POST'])
@token_required
def start_storage_monitoring():
    """
    Start the background storage monitoring service
    ---
    tags:
      - Storage Monitoring
    security:
      - Bearer: []
    description: |
      Start the background storage monitoring service. The service will
      periodically check storage quotas for all active OAuth sessions
      and generate alerts when thresholds are exceeded.
      
      **Admin Access Only**: This endpoint requires admin privileges.
    responses:
      200:
        description: Storage monitoring service started successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Storage monitoring service started (checking every 60 minutes)"
            running:
              type: boolean
              example: true
            check_interval_minutes:
              type: integer
              example: 60
      400:
        description: Service already running or configuration issue
      401:
        description: Authentication required
      403:
        description: Admin access required
      500:
        description: Failed to start service
    """
    try:
        # Get user from token and check admin status
        user = User.query.get(request.user.get('user_id'))
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        from app.services.background_storage_monitor import background_storage_monitor
        
        result = background_storage_monitor.start()
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error starting storage monitoring: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/api/storage/monitoring/stop', methods=['POST'])
@token_required
def stop_storage_monitoring():
    """
    Stop the background storage monitoring service
    ---
    tags:
      - Storage Monitoring
    security:
      - Bearer: []
    description: |
      Stop the background storage monitoring service. This will halt
      all periodic storage checks and alert generation.
      
      **Admin Access Only**: This endpoint requires admin privileges.
    responses:
      200:
        description: Storage monitoring service stopped successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Storage monitoring service stopped"
            running:
              type: boolean
              example: false
            final_stats:
              type: object
              description: Final service statistics
      400:
        description: Service not running or stop failed
      401:
        description: Authentication required
      403:
        description: Admin access required
      500:
        description: Failed to stop service
    """
    try:
        # Get user from token and check admin status
        user = User.query.get(request.user.get('user_id'))
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        from app.services.background_storage_monitor import background_storage_monitor
        
        result = background_storage_monitor.stop()
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error stopping storage monitoring: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/api/storage/monitoring/check-now', methods=['POST'])
@token_required  
def force_storage_check():
    """
    Force an immediate storage check for all active OAuth sessions
    ---
    tags:
      - Storage Monitoring
    security:
      - Bearer: []
    description: |
      Trigger an immediate storage quota check for all active OAuth sessions,
      bypassing the normal scheduled interval. This will generate alerts
      if any sessions exceed storage thresholds.
      
      **Admin Access Only**: This endpoint requires admin privileges.
    responses:
      200:
        description: Storage check completed successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Checked storage for 3 sessions"
            sessions_checked:
              type: integer
              example: 3
            alerts_generated:
              type: integer
              example: 1
            results:
              type: array
              items:
                type: object
                properties:
                  auth_id:
                    type: integer
                    example: 1
                  user_id:
                    type: integer
                    example: 1
                  success:
                    type: boolean
                    example: true
                  quota:
                    type: object
                    properties:
                      usage_percentage:
                        type: number
                        example: 85.2
                      warning_level:
                        type: string
                        example: "medium"
            forced_check:
              type: boolean
              example: true
      401:
        description: Authentication required
      403:
        description: Admin access required
      500:
        description: Check failed
    """
    try:
        # Get user from token and check admin status
        user = User.query.get(request.user.get('user_id'))
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        from app.services.background_storage_monitor import background_storage_monitor
        
        result = background_storage_monitor.force_check_now()
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error during forced storage check: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'forced_check': True
        }), 500


@api.route('/api/storage/overview', methods=['GET'])
@token_required
def get_storage_overview():
    """
    Get storage overview for all active OAuth sessions
    ---
    tags:
      - Storage Monitoring
    security:
      - Bearer: []
    description: |
      Get a comprehensive overview of storage usage across all active
      OAuth sessions, including summary statistics and individual session details.
      
      **Admin Access Only**: This endpoint requires admin privileges.
    responses:
      200:
        description: Storage overview retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            summary:
              type: object
              properties:
                total_sessions:
                  type: integer
                  example: 5
                sessions_with_warnings:
                  type: integer
                  example: 2
                critical_sessions:
                  type: integer
                  example: 1
                total_storage_used_gb:
                  type: number
                  example: 85.5
                total_storage_quota_gb:
                  type: number
                  example: 375.0
                overall_usage_percentage:
                  type: number
                  example: 22.8
            sessions:
              type: array
              items:
                type: object
                properties:
                  auth_id:
                    type: integer
                    example: 1
                  user_id:
                    type: integer
                    example: 1
                  user_email:
                    type: string
                    example: "user@example.com"
                  usage_percentage:
                    type: number
                    example: 85.2
                  warning_level:
                    type: string
                    example: "medium"
                  last_check:
                    type: string
                    format: datetime
                    example: "2024-11-25T11:30:00"
      401:
        description: Authentication required
      403:
        description: Admin access required
      500:
        description: Failed to retrieve overview
    """
    try:
        # Get user from token and check admin status
        user = User.query.get(request.user.get('user_id'))
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        from app.services.storage_monitoring_service import storage_monitoring_service
        
        result = storage_monitoring_service.get_all_storage_status()
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error getting storage overview: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@api.route('/api/storage/monitoring/config', methods=['PUT'])
@token_required
def update_storage_monitoring_config():
    """
    Update storage monitoring service configuration
    ---
    tags:
      - Storage Monitoring
    security:
      - Bearer: []
    description: |
      Update the configuration of the background storage monitoring service,
      such as check interval and enable/disable status.
      
      **Admin Access Only**: This endpoint requires admin privileges.
    parameters:
      - in: body
        name: config
        required: true
        schema:
          type: object
          properties:
            check_interval_minutes:
              type: integer
              minimum: 5
              example: 120
              description: Check interval in minutes (minimum 5)
            enabled:
              type: boolean
              example: true
              description: Enable or disable the monitoring service
    responses:
      200:
        description: Configuration updated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Configuration updated"
            old_config:
              type: object
              description: Previous configuration
            new_config:
              type: object
              description: Updated configuration
            needs_restart:
              type: boolean
              example: true
            restart_result:
              type: object
              description: Result of automatic restart if needed
      400:
        description: Invalid configuration
      401:
        description: Authentication required
      403:
        description: Admin access required
      500:
        description: Configuration update failed
    """
    try:
        # Get user from token and check admin status
        user = User.query.get(request.user.get('user_id'))
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No configuration data provided'
            }), 400
        
        from app.services.background_storage_monitor import background_storage_monitor
        
        result = background_storage_monitor.update_config(
            check_interval_minutes=data.get('check_interval_minutes'),
            enabled=data.get('enabled')
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error updating storage monitoring config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# GOOGLE OAUTH ADMIN AUTHENTICATION ROUTES (API-12, API-12a)
# =============================================================================

@api.route('/auth/google/admin', methods=['GET'])
@token_required
def initiate_admin_google_auth():
    """
    Initiate Google OAuth for admin user (API-12)
    ---
    tags:
      - Google Authentication
    security:
      - Bearer: []
    description: |
      Initiate Google OAuth 2.0 authentication flow for admin users to enable
      Google Drive integration. This endpoint is restricted to admin users only
      and implements API-12 from the functional specifications.
      
      **Admin Access Only**: Only users with admin privileges can authenticate with Google.
      
      The OAuth flow provides persistent authentication per API-12a requirements,
      eliminating the need for repeated authentication.
    responses:
      200:
        description: OAuth flow initiated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            authorization_url:
              type: string
              example: "https://accounts.google.com/o/oauth2/auth?..."
              description: URL to visit for Google authentication
            message:
              type: string
              example: "Please visit the authorization URL to complete Google authentication"
            session_info:
              type: object
              properties:
                initiated_at:
                  type: string
                  format: date-time
                expires_in:
                  type: integer
                  example: 600
                  description: Session expires in seconds
      401:
        description: Authentication required
      403:
        description: Admin privileges required for Google Drive authentication
      500:
        description: Failed to initiate Google authentication
    """
    try:
        current_user_id = request.user['user_id']
        
        # Check if user is admin
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Admin privileges required for Google Drive authentication',
                'error_code': 'ADMIN_REQUIRED'
            }), 403
        
        from app.services.google_admin_auth_fixed import GoogleAdminAuthServiceFixed
        auth_service = GoogleAdminAuthServiceFixed()
        authorization_url = auth_service.initiate_admin_oauth_flow(current_user_id)
        
        return jsonify({
            'success': True,
            'authorization_url': authorization_url,
            'message': 'Please visit the authorization URL to complete Google authentication',
            'instructions': [
                '1. Click the authorization URL to open Google OAuth page',
                '2. Sign in with your Google account',
                '3. Grant permissions for Google Drive and Docs access',
                '4. You will be redirected back to complete authentication'
            ],
            'session_info': {
                'initiated_at': datetime.utcnow().isoformat(),
                'expires_in': 600,  # 10 minutes
                'user_id': current_user_id
            }
        })
        
    except ValueError as ve:
        logger.error(f"Failed to initiate admin Google auth: {str(ve)}")
        return jsonify({
            'success': False,
            'message': str(ve),
            'error_code': 'OAUTH_INIT_FAILED'
        }), 400
        
    except Exception as e:
        logger.error(f"Failed to initiate admin Google auth: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to initiate Google authentication',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@api.route('/auth/google/admin/callback', methods=['GET'])
def google_admin_callback():
    """
    Handle Google OAuth callback for admin (API-12)
    ---
    tags:
      - Google Authentication
    description: |
      Handle the OAuth callback from Google after admin user completes authentication.
      This endpoint processes the authorization code and stores persistent credentials
      per API-12a requirements.
      
      **Internal Endpoint**: This endpoint is called automatically by Google's OAuth service.
    parameters:
      - name: code
        in: query
        type: string
        required: true
        description: Authorization code from Google OAuth
      - name: state
        in: query
        type: string
        required: true
        description: State parameter for CSRF protection
      - name: error
        in: query
        type: string
        required: false
        description: Error code if OAuth failed
    responses:
      200:
        description: Authentication successful
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Google Drive authentication successful!"
            oauth_info:
              type: object
              properties:
                authenticated:
                  type: boolean
                  example: true
                persistent_session_created:
                  type: boolean
                  example: true
                scopes:
                  type: array
                  items:
                    type: string
                  example: ["https://www.googleapis.com/auth/drive"]
                user_info:
                  type: object
                  properties:
                    email:
                      type: string
                      example: "admin@company.com"
                    name:
                      type: string
                      example: "Admin User"
            next_steps:
              type: array
              items:
                type: string
              example: 
                - "Authentication is now persistent and will auto-refresh"
                - "File uploads will be stored in your Google Drive"
                - "Users will receive shareable links with edit permissions"
      400:
        description: Invalid callback parameters or authentication failed
      500:
        description: Authentication processing failed
    """
    try:
        # Check for OAuth errors
        error_param = request.args.get('error')
        if error_param:
            logger.warning(f"OAuth error received: {error_param}")
            return jsonify({
                'success': False,
                'message': f'Google authentication was cancelled or failed: {error_param}',
                'error_code': 'OAUTH_CANCELLED'
            }), 400
        
        authorization_code = request.args.get('code')
        state = request.args.get('state')
        
        if not authorization_code:
            return jsonify({
                'success': False,
                'message': 'Authorization code not provided by Google',
                'error_code': 'MISSING_AUTH_CODE'
            }), 400
        
        if not state:
            return jsonify({
                'success': False,
                'message': 'State parameter missing - possible security issue',
                'error_code': 'MISSING_STATE'
            }), 400
        
        from app.services.google_admin_auth_fixed import GoogleAdminAuthServiceFixed
        auth_service = GoogleAdminAuthServiceFixed()
        credentials = auth_service.handle_oauth_callback(authorization_code, state)
        
        # Get additional info about the authentication
        user_id = session.get('admin_user_id')  # This should be cleared by the callback handler
        if user_id:
            auth_status = auth_service.get_auth_status(user_id)
        else:
            auth_status = {'authenticated': True}
        
        return jsonify({
            'success': True,
            'message': 'Google Drive authentication successful! File uploads will now be stored in admin\'s Google Drive.',
            'oauth_info': {
                'authenticated': True,
                'persistent_session_created': True,
                'scopes': credentials.scopes if credentials else [],
                'auto_refresh_enabled': True,
                'oauth_status': auth_status
            },
            'next_steps': [
                'Authentication is now persistent and will auto-refresh tokens',
                'File uploads will be automatically stored in your Google Drive',
                'Users will receive shareable Google Doc links with edit permissions',
                'Storage usage will be monitored with warnings at capacity thresholds'
            ],
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except ValueError as ve:
        logging.getLogger(__name__).error(f"Google admin callback failed: {str(ve)}")
        return jsonify({
            'success': False,
            'message': str(ve),
            'error_code': 'CALLBACK_VALIDATION_FAILED'
        }), 400
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Google admin callback failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Authentication failed: {str(e)}',
            'error_code': 'CALLBACK_PROCESSING_FAILED'
        }), 500


@api.route('/auth/google/admin/status', methods=['GET'])
@token_required
def google_admin_auth_status():
    """
    Check admin Google authentication status (API-12a)
    ---
    tags:
      - Google Authentication
    security:
      - Bearer: []
    description: |
      Check the current Google authentication status for admin users, including
      persistent session information and storage quota status. This endpoint
      implements API-12a persistent authentication monitoring.
      
      **Admin Access Only**: This endpoint requires admin privileges.
    responses:
      200:
        description: Authentication status retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            oauth_status:
              type: object
              properties:
                authenticated:
                  type: boolean
                  example: true
                is_persistent:
                  type: boolean
                  example: true
                session_id:
                  type: string
                  example: "abc123def456ghi789"
                token_expires_at:
                  type: string
                  format: date-time
                last_refresh_at:
                  type: string
                  format: date-time
                auto_refresh_enabled:
                  type: boolean
                  example: true
                is_active:
                  type: boolean
                  example: true
            storage_status:
              type: object
              properties:
                quota_total:
                  type: integer
                  example: 17179869184
                  description: Total storage quota in bytes
                quota_used:
                  type: integer
                  example: 13743895347
                  description: Used storage in bytes
                usage_percentage:
                  type: number
                  example: 80.0
                warning_level:
                  type: string
                  example: "low"
                  enum: ["none", "low", "medium", "high", "critical"]
                last_check:
                  type: string
                  format: date-time
                formatted_quota:
                  type: object
                  properties:
                    total:
                      type: string
                      example: "16.0 GB"
                    used:
                      type: string
                      example: "12.8 GB"
                    available:
                      type: string
                      example: "3.2 GB"
            scopes:
              type: array
              items:
                type: string
              example: ["https://www.googleapis.com/auth/drive"]
      401:
        description: Authentication required
      403:
        description: Admin privileges required
      500:
        description: Failed to check authentication status
    """
    try:
        current_user_id = request.user['user_id']
        
        # Check if user is admin
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Admin privileges required',
                'error_code': 'ADMIN_REQUIRED'
            }), 403
        
        from app.services.google_admin_auth_fixed import GoogleAdminAuthServiceFixed
        auth_service = GoogleAdminAuthServiceFixed()
        
        # Get comprehensive auth status
        auth_status = auth_service.get_auth_status(current_user_id)
        
        # Get storage information if authenticated
        storage_info = {}
        if auth_status.get('authenticated'):
            storage_info = auth_service.get_storage_info(current_user_id)
        
        # Get current credentials for scope information
        credentials = auth_service.get_admin_credentials(current_user_id)
        scopes = credentials.scopes if credentials else []
        
        return jsonify({
            'success': True,
            'oauth_status': auth_status,
            'storage_status': storage_info,
            'scopes': scopes,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to check Google auth status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to check authentication status',
            'error_code': 'STATUS_CHECK_FAILED'
        }), 500


@api.route('/auth/google/admin/revoke', methods=['POST'])
@token_required
def revoke_admin_google_auth():
    """
    Revoke admin Google authentication
    ---
    tags:
      - Google Authentication
    security:
      - Bearer: []
    description: |
      Manually revoke Google OAuth authentication for the admin user.
      This will deactivate the persistent session and require re-authentication
      for future Google Drive operations.
      
      **Admin Access Only**: This endpoint requires admin privileges.
    parameters:
      - in: body
        name: revocation_data
        required: false
        schema:
          type: object
          properties:
            confirm_revocation:
              type: boolean
              example: true
              description: Confirmation that revocation is intended
            reason:
              type: string
              example: "Manual admin revocation"
              description: Reason for revocation (optional)
    responses:
      200:
        description: Authentication revoked successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Google authentication has been revoked"
            revocation_info:
              type: object
              properties:
                revoked_at:
                  type: string
                  format: date-time
                reason:
                  type: string
                  example: "Manual admin revocation"
                session_id:
                  type: string
                  example: "abc123def456ghi789"
            next_steps:
              type: array
              items:
                type: string
              example:
                - "Re-authenticate at /auth/google/admin to restore Google Drive integration"
                - "File uploads will use local storage until re-authentication"
      400:
        description: Invalid revocation request
      401:
        description: Authentication required
      403:
        description: Admin privileges required
      500:
        description: Failed to revoke authentication
    """
    try:
        current_user_id = request.user['user_id']
        
        # Check if user is admin
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Admin privileges required',
                'error_code': 'ADMIN_REQUIRED'
            }), 403
        
        # Get request data
        data = request.get_json() or {}
        confirm_revocation = data.get('confirm_revocation', True)
        reason = data.get('reason', 'Manual admin revocation')
        
        if not confirm_revocation:
            return jsonify({
                'success': False,
                'message': 'Revocation not confirmed',
                'error_code': 'REVOCATION_NOT_CONFIRMED'
            }), 400
        
        from app.services.google_admin_auth_fixed import GoogleAdminAuthServiceFixed
        auth_service = GoogleAdminAuthServiceFixed()
        
        # Get current session info before revocation
        auth_status = auth_service.get_auth_status(current_user_id)
        session_id = auth_status.get('oauth_status', {}).get('persistent_session_id')
        
        # Revoke authentication
        revocation_successful = auth_service.revoke_admin_auth(current_user_id, reason)
        
        if revocation_successful:
            return jsonify({
                'success': True,
                'message': 'Google authentication has been revoked successfully',
                'revocation_info': {
                    'revoked_at': datetime.utcnow().isoformat(),
                    'reason': reason,
                    'session_id': session_id,
                    'user_id': current_user_id
                },
                'next_steps': [
                    'Re-authenticate at /auth/google/admin to restore Google Drive integration',
                    'File uploads will use local storage until re-authentication',
                    'Previously uploaded files in Google Drive remain accessible'
                ]
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to revoke Google authentication',
                'error_code': 'REVOCATION_FAILED'
            }), 500
        
    except Exception as e:
        logger.error(f"Failed to revoke admin Google auth: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to revoke authentication',
            'error_code': 'REVOCATION_ERROR'
        }), 500




