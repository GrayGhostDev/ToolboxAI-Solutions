# ToolboxAI API - Getting Started Guide
**Version**: 1.0.0
**Last Updated**: 2025-10-02

---

## 📚 Table of Contents
1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [API Structure](#api-structure)
4. [Making Your First Request](#making-your-first-request)
5. [Common Patterns](#common-patterns)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)

---

## Introduction

The ToolboxAI API is a comprehensive RESTful API built with FastAPI, providing access to educational platform features including:

- **Storage & Media**: File uploads, media serving, streaming
- **Multi-Tenancy**: Tenant management, settings, billing
- **Content Management**: Versioning, workflow, tagging
- **Analytics**: Reports, exports, dashboards
- **User Management**: Preferences, notifications

### Base URL
```
Production: https://api.toolboxai.com/api/v1
Development: http://localhost:8019/api/v1
```

### API Documentation
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI Spec**: `/openapi.json`

---

## Authentication

All API requests require authentication using JWT tokens.

### Getting a Token

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using the Token

Include the token in the Authorization header for all requests:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Refresh

```bash
POST /api/v1/auth/refresh
Authorization: Bearer <your_refresh_token>
```

---

## API Structure

### Endpoint Naming Convention

```
/api/v1/{resource}/{resource_id?}/{action?}
```

Examples:
- `GET /api/v1/users` - List users
- `GET /api/v1/users/{user_id}` - Get specific user
- `POST /api/v1/users/{user_id}/preferences` - Update user preferences

### HTTP Methods

- `GET` - Retrieve resources
- `POST` - Create new resources
- `PATCH` - Partial update of resources
- `PUT` - Full update or replace
- `DELETE` - Remove resources

### Response Format

All responses follow a consistent JSON structure:

**Success Response:**
```json
{
  "id": "uuid",
  "field1": "value1",
  "field2": "value2",
  "created_at": "2025-10-02T10:00:00Z"
}
```

**List Response:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

**Error Response:**
```json
{
  "detail": "Error message",
  "status_code": 400,
  "error_code": "VALIDATION_ERROR"
}
```

---

## Making Your First Request

### Example: Upload a File

```python
import requests

# Setup
BASE_URL = "http://localhost:8019/api/v1"
TOKEN = "your_access_token"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# Upload file
with open("document.pdf", "rb") as f:
    files = {"file": ("document.pdf", f, "application/pdf")}
    response = requests.post(
        f"{BASE_URL}/uploads/file",
        files=files,
        headers=headers
    )

print(response.json())
```

**Response:**
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "file_size": 1024000,
  "content_type": "application/pdf",
  "status": "completed",
  "created_at": "2025-10-02T10:00:00Z"
}
```

### Example: Create a Dashboard

```python
import requests

dashboard_data = {
    "name": "Student Performance Dashboard",
    "description": "Real-time student metrics",
    "widgets": [
        {
            "id": "widget-1",
            "type": "chart",
            "title": "Average Scores",
            "data_source": "student_scores",
            "config": {"chart_type": "line"},
            "position": {"x": 0, "y": 0, "w": 6, "h": 4}
        }
    ],
    "layout": {"columns": 12, "row_height": 100},
    "is_public": False,
    "tags": ["students", "performance"]
}

response = requests.post(
    f"{BASE_URL}/analytics/dashboards",
    json=dashboard_data,
    headers=headers
)

print(response.json())
```

### Example: Update User Preferences

```python
preferences = {
    "category": "ui",
    "key": "theme",
    "value": "dark"
}

response = requests.patch(
    f"{BASE_URL}/users/preferences",
    json=preferences,
    headers=headers
)

print(response.json())
```

---

## Common Patterns

### Pagination

List endpoints support pagination:

```bash
GET /api/v1/users?limit=20&offset=0
```

**Parameters:**
- `limit` - Number of items per page (default: 20, max: 100)
- `offset` - Number of items to skip (default: 0)

**Response:**
```json
{
  "items": [...],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

### Filtering

Many endpoints support filtering:

```bash
GET /api/v1/users/notifications?status_filter=unread&type_filter=alert
```

### Sorting

Use `sort_by` and `sort_order` parameters:

```bash
GET /api/v1/analytics/reports?sort_by=created_at&sort_order=desc
```

### Bulk Operations

Some endpoints support bulk operations:

```python
# Bulk create notifications
bulk_data = {
    "user_ids": ["uuid1", "uuid2", "uuid3"],
    "type": "announcement",
    "priority": "high",
    "title": "Important Update",
    "message": "System maintenance scheduled",
    "channels": ["in_app", "email"]
}

response = requests.post(
    f"{BASE_URL}/users/notifications/bulk",
    json=bulk_data,
    headers=headers
)
```

### Background Jobs

Long-running operations return job IDs:

```python
# Start export
response = requests.post(
    f"{BASE_URL}/analytics/export/csv",
    json={"data_source": "student_progress"},
    headers=headers
)

export_id = response.json()["export_id"]

# Check status
status = requests.get(
    f"{BASE_URL}/analytics/export/{export_id}/status",
    headers=headers
)

# Download when complete
if status.json()["status"] == "completed":
    file = requests.get(
        f"{BASE_URL}/analytics/export/{export_id}/download",
        headers=headers
    )
```

---

## Error Handling

### HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created
- `202 Accepted` - Async operation started
- `204 No Content` - Success with no response body
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing/invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `413 Payload Too Large` - File/request too large
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
  "detail": "Validation error",
  "status_code": 422,
  "error_code": "VALIDATION_ERROR",
  "errors": [
    {
      "field": "name",
      "message": "Field is required"
    }
  ]
}
```

### Error Handling Example

```python
try:
    response = requests.post(
        f"{BASE_URL}/analytics/dashboards",
        json=dashboard_data,
        headers=headers
    )
    response.raise_for_status()

    dashboard = response.json()
    print(f"Dashboard created: {dashboard['id']}")

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("Authentication failed - refresh token")
    elif e.response.status_code == 422:
        errors = e.response.json().get("errors", [])
        print(f"Validation errors: {errors}")
    else:
        print(f"Error: {e.response.json()}")
```

---

## Rate Limiting

### Limits

- **Authenticated requests**: 1000 requests/hour
- **File uploads**: 100 uploads/hour
- **Bulk operations**: 10 requests/minute

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1633024800
```

### Handling Rate Limits

```python
response = requests.get(
    f"{BASE_URL}/users",
    headers=headers
)

if response.status_code == 429:
    reset_time = int(response.headers.get("X-RateLimit-Reset"))
    wait_seconds = reset_time - time.time()
    print(f"Rate limited. Retry in {wait_seconds} seconds")
    time.sleep(wait_seconds)
```

---

## Next Steps

- 📖 [API Reference Documentation](./API_REFERENCE.md)
- 🔒 [Authentication Guide](./API_AUTHENTICATION.md)
- 💾 [Storage API Guide](./API_STORAGE_GUIDE.md)
- 📊 [Analytics API Guide](./API_ANALYTICS_GUIDE.md)
- 👤 [User Management Guide](./API_USER_GUIDE.md)
- 🏢 [Multi-Tenancy Guide](./API_TENANT_GUIDE.md)

---

## Support

- **Documentation**: https://docs.toolboxai.com
- **API Status**: https://status.toolboxai.com
- **Support Email**: api-support@toolboxai.com
- **GitHub Issues**: https://github.com/toolboxai/api/issues
