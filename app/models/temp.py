from typing import Dict, Any, List
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy 
from flask import Flask
from datetime import datetime
import os



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
    resume_files = db.relationship('ResumeFile', back_populates='user', lazy='dynamic')

    updated_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    
    

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
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    storage_type = db.Column(db.String(50), nullable=False, default='local')  # 'local' or 's3'
    file_path = db.Column(db.String(500), nullable=False)  # Local path or S3 key
    s3_bucket = db.Column(db.String(100), nullable=True)  # S3 bucket name if using S3
    file_hash = db.Column(db.String(64), nullable=False, unique=True)  # SHA-256 hash for deduplication
    is_processed = db.Column(db.Boolean, default=False)  # Whether file has been processed for text extraction
    extracted_text = db.Column(db.Text, nullable=True)  # Extracted text content
    processing_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    processing_error = db.Column(db.Text, nullable=True)  # Error message if processing failed
    tags = db.Column(db.JSON, nullable=True, default=list)  # User-defined tags
    is_active = db.Column(db.Boolean, default=True)  # For soft delete
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='resume_files')
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('file_size > 0', name='check_positive_file_size'),
        db.CheckConstraint("storage_type in ('local', 's3')", name='check_valid_storage_type'),
        db.CheckConstraint("processing_status in ('pending', 'processing', 'completed', 'failed')", name='check_valid_processing_status'),
        db.Index('idx_user_created', 'user_id', 'created_at'),
        db.Index('idx_processing_status', 'processing_status'),
        db.Index('idx_active_files', 'is_active'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary for JSON serialization."""
        return {
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
            'tags': self.tags or [],
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
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
    
    def __repr__(self):
        return f'<ResumeFile {self.original_filename} (User: {self.user_id})>'