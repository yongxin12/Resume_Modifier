"""
Pytest configuration and shared fixtures for the Resume Modifier project.
Comprehensive test fixtures for TDD approach.
"""

import pytest
import sys
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Ensure core/ is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
core_path = os.path.join(project_root, 'core')
if core_path not in sys.path:
    sys.path.insert(0, core_path)


@pytest.fixture(scope='session')
def app():
    """Create test Flask application."""
    from app import create_app
    from app.extensions import db
    
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    }
    
    app = create_app(config=test_config)
    
    # Create all tables at session start
    with app.app_context():
        db.create_all()
    
    yield app
    
    # Drop tables at session end
    with app.app_context():
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client with fresh database state."""
    from app.extensions import db
    
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        yield app.test_client()
        # Clean up after each test
        db.session.rollback()
        # Only try to clear tables that exist
        try:
            for table in reversed(db.metadata.sorted_tables):
                try:
                    db.session.execute(table.delete())
                except Exception:
                    pass  # Table might not exist
            db.session.commit()
        except Exception:
            db.session.rollback()


@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for tests."""
    from app.extensions import db
    
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def sample_user(app, db_session):
    """Create a sample user for testing (returns User object for compatibility)."""
    from app.models.temp import User
    
    with app.app_context():
        user = User(
            username='testuser',
            email='test@test.com',
            first_name='Test',
            last_name='User',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        user.set_password('testpassword123')
        db_session.add(user)
        db_session.commit()
        
        # Refresh to ensure object is attached
        db_session.refresh(user)
        yield user


@pytest.fixture
def sample_user_id(app, db_session):
    """Create a sample user for testing (returns ID for isolation)."""
    from app.models.temp import User
    
    with app.app_context():
        user = User(
            username='testuser_id',
            email='test_id@example.com',
            first_name='Test',
            last_name='User',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        user.set_password('testpassword123')
        db_session.add(user)
        db_session.commit()
        
        user_id = user.id
        yield user_id


@pytest.fixture
def auth_token(app, sample_user):
    """Generate authentication token for testing."""
    from app.utils.jwt_utils import generate_token
    
    with app.app_context():
        # sample_user is now a User object
        return generate_token(sample_user.id, sample_user.email)


@pytest.fixture
def auth_headers(auth_token):
    """Generate headers with authentication token."""
    return {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def authenticated_headers(auth_headers):
    """Alias for auth_headers (used by some tests)."""
    return auth_headers


@pytest.fixture
def sample_resume_file(app, db_session, sample_user):
    """Create a sample resume file for testing."""
    from app.models.temp import ResumeFile
    
    with app.app_context():
        resume_file = ResumeFile(
            user_id=sample_user.id,
            original_filename='test_resume.pdf',
            stored_filename='stored_test_resume.pdf',
            file_size=1024,
            mime_type='application/pdf',
            storage_type='local',
            file_path='/path/to/test_resume.pdf',
            file_hash='test_hash_123',
            category='active',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(resume_file)
        db_session.commit()
        
        file_id = resume_file.id
        yield file_id


@pytest.fixture
def mock_google_docs_service():
    """Mock Google Docs API service."""
    service = Mock()
    
    # Mock documents().create()
    create_mock = Mock()
    create_mock.execute.return_value = {
        'documentId': 'test_doc_id_123',
        'title': 'Test Resume',
        'revisionId': 'test_revision_id'
    }
    service.documents.return_value.create.return_value = create_mock
    
    # Mock documents().batchUpdate()
    batch_update_mock = Mock()
    batch_update_mock.execute.return_value = {
        'documentId': 'test_doc_id_123',
        'replies': []
    }
    service.documents.return_value.batchUpdate.return_value = batch_update_mock
    
    # Mock documents().get()
    get_mock = Mock()
    get_mock.execute.return_value = {
        'documentId': 'test_doc_id_123',
        'title': 'Test Resume',
        'body': {'content': []}
    }
    service.documents.return_value.get.return_value = get_mock
    
    return service


@pytest.fixture
def mock_google_drive_service():
    """Mock Google Drive API service."""
    service = Mock()
    
    # Mock permissions().create()
    permissions_mock = Mock()
    permissions_mock.execute.return_value = {'id': 'permission_id'}
    service.permissions.return_value.create.return_value = permissions_mock
    
    # Mock files().export()
    export_mock = Mock()
    export_mock.execute.return_value = b'PDF content here'
    service.files.return_value.export.return_value = export_mock
    
    # Mock files().get()
    get_mock = Mock()
    get_mock.execute.return_value = {
        'id': 'test_doc_id_123',
        'name': 'Test Resume',
        'webViewLink': 'https://docs.google.com/document/d/test_doc_id_123/edit'
    }
    service.files.return_value.get.return_value = get_mock
    
    return service


@pytest.fixture
def mock_google_credentials():
    """Mock Google OAuth credentials."""
    creds = Mock()
    creds.valid = True
    creds.expired = False
    creds.token = 'test_access_token'
    creds.refresh_token = 'test_refresh_token'
    creds.token_uri = 'https://oauth2.googleapis.com/token'
    creds.client_id = 'test_client_id'
    creds.client_secret = 'test_client_secret'
    return creds


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
    Software Engineer Position
    
    Requirements:
    - Bachelor's degree in Computer Science or related field
    - 3+ years of experience in Python development
    - Experience with web frameworks like Flask or Django
    - Knowledge of database systems (PostgreSQL, MySQL)
    - Strong problem-solving skills
    
    Responsibilities:
    - Develop and maintain web applications
    - Collaborate with cross-functional teams
    - Write clean, maintainable code
    """


@pytest.fixture
def sample_resume_data():
    """Sample resume data for testing."""
    return {
        'userInfo': {
            'firstName': 'John',
            'lastName': 'Doe',
            'email': 'john.doe@test.com',
            'phone': '+1-555-123-4567',
            'location': 'San Francisco, CA'
        },
        'summary': 'Experienced software engineer with 5+ years in Python development',
        'workExperience': [
            {
                'companyName': 'Tech Corp',
                'jobTitle': 'Senior Software Engineer',
                'location': 'San Francisco, CA',
                'startDate': '2020-01',
                'endDate': 'Present',
                'description': 'Lead development of web applications using Python and Flask'
            }
        ],
        'education': [
            {
                'institutionName': 'Stanford University',
                'degree': 'Bachelor of Science',
                'fieldOfStudy': 'Computer Science',
                'graduationDate': '2018-05'
            }
        ],
        'skills': ['Python', 'Flask', 'Django', 'PostgreSQL', 'AWS', 'Git', 'Docker']
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'test_client_id')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', 'test_client_secret')
    monkeypatch.setenv('GOOGLE_REDIRECT_URI', 'http://localhost:5001/auth/google/callback')
    monkeypatch.setenv('OPENAI_API_KEY', 'test_openai_key')


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        'choices': [{
            'message': {
                'content': json.dumps({
                    'optimized_content': 'Improved resume content with better keywords',
                    'improvements': ['Added relevant keywords', 'Improved formatting'],
                    'ats_score': 85
                })
            }
        }]
    }


@pytest.fixture
def app_context(app):
    """Application context fixture."""
    with app.app_context():
        yield app


@pytest.fixture
def sample_template(app, db_session):
    """Create a test resume template (returns full object for compatibility)."""
    from app.models.temp import ResumeTemplate
    
    with app.app_context():
        template = ResumeTemplate(
            name='Test Template',
            description='A test template for unit testing',
            style_config={
                'font_family': 'Arial',
                'header_font_size': 16,
                'body_font_size': 11,
                'color_scheme': {
                    'primary': '#2E86AB',
                    'text': '#333333'
                }
            },
            sections=['header', 'summary', 'experience', 'education', 'skills'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(template)
        db_session.commit()
        
        db_session.refresh(template)
        yield template


@pytest.fixture
def sample_template_id(app, db_session):
    """Create a test resume template (returns ID for isolation)."""
    from app.models.temp import ResumeTemplate
    
    with app.app_context():
        template = ResumeTemplate(
            name='Test Template ID',
            description='A test template for unit testing',
            style_config={
                'font_family': 'Arial',
                'header_font_size': 16,
                'body_font_size': 11,
                'color_scheme': {
                    'primary': '#2E86AB',
                    'text': '#333333'
                }
            },
            sections=['header', 'summary', 'experience', 'education', 'skills'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(template)
        db_session.commit()
        
        template_id = template.id
        yield template_id


@pytest.fixture
def sample_template_obj(app, db_session):
    """Create a test resume template (returns full object for tests that need it)."""
    from app.models.temp import ResumeTemplate
    
    with app.app_context():
        template = ResumeTemplate(
            name='Test Template Object',
            description='A test template for unit testing',
            style_config={
                'font_family': 'Arial',
                'header_font_size': 16,
                'body_font_size': 11,
                'color_scheme': {
                    'primary': '#2E86AB',
                    'text': '#333333'
                }
            },
            sections=['header', 'summary', 'experience', 'education', 'skills'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(template)
        db_session.commit()
        
        db_session.refresh(template)
        yield template


@pytest.fixture
def sample_resume(app, db_session, sample_user, sample_template):
    """Create a test resume (returns ID for isolation)."""
    from app.models.temp import Resume
    
    with app.app_context():
        resume = Resume(
            user_id=sample_user.id,
            serial_number=1,
            title='Test Resume',
            template_id=sample_template.id,
            parsed_resume={
                'userInfo': {
                    'firstName': 'Test',
                    'lastName': 'User',
                    'email': 'test@test.com'
                },
                'workExperience': [{
                    'companyName': 'Test Company',
                    'jobTitle': 'Test Position',
                    'description': 'Test work description'
                }],
                'education': [{
                    'institutionName': 'Test University',
                    'degree': 'Bachelor of Science',
                    'fieldOfStudy': 'Computer Science'
                }],
                'skills': ['Python', 'JavaScript', 'Testing']
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(resume)
        db_session.commit()
        
        resume_id = resume.id
        yield resume_id


@pytest.fixture
def sample_resume_obj(app, db_session, sample_user, sample_template):
    """Create a test resume (returns full object for tests that need it)."""
    from app.models.temp import Resume
    
    with app.app_context():
        resume = Resume(
            user_id=sample_user.id,
            serial_number=1,
            title='Test Resume Object',
            template_id=sample_template.id,
            parsed_resume={
                'userInfo': {
                    'firstName': 'Test',
                    'lastName': 'User',
                    'email': 'test@test.com'
                },
                'workExperience': [{
                    'companyName': 'Test Company',
                    'jobTitle': 'Test Position',
                    'description': 'Test work description'
                }],
                'education': [{
                    'institutionName': 'Test University',
                    'degree': 'Bachelor of Science',
                    'fieldOfStudy': 'Computer Science'
                }],
                'skills': ['Python', 'JavaScript', 'Testing']
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(resume)
        db_session.commit()
        
        # Return the object itself, refreshed to avoid detached state issues
        db_session.refresh(resume)
        yield resume


@pytest.fixture
def sample_google_auth(app, db_session, sample_user):
    """Create a test Google auth token (returns ID for isolation)."""
    from app.models.temp import GoogleAuth
    
    with app.app_context():
        auth = GoogleAuth(
            user_id=sample_user.id,
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scope='https://www.googleapis.com/auth/documents https://www.googleapis.com/auth/drive',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(auth)
        db_session.commit()
        
        auth_id = auth.id
        yield auth_id


@pytest.fixture
def sample_google_auth_obj(app, db_session, sample_user):
    """Create a test Google auth token (returns full object for tests that need it)."""
    from app.models.temp import GoogleAuth
    
    with app.app_context():
        auth = GoogleAuth(
            user_id=sample_user.id,
            access_token='test_access_token_obj',
            refresh_token='test_refresh_token_obj',
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scope='https://www.googleapis.com/auth/documents https://www.googleapis.com/auth/drive',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(auth)
        db_session.commit()
        
        db_session.refresh(auth)
        yield auth
