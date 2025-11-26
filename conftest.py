"""
Pytest configuration and shared fixtures for the Resume Modifier project.
"""

import pytest
import sys
import os

# Ensure core/ is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
core_path = os.path.join(project_root, 'core')
if core_path not in sys.path:
    sys.path.insert(0, core_path)


@pytest.fixture(scope='session')
def app():
    """Create test Flask application."""
    from app import create_app
    
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    }
    
    app = create_app(config=test_config)
    
    return app


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


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
    """Create a sample user for testing."""
    from app.models.temp import User
    from datetime import datetime
    
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        user.set_password('testpassword123')
        db_session.add(user)
        db_session.commit()
        
        # Return user ID to avoid detached instance issues
        user_id = user.id
        yield user_id


@pytest.fixture
def auth_token(app, sample_user):
    """Generate authentication token for testing."""
    from app.utils.jwt_utils import generate_token
    
    with app.app_context():
        from app.models.temp import User
        user = User.query.get(sample_user)
        return generate_token(user.id, user.email)


@pytest.fixture
def auth_headers(auth_token):
    """Generate headers with authentication token."""
    return {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }
