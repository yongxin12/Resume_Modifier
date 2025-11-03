from flask import Blueprint, request, jsonify, redirect, session, current_app, send_file
from flasgger import swag_from
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
from app.services.pdf_generator import PDFGenerator
from app.response_template.resume_schema import RESUME_TEMPLATE
from app.models.temp import User, Resume, JobDescription, GoogleAuth, ResumeTemplate, GeneratedDocument, ResumeFile
from app.utils.feedback_validator import FeedbackValidator
from app.utils.jwt_utils import generate_token, token_required
from app.utils.profile_validator import ProfileValidator
from app.utils.file_validator import FileValidator
from app.services.file_storage_service import FileStorageService
from app.services.file_processing_service import FileProcessingService
from googleapiclient.errors import HttpError
import datetime
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
        "timestamp": datetime.datetime.utcnow().isoformat(),
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
    # Validate request
    error, status_code, data = JobValidator.validate_request(request)
    if error:
        return error, status_code
    
    try:
        # Process with ResumeAI
        resume_processor = ResumeAI("")  # Empty string as we're using provided resume
        resume_processor.parsed_resume = data['updated_resume']
        analysis = resume_processor.analyze(data['job_description'])

        return jsonify({
            "status": 200,
            "data": analysis
        }), 200
        
    except Exception as e:
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
    Upload a resume file (PDF or DOCX)
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
    responses:
      201:
        description: File uploaded successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "File uploaded successfully"
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
                sanitized_filename:
                  type: string
                  example: "secure_resume_20241025.pdf"
                file_size:
                  type: integer
                  example: 245760
                file_type:
                  type: string
                  example: "pdf"
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
                metadata:
                  type: object
                  example: {"word_count": 250, "page_count": 2}
      400:
        description: Invalid request or validation failed
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "File validation failed"
            errors:
              type: array
              items:
                type: string
      401:
        description: Authentication required
      500:
        description: Upload failed
    """
    try:
        # Get current user from token
        current_user_id = request.user['user_id']
        
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
            return jsonify({
                'success': False,
                'message': 'File validation failed',
                'errors': validation_result.errors
            }), 400
        
        # Upload file to storage
        storage_result = file_storage_service.upload_file(
            file_storage=uploaded_file,
            user_id=current_user_id,
            filename=validation_result.sanitized_filename
        )
        
        if not storage_result.success:
            return jsonify({
                'success': False,
                'message': 'File storage failed',
                'error': storage_result.error_message
            }), 500
        
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
        
        # Create database record
        try:
            resume_file = ResumeFile(
                user_id=current_user_id,
                original_filename=uploaded_file.filename,
                stored_filename=validation_result.sanitized_filename,
                file_path=storage_result.file_path if storage_result.storage_type == 'local' else storage_result.s3_key,
                file_size=storage_result.file_size,
                mime_type=uploaded_file.content_type or 'application/octet-stream',
                storage_type=storage_result.storage_type,
                s3_bucket=getattr(storage_result, 's3_bucket', None),
                file_hash=getattr(validation_result, 'file_hash', None) or 'temp_hash',
                extracted_text=extracted_text,
                is_processed=should_process and extracted_text is not None,
                processing_status='completed' if extracted_text else 'pending',
                processing_error=processing_warning,
                tags=[],
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow()
            )
            
            db.session.add(resume_file)
            db.session.commit()
            
            # Prepare response
            response_data = {
                'success': True,
                'message': 'File uploaded successfully',
                'file': {
                    'file_id': resume_file.id,
                    'user_id': resume_file.user_id,
                    'original_filename': resume_file.original_filename,
                    'stored_filename': resume_file.stored_filename,
                    'file_size': resume_file.file_size,
                    'mime_type': resume_file.mime_type,
                    'storage_type': resume_file.storage_type,
                    'storage_path': resume_file.file_path,
                    'download_url': storage_result.url,
                    'upload_date': resume_file.created_at.isoformat(),
                    'extracted_text': resume_file.extracted_text,
                    'is_processed': resume_file.is_processed,
                    'processing_status': resume_file.processing_status,
                    'file_hash': resume_file.file_hash,
                    's3_bucket': resume_file.s3_bucket
                }
            }
            
            # Add processing warning if any
            if processing_warning:
                response_data['processing_warning'] = processing_warning
            
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
        
        # Find the file record in database
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
            return send_file(
                BytesIO(download_result.content),
                as_attachment=not inline,
                download_name=resume_file.original_filename,
                mimetype=download_result.content_type or 'application/octet-stream'
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
        
        # Get file from database
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
        logger.error(f"Unexpected error during file info retrieval: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving file information: {str(e)}'
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
        
        # Find the file record in database
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
                logger.error(f"Storage deletion failed for file {file_id}: {delete_result.error_message}")
                return jsonify({
                    'success': False,
                    'message': f'Failed to delete file from storage: {delete_result.error_message}'
                }), 500
            
            # Remove from database completely
            db.session.delete(resume_file)
            delete_type = 'hard'
            
        else:
            # Soft delete: mark as inactive
            resume_file.is_active = False
            resume_file.updated_at = datetime.datetime.utcnow()
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
        logger.error(f"Unexpected error during file deletion: {str(e)}")
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
        
        # Build query
        query = ResumeFile.query.filter_by(
            user_id=current_user_id,
            is_active=True
        )
        
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
        
        # Format response
        files_data = []
        for file in files:
            files_data.append({
                'id': file.id,
                'original_filename': file.original_filename,
                'file_size': file.file_size,
                'mime_type': file.mime_type,
                'storage_type': file.storage_type,
                'created_at': file.created_at.isoformat() if file.created_at else None,
                'updated_at': file.updated_at.isoformat() if file.updated_at else None,
                'processing_status': file.processing_status,
                'page_count': file.page_count
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
        # Log the error
        logger.error(f"Unexpected error during file listing: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving files: {str(e)}'
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
                resume_file = ResumeFile.query.filter_by(
                    id=file_id,
                    user_id=current_user_id,
                    is_active=True
                ).first()
                
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
                        logger.error(f"Error deleting file from storage: {str(storage_error)}")
                        # Continue with database deletion even if storage deletion fails
                    
                    # Remove from database
                    db.session.delete(resume_file)
                else:
                    # Soft delete - just mark as inactive
                    resume_file.is_active = False
                    resume_file.updated_at = datetime.utcnow()
                
                db.session.commit()
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Error deleting file {file_id}: {str(e)}")
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
        logger.error(f"Unexpected error during bulk file deletion: {str(e)}")
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
        
        # Find the file
        file_record = ResumeFile.query.filter_by(
            id=file_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
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
                
                logger.error(f"Failed to download file {file_id} for processing: {download_result.error_message}")
                
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
                file_record.page_count = processing_result.page_count
                file_record.metadata = processing_result.metadata
                file_record.language = processing_result.language
                file_record.keywords = processing_result.keywords
                file_record.processing_time = processing_result.processing_time
                
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
                        'metadata': processing_result.metadata,
                        'processing_time': processing_result.processing_time,
                        'page_count': processing_result.page_count,
                        'paragraph_count': processing_result.paragraph_count,
                        'keywords': processing_result.keywords,
                        'language': processing_result.language
                    }
                }), 200
            else:
                # Processing failed
                file_record.processing_status = 'failed'
                file_record.error_message = processing_result.error_message
                
                # Log processing failure
                logger.error(f"File {file_id} processing failed for user {current_user_id}: {processing_result.error_message}")
                
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
            logger.error(f"Error processing file {file_id} for user {current_user_id}: {str(processing_error)}")
            
            return jsonify({
                'success': False,
                'message': f'Error processing file: {str(processing_error)}'
            }), 500
            
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error during file processing: {str(e)}")
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
        updated_at=datetime.datetime.utcnow(),
        created_at=datetime.datetime.utcnow()
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
                
        google_auth_service = GoogleAuthService()
        
        # Get authorization URL
        auth_url = google_auth_service.get_authorization_url(int(user_id))
        
        return redirect(auth_url)
        
    except Exception as e:
        current_app.logger.error(f"Google OAuth initiation error: {str(e)}")
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
        current_app.logger.error(f"Google OAuth callback error: {str(e)}")
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
            
            return jsonify({
                "authenticated": True,
                "google_user": {
                    "email": google_auth.email,
                    "name": google_auth.name,
                    "picture": google_auth.picture
                }
            }), 200
        else:
            return jsonify({"authenticated": False}), 200
            
    except Exception as e:
        current_app.logger.error(f"Google auth status error: {str(e)}")
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
        current_app.logger.error(f"Google auth revoke error: {str(e)}")
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
        current_app.logger.error(f"Google auth store error: {str(e)}")
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
        current_app.logger.error(f"Google auth refresh error: {str(e)}")
        return jsonify({"error": "Failed to refresh authentication tokens"}), 500


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
            now = datetime.datetime.utcnow()  # Using standard utcnow() method
            
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
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
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
    
    # Validate required fields
    if not data or not all(key in data for key in ['user_data', 'job_description', 'template_id']):
        return jsonify({
            "error": "Missing required_fields: user_data, job_description, template_id"
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


