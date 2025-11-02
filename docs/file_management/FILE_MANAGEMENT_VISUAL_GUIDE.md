# 📊 File Management Feature - Visual Reference Guide

## API Endpoints at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                    FILE MANAGEMENT ENDPOINTS                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  POST   /files/upload          Upload resume file (PDF/DOCX)    │
│         Request: file, document_name, description               │
│         Response: {file_id, filename, size, extracted_text}     │
│                                                                 │
│  GET    /files                 List all user files              │
│         Query: page, per_page, sort_by, sort_order, search      │
│         Response: [{file_id, filename, size, date}, ...]        │
│                                                                 │
│  GET    /files/{id}/info       Get file metadata                │
│         Response: {file_id, filename, size, text_length, ...}   │
│                                                                 │
│  GET    /files/{id}            Download file                    │
│         Query: format (original|pdf)                            │
│         Response: binary file (attachment)                      │
│                                                                 │
│  DELETE /files/{id}            Delete single file               │
│         Response: {success, deleted_file_id}                    │
│                                                                 │
│  DELETE /files                 Bulk delete files                │
│         Request: {file_ids: [1, 2, 3]}                          │
│         Response: {deleted_count, failed_count}                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Model Relationships

```
┌──────────────────┐
│     Users        │
├──────────────────┤
│ id (PK)          │
│ username         │
│ email            │
│ ...              │
└────────┬─────────┘
         │ 1:N
         │
         ▼
┌──────────────────────┐
│    ResumeFile        │  ← NEW
├──────────────────────┤
│ id (PK)              │
│ user_id (FK)    ─────┼─→ Users
│ original_filename    │
│ file_size            │
│ file_extension       │
│ mime_type            │
│ storage_key          │
│ storage_provider     │
│ extracted_text       │
│ upload_status        │
│ is_processed         │
│ created_at           │
│ updated_at           │
└──────────────────────┘
```

---

## File Upload Flow

```
┌──────────────┐
│ User Selects │
│  PDF/DOCX    │
└───────┬──────┘
        │
        ▼
┌──────────────────────┐
│  Validate File       │
├──────────────────────┤
│ • Extension check    │
│ • MIME type check    │
│ • Size check (10MB)  │
│ • Not empty check    │
└───────┬──────────────┘
        │ ✓ Valid
        ▼
┌──────────────────────┐
│ Store in Storage     │
├──────────────────────┤
│ • Local FS OR        │
│ • AWS S3 OR          │
│ • Google Cloud Store │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────┐
│ Extract Text         │
├──────────────────────┤
│ • PDF → Parse PDF    │
│ • DOCX → Parse DOCX  │
│ • Store in DB        │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────┐
│ Create DB Record     │
├──────────────────────┤
│ • ResumeFile entry   │
│ • Metadata           │
│ • Extracted text     │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────┐
│ Return Response      │
├──────────────────────┤
│ • file_id            │
│ • filename           │
│ • file_size          │
│ • text_preview       │
│ • upload_status      │
└──────────────────────┘
```

---

## Request/Response Examples

### 1. Upload File

**Request:**
```http
POST /files/upload HTTP/1.1
Authorization: Bearer eyJhbGc...
Content-Type: multipart/form-data

--boundary123
Content-Disposition: form-data; name="file"; filename="resume.pdf"
Content-Type: application/pdf

[binary PDF content]
--boundary123
Content-Disposition: form-data; name="document_name"

My Professional Resume 2024
--boundary123--
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file": {
    "id": 42,
    "original_filename": "resume.pdf",
    "document_name": "My Professional Resume 2024",
    "file_size": 524288,
    "file_extension": "pdf",
    "mime_type": "application/pdf",
    "upload_status": "complete",
    "created_at": "2025-11-01T14:30:00Z",
    "extracted_text_preview": "John Doe\nSoftware Engineer\n5+ years experience...",
    "extracted_text_length": 2104,
    "formatted_file_size": "512 KB"
  }
}
```

---

### 2. List Files

