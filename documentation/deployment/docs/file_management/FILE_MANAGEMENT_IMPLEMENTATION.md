# 📋 File Management Feature - Implementation Guide

## Quick Reference

This guide provides step-by-step instructions for implementing the file management feature into your existing Resume Modifier backend.

---

## Phase 1: Database Setup

### 1.1 Create ResumeFile Model

**File:** `app/models/temp.py`

Add this model to your existing models file:

```python
class ResumeFile(db.Model):
    __tablename__ = 'resume_files'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # File Metadata
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    file_extension = db.Column(db.String(10), nullable=False)  # pdf, docx, etc.
    mime_type = db.Column(db.String(50), nullable=False)
    
    # Storage Information
    storage_key = db.Column(db.String(500), nullable=False)  # S3 path or file path
    storage_provider = db.Column(db.String(50), default='local')  # local, s3, gcs
    
    # File Content
    extracted_text = db.Column(db.Text, nullable=True)  # Full parsed text
    
    # Metadata
    upload_status = db.Column(db.String(50), default='pending')  # pending, complete, failed
    is_processed = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='resume_files', lazy=True)
    
    def __repr__(self):
        return f'<ResumeFile {self.original_filename}>'
    
    def to_dict(self, include_text=False):
        """Convert model to dictionary for JSON response"""
        data = {
            'id': self.id,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_extension': self.file_extension,
            'mime_type': self.mime_type,
            'storage_provider': self.storage_provider,
            'upload_status': self.upload_status,
            'is_processed': self.is_processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'formatted_file_size': self._format_file_size()
        }
        if include_text and self.extracted_text:
            data['extracted_text_length'] = len(self.extracted_text)
            data['extracted_text_preview'] = self.extracted_text[:500] + ('...' if len(self.extracted_text) > 500 else '')
        return data
    
    def _format_file_size(self):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024:
                return f"{self.file_size} {unit}"
            self.file_size /= 1024
        return f"{self.file_size} TB"
```

### 1.2 Create Database Migration

**File:** `migrations/versions/{timestamp}_add_resume_files_table.py`

```python
"""Add ResumeFile table for file management

Revision ID: 0016
Revises: 0015
Create Date: 2025-11-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0016'
down_revision = '0015'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'resume_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_extension', sa.String(10), nullable=False),
        sa.Column('mime_type', sa.String(50), nullable=False),
        sa.Column('storage_key', sa.String(500), nullable=False),
        sa.Column('storage_provider', sa.String(50), nullable=False, server_default='local'),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('upload_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('is_processed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_resume_files_user_id'),
        'resume_files',
        ['user_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_resume_files_created_at'),
        'resume_files',
        ['created_at'],
        unique=False
    )


def downgrade():
    op.drop_index(op.f('ix_resume_files_created_at'), table_name='resume_files')
    op.drop_index(op.f('ix_resume_files_user_id'), table_name='resume_files')
    op.drop_table('resume_files')
```

**Execute migration:**
```bash
flask db upgrade
# or
alembic upgrade head
```

---

## Phase 2: File Validation Utilities

### 2.1 File Validator

**File:** `app/utils/file_validator.py`

```python
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os

class FileValidator:
    """Validates uploaded resume files"""
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    
    # MIME types
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    # Maximum file size (10 MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self):
        self.error = None
        self.error_code = None
    
    def validate(self, file: FileStorage) -> bool:
        """
        Validate uploaded file
        Returns: True if valid, False otherwise
        """
        if not file:
            self.error = "No file provided"
            self.error_code = "FILE_NOT_PROVIDED"
            return False
        
        if file.filename == '':
            self.error = "Empty filename"
            self.error_code = "EMPTY_FILENAME"
            return False
        
        # Check file extension
        if not self._check_extension(file.filename):
            self.error = f"File type not allowed. Supported: {', '.join(self.ALLOWED_EXTENSIONS)}"
            self.error_code = "INVALID_FILE_TYPE"
            return False
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > self.MAX_FILE_SIZE:
            size_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            self.error = f"File too large. Maximum size: {size_mb}MB"
            self.error_code = "FILE_TOO_LARGE"
            return False
        
        if file_size == 0:
            self.error = "File is empty"
            self.error_code = "EMPTY_FILE"
            return False
        
        # Check MIME type
        if file.content_type not in self.ALLOWED_MIME_TYPES:
            self.error = f"Invalid MIME type: {file.content_type}"
            self.error_code = "INVALID_MIME_TYPE"
            return False
        
        return True
    
    def _check_extension(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    @staticmethod
    def get_secure_filename(filename: str) -> str:
        """Get secure filename"""
        return secure_filename(filename)
```

