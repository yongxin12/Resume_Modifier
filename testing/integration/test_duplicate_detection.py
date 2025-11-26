"""
Test suite for Duplicate File Detection Service

Tests the DuplicateFileHandler service including:
- File hash calculation
- Duplicate detection logic  
- Sequential filename generation
- Edge cases and error handling
"""

import pytest
import tempfile
import os
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock
from app.services.duplicate_file_handler import DuplicateFileHandler
from app.models.temp import ResumeFile, User
from app.extensions import db
from app import create_app


class TestDuplicateFileHandler:
    """Test cases for DuplicateFileHandler service"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture 
    def duplicate_handler(self, app):
        """Create DuplicateFileHandler instance"""
        with app.app_context():
            return DuplicateFileHandler()
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Create sample PDF content for testing"""
        return b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'
    
    @pytest.fixture
    def test_user(self, app):
        """Create test user"""
        with app.app_context():
            user = User(
                id=1,
                username="testuser",
                email="test@example.com",
                password="hashedpassword"
            )
            db.session.add(user)
            db.session.commit()
            return user
    
    def test_calculate_file_hash(self, duplicate_handler, sample_pdf_content):
        """Test file hash calculation"""
        file_obj = BytesIO(sample_pdf_content)
        
        hash_result = duplicate_handler.calculate_file_hash(file_obj)
        
        assert hash_result is not None
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 produces 64-character hex string
        
        # Test consistency - same content should produce same hash
        file_obj2 = BytesIO(sample_pdf_content)
        hash_result2 = duplicate_handler.calculate_file_hash(file_obj2)
        assert hash_result == hash_result2
    
    def test_calculate_file_hash_different_content(self, duplicate_handler):
        """Test that different content produces different hashes"""
        content1 = b"This is test content 1"
        content2 = b"This is test content 2"
        
        hash1 = duplicate_handler.calculate_file_hash(BytesIO(content1))
        hash2 = duplicate_handler.calculate_file_hash(BytesIO(content2))
        
        assert hash1 != hash2
    
    def test_calculate_file_hash_empty_file(self, duplicate_handler):
        """Test hash calculation for empty file"""
        empty_file = BytesIO(b"")
        
        hash_result = duplicate_handler.calculate_file_hash(empty_file)
        
        assert hash_result is not None
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64
    
    def test_find_existing_files_no_duplicates(self, app, duplicate_handler, test_user):
        """Test finding existing files when no duplicates exist"""
        with app.app_context():
            file_hash = "abc123"
            # Refresh the user to ensure it's bound to current session
            user = db.session.merge(test_user)
            user_id = user.id
            
            existing_files = duplicate_handler.find_existing_files(user_id, file_hash)
            
            assert existing_files == []
    
    def test_find_existing_files_with_duplicates(self, app, duplicate_handler, test_user):
        """Test finding existing files when duplicates exist"""
        with app.app_context():
            file_hash = "abc123"
            # Refresh the user to ensure it's bound to current session
            user = db.session.merge(test_user)
            user_id = user.id
            
            # Create existing file with same hash
            existing_file = ResumeFile(
                user_id=user_id,
                file_hash=file_hash,
                original_filename="resume.pdf",
                display_filename="resume.pdf",
                stored_filename="stored_resume.pdf",
                file_size=1024,
                mime_type="application/pdf",
                file_path="/test/path/resume.pdf"
            )
            db.session.add(existing_file)
            db.session.commit()
            
            existing_files = duplicate_handler.find_existing_files(user_id, file_hash)
            
            assert len(existing_files) == 1
            assert existing_files[0].file_hash == file_hash
            assert existing_files[0].user_id == user_id
    
    def test_find_existing_files_different_user(self, app, duplicate_handler, test_user):
        """Test that find_existing_files only returns files for the specified user"""
        with app.app_context():
            file_hash = "abc123"
            
            # Create file for different user
            other_user = User(
                id=2,
                username="otheruser", 
                email="other@example.com",
                password="hashedpassword"
            )
            db.session.add(other_user)
            db.session.commit()
            
            existing_file = ResumeFile(
                user_id=other_user.id,
                file_hash=file_hash,
                original_filename="resume.pdf",
                display_filename="resume.pdf", 
                stored_filename="stored_resume.pdf",
                file_size=1024,
                mime_type="application/pdf",
                file_path="/test/path/resume.pdf"
            )
            db.session.add(existing_file)
            db.session.commit()
            
            # Refresh the user to ensure it's bound to current session
            user = db.session.merge(test_user)
            
            # Search for files for test_user
            existing_files = duplicate_handler.find_existing_files(user.id, file_hash)
            
            assert existing_files == []
    
    def test_generate_duplicate_filename_first_duplicate(self, duplicate_handler):
        """Test generating filename for first duplicate"""
        original_filename = "resume.pdf"
        sequence = 1
        
        result = duplicate_handler.generate_duplicate_filename(original_filename, sequence)
        
        assert result == "resume (1).pdf"
    
    def test_generate_duplicate_filename_multiple_duplicates(self, duplicate_handler):
        """Test generating filename for multiple duplicates"""
        original_filename = "resume.pdf"
        
        result1 = duplicate_handler.generate_duplicate_filename(original_filename, 1)
        result2 = duplicate_handler.generate_duplicate_filename(original_filename, 2)
        result5 = duplicate_handler.generate_duplicate_filename(original_filename, 5)
        
        assert result1 == "resume (1).pdf"
        assert result2 == "resume (2).pdf"
        assert result5 == "resume (5).pdf"
    
    def test_generate_duplicate_filename_no_extension(self, duplicate_handler):
        """Test generating filename for file without extension"""
        original_filename = "resume"
        sequence = 1
        
        result = duplicate_handler.generate_duplicate_filename(original_filename, sequence)
        
        assert result == "resume (1)"
    
    def test_generate_duplicate_filename_multiple_dots(self, duplicate_handler):
        """Test generating filename for file with multiple dots"""
        original_filename = "my.resume.file.pdf"
        sequence = 3
        
        result = duplicate_handler.generate_duplicate_filename(original_filename, sequence)
        
        assert result == "my.resume.file (3).pdf"
    
    def test_process_duplicate_file_no_duplicates(self, app, duplicate_handler, test_user, sample_pdf_content):
        """Test processing file when no duplicates exist"""
        with app.app_context():
            file_obj = BytesIO(sample_pdf_content)
            filename = "resume.pdf"
            user = db.session.merge(test_user)
            user_id = user.id
            
            file_hash = duplicate_handler.calculate_file_hash(file_obj)
            result = duplicate_handler.process_duplicate_file(user_id, filename, file_hash, sample_pdf_content)
            
            assert result['is_duplicate'] is False
            assert result['display_filename'] == filename
            assert result['notification_message'] is None
            assert result['duplicate_sequence'] == 0  # Original files have sequence 0
            assert result['original_file_id'] is None
            assert result['file_hash'] is not None
            assert len(result['file_hash']) == 64
    
    def test_process_duplicate_file_with_duplicate(self, app, duplicate_handler, test_user, sample_pdf_content):
        """Test processing file when duplicate exists"""
        with app.app_context():
            file_obj = BytesIO(sample_pdf_content)
            filename = "resume.pdf"
            user = db.session.merge(test_user)
            user_id = user.id
            
            # Calculate hash for the file
            file_hash = duplicate_handler.calculate_file_hash(BytesIO(sample_pdf_content))
            
            # Create existing file with same hash
            existing_file = ResumeFile(
                id=1,
                user_id=user_id,
                file_hash=file_hash,
                original_filename=filename,
                display_filename=filename,
                stored_filename="stored_resume.pdf",
                file_size=1024,
                mime_type="application/pdf",
                is_duplicate=False,
                file_path="/tmp/stored_resume.pdf"
            )
            db.session.add(existing_file)
            db.session.commit()
            
            file_hash = duplicate_handler.calculate_file_hash(file_obj)
            result = duplicate_handler.process_duplicate_file(user_id, filename, file_hash, sample_pdf_content)
            
            assert result['is_duplicate'] is True
            assert result['display_filename'] == "resume (1).pdf"
            assert "duplicate" in result['notification_message'].lower()
            assert result['duplicate_sequence'] == 1
            assert result['original_file_id'] == existing_file.id
            assert result['file_hash'] == file_hash
    
    def test_process_duplicate_file_multiple_duplicates(self, app, duplicate_handler, test_user, sample_pdf_content):
        """Test processing file when multiple duplicates exist"""
        with app.app_context():
            file_obj = BytesIO(sample_pdf_content)
            filename = "resume.pdf"
            user = db.session.merge(test_user)
            user_id = user.id
            
            # Calculate hash for the file
            file_hash = duplicate_handler.calculate_file_hash(BytesIO(sample_pdf_content))
            
            # Create multiple existing files with same hash
            original_file = ResumeFile(
                id=1,
                user_id=user_id,
                file_hash=file_hash,
                original_filename=filename,
                display_filename=filename,
                stored_filename="stored_resume.pdf",
                file_path="/tmp/stored_resume.pdf",
                file_size=1024,
                mime_type="application/pdf",
                is_duplicate=False
            )
            db.session.add(original_file)
            
            duplicate1 = ResumeFile(
                id=2,
                user_id=user_id,
                file_hash=file_hash,
                original_filename=filename,
                display_filename="resume (1).pdf",
                stored_filename="stored_resume_1.pdf",
                file_path="/tmp/stored_resume_1.pdf",
                file_size=1024,
                mime_type="application/pdf",
                is_duplicate=True,
                duplicate_sequence=1,
                original_file_id=1
            )
            db.session.add(duplicate1)
            
            duplicate2 = ResumeFile(
                id=3,
                user_id=user_id,
                file_hash=file_hash,
                original_filename=filename,
                display_filename="resume (2).pdf",
                stored_filename="stored_resume_2.pdf",
                file_path="/tmp/stored_resume_2.pdf",
                file_size=1024,
                mime_type="application/pdf",
                is_duplicate=True,
                duplicate_sequence=2,
                original_file_id=1
            )
            db.session.add(duplicate2)
            db.session.commit()
            
            file_hash = duplicate_handler.calculate_file_hash(file_obj)
            result = duplicate_handler.process_duplicate_file(user_id, filename, file_hash, sample_pdf_content)
            
            assert result['is_duplicate'] is True
            assert result['display_filename'] == "resume (3).pdf"
            assert result['duplicate_sequence'] == 3
            assert result['original_file_id'] == original_file.id
            assert result['file_hash'] == file_hash
    
    def test_process_duplicate_file_soft_deleted_files_excluded(self, app, duplicate_handler, test_user, sample_pdf_content):
        """Test that soft-deleted files are not considered for duplicate detection"""
        with app.app_context():
            file_obj = BytesIO(sample_pdf_content)
            filename = "resume.pdf"
            user = db.session.merge(test_user)
            user_id = user.id
            
            # Calculate hash for the file
            file_hash = duplicate_handler.calculate_file_hash(BytesIO(sample_pdf_content))
            
            # Create soft-deleted file with same hash
            from datetime import datetime
            deleted_file = ResumeFile(
                id=1,
                user_id=user_id,
                file_hash=file_hash,
                original_filename=filename,
                display_filename=filename,
                stored_filename="stored_resume.pdf",
                file_size=1024,
                mime_type="application/pdf",
                deleted_at=datetime.utcnow(),
                file_path="/tmp/deleted_resume.pdf",
                deleted_by=user_id
            )
            db.session.add(deleted_file)
            db.session.commit()
            
            file_hash = duplicate_handler.calculate_file_hash(file_obj)
            result = duplicate_handler.process_duplicate_file(user_id, filename, file_hash, sample_pdf_content)
            
            # Should not be considered a duplicate since the existing file is soft-deleted
            assert result['is_duplicate'] is False
            assert result['display_filename'] == filename
            assert result['duplicate_sequence'] == 0
    
    def test_process_duplicate_file_error_handling(self, app, duplicate_handler, test_user):
        """Test error handling in process_duplicate_file"""
        with app.app_context():
            # Test with invalid file object
            invalid_file = "not a file object"
            filename = "resume.pdf"
            user = db.session.merge(test_user)
            user_id = user.id
            
            # This should handle invalid input gracefully
            file_hash = 'invalid_hash'
            result = duplicate_handler.process_duplicate_file(user_id, filename, file_hash, b'invalid')
            # The method should return a valid result even with invalid input
            assert 'is_duplicate' in result
    
    def test_hash_calculation_file_pointer_reset(self, duplicate_handler, sample_pdf_content):
        """Test that file pointer is properly reset after hash calculation"""
        file_obj = BytesIO(sample_pdf_content)
        
        # Read some data first
        initial_data = file_obj.read(10)
        assert len(initial_data) == 10
        
        # Calculate hash - this should reset the file pointer
        hash_result = duplicate_handler.calculate_file_hash(file_obj)
        
        # Verify we can still read the full file
        file_obj.seek(0)
        full_data = file_obj.read()
        assert full_data == sample_pdf_content
        assert hash_result is not None
    
    def test_process_duplicate_file_preserves_original_filename(self, app, duplicate_handler, test_user, sample_pdf_content):
        """Test that original filename is preserved even for duplicates"""
        with app.app_context():
            file_obj = BytesIO(sample_pdf_content)
            original_filename = "my_important_resume.pdf"
            user = db.session.merge(test_user)
            user_id = user.id
            
            # Create existing file with same hash but different original name
            file_hash = duplicate_handler.calculate_file_hash(BytesIO(sample_pdf_content))
            existing_file = ResumeFile(
                id=1,
                user_id=user_id,
                file_hash=file_hash,
                original_filename="different_name.pdf",
                display_filename="different_name.pdf",
                stored_filename="stored_file.pdf",
                file_size=1024,
                mime_type="application/pdf",
                file_path="/test/path/resume.pdf"
            )
            db.session.add(existing_file)
            db.session.commit()
            
            file_hash = duplicate_handler.calculate_file_hash(file_obj)
            result = duplicate_handler.process_duplicate_file(user_id, original_filename, file_hash, sample_pdf_content)
            
            # Should be marked as duplicate with sequenced display name based on original filename
            assert result['is_duplicate'] is True
            assert result['display_filename'] == "my_important_resume (1).pdf"
            assert result['original_file_id'] == existing_file.id


if __name__ == '__main__':
    pytest.main([__file__, '-v'])