# API Authentication

All ToolboxAI-Solutions API endpoints require authentication using an API key or bearer token.

## Authentication Methods

### 1. API Key
Obtain your API key from the admin dashboard. Include it in the `x-api-key` header:
```http
GET /api/users
x-api-key: YOUR_API_KEY
```

### 2. Bearer Token (OAuth2)
Authenticate using OAuth2 and include the token in the `Authorization` header:
```http
GET /api/data
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Example Request
```http
GET /api/users/123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

## Token Expiry
Tokens expire after a set period. Refresh tokens as needed using the `/api/auth/refresh` endpoint.

## Error Codes
- `401 Unauthorized`: Invalid or missing token/key
- `403 Forbidden`: Insufficient permissions
