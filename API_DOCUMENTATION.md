# Resume Editor API Documentation

## Overview
The Resume Editor API provides AI-powered resume parsing, analysis, and scoring functionality. Built with Flask and OpenAI, it helps users optimize their resumes for job applications.

## Base URL
```
http://localhost:5001
```

## Swagger/OpenAPI Documentation
Interactive API documentation is available at:
```
http://localhost:5001/apidocs
```

---

## Endpoints

### System Endpoints

#### Health Check
```http
GET /health
```

**Description:** Check system health and component status

**Response:**
```json
{
  "status": "healthy",
  "service": "Resume Editor API",
  "timestamp": "2025-10-11T10:30:00.000Z",
  "components": {
    "database": "connected",
    "openai": "configured"
  }
}
```

**Status Codes:**
- `200`: Service healthy
- `503`: Service unhealthy

---

### Authentication Endpoints

#### Register User
```http
POST /api/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "status": 201,
  "user": {
    "email": "user@example.com"
  }
}
```

**Status Codes:**
- `201`: User created successfully
- `400`: Invalid input or email already registered
- `500`: Registration failed

---

#### Login
```http
POST /api/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "status": "success",
  "user": {
    "email": "user@example.com"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Status Codes:**
- `200`: Login successful
- `400`: Missing credentials
- `401`: Invalid credentials

---

### Resume Processing Endpoints

#### Upload PDF Resume
```http
POST /api/pdfupload
```

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (required): PDF file containing the resume

**Response:**
```json
{
  "status": 200,
  "data": {
    "personalInfo": {
      "firstName": "John",
      "lastName": "Doe",
      "email": "john.doe@example.com",
      "phone": "+1-555-0123",
      "location": "San Francisco, CA"
    },
    "workExperience": [...],
    "education": [...],
    "skills": [...]
  }
}
```

**Status Codes:**
- `200`: Resume parsed successfully
- `400`: Invalid file format
- `500`: Processing failed

---

#### Analyze Resume with Job Description
```http
POST /api/job_description_upload
```

**Request Body:**
```json
{
  "updated_resume": {
    "personalInfo": {...},
    "workExperience": [...],
    "education": [...],
    "skills": [...]
  },
  "job_description": "Job description text here..."
}
```

**Response:**
```json
{
  "status": 200,
  "data": {
    "overallAnalysis": {
      "comment": "Overall assessment...",
      "score": 85
    },
    "workExperience": [...],
    "education": [...],
    "achievements": {...},
    "project": [...]
  }
}
```

**Status Codes:**
- `200`: Analysis completed
- `400`: Invalid request data
- `500`: Analysis failed

---

#### Score Resume
```http
POST /api/resume/score
```

**Description:** Get detailed AI-powered scoring with sub-scores for keyword matching, language expression, and ATS readability. This endpoint provides comprehensive resume analysis with weighted scoring across multiple dimensions.

**Request Body:**
```json
{
  "resume": {
    "personalInfo": {...},
    "workExperience": [...],
    "education": [...],
    "skills": [...]
  },
  "job_description": "Optional job description to score against"
}
```

**Response:**
```json
{
  "status": 200,
  "data": {
    "overall_score": 85.5,
    "scores": {
      "keyword_matching": {
        "score": 88,
        "weight": 0.35,
        "details": {
          "matched_keywords": ["Python", "React", "Flask"],
          "missing_keywords": ["Docker", "Kubernetes"],
          "keyword_density": 0.75,
          "comment": "Strong keyword alignment with 75% coverage..."
        }
      },
      "language_expression": {
        "score": 85,
        "weight": 0.35,
        "details": {
          "grammar_quality": 90,
          "professional_tone": 88,
          "clarity": 82,
          "action_verbs_usage": 80,
          "comment": "Excellent grammar and professional tone..."
        }
      },
      "ats_readability": {
        "score": 83,
        "weight": 0.30,
        "details": {
          "format_compatibility": 95,
          "structure_clarity": 85,
          "parsing_friendliness": 80,
          "section_organization": 72,
          "comment": "Good ATS compatibility with clear structure..."
        }
      }
    },
    "recommendations": [
      "Add more quantifiable achievements",
      "Include missing keywords: Docker, Kubernetes",
      "Improve project section organization"
    ],
    "strengths": [
      "Strong technical skills alignment",
      "Clear work experience descriptions",
      "Professional formatting"
    ],
    "weaknesses": [
      "Missing some key technologies",
      "Could use more action verbs",
      "Project section needs better structure"
    ]
  }
}
```

**Scoring Breakdown:**
- **Keyword Matching (35% weight):** Evaluates keyword relevance and coverage
- **Language Expression (35% weight):** Assesses grammar, tone, clarity, and action verb usage
- **ATS Readability (30% weight):** Measures format compatibility and parsing friendliness
- **Overall Score:** Weighted average of the three sub-scores

**Status Codes:**
- `200`: Scoring completed successfully
- `400`: Invalid request data
- `500`: Scoring failed

---

### Google Integration Endpoints

#### Google OAuth Authentication
```http
GET /api/auth/google
```

**Description:** Initiate Google OAuth flow for Google Docs and Drive integration

**Response:** Redirects to Google OAuth consent screen

---

#### Google OAuth Callback
```http
GET /api/auth/google/callback
```

**Description:** Handle Google OAuth callback and store credentials

**Parameters:**
- `code` (query): Authorization code from Google
- `state` (query): State parameter for security

---

### Export Endpoints (Authenticated)

#### Export to Google Docs
```http
POST /api/export/google-docs
```

**Request Body:**
```json
{
  "resume_id": 123,
  "template_id": 1,
  "title": "John Doe - Software Engineer Resume"
}
```

**Response:**
```json
{
  "status": 200,
  "data": {
    "document_id": "1abc123...",
    "document_url": "https://docs.google.com/document/d/1abc123.../edit",
    "shareable_link": "https://docs.google.com/document/d/1abc123.../edit?usp=sharing"
  }
}
```

---

#### Export to PDF
```http
POST /api/export/pdf
```

**Request Body:**
```json
{
  "resume_id": 123,
  "template": "professional"
}
```

**Response:** PDF file download

---

#### Export to DOCX
```http
POST /api/export/docx
```

**Request Body:**
```json
{
  "resume_id": 123,  
  "template": "modern"
}
```

**Response:** DOCX file download

---

### Resume Management Endpoints (Authenticated)

All endpoints below require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <token>
```

