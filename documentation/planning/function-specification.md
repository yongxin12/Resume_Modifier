
---

# 📄 Project Requirements Document


---

## 1. Project Overview

**Resume Modifier** is an AI-powered platform designed to help job seekers efficiently **analyze and score resumes**, and **improve job-resume matching** through automated intelligence and data integration.
The tool aims to serve North American and global job seekers by integrating DataSum’s job APIs with custom-built resume scoring and AI recommendation systems.

* **Backend:** Flask
* **Database:** PostgreSQL
* **AI Services:** OpenAI API / Custom NLP model
* **Primary APIs:** Resume Upload, Job Search, Resume Scoring

---

## 2. Functional Requirements Table

| Req ID     | Description                              | User Story                                                                                                 | Expected Behavior / Outcome                                                                                                                       |
| ---------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |                                                |
| **API-02** | **Health Check Endpoint**                | As a developer, I want a health check route so I can confirm the backend is running.                       | `/health` endpoint returns `{ status: "OK" }` with HTTP 200.                                                                                      |
| **API-03** | **Database Configuration**               | As a backend developer, I want a reliable database connection so the API can persist user and resume data. | PostgreSQL or MongoDB connection established with ORM (SQLAlchemy / Prisma / Mongoose). `.env` variables include DB credentials.                  |
| **API-03a** | **User Registration API**                | As a user, I want to create an account with email and password so I can access the platform.               | `/api/register` POST endpoint accepts email/password, validates uniqueness, hashes password, and returns user ID with JWT token.                  |
| **API-03b** | **User Login API**                       | As a user, I want to log in with my credentials so I can access my account.                                | `/api/login` POST endpoint validates credentials, returns JWT token for authenticated sessions.                                                    |
| **API-03c** | **Password Reset Request API**           | As a user, I want to request a password reset via email when I forget my password.                        | `/api/auth/password-reset/request` POST endpoint accepts email, generates secure token, sends reset email, returns confirmation message.          |
| **API-03d** | **Password Reset Verification API**      | As a user, I want to verify my reset token and set a new password securely.                               | `/api/auth/password-reset/verify` POST endpoint accepts token and new password, validates token, updates password hash, invalidates token.        |
| **API-03e** | **Password Reset Token Validation API**  | As a user, I want to check if my password reset token is valid before submitting a new password.          | `/api/auth/password-reset/validate` GET endpoint accepts token parameter, returns validity status and expiration info without consuming token.    |
| **API-03f** | **Admin User Management**                | As an administrator, I need specific user accounts to have admin privileges for Google Drive integration management. | User model includes `is_admin` boolean field. Only admin users can authenticate with Google and manage centralized Google Drive storage. |
| **API-04** | **Automatic API Documentation**          | As a developer, I want to automatically generate API docs so endpoints are always documented.              | Swagger UI or Redoc is auto-generated from FastAPI routes and available at `/docs` or `/api/docs`.                                                |
| **API-05** | **File Upload Management**               | As a user, I want to upload PDFs or other resume file formats to store documents, enabling me to delete or download these files, or use them for resume processing. | `/files/upload` POST endpoint accepts PDF or DOCX, stores in cloud/local storage, and returns file metadata including file ID and extracted text preview. |
| **API-05e** | **Duplicate File Handling**              | As a user, I want to receive notifications when uploading duplicate resume PDF files; files with identical names should be distinguished by appending a sequential duplicate number, e.g., (1). | System detects duplicate file hashes, displays notification, and saves with incremented filename like "Resume.pdf", "Resume (1).pdf", "Resume (2).pdf". |
| **API-05f** | **Google Drive Integration (Admin Only)** | As an administrator, I want all uploaded documents to be stored simultaneously in both the database and the administrator's Google Drive using admin-only Google authentication. | Each uploaded file is automatically stored in admin's Google Drive folder using admin's authenticated Google account. Only administrators can authenticate with Google. |
| **API-05g** | **Google Drive Sharing (Admin-Controlled)** | As an administrator, I want to share Google Doc links for uploaded files from my Google Drive with file owners, granting them edit permissions while maintaining centralized storage control. | After upload to admin's Google Drive, system converts PDF/DOCX to Google Doc, makes publicly editable via link, and provides shareable link only to file owner. |
| **API-05h** | **Soft Deletion System**                 | As a node administrator or developer, I need to implement soft deletion functionality to preserve all data in case of user errors. | Files are marked as deleted (`is_active=false`) but preserved in database and storage. Admin interface allows restoration of deleted files. |
| **API-05i** | **Google Doc Link Access**               | As a user, I want to obtain the Google Doc link for uploaded files to make modifications. | `/files/{id}/google-doc` GET endpoint returns Google Doc link with edit permissions for the user to collaborate on their document. |
| **API-05j** | **Deleted Files Filtering**              | As a user, I do not want to see deleted files. | All file listing APIs automatically filter out soft-deleted files (`is_active=false`) unless admin explicitly requests to see deleted files. |
| **API-05k** | **File Categorization System**           | As a user, I want to organize my uploaded files into categories (Active, Archived, Draft) for better file management and organization. | Files can be assigned one of three categories: 'active', 'archived', or 'draft'. Category assignment is for organizational purposes only and doesn't affect file functionality. |
| **API-05l** | **File Category Assignment**             | As a user, I want to assign or change the category of my uploaded files to keep them organized. | `PUT /files/{id}/category` endpoint accepts category parameter and updates file categorization. Validates category is one of: active, archived, draft. |
| **API-05m** | **File Category Filtering**              | As a user, I want to filter my file listings by category to quickly find files in specific organizational states. | `/files` GET endpoint supports `category` query parameter to filter results by: active, archived, draft, or 'all' for no filtering. |
| **API-05n** | **Bulk Category Assignment**             | As a user, I want to change the category of multiple files at once for efficient organization. | `PUT /files/category` endpoint accepts array of file_ids and target category, updates multiple files simultaneously with validation. |
| **API-05o** | **Category Statistics**                  | As a user, I want to see how many files I have in each category to understand my file organization. | `/files/categories/stats` GET endpoint returns count of files in each category plus total file count for the authenticated user. |
| **API-05a** | **File Download API**                    | As a user, I want to download my stored resume documents in their original format or as PDF.               | `/files/{id}` GET endpoint returns binary file with appropriate content headers for download. Supports format conversion parameter.                |
| **API-05b** | **File List API**                        | As a user, I want to view all my uploaded resume documents with metadata like size, upload date, and format. | `/files` GET endpoint returns paginated list of user's documents with metadata. Supports sorting, filtering, and search functionality.              |
| **API-05c** | **File Metadata API**                    | As a user, I want to retrieve detailed information about a specific document including extracted text summary. | `/files/{id}/info` GET endpoint returns comprehensive file metadata including extracted text preview and processing status.                       |
| **API-05c-1** | **File Thumbnail Generation**           | As a user, I want thumbnails generated automatically when I upload PDFs so I can quickly identify documents. | System automatically generates 150x200px thumbnails from first page of uploaded PDF files during processing workflow.                          |
| **API-05c-2** | **File Thumbnail API**                  | As a user, I want to see thumbnails of the files I want to preview so I can quickly identify correct resumes. | `/files/{id}/info` includes `thumbnail` object with `thumbnail_url`, `has_thumbnail`, and `thumbnail_status` fields in response.                |
| **API-05c-3** | **Thumbnail Endpoint**                  | As a user, I want direct access to thumbnail images with proper caching for performance.                   | `/files/{id}/thumbnail` GET endpoint serves thumbnail images with cache headers. Returns default placeholder when unavailable.                   |
| **API-05d** | **File Deletion API**                    | As a user, I want to delete stored resume documents to manage storage and remove outdated files.           | `/files/{id}` DELETE endpoint removes document from storage and database. Returns confirmation. Bulk deletion via `/files` DELETE with file_ids array. |
| **API-06** | **Resume Upload API**                    | As a user, I want to upload my resume so I can receive analysis and feedback.                              | `/resume/upload` POST endpoint accepts PDF or DOCX, stores it in S3 / Supabase storage, and returns file metadata.                                |
| **API-07** | **Resume Scoring API**                   | As a user, I want my resume scored by AI so I can understand my job fit.                                   | `/resume/score` POST endpoint accepts resume text, file, or file_id and returns a structured JSON score.                                         |
| **API-08** | **AI Resume Scoring Model**              | As a developer, I want to integrate an AI model to score resumes based on key metrics.                     | Uses OpenAI API or custom NLP model to evaluate **keyword matching**, **language clarity**, and **ATS readability**.                              |
| **API-09** | **Scoring Breakdown**                    | As a user, I want to see detailed evaluation of my resume quality.                                         | Output JSON format:<br>`{ "overall_score": 85, "keyword_match": 88, "language_expression": 80, "ats_readability": 87 }`                           |
| **API-10** | **Frontend Integration with Backend**    | As a developer, I want the frontend to consume APIs correctly so users can see live data.                  | CORS configured, frontend can access backend routes securely. All major endpoints return consistent JSON structure.                               |
| **API-11** | **Resume Template Management**           | As a user, I want to select from multiple resume templates for professional formatting.                    | `/templates` GET endpoint returns available templates. Templates stored as structured data with styling rules and layout definitions.              |
| **API-12** | **Google Docs Authentication (Admin Only)** | As an administrator, I want to authenticate with Google to enable document storage and sharing functionality for all users. | OAuth 2.0 flow for Google Docs API access. `/auth/google` endpoint restricted to administrators only. Handles authentication and stores tokens securely. |
| **API-12a** | **Persistent OAuth Authentication** | As an administrator, after completing OAuth authentication, I do not wish to repeat the process each time. I prefer to maintain the authenticated state until receiving a warning when storage space is nearly full. | System maintains OAuth token persistence with automatic refresh, eliminating need for re-authentication. Authentication state persists across sessions until manual revocation or storage warnings. |
| **API-12b** | **Google Drive Storage Monitoring** | As an administrator, I want to receive warnings when Google Drive storage space is nearly full to manage storage capacity proactively. | System monitors Google Drive storage usage and sends warnings at 80%, 90%, and 95% capacity thresholds. Provides storage usage analytics and cleanup recommendations. |
| **API-13** | **Resume Generation API**                | As a user, I want to generate a professionally formatted resume using my data and selected template.       | `/resume/generate` POST endpoint combines user data from uploaded files, job description, and template to create formatted resume content.          |
| **API-14** | **Google Docs Export API**               | As a user, I want to export my generated resume as a Google Doc for professional presentation.             | `/resume/export/gdocs` POST endpoint creates Google Doc from file_id or generated content, applies formatting, and returns shareable link.          |
| **API-15** | **Document Format Export**               | As a user, I want to download my resume in multiple formats (PDF, DOCX) from Google Docs.                 | Uses Google Drive API to export created document in PDF/DOCX format and returns downloadable file or streaming response.                          |

