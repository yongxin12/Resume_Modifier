# Enhanced File Management API Documentation

## Enhanced File Management Endpoints

### File Upload with Advanced Features

#### Enhanced File Upload
```http
POST /api/files/upload
```

**Description:** Upload a file with duplicate detection, Google Drive integration, and comprehensive error handling.

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data
```

**Request Body (form-data):**
- `file` (required): The file to upload (PDF, DOCX)
- `process` (optional): Whether to process the file immediately ('true'/'false', default: 'false')

**Query Parameters:**
- `google_drive` (optional): Enable Google Drive upload ('true'/'false', default: based on config)
- `convert_to_doc` (optional): Convert to Google Docs format ('true'/'false', default: based on config)
- `share_with_user` (optional): Share Google Drive file with user ('true'/'false', default: based on config)

**Success Response (201):**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file": {
    "id": 123,
    "original_filename": "resume.pdf",
    "display_filename": "resume.pdf",
    "stored_filename": "stored_resume_20241114.pdf",
    "file_size": 1024,
    "mime_type": "application/pdf",
    "file_hash": "sha256_hash_here",
    "uploaded_at": "2024-11-14T10:00:00.000Z",
    "url": "http://localhost:5001/api/files/123",
    "duplicate_info": {
      "is_duplicate": false,
      "duplicate_sequence": null,
      "original_file_id": null
    },
    "google_drive": {
      "file_id": "1ABC123xyz",
      "doc_id": "1DEF456abc",
      "is_shared": true,
      "drive_link": "https://drive.google.com/file/d/1ABC123xyz/view",
      "doc_link": "https://docs.google.com/document/d/1DEF456abc/edit"
    }
  },
  "duplicate_notification": null,
  "warnings": []
}
```

**Duplicate File Response (201):**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file": {
    "id": 124,
    "original_filename": "resume.pdf",
    "display_filename": "resume (1).pdf",
    "duplicate_info": {
      "is_duplicate": true,
      "duplicate_sequence": 1,
      "original_file_id": 123
    }
  },
  "duplicate_notification": "Duplicate file detected. Saved as 'resume (1).pdf' to avoid conflicts.",
  "warnings": []
}
```

**Error Response (400-500):**
```json
{
  "success": false,
  "error_code": "FILE_SIZE_EXCEEDED",
  "message": "File is too large. Please upload a file smaller than 10MB",
  "timestamp": "2024-11-14T10:00:00.000Z"
}
```

**Error Codes:**
- `FILE_NOT_PROVIDED`: No file provided in request
- `FILE_SIZE_EXCEEDED`: File size exceeds maximum allowed size
- `FILE_TYPE_INVALID`: File type not supported
- `GOOGLE_DRIVE_UPLOAD_FAILED`: Google Drive upload failed (with warning)
- `DUPLICATE_DETECTION_FAILED`: Duplicate detection failed (with warning)

---

### Google Drive Integration

#### Access Google Doc Version
```http
GET /api/files/{file_id}/google-doc
```

**Description:** Get Google Drive and Google Docs links for a file.

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Query Parameters:**
- `ensure_sharing` (optional): Ensure file is shared with user ('true'/'false', default: 'false')

**Success Response (200):**
```json
{
  "success": true,
  "google_doc": {
    "file_id": "1ABC123xyz",
    "doc_id": "1DEF456abc",
    "has_doc_version": true,
    "is_shared": true,
    "drive_link": "https://drive.google.com/file/d/1ABC123xyz/view",
    "doc_link": "https://docs.google.com/document/d/1DEF456abc/edit",
    "sharing_info": {
      "access_level": "writer",
      "shared_at": "2024-11-14T10:00:00.000Z"
    }
  }
}
```

**Error Response (404):**
```json
{
  "success": false,
  "error_code": "RECORD_NOT_FOUND",
  "message": "No Google Drive version available for this file",
  "timestamp": "2024-11-14T10:00:00.000Z"
}
```

---

### File Restoration

#### Restore Deleted File
```http
POST /api/files/{file_id}/restore
```

**Description:** Restore a soft-deleted file.

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "File restored successfully",
  "file": {
    "id": 123,
    "original_filename": "resume.pdf",
    "display_filename": "resume.pdf",
    "deleted_at": null,
    "deleted_by": null,
    "restored_at": "2024-11-14T10:30:00.000Z",
    "restored_by": 1
  }
}
```

**Error Response (404):**
```json
{
  "success": false,
  "error_code": "RECORD_NOT_FOUND",
  "message": "File not found or not deleted",
  "timestamp": "2024-11-14T10:00:00.000Z"
}
```

---

### Enhanced File Listing

#### List Files with Soft Deletion Support
```http
GET /api/files
```

**Description:** List user's files with support for including/excluding deleted files.

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Query Parameters:**
- `include_deleted` (optional): Include soft-deleted files ('true'/'false', default: 'false')
- `page` (optional): Page number for pagination (default: 1)
- `per_page` (optional): Items per page (default: 10, max: 100)
- `sort` (optional): Sort field ('name', 'date', 'size', default: 'date')
- `order` (optional): Sort order ('asc', 'desc', default: 'desc')

**Success Response (200):**
```json
{
  "success": true,
  "files": [
    {
      "id": 123,
      "original_filename": "resume.pdf",
      "display_filename": "resume.pdf",
      "file_size": 1024,
      "mime_type": "application/pdf",
      "uploaded_at": "2024-11-14T10:00:00.000Z",
      "is_deleted": false,
      "duplicate_info": {
        "is_duplicate": false,
        "duplicate_sequence": null
      },
      "google_drive": {
        "has_drive_version": true,
        "has_doc_version": true,
        "is_shared": true
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 25,
    "pages": 3
  },
  "total": 25
}
```

