# Empty file is sufficient
# This makes the app directory a Python package 

from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from app.extensions import db, migrate, login_manager
import os
from dotenv import load_dotenv

def create_app(config=None):
    # Create app
    app = Flask(__name__)
    
    # Load environment variables first (but only if not testing)
    if not config or not config.get('TESTING'):
        print("Loading environment variables from .env")
        load_dotenv()
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://mysql:Mintmelon666!@localhost:3306/resume_app')
        # Set Flask secret key for sessions
        app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
        
        # Load Google Drive configuration (Service Account)
        app.config['GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE'] = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE')
        app.config['GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO'] = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO')
        app.config['GOOGLE_DRIVE_PARENT_FOLDER_ID'] = os.getenv('GOOGLE_DRIVE_PARENT_FOLDER_ID')
        app.config['GOOGLE_DRIVE_SHARED_DRIVE_ID'] = os.getenv('GOOGLE_DRIVE_SHARED_DRIVE_ID')
        app.config['GOOGLE_DRIVE_ENABLED'] = os.getenv('GOOGLE_DRIVE_ENABLED', 'true').lower() == 'true'
        
        # Load Google OAuth configuration (Admin Authentication)
        app.config['GOOGLE_ADMIN_OAUTH_CLIENT_ID'] = os.getenv('GOOGLE_ADMIN_OAUTH_CLIENT_ID')
        app.config['GOOGLE_ADMIN_OAUTH_CLIENT_SECRET'] = os.getenv('GOOGLE_ADMIN_OAUTH_CLIENT_SECRET')
        app.config['GOOGLE_ADMIN_OAUTH_REDIRECT_URI'] = os.getenv('GOOGLE_ADMIN_OAUTH_REDIRECT_URI', 'http://localhost:5001/auth/google/admin/callback')
        app.config['GOOGLE_ADMIN_DRIVE_FOLDER_NAME'] = os.getenv('GOOGLE_ADMIN_DRIVE_FOLDER_NAME', 'Resume_Modifier_Files')
        app.config['GOOGLE_DRIVE_ENABLE_SHARING'] = os.getenv('GOOGLE_DRIVE_ENABLE_SHARING', 'true').lower() == 'true'
        app.config['GOOGLE_DRIVE_DEFAULT_PERMISSIONS'] = os.getenv('GOOGLE_DRIVE_DEFAULT_PERMISSIONS', 'writer')
    else:
        print("Loading test configuration")
        # For testing, use SQLite by default
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SECRET_KEY'] = 'test-secret-key'
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Override with custom config if provided
    if config:
        app.config.update(config)
    
    # Swagger configuration
    app.config['SWAGGER'] = {
        'title': 'Resume Editor API',
        'uiversion': 3,
        'version': '1.0.0',
        'description': 'API documentation for Resume Editor application with AI-powered resume parsing, analysis, and scoring',
        'termsOfService': '',
        'contact': {
            'name': 'API Support',
            'email': 'support@resumeeditor.com'
        }
    }
    
    # Configure Flask sessions for Docker environment (will be done after extensions are initialized)
    
    # CORS Configuration - Allow frontend origins including Lovable
    cors_origins = os.getenv('CORS_ORIGINS', '*')
    if cors_origins != '*':
        # Parse comma-separated origins
        allowed_origins = [origin.strip() for origin in cors_origins.split(',')]
    else:
        allowed_origins = '*'
    
    # Always include Lovable frontend origins for development/production
    lovable_origins = [
        'https://bf2cf7ea-4663-40a3-94f2-8b02671da1f2.lovableproject.com',
        'https://id-preview--bf2cf7ea-4663-40a3-94f2-8b02671da1f2.lovable.app',
    ]
    
    if allowed_origins == '*':
        # If wildcard, keep it as wildcard (allows all origins)
        final_origins = '*'
    else:
        # Merge configured origins with Lovable origins
        final_origins = list(set(allowed_origins + lovable_origins))
    
    # Initialize extensions
    CORS(app, resources={
        r"/*": {
            "origins": final_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["Authorization", "Content-Type", "X-Requested-With", "Accept"],
            "expose_headers": ["Content-Range", "X-Content-Range"],
            "supports_credentials": True,
            "max_age": 600
        }
    })
    swagger = Swagger(app)
    db.init_app(app)
    
    # Import models to ensure they're known to Flask-Migrate
    # Models are imported automatically by importing from app.models.temp
    # This ensures they are registered with Flask-SQLAlchemy
    with app.app_context():
        # Import models to register them with Flask-SQLAlchemy
        from app.models.temp import User, Resume, JobDescription, ResumeFile, ResumeTemplate, GoogleAuth, GeneratedDocument, UserSite, PasswordResetToken
        # Models are automatically registered when imported, no need to manually add to metadata
    
    # Initialize Flask-Migrate after models are imported
    migrate.init_app(app, db)
    
    # Initialize login manager
    login_manager.init_app(app)
    
    # Initialize email service
    from app.services.email_service import email_service
    email_service.init_app(app)
    
    # Configure Flask sessions for Docker environment (after all extensions are initialized)
    try:
        from app.services.flask_session_config import configure_flask_sessions_for_docker, setup_oauth_session_support, validate_session_configuration
        configure_flask_sessions_for_docker(app)
        setup_oauth_session_support(app)
        
        # Validate session configuration
        session_validation = validate_session_configuration(app)
        if not session_validation.get('OVERALL_VALID', False):
            print("⚠️  Session configuration validation failed - OAuth may not work properly")
        
        # Initialize OAuth temporary states table
        from app.services.google_admin_auth_fixed import create_oauth_temp_states_table
        with app.app_context():
            create_oauth_temp_states_table()
        
        print("✅ OAuth session configuration completed successfully")
    except Exception as e:
        print(f"⚠️  Warning: OAuth session configuration failed: {e}")
        print("   OAuth functionality may not work properly")
    
    # Register blueprints
    from app.server import api
    from app.web import web
    from app.api.file_category_endpoints import file_category_bp
    
    app.register_blueprint(api)
    app.register_blueprint(web)
    app.register_blueprint(file_category_bp, url_prefix='/api/files')
    
    return app 