---

## 3. Technical Implementation Details

### **Backend Setup**

* Framework: **Flask** (Python) - as per current implementation
* Deployment: **Railway**
* Environment variables:

  ```
  DATABASE_URL=...
  OPENAI_API_KEY=...
  STORAGE_BUCKET_URL=...
  GOOGLE_CLIENT_ID=...
  GOOGLE_CLIENT_SECRET=...
  GOOGLE_REDIRECT_URI=...
  FILE_STORAGE_PROVIDER=local|s3|gcs
  FILE_STORAGE_PATH=/app/storage
  FILE_MAX_SIZE=10485760
  AWS_ACCESS_KEY_ID=... (if using S3)
  AWS_SECRET_ACCESS_KEY=... (if using S3)
  AWS_S3_BUCKET_NAME=... (if using S3)
  # Email Configuration for Password Recovery
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USERNAME=...
  SMTP_PASSWORD=...
  SMTP_USE_TLS=true
  EMAIL_FROM_ADDRESS=noreply@resumemodifier.com
  EMAIL_FROM_NAME=Resume Modifier
  # Password Reset Configuration
  PASSWORD_RESET_TOKEN_EXPIRY=3600  # 1 hour in seconds
  PASSWORD_RESET_SECRET_KEY=...  # For token signing
  FRONTEND_URL=http://localhost:3000  # For reset link generation
  # Google Drive Integration Configuration
  GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE=/path/to/service-account.json
  GOOGLE_DRIVE_ADMIN_EMAIL=admin@resumemodifier.com  # Admin Google account
  GOOGLE_DRIVE_FOLDER_ID=1abc123def456ghi789  # Root folder for resume files
  GOOGLE_DRIVE_ENABLE_SHARING=true  # Whether to share files with users
  GOOGLE_DRIVE_DEFAULT_PERMISSIONS=writer  # Default permissions for shared files
  ```
* Ensure `.env` is added to `.gitignore`
* Required Python packages:
  ```
  google-api-python-client
  google-auth-httplib2
  google-auth-oauthlib
  jinja2
  weasyprint (for PDF generation as fallback)
  python-docx (for DOCX parsing)
  pypdf (for PDF text extraction)
  boto3 (for AWS S3 support, optional)
  # Email and Security packages for Password Recovery
  flask-mail==0.9.1
  itsdangerous==2.1.2
  email-validator==2.1.0
  ```

### **Database**

* **Option A (preferred):** PostgreSQL (with SQLAlchemy ORM)
* **Option B:** MongoDB (Mongoose)
* Store:

  * Job data cache
  * Resume metadata and scoring history
  * User identifiers with admin privileges
  * Google authentication tokens (admin only)

#### **Enhanced User Model for Admin Management**
```python
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
    is_admin = db.Column(db.Boolean, default=False, nullable=False)  # Admin privilege for Google Drive access
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Admin User Management:**
- Only users with `is_admin=True` can authenticate with Google OAuth
- Admin users manage centralized Google Drive storage for all uploaded files
- First registered user is automatically made admin during database setup
- Additional admin users can be created manually by existing admins

### **API Documentation**

* Auto-generated **Swagger UI** (`/docs`) and **OpenAPI JSON Schema**
* Updated automatically from route definitions

### **Health Check**

* Endpoint: `/health`
* Method: `GET`
* Response Example:

  ```json
  { "status": "OK", "timestamp": "2025-10-11T10:00:00Z" }
  ```
* Use for CI/CD and Railway deployment verification

### **AI Resume Scoring**

* Integration with OpenAI GPT or local NLP model
* Scoring logic:

  1. Extract keywords from job description
  2. Compare with resume text (keyword match %)
  3. Use AI prompt to assess language tone and clarity
  4. Calculate ATS-readability using regex and heuristic metrics

### **File Management System (NEW)**

#### **Overview**
Comprehensive document storage and management enabling users to upload, store, download, and delete resume files (PDF, DOCX) while maintaining version history and integrating with resume scoring and generation features.

#### **Database Model: ResumeFile (Enhanced)**
```python
class ResumeFile(db.Model):
    __tablename__ = 'resume_files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_size = db.Column(db.Integer, nullable=False)  # bytes
    mime_type = db.Column(db.String(100), nullable=False)
    storage_type = db.Column(db.String(50), nullable=False, default='local')  # 'local' or 's3'
    file_path = db.Column(db.String(500), nullable=False)  # Local path or S3 key
    s3_bucket = db.Column(db.String(100), nullable=True)  # S3 bucket name if using S3
    file_hash = db.Column(db.String(64), nullable=False)  # SHA-256 hash (NOT unique anymore)
    
    # Google Drive Integration Fields
    google_drive_file_id = db.Column(db.String(100), nullable=True)  # Google Drive file ID
    google_doc_id = db.Column(db.String(100), nullable=True)  # Google Doc ID (if converted)
    google_drive_link = db.Column(db.String(500), nullable=True)  # Direct link to Google Drive file
    google_doc_link = db.Column(db.String(500), nullable=True)  # Direct link to Google Doc
    is_shared_with_user = db.Column(db.Boolean, default=False)  # Whether shared with user
    
    # Processing and Content Fields
    is_processed = db.Column(db.Boolean, default=False)
    extracted_text = db.Column(db.Text, nullable=True)
    processing_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    processing_error = db.Column(db.Text, nullable=True)
    
    # Duplicate Handling Fields
    is_duplicate = db.Column(db.Boolean, default=False)  # Whether this is a duplicate file
    duplicate_sequence = db.Column(db.Integer, default=0)  # Sequence number for duplicates (0 = original)
    original_file_id = db.Column(db.Integer, db.ForeignKey('resume_files.id'), nullable=True)  # Reference to original file
    
    # Soft Deletion and Metadata
    is_active = db.Column(db.Boolean, default=True)  # For soft delete functionality
    deleted_at = db.Column(db.DateTime, nullable=True)  # Timestamp when soft deleted
    deleted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Who deleted it
    tags = db.Column(db.JSON, nullable=True, default=list)  # User-defined tags
    
    # File Organization and Categorization Fields (NEW)
    category = db.Column(db.String(20), nullable=False, default='active')  # active, archived, draft
    category_updated_at = db.Column(db.DateTime, nullable=True)  # When category was last changed
    category_updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Who changed category
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='resume_files', lazy=True)
    deleted_by_user = db.relationship('User', foreign_keys=[deleted_by], lazy=True)
    original_file = db.relationship('ResumeFile', remote_side=[id], backref='duplicates')