---

## Phase 3: File Storage Service

### 3.1 Storage Service (Local & Cloud Abstraction)

**File:** `app/services/file_storage_service.py`

```python
import os
import uuid
from datetime import datetime
from werkzeug.datastructures import FileStorage
from app.extensions import db
from app.models.temp import ResumeFile
import logging

logger = logging.getLogger(__name__)

class FileStorageService:
    """Handles file storage operations - supports local and cloud storage"""
    
    def __init__(self):
        self.storage_provider = os.getenv('FILE_STORAGE_PROVIDER', 'local')
        self.storage_path = os.getenv('FILE_STORAGE_PATH', '/app/storage')
        
        if self.storage_provider == 's3':
            self._init_s3()
        elif self.storage_provider == 'gcs':
            self._init_gcs()
    
    def _init_s3(self):
        """Initialize S3 client"""
        try:
            import boto3
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_S3_REGION', 'us-east-1')
            )
            self.s3_bucket = os.getenv('AWS_S3_BUCKET_NAME')
        except ImportError:
            logger.warning("boto3 not installed. S3 storage unavailable.")
    
    def _init_gcs(self):
        """Initialize Google Cloud Storage client"""
        try:
            from google.cloud import storage
            self.gcs_client = storage.Client()
            self.gcs_bucket = self.gcs_client.bucket(os.getenv('GCS_BUCKET_NAME'))
        except ImportError:
            logger.warning("google-cloud-storage not installed. GCS unavailable.")
    
    def save_file(self, user_id: int, file: FileStorage, description: str = None) -> ResumeFile:
        """
        Save uploaded file and create database record
        Returns: ResumeFile model instance
        """
        file_id = str(uuid.uuid4())
        original_filename = file.filename
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        
        # Generate storage key
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        storage_key = f"{user_id}/resumes/{file_id}/{timestamp}_{original_filename}"
        
        try:
            # Save to storage provider
            if self.storage_provider == 'local':
                storage_key = self._save_local(storage_key, file)
            elif self.storage_provider == 's3':
                storage_key = self._save_s3(storage_key, file)
            elif self.storage_provider == 'gcs':
                storage_key = self._save_gcs(storage_key, file)
            
            # Get file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            # Create database record
            resume_file = ResumeFile(
                user_id=user_id,
                original_filename=original_filename,
                file_size=file_size,
                file_extension=file_extension,
                mime_type=file.content_type,
                storage_key=storage_key,
                storage_provider=self.storage_provider,
                upload_status='complete'
            )
            
            db.session.add(resume_file)
            db.session.commit()
            
            logger.info(f"File saved: {storage_key} for user {user_id}")
            return resume_file
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise
    
    def _save_local(self, storage_key: str, file: FileStorage) -> str:
        """Save file to local filesystem"""
        full_path = os.path.join(self.storage_path, storage_key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        file.save(full_path)
        return storage_key
    
    def _save_s3(self, storage_key: str, file: FileStorage) -> str:
        """Save file to AWS S3"""
        file.seek(0)
        self.s3_client.upload_fileobj(
            file,
            self.s3_bucket,
            storage_key,
            ExtraArgs={'ContentType': file.content_type}
        )
        return storage_key
    
    def _save_gcs(self, storage_key: str, file: FileStorage) -> str:
        """Save file to Google Cloud Storage"""
        blob = self.gcs_bucket.blob(storage_key)
        file.seek(0)
        blob.upload_from_string(
            file.read(),
            content_type=file.content_type
        )
        return storage_key
    
    def get_file(self, resume_file: ResumeFile) -> bytes:
        """Retrieve file content"""
        if self.storage_provider == 'local':
            return self._get_local(resume_file.storage_key)
        elif self.storage_provider == 's3':
            return self._get_s3(resume_file.storage_key)
        elif self.storage_provider == 'gcs':
            return self._get_gcs(resume_file.storage_key)
    
    def _get_local(self, storage_key: str) -> bytes:
        """Get file from local filesystem"""
        full_path = os.path.join(self.storage_path, storage_key)
        with open(full_path, 'rb') as f:
            return f.read()
    
    def _get_s3(self, storage_key: str) -> bytes:
        """Get file from S3"""
        response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=storage_key)
        return response['Body'].read()
    
    def _get_gcs(self, storage_key: str) -> bytes:
        """Get file from GCS"""
        blob = self.gcs_bucket.blob(storage_key)
        return blob.download_as_bytes()
    
    def delete_file(self, resume_file: ResumeFile) -> bool:
        """Delete file from storage"""
        try:
            if self.storage_provider == 'local':
                self._delete_local(resume_file.storage_key)
            elif self.storage_provider == 's3':
                self._delete_s3(resume_file.storage_key)
            elif self.storage_provider == 'gcs':
                self._delete_gcs(resume_file.storage_key)
            
            # Delete database record
            db.session.delete(resume_file)
            db.session.commit()
            
            logger.info(f"File deleted: {resume_file.storage_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
    
    def _delete_local(self, storage_key: str):
        """Delete file from local filesystem"""
        full_path = os.path.join(self.storage_path, storage_key)
        if os.path.exists(full_path):
            os.remove(full_path)
    
    def _delete_s3(self, storage_key: str):
        """Delete file from S3"""
        self.s3_client.delete_object(Bucket=self.s3_bucket, Key=storage_key)
    
    def _delete_gcs(self, storage_key: str):
        """Delete file from GCS"""
        blob = self.gcs_bucket.blob(storage_key)
        blob.delete()
```

