from typing import Dict, Any, List
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy 
from flask import Flask
from datetime import datetime, timedelta
import os
import hashlib
import secrets
from sqlalchemy import event



class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    city = db.Column(db.String(100))
    bio = db.Column(db.String(200))
    country = db.Column(db.String(100))


    resumes = db.relationship('Resume', back_populates='user', lazy='dynamic')
    job_descriptions = db.relationship('JobDescription', back_populates='user', lazy='dynamic')
    resume_files = db.relationship('ResumeFile', foreign_keys='ResumeFile.user_id', back_populates='user', lazy='dynamic')

    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    

    def set_password(self, password):
        self.password = generate_password_hash(password)


    def check_password(self, password):
        return check_password_hash(self.password, password)
    

class Resume(db.Model):
    __tablename__ = 'resumes'
    
    user_id = db.Column(db.ForeignKey('users.id'), primary_key=True)
    serial_number = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    extracted_text = db.Column(db.String(5000), nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey('resume_templates.id'), nullable=True)  # Updated to reference template
    parsed_resume = db.Column(db.JSON, nullable=False)
    user = db.relationship('User', back_populates='resumes')
    
    updated_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)


class JobDescription(db.Model):
    __tablename__ = 'job_descriptions'
    user_id = db.Column(db.ForeignKey('users.id'), primary_key=True)
    serial_number = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(500), nullable=False)
    user = db.relationship('User', back_populates='job_descriptions')

    created_at = db.Column(db.DateTime, nullable=False)


class UserSite(db.Model):
    __tablename__ = 'user_sites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    resume_serial = db.Column(db.Integer, nullable=False)
    subdomain = db.Column(db.String(100), nullable=False, unique=True)
    html_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'resume_serial', name='uix_user_resume'),
    )
    
    def __repr__(self):
        return f'<UserSite {self.subdomain}>'


class ResumeTemplate(db.Model):
    __tablename__ = 'resume_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    style_config = db.Column(db.JSON, nullable=False)  # Contains font, colors, layout rules
    sections = db.Column(db.JSON, nullable=False)  # Ordered list of sections
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to resumes using this template
    resumes = db.relationship('Resume', backref='template_ref', lazy='dynamic')
    
    def __repr__(self):
        return f'<ResumeTemplate {self.name}>'


class GoogleAuth(db.Model):
    __tablename__ = 'google_auth_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    google_user_id = db.Column(db.String(100))  # Google user ID
    email = db.Column(db.String(100))  # Google email
    name = db.Column(db.String(200))  # Google display name
    picture = db.Column(db.String(500))  # Google profile picture URL
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=False)
    token_expires_at = db.Column(db.DateTime, nullable=False)
    scope = db.Column(db.String(500), nullable=False)  # Granted OAuth scopes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to user
    user = db.relationship('User', backref='google_auth', lazy=True)
    
    # Unique constraint - one Google auth per user
    __table_args__ = (
        db.UniqueConstraint('user_id', name='unique_user_google_auth'),
    )
    
    def __repr__(self):
        return f'<GoogleAuth {self.user_id}>'


class GeneratedDocument(db.Model):
    __tablename__ = 'generated_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resume_id = db.Column(db.Integer, nullable=False)  # Reference to resume serial_number
    template_id = db.Column(db.Integer, db.ForeignKey('resume_templates.id'), nullable=False)
    google_doc_id = db.Column(db.String(200), nullable=False)  # Google Docs document ID
    google_doc_url = db.Column(db.String(500), nullable=False)  # Shareable link
    document_title = db.Column(db.String(200), nullable=False)
    job_description_used = db.Column(db.Text)  # Job description that was used for generation
    generation_status = db.Column(db.String(50), default='created')  # created, exported, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='generated_documents', lazy=True)
    template = db.relationship('ResumeTemplate', backref='generated_documents', lazy=True)
    
    # Foreign key constraint for resume reference
    __table_args__ = (
        db.ForeignKeyConstraint(
            ['user_id', 'resume_id'], 
            ['resumes.user_id', 'resumes.serial_number']
        ),
    )
    
    def __repr__(self):
        return f'<GeneratedDocument {self.document_title}>'