#### Save Resume
```http
PUT /api/save_resume
```

**Request Body:**
```json
{
  "resume_title": "My Software Engineer Resume",
  "updated_resume": {
    "personalInfo": {...},
    "workExperience": [...],
    "education": [...],
    "skills": [...]
  }
}
```

**Response:**
```json
{
  "status": 200
}
```

---

#### Get Resume List
```http
GET /api/get_resume_list
```

**Response:**
```json
{
  "status": 200,
  "data": [
    {
      "resume_id": 1,
      "resume_title": "Software Engineer Resume",
      "created_at": "2025-10-10T10:00:00"
    },
    {
      "resume_id": 2,
      "resume_title": "Data Scientist Resume",
      "created_at": "2025-10-11T15:30:00"
    }
  ]
}
```

---

#### Get Specific Resume
```http
GET /api/get_resume/<resume_id>
```

**Response:**
```json
{
  "status": 200,
  "data": {
    "resume_title": "Software Engineer Resume",
    "resume": {
      "personalInfo": {...},
      "workExperience": [...],
      "education": [...],
      "skills": [...]
    }
  }
}
```

---

#### Update Profile
```http
PUT /api/put_profile
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "city": "San Francisco",
  "country": "USA",
  "bio": "Experienced software engineer..."
}
```

---

#### Get Profile
```http
GET /api/get_profile
```

**Response:**
```json
{
  "status": 200,
  "data": {
    "profile": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "city": "San Francisco",
      "country": "USA",
      "bio": "Experienced software engineer..."
    }
  }
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message",
  "details": "Detailed error information (when available)"
}
```

Common error status codes:
- `400`: Bad Request - Invalid input data
- `401`: Unauthorized - Authentication required or failed
- `404`: Not Found - Resource not found
- `500`: Internal Server Error - Server-side error
- `503`: Service Unavailable - Service is down or unhealthy