---

## Phase 4: File Processing Service

### 4.1 File Text Extraction

**File:** `app/services/file_processing_service.py`

```python
from app.utils.parse_pdf import parse_pdf_file
from app.models.temp import ResumeFile
from app.extensions import db
import logging

logger = logging.getLogger(__name__)

class FileProcessingService:
    """Handles file processing - text extraction, parsing, etc."""
    
    @staticmethod
    def extract_text(resume_file: ResumeFile) -> str:
        """
        Extract text from resume file
        Supports: PDF, DOCX
        Returns: Extracted text string
        """
        try:
            if resume_file.file_extension.lower() == 'pdf':
                return FileProcessingService._extract_pdf(resume_file)
            elif resume_file.file_extension.lower() == 'docx':
                return FileProcessingService._extract_docx(resume_file)
            else:
                logger.warning(f"Unsupported file type: {resume_file.file_extension}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return ""
    
    @staticmethod
    def _extract_pdf(resume_file: ResumeFile) -> str:
        """Extract text from PDF file"""
        from app.services.file_storage_service import FileStorageService
        
        storage_service = FileStorageService()
        file_content = storage_service.get_file(resume_file)
        
        # Use existing parse_pdf_file utility
        import io
        pdf_stream = io.BytesIO(file_content)
        text = parse_pdf_file(pdf_stream)
        
        return text if text else ""
    
    @staticmethod
    def _extract_docx(resume_file: ResumeFile) -> str:
        """Extract text from DOCX file"""
        from app.services.file_storage_service import FileStorageService
        
        try:
            from docx import Document
            import io
        except ImportError:
            logger.warning("python-docx not installed. DOCX extraction unavailable.")
            return ""
        
        storage_service = FileStorageService()
        file_content = storage_service.get_file(resume_file)
        
        # Parse DOCX
        doc_stream = io.BytesIO(file_content)
        doc = Document(doc_stream)
        
        # Extract text from all paragraphs
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    
    @staticmethod
    def process_file(resume_file: ResumeFile) -> bool:
        """
        Process file: extract text and update metadata
        Returns: True if successful
        """
        try:
            # Extract text
            extracted_text = FileProcessingService.extract_text(resume_file)
            
            # Update database
            resume_file.extracted_text = extracted_text
            resume_file.is_processed = True
            resume_file.upload_status = 'complete'
            
            db.session.commit()
            
            logger.info(f"File processed: {resume_file.id} ({len(extracted_text)} chars)")
            return True
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            resume_file.upload_status = 'failed'
            db.session.commit()
            return False
```