**Request:**
```http
GET /files?page=1&per_page=10&sort_by=created_at&sort_order=desc&search=resume HTTP/1.1
Authorization: Bearer eyJhbGc...
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": 42,
        "original_filename": "resume.pdf",
        "file_size": 524288,
        "file_extension": "pdf",
        "mime_type": "application/pdf",
        "created_at": "2025-11-01T14:30:00Z",
        "upload_status": "complete",
        "is_processed": true,
        "formatted_file_size": "512 KB"
      },
      {
        "id": 41,
        "original_filename": "resume_draft.docx",
        "file_size": 312456,
        "file_extension": "docx",
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "created_at": "2025-10-28T10:15:00Z",
        "upload_status": "complete",
        "is_processed": true,
        "formatted_file_size": "305 KB"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 2,
      "total_pages": 1
    }
  }
}
```

---

### 3. Get File Metadata

**Request:**
```http
GET /files/42/info HTTP/1.1
Authorization: Bearer eyJhbGc...
```

**Response (200 OK):**
```json
{
  "success": true,
  "file": {
    "id": 42,
    "original_filename": "resume.pdf",
    "file_size": 524288,
    "file_extension": "pdf",
    "mime_type": "application/pdf",
    "created_at": "2025-11-01T14:30:00Z",
    "updated_at": "2025-11-01T14:30:00Z",
    "upload_status": "complete",
    "is_processed": true,
    "extracted_text_length": 2104,
    "extracted_text_preview": "John Doe\nSoftware Engineer\n5+ years experience...",
    "storage_provider": "s3",
    "formatted_file_size": "512 KB"
  }
}
```

---

### 4. Download File

**Request:**
```http
GET /files/42?format=original HTTP/1.1
Authorization: Bearer eyJhbGc...
```

**Response (200 OK):**
```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="resume.pdf"
Content-Length: 524288

[binary PDF content]
```

---

### 5. Delete File

**Request:**
```http
DELETE /files/42 HTTP/1.1
Authorization: Bearer eyJhbGc...
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "File deleted successfully",
  "deleted_file_id": 42
}
```

---

### 6. Bulk Delete Files

**Request:**
```http
DELETE /files HTTP/1.1
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "file_ids": [42, 41, 40]
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

## Error Responses

### Upload Errors

```json
{
  "success": false,
  "error": "FILE_NOT_PROVIDED",
  "message": "No file provided"
}

{
  "success": false,
  "error": "INVALID_FILE_TYPE",
  "message": "File type not allowed. Supported: pdf, docx"
}

{
  "success": false,
  "error": "FILE_TOO_LARGE",
  "message": "File too large. Maximum size: 10MB"
}

{
  "success": false,
  "error": "EMPTY_FILE",
  "message": "File is empty"
}
```

### Download/Delete Errors

```json
{
  "success": false,
  "error": "FILE_NOT_FOUND",
  "message": "File with ID 42 not found"
}

{
  "success": false,
  "error": "DOWNLOAD_FAILED",
  "message": "Error retrieving file from storage"
}
```

---

## Integration with Other APIs

### Resume Scoring with File

**Before:**
```json
POST /resume/score
{
  "resume_text": "John Doe...",
  "job_description": "We need..."
}
```

**Now (Alternative):**
```json
POST /resume/score
{
  "method": "file_id",
  "file_id": 42,
  "job_description": "We need..."
}
```

---

### Resume Generation with File

```json
POST /resume/generate
{
  "file_id": 42,
  "template_id": 2,
  "job_description": "Senior Engineer at Google...",
  "optimization_level": "aggressive"
}
```

---

### Google Docs Export with File

```json
POST /resume/export/gdocs
{
  "file_id": 42,
  "template_id": 2,
  "document_title": "Resume - Google Senior Engineer"
}
```

---

## Storage Architecture

### Local Storage (Development)
```
/app/storage/
├── {user_id}/
│   └── resumes/
│       └── {file_id}/
│           └── 20251101_143000_resume.pdf
└── {user_id2}/
    └── resumes/
        └── {file_id2}/
            └── 20251101_100000_resume_v2.docx