---

## Database Configuration

The application uses PostgreSQL for data persistence:

```yaml
Database: resume_app
Host: localhost (or db in Docker)
Port: 5432
User: postgres
```

Connection string format:
```
postgresql://postgres:postgres@db:5432/resume_app
```

---

## Environment Variables

Required environment variables:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/resume_app

# JWT Configuration
JWT_SECRET=your-jwt-secret-key

# Flask Configuration
FLASK_APP=app.server
FLASK_ENV=development
FLASK_DEBUG=1
```

---

## Running the Application

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Access Points

- **API Base URL:** http://localhost:5001
- **Swagger UI:** http://localhost:5001/apidocs
- **Database:** localhost:5432

---

## Testing

A test script is provided at `test_api.py`:

```bash
python test_api.py
```

This will test:
- Health check endpoint
- Resume scoring functionality
- Authentication (register/login)

---

## AI Models

The application uses OpenAI's GPT-4o-mini model for:
- Resume parsing from PDF
- Resume analysis against job descriptions
- Resume scoring with detailed metrics
- Section feedback and improvement suggestions

---

## Scoring Metrics Details

### Keyword Matching (35%)
- Identifies relevant keywords from resume
- Compares with job description (if provided)
- Calculates keyword density and coverage
- Lists matched and missing keywords

### Language Expression (35%)
- **Grammar Quality:** Checks for errors and proper structure
- **Professional Tone:** Evaluates formality and appropriateness
- **Clarity:** Assesses content understandability
- **Action Verbs Usage:** Measures strong vs. passive language

### ATS Readability (30%)
- **Format Compatibility:** Standard sections, no complex formatting
- **Structure Clarity:** Logical flow and organization
- **Parsing Friendliness:** Easy-to-extract information
- **Section Organization:** Proper headings and hierarchy

---

## Future Enhancements

Potential improvements:
1. Batch resume processing
2. Resume template generation
3. Cover letter generation based on resume + job description
4. Real-time collaboration features
5. Resume version control and comparison
6. LinkedIn profile import
7. Multi-language support

---

---

## File Management Endpoints

### Upload File
```http
POST /api/files/upload
```

**Description:** Upload resume files (PDF or DOCX) with automatic processing

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request Body:**
- `file`: Resume file (PDF or DOCX, max 10MB)
- `process`: Optional boolean (default: true) - whether to process file content

**Response:**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file": {
    "file_id": 123,
    "user_id": 1,
    "original_filename": "resume.pdf",
    "sanitized_filename": "secure_resume_20241025.pdf",
    "file_size": 245760,
    "file_type": "pdf",
    "mime_type": "application/pdf",
    "processing_status": "completed",
    "extracted_text": "John Doe Software Engineer...",
    "language": "en",
    "page_count": 2,
    "upload_date": "2024-10-25T10:30:00Z"
  }
}
```

**Status Codes:**
- `201`: File uploaded successfully
- `400`: Invalid file, file type not supported, or file too large
- `401`: Authentication required
- `500`: Upload failed

---

### Download File
```http
GET /api/files/{file_id}/download
```

**Description:** Download an uploaded file

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `inline`: Optional boolean (default: false) - display inline instead of download

**Response:**
- Binary file content with appropriate headers

**Status Codes:**
- `200`: File downloaded successfully
- `401`: Authentication required
- `403`: Access denied to this file
- `404`: File not found
- `500`: Download failed

---

### List Files
```http
GET /api/files
```

**Description:** List user's uploaded files with pagination and filtering

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Files per page (default: 10, max: 100)
- `sort_by`: Sort field (created_at, updated_at, file_size, original_filename)
- `sort_order`: Sort order (asc, desc)
- `mime_type`: Filter by MIME type
- `processing_status`: Filter by processing status (pending, processing, completed, failed)

**Response:**
```json
{
  "success": true,
  "files": [
    {
      "id": 123,
      "original_filename": "resume.pdf",
      "file_size": 245760,
      "file_type": "pdf",
      "processing_status": "completed",
      "upload_date": "2024-10-25T10:30:00Z",
      "page_count": 2,
      "language": "en"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_files": 42,
    "files_per_page": 10
  }
}
```

