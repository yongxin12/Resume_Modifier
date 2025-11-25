"""
Integration tests for thumbnail API endpoints
Tests the complete thumbnail workflow from upload to access
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock
import json
from io import BytesIO

# Add core to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../core'))

from app import create_app
from app.extensions import db
from app.models.temp import User, ResumeFile
from app.services.thumbnail_service import ThumbnailService


class TestThumbnailAPI:
    """Test suite for thumbnail API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create Flask application for testing"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
        
        # Cleanup upload folder
        shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def sample_user(self, app):
        """Create sample user for testing"""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                password='hashed_password',
                first_name='Test',
                last_name='User'
            )
            db.session.add(user)
            db.session.commit()
            return user
    
    @pytest.fixture
    def auth_token(self, app, sample_user):
        """Generate auth token for testing"""
        with app.app_context():
            from app.utils.jwt_utils import generate_token
            # Re-attach user to session to access id and email
            user = db.session.merge(sample_user)
            return generate_token(user.id, user.email)
    
    @pytest.fixture
    def sample_resume_file(self, app, sample_user):
        """Create sample resume file for testing"""
        with app.app_context():
            # Re-attach user to session to access id
            user = db.session.merge(sample_user)
            resume_file = ResumeFile(
                user_id=user.id,
                original_filename='test_resume.pdf',
                stored_filename='test_resume_stored.pdf',
                file_size=100000,
                mime_type='application/pdf',
                storage_type='local',
                file_path='/uploads/files/test_resume_stored.pdf',
                file_hash='test_hash',
                processing_status='completed',
                is_processed=True,
                extracted_text='Test resume content',
                has_thumbnail=True,
                thumbnail_status='completed',
                thumbnail_path='/uploads/thumbnails/1.jpg',
                thumbnail_generated_at=datetime.utcnow()
            )
            db.session.add(resume_file)
            db.session.commit()
            return resume_file
    
    @pytest.fixture
    def sample_resume_file_no_thumbnail(self, app, sample_user):
        """Create sample resume file without thumbnail"""
        with app.app_context():
            # Re-attach user to session to access id
            user = db.session.merge(sample_user)
            resume_file = ResumeFile(
                user_id=user.id,
                original_filename='test_resume_no_thumb.pdf',
                stored_filename='test_resume_no_thumb_stored.pdf',
                file_size=50000,
                mime_type='application/pdf',
                storage_type='local',
                file_path='/uploads/files/test_resume_no_thumb_stored.pdf',
                file_hash='test_hash_2',
                processing_status='completed',
                is_processed=True,
                extracted_text='Test resume content without thumbnail',
                has_thumbnail=False,
                thumbnail_status='failed'
            )
            db.session.add(resume_file)
            db.session.commit()
            return resume_file
    
    def test_file_info_includes_thumbnail_data(self, client, app, sample_resume_file, auth_token):
        """Test that file info endpoint includes thumbnail information"""
        with app.app_context():
            # Re-attach file to session to access id
            file = db.session.merge(sample_resume_file)
            headers = {'Authorization': f'Bearer {auth_token}'}
            
            response = client.get(f'/api/files/{file.id}/info', headers=headers)
            
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is True
            assert 'thumbnail' in data['file']
            
            thumbnail_info = data['file']['thumbnail']
            assert thumbnail_info['has_thumbnail'] is True
            assert thumbnail_info['thumbnail_url'] == f'/api/files/{file.id}/thumbnail'
            assert thumbnail_info['thumbnail_status'] == 'completed'
            assert thumbnail_info['thumbnail_generated_at'] is not None
    
    def test_file_info_no_thumbnail(self, client, app, sample_resume_file_no_thumbnail, auth_token):
        """Test file info for file without thumbnail"""
        with app.app_context():
            # Re-attach file to session to access id
            file = db.session.merge(sample_resume_file_no_thumbnail)
            headers = {'Authorization': f'Bearer {auth_token}'}
            
            response = client.get(f'/api/files/{file.id}/info', headers=headers)
            
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is True
            assert 'thumbnail' in data['file']
            
            thumbnail_info = data['file']['thumbnail']
            assert thumbnail_info['has_thumbnail'] is False
            assert thumbnail_info['thumbnail_url'] is None
            assert thumbnail_info['thumbnail_status'] == 'failed'
    
    def test_thumbnail_endpoint_requires_authentication(self, client, app, sample_resume_file):
        """Test that thumbnail endpoint requires authentication"""
        with app.app_context():
            # Re-attach file to session to access id
            file = db.session.merge(sample_resume_file)
            response = client.get(f'/api/files/{file.id}/thumbnail')
            
            assert response.status_code == 401
    
    def test_thumbnail_endpoint_user_authorization(self, client, app, auth_token):
        """Test that users can only access their own thumbnails"""
        with app.app_context():
            # Create another user and their file
            other_user = User(
                username='otheruser',
                email='other@example.com',
                password='hashed_password',
                first_name='Other',
                last_name='User'
            )
            db.session.add(other_user)
            db.session.commit()
            
            other_file = ResumeFile(
                user_id=other_user.id,
                original_filename='other_resume.pdf',
                stored_filename='other_resume_stored.pdf',
                file_size=100000,
                mime_type='application/pdf',
                storage_type='local',
                file_path='/uploads/files/other_resume_stored.pdf',
                file_hash='other_hash',
                has_thumbnail=True,
                thumbnail_status='completed'
            )
            db.session.add(other_file)
            db.session.commit()
            
            headers = {'Authorization': f'Bearer {auth_token}'}
            
            response = client.get(f'/api/files/{other_file.id}/thumbnail', headers=headers)
            
            assert response.status_code == 404
            data = response.get_json()
            assert data['success'] is False
            assert 'not found' in data['message'].lower()
    
    @patch('os.path.exists')
    @patch('flask.send_file')
    def test_thumbnail_endpoint_serves_existing_thumbnail(self, mock_send_file, mock_exists, 
                                                         client, app, sample_resume_file, auth_token):
        """Test serving existing thumbnail file"""
        with app.app_context():
            # Re-attach file to session to access id
            file = db.session.merge(sample_resume_file)
            mock_exists.return_value = True
            mock_send_file.return_value = MagicMock()
            
            headers = {'Authorization': f'Bearer {auth_token}'}
            
            response = client.get(f'/api/files/{file.id}/thumbnail', headers=headers)
            
            # The actual response will be mocked, but we can verify the call
            mock_send_file.assert_called_once()
            call_args = mock_send_file.call_args
            
            # Verify correct parameters
            assert call_args[1]['mimetype'] == 'image/jpeg'
            assert call_args[1]['as_attachment'] is False
            assert call_args[1]['max_age'] == 86400  # 24 hours cache
    
    @patch('os.path.exists')
    @patch('flask.send_file')
    def test_thumbnail_endpoint_serves_default_when_missing(self, mock_send_file, mock_exists,
                                                           client, app, sample_resume_file_no_thumbnail, auth_token):
        """Test serving default thumbnail when file thumbnail is missing"""
        with app.app_context():
            # Mock that thumbnail doesn't exist but default does
            def exists_side_effect(path):
                if 'default_thumbnail.jpg' in path:
                    return True
                return False
            
            mock_exists.side_effect = exists_side_effect
            mock_send_file.return_value = MagicMock()
            
            # Re-attach file to session to access id
            file = db.session.merge(sample_resume_file_no_thumbnail)
            headers = {'Authorization': f'Bearer {auth_token}'}
            
            response = client.get(f'/api/files/{file.id}/thumbnail', headers=headers)
            
            # Should serve default thumbnail
            mock_send_file.assert_called_once()
            call_args = mock_send_file.call_args
            
            # Verify it's serving the default thumbnail
            assert 'default_thumbnail.jpg' in str(call_args[0][0])
            assert call_args[1]['mimetype'] == 'image/jpeg'
    
    def test_thumbnail_endpoint_404_when_no_default(self, client, app, sample_resume_file_no_thumbnail, auth_token):
        """Test 404 response when neither thumbnail nor default exists"""
        with app.app_context():
            with patch('os.path.exists', return_value=False):
                # Re-attach file to session to access id
                file = db.session.merge(sample_resume_file_no_thumbnail)
                headers = {'Authorization': f'Bearer {auth_token}'}
                
                response = client.get(f'/api/files/{file.id}/thumbnail', headers=headers)
                
                assert response.status_code == 404
                data = response.get_json()
                assert data['success'] is False
                assert 'not available' in data['message'].lower()
    
    def test_thumbnail_endpoint_invalid_file_id(self, client, app, auth_token):
        """Test thumbnail endpoint with invalid file ID"""
        with app.app_context():
            headers = {'Authorization': f'Bearer {auth_token}'}
            
            # Test with non-integer ID
            response = client.get('/api/files/invalid/thumbnail', headers=headers)
            assert response.status_code == 404  # Route not found
            
            # Test with non-existent ID
            response = client.get('/api/files/99999/thumbnail', headers=headers)
            assert response.status_code == 404
            data = response.get_json()
            assert data['success'] is False
    
    def test_thumbnail_generation_during_upload(self, client, app, sample_user, auth_token):
        """Test that thumbnails are generated during file upload"""
        with app.app_context():
            with patch('app.services.thumbnail_service.ThumbnailService.generate_thumbnail') as mock_generate:
                with patch('app.services.thumbnail_service.ThumbnailService.ensure_thumbnail_directory'):
                    mock_generate.return_value = True
                    
                    # Create a mock PDF file
                    pdf_data = b'%PDF-1.4 mock pdf content'
                    pdf_file = (BytesIO(pdf_data), 'test_upload.pdf')
                    
                    headers = {'Authorization': f'Bearer {auth_token}'}
                    
                    response = client.post(
                        '/api/files/upload',
                        data={'file': pdf_file},
                        headers=headers,
                        content_type='multipart/form-data'
                    )
                    
                    # Note: This test would need more setup to work with the full upload workflow
                    # For now, we're testing the concept
                    # In a real scenario, you'd need to mock the entire file storage and processing pipeline
    
    def test_file_info_backwards_compatibility(self, client, app, sample_resume_file, auth_token):
        """Test that adding thumbnail info doesn't break existing functionality"""
        with app.app_context():
            # Re-attach file to session to access id
            file = db.session.merge(sample_resume_file)
            headers = {'Authorization': f'Bearer {auth_token}'}
            
            response = client.get(f'/api/files/{file.id}/info', headers=headers)
            
            assert response.status_code == 200
            
            data = response.get_json()
            
            # Verify all existing fields are still present
            file_info = data['file']
            expected_fields = [
                'id', 'original_filename', 'stored_filename', 'file_size',
                'file_size_formatted', 'mime_type', 'storage_type',
                'processing_status', 'is_processed', 'tags', 'is_active',
                'created_at', 'updated_at'
            ]
            
            for field in expected_fields:
                assert field in file_info, f"Field {field} missing from response"
            
            # Verify new thumbnail field is present
            assert 'thumbnail' in file_info
            
            # Verify thumbnail object structure
            thumbnail = file_info['thumbnail']
            thumbnail_fields = ['has_thumbnail', 'thumbnail_url', 'thumbnail_status', 'thumbnail_generated_at']
            
            for field in thumbnail_fields:
                assert field in thumbnail, f"Thumbnail field {field} missing"
    
    def test_thumbnail_cache_headers(self, client, app, sample_resume_file, auth_token):
        """Test that thumbnail endpoint returns proper cache headers"""
        with app.app_context():
            with patch('os.path.exists', return_value=True):
                with patch('flask.send_file') as mock_send_file:
                    mock_response = MagicMock()
                    mock_response.headers = {}
                    mock_send_file.return_value = mock_response
                    
                    # Re-attach file to session to access id
                    file = db.session.merge(sample_resume_file)
                    headers = {'Authorization': f'Bearer {auth_token}'}
                    
                    response = client.get(f'/api/files/{file.id}/thumbnail', headers=headers)
                    
                    # Verify send_file was called with correct cache settings
                    mock_send_file.assert_called_once()
                    call_args = mock_send_file.call_args
                    assert call_args[1]['max_age'] == 86400  # 24 hours


if __name__ == '__main__':
    pytest.main([__file__, '-v'])