# 📸 Thumbnail Feature Specification

## Overview

This document defines the comprehensive implementation of PDF thumbnail generation and delivery for the `/api/files/{file_id}/info` endpoint, enabling users to preview resume files visually before accessing full content.

---

## 1. Feature Requirements

### 1.1 User Story
**As a user, I want to see thumbnails of the files I want to preview, so I can quickly identify and select the correct resume without opening the full document.**

### 1.2 Functional Requirements

| Req ID | Description | User Story | Expected Behavior |
|--------|-------------|------------|-------------------|
| **THUMB-01** | **Thumbnail Generation** | As a user, I want thumbnails generated automatically when I upload PDFs | System generates 150x200px thumbnails from first page of uploaded PDF files |
| **THUMB-02** | **Thumbnail Storage** | As a developer, I want thumbnails stored efficiently with proper organization | Thumbnails stored in `/uploads/thumbnails/` directory with unique filenames matching file IDs |
| **THUMB-03** | **Thumbnail Delivery** | As a user, I want thumbnail URLs in file info responses | `/api/files/{file_id}/info` includes `thumbnail_url` field pointing to accessible thumbnail image |
| **THUMB-04** | **Thumbnail Endpoint** | As a user, I want direct access to thumbnail images | New `/api/files/{file_id}/thumbnail` endpoint serves thumbnail images with proper caching headers |
| **THUMB-05** | **Error Handling** | As a user, I want graceful handling when thumbnails are unavailable | System provides default placeholder image when thumbnail generation fails or is unavailable |
| **THUMB-06** | **Performance Optimization** | As a developer, I want thumbnail generation to be efficient and non-blocking | Thumbnails generated asynchronously after upload, with status tracking in database |

---

## 2. Technical Specification

### 2.1 Database Schema Changes

**Add to `ResumeFile` model:**

```python
class ResumeFile(db.Model):
    # ... existing fields ...
    
    # Thumbnail Fields
    has_thumbnail = db.Column(db.Boolean, default=False)  # Whether thumbnail exists
    thumbnail_path = db.Column(db.String(500), nullable=True)  # Path to thumbnail file
    thumbnail_status = db.Column(db.String(50), default='pending')  # pending, generating, completed, failed
    thumbnail_generated_at = db.Column(db.DateTime, nullable=True)  # When thumbnail was created
    thumbnail_error = db.Column(db.Text, nullable=True)  # Error message if generation failed
```

### 2.2 Migration Script

```python
# Migration: Add thumbnail fields to resume_files table
def upgrade():
    op.add_column('resume_files', sa.Column('has_thumbnail', sa.Boolean(), default=False))
    op.add_column('resume_files', sa.Column('thumbnail_path', sa.String(500), nullable=True))
    op.add_column('resume_files', sa.Column('thumbnail_status', sa.String(50), default='pending'))
    op.add_column('resume_files', sa.Column('thumbnail_generated_at', sa.DateTime(), nullable=True))
    op.add_column('resume_files', sa.Column('thumbnail_error', sa.Text(), nullable=True))
```

### 2.3 Thumbnail Generation Service

**File: `core/app/services/thumbnail_service.py`**

```python
class ThumbnailService:
    """Service for generating and managing PDF thumbnails"""
    
    THUMBNAIL_SIZE = (150, 200)  # width x height
    THUMBNAIL_DIR = 'uploads/thumbnails'
    THUMBNAIL_QUALITY = 85
    THUMBNAIL_FORMAT = 'JPEG'
    
    @staticmethod
    def generate_thumbnail(file_path: str, output_path: str) -> bool:
        """Generate thumbnail from PDF first page"""
        
    @staticmethod
    def get_thumbnail_path(file_id: int) -> str:
        """Get expected thumbnail file path for given file ID"""
        
    @staticmethod
    def ensure_thumbnail_directory() -> None:
        """Ensure thumbnail directory exists with proper permissions"""
        
    @staticmethod
    def get_default_thumbnail() -> str:
        """Get path to default placeholder thumbnail"""
```

### 2.4 API Response Schema Changes

**Updated `/api/files/{file_id}/info` Response:**

```json
{
  "success": true,
  "file": {
    "id": 42,
    "original_filename": "Resume_2024.pdf",
    "file_size": 524288,
    "file_size_formatted": "512 KB",
    "mime_type": "application/pdf",
    // ... existing fields ...
    
    // NEW THUMBNAIL FIELDS
    "thumbnail": {
      "has_thumbnail": true,
      "thumbnail_url": "/api/files/42/thumbnail",
      "thumbnail_status": "completed",
      "thumbnail_generated_at": "2025-11-22T10:30:00Z"
    }
  }
}
```

### 2.5 New Thumbnail Endpoint

**Endpoint: `GET /api/files/{file_id}/thumbnail`**

```python
@api.route('/api/files/<int:file_id>/thumbnail', methods=['GET'])
@token_required
def get_file_thumbnail(file_id):
    """
    Get thumbnail image for a file
    ---
    tags:
      - File Management
    parameters:
      - name: file_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Thumbnail image
        content:
          image/jpeg:
            schema:
              type: string
              format: binary
      404:
        description: Thumbnail not found
    """
```

---

## 3. Implementation Architecture

### 3.1 Component Interaction Flow

```
PDF Upload → File Processing → Thumbnail Generation → Database Update → API Response
     ↓              ↓               ↓                    ↓              ↓
1. User uploads → 2. Extract text → 3. Generate thumb → 4. Update model → 5. Return with thumbnail_url
```

