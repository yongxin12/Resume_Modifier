# 📁 File Management Feature Design Document

## Overview

This document outlines the design for a comprehensive file management system that enables users to upload, store, download, and delete resume documents in multiple formats (PDF, DOCX, etc.). This feature integrates seamlessly with the existing Resume Modifier API and enables core functionality for resume processing.

---

## 1. Architecture Overview

### 1.1 Component Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React/Vue)                      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────────┐
│              Flask API Server (Backend)                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Endpoints:                                              ││
│  │ • POST   /files/upload       - Upload document          ││
│  │ • GET    /files/{id}         - Download document        ││
│  │ • GET    /files              - List user's documents    ││
│  │ • DELETE /files/{id}         - Delete document          ││
│  │ • GET    /files/{id}/info    - Get metadata             ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Services:                                               ││
│  │ • FileStorageService    - Storage abstraction           ││
│  │ • FileProcessingService - Parsing & validation          ││
│  │ • FileMetadataService   - Database operations           ││
│  └─────────────────────────────────────────────────────────┘│
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼────┐    ┌──────▼─────┐    ┌───▼──────────┐
│ PostgreSQL │    │ S3/Storage  │    │ File System  │
│ Database   │    │ (Cloud)     │    │ (Local dev)  │
└────────────┘    └─────────────┘    └──────────────┘
```

### 1.2 Database Model

**New `ResumFile` Model:**
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
    storage_provider = db.Column(db.String(50), default='local')  # 'local', 's3', 'gcs'
    
    # File Content (for text extraction)
    extracted_text = db.Column(db.Text, nullable=True)  # Parsed text content
    
    # Metadata
    upload_status = db.Column(db.String(50), default='pending')  # pending, complete, failed
    is_processed = db.Column(db.Boolean, default=False)
    
    # Relationships & Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='resume_files', lazy=True)
```

### 1.3 Storage Strategy

#### Option A: Cloud Storage (Recommended for Production)
- **Provider:** AWS S3 / Google Cloud Storage / Supabase Storage
- **Benefits:** Scalable, secure, automatic backups
- **Implementation:** Boto3 (S3) or GCS client
- **Path Structure:** `s3://bucket-name/{user_id}/resumes/{file_id}/{timestamp}_{filename}`

#### Option B: Local File System (Development)
- **Storage Location:** `/app/storage/resumes/{user_id}/{file_id}/`
- **Benefits:** Simple setup, no external dependencies
- **Limitations:** Single-server only, manual backup required

#### Option C: Database BLOB (Not Recommended)
- **Method:** Store file as BYTEA in PostgreSQL
- **Limitations:** Poor performance, database bloat

**Recommended Approach:** Use abstraction layer to support both cloud and local storage.

---

## 2. API Specifications

### 2.1 File Upload Endpoint

**Endpoint:** `POST /files/upload`

**Authentication:** Required (JWT token in header)

**Request Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data
```

**Request Body:**
```
- file: File (multipart) - PDF or DOCX document
- document_name: String (optional) - Custom name for the document
- description: String (optional) - Brief description
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file": {
    "id": 15,
    "original_filename": "Resume_2024.pdf",
    "document_name": "My Resume 2024",
    "file_size": 524288,
    "file_extension": "pdf",
    "mime_type": "application/pdf",
    "upload_status": "complete",
    "created_at": "2025-11-01T10:30:00Z",
    "extracted_text_preview": "John Doe\nSoftware Engineer...",
    "extracted_text_length": 1547
  }
}
```

**Error Responses:**
```json
{
  "success": false,
  "error": "FILE_NOT_PROVIDED",
  "message": "No file uploaded"
}

{
  "success": false,
  "error": "INVALID_FILE_TYPE",
  "message": "Only PDF and DOCX files are supported"
}

