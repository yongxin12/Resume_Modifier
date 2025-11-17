# File Categorization API Documentation

## Overview
The File Categorization API allows users to organize their uploaded resume files into three predefined categories for better file management and organization.

**Base URL:** `http://localhost:5001`

**Categories Available:**
- **Active**: Frequently used files, ready for immediate use (default)
- **Archived**: Infrequently used files, stored for reference
- **Draft**: Work-in-progress files, not yet finalized

## Authentication
All endpoints require JWT authentication via the `Authorization` header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Endpoints

### 1. Update File Category

Update the category of a single file.

**Endpoint:** `PUT /files/{id}/category`

#### Parameters

**Path Parameters:**
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `id` | integer | ✅ | Unique file identifier | `42` |

**Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | ✅ | JWT bearer token |
| `Content-Type` | string | ✅ | Must be `application/json` |

**Request Body:**
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `category` | string | ✅ | Must be one of: `active`, `archived`, `draft` | Target category |

#### Request Example
```http
PUT /files/42/category HTTP/1.1
Host: localhost:5001
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "category": "archived"
}
```

#### Response Schema

**Success (200 OK):**
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

**Error Responses:**

**400 Bad Request - Invalid Category:**
```json
{
  "success": false,
  "error": "INVALID_INPUT",
  "message": "Invalid category 'invalid'. Must be one of: active, archived, draft",
  "details": {
    "valid_categories": ["active", "archived", "draft"]
  }
}
```

**404 Not Found - File Not Found:**
```json
{
  "success": false,
  "error": "FILE_NOT_FOUND",
  "message": "File with ID 42 not found or access denied",
  "details": {
    "file_id": 42
  }
}
```

---

### 2. Bulk Update Categories

Update categories for multiple files simultaneously.

**Endpoint:** `PUT /files/category`

#### Parameters

**Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | ✅ | JWT bearer token |
| `Content-Type` | string | ✅ | Must be `application/json` |

**Request Body:**
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `file_ids` | array[integer] | ✅ | Non-empty array, max 100 items | Array of file IDs to update |
| `category` | string | ✅ | Must be one of: `active`, `archived`, `draft` | Target category for all files |

#### Request Example
```http
PUT /files/category HTTP/1.1
Host: localhost:5001
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "file_ids": [42, 43, 44],
  "category": "archived"
}
```

#### Response Schema

**Success (200 OK):**
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

**Partial Success (200 OK) - Some files failed:**
```json
{
  "success": true,
  "message": "Bulk category update completed",
  "summary": {
    "total_requested": 3,
    "successful_updates": 2,
    "failed_updates": 1,
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
    }
  ],
  "failed_files": [
    {
      "id": 44,
      "error": "File not found or access denied"
    }
  ]
}
```

**Error Responses:**

**400 Bad Request - Invalid Request:**
```json
{
  "success": false,
  "error": "INVALID_INPUT",
  "message": "file_ids must be a non-empty array of integers"
}
```

---

### 3. List Files by Category

Retrieve files with optional category filtering, pagination, and search.

**Endpoint:** `GET /files`

#### Parameters

**Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | ✅ | JWT bearer token |

**Query Parameters:**
| Parameter | Type | Required | Default | Validation | Description |
|-----------|------|----------|---------|------------|-------------|
| `category` | string | ❌ | null | `active`, `archived`, `draft`, `all` | Filter files by category |
| `page` | integer | ❌ | 1 | Minimum: 1 | Page number for pagination |
| `per_page` | integer | ❌ | 20 | Range: 1-100 | Items per page |
| `sort_by` | string | ❌ | `created_at` | `created_at`, `updated_at`, `original_filename`, `file_size`, `category` | Field to sort by |
| `sort_order` | string | ❌ | `desc` | `asc`, `desc` | Sort direction |
| `search` | string | ❌ | null | Max length: 255 | Search term for filename filtering |

#### Request Examples
```http
# Get all active files
GET /files?category=active HTTP/1.1
Host: localhost:5001
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

# Get archived files with pagination
GET /files?category=archived&page=2&per_page=10 HTTP/1.1
Host: localhost:5001
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

# Search draft files by filename
GET /files?category=draft&search=resume&sort_by=updated_at&sort_order=asc HTTP/1.1
Host: localhost:5001
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

# Get all files (no category filter)
GET /files?category=all HTTP/1.1
Host: localhost:5001
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Response Schema

**Success (200 OK):**
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
        "mime_type": "application/pdf",
        "created_at": "2025-11-01T10:30:00Z",
        "updated_at": "2025-11-16T10:30:00Z",
        "category_updated_at": "2025-11-10T15:20:00Z",
        "category_updated_by": 123
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 8,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    },
    "filter": {
      "category": "active",
      "search": null,
      "sort_by": "created_at",
      "sort_order": "desc"
    }
  }
}
```

**Error Responses:**

**400 Bad Request - Invalid Category:**
```json
{
  "success": false,
  "error": "INVALID_INPUT",
  "message": "Invalid category 'invalid'. Must be one of: active, archived, draft, all",
  "details": {
    "valid_categories": ["active", "archived", "draft", "all"]
  }
}
```

---

### 4. Get Category Statistics

Retrieve file count statistics by category for the authenticated user.

