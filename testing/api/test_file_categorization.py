"""
Test Suite for File Categorization System
Comprehensive tests using TDD approach for file category management
"""

import pytest
import json
from datetime import datetime
from flask import Flask
from flask_testing import TestCase
from unittest.mock import Mock, patch, MagicMock
from app.models.temp import ResumeFile, User, db
from app.services.file_category_service import FileCategoryService
from app.utils.error_handler import FileManagementError, ErrorCode


class FileCategoryModelTest(TestCase):
    """Test ResumeFile model category functionality."""
    
    def create_app(self):
        """Create test Flask app."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        # Initialize db with this Flask app
        db.init_app(app)
        return app
    
    def setUp(self):
        """Set up test database and sample data."""
        db.create_all()
        
        # Create test user
        self.test_user = User(
            username='testuser',
            email='test@example.com',
            password='hashed_password',
            first_name='Test',
            last_name='User',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(self.test_user)
        db.session.commit()
        
        # Create test files
        self.test_file_active = ResumeFile(
            user_id=self.test_user.id,
            original_filename='resume_active.pdf',
            stored_filename='stored_active.pdf',
            file_size=1024,
            mime_type='application/pdf',
            storage_type='local',
            file_path='/path/to/active',
            file_hash='hash_active',
            category='active',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.test_file_draft = ResumeFile(
            user_id=self.test_user.id,
            original_filename='resume_draft.pdf',
            stored_filename='stored_draft.pdf',
            file_size=2048,
            mime_type='application/pdf',
            storage_type='local',
            file_path='/path/to/draft',
            file_hash='hash_draft',
            category='draft',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add_all([self.test_file_active, self.test_file_draft])
        db.session.commit()
    
    def tearDown(self):
        """Clean up test database."""
        db.session.remove()
        db.drop_all()
    
    # Model Tests
    def test_default_category_is_active(self):
        """Test that new files default to 'active' category after saving to database."""
        new_file = ResumeFile(
            user_id=self.test_user.id,
            original_filename='new_file.pdf',
            stored_filename='stored_new.pdf',
            file_size=512,
            mime_type='application/pdf',
            storage_type='local',
            file_path='/path/to/new',
            file_hash='hash_new',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        # Add to session and commit to trigger database defaults
        db.session.add(new_file)
        db.session.commit()
        
        self.assertEqual(new_file.category, 'active')
    
    def test_update_category_success(self):
        """Test successful category update."""
        original_category = self.test_file_active.category
        result = self.test_file_active.update_category('archived', self.test_user.id)
        
        self.assertTrue(result)
        self.assertEqual(self.test_file_active.category, 'archived')
        self.assertIsNotNone(self.test_file_active.category_updated_at)
        self.assertEqual(self.test_file_active.category_updated_by, self.test_user.id)
    
    def test_update_category_invalid(self):
        """Test category update with invalid category."""
        result = self.test_file_active.update_category('invalid_category', self.test_user.id)
        
        self.assertFalse(result)
        self.assertEqual(self.test_file_active.category, 'active')  # Should remain unchanged
    
    def test_update_category_same_value(self):
        """Test updating to same category value."""
        result = self.test_file_active.update_category('active', self.test_user.id)
        
        self.assertTrue(result)
        # Should not update timestamp if category didn't actually change
    
    def test_get_files_by_category(self):
        """Test filtering files by category."""
        # Test specific category
        active_files = ResumeFile.get_files_by_category(self.test_user.id, 'active').all()
        self.assertEqual(len(active_files), 1)
        self.assertEqual(active_files[0].category, 'active')
        
        draft_files = ResumeFile.get_files_by_category(self.test_user.id, 'draft').all()
        self.assertEqual(len(draft_files), 1)
        self.assertEqual(draft_files[0].category, 'draft')
        
        # Test all categories
        all_files = ResumeFile.get_files_by_category(self.test_user.id, None).all()
        self.assertEqual(len(all_files), 2)
        
        # Test non-existent category
        archived_files = ResumeFile.get_files_by_category(self.test_user.id, 'archived').all()
        self.assertEqual(len(archived_files), 0)
    
    def test_get_category_statistics(self):
        """Test category statistics calculation."""
        stats = ResumeFile.get_category_statistics(self.test_user.id)
        
        self.assertIn('categories', stats)
        self.assertIn('total_files', stats)
        self.assertIn('total_active_files', stats)
        
        # Check category counts
        self.assertEqual(stats['categories']['active']['count'], 1)
        self.assertEqual(stats['categories']['draft']['count'], 1)
        self.assertEqual(stats['categories']['archived']['count'], 0)
        
        # Check percentages
        self.assertEqual(stats['categories']['active']['percentage'], 50.0)
        self.assertEqual(stats['categories']['draft']['percentage'], 50.0)
        self.assertEqual(stats['categories']['archived']['percentage'], 0.0)
        
        # Check totals
        self.assertEqual(stats['total_active_files'], 2)
    
    def test_bulk_update_category(self):
        """Test bulk category update."""
        file_ids = [self.test_file_active.id, self.test_file_draft.id]
        
        result = ResumeFile.bulk_update_category(
            self.test_user.id, file_ids, 'archived', self.test_user.id
        )
        
        self.assertEqual(result['successful_updates'], 2)
        self.assertEqual(result['failed_updates'], 0)
        self.assertEqual(len(result['updated_files']), 2)
        
        # Commit the changes made by bulk_update_category
        db.session.commit()
        
        # Verify files were updated
        db.session.refresh(self.test_file_active)
        db.session.refresh(self.test_file_draft)
        
        self.assertEqual(self.test_file_active.category, 'archived')
        self.assertEqual(self.test_file_draft.category, 'archived')
    
    def test_bulk_update_category_invalid(self):
        """Test bulk update with invalid category."""
        file_ids = [self.test_file_active.id]
        
        result = ResumeFile.bulk_update_category(
            self.test_user.id, file_ids, 'invalid', self.test_user.id
        )
        
        self.assertEqual(result['successful_updates'], 0)
        self.assertEqual(result['failed_updates'], 1)
        self.assertIn('error', result)
    
    def test_to_dict_includes_category(self):
        """Test that to_dict includes category information."""
        file_dict = self.test_file_active.to_dict()
        
        self.assertIn('category', file_dict)
        self.assertEqual(file_dict['category'], 'active')
        self.assertIn('category_updated_at', file_dict)
        self.assertIn('category_updated_by', file_dict)


class FileCategoryServiceTest(TestCase):
    """Test FileCategoryService business logic."""
    
    def create_app(self):
        """Create test Flask app."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        # Initialize db with this Flask app
        db.init_app(app)
        return app
    
    def setUp(self):
        """Set up test data."""
        db.create_all()
        
        self.test_user = User(
            username='testuser',
            email='test@example.com',
            password='hashed_password',
            first_name='Test',
            last_name='User',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(self.test_user)
        db.session.commit()
        
        self.test_file = ResumeFile(
            user_id=self.test_user.id,
            original_filename='test_file.pdf',
            stored_filename='stored_test.pdf',
            file_size=1024,
            mime_type='application/pdf',
            storage_type='local',
            file_path='/path/to/test',
            file_hash='hash_test',
            category='active',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(self.test_file)
        db.session.commit()
    
    def tearDown(self):
        """Clean up test database."""
        db.session.remove()
        db.drop_all()
    
    def test_validate_category_valid(self):
        """Test category validation with valid categories."""
        valid_categories = ['active', 'archived', 'draft']
        for category in valid_categories:
            self.assertTrue(FileCategoryService.validate_category(category))
    
    def test_validate_category_invalid(self):
        """Test category validation with invalid categories."""
        invalid_categories = ['invalid', 'ACTIVE', '', None, 123]
        for category in invalid_categories:
            self.assertFalse(FileCategoryService.validate_category(category))
    
    def test_update_file_category_success(self):
        """Test successful file category update."""
        result = FileCategoryService.update_file_category(
            self.test_file.id, self.test_user.id, 'archived'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('file', result)
        self.assertEqual(result['file']['category'], 'archived')
    
    def test_update_file_category_invalid_category(self):
        """Test file category update with invalid category."""
        with self.assertRaises(FileManagementError) as context:
            FileCategoryService.update_file_category(
                self.test_file.id, self.test_user.id, 'invalid'
            )
        
        self.assertEqual(context.exception.error_detail.code, ErrorCode.INVALID_REQUEST)
    
    def test_update_file_category_file_not_found(self):
        """Test file category update with non-existent file."""
        with self.assertRaises(FileManagementError) as context:
            FileCategoryService.update_file_category(
                99999, self.test_user.id, 'archived'
            )
        
        self.assertEqual(context.exception.error_detail.code, ErrorCode.RECORD_NOT_FOUND)
    
    def test_bulk_update_categories_success(self):
        """Test successful bulk category update."""
        result = FileCategoryService.bulk_update_categories(
            [self.test_file.id], self.test_user.id, 'draft'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['summary']['successful_updates'], 1)
        self.assertEqual(result['summary']['failed_updates'], 0)
    
    def test_bulk_update_categories_empty_list(self):
        """Test bulk update with empty file list."""
        with self.assertRaises(FileManagementError) as context:
            FileCategoryService.bulk_update_categories(
                [], self.test_user.id, 'archived'
            )
        
        self.assertEqual(context.exception.error_detail.code, ErrorCode.INVALID_REQUEST)
    
    def test_get_files_by_category_filtering(self):
        """Test file retrieval with category filtering."""
        result = FileCategoryService.get_files_by_category(
            self.test_user.id, 'active'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']['files']), 1)
        self.assertEqual(result['data']['files'][0]['category'], 'active')
    
    def test_get_files_by_category_invalid_category(self):
        """Test file retrieval with invalid category."""
        with self.assertRaises(FileManagementError) as context:
            FileCategoryService.get_files_by_category(
                self.test_user.id, 'invalid'
            )
        
        self.assertEqual(context.exception.error_detail.code, ErrorCode.INVALID_REQUEST)
    
    def test_get_category_statistics_success(self):
        """Test category statistics retrieval."""
        result = FileCategoryService.get_category_statistics(self.test_user.id)
        
        self.assertTrue(result['success'])
        self.assertIn('statistics', result)
        self.assertIn('categories', result['statistics'])
    
    def test_set_default_category_for_upload(self):
        """Test setting default category for new upload."""
        new_file = ResumeFile(
            user_id=self.test_user.id,
            original_filename='new_upload.pdf',
            stored_filename='stored_upload.pdf',
            file_size=512,
            mime_type='application/pdf',
            storage_type='local',
            file_path='/path/to/upload',
            file_hash='hash_upload',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        # Clear category to simulate fresh upload
        new_file.category = None
        
        FileCategoryService.set_default_category_for_upload(new_file, self.test_user.id)
        
        self.assertEqual(new_file.category, 'active')
        self.assertIsNotNone(new_file.category_updated_at)
        self.assertEqual(new_file.category_updated_by, self.test_user.id)
    
    def test_validate_category_access_success(self):
        """Test successful category access validation."""
        result = FileCategoryService.validate_category_access(
            self.test_file.id, self.test_user.id
        )
        
        self.assertTrue(result)
    
    def test_validate_category_access_denied(self):
        """Test category access validation denial."""
        # Create another user
        other_user = User(
            username='otheruser',
            email='other@example.com',
            password='hashed_password',
            first_name='Other',
            last_name='User',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(other_user)
        db.session.commit()
        
        result = FileCategoryService.validate_category_access(
            self.test_file.id, other_user.id
        )
        
        self.assertFalse(result)


class FileCategoryAPITest(TestCase):
    """Test file category API endpoints."""
    
    def create_app(self):
        """Create test Flask app with API endpoints."""
        from flask import Flask
        from app.api.file_category_endpoints import file_category_bp
        
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Initialize db with this Flask app
        db.init_app(app)
        app.register_blueprint(file_category_bp, url_prefix='/files')
        
        return app
    
    def setUp(self):
        """Set up test data and authentication."""
        db.create_all()
        
        self.test_user = User(
            username='testuser',
            email='test@example.com',
            password='hashed_password',
            first_name='Test',
            last_name='User',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(self.test_user)
        db.session.commit()
        
        self.test_file = ResumeFile(
            user_id=self.test_user.id,
            original_filename='api_test.pdf',
            stored_filename='stored_api_test.pdf',
            file_size=1024,
            mime_type='application/pdf',
            storage_type='local',
            file_path='/path/to/api_test',
            file_hash='hash_api_test',
            category='active',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(self.test_file)
        db.session.commit()
        
        # Mock token_required decorator by patching verify_token to return user data
        self.mock_payload = {'user_id': self.test_user.id, 'email': self.test_user.email}
        self.token_patcher = patch('app.utils.jwt_utils.verify_token', return_value=self.mock_payload)
        self.token_patcher.start()
        
        # Set up auth headers with dummy token
        self.auth_headers = {
            'Authorization': 'Bearer test_token',
            'Content-Type': 'application/json'
        }
    
    def tearDown(self):
        """Clean up test data and patches."""
        self.token_patcher.stop()
        db.session.remove()
        db.drop_all()
    
    def test_update_file_category_success(self):
        """Test successful single file category update via API."""
        response = self.client.put(
            f'/files/{self.test_file.id}/category',
            data=json.dumps({'category': 'archived'}),
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['file']['category'], 'archived')
    
    def test_update_file_category_invalid_json(self):
        """Test file category update with invalid JSON."""
        response = self.client.put(
            f'/files/{self.test_file.id}/category',
            data='invalid json',
            headers={'Authorization': 'Bearer test_token', 'Content-Type': 'text/plain'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_update_file_category_missing_category(self):
        """Test file category update with missing category field."""
        response = self.client.put(
            f'/files/{self.test_file.id}/category',
            data=json.dumps({}),
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('valid_categories', data)
    
    def test_bulk_update_categories_success(self):
        """Test successful bulk category update via API."""
        response = self.client.put(
            '/files/category',
            data=json.dumps({
                'file_ids': [self.test_file.id],
                'category': 'draft'
            }),
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['summary']['successful_updates'], 1)
    
    def test_bulk_update_categories_invalid_file_ids(self):
        """Test bulk update with invalid file IDs."""
        response = self.client.put(
            '/files/category',
            data=json.dumps({
                'file_ids': ['invalid'],
                'category': 'draft'
            }),
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_list_files_by_category(self):
        """Test file listing with category filtering."""
        response = self.client.get('/files/list?category=active', headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('files', data['data'])
    
    def test_get_category_statistics(self):
        """Test category statistics endpoint."""
        response = self.client.get('/files/categories/stats', headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('statistics', data)
    
    def test_get_available_categories(self):
        """Test available categories endpoint."""
        response = self.client.get('/files/categories', headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('categories', data)
        self.assertIn('valid_categories', data)
        self.assertIn('default_category', data)


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])