```

#### **Enhanced File Upload Workflow (API-05 + New Features)**
```
1. POST /files/upload with multipart file
2. Validate: file extension, MIME type, size (max 10MB)
3. Calculate SHA-256 hash of file content for duplicate detection
4. Check for existing files with same hash for same user
5. If duplicate found:
   a. Generate incremented filename (e.g., "Resume (1).pdf")
   b. Set is_duplicate=True and reference original_file_id
   c. Return notification about duplicate detection
6. Extract text using parse_pdf_file() utility (if process=true)
7. Store file in local/S3 storage with unique stored_filename
8. Upload file to Google Drive in organized folder structure
9. Convert PDF/DOCX to Google Doc (if requested)
10. Share Google Doc with user email (edit permissions)
11. Create ResumeFile database record with all metadata
12. Return comprehensive response with file info and Google links
```

#### **Duplicate File Handling Workflow (API-05e)**
```
1. System calculates file hash during upload
2. Query database for existing files with same hash and user_id
3. If duplicates exist:
   a. Count existing duplicates to determine sequence number
   b. Generate new filename: "Original.pdf" → "Original (1).pdf" → "Original (2).pdf"
   c. Set duplicate metadata: is_duplicate=True, duplicate_sequence=N, original_file_id=X
   d. Display notification: "Duplicate file detected. Saved as 'Resume (1).pdf'"
4. Store duplicate with all same processing as original
5. Allow users to view duplicate relationship in file info
```

#### **Google Drive Integration Workflow (API-05f, API-05g)**
```
1. After successful local/S3 storage:
   a. Authenticate with Google Drive API using service account
   b. Create organized folder structure: /Resume Files/{user_email}/{YYYY-MM}/
   c. Upload file to Google Drive folder
   d. Store google_drive_file_id in database
2. If document conversion requested:
   a. Convert PDF/DOCX to Google Doc format
   b. Store google_doc_id and google_doc_link
3. Share document with user:
   a. Add user email with "writer" permissions
   b. Set is_shared_with_user=True
   c. Return shareable links in API response
```

#### **Soft Deletion Workflow (API-05h)**
```
1. DELETE /files/{id} (soft delete):
   a. Set is_active=False
   b. Set deleted_at=current_timestamp
   c. Set deleted_by=current_user_id
   d. Keep file in storage and all metadata intact
2. File listing APIs automatically filter is_active=True
3. Admin endpoints can access deleted files
4. Restore functionality available for admins
```

**Request Example:**
```
POST /files/upload HTTP/1.1
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data

file=<binary_data>
document_name=My Professional Resume
```

**Response Example (201 Created):**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file": {
    "id": 42,
    "original_filename": "Resume_2024.pdf",
    "document_name": "My Professional Resume",
    "file_size": 524288,
    "file_extension": "pdf",
    "mime_type": "application/pdf",
    "upload_status": "complete",
    "created_at": "2025-11-01T10:30:00Z",
    "extracted_text_preview": "John Doe\nSoftware Engineer with 5+ years...",
    "extracted_text_length": 2104
  }
}
```

#### **File Download (API-05a)**
```
GET /files/{id}?format=original
- Returns binary file with Content-Disposition: attachment header
- Supports format parameter: 'original' or 'pdf' (converts DOCX to PDF)
- Validates user owns the file before download
```

#### **File Listing (API-05b)**
```
GET /files?page=1&per_page=20&sort_by=created_at&sort_order=desc&search=resume
- Returns paginated list of user's uploaded files
- Includes metadata: filename, size, type, upload_date, status
- Supports sorting by: created_at, filename, file_size
- Supports filtering by status and file extension
```

**Response Example (200 OK):**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": 42,
        "original_filename": "Resume_2024.pdf",
        "file_size": 524288,
        "file_extension": "pdf",
        "mime_type": "application/pdf",
        "created_at": "2025-11-01T10:30:00Z",
        "upload_status": "complete",
        "is_processed": true,
        "formatted_file_size": "512 KB"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 8,
      "total_pages": 1
    }
  }
}
```

#### **File Metadata (API-05c) - Enhanced with Thumbnails**
```
GET /files/{id}/info
- Returns detailed file information including thumbnail data
- Includes: extracted_text length, storage_provider, processing_status
- NEW: thumbnail object with has_thumbnail, thumbnail_url, thumbnail_status
- Response format:
{
  "success": true,
  "file": {
    "id": 42,
    "original_filename": "Resume_2024.pdf",
    // ... existing fields ...
    "thumbnail": {
      "has_thumbnail": true,
      "thumbnail_url": "/api/files/42/thumbnail",
      "thumbnail_status": "completed",
      "thumbnail_generated_at": "2025-11-22T10:30:00Z"
    }
  }
}
```

#### **Thumbnail Generation (API-05c-1)**
```
- Automatic PDF thumbnail generation during file processing
- Generates 150x200px JPEG thumbnails from first page
- Asynchronous processing with status tracking
- Fallback to default placeholder for generation failures
- Storage: /uploads/thumbnails/{file_id}.jpg
```

#### **Thumbnail Access (API-05c-3)**
```
GET /files/{id}/thumbnail
- Serves thumbnail image directly with proper MIME type
- Requires authentication (JWT token)
- User authorization: access only own files
- Cache headers for performance optimization
- Returns default placeholder when thumbnail unavailable
- Content-Type: image/jpeg
- Cache-Control: public, max-age=86400
```

#### **File Deletion (API-05d) - Enhanced with Soft Delete**
```
DELETE /files/{id}?permanent=false
- Default: Soft delete (set is_active=false, preserve data)
- With permanent=true: Hard delete (remove from storage and database)
- Validates ownership before deletion
- Returns deletion type and confirmation

DELETE /files (bulk) 
- Accepts JSON array of file_ids and permanent flag
- Soft delete by default, hard delete with permanent=true
- Returns deleted_count, failed_count, and deletion_type
```

#### **Google Doc Access (API-05i)**
```
GET /files/{id}/google-doc
- Returns Google Doc link for the uploaded file
- Validates user ownership or shared access
- Creates Google Doc if not already converted
- Shares with user if not already shared
- Returns both view and edit links
```

**Response Example (200 OK):**
```json
{
  "success": true,
  "google_doc": {
    "doc_id": "1abc123def456ghi789",
    "edit_link": "https://docs.google.com/document/d/1abc123.../edit",
    "view_link": "https://docs.google.com/document/d/1abc123.../view",
    "is_shared": true,
    "permissions": "writer",
    "created_at": "2025-11-14T10:30:00Z"
  },
  "file_info": {
    "id": 123,
    "original_filename": "Resume.pdf",
    "is_duplicate": false
  }
}
```

#### **Deleted Files Management (Admin Only)**
```
GET /admin/files/deleted
- Lists all soft-deleted files across all users
- Includes deletion metadata (deleted_by, deleted_at)
- Supports pagination and filtering

POST /admin/files/{id}/restore
- Restores soft-deleted file (set is_active=true)
- Clears deletion metadata
- Returns restored file info

DELETE /admin/files/{id}/permanent
- Permanently deletes soft-deleted file
- Removes from storage and database
- Irreversible operation
```

#### **Enhanced File Upload Response (Updated API-05)**
**Response Example with New Features (201 Created):**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "duplicate_detected": true,
  "duplicate_notification": "Duplicate file detected. Saved as 'Resume (1).pdf'",
  "file": {
    "id": 42,
    "original_filename": "Resume.pdf",
    "stored_filename": "Resume (1).pdf",
    "file_size": 524288,
    "mime_type": "application/pdf",
    "is_duplicate": true,
    "duplicate_sequence": 1,
    "original_file_id": 38,
    "upload_status": "complete",
    "created_at": "2025-11-14T10:30:00Z",
    "extracted_text_preview": "John Doe\nSoftware Engineer with 5+ years...",
    "google_drive": {
      "file_id": "1xyz789abc123def456",
      "drive_link": "https://drive.google.com/file/d/1xyz789.../view",
      "doc_link": "https://docs.google.com/document/d/1abc123.../edit",
      "is_shared": true,
      "shared_with": "user@example.com"
    }
  }
}
```