---

## Phase 5: File Metadata Service

### 5.1 Database Operations Service

**File:** `app/services/file_metadata_service.py`

```python
from app.extensions import db
from app.models.temp import ResumeFile
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)

class FileMetadataService:
    """Handles database operations for file metadata"""
    
    @staticmethod
    def get_file_by_id(file_id: int, user_id: int) -> ResumeFile:
        """Get file by ID, checking ownership"""
        return ResumeFile.query.filter_by(id=file_id, user_id=user_id).first()
    
    @staticmethod
    def get_user_files(user_id: int, page: int = 1, per_page: int = 20, 
                       sort_by: str = 'created_at', sort_order: str = 'desc',
                       search: str = None) -> tuple:
        """
        Get paginated list of user's files
        Returns: (files, pagination_info)
        """
        query = ResumeFile.query.filter_by(user_id=user_id)
        
        # Apply search filter
        if search:
            query = query.filter(
                ResumeFile.original_filename.ilike(f"%{search}%")
            )
        
        # Apply sorting
        sort_column = getattr(ResumeFile, sort_by, ResumeFile.created_at)
        if sort_order.lower() == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        pagination_info = {
            'page': page,
            'per_page': per_page,
            'total': paginated.total,
            'total_pages': paginated.pages
        }
        
        return paginated.items, pagination_info
    
    @staticmethod
    def delete_file(file_id: int, user_id: int) -> bool:
        """Delete file (database record only - storage handled separately)"""
        try:
            file_record = FileMetadataService.get_file_by_id(file_id, user_id)
            if not file_record:
                return False
            
            db.session.delete(file_record)
            db.session.commit()
            logger.info(f"File record deleted: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file record: {str(e)}")
            return False
    
    @staticmethod
    def bulk_delete_files(file_ids: list, user_id: int) -> tuple:
        """
        Delete multiple files
        Returns: (deleted_count, failed_count)
        """
        deleted_count = 0
        failed_count = 0
        
        for file_id in file_ids:
            if FileMetadataService.delete_file(file_id, user_id):
                deleted_count += 1
            else:
                failed_count += 1
        
        return deleted_count, failed_count
```

---

## Phase 6: API Endpoints

### 6.1 File Management Routes

**File:** `app/server.py` (add these routes)

