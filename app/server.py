from flask import Blueprint, request, jsonify, redirect, session, current_app, send_file
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
from app.models.temp import User, Resume, JobDescription, GoogleAuth, ResumeTemplate, GeneratedDocument
from app.utils.feedback_validator import FeedbackValidator
from app.utils.jwt_utils import generate_token, token_required
from app.utils.profile_validator import ProfileValidator
from googleapiclient.errors import HttpError
import datetime
import io
import os

# Create blueprint
api = Blueprint('api', __name__)

@api.route('/')
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
def process_feedback():
    """Process feedback and updated resume data."""
    # Validate request
    error, status_code, data = FeedbackValidator.validate_request(request)
    if error:
        return error, status_code
    
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
        "user": {"email": user.email},
        "token": token
    }), 200


# Google OAuth Routes
@api.route('/auth/google', methods=['GET'])
def google_auth():
    """Initiate Google OAuth flow"""
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
    """Handle Google OAuth callback"""
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
    """Save or update a resume for the user"""
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
    """Get list of resumes for the current user"""
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
    """Get a specific resume by ID"""
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
    """Get user profile"""
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
@token_required
def export_resume_to_google_docs():
    """
    Export resume to Google Docs
    ---
    tags:
      - Google Docs Export
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            resume_id:
              type: integer
              description: Resume ID to export
            template_id:
              type: integer
              description: Template ID to apply
            document_title:
              type: string
              description: Optional document title
          required:
            - resume_id
            - template_id
    responses:
      200:
        description: Google Docs document created successfully
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            data:
              type: object
              properties:
                document_id:
                  type: string
                  description: Google Docs document ID
                shareable_url:
                  type: string
                  description: Shareable Google Docs URL
                generated_document_id:
                  type: integer
                  description: Database record ID
      401:
        description: Google authentication required
      404:
        description: Resume or template not found
      500:
        description: Export failed
    """
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