#### **Storage Strategy**
**Production:** AWS S3 or Google Cloud Storage
- Path: `s3://bucket/{user_id}/resumes/{file_id}/{timestamp}_{filename}`
- Benefits: Scalable, automatic backups, CDN-friendly

**Development:** Local filesystem
- Path: `/app/storage/resumes/{user_id}/{file_id}/{filename}`
- Easy testing without cloud dependencies

**Configuration via Environment:**
```env
FILE_STORAGE_PROVIDER=local|s3|gcs
FILE_STORAGE_PATH=/app/storage  # Local only
FILE_MAX_SIZE=10485760  # 10MB
AWS_ACCESS_KEY_ID=...  # S3 only
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET_NAME=...
```

#### **File Validation**
- **Supported Formats:** PDF (.pdf), DOCX (.docx)
- **Maximum Size:** 10 MB
- **MIME Type Validation:** Verify against allowed types
- **File Extension Check:** Ensure extension matches content

#### **Text Extraction**
- Uses existing `parse_pdf_file()` utility for PDF parsing
- Uses `python-docx` library for DOCX parsing
- Stores full text in database for later AI processing
- Generates preview (first 500 characters) for UI display

#### **Service Components**
1. **FileStorageService** - Save, retrieve, delete from storage provider
2. **FileProcessingService** - Extract text, validate, convert formats
3. **FileMetadataService** - Database operations with pagination and filtering
4. **FileCategoryService** - Category assignment, validation, and statistics (NEW)

---

### **File Categorization System (NEW)**

#### **Overview**
File categorization system allows users to organize their uploaded resume files into three predefined categories for better file management and organization. This is a front-end organizational feature that doesn't affect file functionality.

#### **Category Types**
- **Active**: Frequently used files, ready for immediate use (default)
- **Archived**: Infrequently used files, stored for reference
- **Draft**: Work-in-progress files, not yet finalized

#### **Enhanced Database Model Updates**
The ResumeFile model includes new categorization fields:
- `category`: VARCHAR(20) NOT NULL DEFAULT 'active'
- `category_updated_at`: DATETIME NULL (timestamp of last category change)
- `category_updated_by`: INT NULL (foreign key to users.id)

#### **Category Assignment Workflow (API-05l)**
```
PUT /files/{id}/category
1. Validate user owns the file
2. Validate category is one of: 'active', 'archived', 'draft'
3. Update file.category, category_updated_at, category_updated_by
4. Return updated file metadata with new category
```

**API Specification:**
- **Endpoint**: `PUT /files/{id}/category`
- **Authentication**: Required (Bearer JWT token)
- **Content-Type**: `application/json`

**Path Parameters:**
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `id` | integer | Yes | Unique file identifier | `42` |

**Request Headers:**
| Header | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `Authorization` | string | Yes | JWT bearer token | `Bearer eyJ0eXAiOiJKV1Q...` |
| `Content-Type` | string | Yes | Request content type | `application/json` |

**Request Body Schema:**
| Field | Type | Required | Validation | Description | Example |
|-------|------|----------|------------|-------------|---------|
| `category` | string | Yes | Must be one of: 'active', 'archived', 'draft' | Target category for file | `"archived"` |

**Request Example:**
```json
PUT /files/42/category
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "category": "archived"
}
```

**Response Example (200 OK):**
```json
{
  "success": true,
  "message": "File category updated successfully",
  "file": {
    "id": 42,
    "original_filename": "Resume_2024.pdf",
    "category": "archived",
    "category_updated_at": "2025-11-16T10:30:00Z",
    "category_updated_by": 123,
    "created_at": "2025-11-01T10:30:00Z",
    "updated_at": "2025-11-16T10:30:00Z"
  }
}
```

#### **Category Filtering Workflow (API-05m)**
```
GET /files?category=active&page=1&per_page=20
1. Validate category parameter (active, archived, draft, or 'all')
2. Filter files by user_id, is_active=true, and category (if specified)
3. Apply pagination and sorting
4. Return filtered file list with metadata
```

**API Specification:**
- **Endpoint**: `GET /files`
- **Authentication**: Required (Bearer JWT token)
- **Content-Type**: Not required for GET requests

**Request Headers:**
| Header | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `Authorization` | string | Yes | JWT bearer token | `Bearer eyJ0eXAiOiJKV1Q...` |

**Query Parameters:**
| Parameter | Type | Required | Default | Validation | Description | Example |
|-----------|------|----------|---------|------------|-------------|---------|
| `category` | string | No | null (all files) | 'active', 'archived', 'draft', 'all' | Filter files by category | `active` |
| `page` | integer | No | 1 | Minimum: 1 | Page number for pagination | `1` |
| `per_page` | integer | No | 20 | Range: 1-100 | Items per page | `20` |
| `sort_by` | string | No | 'created_at' | 'created_at', 'updated_at', 'original_filename', 'file_size', 'category' | Field to sort by | `created_at` |
| `sort_order` | string | No | 'desc' | 'asc', 'desc' | Sort direction | `desc` |
| `search` | string | No | null | Max length: 255 | Search term for filename filtering | `resume` |

**Request Examples:**
```
GET /files?category=active
GET /files?category=archived&sort_by=created_at&sort_order=desc
GET /files?category=draft&search=resume
GET /files?category=all&page=2&per_page=10
GET /files  // No category filtering (shows all files)
```

**Response Example (200 OK):**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": 42,
        "original_filename": "Resume_Active.pdf",
        "category": "active",
        "file_size": 524288,
        "formatted_file_size": "512 KB",
        "created_at": "2025-11-01T10:30:00Z",
        "category_updated_at": "2025-11-10T15:20:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 8,
      "total_pages": 1
    },
    "filter": {
      "category": "active"
    }
  }
}
```

#### **Bulk Category Assignment Workflow (API-05n)**
```
PUT /files/category
1. Validate request contains file_ids array and target category
2. Verify user owns all specified files
3. Validate category is one of: 'active', 'archived', 'draft'
4. Update all files in single transaction
5. Return summary of successful and failed updates
```

**API Specification:**
- **Endpoint**: `PUT /files/category`
- **Authentication**: Required (Bearer JWT token)
- **Content-Type**: `application/json`

**Request Headers:**
| Header | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `Authorization` | string | Yes | JWT bearer token | `Bearer eyJ0eXAiOiJKV1Q...` |
| `Content-Type` | string | Yes | Request content type | `application/json` |

**Request Body Schema:**
| Field | Type | Required | Validation | Description | Example |
|-------|------|----------|------------|-------------|---------|
| `file_ids` | array[integer] | Yes | Non-empty array, max 100 items | Array of file IDs to update | `[42, 43, 44]` |
| `category` | string | Yes | Must be one of: 'active', 'archived', 'draft' | Target category for all files | `"archived"` |

**Request Example:**
```json
PUT /files/category
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "file_ids": [42, 43, 44],
  "category": "archived"
}
```

**Response Example (200 OK):**
```json
{
  "success": true,
  "message": "Bulk category update completed",
  "summary": {
    "total_requested": 3,
    "successful_updates": 3,
    "failed_updates": 0,
    "category": "archived"
  },
  "updated_files": [
    {
      "id": 42,
      "original_filename": "Resume_A.pdf",
      "category": "archived"
    },
    {
      "id": 43,
      "original_filename": "Resume_B.pdf", 
      "category": "archived"
    },
    {
      "id": 44,
      "original_filename": "Resume_C.pdf",
      "category": "archived"
    }
  ],
  "failed_files": []
}
```

#### **Category Statistics Workflow (API-05o)**
```
GET /files/categories/stats
1. Query database for file counts by category for authenticated user
2. Calculate totals for active files only (is_active=true)
3. Return comprehensive statistics
```

**API Specification:**
- **Endpoint**: `GET /files/categories/stats`
- **Authentication**: Required (Bearer JWT token)
- **Content-Type**: Not required for GET requests

**Request Headers:**
| Header | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `Authorization` | string | Yes | JWT bearer token | `Bearer eyJ0eXAiOiJKV1Q...` |

**Query Parameters:**
None - This endpoint returns statistics for the authenticated user automatically.

**Request Example:**
```
GET /files/categories/stats
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response Example (200 OK):**
```json
{
  "success": true,
  "statistics": {
    "categories": {
      "active": {
        "count": 15,
        "percentage": 60.0
      },
      "archived": {
        "count": 8,
        "percentage": 32.0
      },
      "draft": {
        "count": 2,
        "percentage": 8.0
      }
    },
    "total_files": 25,
    "total_active_files": 25,
    "total_deleted_files": 3,
    "last_updated": "2025-11-16T10:30:00Z"
  }
}
```