**Status Codes:**
- `200`: Files retrieved successfully
- `401`: Authentication required
- `500`: Server error

---

### Process File
```http
POST /api/files/{file_id}/process
```

**Description:** Extract text content from an uploaded file

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `force`: Optional boolean (default: false) - force reprocessing of already processed files

**Response:**
```json
{
  "success": true,
  "message": "File processed successfully",
  "processing_result": {
    "success": true,
    "text": "John Doe Software Engineer with 5 years of experience...",
    "page_count": 2,
    "language": "en",
    "metadata": {
      "author": "John Doe",
      "creation_date": "2024-01-15",
      "word_count": 485
    }
  },
  "file_info": {
    "file_id": 123,
    "processing_status": "completed",
    "processing_date": "2024-10-25T10:35:00Z"
  }
}
```

**Status Codes:**
- `200`: File processed successfully
- `400`: Invalid file ID or file already processed (use force=true to reprocess)
- `401`: Authentication required
- `403`: Access denied to this file
- `404`: File not found
- `408`: Processing timeout
- `500`: Processing failed

---

### Delete File
```http
DELETE /api/files/{file_id}
```

**Description:** Delete an uploaded file (soft delete by default)

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `force`: Optional boolean (default: false) - permanent deletion from storage (hard delete)

**Response:**
```json
{
  "success": true,
  "message": "File deleted successfully",
  "file_id": 123,
  "delete_type": "soft"
}
```

**Status Codes:**
- `200`: File deleted successfully
- `401`: Authentication required
- `403`: Access denied to this file
- `404`: File not found
- `500`: Deletion failed

---

## File Management Error Codes

The file management system uses standardized error codes for better error handling:

### Authentication Errors (AUTH_xxx)
- `AUTH_001`: Authentication token missing
- `AUTH_002`: Authentication token invalid
- `AUTH_003`: Authentication token expired
- `AUTH_004`: Access denied to resource

### File Validation Errors (FILE_xxx)
- `FILE_001`: No file provided
- `FILE_002`: File size exceeds limit
- `FILE_003`: File type not supported
- `FILE_004`: File format invalid
- `FILE_005`: File corrupted
- `FILE_006`: Filename invalid

### Storage Errors (STORAGE_xxx)
- `STORAGE_001`: Storage configuration error
- `STORAGE_002`: File upload failed
- `STORAGE_003`: File download failed
- `STORAGE_004`: File deletion failed

### Processing Errors (PROCESS_xxx)
- `PROCESS_001`: File processing failed
- `PROCESS_002`: Processing timeout
- `PROCESS_003`: Unsupported file format
- `PROCESS_004`: Text extraction failed

### Database Errors (DB_xxx)
- `DB_001`: Database operation failed
- `DB_002`: Record not found
- `DB_003`: Record already exists

---

## File Management Configuration

### Environment Variables

**Storage Configuration:**
- `FILE_STORAGE_TYPE`: Storage type ('local' or 's3')
- `LOCAL_STORAGE_PATH`: Path for local file storage
- `AWS_S3_BUCKET`: S3 bucket name (if using S3)
- `AWS_S3_REGION`: AWS region
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

**Upload Limits:**
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 10MB)
- `ALLOWED_MIME_TYPES`: Comma-separated list of allowed MIME types
- `MAX_FILES_PER_USER`: Maximum files per user (default: 100)
- `UPLOAD_TIMEOUT_SECONDS`: Upload timeout (default: 300 seconds)

**Processing Configuration:**
- `MAX_EXTRACTED_TEXT_LENGTH`: Maximum extracted text length
- `PROCESSING_TIMEOUT_SECONDS`: Processing timeout (default: 60 seconds)
- `ENABLE_OCR`: Enable OCR for image-based PDFs (default: false)
- `ENABLE_LANGUAGE_DETECTION`: Enable language detection (default: true)

---

## Support

For issues or questions, please refer to the project documentation or contact the development team.

```
