"""
Test suite for ResumeFile model

Following TDD approach - tests written first, then implementation
"""
import pytest
from datetime import datetime
from app.extensions import db
from app.models.temp import User, ResumeFile


class TestResumeFileModel:
    """Test ResumeFile model functionality"""
    
    def test_resume_file_creation(self, app, client):
        """Test basic ResumeFile model creation and database persistence."""
        with app.app_context():
            # Create a test user first
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
            
            # Create a ResumeFile instance
            resume_file = ResumeFile(
                user_id=user.id,
                original_filename='test_resume.pdf',
                stored_filename='uuid_generated_filename.pdf',
                file_size=1024000,  # 1MB
                mime_type='application/pdf',
                storage_type='local',
                file_path='/uploads/test/uuid_generated_filename.pdf',
                file_hash='abcd1234567890efgh',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add to database
            db.session.add(resume_file)
            db.session.commit()
            
            # Verify the instance was created and persisted
            assert resume_file.id is not None
            assert resume_file.original_filename == 'test_resume.pdf'
            assert resume_file.stored_filename == 'uuid_generated_filename.pdf'
            assert resume_file.file_size == 1024000
            assert resume_file.mime_type == 'application/pdf'
            assert resume_file.storage_type == 'local'
            assert resume_file.file_path == '/uploads/test/uuid_generated_filename.pdf'
            assert resume_file.file_hash == 'abcd1234567890efgh'
            assert resume_file.user_id == user.id
            
            # Verify it can be retrieved from database
            retrieved_file = db.session.get(ResumeFile, resume_file.id)
            assert retrieved_file is not None
            assert retrieved_file.original_filename == 'test_resume.pdf'
            assert retrieved_file.user_id == user.id
    
    def test_resume_file_user_relationship(self, app, client):
        """Test the relationship between ResumeFile and User models."""
        with app.app_context():
            # Create a test user
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
            
            # Create multiple ResumeFile instances for the user
            file1 = ResumeFile(
                user_id=user.id,
                original_filename='resume1.pdf',
                stored_filename='file1.pdf',
                file_size=500000,
                mime_type='application/pdf',
                storage_type='local',
                file_path='/uploads/file1.pdf',
                file_hash='hash1',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            file2 = ResumeFile(
                user_id=user.id,
                original_filename='resume2.docx',
                stored_filename='file2.docx',
                file_size=750000,
                mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                storage_type='local',
                file_path='/uploads/file2.docx',
                file_hash='hash2',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add_all([file1, file2])
            db.session.commit()
            
            # Test the relationship from user side
            user_files = user.resume_files.all()
            assert len(user_files) == 2
            assert file1 in user_files
            assert file2 in user_files
            
            # Test the relationship from file side
            assert file1.user == user
            assert file2.user == user
            assert file1.user.username == 'testuser'
            assert file2.user.email == 'test@test.com'
    
    def test_resume_file_to_dict_method(self, app, client):
        """Test the to_dict method for JSON serialization"""
        with app.app_context():
            # Create test user
            user = User(
                username='testuser3',
                email='test3@example.com',
                password='hashed_password', 
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
            
            # Create ResumeFile
            resume_file = ResumeFile(
                user_id=user.id,
                original_filename='resume3.docx',
                stored_filename='stored_resume3.docx',
                file_size=750000,
                mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                storage_type='s3',
                file_path='3/resumes/ghi789/resume3.docx',
                s3_bucket='my-resume-bucket',
                file_hash='ghi789',
                extracted_text='Jane Smith\nProduct Manager with 3 years experience...',
                processing_status='completed',
                is_processed=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(resume_file)
            db.session.commit()
            
            # Test to_dict without text
            result = resume_file.to_dict()
            
            expected_keys = {
                # Core fields from the model
                'id', 'user_id', 'original_filename', 'stored_filename', 'file_size', 'file_size_formatted',
                'mime_type', 'storage_type', 'file_path', 's3_bucket', 'file_hash', 'is_processed',
                'extracted_text', 'processing_status', 'processing_error', 'tags', 'is_active',
                'created_at', 'updated_at',
                # Category fields (included by default)
                'category', 'category_updated_at', 'category_updated_by',
                # Google Drive and duplicate info (included by default)
                'google_drive', 'duplicate_info'
            }
            
            assert set(result.keys()) == expected_keys
            assert result['original_filename'] == 'resume3.docx'
            assert result['storage_type'] == 's3'
            assert result['file_size_formatted'] == '732.4 KB'
            assert result['extracted_text'] == 'Jane Smith\nProduct Manager with 3 years experience...'
    
    def test_resume_file_format_file_size(self, app, client):
        """Test file size formatting utility method"""
        with app.app_context():
            # Create test user
            user = User(
                username='testuser4',
                email='test4@example.com',
                password='hashed_password',
                created_at=datetime.utcnow(), 
                updated_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
            
            # Test different file sizes
            test_cases = [
                (500, '500 B'),
                (1024, '1.0 KB'),
                (1536, '1.5 KB'),  # 1.5KB 
                (1048576, '1.0 MB'),
                (1073741824, '1.0 GB'),
                (1099511627776, '1.0 TB')
            ]
            
            for size_bytes, expected_format in test_cases:
                resume_file = ResumeFile(
                    user_id=user.id,
                    original_filename=f'test_{size_bytes}.pdf',
                    stored_filename=f'stored_{size_bytes}.pdf',
                    file_size=size_bytes,
                    mime_type='application/pdf',
                    storage_type='local',
                    file_path=f'{user.id}/resumes/test_{size_bytes}/test.pdf',
                    file_hash=f'hash_{size_bytes}',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                formatted_size = resume_file.format_file_size()
                assert formatted_size == expected_format
    
    def test_resume_file_defaults(self, app, client):
        """Test default values for ResumeFile fields"""
        with app.app_context():
            # Create test user
            user = User(
                username='testuser5',
                email='test5@example.com',
                password='hashed_password',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
            
            # Create ResumeFile with minimal required fields
            resume_file = ResumeFile(
                user_id=user.id,
                original_filename='minimal.pdf',
                stored_filename='stored_minimal.pdf',
                file_size=1000,
                mime_type='application/pdf',
                storage_type='local',
                file_path='test/path/minimal.pdf',
                file_hash='minimal_hash'
            )
            
            db.session.add(resume_file)
            db.session.commit()
            
            # Test defaults
            assert resume_file.storage_type == 'local'
            assert resume_file.processing_status == 'pending'
            assert resume_file.is_processed is False
            assert resume_file.extracted_text is None
            assert resume_file.is_active is True
            assert resume_file.tags == []
            assert resume_file.created_at is not None
            assert resume_file.updated_at is not None
    
    def test_resume_file_repr(self, app, client):
        """Test string representation of ResumeFile"""
        with app.app_context():
            # Create test user
            user = User(
                username='testuser6',
                email='test6@example.com',
                password='hashed_password',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
            
            # Create ResumeFile
            resume_file = ResumeFile(
                user_id=user.id,
                original_filename='repr_test.pdf',
                stored_filename='stored_repr_test.pdf',
                file_size=1000,
                mime_type='application/pdf',
                storage_type='local',
                file_path='test/repr.pdf',
                file_hash='repr_hash',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(resume_file)
            db.session.commit()
            
            # Test repr
            repr_str = repr(resume_file)
            assert 'ResumeFile' in repr_str
            assert 'repr_test.pdf' in repr_str
    
    def test_resume_file_constraints(self, app, client):
        """Test database constraints and validations"""
        with app.app_context():
            # Create test user
            user = User(
                username='testuser7',
                email='test7@example.com',
                password='hashed_password',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
            
            # Test required fields - should work with all required fields
            resume_file = ResumeFile(
                user_id=user.id, 
                original_filename='constraint_test.pdf',
                stored_filename='stored_constraint_test.pdf',
                file_size=1000,
                mime_type='application/pdf',
                storage_type='local',
                file_path='test/constraint.pdf',
                file_hash='constraint_hash',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(resume_file)
            db.session.commit()
            
            # Verify the record was created successfully
            assert resume_file.id is not None
            assert resume_file.user_id == user.id
            assert resume_file.file_size == 1000