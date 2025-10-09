# Storage API Reference

Complete API reference for the ToolBoxAI Storage System. All endpoints support authentication via JWT tokens and respect organization-level multi-tenancy.

## Base URL

```
https://api.toolboxai.com/api/v1/storage
```

## Authentication

All endpoints require authentication via Bearer token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

The token must include the following claims:
- `user_id`: Current user identifier
- `organization_id`: Organization context
- `role`: User role (student, teacher, admin)

## Rate Limiting

| Endpoint Category | Rate Limit | Window |
|------------------|------------|---------|
| File Upload | 100 requests | 1 hour |
| File Download | 1000 requests | 1 hour |
| Admin Operations | 50 requests | 1 hour |
| Bulk Operations | 10 requests | 1 hour |

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1643723400
```

## File Upload

### Upload Single File

Upload a single file with metadata and processing options.

**Endpoint:** `POST /files/upload`

**Content-Type:** `multipart/form-data`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | The file to upload |
| `category` | string | Yes | File category (see categories below) |
| `title` | string | No | Human-readable title |
| `description` | string | No | File description |
| `tags` | string[] | No | Array of tags |
| `virus_scan` | boolean | No | Enable virus scanning (default: true) |
| `generate_thumbnails` | boolean | No | Generate image thumbnails |
| `optimize_images` | boolean | No | Optimize image files |
| `retention_days` | integer | No | Custom retention period |

**Request Example:**

```bash
curl -X POST "https://api.toolboxai.com/api/v1/storage/files/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "category=educational_content" \
  -F "title=Biology Textbook Chapter 1" \
  -F "description=Introduction to cellular biology" \
  -F "tags=biology,textbook,cells" \
  -F "virus_scan=true"
```

**Response (201 Created):**

```json
{
  "status": "success",
  "data": {
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "filename": "biology-chapter-1.pdf",
    "original_filename": "document.pdf",
    "file_size": 2048576,
    "mime_type": "application/pdf",
    "status": "processing",
    "category": "educational_content",
    "title": "Biology Textbook Chapter 1",
    "description": "Introduction to cellular biology",
    "tags": ["biology", "textbook", "cells"],
    "cdn_url": "https://cdn.toolboxai.com/files/f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "thumbnail_url": null,
    "checksum": "sha256:a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
    "virus_scanned": false,
    "created_at": "2025-01-27T10:30:00Z",
    "updated_at": "2025-01-27T10:30:00Z"
  },
  "message": "File uploaded successfully",
  "metadata": {
    "processing_eta": "30 seconds",
    "estimated_scan_time": "15 seconds"
  }
}
```

### Upload with Progress Tracking

For large files, use the resumable upload endpoint with progress tracking.

**Endpoint:** `POST /files/upload/resumable`

**Content-Type:** `application/json`

**Request Body:**

```json
{
  "filename": "large-video.mp4",
  "file_size": 104857600,
  "mime_type": "video/mp4",
  "category": "media_resource",
  "title": "Lecture Recording",
  "chunk_size": 1048576,
  "metadata": {
    "course_id": "bio101",
    "lecture_number": 5
  }
}
```

**Response (201 Created):**

```json
{
  "status": "success",
  "data": {
    "upload_id": "upload_123456789",
    "upload_url": "https://api.toolboxai.com/api/v1/storage/files/upload/resumable/upload_123456789",
    "chunk_size": 1048576,
    "total_chunks": 100,
    "expires_at": "2025-01-27T11:30:00Z"
  }
}
```

### Upload File Chunk

**Endpoint:** `PUT /files/upload/resumable/{upload_id}`

**Headers:**
- `Content-Range: bytes 0-1048575/104857600`
- `Content-Type: application/octet-stream`

**Response (206 Partial Content or 201 Created):**

```json
{
  "status": "success",
  "data": {
    "upload_id": "upload_123456789",
    "chunks_received": 1,
    "total_chunks": 100,
    "bytes_uploaded": 1048576,
    "total_bytes": 104857600,
    "progress_percentage": 1.0,
    "completed": false
  }
}
```

### Batch Upload

Upload multiple files in a single request.

**Endpoint:** `POST /files/upload/batch`

**Content-Type:** `multipart/form-data`

**Parameters:**
- Multiple `file` parameters
- `manifest`: JSON array of file metadata

**Request Example:**

```bash
curl -X POST "https://api.toolboxai.com/api/v1/storage/files/upload/batch" \
  -H "Authorization: Bearer <token>" \
  -F "file=@file1.pdf" \
  -F "file=@file2.pdf" \
  -F 'manifest=[
    {
      "filename": "file1.pdf",
      "category": "educational_content",
      "title": "Chapter 1"
    },
    {
      "filename": "file2.pdf",
      "category": "educational_content",
      "title": "Chapter 2"
    }
  ]'