```python
from app.services.file_storage_service import FileStorageService
from app.services.file_processing_service import FileProcessingService
from app.services.file_metadata_service import FileMetadataService
from app.utils.file_validator import FileValidator
from flask import send_file
import io

# File Upload
@api.route('/files/upload', methods=['POST'])
@token_required
def upload_file(user_id):
    """
    Upload resume file
    ---
    tags:
      - Files
    parameters:
      - in: header
        name: Authorization
        type: string
        required: true
        description: JWT token
    requestBody:
      required: true
      content:
        multipart/form-data:
          schema:
            type: object
            properties:
              file:
                type: string
                format: binary
                description: PDF or DOCX file
              document_name:
                type: string
                description: Optional custom name
    responses:
      201:
        description: File uploaded successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            file:
              type: object
      400:
        description: Invalid file or request
      401:
        description: Unauthorized
    """
    file = request.files.get('file')
    
    # Validate file
    validator = FileValidator()
    if not validator.validate(file):
        return jsonify({
            'success': False,
            'error': validator.error_code,
            'message': validator.error
        }), 400
    
    try:
        # Save file
        storage_service = FileStorageService()
        resume_file = storage_service.save_file(user_id, file)
        
        # Extract text asynchronously
        processor = FileProcessingService()
        processor.process_file(resume_file)
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'file': resume_file.to_dict(include_text=True)
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'UPLOAD_FAILED',
            'message': str(e)
        }), 500


# List Files
@api.route('/files', methods=['GET'])
@token_required
def list_files(user_id):
    """
    List user's uploaded files
    ---
    tags:
      - Files
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 20
      - in: query
        name: sort_by
        type: string
        default: created_at
      - in: query
        name: sort_order
        type: string
        default: desc
      - in: query
        name: search
        type: string
    responses:
      200:
        description: List of files
      401:
        description: Unauthorized
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    search = request.args.get('search', None)
    
    metadata_service = FileMetadataService()
    files, pagination = metadata_service.get_user_files(
        user_id=user_id,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search
    )
    
    return jsonify({
        'success': True,
        'data': {
            'files': [f.to_dict() for f in files],
            'pagination': pagination
        }
    }), 200


# Get File Info
@api.route('/files/<int:file_id>/info', methods=['GET'])
@token_required
def get_file_info(user_id, file_id):
    """
    Get detailed file metadata
    ---
    tags:
      - Files
    parameters:
      - in: path
        name: file_id
        type: integer
        required: true
    responses:
      200:
        description: File metadata
      404:
        description: File not found
    """
    metadata_service = FileMetadataService()
    file_record = metadata_service.get_file_by_id(file_id, user_id)
    
    if not file_record:
        return jsonify({
            'success': False,
            'error': 'FILE_NOT_FOUND',
            'message': f'File with ID {file_id} not found'
        }), 404
    
    return jsonify({
        'success': True,
        'file': file_record.to_dict(include_text=True)
    }), 200


# Download File
@api.route('/files/<int:file_id>', methods=['GET'])
@token_required
def download_file(user_id, file_id):
    """
    Download file
    ---
    tags:
      - Files
    parameters:
      - in: path
        name: file_id
        type: integer
        required: true
      - in: query
        name: format
        type: string
        default: original
        description: 'original' or 'pdf'
    responses:
      200:
        description: File download
      404:
        description: File not found
    """
    metadata_service = FileMetadataService()
    file_record = metadata_service.get_file_by_id(file_id, user_id)
    
    if not file_record:
        return jsonify({
            'success': False,
            'error': 'FILE_NOT_FOUND',
            'message': f'File with ID {file_id} not found'
        }), 404
    
    try:
        storage_service = FileStorageService()
        file_content = storage_service.get_file(file_record)
        
        # Create file stream
        file_stream = io.BytesIO(file_content)
        
        return send_file(
            file_stream,
            mimetype=file_record.mime_type,
            as_attachment=True,
            download_name=file_record.original_filename
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'DOWNLOAD_FAILED',
            'message': str(e)
        }), 500


# Delete File
@api.route('/files/<int:file_id>', methods=['DELETE'])
@token_required
def delete_file(user_id, file_id):
    """
    Delete file
    ---
    tags:
      - Files
    parameters:
      - in: path
        name: file_id
        type: integer
        required: true
    responses:
      200:
        description: File deleted
      404:
        description: File not found
    """
    metadata_service = FileMetadataService()
    file_record = metadata_service.get_file_by_id(file_id, user_id)
    
    if not file_record:
        return jsonify({
            'success': False,
            'error': 'FILE_NOT_FOUND',
            'message': f'File with ID {file_id} not found'
        }), 404
    
    try:
        storage_service = FileStorageService()
        storage_service.delete_file(file_record)
        
        return jsonify({
            'success': True,
            'message': 'File deleted successfully',
            'deleted_file_id': file_id
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'DELETE_FAILED',
            'message': str(e)
        }), 500


# Bulk Delete Files
@api.route('/files', methods=['DELETE'])
@token_required
def bulk_delete_files(user_id):
    """
    Delete multiple files
    ---
    tags:
      - Files
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              file_ids:
                type: array
                items:
                  type: integer
    responses:
      200:
        description: Files deleted
    """
    data = request.get_json()
    file_ids = data.get('file_ids', [])
    
    if not file_ids:
        return jsonify({
            'success': False,
            'error': 'NO_FILES',
            'message': 'No file IDs provided'
        }), 400
    
    metadata_service = FileMetadataService()
    deleted_count, failed_count = metadata_service.bulk_delete_files(file_ids, user_id)
    
    return jsonify({
        'success': True,
        'message': f'{deleted_count} files deleted successfully',
        'deleted_count': deleted_count,
        'failed_count': failed_count
    }), 200
```