#### **Enhanced File Listing Integration**
The existing `/files` endpoint is enhanced to support category filtering while maintaining backward compatibility:

**Updated Query Parameters:**
- `category`: Filter by specific category ('active', 'archived', 'draft') or 'all' for no filtering
- Existing parameters (page, per_page, sort_by, sort_order, search) remain unchanged

**Default Behavior:**
- If no category parameter is provided, returns all active files (existing behavior)
- Default category for new uploads remains 'active'

#### **Database Migration Requirements**
```sql
-- Add category-related columns to resume_files table
ALTER TABLE resume_files 
ADD COLUMN category VARCHAR(20) NOT NULL DEFAULT 'active',
ADD COLUMN category_updated_at DATETIME NULL,
ADD COLUMN category_updated_by INT NULL,
ADD CONSTRAINT fk_category_updated_by FOREIGN KEY (category_updated_by) REFERENCES users(id),
ADD CONSTRAINT check_valid_category CHECK (category IN ('active', 'archived', 'draft'));

-- Add indexes for efficient category queries
CREATE INDEX idx_resume_files_category ON resume_files(user_id, category, is_active);
CREATE INDEX idx_resume_files_category_updated ON resume_files(category_updated_at);
```

#### **Validation Rules**
1. **Category Values**: Must be exactly one of: 'active', 'archived', 'draft' (case-sensitive)
2. **File Ownership**: Users can only categorize their own files
3. **Active Files Only**: Category changes only apply to active files (is_active=true)
4. **Concurrent Updates**: Use database-level constraints to prevent invalid states

#### **Error Handling**
- **Invalid Category**: HTTP 400 with clear validation message
- **File Not Found**: HTTP 404 for non-existent or inaccessible files
- **Unauthorized Access**: HTTP 403 for files owned by other users
- **Bulk Operation Failures**: Partial success responses with detailed error info

#### **Integration Points**
- **File Upload**: New files default to 'active' category
- **File Metadata**: Category information included in all file detail responses
- **Search/Filter**: Category filtering integrated with existing search functionality
- **Statistics Dashboard**: Category stats available for user dashboard displays

#### **Integration with Resume Scoring (API-07)**
Score existing uploaded file without re-uploading:
```json
POST /resume/score
{
  "method": "file_id",
  "file_id": 42,
  "job_description": "Marketing Manager at TechCorp..."
}
```

#### **Integration with Resume Generation (API-13)**
Generate formatted resume from uploaded file:
```json
POST /resume/generate
{
  "file_id": 42,
  "template_id": 2,
  "job_description": "Senior Product Manager...",
  "optimization_level": "aggressive"
}
```

#### **Integration with Google Docs Export (API-14)**
Export uploaded file to Google Docs:
```json
POST /resume/export/gdocs
{
  "file_id": 42,
  "template_id": 2,
  "document_title": "Resume - Product Manager Position"
}
```

---

### **Password Recovery System (NEW)**

#### **Overview**
Secure email-based password recovery system that allows users to reset their passwords when forgotten, maintaining security best practices with time-limited tokens and email verification.

#### **Database Model: PasswordResetToken**
```python
class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)  # Support IPv6
    user_agent = db.Column(db.Text, nullable=True)
    user = db.relationship('User', backref='password_reset_tokens', lazy=True)
```

#### **Password Reset Request Workflow (API-03c)**
```
1. POST /api/auth/password-reset/request with email
2. Validate email format and check if user exists
3. Generate secure random token using secrets.token_urlsafe()
4. Hash token and store in database with 1-hour expiration
5. Send email with reset link containing raw token
6. Return success message (don't reveal if email exists)
```

**Request Example:**
```json
POST /api/auth/password-reset/request
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response Example (200 OK):**
```json
{
  "success": true,
  "message": "If an account with that email exists, you will receive a password reset link shortly.",
  "timestamp": "2025-11-03T10:30:00Z"
}
```

#### **Password Reset Verification Workflow (API-03d)**
```
1. POST /api/auth/password-reset/verify with token and new password
2. Hash the provided token and look up in database
3. Validate token is not expired and not already used
4. Validate new password meets security requirements
5. Hash new password using werkzeug.security
6. Update user's password and mark token as used
7. Invalidate all other reset tokens for the user
8. Return success confirmation
```

**Request Example:**
```json
POST /api/auth/password-reset/verify
Content-Type: application/json

{
  "token": "abc123def456ghi789jkl012mno345pqr678stu",
  "new_password": "NewSecurePassword123!",
  "confirm_password": "NewSecurePassword123!"
}
```

**Response Example (200 OK):**
```json
{
  "success": true,
  "message": "Password has been successfully reset. You can now log in with your new password.",
  "timestamp": "2025-11-03T10:35:00Z"
}
```

#### **Token Validation Workflow (API-03e)**
```
1. GET /api/auth/password-reset/validate?token=xyz
2. Hash the provided token and look up in database
3. Check if token exists, is not expired, and not used
4. Return validation status without consuming the token
```

**Response Example (200 OK):**
```json
{
  "valid": true,
  "expires_at": "2025-11-03T11:30:00Z",
  "time_remaining": 1785  // seconds
}
```

#### **Email Service Configuration**
```python
# Email Templates
PASSWORD_RESET_TEMPLATE = '''
Subject: Reset Your Resume Modifier Password

Hello,

You recently requested to reset your password for your Resume Modifier account. 

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour for security reasons.

If you did not request this password reset, please ignore this email.

Best regards,
Resume Modifier Team
'''

