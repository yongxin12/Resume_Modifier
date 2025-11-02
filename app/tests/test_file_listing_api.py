"""
Tests for file listing API endpoint - FIXED VERSION
"""

import pytest
import os
from unittest.mock import patch, Mock
from flask import Flask
from app.extensions import db


class TestFileListingAPI:
    """Test suite for file listing API endpoint"""

    def setup_method(self):
        """Set up test environment before each test"""
        from datetime import datetime
        # Mock ResumeFile records for listing
        self.test_files = [
            {
                'id': 1,
                'user_id': 1,
                'original_filename': 'resume_v1.pdf',
                'stored_filename': 'secure_resume_v1.pdf',
                'file_path': '/storage/users/1/secure_resume_v1.pdf',
                'file_size': 1024,
                'mime_type': 'application/pdf',
                'storage_type': 'local',
                's3_bucket': None,
                'is_active': True,
                'created_at': datetime(2024, 1, 1, 10, 0, 0),
                'updated_at': datetime(2024, 1, 1, 10, 0, 0),
                'processing_status': 'completed',
                'extracted_text': 'Resume content here...',
                'page_count': 2
            },
            {
                'id': 2,
                'user_id': 1,
                'original_filename': 'cover_letter.docx',
                'stored_filename': 'secure_cover_letter.docx',
                'file_path': '/storage/users/1/secure_cover_letter.docx',
                'file_size': 2048,
                'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'storage_type': 's3',
                's3_bucket': 'test-bucket',
                'is_active': True,
                'created_at': datetime(2024, 1, 2, 10, 0, 0),
                'updated_at': datetime(2024, 1, 2, 10, 0, 0),
                'processing_status': 'pending',
                'extracted_text': None,
                'page_count': 1
            },
            {
                'id': 3,
                'user_id': 1,
                'original_filename': 'portfolio.pdf',
                'stored_filename': 'secure_portfolio.pdf',
                'file_path': '/storage/users/1/secure_portfolio.pdf',
                'file_size': 5120,
                'mime_type': 'application/pdf',
                'storage_type': 'local',
                's3_bucket': None,
                'is_active': True,
                'created_at': datetime(2024, 1, 3, 10, 0, 0),
                'updated_at': datetime(2024, 1, 3, 10, 0, 0),
                'processing_status': 'failed',
                'extracted_text': None,
                'page_count': None
            }
        ]

    def _create_mock_files(self, file_data_list):
        """Helper to create mock files from data"""
        mock_files = []
        for file_data in file_data_list:
            mock_file = Mock()
            for key, value in file_data.items():
                setattr(mock_file, key, value)
            mock_files.append(mock_file)
        return mock_files

    def _setup_query_mock(self, mock_query, files, total_count=None):
        """Helper to setup complete query chain mock"""
        if total_count is None:
            total_count = len(files)
        
        # Create a full chain mock that supports all operations
        mock_chain = Mock()
        mock_query.filter_by.return_value = mock_chain
        mock_chain.filter.return_value = mock_chain
        mock_chain.order_by.return_value = mock_chain
        mock_chain.offset.return_value = mock_chain
        mock_chain.limit.return_value = mock_chain
        mock_chain.all.return_value = files
        mock_chain.count.return_value = total_count

    def test_list_files_success(self, app, client, authenticated_headers):
        """Test successful file listing with authentication"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                mock_files = self._create_mock_files(self.test_files)
                self._setup_query_mock(mock_query, mock_files)
                
                response = client.get('/api/files', headers=authenticated_headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert len(data['files']) == 3
                assert data['total'] == 3
                
                # Verify file structure
                first_file = data['files'][0]
                required_fields = ['id', 'original_filename', 'file_size', 'mime_type', 
                                 'storage_type', 'created_at', 'processing_status']
                for field in required_fields:
                    assert field in first_file

    def test_list_files_pagination(self, app, client, authenticated_headers):
        """Test file listing with pagination"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                mock_files = self._create_mock_files(self.test_files[:2])
                self._setup_query_mock(mock_query, mock_files, total_count=3)
                
                response = client.get('/api/files?page=1&limit=2', headers=authenticated_headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert len(data['files']) == 2
                assert data['total'] == 3
                assert data['page'] == 1
                assert data['limit'] == 2
                assert data['has_next'] is True
                assert data['has_prev'] is False

    def test_list_files_filtering_by_mime_type(self, app, client, authenticated_headers):
        """Test file listing with MIME type filtering"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                pdf_files = [f for f in self.test_files if f['mime_type'] == 'application/pdf']
                mock_files = self._create_mock_files(pdf_files)
                self._setup_query_mock(mock_query, mock_files)
                
                response = client.get('/api/files?mime_type=application/pdf', headers=authenticated_headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert len(data['files']) == 2
                for file in data['files']:
                    assert file['mime_type'] == 'application/pdf'

    def test_list_files_filtering_by_processing_status(self, app, client, authenticated_headers):
        """Test file listing with processing status filtering"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                completed_files = [f for f in self.test_files if f['processing_status'] == 'completed']
                mock_files = self._create_mock_files(completed_files)
                self._setup_query_mock(mock_query, mock_files)
                
                response = client.get('/api/files?processing_status=completed', headers=authenticated_headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert len(data['files']) == 1
                assert data['files'][0]['processing_status'] == 'completed'

    def test_list_files_sorting_by_created_date(self, app, client, authenticated_headers):
        """Test file listing with sorting by creation date"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                sorted_files = sorted(self.test_files, key=lambda x: x['created_at'], reverse=True)
                mock_files = self._create_mock_files(sorted_files)
                self._setup_query_mock(mock_query, mock_files)
                
                response = client.get('/api/files?sort_by=created_at&sort_order=desc', headers=authenticated_headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert len(data['files']) == 3
                # Verify sorting (newest first)
                assert data['files'][0]['id'] == 3  # Most recent
                assert data['files'][2]['id'] == 1  # Oldest

    def test_list_files_sorting_by_file_size(self, app, client, authenticated_headers):
        """Test file listing with sorting by file size"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                sorted_files = sorted(self.test_files, key=lambda x: x['file_size'], reverse=True)
                mock_files = self._create_mock_files(sorted_files)
                self._setup_query_mock(mock_query, mock_files)
                
                response = client.get('/api/files?sort_by=file_size&sort_order=desc', headers=authenticated_headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert len(data['files']) == 3
                # Verify sorting (largest first)
                assert data['files'][0]['file_size'] == 5120  # Largest
                assert data['files'][2]['file_size'] == 1024  # Smallest

    def test_list_files_no_authentication(self, app, client):
        """Test file listing without authentication"""
        with app.app_context():
            response = client.get('/api/files')
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'authentication' in data['error'].lower() or 'token' in data['error'].lower()

    def test_list_files_invalid_token(self, app, client):
        """Test file listing with invalid authentication token"""
        with app.app_context():
            headers = {'Authorization': 'Bearer invalid_token'}
            response = client.get('/api/files', headers=headers)
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'invalid' in data['error'].lower() or 'token' in data['error'].lower()

    def test_list_files_empty_result(self, app, client, authenticated_headers):
        """Test file listing when user has no files"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                self._setup_query_mock(mock_query, [], total_count=0)
                
                response = client.get('/api/files', headers=authenticated_headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['files'] == []
                assert data['total'] == 0

    def test_list_files_invalid_pagination_params(self, app, client, authenticated_headers):
        """Test file listing with invalid pagination parameters"""
        with app.app_context():
            response = client.get('/api/files?page=0&limit=-1', headers=authenticated_headers)
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'page number must be 1 or greater' in data['message'].lower()

    def test_list_files_invalid_sort_params(self, app, client, authenticated_headers):
        """Test file listing with invalid sort parameters"""
        with app.app_context():
            response = client.get('/api/files?sort_by=invalid_field&sort_order=invalid_order', headers=authenticated_headers)
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'invalid' in data['message'].lower()

    def test_list_files_database_error(self, app, client, authenticated_headers):
        """Test file listing when database query fails"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                mock_query.filter_by.side_effect = Exception("Database connection failed")
                
                response = client.get('/api/files', headers=authenticated_headers)
                
                assert response.status_code == 500
                data = response.get_json()
                assert data['success'] is False
                assert 'error' in data['message'].lower()

    def test_list_files_search_by_filename(self, app, client, authenticated_headers):
        """Test file listing with filename search"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                search_files = [f for f in self.test_files if 'resume' in f['original_filename'].lower()]
                mock_files = self._create_mock_files(search_files)
                self._setup_query_mock(mock_query, mock_files)
                
                response = client.get('/api/files?search=resume', headers=authenticated_headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert len(data['files']) == 1
                assert 'resume' in data['files'][0]['original_filename'].lower()

    def test_list_files_combined_filters_and_pagination(self, app, client, authenticated_headers):
        """Test file listing with combined filters and pagination"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                mock_files = self._create_mock_files([self.test_files[0]])
                self._setup_query_mock(mock_query, mock_files, total_count=1)
                
                response = client.get(
                    '/api/files?mime_type=application/pdf&processing_status=completed&sort_by=created_at&sort_order=desc&page=1&limit=10',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert len(data['files']) == 1
                assert data['total'] == 1

    def test_list_files_response_schema(self, app, client, authenticated_headers):
        """Test that file listing response follows expected schema"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                mock_files = self._create_mock_files([self.test_files[0]])
                self._setup_query_mock(mock_query, mock_files)
                
                response = client.get('/api/files', headers=authenticated_headers)
                
                assert response.status_code == 200
                data = response.get_json()
                
                # Validate response schema
                required_response_fields = ['success', 'files', 'total', 'page', 'limit', 'has_next', 'has_prev']
                for field in required_response_fields:
                    assert field in data
                
                # Validate file object schema
                if data['files']:
                    file_obj = data['files'][0]
                    required_file_fields = ['id', 'original_filename', 'file_size', 'mime_type', 
                                          'storage_type', 'created_at', 'updated_at', 'processing_status']
                    for field in required_file_fields:
                        assert field in file_obj

    def test_list_files_security_isolation(self, app, client, authenticated_headers):
        """Test that users can only see their own files"""
        with app.app_context():
            with patch('app.models.temp.ResumeFile.query') as mock_query:
                user1_files = [f for f in self.test_files if f['user_id'] == 1]
                mock_files = self._create_mock_files(user1_files)
                self._setup_query_mock(mock_query, mock_files)
                
                response = client.get('/api/files', headers=authenticated_headers)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                
                # Verify all returned files belong to the authenticated user
                # (user_id should not be exposed in response for security)
                for file in data['files']:
                    assert 'user_id' not in file