---

## Phase 7: Environment Configuration

### 7.1 Update `.env` file

Add these environment variables:

```env
# File Storage
FILE_STORAGE_PROVIDER=local  # Options: local, s3, gcs
FILE_STORAGE_PATH=/app/storage
FILE_MAX_SIZE=10485760  # 10MB

# AWS S3 (if using S3)
AWS_ACCESS_KEY_ID=your_key_id
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET_NAME=your_bucket_name
AWS_S3_REGION=us-east-1

# Google Cloud Storage (if using GCS)
GCS_PROJECT_ID=your_project_id
GCS_BUCKET_NAME=your_bucket_name
GCS_CREDENTIALS_PATH=/path/to/credentials.json
```

---

## Phase 8: Testing

### 8.1 Basic Test Script

**File:** `test_file_management.py`

```python
import pytest
import io
from werkzeug.datastructures import FileStorage
from app import create_app
from app.extensions import db
from app.models.temp import User, ResumeFile
import json

@pytest.fixture
def app():
    app = create_app()
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_header(client):
    """Generate valid auth token"""
    from app.utils.jwt_utils import generate_token
    token = generate_token(user_id=1)
    return {'Authorization': f'Bearer {token}'}

class TestFileUpload:
    def test_upload_pdf(self, client, auth_header):
        """Test PDF upload"""
        data = {
            'file': (io.BytesIO(b'%PDF-1.4...'), 'resume.pdf')
        }
        response = client.post(
            '/files/upload',
            data=data,
            headers=auth_header,
            content_type='multipart/form-data'
        )
        assert response.status_code == 201
        assert response.json['success'] == True

    def test_upload_no_file(self, client, auth_header):
        """Test upload without file"""
        response = client.post(
            '/files/upload',
            data={},
            headers=auth_header
        )
        assert response.status_code == 400
        assert response.json['error_code'] == 'FILE_NOT_PROVIDED'

class TestFileList:
    def test_list_files(self, client, auth_header):
        """Test listing files"""
        response = client.get(
            '/files',
            headers=auth_header
        )
        assert response.status_code == 200
        assert 'data' in response.json

class TestFileDelete:
    def test_delete_file(self, client, auth_header, app):
        """Test file deletion"""
        # Setup: create a file
        with app.app_context():
            file = ResumeFile(
                user_id=1,
                original_filename='test.pdf',
                file_size=1024,
                file_extension='pdf',
                mime_type='application/pdf',
                storage_key='1/resumes/test/test.pdf'
            )
            db.session.add(file)
            db.session.commit()
            file_id = file.id
        
        # Test delete
        response = client.delete(
            f'/files/{file_id}',
            headers=auth_header
        )
        assert response.status_code == 200

if __name__ == '__main__':
    pytest.main([__file__])
```

**Run tests:**
```bash
pytest test_file_management.py -v
```

---

## Deployment Checklist

- [ ] Database migration executed (`flask db upgrade`)
- [ ] Environment variables configured in Railway
- [ ] Storage bucket created (if using S3/GCS)
- [ ] All new utility files created
- [ ] All service files created
- [ ] API routes added to `server.py`
- [ ] File validator tests passing
- [ ] File upload/download/delete tests passing
- [ ] Integration with resume scoring verified
- [ ] Deployed to staging environment
- [ ] End-to-end testing completed
- [ ] Deployed to production

---

## Quick Start Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install python-docx boto3  # Additional for file processing

# 2. Create migration
flask db migrate -m "Add ResumeFile model"

# 3. Apply migration
flask db upgrade

# 4. Create storage directory (local)
mkdir -p /app/storage

# 5. Test file management
pytest test_file_management.py -v

# 6. Run server
flask run
# or with Railway
railway run flask run
```

---

## Support & Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('file_management')
```

### Test File Upload with curl

```bash
curl -X POST http://localhost:5000/files/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@resume.pdf"
```

### Check File Storage

```bash
# Local storage
ls -la /app/storage/

# S3 storage
aws s3 ls s3://your_bucket_name/
```