# SMTP Configuration
MAIL_SETTINGS = {
    'MAIL_SERVER': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
    'MAIL_PORT': int(os.getenv('SMTP_PORT', 587)),
    'MAIL_USE_TLS': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
    'MAIL_USERNAME': os.getenv('SMTP_USERNAME'),
    'MAIL_PASSWORD': os.getenv('SMTP_PASSWORD'),
    'MAIL_DEFAULT_SENDER': (
        os.getenv('EMAIL_FROM_NAME', 'Resume Modifier'),
        os.getenv('EMAIL_FROM_ADDRESS', 'noreply@resumemodifier.com')
    )
}
```

#### **Security Features**
1. **Token Security:**
   - Cryptographically secure random tokens (32 bytes)
   - Tokens are hashed before database storage
   - 1-hour expiration window
   - Single-use tokens (marked as used after verification)

2. **Rate Limiting:**
   - Maximum 3 reset requests per email per hour
   - IP-based rate limiting for abuse prevention

3. **Information Disclosure Prevention:**
   - Same response message regardless of email existence
   - No timing attacks through consistent response times

4. **Audit Trail:**
   - Log all password reset attempts with IP and user agent
   - Track successful resets for security monitoring

#### **Service Components**
1. **EmailService** - SMTP configuration and email sending
2. **PasswordResetService** - Token generation, validation, and management
3. **SecurityService** - Rate limiting and audit logging

#### **Error Handling**
- Invalid/expired tokens return clear error messages
- Email delivery failures are logged but don't expose errors to users
- Password validation errors include specific requirements
- Rate limit exceeded returns appropriate HTTP 429 status

#### **Integration Points**
- Integrates with existing User model and authentication system
- Uses centralized error handling from file management system
- Leverages existing JWT utilities for consistent token handling
- Compatible with existing user registration and login flows

---

### **Google Docs Resume Generation & Export**

* **Authentication Flow:**
  1. User initiates Google OAuth 2.0 flow via `/auth/google`
  2. Store access and refresh tokens securely in database
  3. Handle token refresh automatically for API calls

* **Resume Generation Workflow:**
  1. User selects template from `/templates` endpoint
  2. System combines user profile data from uploaded files with job description requirements
  3. AI service optimizes content for job matching and ATS compatibility
  4. Template engine (Jinja2) renders structured resume content

* **Google Docs Export Process:**
  1. Create new Google Doc via Google Docs API
  2. Insert formatted content using Google Docs API batch update requests
  3. Apply professional styling (fonts, spacing, headers, bullet points)
  4. Generate shareable link with appropriate permissions
  5. Export to PDF/DOCX via Google Drive API if requested

* **Template Management:**
  ```json
  {
    "template_id": 1,
    "name": "Professional Modern",
    "style": {
      "font_family": "Arial",
      "header_size": 16,
      "body_size": 11,
      "color_scheme": "blue_accent"
    },
    "sections": ["header", "summary", "experience", "education", "skills"]
  }
  ```

---

### **OAuth Persistence System for Administrator (NEW)**

#### **Overview**
Enhanced OAuth authentication system that maintains persistent Google authentication state for administrators, eliminating repeated authentication flows while providing storage monitoring capabilities to ensure optimal Google Drive usage.

#### **Enhanced Database Model: GoogleAuth (Updated)**
```python
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
    
    # OAuth Persistence Fields (NEW)
    is_persistent = db.Column(db.Boolean, default=True, nullable=False)  # Enable persistence
    auto_refresh_enabled = db.Column(db.Boolean, default=True, nullable=False)  # Auto-refresh tokens
    last_refresh_at = db.Column(db.DateTime, nullable=True)  # Last token refresh timestamp
    refresh_attempts = db.Column(db.Integer, default=0, nullable=False)  # Count of refresh attempts
    max_refresh_failures = db.Column(db.Integer, default=5, nullable=False)  # Max failures before deactivation
    
    # Storage Monitoring Fields (NEW)
    drive_quota_total = db.Column(db.BigInteger, nullable=True)  # Total Google Drive quota in bytes
    drive_quota_used = db.Column(db.BigInteger, nullable=True)  # Used Google Drive space in bytes
    last_quota_check = db.Column(db.DateTime, nullable=True)  # Last quota check timestamp
    quota_warning_level = db.Column(db.String(20), nullable=True)  # Current warning level: none, low, medium, high, critical
    quota_warnings_sent = db.Column(db.JSON, nullable=True, default=list)  # History of warnings sent
    
    # Session and Security Fields (NEW)
    persistent_session_id = db.Column(db.String(128), nullable=True, unique=True)  # Unique session identifier
    last_activity_at = db.Column(db.DateTime, nullable=True)  # Last API activity timestamp
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Active status
    deactivated_reason = db.Column(db.String(100), nullable=True)  # Reason for deactivation
    deactivated_at = db.Column(db.DateTime, nullable=True)  # Deactivation timestamp
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='google_auth', lazy=True)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('user_id', name='unique_user_google_auth'),
        db.CheckConstraint('refresh_attempts >= 0', name='check_positive_refresh_attempts'),
        db.CheckConstraint('max_refresh_failures > 0', name='check_positive_max_failures'),
        db.CheckConstraint("quota_warning_level IN ('none', 'low', 'medium', 'high', 'critical')", name='check_valid_warning_level'),
        db.Index('idx_google_auth_session', 'persistent_session_id'),
        db.Index('idx_google_auth_active', 'is_active', 'user_id'),
        db.Index('idx_google_auth_expires', 'token_expires_at'),
        db.Index('idx_google_auth_quota_check', 'last_quota_check'),
    )
```

#### **Persistent Authentication Workflow (API-12a)**

**Initial OAuth Setup:**
```
1. Administrator initiates OAuth via /auth/google?user_id={admin_user_id}
2. System validates user has admin privileges (is_admin=True)
3. Redirect to Google OAuth with required scopes:
   - https://www.googleapis.com/auth/documents
   - https://www.googleapis.com/auth/drive
   - https://www.googleapis.com/auth/drive.file
   - https://www.googleapis.com/auth/drive.metadata.readonly
4. Handle OAuth callback and exchange authorization code for tokens
5. Create GoogleAuth record with persistence enabled by default
6. Generate unique persistent_session_id for long-term authentication
7. Store tokens with auto-refresh enabled
8. Return success confirmation with session info
```

**Automatic Token Refresh System:**
```
1. Background service checks token expiration every 15 minutes
2. For tokens expiring within 5 minutes:
   a. Attempt refresh using refresh_token
   b. Update access_token and token_expires_at
   c. Increment refresh_attempts counter
   d. Record last_refresh_at timestamp
3. On successful refresh:
   a. Reset refresh_attempts counter to 0
   b. Update last_activity_at
   c. Continue normal operation
4. On refresh failure:
   a. Increment refresh_attempts
   b. If attempts < max_refresh_failures: retry with exponential backoff
   c. If attempts >= max_refresh_failures: deactivate authentication
   d. Send notification to administrator about authentication failure
```

**Session Persistence Management:**
```
1. Each API request validates persistent_session_id
2. Update last_activity_at on successful API calls
3. Maintain authentication state across application restarts
4. No re-authentication required unless:
   a. Administrator manually revokes access
   b. Token refresh fails repeatedly
   c. Google revokes application access
   d. Storage quota reaches critical levels (95%+)
```

#### **Storage Monitoring Workflow (API-12b)**

**Quota Monitoring Service:**
```
1. Scheduled task runs every 6 hours to check Google Drive quota
2. Call Google Drive API to get storage information:
   GET https://www.googleapis.com/drive/v3/about?fields=storageQuota
3. Parse response for:
   - storageQuota.limit (total available space)
   - storageQuota.usage (total used space)
   - storageQuota.usageInDrive (space used by Drive files)
4. Calculate usage percentage: (used / total) * 100
5. Update GoogleAuth record with current quota information
6. Determine warning level based on usage percentage
7. Send notifications if warning thresholds crossed
```

**Warning Level Definitions:**
- **None (0-79%)**: Normal usage, no warnings
- **Low (80-84%)**: First warning, suggest cleanup
- **Medium (85-89%)**: Second warning, recommend action
- **High (90-94%)**: Urgent warning, immediate attention needed
- **Critical (95-100%)**: Emergency level, may disable new uploads

**Storage Warning System:**
```python
STORAGE_WARNING_THRESHOLDS = {
    'low': 80,      # 80% - First warning
    'medium': 85,   # 85% - Second warning  
    'high': 90,     # 90% - Urgent warning
    'critical': 95  # 95% - Critical warning
}