---

### Administrative Endpoints

#### List Deleted Files (Admin)
```http
GET /api/admin/files/deleted
```

**Description:** List all soft-deleted files across all users (admin only).

**Headers:**
```
Authorization: Bearer <ADMIN_JWT_TOKEN>
```

**Query Parameters:**
- `page` (optional): Page number for pagination (default: 1)
- `per_page` (optional): Items per page (default: 10, max: 100)
- `user_id` (optional): Filter by specific user ID

**Success Response (200):**
```json
{
  "success": true,
  "files": [
    {
      "id": 124,
      "user_id": 5,
      "user_email": "user@example.com",
      "original_filename": "old_resume.pdf",
      "display_filename": "old_resume.pdf",
      "file_size": 2048,
      "deleted_at": "2024-11-13T15:30:00.000Z",
      "deleted_by": 5,
      "days_deleted": 1
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 5,
    "pages": 1
  },
  "total": 5
}
```

#### Restore File (Admin)
```http
POST /api/admin/files/{file_id}/restore
```

**Description:** Restore any deleted file (admin only).

**Headers:**
```
Authorization: Bearer <ADMIN_JWT_TOKEN>
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "File restored successfully by admin",
  "file": {
    "id": 124,
    "user_id": 5,
    "original_filename": "old_resume.pdf",
    "restored_at": "2024-11-14T10:30:00.000Z",
    "restored_by": 1,
    "restored_by_admin": true
  }
}
```

#### Permanent Delete (Admin)
```http
DELETE /api/admin/files/{file_id}/permanent-delete
```

**Description:** Permanently delete a file from database and storage (admin only).

**Headers:**
```
Authorization: Bearer <ADMIN_JWT_TOKEN>
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "File permanently deleted",
  "file_id": 124,
  "deleted_at": "2024-11-14T10:30:00.000Z",
  "deleted_by_admin": 1
}
```

**Warning:** This action is irreversible and removes the file from both database and storage.

---

## Enhanced Error Codes

### Google Drive Integration Errors
- `GOOGLE_DRIVE_CONFIG_ERROR`: Google Drive integration not properly configured
- `GOOGLE_DRIVE_AUTH_FAILED`: Unable to connect to Google Drive
- `GOOGLE_DRIVE_QUOTA_EXCEEDED`: Google Drive API quota exceeded
- `GOOGLE_DRIVE_UPLOAD_FAILED`: Failed to upload file to Google Drive
- `GOOGLE_DRIVE_SHARING_FAILED`: Failed to share Google Drive file with user
- `GOOGLE_DRIVE_CONVERSION_FAILED`: Failed to convert file to Google Docs format
- `GOOGLE_DRIVE_SERVICE_UNAVAILABLE`: Google Drive service temporarily unavailable

### Duplicate Detection Errors
- `DUPLICATE_DETECTION_FAILED`: Duplicate detection service failed
- `DUPLICATE_HASH_COLLISION`: Hash collision detected during duplicate processing

### Soft Deletion Errors
- `FILE_ALREADY_DELETED`: File is already deleted
- `FILE_NOT_DELETED`: File is not in deleted state
- `RESTORE_FAILED`: Failed to restore deleted file

---

## Configuration

### Environment Variables

#### Google Drive Integration
```bash
# Google Drive Configuration
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_CREDENTIALS_JSON={"type": "service_account", ...}
GOOGLE_DRIVE_CREDENTIALS_FILE=/path/to/credentials.json
GOOGLE_DRIVE_DEFAULT_ACCESS_LEVEL=writer
GOOGLE_DRIVE_SHARE_WITH_USER=true
GOOGLE_DRIVE_CONVERT_TO_DOC=true
```

#### File Management
```bash
# File Upload Configuration
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf,docx
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=/app/uploads

# Duplicate Detection
DUPLICATE_DETECTION_ENABLED=true
HASH_ALGORITHM=sha256
```

#### Soft Deletion
```bash
# Soft Deletion Configuration  
SOFT_DELETE_ENABLED=true
PERMANENT_DELETE_AFTER_DAYS=30
```

---

## Rate Limiting

### Google Drive API
- Upload operations: 1000 requests per 100 seconds per user
- Sharing operations: 100 requests per 100 seconds per user
- Conversion operations: 100 requests per 100 seconds per user

### File Operations
- Upload: 10 files per minute per user
- Restoration: 20 operations per minute per user
- Admin operations: 100 operations per minute per admin

---

## Testing

### Configuration Validation
Use the included validation script to verify Google Drive setup:

```bash
python validate_google_drive.py
```

### Test Endpoints
All endpoints can be tested using the comprehensive test suite:

```bash
python -m pytest app/tests/ -v
```

---

## Security Considerations

### File Access
- Users can only access their own files
- Admin users can access all files for management
- Soft-deleted files are excluded from normal operations

### Google Drive Integration
- Service account authentication provides secure API access
- File sharing permissions are configurable per user
- Files are automatically shared with the uploading user

### Data Protection
- File hashes enable duplicate detection without exposing content
- Soft deletion provides data recovery capabilities
- Audit logging tracks all file operations

---

For more detailed examples and interactive testing, visit the Swagger documentation at `/apidocs` when the server is running.