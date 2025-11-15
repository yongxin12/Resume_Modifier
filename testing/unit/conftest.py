"""
Comprehensive test fixtures for TDD approach
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add core directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from app import create_app
from app.extensions import db
from app.models.temp import User, Resume, ResumeTemplate, GoogleAuth, GeneratedDocument, ResumeFile, PasswordResetToken
from sqlalchemy import text
from datetime import datetime, timedelta
import json


@pytest.fixture(scope='session')
def app():
    """Create application for testing session"""
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key'
    }
    
    app = create_app(config=test_config)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client fixture"""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Application context fixture"""
    with app.app_context():
        yield app


@pytest.fixture(autouse=True)
def clean_db(app_context):
    """Clean database before and after each test"""
    # Clean before test
    try:
        db.session.execute(text('DELETE FROM password_reset_tokens'))
        db.session.execute(text('DELETE FROM resume_files'))
        db.session.execute(text('DELETE FROM generated_documents'))
        db.session.execute(text('DELETE FROM google_auth_tokens'))
        db.session.execute(text('DELETE FROM resumes'))
        db.session.execute(text('DELETE FROM resume_templates'))
        db.session.execute(text('DELETE FROM users WHERE email LIKE \'%@test.com\''))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    
    yield
    
    # Clean after test
    try:
        db.session.execute(text('DELETE FROM password_reset_tokens'))
        db.session.execute(text('DELETE FROM resume_files'))
        db.session.execute(text('DELETE FROM generated_documents'))
        db.session.execute(text('DELETE FROM google_auth_tokens'))
        db.session.execute(text('DELETE FROM resumes'))
        db.session.execute(text('DELETE FROM resume_templates'))
        db.session.execute(text('DELETE FROM users WHERE email LIKE \'%@test.com\''))
        db.session.commit()
    except Exception as e:
        db.session.rollback()


@pytest.fixture
def sample_user():
    """Create a test user"""
    user = User(
        username='testuser',
        email='test@test.com',
        first_name='Test',
        last_name='User',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def authenticated_headers(client, sample_user):
    """Get authentication headers for test user"""
    response = client.post('/api/login', json={
        'email': 'test@test.com',
        'password': 'password123'
    })
    token = response.get_json()['token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def sample_template():
    """Create a test resume template"""
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
    db.session.add(template)
    db.session.commit()
    return template


@pytest.fixture
def sample_resume(sample_user, sample_template):
    """Create a test resume"""
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
    db.session.add(resume)
    db.session.commit()
    return resume


@pytest.fixture
def sample_google_auth(sample_user):
    """Create a test Google auth token"""
    auth = GoogleAuth(
        user_id=sample_user.id,
        access_token='test_access_token',
        refresh_token='test_refresh_token',
        token_expires_at=datetime.utcnow() + timedelta(hours=1),
        scope='https://www.googleapis.com/auth/documents https://www.googleapis.com/auth/drive',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(auth)
    db.session.commit()
    return auth


@pytest.fixture
def mock_google_docs_service():
    """Mock Google Docs API service"""
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
    """Mock Google Drive API service"""
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
    """Mock Google OAuth credentials"""
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
    """Sample job description for testing"""
    return """
    Software Engineer Position
    
    Requirements:
    - Bachelor's degree in Computer Science or related field
    - 3+ years of experience in Python development
    - Experience with web frameworks like Flask or Django
    - Knowledge of database systems (PostgreSQL, MySQL)
    - Familiarity with cloud platforms (AWS, Google Cloud)
    - Strong problem-solving skills
    - Excellent communication abilities
    
    Responsibilities:
    - Develop and maintain web applications
    - Collaborate with cross-functional teams
    - Write clean, maintainable code
    - Participate in code reviews
    - Debug and troubleshoot applications
    """


@pytest.fixture
def sample_resume_data():
    """Sample resume data for testing"""
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
            },
            {
                'companyName': 'StartupXYZ',
                'jobTitle': 'Software Developer',
                'location': 'Palo Alto, CA', 
                'startDate': '2018-06',
                'endDate': '2019-12',
                'description': 'Developed REST APIs and database schemas'
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
        'skills': [
            'Python', 'Flask', 'Django', 'PostgreSQL', 'AWS', 'Git', 'Docker'
        ],
        'certifications': [
            {
                'name': 'AWS Certified Developer',
                'issuer': 'Amazon Web Services',
                'date': '2021-03'
            }
        ]
    }


# Environment variable fixtures
@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'test_client_id')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', 'test_client_secret')
    monkeypatch.setenv('GOOGLE_REDIRECT_URI', 'http://localhost:5001/auth/google/callback')
    monkeypatch.setenv('OPENAI_API_KEY', 'test_openai_key')


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
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