WARNING_ACTIONS = {
    'low': {
        'message': 'Google Drive storage is 80% full. Consider archiving old files.',
        'action': 'log_warning'
    },
    'medium': {
        'message': 'Google Drive storage is 85% full. Please review and delete unnecessary files.',
        'action': 'email_admin'
    },
    'high': {
        'message': 'Google Drive storage is 90% full. Immediate cleanup required to prevent service interruption.',
        'action': ['email_admin', 'dashboard_alert']
    },
    'critical': {
        'message': 'Google Drive storage is 95% full. New file uploads may be disabled.',
        'action': ['email_admin', 'dashboard_alert', 'disable_uploads']
    }
}
```

#### **Enhanced API Endpoints**

**OAuth Status Check (NEW):**
```
GET /api/auth/google/status
- Returns current OAuth authentication status for admin users
- Includes token validity, storage quota, and warning levels
- Requires admin authentication
```

**Response Example:**
```json
{
  "success": true,
  "oauth_status": {
    "is_authenticated": true,
    "is_persistent": true,
    "session_id": "abc123def456ghi789",
    "token_expires_at": "2025-12-22T10:30:00Z",
    "last_refresh_at": "2025-11-22T08:15:00Z",
    "auto_refresh_enabled": true,
    "is_active": true
  },
  "storage_status": {
    "quota_total": 17179869184,  // 16 GB
    "quota_used": 13743895347,   // 12.8 GB  
    "usage_percentage": 80.0,
    "warning_level": "low",
    "last_check": "2025-11-22T12:00:00Z",
    "formatted_quota": {
      "total": "16.0 GB",
      "used": "12.8 GB", 
      "available": "3.2 GB"
    }
  }
}
```

**OAuth Revocation (NEW):**
```
POST /api/auth/google/revoke
- Manually revoke OAuth authentication
- Deactivates persistent session
- Requires admin authentication and confirmation
```

**Request Example:**
```json
{
  "confirm_revocation": true,
  "reason": "Manual admin revocation"
}
```

**Storage Analytics (NEW):**
```
GET /api/auth/google/storage/analytics
- Detailed storage usage analytics
- File type breakdown, large file identification
- Storage trends and cleanup recommendations
```

**Response Example:**
```json
{
  "success": true,
  "analytics": {
    "usage_by_type": {
      "documents": {"count": 150, "size": 8589934592, "percentage": 50.0},
      "pdfs": {"count": 300, "size": 6442450944, "percentage": 37.5},
      "images": {"count": 75, "size": 2147483648, "percentage": 12.5}
    },
    "large_files": [
      {
        "name": "Large_Portfolio.pdf", 
        "size": 52428800,
        "formatted_size": "50 MB",
        "created": "2025-01-15T10:30:00Z"
      }
    ],
    "recommendations": [
      "Consider archiving files older than 1 year",
      "Compress large PDF files to reduce storage usage",
      "Delete duplicate files found in analysis"
    ],
    "projected_full_date": "2025-12-15T00:00:00Z"
  }
}
```

#### **Background Services**

**Token Refresh Service:**
```python
class OAuthTokenRefreshService:
    def __init__(self):
        self.refresh_interval = 900  # 15 minutes
        self.expiry_threshold = 300   # 5 minutes
        
    def run_refresh_check(self):
        """Check and refresh expiring tokens"""
        expiring_soon = datetime.utcnow() + timedelta(seconds=self.expiry_threshold)
        
        auth_records = GoogleAuth.query.filter(
            GoogleAuth.is_active == True,
            GoogleAuth.auto_refresh_enabled == True,
            GoogleAuth.token_expires_at <= expiring_soon
        ).all()
        
        for auth in auth_records:
            self.refresh_token_if_needed(auth)
    
    def refresh_token_if_needed(self, auth: GoogleAuth):
        """Refresh individual auth token"""
        try:
            # Use Google OAuth2 library to refresh
            credentials = google.oauth2.credentials.Credentials(
                token=auth.access_token,
                refresh_token=auth.refresh_token,
                # ... other credential fields
            )
            
            request = google.auth.transport.requests.Request()
            credentials.refresh(request)
            
            # Update database record
            auth.access_token = credentials.token
            auth.token_expires_at = credentials.expiry
            auth.last_refresh_at = datetime.utcnow()
            auth.refresh_attempts = 0  # Reset on success
            
            db.session.commit()
            
        except Exception as e:
            self.handle_refresh_failure(auth, str(e))
```

**Storage Monitoring Service:**
```python
class GoogleDriveStorageMonitor:
    def __init__(self):
        self.check_interval = 21600  # 6 hours
        self.warning_thresholds = {
            'low': 80, 'medium': 85, 'high': 90, 'critical': 95
        }
    
    def check_storage_usage(self):
        """Check storage for all active admin authentications"""
        active_auths = GoogleAuth.query.filter(
            GoogleAuth.is_active == True,
            GoogleAuth.is_persistent == True
        ).all()
        
        for auth in active_auths:
            self.update_storage_info(auth)
    
    def update_storage_info(self, auth: GoogleAuth):
        """Update storage information for specific auth"""
        try:
            # Build Google Drive service
            service = build('drive', 'v3', credentials=self.get_credentials(auth))
            
            # Get storage quota information
            about = service.about().get(fields='storageQuota').execute()
            quota = about.get('storageQuota', {})
            
            # Update database
            auth.drive_quota_total = int(quota.get('limit', 0))
            auth.drive_quota_used = int(quota.get('usage', 0))
            auth.last_quota_check = datetime.utcnow()
            
            # Calculate and update warning level
            usage_percentage = self.calculate_usage_percentage(auth)
            new_warning_level = self.determine_warning_level(usage_percentage)
            
            if new_warning_level != auth.quota_warning_level:
                self.handle_warning_level_change(auth, new_warning_level)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to check storage for auth {auth.id}: {e}")
```

#### **Integration with Existing Systems**

**File Upload Integration:**
```python
# Enhanced file upload service
class FileUploadService:
    def upload_file(self, file_data, user_id, google_drive_enabled=True):
        # ... existing upload logic ...
        
        if google_drive_enabled:
            # Check storage before upload
            storage_status = self.check_storage_availability()
            if storage_status['warning_level'] == 'critical':
                return {
                    'success': False,
                    'error': 'Upload disabled due to low storage space',
                    'storage_warning': storage_status
                }
            
            # Proceed with Google Drive upload
            google_result = self.upload_to_google_drive(file_data)
            
            # Update storage usage after upload
            self.update_storage_usage_post_upload()
```

**Authentication Middleware Enhancement:**
```python
def require_persistent_google_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user has valid persistent OAuth
        auth = GoogleAuth.query.filter_by(
            user_id=get_current_user_id(),
            is_active=True,
            is_persistent=True
        ).first()
        
        if not auth:
            return jsonify({
                'error': 'Google authentication required',
                'redirect_url': '/auth/google'
            }), 401
        
        # Check if token is still valid
        if auth.token_expires_at <= datetime.utcnow():
            # Attempt refresh
            if not refresh_token_synchronously(auth):
                return jsonify({
                    'error': 'Authentication expired',
                    'redirect_url': '/auth/google'
                }), 401
        
        # Update activity timestamp
        auth.last_activity_at = datetime.utcnow()
        db.session.commit()
        
        return f(*args, **kwargs)
    return decorated_function
```

#### **Security and Error Handling**

**Security Measures:**
1. **Session Security**: Unique persistent_session_id prevents session hijacking
2. **Token Encryption**: Store refresh tokens encrypted at rest
3. **Activity Monitoring**: Track last_activity_at for security audits
4. **Automatic Deactivation**: Deactivate after repeated refresh failures
5. **Admin-Only Access**: Verify is_admin=True for all OAuth operations

**Error Scenarios and Handling:**
1. **Token Refresh Failure**: Exponential backoff, notification, eventual deactivation
2. **Google API Errors**: Graceful degradation, local storage fallback
3. **Storage Full**: Disable uploads, emergency cleanup recommendations
4. **Network Issues**: Queue operations, retry with timeout
5. **User Revocation**: Clean session termination, audit logging

#### **Configuration Variables**
```env
# OAuth Persistence Configuration
OAUTH_TOKEN_REFRESH_INTERVAL=900  # 15 minutes
OAUTH_TOKEN_EXPIRY_THRESHOLD=300  # 5 minutes  
OAUTH_MAX_REFRESH_FAILURES=5
OAUTH_REFRESH_RETRY_BACKOFF=60    # 1 minute

# Storage Monitoring Configuration
STORAGE_CHECK_INTERVAL=21600      # 6 hours
STORAGE_WARNING_LOW=80            # 80% threshold
STORAGE_WARNING_MEDIUM=85         # 85% threshold  
STORAGE_WARNING_HIGH=90           # 90% threshold
STORAGE_WARNING_CRITICAL=95       # 95% threshold

# Email Notifications
STORAGE_WARNING_EMAIL_ENABLED=true
STORAGE_WARNING_EMAIL_FROM=admin@resumemodifier.com
STORAGE_WARNING_EMAIL_TO=admin@resumemodifier.com

# Session Management
PERSISTENT_SESSION_ENABLED=true
SESSION_ACTIVITY_TIMEOUT=2592000  # 30 days
SESSION_CLEANUP_INTERVAL=86400    # 24 hours
```

#### **Database Migration Requirements**
```sql
-- Add OAuth persistence fields to google_auth_tokens table
ALTER TABLE google_auth_tokens
ADD COLUMN is_persistent BOOLEAN DEFAULT TRUE NOT NULL,
ADD COLUMN auto_refresh_enabled BOOLEAN DEFAULT TRUE NOT NULL,
ADD COLUMN last_refresh_at DATETIME NULL,
ADD COLUMN refresh_attempts INT DEFAULT 0 NOT NULL,
ADD COLUMN max_refresh_failures INT DEFAULT 5 NOT NULL,

