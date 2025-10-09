# Authentication Guide

## Overview

The ToolBoxAI API uses JWT (JSON Web Tokens) for authentication with role-based access control (RBAC). This guide covers all authentication flows, security features, and best practices.

## Authentication Endpoints

### Login
```http
POST /api/v1/auth/login
```

Authenticate using username/email and password to receive a JWT token.

#### Request Body
```json
{
  "email": "teacher@school.edu",
  "password": "SecurePass123!"
}
```

#### Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "role": "teacher",
  "user": {
    "id": "123",
    "username": "jane_smith",
    "email": "teacher@school.edu",
    "displayName": "Jane Smith",
    "role": "teacher"
  }
}
```

### Token Refresh
```http
POST /api/v1/auth/refresh
Authorization: Bearer <current_token>
```

Refresh an existing token before it expires.

#### Response
```json
{
  "access_token": "{{ACCESS_TOKEN}}",
  "token_type": "bearer",
  "expires_in": 1800,
  "role": "teacher"
}
```

### Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

Invalidate the current token (client-side logout).

#### Response
```json
{
  "message": "Successfully logged out"
}
```

## User Roles

### Admin
- **Permissions**: Full system access, user management, system configuration
- **Access**: All endpoints
- **Rate Limit**: 10,000 requests/minute

### Teacher
- **Permissions**: Content creation, class management, student progress
- **Access**: Most endpoints except admin functions
- **Rate Limit**: 5,000 requests/minute

### Student
- **Permissions**: View content, submit assignments, track progress
- **Access**: Limited to read operations and submissions
- **Rate Limit**: 1,000 requests/minute

## Demo Accounts

For testing and development:

```json
{
  "admin": {
    "email": "admin@toolboxai.com",
    "password": "Admin123!",
    "role": "admin"
  },
  "teacher": {
    "email": "jane.smith@school.edu",
    "password": "Teacher123!",
    "role": "teacher"
  },
  "student": {
    "email": "alex.johnson@student.edu",
    "password": "Student123!",
    "role": "student"
  }
}
```

## JWT Token Structure

### Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### Payload
```json
{
  "sub": "username",
  "role": "teacher",
  "user_id": 123,
  "exp": 1642771200,
  "iat": 1642769400
}
```

### Token Expiration
- **Access Token**: 30 minutes (configurable)
- **Refresh Window**: 7 days before requiring re-authentication
- **Security**: Tokens are signed with HS256 algorithm

## Using Authentication

### Include Token in Requests
```bash
curl -H "Authorization: Bearer {{ACCESS_TOKEN}}" \
     https://api.toolboxai.com/api/v1/classes
```

### JavaScript Example
```javascript
// Store token after login
const token = loginResponse.access_token;
localStorage.setItem('auth_token', token);