class ResumeFile(db.Model):
    """Model for storing uploaded resume files and their metadata."""
    __tablename__ = 'resume_files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    display_filename = db.Column(db.String(255), nullable=True)  # Filename shown to user (with duplicate info)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False, default='application/octet-stream')
    storage_type = db.Column(db.String(50), nullable=False, default='local')  # 'local' or 's3'
    file_path = db.Column(db.String(500), nullable=False)  # Local path or S3 key
    s3_bucket = db.Column(db.String(100), nullable=True)  # S3 bucket name if using S3
    file_hash = db.Column(db.String(64), nullable=False)  # SHA-256 hash (removed unique constraint)
    
    # Google Drive Integration Fields
    google_drive_file_id = db.Column(db.String(100), nullable=True)  # Google Drive file ID
    google_doc_id = db.Column(db.String(100), nullable=True)  # Google Doc ID (if converted)
    google_drive_link = db.Column(db.String(500), nullable=True)  # Direct link to Google Drive file
    google_doc_link = db.Column(db.String(500), nullable=True)  # Direct link to Google Doc
    is_shared_with_user = db.Column(db.Boolean, default=False)  # Whether shared with user
    
    # Processing and Content Fields
    is_processed = db.Column(db.Boolean, default=False)  # Whether file has been processed for text extraction
    extracted_text = db.Column(db.Text, nullable=True)  # Extracted text content
    processing_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    processing_error = db.Column(db.Text, nullable=True)  # Error message if processing failed
    
    # Processing Result Fields (for storing extracted metadata)
    page_count = db.Column(db.Integer, nullable=True)  # Number of pages in document
    paragraph_count = db.Column(db.Integer, nullable=True)  # Number of paragraphs
    language = db.Column(db.String(10), nullable=True)  # Detected language code (e.g., 'en')
    keywords = db.Column(db.JSON, nullable=True, default=list)  # Extracted keywords as JSON array
    processing_time = db.Column(db.Float, nullable=True)  # Time taken to process in seconds
    processing_metadata = db.Column(db.JSON, nullable=True, default=dict)  # Additional processing metadata as JSON
    
    # Duplicate Handling Fields
    is_duplicate = db.Column(db.Boolean, default=False)  # Whether this is a duplicate file
    duplicate_sequence = db.Column(db.Integer, default=0)  # Sequence number for duplicates (0 = original)
    original_file_id = db.Column(db.Integer, db.ForeignKey('resume_files.id'), nullable=True)  # Reference to original file
    
    # Thumbnail Fields
    has_thumbnail = db.Column(db.Boolean, default=False)  # Whether thumbnail exists
    thumbnail_path = db.Column(db.String(500), nullable=True)  # Path to thumbnail file
    thumbnail_status = db.Column(db.String(50), default='pending')  # pending, generating, completed, failed
    thumbnail_generated_at = db.Column(db.DateTime, nullable=True)  # When thumbnail was created
    thumbnail_error = db.Column(db.Text, nullable=True)  # Error message if generation failed
    
    # Soft Deletion and Metadata
    is_active = db.Column(db.Boolean, default=True)  # For soft delete functionality
    deleted_at = db.Column(db.DateTime, nullable=True)  # Timestamp when soft deleted
    deleted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Who deleted it
    tags = db.Column(db.JSON, nullable=True, default=list)  # User-defined tags
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], back_populates='resume_files')
    deleted_by_user = db.relationship('User', foreign_keys=[deleted_by], backref='deleted_files')
    original_file = db.relationship('ResumeFile', remote_side=[id], backref='duplicates')
    
    # Constraints and Indexes
    __table_args__ = (
        db.CheckConstraint('file_size > 0', name='check_positive_file_size'),
        db.CheckConstraint("storage_type in ('local', 's3')", name='check_valid_storage_type'),
        db.CheckConstraint("processing_status in ('pending', 'processing', 'completed', 'failed')", name='check_valid_processing_status'),
        db.CheckConstraint("thumbnail_status in ('pending', 'generating', 'completed', 'failed', 'unavailable')", name='check_valid_thumbnail_status'),
        db.CheckConstraint('duplicate_sequence >= 0', name='check_positive_duplicate_sequence'),
        db.Index('idx_user_created', 'user_id', 'created_at'),
        db.Index('idx_processing_status', 'processing_status'),
        db.Index('idx_active_files', 'is_active'),
        db.Index('idx_file_hash', 'file_hash'),  # For duplicate detection
        db.Index('idx_user_hash', 'user_id', 'file_hash'),  # For user-specific duplicate detection
        db.Index('idx_google_drive_file', 'google_drive_file_id'),
        db.Index('idx_google_doc', 'google_doc_id'),
        db.Index('idx_duplicates', 'original_file_id', 'duplicate_sequence'),
        db.Index('idx_deleted_files', 'is_active', 'deleted_at'),
        db.Index('idx_thumbnail_status', 'thumbnail_status'),
    )
    
    def to_dict(self, include_google_drive=True, include_duplicates=True) -> Dict[str, Any]:
        """Convert model instance to dictionary for JSON serialization."""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'file_size': self.file_size,
            'file_size_formatted': self.format_file_size(),
            'mime_type': self.mime_type,
            'storage_type': self.storage_type,
            'file_path': self.file_path,
            's3_bucket': self.s3_bucket,
            'file_hash': self.file_hash,
            'is_processed': self.is_processed,
            'extracted_text': self.extracted_text,
            'processing_status': self.processing_status,
            'processing_error': self.processing_error,
            'page_count': self.page_count,
            'paragraph_count': self.paragraph_count,
            'language': self.language,
            'keywords': self.keywords or [],
            'processing_time': self.processing_time,
            'processing_metadata': self.processing_metadata or {},
            'tags': self.tags or [],
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Add Google Drive information if requested
        if include_google_drive:
            result['google_drive'] = {
                'file_id': self.google_drive_file_id,
                'doc_id': self.google_doc_id,
                'drive_link': self.google_drive_link,
                'doc_link': self.google_doc_link,
                'is_shared': self.is_shared_with_user
            }
        
        # Add duplicate information if requested
        if include_duplicates:
            result['duplicate_info'] = {
                'is_duplicate': self.is_duplicate,
                'duplicate_sequence': self.duplicate_sequence,
                'original_file_id': self.original_file_id
            }
        
        # Add soft deletion information if file is deleted
        if not self.is_active:
            result['deletion_info'] = {
                'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
                'deleted_by': self.deleted_by
            }
            
        return result
    
    def format_file_size(self) -> str:
        """Format file size in human-readable format."""
        if self.file_size is None:
            return "0 B"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                if unit == 'B':
                    return f"{int(size)} {unit}"
                else:
                    return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_display_filename(self) -> str:
        """Get the filename for display to users, including duplicate notation."""
        # Return stored display_filename if available, otherwise compute it
        if self.display_filename:
            return self.display_filename
        
        if not self.is_duplicate or self.duplicate_sequence == 0:
            return self.original_filename
        
        # Split filename and extension
        name, ext = os.path.splitext(self.original_filename)
        return f"{name} ({self.duplicate_sequence}){ext}"
    
    def set_display_filename_if_empty(self):
        """Set display_filename if it's empty or None."""
        if not self.display_filename:
            if not self.is_duplicate or self.duplicate_sequence == 0:
                self.display_filename = self.original_filename
            else:
                name, ext = os.path.splitext(self.original_filename)
                self.display_filename = f"{name} ({self.duplicate_sequence}){ext}"
    
    def soft_delete(self, deleted_by_user_id: int):
        """Mark file as soft deleted."""
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_user_id
    
    def restore(self):
        """Restore soft deleted file."""
        self.is_active = True
        self.deleted_at = None
        self.deleted_by = None
    
    def get_thumbnail_path(self) -> str:
        """Get path to thumbnail file for this resume file."""
        import os
        from flask import current_app
        
        if not self.has_thumbnail or not self.thumbnail_path:
            return None
            
        # If thumbnail_path is already absolute, return as-is
        if os.path.isabs(self.thumbnail_path):
            return self.thumbnail_path
            
        # Otherwise, construct path relative to upload directory
        upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        return os.path.join(upload_dir, 'thumbnails', f"{self.id}.jpg")
    
    def has_valid_thumbnail(self) -> bool:
        """Check if file has a valid thumbnail."""
        import os
        
        if not self.has_thumbnail or self.thumbnail_status != 'completed':
            return False
            
        thumbnail_path = self.get_thumbnail_path()
        if not thumbnail_path:
            return False
            
        return os.path.exists(thumbnail_path)
    
    def get_thumbnail_url(self) -> str:
        """Get URL for thumbnail access."""
        if not self.has_thumbnail:
            return None
            
        return f"/api/files/{self.id}/thumbnail"
    
    def set_thumbnail_completed(self, thumbnail_path: str):
        """Mark thumbnail generation as completed."""
        self.has_thumbnail = True
        self.thumbnail_status = 'completed'
        self.thumbnail_path = thumbnail_path
        self.thumbnail_generated_at = datetime.utcnow()
        self.thumbnail_error = None
    
    def set_thumbnail_failed(self, error_message: str):
        """Mark thumbnail generation as failed."""
        self.has_thumbnail = False
        self.thumbnail_status = 'failed'
        self.thumbnail_error = error_message
        self.thumbnail_path = None
    
    def is_google_drive_synced(self) -> bool:
        """Check if file is synced with Google Drive."""
        return self.google_drive_file_id is not None
    
    def is_google_doc_available(self) -> bool:
        """Check if Google Doc version is available."""
        return self.google_doc_id is not None
    
    @classmethod
    def find_duplicates_by_hash(cls, user_id: int, file_hash: str):
        """Find all files with the same hash for a user."""
        return cls.query.filter_by(
            user_id=user_id,
            file_hash=file_hash,
            is_active=True
        ).all()
    
    @classmethod
    def get_active_files(cls, user_id: int):
        """Get all active (non-deleted) files for a user."""
        return cls.query.filter_by(
            user_id=user_id,
            is_active=True
        )
    
    @classmethod
    def get_deleted_files(cls, user_id: int = None):
        """Get all soft-deleted files, optionally filtered by user."""
        query = cls.query.filter_by(is_active=False)
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query
    
    def __repr__(self):
        return f'<ResumeFile {self.original_filename} (User: {self.user_id})>'