{
  "success": false,
  "error": "FILE_TOO_LARGE",
  "message": "File size exceeds maximum limit of 10MB"
}
```

---

### 2.2 List User Files Endpoint

**Endpoint:** `GET /files`

**Authentication:** Required

**Query Parameters:**
```
- page: Integer (optional, default: 1) - Pagination page number
- per_page: Integer (optional, default: 20) - Items per page
- sort_by: String (optional, default: 'created_at') - Sort field
- sort_order: String (optional, default: 'desc') - 'asc' or 'desc'
- search: String (optional) - Search in filename or description
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": 15,
        "original_filename": "Resume_2024.pdf",
        "document_name": "My Resume 2024",
        "file_size": 524288,
        "file_extension": "pdf",
        "mime_type": "application/pdf",
        "created_at": "2025-11-01T10:30:00Z",
        "updated_at": "2025-11-01T10:30:00Z",
        "upload_status": "complete",
        "is_processed": true
      },
      {
        "id": 14,
        "original_filename": "Resume_Draft.docx",
        "document_name": "Draft Resume",
        "file_size": 312456,
        "file_extension": "docx",
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "created_at": "2025-10-28T14:20:00Z",
        "updated_at": "2025-10-28T14:20:00Z",
        "upload_status": "complete",
        "is_processed": false
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 2,
      "total_pages": 1
    }
  }
}
```

---

### 2.3 Download File Endpoint

**Endpoint:** `GET /files/{id}`

**Authentication:** Required

**Path Parameters:**
```
- id: Integer - File ID
```

**Query Parameters:**
```
- format: String (optional, default: 'original') - 'original' or 'pdf'
```

**Response (200 OK):**
- Returns the binary file as attachment
- Content-Disposition header set to trigger download
- Content-Type appropriate for file type

**Error Response (404 Not Found):**
```json
{
  "success": false,
  "error": "FILE_NOT_FOUND",
  "message": "File with ID 99 not found"
}
```

---

### 2.4 Get File Metadata Endpoint

**Endpoint:** `GET /files/{id}/info`

**Authentication:** Required

**Response (200 OK):**
```json
{
  "success": true,
  "file": {
    "id": 15,
    "original_filename": "Resume_2024.pdf",
    "document_name": "My Resume 2024",
    "file_size": 524288,
    "file_extension": "pdf",
    "mime_type": "application/pdf",
    "created_at": "2025-11-01T10:30:00Z",
    "updated_at": "2025-11-01T10:30:00Z",
    "upload_status": "complete",
    "is_processed": true,
    "extracted_text_length": 1547,
    "storage_provider": "s3",
    "formatted_file_size": "512 KB"
  }
}
```

---

### 2.5 Delete File Endpoint

**Endpoint:** `DELETE /files/{id}`

**Authentication:** Required

**Response (200 OK):**
```json
{
  "success": true,
  "message": "File deleted successfully",
  "deleted_file_id": 15
}
```

**Error Response (404):**
```json
{
  "success": false,
  "error": "FILE_NOT_FOUND",
  "message": "File with ID 15 not found"
}
```

---

### 2.6 Bulk Delete Endpoint

**Endpoint:** `DELETE /files`

**Authentication:** Required

**Request Body:**
```json
{
  "file_ids": [15, 14, 13]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "3 files deleted successfully",
  "deleted_count": 3,
  "failed_count": 0
}
```

---

## 3. Integration Points with Existing Features

### 3.1 Integration with Resume Upload (API-06)

**Current Behavior:**
- `/resume/upload` stores resume directly in database

**Enhanced Behavior:**
- Upload flow:
  1. Receive file via `/files/upload`
  2. Store file using `FileStorageService`
  3. Create `ResumeFile` record in database
  4. Extract text via `parse_pdf_file` utility
  5. Return file metadata and extracted text preview

**Code Example:**
```python
@api.route('/files/upload', methods=['POST'])
@token_required
def upload_file(user_id):
    file = request.files.get('file')
    
    # Validate file
    validator = FileValidator()
    if not validator.validate(file):
        return jsonify({"error": validator.error}), 400
    
    # Store file
    storage_service = FileStorageService()
    file_record = storage_service.save_file(user_id, file)
    
    # Extract text
    processor = FileProcessingService()
    extracted_text = processor.extract_text(file_record)
    file_record.extracted_text = extracted_text
    db.session.commit()
    
    return jsonify(file_record.to_dict()), 201
```

---

### 3.2 Integration with Resume Scoring (API-07)

**Use Case:** Score a previously uploaded document

**Endpoint:** `POST /resume/score`

**Enhanced Request:**
```json
{
  "method": "file_id",  // Instead of direct text/file upload
  "file_id": 15,
  "job_description": "Software Engineer position..."
}
```

**Processing Flow:**
1. Retrieve file metadata from `ResumeFile`
2. Load extracted text
3. Pass to `ResumeAI.score_resume()`
4. Return scoring breakdown

---

### 3.3 Integration with Resume Generation (API-13)

**Use Case:** Generate resume from uploaded document + job description

**Endpoint:** `POST /resume/generate`

**Enhanced Request:**
```json
{
  "file_id": 15,
  "template_id": 2,
  "job_description": "Marketing Manager at TechCorp...",
  "optimization_level": "aggressive"
}
```

**Processing Flow:**
1. Load file content and metadata
2. Parse resume data using existing `parse_pdf_file`
3. Extract resume fields (name, email, experience, education, skills)
4. Enhance with AI optimization based on job description
5. Generate formatted resume using template
6. Return generation metadata

---

### 3.4 Integration with Google Docs Export (API-14)

**Use Case:** Export uploaded document to Google Docs

**Endpoint:** `POST /resume/export/gdocs`

**Enhanced Request:**
```json
{
  "file_id": 15,
  "template_id": 2,
  "document_title": "Resume - Marketing Manager Position"
}
```

**Processing Flow:**
1. Retrieve file and extract formatted content
2. Use existing `GoogleDocsService` to create Google Doc
3. Insert content with professional formatting
4. Return Google Docs URL and metadata

---

## 4. Technical Implementation

### 4.1 File Validation

**Supported Formats:**
- PDF (.pdf) - `application/pdf`
- DOCX (.docx) - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

**Validation Rules:**
- Maximum file size: 10MB
- Only registered MIME types allowed
- File extension validation
- Virus scanning (optional, using VirusTotal API)

**Implementation File:** `app/utils/file_validator.py`

---

### 4.2 File Storage Service

**Interface:**
```python
class FileStorageService:
    def save_file(self, user_id: int, file: FileStorage) -> ResumeFile
    def get_file(self, file_id: int) -> bytes
    def delete_file(self, file_id: int) -> bool
    def get_file_path(self, file_id: int) -> str