// Use token in API requests
const response = await fetch('/api/v1/classes', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

### Python Example
```python
import requests

# Login and get token
login_response = requests.post('http://localhost:8009/api/v1/auth/login', json={
    'email': 'teacher@school.edu',
    'password': 'Teacher123!'
})
token = login_response.json()['access_token']

# Use token for authenticated requests
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:8009/api/v1/classes', headers=headers)
```

## Role-Based Access Control

### Endpoint Protection
Different endpoints require different role levels:

```python
# Admin only
@require_role("admin")
async def admin_function():
    pass

# Teacher or Admin
@require_any_role(["teacher", "admin"])
async def teacher_function():
    pass

# Any authenticated user
@require_authentication
async def authenticated_function():
    pass
```

### Permission Matrix

| Endpoint Category | Student | Teacher | Admin |
|------------------|---------|---------|-------|
| Authentication | ✅ | ✅ | ✅ |
| Content Viewing | ✅ | ✅ | ✅ |
| Content Creation | ❌ | ✅ | ✅ |
| Class Management | ❌ | ✅ | ✅ |
| User Management | ❌ | ❌ | ✅ |
| System Admin | ❌ | ❌ | ✅ |
| Analytics (Own) | ✅ | ✅ | ✅ |
| Analytics (All) | ❌ | ❌ | ✅ |

## Security Features

### Rate Limiting
- **Per IP**: 100 requests/minute (unauthenticated)
- **Per User**: Based on role (see above)
- **Burst Protection**: Temporary lockout for abuse

### Token Security
- **Secure Storage**: Store tokens securely (not in localStorage for production)
- **HTTPS Only**: All authentication must use HTTPS in production
- **Token Validation**: Tokens are validated on every request

### Password Requirements
- **Minimum Length**: 8 characters
- **Complexity**: Must include uppercase, lowercase, number, and special character
- **Examples**: `SecurePass123!`, `MyPassword1@`, `StrongKey789#`

## Real-time Authentication

### Pusher Channel Authentication
For real-time features using Pusher Channels:

```http
POST /api/v1/pusher/auth
Authorization: Bearer <token>
Content-Type: application/x-www-form-urlencoded

socket_id=123.456&channel_name=private-dashboard-updates
```

### WebSocket Authentication
For WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8009/ws/content');
ws.onopen = function() {
  // Send auth message
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'Bearer ' + authToken
  }));
};
```

## Error Codes

### Authentication Errors

| Code | Status | Description | Solution |
|------|--------|-------------|----------|
| `INVALID_CREDENTIALS` | 401 | Wrong username/password | Check credentials |
| `TOKEN_EXPIRED` | 401 | JWT token has expired | Refresh token |
| `INVALID_TOKEN` | 401 | Malformed or invalid token | Re-authenticate |
| `INSUFFICIENT_PERMISSIONS` | 403 | Role lacks required permissions | Check user role |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Wait and retry |

### Example Error Response
```json
{
  "success": false,
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "JWT token has expired",
    "details": {
      "expired_at": "2025-01-21T10:00:00Z",
      "current_time": "2025-01-21T10:30:00Z"
    }
  },
  "metadata": {
    "timestamp": "2025-01-21T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

## Best Practices

### Token Management
1. **Store Securely**: Use secure storage mechanisms
2. **Refresh Proactively**: Refresh tokens before expiration
3. **Handle Expiration**: Implement automatic re-authentication
4. **Logout Cleanup**: Clear tokens on logout

### Security Considerations
1. **HTTPS Only**: Never send tokens over HTTP
2. **Environment Separation**: Use different secrets for dev/staging/prod
3. **Token Rotation**: Implement regular token refresh
4. **Audit Logging**: Monitor authentication events

### Development Tips
1. **Use Demo Accounts**: Pre-configured accounts for testing
2. **Check Token Validity**: Validate tokens before API calls
3. **Handle Errors Gracefully**: Implement proper error handling
4. **Test All Roles**: Ensure proper access control

## Integration Examples

### React Hook
```javascript
import { useState, useEffect } from 'react';

function useAuth() {
  const [token, setToken] = useState(localStorage.getItem('auth_token'));
  const [user, setUser] = useState(null);

  const login = async (email, password) => {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();
    if (data.access_token) {
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('auth_token', data.access_token);
    }
    return data;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('auth_token');
  };

  return { token, user, login, logout };
}
```

### Python Client
```python
class ToolBoxAIClient:
    def __init__(self, base_url="http://localhost:8009"):
        self.base_url = base_url
        self.token = None

    def login(self, email, password):
        response = requests.post(f"{self.base_url}/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            return data
        raise Exception("Login failed")

    def authenticated_request(self, method, endpoint, **kwargs):
        headers = kwargs.get('headers', {})
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        kwargs['headers'] = headers

        return requests.request(method, f"{self.base_url}{endpoint}", **kwargs)
```

---

**Security Note**: Always use HTTPS in production and follow security best practices for token storage and transmission.