# Event listener to automatically set display_filename if it's None
@event.listens_for(ResumeFile, 'before_insert')
def set_display_filename_before_insert(mapper, connection, target):
    """Automatically set display_filename before inserting if it's None."""
    if target.display_filename is None:
        target.set_display_filename_if_empty()


class PasswordResetToken(db.Model):
    """Model for managing password reset tokens with enhanced security."""
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(128), nullable=False, unique=True)  # SHA-512 hash of the token
    expires_at = db.Column(db.DateTime, nullable=False)  # Token expiration time
    is_used = db.Column(db.Boolean, default=False, nullable=False)  # Whether token has been used
    ip_address = db.Column(db.String(45), nullable=True)  # IP address of requester (IPv6 compatible)
    user_agent = db.Column(db.String(500), nullable=True)  # User agent string for security tracking
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)  # When token was used
    
    # Relationships
    user = db.relationship('User', backref='password_reset_tokens', lazy=True)
    
    # Database constraints and indexes
    __table_args__ = (
        db.Index('idx_password_reset_user_created', 'user_id', 'created_at'),
        db.Index('idx_password_reset_token_hash', 'token_hash'),
        db.Index('idx_password_reset_expires_at', 'expires_at'),
        db.Index('idx_password_reset_is_used', 'is_used'),
    )
    
    @staticmethod
    def generate_token() -> str:
        """Generate a cryptographically secure random token."""
        return secrets.token_urlsafe(32)  # 256-bit entropy, URL-safe base64
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Create SHA-512 hash of the token for secure storage."""
        return hashlib.sha512(token.encode('utf-8')).hexdigest()
    
    @classmethod
    def create_token(cls, user_id: int, ip_address: str = None, user_agent: str = None, 
                     expiry_hours: int = 1) -> tuple:
        """
        Create a new password reset token for a user.
        
        Args:
            user_id: ID of the user requesting password reset
            ip_address: IP address of the requester
            user_agent: User agent string of the requester
            expiry_hours: Hours until token expires (default: 1 hour)
            
        Returns:
            tuple: (token_instance, raw_token) - token instance and unhashed token string
        """
        raw_token = cls.generate_token()
        token_hash = cls.hash_token(raw_token)
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        token_instance = cls(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address[:45] if ip_address else None,  # Truncate if too long
            user_agent=user_agent[:500] if user_agent else None  # Truncate if too long
        )
        
        return token_instance, raw_token
    
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        return not self.is_used and datetime.utcnow() < self.expires_at
    
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() >= self.expires_at
    
    def mark_used(self) -> None:
        """Mark token as used."""
        self.is_used = True
        self.used_at = datetime.utcnow()
    
    @classmethod
    def verify_token(cls, raw_token: str):
        """
        Verify a raw token and return the token instance if valid.
        
        Args:
            raw_token: The unhashed token string to verify
            
        Returns:
            PasswordResetToken or None: Token instance if valid, None otherwise
        """
        if not raw_token:
            return None
            
        token_hash = cls.hash_token(raw_token)
        token = cls.query.filter_by(token_hash=token_hash).first()
        
        if token and token.is_valid():
            return token
        return None
    
    @classmethod
    def cleanup_expired_tokens(cls) -> int:
        """
        Remove expired tokens from database.
        
        Returns:
            int: Number of tokens deleted
        """
        expired_tokens = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        count = len(expired_tokens)
        
        for token in expired_tokens:
            db.session.delete(token)
        
        return count
    
    @classmethod
    def get_active_tokens_for_user(cls, user_id: int):
        """
        Get all active (non-used, non-expired) tokens for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            list: List of active PasswordResetToken instances
        """
        return cls.query.filter(
            cls.user_id == user_id,
            cls.is_used == False,
            cls.expires_at > datetime.utcnow()
        ).all()
    
    @classmethod
    def revoke_all_user_tokens(cls, user_id: int) -> int:
        """
        Revoke all active tokens for a user by marking them as used.
        
        Args:
            user_id: ID of the user
            
        Returns:
            int: Number of tokens revoked
        """
        active_tokens = cls.get_active_tokens_for_user(user_id)
        count = len(active_tokens)
        
        for token in active_tokens:
            token.mark_used()
        
        return count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_used': self.is_used,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'is_valid': self.is_valid(),
            'is_expired': self.is_expired()
        }
    
    def __repr__(self):
        return f'<PasswordResetToken {self.id} (User: {self.user_id}, Valid: {self.is_valid()})>'