**Endpoint:** `GET /files/categories/stats`

#### Parameters

**Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | ✅ | JWT bearer token |

**Query Parameters:** None

#### Request Example
```http
GET /files/categories/stats HTTP/1.1
Host: localhost:5001
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Response Schema

**Success (200 OK):**
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

---

### 5. Get Available Categories

Retrieve information about all available file categories.

**Endpoint:** `GET /files/categories`

#### Parameters

**Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | ✅ | JWT bearer token |

**Query Parameters:** None

#### Request Example
```http
GET /files/categories HTTP/1.1
Host: localhost:5001
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Response Schema

**Success (200 OK):**
```json
{
  "success": true,
  "categories": {
    "active": {
      "name": "active",
      "display_name": "Active",
      "description": "Frequently used files, ready for immediate use",
      "is_default": true
    },
    "archived": {
      "name": "archived",
      "display_name": "Archived",
      "description": "Infrequently used files, stored for reference",
      "is_default": false
    },
    "draft": {
      "name": "draft",
      "display_name": "Draft",
      "description": "Work-in-progress files, not yet finalized",
      "is_default": false
    }
  },
  "valid_categories": ["active", "archived", "draft"],
  "default_category": "active"
}
```

---

## Error Handling

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_INPUT` | Request validation failed |
| 401 | `UNAUTHORIZED` | Missing or invalid JWT token |
| 403 | `PERMISSION_DENIED` | Access denied to resource |
| 404 | `FILE_NOT_FOUND` | Requested file not found |
| 408 | `TIMEOUT` | Request timeout |
| 500 | `DATABASE_ERROR` | Internal database error |
| 500 | `UNKNOWN` | Unexpected server error |

### Error Response Format

All error responses follow this consistent format:

```json
{
  "success": false,
  "error": "ERROR_CODE",
  "message": "Human-readable error description",
  "details": {
    "additional": "context information"
  }
}
```

### Validation Rules

#### Category Validation
- Must be exactly one of: `active`, `archived`, `draft`
- Case-sensitive (lowercase only)
- Cannot be empty or null

#### File ID Validation
- Must be positive integer
- File must exist and belong to authenticated user
- File must be active (not soft-deleted)

#### Pagination Validation
- `page`: Minimum value is 1
- `per_page`: Range is 1-100
- Invalid values are automatically corrected to defaults

#### Search Validation
- Maximum length: 255 characters
- Special characters are properly escaped
- Empty string treated as no search filter

---

## Usage Examples

### JavaScript/Fetch API

```javascript
// Update single file category
const updateFileCategory = async (fileId, category) => {
  const response = await fetch(`/files/${fileId}/category`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ category })
  });
  
  return await response.json();
};

// Get files by category with pagination
const getFilesByCategory = async (category = 'active', page = 1) => {
  const response = await fetch(`/files?category=${category}&page=${page}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};

// Get category statistics
const getCategoryStats = async () => {
  const response = await fetch('/files/categories/stats', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};
```

### Python/Requests

```python
import requests

# Configuration
BASE_URL = 'http://localhost:5001'
TOKEN = 'your_jwt_token_here'
HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

# Update file category
def update_file_category(file_id, category):
    url = f'{BASE_URL}/files/{file_id}/category'
    data = {'category': category}
    response = requests.put(url, json=data, headers=HEADERS)
    return response.json()

# Bulk update categories
def bulk_update_categories(file_ids, category):
    url = f'{BASE_URL}/files/category'
    data = {'file_ids': file_ids, 'category': category}
    response = requests.put(url, json=data, headers=HEADERS)
    return response.json()

# Get files by category
def get_files_by_category(category='active', page=1, per_page=20):
    url = f'{BASE_URL}/files'
    params = {
        'category': category,
        'page': page,
        'per_page': per_page
    }
    response = requests.get(url, params=params, headers=HEADERS)
    return response.json()
```

### cURL Examples

```bash
# Update single file category
curl -X PUT "http://localhost:5001/files/42/category" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{"category": "archived"}'

# Bulk update categories
curl -X PUT "http://localhost:5001/files/category" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{"file_ids": [42, 43, 44], "category": "draft"}'

# Get active files with pagination
curl -X GET "http://localhost:5001/files?category=active&page=1&per_page=10" \
  -H "Authorization: Bearer your_jwt_token"

# Get category statistics
curl -X GET "http://localhost:5001/files/categories/stats" \
  -H "Authorization: Bearer your_jwt_token"
```

---

## Rate Limiting

Currently, there are no specific rate limits for these endpoints. However, it's recommended to:

- Batch multiple file updates using the bulk endpoint
- Implement client-side throttling for frequent requests
- Cache category statistics to reduce server load

---

## Integration Notes

### Frontend Integration
- Use category statistics for dashboard widgets
- Implement category filters in file listing components
- Provide bulk action UI for category management
- Show category information in file metadata displays

### Database Considerations
- All category operations are transactional
- Indexes are optimized for category-based queries
- Audit trail is maintained for all category changes
- Soft-deleted files are excluded from all operations

### Security Notes
- All endpoints require valid JWT authentication
- Users can only access and modify their own files
- Category changes are logged with user information
- Input validation prevents SQL injection and XSS attacks