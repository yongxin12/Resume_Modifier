"""
Swagger/OpenAPI specification updates for Enhanced File Management API

Add these specifications to the enhanced upload endpoint and new endpoints
in app/server.py for automatic API documentation generation.
"""

# Enhanced File Upload Endpoint Swagger Spec
upload_swagger_spec = """
---
tags:
  - Files
summary: Enhanced file upload with duplicate detection and Google Drive integration
description: |
  Upload a file with advanced features including:
  - Automatic duplicate detection using SHA-256 hashing
  - Google Drive integration with optional conversion to Google Docs
  - Intelligent filename generation for duplicates
  - Comprehensive error handling with user-friendly messages
consumes:
  - multipart/form-data
parameters:
  - name: Authorization
    in: header
    type: string
    required: true
    description: Bearer JWT token
  - name: file
    in: formData
    type: file
    required: true
    description: File to upload (PDF or DOCX)
  - name: process
    in: formData
    type: string
    enum: ['true', 'false']
    default: 'false'
    description: Whether to process the file immediately
  - name: google_drive
    in: query
    type: string
    enum: ['true', 'false']
    description: Enable Google Drive upload
  - name: convert_to_doc
    in: query
    type: string
    enum: ['true', 'false']
    description: Convert to Google Docs format
  - name: share_with_user
    in: query
    type: string
    enum: ['true', 'false']
    description: Share Google Drive file with user
responses:
  201:
    description: File uploaded successfully
    schema:
      type: object
      properties:
        success:
          type: boolean
          example: true
        message:
          type: string
          example: "File uploaded successfully"
        file:
          type: object
          properties:
            id:
              type: integer
              example: 123
            original_filename:
              type: string
              example: "resume.pdf"
            display_filename:
              type: string
              example: "resume.pdf"
            file_size:
              type: integer
              example: 1024
            mime_type:
              type: string
              example: "application/pdf"
            duplicate_info:
              type: object
              properties:
                is_duplicate:
                  type: boolean
                  example: false
                duplicate_sequence:
                  type: integer
                  nullable: true
                original_file_id:
                  type: integer
                  nullable: true
            google_drive:
              type: object
              nullable: true
              properties:
                file_id:
                  type: string
                  example: "1ABC123xyz"
                doc_id:
                  type: string
                  nullable: true
                  example: "1DEF456abc"
                is_shared:
                  type: boolean
                  example: true
                drive_link:
                  type: string
                  example: "https://drive.google.com/file/d/1ABC123xyz/view"
                doc_link:
                  type: string
                  nullable: true
                  example: "https://docs.google.com/document/d/1DEF456abc/edit"
        duplicate_notification:
          type: string
          nullable: true
          example: "Duplicate file detected. Saved as 'resume (1).pdf' to avoid conflicts."
        warnings:
          type: array
          items:
            type: string
          example: []
  400:
    description: Bad request
    schema:
      $ref: '#/definitions/ErrorResponse'
  401:
    description: Unauthorized
    schema:
      $ref: '#/definitions/ErrorResponse'
  500:
    description: Internal server error
    schema:
      $ref: '#/definitions/ErrorResponse'
"""

# Google Doc Access Endpoint Swagger Spec
google_doc_access_swagger_spec = """
---
tags:
  - Files
  - Google Drive
summary: Access Google Doc version of uploaded file
description: |
  Get Google Drive and Google Docs links for a file that has been uploaded to Google Drive.
  Optionally ensure the file is properly shared with the user.
parameters:
  - name: Authorization
    in: header
    type: string
    required: true
    description: Bearer JWT token
  - name: file_id
    in: path
    type: integer
    required: true
    description: ID of the file
  - name: ensure_sharing
    in: query
    type: string
    enum: ['true', 'false']
    default: 'false'
    description: Ensure file is shared with user
responses:
  200:
    description: Google Doc information retrieved successfully
    schema:
      type: object
      properties:
        success:
          type: boolean
          example: true
        google_doc:
          type: object
          properties:
            file_id:
              type: string
              example: "1ABC123xyz"
            doc_id:
              type: string
              nullable: true
              example: "1DEF456abc"
            has_doc_version:
              type: boolean
              example: true
            is_shared:
              type: boolean
              example: true
            drive_link:
              type: string
              example: "https://drive.google.com/file/d/1ABC123xyz/view"
            doc_link:
              type: string
              nullable: true
              example: "https://docs.google.com/document/d/1DEF456abc/edit"
            sharing_info:
              type: object
              nullable: true
              properties:
                access_level:
                  type: string
                  example: "writer"
                shared_at:
                  type: string
                  format: date-time
                  example: "2024-11-14T10:00:00.000Z"
  404:
    description: File not found or no Google Drive version available
    schema:
      $ref: '#/definitions/ErrorResponse'
  401:
    description: Unauthorized
    schema:
      $ref: '#/definitions/ErrorResponse'
"""