```

**Response (201 Created):**

```json
{
  "status": "success",
  "data": {
    "batch_id": "batch_987654321",
    "files": [
      {
        "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "filename": "file1.pdf",
        "status": "processing",
        "cdn_url": "https://cdn.toolboxai.com/files/f47ac10b-58cc-4372-a567-0e02b2c3d479"
      },
      {
        "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d480",
        "filename": "file2.pdf",
        "status": "processing",
        "cdn_url": "https://cdn.toolboxai.com/files/f47ac10b-58cc-4372-a567-0e02b2c3d480"
      }
    ],
    "total_files": 2,
    "successful_uploads": 2,
    "failed_uploads": 0
  }
}
```

## File Management

### Get File Information

Retrieve detailed information about a specific file.

**Endpoint:** `GET /files/{file_id}`

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "filename": "biology-chapter-1.pdf",
    "original_filename": "document.pdf",
    "file_size": 2048576,
    "mime_type": "application/pdf",
    "file_extension": ".pdf",
    "status": "available",
    "category": "educational_content",
    "title": "Biology Textbook Chapter 1",
    "description": "Introduction to cellular biology",
    "tags": ["biology", "textbook", "cells"],
    "storage_path": "org_123/educational_content/2025/01/biology-chapter-1.pdf",
    "bucket_name": "toolboxai-org-123",
    "cdn_url": "https://cdn.toolboxai.com/files/f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "thumbnail_url": "https://cdn.toolboxai.com/thumbs/f47ac10b-58cc-4372-a567-0e02b2c3d479_300x300.webp",
    "checksum": "sha256:a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
    "virus_scanned": true,
    "virus_scan_result": {
      "is_clean": true,
      "scanned_at": "2025-01-27T10:30:15Z",
      "scan_duration_ms": 1250
    },
    "contains_pii": false,
    "requires_consent": false,
    "retention_days": 2555,
    "deletion_date": null,
    "uploaded_by": "user_456",
    "download_count": 15,
    "last_accessed_at": "2025-01-27T09:45:00Z",
    "created_at": "2025-01-27T10:30:00Z",
    "updated_at": "2025-01-27T10:30:15Z",
    "metadata": {
      "course_id": "bio101",
      "chapter_number": 1,
      "approval_status": "approved"
    }
  }
}
```

### List Files

Retrieve a paginated list of files with filtering options.

**Endpoint:** `GET /files`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number (default: 1) |
| `size` | integer | Items per page (default: 20, max: 100) |
| `category` | string | Filter by file category |
| `status` | string | Filter by file status |
| `search` | string | Search in title, description, tags |
| `tags` | string[] | Filter by tags (comma-separated) |
| `uploaded_by` | string | Filter by uploader user ID |
| `min_size` | integer | Minimum file size in bytes |
| `max_size` | integer | Maximum file size in bytes |
| `created_after` | string | ISO date filter |
| `created_before` | string | ISO date filter |
| `sort_by` | string | Sort field (created_at, file_size, title) |
| `sort_order` | string | Sort direction (asc, desc) |

**Request Example:**

```bash
curl "https://api.toolboxai.com/api/v1/storage/files?category=educational_content&search=biology&page=1&size=10&sort_by=created_at&sort_order=desc" \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "files": [
      {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "filename": "biology-chapter-1.pdf",
        "title": "Biology Textbook Chapter 1",
        "file_size": 2048576,
        "mime_type": "application/pdf",
        "status": "available",
        "category": "educational_content",
        "cdn_url": "https://cdn.toolboxai.com/files/f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "thumbnail_url": "https://cdn.toolboxai.com/thumbs/f47ac10b-58cc-4372-a567-0e02b2c3d479_300x300.webp",
        "download_count": 15,
        "created_at": "2025-01-27T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 10,
      "total_items": 45,
      "total_pages": 5,
      "has_next": true,
      "has_previous": false
    }
  }
}
```

### Update File Metadata

Update file information without changing the file content.

**Endpoint:** `PATCH /files/{file_id}`

**Request Body:**