```

### AWS S3 (Production)
```
s3://bucket-name/
├── 1/resumes/abc-123/20251101_143000_resume.pdf
├── 1/resumes/def-456/20251101_100000_resume_v2.docx
├── 2/resumes/ghi-789/20251101_120000_resume.pdf
└── ...
```

### Google Cloud Storage (Production)
```
gs://bucket-name/
├── 1/resumes/abc-123/20251101_143000_resume.pdf
├── 1/resumes/def-456/20251101_100000_resume_v2.docx
├── 2/resumes/ghi-789/20251101_120000_resume.pdf
└── ...
```

---

## Database Schema

### ResumeFile Table

```sql
CREATE TABLE resume_files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    original_filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    file_extension VARCHAR(10) NOT NULL,
    mime_type VARCHAR(50) NOT NULL,
    storage_key VARCHAR(500) NOT NULL,
    storage_provider VARCHAR(50) DEFAULT 'local',
    extracted_text TEXT,
    upload_status VARCHAR(50) DEFAULT 'pending',
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);
```

---

## Service Components

```
┌────────────────────────────────────────────────────────────┐
│                   Flask API Endpoints                      │
│  /files/upload, /files, /files/{id}, /files/{id}/info     │
└─────────────────────┬──────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ FileValidator│ │FileProcessing│ │FileMetadata  │
│  (Validation)│ │  (Parsing)   │ │  (Database)  │
└──────────────┘ └──────────────┘ └──────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
                      ▼
        ┌─────────────────────────┐
        │ FileStorageService      │
        │ (Multi-provider support)│
        └─────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
    ┌────────┐   ┌────────┐   ┌────────┐
    │ Local  │   │ AWS S3 │   │  GCS   │
    │  FS    │   │        │   │        │
    └────────┘   └────────┘   └────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
                      ▼
            ┌──────────────────┐
            │ File Storage     │
            │ (Physical Files) │
            └──────────────────┘
```

---

## Environment Configuration

### Local Development
```env
FILE_STORAGE_PROVIDER=local
FILE_STORAGE_PATH=/app/storage
FILE_MAX_SIZE=10485760
```

### Production with S3
```env
FILE_STORAGE_PROVIDER=s3
FILE_MAX_SIZE=10485760
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_S3_BUCKET_NAME=my-resume-bucket
AWS_S3_REGION=us-east-1
```

### Production with GCS
```env
FILE_STORAGE_PROVIDER=gcs
FILE_MAX_SIZE=10485760
GCS_PROJECT_ID=my-project-123
GCS_BUCKET_NAME=my-resume-bucket
GCS_CREDENTIALS_PATH=/secrets/gcs-credentials.json
```

---

## Performance Metrics

### Upload Performance
- Small file (< 1MB): ~500ms
- Medium file (1-5MB): ~1-2s
- Large file (5-10MB): ~2-5s

### Download Performance
- S3: ~200-500ms (depends on region)
- Local: ~50-100ms
- GCS: ~200-500ms (depends on region)

### Text Extraction Performance
- Small PDF (< 50 pages): ~500ms
- Medium PDF (50-200 pages): ~1-2s
- Large PDF (> 200 pages): ~3-5s
- DOCX (any size): ~100-300ms

---

## Security Checklist

- [x] File extension whitelist (PDF, DOCX only)
- [x] MIME type validation
- [x] File size limit (10MB)
- [x] User ownership validation
- [x] JWT authentication required
- [x] Secure storage key generation (UUID)
- [x] Encrypted at rest (S3/GCS)
- [x] HTTPS for all transfers
- [x] Input sanitization
- [x] Rate limiting (recommended: 100 files/hour)
- [x] Audit logging
- [x] Error messages don't leak sensitive info

---

## Monitoring & Alerts

```
Monitor These Metrics:
├── Upload success rate (target: > 99%)
├── Average upload time (target: < 2s)
├── Storage usage per user (warn at: 80% quota)
├── Failed downloads (target: < 0.1%)
├── Failed deletions (target: < 0.1%)
├── API response time (target: < 1.5s)
├── Storage provider availability (target: > 99.9%)
├── Database connection errors
├── Unauthorized access attempts
└── Virus/malware detections
```