### 3.2 Directory Structure

```
core/app/
├── services/
│   ├── thumbnail_service.py          # New: Thumbnail generation logic
│   └── file_processing_service.py     # Enhanced: Include thumbnail generation
├── utils/
│   └── thumbnail_validator.py         # New: Thumbnail validation utilities
└── models/
    └── temp.py                        # Enhanced: Add thumbnail fields

uploads/
├── files/                            # Existing: Original uploaded files
└── thumbnails/                       # New: Generated thumbnail images
    ├── 1.jpg                         # Thumbnail for file ID 1
    ├── 2.jpg                         # Thumbnail for file ID 2
    └── default_placeholder.jpg       # Default when generation fails
```

### 3.3 Configuration Settings

**Add to `.env`:**

```env
# Thumbnail Configuration
THUMBNAIL_ENABLED=true
THUMBNAIL_QUALITY=85
THUMBNAIL_MAX_SIZE=150x200
THUMBNAIL_FORMAT=JPEG
THUMBNAIL_DEFAULT_PATH=static/default_thumbnail.jpg
```

---

## 4. Error Handling Strategy

### 4.1 Generation Failure Scenarios

| Scenario | Response Strategy | User Experience |
|----------|------------------|-----------------|
| **PDF Corrupt/Unreadable** | Log error, set status='failed', use default thumbnail | Default placeholder shown |
| **Insufficient Permissions** | Log error, retry with elevated permissions | Graceful fallback to default |
| **Storage Space Full** | Log error, cleanup old thumbnails, retry | Temporary default until retry |
| **Processing Timeout** | Cancel generation, set status='failed' | Default placeholder shown |

### 4.2 Thumbnail Status States

```python
THUMBNAIL_STATUS = {
    'pending': 'Not yet generated',
    'generating': 'Currently being processed', 
    'completed': 'Successfully generated',
    'failed': 'Generation failed',
    'unavailable': 'Thumbnail not supported for this file type'
}
```

---

## 5. Performance Considerations

### 5.1 Optimization Strategies

1. **Asynchronous Generation**: Thumbnails generated in background after upload
2. **Caching Headers**: Thumbnail endpoint includes proper cache-control headers
3. **Lazy Loading**: Thumbnails generated only when first requested (optional)
4. **Batch Processing**: Multiple thumbnails processed in batches during low usage

### 5.2 Resource Management

- **File Size Limit**: Thumbnails limited to max 50KB each
- **Cleanup Strategy**: Remove thumbnails when original files are deleted
- **Storage Monitoring**: Log warnings when thumbnail storage exceeds thresholds

---

## 6. Security Considerations

### 6.1 Access Control

1. **Authentication Required**: Thumbnail endpoint requires valid JWT token
2. **User Authorization**: Users can only access thumbnails for their own files
3. **File Path Validation**: Prevent directory traversal attacks in thumbnail paths

### 6.2 Content Security

1. **MIME Type Validation**: Verify generated thumbnails are valid images
2. **Size Limits**: Enforce maximum dimensions and file size for thumbnails
3. **Sanitization**: Clean file paths and prevent injection attacks

---

## 7. Testing Strategy

### 7.1 Unit Tests Required

- `test_thumbnail_service.py`: Test thumbnail generation logic
- `test_thumbnail_api.py`: Test API endpoints with thumbnail fields
- `test_thumbnail_validator.py`: Test validation utilities

### 7.2 Integration Tests Required

- Test full upload-to-thumbnail workflow
- Test thumbnail API endpoint with authentication
- Test error handling for failed generation scenarios

### 7.3 Performance Tests

- Test thumbnail generation time limits
- Test concurrent thumbnail generation
- Test storage cleanup operations

---

## 8. Deployment Considerations

### 8.1 Dependencies

**Add to `requirements.txt`:**

```
pdf2image>=1.16.3    # PDF to image conversion
Pillow>=10.0.0       # Image processing and optimization
```

### 8.2 System Requirements

- **ImageMagick**: Required for PDF rendering (install via system package manager)
- **Ghostscript**: Required for PDF processing (install via system package manager)
- **Storage**: Additional 10-50MB per 1000 uploaded PDFs for thumbnails

### 8.3 Environment Setup

```bash
# Ubuntu/Debian
sudo apt-get install imagemagick ghostscript

# CentOS/RHEL
sudo yum install ImageMagick ghostscript

# macOS
brew install imagemagick ghostscript
```

---

## 9. Monitoring and Metrics

### 9.1 Key Metrics to Track

- Thumbnail generation success rate
- Average generation time per file
- Storage usage for thumbnails
- API response times for thumbnail endpoints

### 9.2 Logging Requirements

- Log all thumbnail generation attempts with outcomes
- Log storage cleanup operations
- Log performance metrics for optimization

---

## 10. Future Enhancements

### 10.1 Potential Improvements

1. **Multiple Thumbnail Sizes**: Generate small, medium, large variants
2. **Video Thumbnails**: Support for video file previews
3. **Smart Cropping**: AI-powered thumbnail cropping for optimal preview
4. **CDN Integration**: Distribute thumbnails via Content Delivery Network

### 10.2 Scalability Considerations

- **Cloud Storage**: Move thumbnails to S3/CloudFlare for better performance
- **Microservice Architecture**: Separate thumbnail service for horizontal scaling
- **Caching Layer**: Redis cache for frequently accessed thumbnails

---

This specification provides a comprehensive foundation for implementing the thumbnail feature while maintaining consistency with the existing project architecture and following test-driven development principles.