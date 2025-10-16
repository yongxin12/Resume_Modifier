from typing import Dict, Any, List
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy 
from flask import Flask
from datetime import datetime



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