```json
{
  "title": "Updated Biology Chapter 1",
  "description": "Comprehensive introduction to cellular biology with diagrams",
  "tags": ["biology", "textbook", "cells", "diagrams"],
  "metadata": {
    "course_id": "bio101",
    "chapter_number": 1,
    "approval_status": "approved",
    "last_reviewed": "2025-01-27"
  },
  "retention_days": 3650
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "title": "Updated Biology Chapter 1",
    "description": "Comprehensive introduction to cellular biology with diagrams",
    "tags": ["biology", "textbook", "cells", "diagrams"],
    "metadata": {
      "course_id": "bio101",
      "chapter_number": 1,
      "approval_status": "approved",
      "last_reviewed": "2025-01-27"
    },
    "retention_days": 3650,
    "updated_at": "2025-01-27T11:00:00Z"
  },
  "message": "File metadata updated successfully"
}
```

## File Download

### Get Download URL

Generate a secure, time-limited download URL.

**Endpoint:** `GET /files/{file_id}/download`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `expires_in` | integer | URL expiration in seconds (default: 3600) |
| `disposition` | string | attachment or inline (default: inline) |
| `filename` | string | Custom download filename |

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "download_url": "https://cdn.toolboxai.com/files/f47ac10b-58cc-4372-a567-0e02b2c3d479?token=xyz&expires=1643726400",
    "expires_at": "2025-01-27T12:00:00Z",
    "file_size": 2048576,
    "mime_type": "application/pdf",
    "filename": "biology-chapter-1.pdf"
  }
}
```

### Stream File Content

Stream file content directly (for small files).

**Endpoint:** `GET /files/{file_id}/stream`

**Response:** Raw file content with appropriate headers

```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Length: 2048576
Content-Disposition: inline; filename="biology-chapter-1.pdf"
Cache-Control: public, max-age=3600
ETag: "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"

[Binary file content]
```

## File Sharing

### Create Share Link

Generate a shareable link with configurable permissions and expiration.

**Endpoint:** `POST /files/{file_id}/shares`

**Request Body:**

```json
{
  "share_type": "public_link",
  "expires_in_hours": 48,
  "password": "optional-password",
  "can_download": true,
  "view_only": false,
  "max_downloads": 100,
  "shared_with_users": [],
  "shared_with_class": null,
  "message": "Please review this document"
}
```

**Response (201 Created):**

```json
{
  "status": "success",
  "data": {
    "share_id": "share_789123456",
    "share_token": "{{SHARE_TOKEN}}",
    "share_url": "https://share.toolboxai.com/s/abc123def456ghi789",
    "share_type": "public_link",
    "password_protected": true,
    "can_download": true,
    "view_only": false,
    "expires_at": "2025-01-29T10:30:00Z",
    "max_downloads": 100,
    "download_count": 0,
    "created_at": "2025-01-27T10:30:00Z"
  },
  "message": "Share link created successfully"
}
```

### List File Shares

Get all active shares for a file.

**Endpoint:** `GET /files/{file_id}/shares`

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "shares": [
      {
        "share_id": "share_789123456",
        "share_type": "public_link",
        "share_url": "https://share.toolboxai.com/s/abc123def456ghi789",
        "password_protected": true,
        "can_download": true,
        "expires_at": "2025-01-29T10:30:00Z",
        "download_count": 5,
        "max_downloads": 100,
        "last_accessed_at": "2025-01-27T11:15:00Z",
        "created_at": "2025-01-27T10:30:00Z"
      }
    ],
    "total_shares": 1
  }
}
```

### Revoke Share

Revoke an active share link.

**Endpoint:** `DELETE /files/{file_id}/shares/{share_id}`

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Share link revoked successfully"
}
```

## File Versions

### Upload New Version

Create a new version of an existing file.

**Endpoint:** `POST /files/{file_id}/versions`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file`: New file content
- `change_description`: Description of changes

**Response (201 Created):**

```json
{
  "status": "success",
  "data": {
    "version_id": "version_456789123",
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "version_number": 2,
    "file_size": 2150400,
    "checksum": "sha256:b776a47920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae4",
    "change_description": "Added missing diagrams and corrected typos",
    "changed_by": "user_456",
    "created_at": "2025-01-27T11:30:00Z"
  },
  "message": "New file version created successfully"
}
```

### List File Versions

Get version history for a file.

