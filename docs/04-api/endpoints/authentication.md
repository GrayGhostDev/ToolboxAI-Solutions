# Authentication Endpoints

## Overview

The ToolBoxAI platform uses JWT (JSON Web Tokens) for authentication with role-based access control. The platform supports multiple user roles: student, teacher, admin, and parent.

## Base URL
```
http://127.0.0.1:8008
```

## Authentication Endpoints

### POST /auth/login
Authenticate user and return JWT access token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "string",
    "username": "string",
    "email": "string",
    "role": "student|teacher|admin|parent",
    "grade_level": 7
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8008/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student@example.com",
    "password": "secure_password"
  }'
```

**JavaScript Example:**
```javascript
const response = await fetch('http://127.0.0.1:8008/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'student@example.com',
    password: 'secure_password'
  })
});

const data = await response.json();
```

**Python Example:**
```python
import requests

response = requests.post(
    'http://127.0.0.1:8008/auth/login',
    json={
        'username': 'student@example.com',
        'password': 'secure_password'
    }
)

data = response.json()
```

### POST /auth/refresh
Refresh JWT access token using refresh token.

**Request Body (Option 1 - Body):**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Request Headers (Option 2 - Header):**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8008/auth/refresh" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN"
```

### POST /auth/token
Alternative token creation endpoint with authentication.

**Request/Response:** Same as `/auth/login`

### POST /auth/verify
Verify JWT token validity.

**Request Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response:**
```json
{
  "valid": true,
  "user": {
    "id": "string",
    "username": "string",
    "role": "student|teacher|admin|parent",
    "expires_at": "2024-01-01T12:00:00Z"
  }
}
```

## Authentication Flow

### 1. Initial Login
1. User provides username/password to `/auth/login`
2. Server validates credentials
3. Server returns access token + refresh token
4. Client stores tokens securely

### 2. Making Authenticated Requests
Include the access token in the Authorization header:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 3. Token Refresh
1. When access token expires (typically 1 hour)
2. Use refresh token with `/auth/refresh`
3. Receive new access token
4. Continue making requests with new token

### 4. Token Verification
Verify token validity with `/auth/verify` before making critical requests.

## Role-Based Access Control (RBAC)

### User Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| `student` | Student users | View own content, submit assessments, access lessons |
| `teacher` | Teacher users | Manage classes, create content, view student progress |
| `admin` | Administrator users | Full system access, user management, system configuration |
| `parent` | Parent/guardian users | View child's progress, receive notifications |

### Protected Endpoints
Most endpoints require authentication. Common authorization requirements:

- **Student Access:** Most read operations for own data
- **Teacher Access:** Class management, content creation, student progress
- **Admin Access:** User management, system administration, all data access
- **Parent Access:** Child progress viewing, notifications

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials",
  "error_code": "INVALID_TOKEN"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions",
  "error_code": "INSUFFICIENT_PERMISSIONS",
  "required_role": "teacher"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Security Considerations

### Token Security
- Store tokens securely (e.g., httpOnly cookies, secure storage)
- Never expose tokens in URLs or logs
- Implement proper token rotation
- Use HTTPS in production

### Password Requirements
- Minimum 8 characters
- Mix of letters, numbers, and symbols
- No common passwords
- Regular password rotation recommended

### Rate Limiting
Authentication endpoints are rate-limited:
- `/auth/login`: 5 attempts per minute per IP
- `/auth/refresh`: 10 requests per minute per user
- `/auth/verify`: 30 requests per minute per user

## Integration Examples

### React/TypeScript
```typescript
interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  user: {
    id: string;
    username: string;
    role: 'student' | 'teacher' | 'admin' | 'parent';
  };
}

class AuthService {
  private baseUrl = 'http://127.0.0.1:8008';

  async login(username: string, password: string): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error('Authentication failed');
    }

    return response.json();
  }

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${refreshToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    return response.json();
  }
}
```

### Python SDK
```python
import requests
from typing import Optional, Dict, Any

class ToolBoxAIAuth:
    def __init__(self, base_url: str = "http://127.0.0.1:8008"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user and store tokens."""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()

        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

        return data

    def refresh(self) -> Dict[str, Any]:
        """Refresh access token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        response = requests.post(
            f"{self.base_url}/auth/refresh",
            headers={"Authorization": f"Bearer {self.refresh_token}"}
        )
        response.raise_for_status()

        data = response.json()
        self.access_token = data["access_token"]

        return data

    def get_headers(self) -> Dict[str, str]:
        """Get headers with current access token."""
        if not self.access_token:
            raise ValueError("Not authenticated")

        return {"Authorization": f"Bearer {self.access_token}"}
```

## Testing Authentication

### Test Credentials
For development/testing environments:

```json
{
  "students": [
    {"username": "student1@test.com", "password": "student123", "role": "student"},
    {"username": "student2@test.com", "password": "student123", "role": "student"}
  ],
  "teachers": [
    {"username": "teacher1@test.com", "password": "teacher123", "role": "teacher"}
  ],
  "admins": [
    {"username": "admin@test.com", "password": "admin123", "role": "admin"}
  ]
}
```

### Postman Collection
A Postman collection is available at `/docs/03-api/examples/postman/authentication.json` with pre-configured requests for all authentication endpoints.