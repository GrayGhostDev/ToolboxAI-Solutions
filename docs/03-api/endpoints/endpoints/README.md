---
title: API Endpoints Reference
description: Complete reference for all ToolboxAI Solutions API endpoints
version: 2.0.0
last_updated: 2025-09-14
---

# API Endpoints Reference

This document provides a comprehensive reference for all API endpoints in ToolboxAI Solutions.

## Base URLs

- **Production**: `https://api.toolboxai.com/v2`
- **Staging**: `https://staging-api.toolboxai.com/v2`
- **Development**: `http://localhost:8008/v2`

## Authentication

All API endpoints require authentication unless otherwise specified. See [Authentication Guide](authentication.md) for details.

## Rate Limiting

- **Standard Users**: 1000 requests per hour
- **Premium Users**: 5000 requests per hour
- **Enterprise**: 50000 requests per hour

## Response Format

All API responses follow this format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2025-09-14T10:30:00Z",
  "request_id": "req_123456789"
}
```

## Error Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": { ... }
  },
  "timestamp": "2025-09-14T10:30:00Z",
  "request_id": "req_123456789"
}
```

## Endpoint Categories

### 🔐 Authentication & Authorization
- [Login & Registration](authentication.md)
- [Token Management](tokens.md)
- [User Roles & Permissions](permissions.md)

### 👥 User Management
- [User CRUD Operations](users.md)
- [Profile Management](profiles.md)
- [User Analytics](user-analytics.md)

### 📚 Educational Content
- [Lessons](lessons.md)
- [Quizzes & Assessments](assessments.md)
- [Content Generation](content-generation.md)

### 🎮 Roblox Integration
- [Environment Generation](environments.md)
- [Game Management](games.md)
- [Plugin Communication](plugins.md)

### 📊 Analytics & Reporting
- [Progress Tracking](progress.md)
- [Performance Metrics](metrics.md)
- [Custom Reports](reports.md)

### 🏫 School & Class Management
- [Schools](schools.md)
- [Classes](classes.md)
- [Enrollments](enrollments.md)

### 💬 Communication
- [Messages](messages.md)
- [Notifications](notifications.md)
- [WebSocket Events](websocket.md)

### ⚙️ System & Administration
- [System Health](health.md)
- [Configuration](configuration.md)
- [Audit Logs](audit.md)

## Quick Reference

### Most Common Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health check |
| `POST` | `/auth/login` | User authentication |
| `GET` | `/users/me` | Current user profile |
| `POST` | `/lessons` | Create new lesson |
| `GET` | `/lessons/{id}` | Get lesson details |
| `POST` | `/lessons/{id}/generate` | Generate 3D environment |
| `GET` | `/progress` | User progress data |
| `GET` | `/analytics/overview` | Analytics overview |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws` | Main WebSocket connection |
| `/ws/notifications` | Real-time notifications |
| `/ws/progress` | Live progress updates |
| `/ws/analytics` | Real-time analytics |

## SDKs and Libraries

- [JavaScript/TypeScript SDK](../../11-sdks/javascript-sdk.md)
- [Python SDK](../../11-sdks/python-sdk.md)
- [Roblox Lua SDK](../../11-sdks/roblox-lua-sdk.md)

## Examples

### cURL Examples

```bash
# Health check
curl -X GET https://api.toolboxai.com/v2/health

# Login
curl -X POST https://api.toolboxai.com/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Get user profile
curl -X GET https://api.toolboxai.com/v2/users/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### JavaScript Examples

```javascript
// Using fetch
const response = await fetch('/api/v2/lessons', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'Math Lesson',
    content: 'Algebra basics',
    subject: 'Mathematics',
    grade_level: 8
  })
});

const data = await response.json();
```

### Python Examples

```python
import requests

# Login
response = requests.post('https://api.toolboxai.com/v2/auth/login', json={
    'email': 'user@example.com',
    'password': 'password123'
})

token = response.json()['data']['access_token']

# Create lesson
headers = {'Authorization': f'Bearer {token}'}
lesson_data = {
    'title': 'Science Lesson',
    'content': 'Physics fundamentals',
    'subject': 'Science',
    'grade_level': 10
}

response = requests.post(
    'https://api.toolboxai.com/v2/lessons',
    json=lesson_data,
    headers=headers
)
```

## Testing

### Postman Collection

Download our [Postman Collection](https://api.toolboxai.com/postman/collection.json) for easy API testing.

### Interactive Documentation

Visit our [Interactive API Explorer](https://api.toolboxai.com/docs) for live testing.

## Support

- 📧 **API Support**: api-support@toolboxai.com
- 💬 **Live Chat**: Available in dashboard
- 📚 **Documentation**: [Full documentation](https://docs.toolboxai.com)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/toolboxai/solutions/issues)

---

**Last Updated**: 2025-09-14
**API Version**: 2.0.0
**Next Review**: 2025-10-14