**Endpoint:** `GET /files/{file_id}/versions`

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "versions": [
      {
        "version_id": "version_456789123",
        "version_number": 2,
        "file_size": 2150400,
        "checksum": "sha256:b776a47920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae4",
        "change_description": "Added missing diagrams and corrected typos",
        "changed_by": "user_456",
        "created_at": "2025-01-27T11:30:00Z"
      },
      {
        "version_id": "version_123456789",
        "version_number": 1,
        "file_size": 2048576,
        "checksum": "sha256:a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
        "change_description": "Initial version",
        "changed_by": "user_456",
        "created_at": "2025-01-27T10:30:00Z"
      }
    ],
    "total_versions": 2,
    "current_version": 2
  }
}
```

### Rollback to Version

Rollback to a previous version of a file.

**Endpoint:** `POST /files/{file_id}/versions/{version_number}/rollback`

**Request Body:**

```json
{
  "change_description": "Rollback due to errors in version 2"
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "version_id": "version_789456123",
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "version_number": 3,
    "rollback_from_version": 1,
    "change_description": "Rollback due to errors in version 2",
    "created_at": "2025-01-27T12:00:00Z"
  },
  "message": "File rolled back successfully"
}
```

## Storage Management

### Get Storage Usage

Retrieve organization storage usage statistics.

**Endpoint:** `GET /storage/usage`

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "organization_id": "org_123",
    "total_quota": 21474836480,
    "used_storage": 5368709120,
    "available_storage": 16106127360,
    "used_percentage": 25.0,
    "file_count": 1247,
    "max_files": 50000,
    "usage_by_category": {
      "educational_content": {
        "file_count": 425,
        "total_size": 2147483648,
        "percentage": 40.0
      },
      "student_submission": {
        "file_count": 567,
        "total_size": 1073741824,
        "percentage": 20.0
      },
      "media_resource": {
        "file_count": 123,
        "total_size": 1610612736,
        "percentage": 30.0
      },
      "temporary": {
        "file_count": 89,
        "total_size": 268435456,
        "percentage": 5.0
      },
      "other": {
        "file_count": 43,
        "total_size": 268435456,
        "percentage": 5.0
      }
    },
    "warning_threshold": 80,
    "critical_threshold": 95,
    "is_warning_threshold_reached": false,
    "is_critical_threshold_reached": false,
    "last_calculated_at": "2025-01-27T10:00:00Z"
  }
}
```

### Get Usage Analytics

Retrieve detailed usage analytics and trends.

**Endpoint:** `GET /storage/analytics`

**Query Parameters:**
- `days`: Number of days to analyze (default: 30)
- `include_trends`: Include trend analysis (default: true)

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "period": {
      "start_date": "2024-12-28T00:00:00Z",
      "end_date": "2025-01-27T00:00:00Z",
      "days": 30
    },
    "summary": {
      "total_uploads": 342,
      "total_downloads": 1567,
      "total_size_uploaded": 1073741824,
      "average_file_size": 3145728,
      "most_active_day": "2025-01-15",
      "peak_upload_hour": 14
    },
    "trends": {
      "daily_uploads": [
        {"date": "2025-01-26", "uploads": 15, "size": 47185920},
        {"date": "2025-01-25", "uploads": 12, "size": 37748736}
      ],
      "category_growth": {
        "educational_content": 25.5,
        "student_submission": 15.2,
        "media_resource": -5.3
      },
      "storage_growth_rate": 12.8
    },
    "predictions": {
      "estimated_monthly_growth": 15.2,
      "projected_quota_exhaustion": "2025-08-15",
      "recommended_quota_increase": 5368709120
    },
    "recommendations": [
      "Consider archiving files older than 2 years",
      "Optimize image files to save 15% storage space",
      "Set up automated cleanup for temporary files"
    ]
  }
}
```

## Administrative Operations

### Update Storage Quota

Update organization storage quota (admin only).

**Endpoint:** `PATCH /admin/organizations/{org_id}/quota`

**Request Body:**

```json
{
  "total_quota": 53687091200,
  "max_files": 100000,
  "max_file_size_mb": 200,
  "warning_threshold": 85,
  "critical_threshold": 95
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "organization_id": "org_123",
    "total_quota": 53687091200,
    "max_files": 100000,
    "max_file_size_mb": 200,
    "warning_threshold": 85,
    "critical_threshold": 95,
    "updated_at": "2025-01-27T12:00:00Z"
  },
  "message": "Storage quota updated successfully"
}
```

### Bulk File Operations

Perform operations on multiple files (admin only).

**Endpoint:** `POST /admin/files/bulk`

**Request Body:**

```json
{
  "action": "update_category",
  "file_ids": [
    "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "f47ac10b-58cc-4372-a567-0e02b2c3d480"
  ],
  "parameters": {
    "category": "archived_content",
    "retention_days": 1825
  }
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "operation_id": "bulk_op_123456",
    "action": "update_category",
    "total_files": 2,
    "successful_operations": 2,
    "failed_operations": 0,
    "results": [
      {
        "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "status": "success"
      },
      {
        "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d480",
        "status": "success"
      }
    ]
  },
  "message": "Bulk operation completed successfully"
}
```

## WebSocket Events

For real-time updates, connect to the WebSocket endpoint:

**WebSocket URL:** `wss://api.toolboxai.com/ws/storage`

