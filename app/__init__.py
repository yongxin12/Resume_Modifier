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
    
    # Initialize extensions
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    swagger = Swagger(app)
    db.init_app(app)
    
    # Import models to ensure they're known to Flask-Migrate
    # Models are imported automatically by importing from app.models.db
    # This ensures they are registered with Flask-SQLAlchemy
    with app.app_context():
        # Import models and explicitly register them with Flask-SQLAlchemy
        from app.models.temp import User, Resume, JobDescription, ResumeFile, ResumeTemplate, GoogleAuth, GeneratedDocument, UserSite, PasswordResetToken
        # Make sure the models are registered with db.metadata
        for model in [User, Resume, JobDescription, ResumeFile, ResumeTemplate, GoogleAuth, GeneratedDocument, UserSite, PasswordResetToken]:
            if hasattr(model, '__table__'):
                if model.__table__.name not in db.metadata.tables:
                    db.metadata.tables[model.__table__.name] = model.__table__
    
    # Initialize Flask-Migrate after models are imported
    migrate.init_app(app, db)
    
    # Initialize login manager
    login_manager.init_app(app)
    
    # Initialize email service
    from app.services.email_service import email_service
    email_service.init_app(app)
    
    # Register blueprints
    from app.server import api
    from app.web import web
    app.register_blueprint(api)
    app.register_blueprint(web)
    
    return app 