```

**Implementation:** `app/services/file_storage_service.py`

---

### 4.3 File Processing Service

**Features:**
- Extract text from PDF/DOCX
- Parse resume structure (name, email, phone, sections)
- Generate text previews
- Convert formats

**Implementation:** `app/services/file_processing_service.py`

---

### 4.4 File Metadata Service

**Features:**
- CRUD operations for `ResumeFile` model
- Pagination and filtering
- Search functionality
- Relationship management

**Implementation:** `app/services/file_metadata_service.py`

---

### 4.5 Environment Configuration

**New Environment Variables:**
```env
# File Storage Configuration
FILE_STORAGE_PROVIDER=local  # Options: local, s3, gcs
FILE_STORAGE_PATH=/app/storage  # For local storage
FILE_MAX_SIZE=10485760  # 10MB in bytes

# S3 Configuration (if using S3)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET_NAME=...
AWS_S3_REGION=us-east-1

# GCS Configuration (if using Google Cloud Storage)
GCS_PROJECT_ID=...
GCS_BUCKET_NAME=...
GCS_CREDENTIALS_PATH=...
```

---

## 5. Database Migration

**Migration Script:** `migrations/versions/0016_add_resume_files_table.py`

```python
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
        sa.Column('storage_provider', sa.String(50), default='local'),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('upload_status', sa.String(50), default='pending'),
        sa.Column('is_processed', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_resume_files_user_id'), 
        'resume_files', 
        ['user_id'], 
        unique=False
    )
```

---

## 6. Security Considerations

### 6.1 Access Control
- Validate user ownership before file operations
- Use JWT tokens for authentication
- Implement rate limiting (100 files per hour per user)

### 6.2 File Security
- Validate file extensions and MIME types
- Scan uploaded files for malware (optional)
- Encrypt files at rest (for production S3)
- Use HTTPS for all file transfers

### 6.3 Data Privacy
- Ensure files are only accessible to their owner
- Implement audit logging for file operations
- Automatic deletion of old files (optional, configurable)

---

## 7. Performance Considerations

### 7.1 Optimization Strategies
- Implement async file processing for text extraction
- Cache extracted text in database
- Use CDN for file downloads
- Compress PDF files before storage
- Implement chunked uploads for large files

### 7.2 Caching
- Cache file metadata for 5 minutes
- Store extracted text previews (first 500 characters)
- Implement Redis caching for frequently accessed files

### 7.3 Monitoring
- Track upload/download times
- Monitor storage quota per user (optional: 500MB limit)
- Log failed operations for debugging

---

## 8. Testing Strategy

### 8.1 Unit Tests
- `test_file_validator.py` - File validation logic
- `test_file_storage_service.py` - Storage operations
- `test_file_processing_service.py` - Text extraction

### 8.2 Integration Tests
- `test_file_upload_endpoint.py` - Upload flow
- `test_file_download_endpoint.py` - Download flow
- `test_file_deletion_endpoint.py` - Deletion flow

### 8.3 End-to-End Tests
- Complete upload → process → score → export workflow
- Error handling and recovery
- Concurrent file operations

---

## 9. Deployment Checklist

- [ ] Database migration executed
- [ ] Environment variables configured
- [ ] Storage bucket created (if using cloud)
- [ ] File validator tests passing
- [ ] API endpoints tested with Swagger UI
- [ ] Integration with resume scoring verified
- [ ] Integration with Google Docs export verified
- [ ] Performance benchmarks met
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Deployed to staging
- [ ] Smoke tests passed
- [ ] Deployed to production

---

## 10. Future Enhancements

- **Batch Upload:** Support multiple file uploads at once
- **File Versioning:** Track document versions and changes
- **OCR Integration:** Extract text from image-based PDFs
- **Resume Parsing:** Advanced resume structure parsing
- **Template Conversion:** Convert between document formats
- **Collaborative Features:** Share documents with reviewers
- **Archive Feature:** Soft-delete with recovery window