# File Restoration Endpoint Swagger Spec
file_restore_swagger_spec = """
---
tags:
  - Files
summary: Restore soft-deleted file
description: |
  Restore a file that has been soft-deleted, making it available again.
  Only the file owner can restore their own files.
parameters:
  - name: Authorization
    in: header
    type: string
    required: true
    description: Bearer JWT token
  - name: file_id
    in: path
    type: integer
    required: true
    description: ID of the file to restore
responses:
  200:
    description: File restored successfully
    schema:
      type: object
      properties:
        success:
          type: boolean
          example: true
        message:
          type: string
          example: "File restored successfully"
        file:
          type: object
          properties:
            id:
              type: integer
              example: 123
            original_filename:
              type: string
              example: "resume.pdf"
            display_filename:
              type: string
              example: "resume.pdf"
            deleted_at:
              type: string
              nullable: true
              example: null
            deleted_by:
              type: integer
              nullable: true
              example: null
            restored_at:
              type: string
              format: date-time
              example: "2024-11-14T10:30:00.000Z"
            restored_by:
              type: integer
              example: 1
  404:
    description: File not found or not deleted
    schema:
      $ref: '#/definitions/ErrorResponse'
  401:
    description: Unauthorized
    schema:
      $ref: '#/definitions/ErrorResponse'
"""

# Enhanced File Listing Swagger Spec
enhanced_file_listing_swagger_spec = """
---
tags:
  - Files
summary: List files with soft deletion support
description: |
  List user's files with support for including/excluding deleted files.
  Supports pagination, sorting, and filtering options.
parameters:
  - name: Authorization
    in: header
    type: string
    required: true
    description: Bearer JWT token
  - name: include_deleted
    in: query
    type: string
    enum: ['true', 'false']
    default: 'false'
    description: Include soft-deleted files
  - name: page
    in: query
    type: integer
    minimum: 1
    default: 1
    description: Page number for pagination
  - name: per_page
    in: query
    type: integer
    minimum: 1
    maximum: 100
    default: 10
    description: Items per page
  - name: sort
    in: query
    type: string
    enum: ['name', 'date', 'size']
    default: 'date'
    description: Sort field
  - name: order
    in: query
    type: string
    enum: ['asc', 'desc']
    default: 'desc'
    description: Sort order
responses:
  200:
    description: Files retrieved successfully
    schema:
      type: object
      properties:
        success:
          type: boolean
          example: true
        files:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 123
              original_filename:
                type: string
                example: "resume.pdf"
              display_filename:
                type: string
                example: "resume.pdf"
              file_size:
                type: integer
                example: 1024
              mime_type:
                type: string
                example: "application/pdf"
              uploaded_at:
                type: string
                format: date-time
                example: "2024-11-14T10:00:00.000Z"
              is_deleted:
                type: boolean
                example: false
              duplicate_info:
                type: object
                properties:
                  is_duplicate:
                    type: boolean
                    example: false
                  duplicate_sequence:
                    type: integer
                    nullable: true
              google_drive:
                type: object
                nullable: true
                properties:
                  has_drive_version:
                    type: boolean
                    example: true
                  has_doc_version:
                    type: boolean
                    example: true
                  is_shared:
                    type: boolean
                    example: true
        pagination:
          type: object
          properties:
            page:
              type: integer
              example: 1
            per_page:
              type: integer
              example: 10
            total:
              type: integer
              example: 25
            pages:
              type: integer
              example: 3
        total:
          type: integer
          example: 25
  401:
    description: Unauthorized
    schema:
      $ref: '#/definitions/ErrorResponse'
"""

# Error Response Definition
error_response_definition = """
ErrorResponse:
  type: object
  properties:
    success:
      type: boolean
      example: false
    error_code:
      type: string
      example: "FILE_SIZE_EXCEEDED"
    message:
      type: string
      example: "File is too large. Please upload a file smaller than 10MB"
    timestamp:
      type: string
      format: date-time
      example: "2024-11-14T10:00:00.000Z"
    details:
      type: object
      nullable: true
      description: Additional error details when available
"""

# Admin Endpoints Swagger Specs
admin_deleted_files_swagger_spec = """
---
tags:
  - Admin
  - Files
summary: List deleted files (Admin only)
description: |
  List all soft-deleted files across all users. Requires admin privileges.
parameters:
  - name: Authorization
    in: header
    type: string
    required: true
    description: Bearer JWT token (admin)
  - name: page
    in: query
    type: integer
    minimum: 1
    default: 1
    description: Page number for pagination
  - name: per_page
    in: query
    type: integer
    minimum: 1
    maximum: 100
    default: 10
    description: Items per page
  - name: user_id
    in: query
    type: integer
    description: Filter by specific user ID
responses:
  200:
    description: Deleted files retrieved successfully
    schema:
      type: object
      properties:
        success:
          type: boolean
          example: true
        files:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 124
              user_id:
                type: integer
                example: 5
              user_email:
                type: string
                example: "user@example.com"
              original_filename:
                type: string
                example: "old_resume.pdf"
              display_filename:
                type: string
                example: "old_resume.pdf"
              file_size:
                type: integer
                example: 2048
              deleted_at:
                type: string
                format: date-time
                example: "2024-11-13T15:30:00.000Z"
              deleted_by:
                type: integer
                example: 5
              days_deleted:
                type: integer
                example: 1
        pagination:
          type: object
          properties:
            page:
              type: integer
              example: 1
            per_page:
              type: integer
              example: 10
            total:
              type: integer
              example: 5
            pages:
              type: integer
              example: 1
        total:
          type: integer
          example: 5
  401:
    description: Unauthorized
    schema:
      $ref: '#/definitions/ErrorResponse'
  403:
    description: Admin access required
    schema:
      $ref: '#/definitions/ErrorResponse'
"""