### Event Types

**Upload Progress:**
```json
{
  "event": "upload_progress",
  "data": {
    "upload_id": "upload_123456789",
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "progress_percentage": 45.2,
    "bytes_uploaded": 47185920,
    "total_bytes": 104357600,
    "estimated_time_remaining": 25
  }
}
```

**Virus Scan Complete:**
```json
{
  "event": "virus_scan_complete",
  "data": {
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "is_clean": true,
    "scan_duration_ms": 1250,
    "status": "available"
  }
}
```

**Processing Complete:**
```json
{
  "event": "processing_complete",
  "data": {
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "available",
    "cdn_url": "https://cdn.toolboxai.com/files/f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "thumbnail_url": "https://cdn.toolboxai.com/thumbs/f47ac10b-58cc-4372-a567-0e02b2c3d479_300x300.webp",
    "processing_duration_ms": 5420
  }
}
```

**Quota Warning:**
```json
{
  "event": "quota_warning",
  "data": {
    "organization_id": "org_123",
    "used_percentage": 85.2,
    "threshold_type": "warning",
    "available_storage": 1610612736,
    "recommended_action": "cleanup_old_files"
  }
}
```

## File Categories

| Category | Description | Max Size | Allowed MIME Types |
|----------|-------------|----------|-------------------|
| `educational_content` | Course materials, textbooks | 100MB | PDF, DOC, DOCX, TXT, HTML |
| `student_submission` | Student assignments | 50MB | PDF, DOC, DOCX, TXT, Images |
| `assessment` | Quizzes, tests, rubrics | 25MB | PDF, JSON, CSV, DOC |
| `media_resource` | Images, videos, audio | 500MB | Images, Videos, Audio |
| `avatar` | Profile pictures | 10MB | JPEG, PNG, WebP |
| `administrative` | Administrative documents | 100MB | PDF, DOC, DOCX, XLS, XLSX |
| `temporary` | Temporary files | 1GB | Any |
| `report` | Generated reports | 50MB | PDF, CSV, XLS, XLSX |

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `STORAGE_001` | 400 | Invalid file format |
| `STORAGE_002` | 413 | File too large |
| `STORAGE_003` | 429 | Upload rate limit exceeded |
| `STORAGE_004` | 403 | Quota exceeded |
| `STORAGE_005` | 404 | File not found |
| `STORAGE_006` | 403 | Access denied |
| `STORAGE_007` | 410 | File deleted or expired |
| `STORAGE_008` | 423 | File quarantined (virus detected) |
| `STORAGE_009` | 422 | Virus scan failed |
| `STORAGE_010` | 400 | Invalid share configuration |
| `STORAGE_011` | 410 | Share link expired |
| `STORAGE_012` | 429 | Download limit exceeded |
| `STORAGE_013` | 409 | File already exists |
| `STORAGE_014` | 422 | Processing failed |
| `STORAGE_015` | 503 | Storage service unavailable |

### Error Response Format

```json
{
  "status": "error",
  "error": {
    "code": "STORAGE_002",
    "message": "File size exceeds maximum allowed size",
    "details": {
      "file_size": 104857600,
      "max_allowed_size": 52428800,
      "category": "educational_content"
    }
  },
  "request_id": "req_123456789"
}
```

## SDKs and Examples

### Python SDK

```python
from toolboxai_storage import StorageClient

client = StorageClient(
    api_key="your-api-key",
    base_url="https://api.toolboxai.com"
)

# Upload file
result = await client.upload_file(
    file_path="document.pdf",
    category="educational_content",
    title="Course Materials"
)

# Download file
download_url = await client.get_download_url(result.file_id)
```

### JavaScript SDK

```javascript
import { StorageClient } from '@toolboxai/storage-js';

const client = new StorageClient({
  apiKey: 'your-api-key',
  baseURL: 'https://api.toolboxai.com'
});

// Upload with progress
const result = await client.uploadFile(file, {
  category: 'educational_content',
  title: 'Course Materials',
  onProgress: (progress) => {
    console.log(`Upload progress: ${progress.percentage}%`);
  }
});
```

For complete examples and advanced usage, see the [User Guide](../02-guides/STORAGE_USER_GUIDE.md) and [Implementation Guide](../04-implementation/SUPABASE_STORAGE.md).