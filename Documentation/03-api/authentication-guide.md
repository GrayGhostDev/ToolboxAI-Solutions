# Authentication Guide

## Overview

The ToolBoxAI Educational Platform uses JWT (JSON Web Token) based authentication for secure access to all API endpoints. This guide provides comprehensive information about authentication, including test credentials and implementation details.

## Test User Credentials

The following test users are available in the development and staging environments:

| Username | Password | Role | Email | Description |
|----------|----------|------|-------|-------------|
| `john_teacher` | `Teacher123!` | Teacher | john.smith@school.edu | Primary teacher account with full class management |
| `testuser` | `password123` | Teacher | test@example.com | Basic test teacher account |
| `alice_student` | `Student123!` | Student | alice@test.edu | Student account for testing |
| `charlie_student` | `Student123!` | Student | charlie@test.edu | Another student account |
| `admin_user` | `Admin123!` | Admin | admin@school.edu | Administrator with full system access |
| `parent_user` | `Parent123!` | Parent | parent@test.edu | Parent account for monitoring |

**Note:** The password hash for `testuser` is: `$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K`

## Authentication Flow

### 1. Login

To authenticate, send a POST request to the login endpoint:

```bash
POST http://localhost:8008/auth/login
Content-Type: application/json

{
  "username": "john_teacher",
  "password": "Teacher123!"
}
```

**Successful Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user-uuid",
    "username": "john_teacher",
    "email": "john.smith@school.edu",
    "role": "teacher",
    "first_name": "John",
    "last_name": "Smith"
  }
}
```

### 2. Using the Token

Include the JWT token in the Authorization header for all subsequent requests:

```bash
curl -X GET http://localhost:8008/dashboard/teacher \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. Token Expiration

- **Access Token Lifetime:** 30 minutes
- **Refresh Token Lifetime:** 7 days (if implemented)
- **Token Renewal:** Request a new token before expiration

## API Endpoints

### Authentication Endpoints

| Endpoint | Method | Description | Authentication Required |
|----------|--------|-------------|------------------------|
| `/auth/login` | POST | User login | No |
| `/auth/logout` | POST | User logout | Yes |
| `/auth/refresh` | POST | Refresh access token | Yes (Refresh Token) |
| `/auth/verify` | GET | Verify current token | Yes |
| `/auth/profile` | GET | Get user profile | Yes |

### Protected Endpoints

All other API endpoints require authentication:

- **Dashboard:** `/dashboard/*`
- **Content Generation:** `/generate_content`
- **Quiz Management:** `/quiz/*`
- **Analytics:** `/analytics/*`
- **WebSocket:** `/ws` (token in query parameter)

## Role-Based Access Control (RBAC)

The platform implements role-based access control with the following roles:

### Teacher Role
- Create and manage classes
- Generate educational content
- Create quizzes and assessments
- View student progress
- Access all teaching resources

### Student Role
- Access assigned content
- Take quizzes and assessments
- View own progress
- Participate in learning activities
- Access student dashboard

### Admin Role
- Full system access
- User management
- System configuration
- Analytics and reporting
- Content moderation

### Parent Role
- View children's progress
- Access reports
- Communicate with teachers
- Monitor learning activities

## Code Examples

### Python (requests)
```python
import requests

# Login
response = requests.post(
    "http://localhost:8008/auth/login",
    json={"username": "john_teacher", "password": "Teacher123!"}
)
token = response.json()["access_token"]

# Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}
dashboard = requests.get(
    "http://localhost:8008/dashboard/teacher",
    headers=headers
)
print(dashboard.json())
```

### JavaScript (fetch)
```javascript
// Login
const loginResponse = await fetch('http://localhost:8008/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'john_teacher',
    password: 'Teacher123!'
  })
});
const { access_token } = await loginResponse.json();

// Use token for authenticated requests
const dashboardResponse = await fetch('http://localhost:8008/dashboard/teacher', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
const dashboardData = await dashboardResponse.json();
```

### cURL
```bash
# Login and save token
TOKEN=$(curl -s -X POST http://localhost:8008/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john_teacher","password":"Teacher123!"}' \
  | jq -r '.access_token')

# Use token for authenticated requests
curl -X GET http://localhost:8008/dashboard/teacher \
  -H "Authorization: Bearer $TOKEN"
```

## WebSocket Authentication

For WebSocket connections, pass the token as a query parameter:

```javascript
const ws = new WebSocket(`ws://localhost:9876/ws?token=${access_token}`);
```

## Security Best Practices

1. **Never store passwords in plain text** - Always use secure hashing (bcrypt)
2. **Use HTTPS in production** - Encrypt all traffic
3. **Implement rate limiting** - Prevent brute force attacks (100 requests/minute)
4. **Rotate secrets regularly** - Change JWT secret keys periodically
5. **Implement token refresh** - Don't use long-lived access tokens
6. **Validate all inputs** - Prevent injection attacks
7. **Log authentication events** - Monitor for suspicious activity

## Troubleshooting

### Common Issues

#### "Invalid credentials" Error
- Verify username and password are correct
- Check if user account is active
- Ensure password meets requirements

#### "Token expired" Error
- Request a new token via `/auth/login`
- Implement automatic token refresh

#### "Unauthorized" Error
- Ensure token is included in Authorization header
- Check token format: `Bearer <token>`
- Verify token hasn't expired

#### CORS Issues
- Ensure frontend origin is allowed
- Check CORS configuration in FastAPI

### Debug Mode

Enable debug logging for authentication:

```python
import logging
logging.getLogger("auth").setLevel(logging.DEBUG)
```

## Database Schema

User authentication data is stored in the `users` table:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Environment Variables

Configure authentication settings in `.env`:

```env
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Database
DATABASE_URL=postgresql://user:password@localhost/educational_platform

# Security
BCRYPT_ROUNDS=12
RATE_LIMIT=100  # requests per minute
```

## Support

For authentication issues or questions:
1. Check this documentation
2. Review server logs: `tail -f logs/auth.log`
3. Test with provided credentials
4. Verify database connectivity

---

*Last Updated: 2025-09-08*
*Version: 1.0.0*