-- Add storage monitoring fields
ADD COLUMN drive_quota_total BIGINT NULL,
ADD COLUMN drive_quota_used BIGINT NULL,
ADD COLUMN last_quota_check DATETIME NULL,
ADD COLUMN quota_warning_level VARCHAR(20) NULL,
ADD COLUMN quota_warnings_sent JSON NULL,

-- Add session management fields
ADD COLUMN persistent_session_id VARCHAR(128) NULL UNIQUE,
ADD COLUMN last_activity_at DATETIME NULL,
ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL,
ADD COLUMN deactivated_reason VARCHAR(100) NULL,
ADD COLUMN deactivated_at DATETIME NULL;

-- Add constraints and indexes
ALTER TABLE google_auth_tokens
ADD CONSTRAINT check_positive_refresh_attempts CHECK (refresh_attempts >= 0),
ADD CONSTRAINT check_positive_max_failures CHECK (max_refresh_failures > 0),
ADD CONSTRAINT check_valid_warning_level CHECK (quota_warning_level IN ('none', 'low', 'medium', 'high', 'critical'));

CREATE INDEX idx_google_auth_session ON google_auth_tokens(persistent_session_id);
CREATE INDEX idx_google_auth_active ON google_auth_tokens(is_active, user_id);
CREATE INDEX idx_google_auth_expires ON google_auth_tokens(token_expires_at);
CREATE INDEX idx_google_auth_quota_check ON google_auth_tokens(last_quota_check);
```

#### **Service Components**
1. **OAuthPersistenceService** - Manage persistent authentication sessions
2. **TokenRefreshService** - Background token refresh automation  
3. **StorageMonitoringService** - Google Drive quota monitoring and warnings
4. **SessionManagementService** - Persistent session lifecycle management
5. **NotificationService** - Storage warning notifications and alerts

#### **Testing Strategy**
1. **Unit Tests**: Token refresh logic, storage calculation, warning thresholds
2. **Integration Tests**: End-to-end OAuth flow with persistence
3. **Load Tests**: Multiple concurrent token refreshes
4. **Storage Tests**: Various quota scenarios and warning triggers
5. **Security Tests**: Session hijacking prevention, token encryption

---

## 4. Non-Functional Requirements

| Category          | Requirement                                                |
| ----------------- | ---------------------------------------------------------- |
| **Performance**   | API response time < 1.5s for standard requests             |
| **Scalability**   | Dockerized backend, supports multiple API instances        |
| **Reliability**   | Health check monitored via Railway uptime                  |
| **Security**      | Input validation, API key authentication, HTTPS enforced   |
| **Documentation** | Swagger auto-generated; versioned API changelog maintained |

---

## 5. Milestone Checklist

| Milestone                      | Description                                  | Responsible | Status  |
| ------------------------------ | -------------------------------------------- | ----------- | ------- |
| ✅ Setup Backend Environment    | Railway backend created and running          | RZ          | Pending |
| ✅ Health Endpoint Working      | `/health` route verified                     | RZ          | Pending |
| ✅ Database Connection Live     | PostgreSQL or MongoDB connection established | RZ          | Pending |
| ✅ Auto API Docs Active         | Swagger UI accessible                        | RZ          | Pending |
| ✅ User Registration API        | `/api/register` endpoint with validation     | RZ          | Pending |
| ✅ User Login API               | `/api/login` endpoint with JWT tokens        | RZ          | Pending |
| ✅ Password Reset Request API   | `/api/auth/password-reset/request` endpoint  | RZ          | Pending |
| ✅ Password Reset Verify API    | `/api/auth/password-reset/verify` endpoint   | RZ          | Pending |
| ✅ Password Reset Validate API  | `/api/auth/password-reset/validate` endpoint | RZ          | Pending |
| ✅ Email Service Integration    | SMTP configuration and email sending        | RZ          | Pending |
| ✅ File Upload API              | `/files/upload` functional with validation   | RZ          | Pending |
| ✅ File Download API            | `/files/{id}` download with format support   | RZ          | Pending |
| ✅ File Listing API             | `/files` listing with pagination & filtering | RZ          | Pending |
| ✅ File Metadata API            | `/files/{id}/info` with text extraction      | RZ          | Pending |
| ✅ File Deletion API            | `/files/{id}` and bulk delete support        | RZ          | Pending |
| ✅ File Storage Integration     | S3/local storage configured and working      | RZ          | Pending |
| ✅ Resume Upload API            | `/resume/upload` functional                  | RZ          | Pending |
| ✅ Resume Scoring API           | `/resume/score` with file_id support         | RZ          | Pending |
| ✅ Google OAuth Integration     | Google Docs API authentication working       | RZ          | Pending |
| ✅ OAuth Persistence System     | Persistent authentication with auto-refresh  | RZ          | Pending |
| ✅ Storage Monitoring Service   | Google Drive quota monitoring and warnings   | RZ          | Pending |
| ✅ Background Token Refresh     | Automatic OAuth token refresh service        | RZ          | Pending |
| ✅ Storage Analytics API        | Storage usage analytics and recommendations  | RZ          | Pending |
| ✅ Resume Template System       | Template management and selection API        | RZ          | Pending |
| ✅ Resume Generation Engine     | Content generation with job matching AI      | RZ          | Pending |
| ✅ Google Docs Export API       | Document creation from file_id or text       | RZ          | Pending |
| ✅ Multi-format Export          | PDF/DOCX export from Google Docs             | RZ          | Pending |
| ✅ Frontend-Backend Integration | End-to-end file upload and processing        | Jing        | Pending |

---

## 6. Next Steps

1. **Confirm backend framework (Flask as currently implemented).**
2. **Set up Railway deployment** with environment variables including Google API credentials and SMTP configuration.
3. **Implement `/health` and `/docs` endpoints.**
4. **Establish database schema (users, resumes, resume_files, jobs, templates, password_reset_tokens tables).**
5. **Implement user authentication system:**
   - Create `User` model with email/password fields
   - Implement `/api/register` endpoint with password hashing
   - Implement `/api/login` endpoint with JWT token generation
   - Set up JWT middleware for protected routes
6. **Implement password recovery system:**
   - Create `PasswordResetToken` model with security fields
   - Set up email service with SMTP configuration
   - Implement `PasswordResetService` for token management
   - Create `/api/auth/password-reset/request` endpoint
   - Create `/api/auth/password-reset/verify` endpoint  
   - Create `/api/auth/password-reset/validate` endpoint
   - Implement email templates and delivery system
   - Add rate limiting and security measures
7. **Implement file management system:**
   - Create `ResumeFile` model with metadata fields
   - Set up local or S3 file storage provider
   - Implement `FileStorageService` for save/retrieve/delete operations
   - Implement `FileProcessingService` for text extraction from PDF/DOCX
   - Implement `FileMetadataService` for database operations
   - Implement `FileValidator` for file validation
   - Create `/files` endpoints (upload, download, list, delete, info)
8. **Integrate file management with resume operations:**
   - Update `/resume/score` to accept file_id parameter
   - Update `/resume/generate` to use file_id for source data
   - Update `/resume/export/gdocs` to support file_id parameter
9. **Set up Google Cloud project and enable Google Docs/Drive APIs.**
10. **Implement OAuth 2.0 authentication flow for Google services.**
11. **Implement OAuth persistence system:**
    - Enhance `GoogleAuth` model with persistence and monitoring fields
    - Create `OAuthPersistenceService` for session management
    - Implement `TokenRefreshService` for automatic token refresh
    - Create `StorageMonitoringService` for Google Drive quota monitoring
    - Implement background services for automated token refresh and storage checks
    - Create admin endpoints for OAuth status, revocation, and storage analytics
    - Add storage warning notification system with email alerts
12. **Create resume template management system.**
13. **Integrate AI model for resume scoring and content optimization.**
13. **Develop Google Docs export functionality with professional formatting.**
14. **Create comprehensive test suite for all authentication flows (registration, login, password recovery).**
15. **Create comprehensive test suite for file management (upload, download, delete flows).**
16. **Deploy to staging and verify end-to-end authentication → file upload → processing → export workflow.**

---

## 7. Implementation Reference

**For detailed implementation guidance, see:** [`FILE_MANAGEMENT_DESIGN.md`](./FILE_MANAGEMENT_DESIGN.md)

This document includes:
- Complete architecture diagrams
- Service component interfaces
- Database migration scripts
- Environment configuration examples
- Security considerations
- Performance optimization strategies
- Testing strategy and test file structure
- Deployment checklist
