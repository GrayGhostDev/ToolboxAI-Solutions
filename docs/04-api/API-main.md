# ToolBoxAI API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Authentication & Authorization](#authentication--authorization)
4. [API Endpoints](#api-endpoints)
5. [Request/Response Formats](#requestresponse-formats)
6. [Error Handling](#error-handling)
7. [Rate Limiting & Security](#rate-limiting--security)
8. [Docker Environment & Networking](#docker-environment--networking)
9. [Development vs Production](#development-vs-production)
10. [API Testing](#api-testing)
11. [OpenAPI Documentation](#openapi-documentation)

## Overview

The ToolBoxAI API is a comprehensive educational platform API built with FastAPI, designed to power Roblox-integrated learning environments. The API provides endpoints for content generation, user management, agent orchestration, realtime communication via Pusher, and educational analytics.

### Key Features

- **Modular Architecture**: Factory-pattern based FastAPI application
- **Multi-Role Authentication**: Support for admin, teacher, and student roles
- **AI Agent Integration**: Orchestrated content generation and educational assistance
- **Realtime Communication**: Pusher Channels for live updates and notifications
- **Educational Content**: STEM-focused curriculum with Roblox integration
- **Analytics & Reporting**: Comprehensive learning analytics and progress tracking
- **OAuth2 Support**: Enterprise-grade authentication with MFA capabilities
- **Container-Ready**: Full Docker support with service mesh architecture

### Base URL

- **Development**: `http://localhost:8009` or `http://127.0.0.1:8009`
- **Docker Development**: `http://fastapi-main:8009` (internal container communication)
- **Production**: As configured in deployment environment

## Architecture

The API follows a modern, modular architecture:

```
FastAPI Application (Port 8009)
├── Core Services
│   ├── Application Factory (apps/backend/core/app_factory.py)
│   ├── Configuration Management (apps/backend/core/config.py)
│   ├── Logging & Observability (apps/backend/core/logging.py)
│   └── Middleware Registry (apps/backend/core/middleware.py)
├── API Routes (/api/v1/*)
│   ├── Authentication & User Management
│   ├── Educational Content Generation
│   ├── Agent Orchestration
│   ├── Analytics & Reporting
│   └── Roblox Integration
├── Realtime Services
│   ├── Pusher Channels (primary)
│   └── WebSocket Endpoints (legacy)
├── Health & Monitoring
│   ├── System Health Checks
│   ├── Integration Status
│   └── Performance Metrics
└── Database Integration
    ├── PostgreSQL (primary data)
    ├── Redis (caching & sessions)
    └── Supabase (optional enhancement)
```

### Service Dependencies

- **PostgreSQL**: User data, content storage, analytics
- **Redis**: Session management, caching, rate limiting
- **Pusher**: Realtime notifications and updates
- **OpenAI/LLM APIs**: Content generation and AI features
- **Roblox APIs**: Game environment integration

## Authentication & Authorization

### JWT Token-Based Authentication

The API uses JWT (JSON Web Tokens) for stateless authentication with the following flow:

1. **Login**: `POST /auth/login` with credentials
2. **Token Receipt**: Access token (30 min) + Refresh token (7 days)
3. **Authenticated Requests**: Include `Authorization: Bearer <token>` header
4. **Token Refresh**: `POST /auth/refresh` to obtain new access token

### Authentication Endpoints

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "remember_me": true
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": 1,
      "email": "user@example.com",
      "role": "teacher",
      "full_name": "Jane Doe"
    }
  }
}
```

#### Token Refresh
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Token Verification
```http
POST /auth/token
Content-Type: application/json

{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Role-Based Access Control (RBAC)

The API supports three primary user roles:

- **Admin**: Full system access, user management, system configuration
- **Teacher**: Classroom management, content creation, student progress monitoring
- **Student**: Learning content access, progress tracking, gamification features

### Multi-Factor Authentication (MFA)

Enterprise MFA support is available through dedicated endpoints:

- `POST /api/v1/mfa/setup/init` - Initialize MFA setup
- `POST /api/v1/mfa/setup/confirm` - Confirm MFA configuration
- `POST /api/v1/mfa/verify` - Verify MFA token during login
- `GET /api/v1/mfa/status` - Check MFA enrollment status

### OAuth2 Integration

For enterprise integrations, OAuth2 endpoints are available:

- `GET /oauth/authorize` - OAuth authorization endpoint
- `POST /oauth/token` - OAuth token exchange
- `POST /oauth/register` - OAuth client registration
- `GET /.well-known/oauth-authorization-server` - OAuth discovery

## API Endpoints

### Authentication (`/auth/*`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/login` | User authentication | No |
| POST | `/auth/refresh` | Refresh access token | No |
| POST | `/auth/token` | Verify token validity | No |
| POST | `/auth/logout` | Invalidate session | Yes |

### User Management (`/api/v1/users/*`)

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/api/v1/users/me` | Get current user profile | Yes | Any |
| GET | `/api/v1/users/me/profile` | Get detailed profile | Yes | Any |
| PATCH | `/api/v1/users/me/profile` | Update user profile | Yes | Any |
| GET | `/api/v1/users/{user_id}` | Get user by ID | Yes | Admin |
| PUT | `/api/v1/users/{user_id}` | Update user | Yes | Admin |
| DELETE | `/api/v1/users/{user_id}` | Delete user | Yes | Admin |

### Content Generation (`/api/v1/content/*`)

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/api/v1/content/generate` | Generate educational content | Yes | Teacher/Admin |
| GET | `/content/{content_id}` | Retrieve generated content | Yes | Any |
| POST | `/api/v1/content/validate` | Validate content structure | Yes | Teacher/Admin |

### Agent Orchestration (`/api/v1/agents/*`)

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/api/v1/agents/execute` | Execute agent task | Yes | Teacher/Admin |
| GET | `/api/v1/agents/status` | Get agent system status | Yes | Any |
| POST | `/api/v1/agents/swarm/execute` | Execute multi-agent task | Yes | Admin |

### Pusher/Realtime (`/pusher/*`, `/realtime/*`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/pusher/auth` | Authenticate Pusher channel | Yes |
| POST | `/realtime/trigger` | Trigger realtime event | Yes |
| POST | `/pusher/webhook` | Pusher webhook handler | No* |
| GET | `/pusher/stats` | Get Pusher statistics | Yes |

*Webhook endpoints use signature validation

### Pusher Channel Events (`/api/v1/pusher/*`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/pusher/message` | Send channel message | Yes |
| POST | `/api/v1/pusher/subscribe` | Subscribe to channel | Yes |
| POST | `/api/v1/pusher/unsubscribe` | Unsubscribe from channel | Yes |
| GET | `/api/v1/pusher/user/channels` | Get user's channels | Yes |
| POST | `/api/v1/pusher/broadcast` | Broadcast to multiple channels | Yes |

### WebSocket Endpoints (Legacy) (`/ws/*`)

| Endpoint | Description | Auth Required |
|----------|-------------|---------------|
| `/ws/content` | Content generation updates | Yes |
| `/ws/roblox` | Roblox environment sync | Yes |
| `/ws/agent/{agent_id}` | Agent communication | Yes |
| `/ws/native` | Test echo endpoint | No |

### Health & Monitoring (`/health/*`, `/metrics`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Basic health check | No |
| GET | `/metrics` | Prometheus metrics | No |
| GET | `/health/integrations` | Integration status | Yes |
| GET | `/health/database` | Database health | Yes |
| GET | `/health/supabase` | Supabase connection status | Yes |
| GET | `/health/mcp` | MCP server status | Yes |

### Analytics & Reporting (`/api/v1/analytics/*`)

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/api/v1/analytics/dashboard` | Dashboard metrics | Yes | Teacher/Admin |
| POST | `/api/v1/analytics/predict` | Predictive analytics | Yes | Admin |
| GET | `/api/v1/analytics/trends/{metric}` | Trend analysis | Yes | Teacher/Admin |
| POST | `/api/v1/analytics/export` | Export analytics data | Yes | Admin |

### Roblox Integration (`/api/v1/roblox/*`)

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/api/v1/roblox/deploy/{content_id}` | Deploy content to Roblox | Yes | Teacher/Admin |
| GET | `/api/v1/roblox/download/{content_id}` | Download Roblox package | Yes | Any |
| POST | `/api/v1/roblox/sync` | Sync Roblox environment | Yes | Teacher/Admin |

### Administrative (`/api/v1/admin/*`)

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/api/v1/admin/users` | List all users | Yes | Admin |
| POST | `/api/v1/admin/users` | Create new user | Yes | Admin |
| GET | `/api/v1/admin/system/status` | System status overview | Yes | Admin |
| POST | `/api/v1/admin/maintenance` | Trigger maintenance tasks | Yes | Admin |

## Request/Response Formats

### Standard Response Format

All API responses follow a consistent structure:

```json
{
  "status": "success|error",
  "data": {
    // Response payload
  },
  "message": "Human-readable message",
  "metadata": {
    "timestamp": "2025-09-24T10:30:00Z",
    "request_id": "req_12345",
    "version": "1.0.0"
  }
}
```

### Content Generation Request Example

```http
POST /api/v1/content/generate
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "subject": "Mathematics",
  "grade_level": 8,
  "topic": "Quadratic Equations",
  "content_type": "interactive_lesson",
  "duration_minutes": 45,
  "learning_objectives": [
    "Understand quadratic equation structure",
    "Solve using factoring method",
    "Apply to real-world problems"
  ],
  "roblox_integration": {
    "environment": "math_classroom",
    "interactive_elements": true,
    "gamification": true
  }
}
```

### Content Generation Response Example

```json
{
  "status": "success",
  "data": {
    "content_id": "cont_67890",
    "title": "Interactive Quadratic Equations Lesson",
    "subject": "Mathematics",
    "grade_level": 8,
    "estimated_duration": 45,
    "content": {
      "lesson_plan": "...",
      "interactive_activities": [...],
      "assessment_questions": [...],
      "roblox_scripts": {
        "client_script": "...",
        "server_script": "...",
        "shared_modules": [...]
      }
    },
    "metadata": {
      "created_at": "2025-09-24T10:30:00Z",
      "generated_by": "gpt-4",
      "complexity_score": 7.2,
      "estimated_engagement": 8.5
    }
  },
  "message": "Content generated successfully",
  "metadata": {
    "processing_time_ms": 3420,
    "tokens_used": 2156,
    "cost_estimate": "$0.12"
  }
}
```

### Agent Execution Request Example

```http
POST /api/v1/agents/execute
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "agent_type": "content_generator",
  "task": {
    "action": "generate_lesson",
    "parameters": {
      "subject": "Science",
      "topic": "Photosynthesis",
      "grade_level": 6,
      "format": "interactive_experiment"
    }
  },
  "priority": "normal",
  "timeout_seconds": 300
}
```

### Pusher Authentication Request Example

```http
POST /pusher/auth
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "socket_id": "123456.789012",
  "channel_name": "private-user-1234"
}
```

## Error Handling

### Standard Error Response

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request data is invalid",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  },
  "metadata": {
    "timestamp": "2025-09-24T10:30:00Z",
    "request_id": "req_12345",
    "correlation_id": "corr_67890"
  }
}
```

### HTTP Status Codes

| Status Code | Description | When Used |
|-------------|-------------|-----------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Common Error Codes

| Error Code | Description | Resolution |
|------------|-------------|------------|
| `INVALID_TOKEN` | JWT token is invalid or expired | Re-authenticate or refresh token |
| `INSUFFICIENT_PERMISSIONS` | User lacks required role/permissions | Contact admin for access |
| `VALIDATION_ERROR` | Request data validation failed | Check request format and required fields |
| `RATE_LIMIT_EXCEEDED` | Too many requests in time window | Wait and retry with exponential backoff |
| `RESOURCE_NOT_FOUND` | Requested resource doesn't exist | Verify resource ID and permissions |
| `SERVICE_UNAVAILABLE` | External service is unavailable | Check service status and retry later |
| `CONTENT_GENERATION_FAILED` | AI content generation failed | Retry with different parameters |
| `AGENT_EXECUTION_TIMEOUT` | Agent task exceeded timeout | Increase timeout or optimize task |

## Rate Limiting & Security

### Rate Limiting

The API implements several levels of rate limiting:

- **Global Rate Limit**: 60 requests per minute per IP address
- **User Rate Limit**: 100 requests per minute per authenticated user
- **Content Generation**: 10 concurrent generations per user
- **WebSocket Connections**: 1000 concurrent connections per server

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1632412800
Retry-After: 30
```

### Security Headers

All API responses include security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

### CORS Configuration

The API is configured with environment-appropriate CORS policies:

**Development:**
```javascript
// Allowed origins
http://localhost:5179
http://127.0.0.1:5179
http://localhost:3000
```

**Production:**
```javascript
// Domain-based origins only
https://yourdomain.com
https://app.yourdomain.com
```

### Input Validation

All endpoints implement comprehensive input validation:

- **Request Size Limits**: 10MB for file uploads, 1MB for JSON payloads
- **Content Type Validation**: Strict content-type checking
- **SQL Injection Protection**: Parameterized queries and ORM usage
- **XSS Prevention**: Input sanitization and output encoding
- **CSRF Protection**: Token-based CSRF protection for state-changing operations

## Docker Environment & Networking

### Container Communication

In Docker development environments, services communicate using container names:

```yaml
# Internal container communication
VITE_API_BASE_URL: http://fastapi-main:8009/api/v1
DATABASE_URL: postgresql://user:pass@postgres:5432/db
REDIS_URL: redis://redis:6379/0
```

### Service Discovery

The Docker environment includes the following services:

| Service | Container Name | Internal Port | External Port | Purpose |
|---------|----------------|---------------|---------------|---------|
| FastAPI Backend | `toolboxai-fastapi` | 8009 | 8009 | Main API server |
| PostgreSQL | `toolboxai-postgres` | 5432 | 5434 | Primary database |
| Redis | `toolboxai-redis` | 6379 | 6381 | Cache and sessions |
| Dashboard Frontend | `toolboxai-dashboard-frontend` | 5179 | 5179 | React frontend |
| MCP Server | `toolboxai-mcp-server` | 9877 | 9877 | Model Context Protocol |
| Agent Coordinator | `toolboxai-agent-coordinator` | 8888 | 8888 | AI agent orchestration |

### Health Checks

All services implement Docker health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8009/health"]
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 60s
```

### Environment Variables

Key environment variables for Docker deployment:

```bash
# Database connections (use container names)
DATABASE_URL=postgresql://eduplatform:eduplatform2024@postgres:5432/educational_platform_dev
REDIS_URL=redis://redis:6379/0

# API configuration
HOST=0.0.0.0
PORT=8009
ENVIRONMENT=development

# External services
OPENAI_API_KEY=sk-...
PUSHER_APP_ID=123456
PUSHER_KEY=abcdef123456
PUSHER_SECRET=1234567890abcdef
PUSHER_CLUSTER=us2
```

## Development vs Production

### Development Environment

**Characteristics:**
- Debug mode enabled (`DEBUG=true`)
- Hot reload with file watching
- Permissive CORS policy
- Detailed error messages
- Local development URLs

**Configuration:**
```bash
# Development .env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
CORS_ORIGINS=["http://localhost:5179","http://127.0.0.1:5179"]
SKIP_AUTH=false  # Keep authentication active
```

**Access URLs:**
- API Base: `http://localhost:8009`
- Documentation: `http://localhost:8009/docs`
- Admin Interface: `http://localhost:5179`

### Production Environment

**Characteristics:**
- Performance optimized
- Security hardened
- Restricted CORS policy
- Minimal error exposure
- Production monitoring

**Configuration:**
```bash
# Production .env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=["https://yourdomain.com"]
COOKIE_SECURE=true
JWT_REQUIRE_HTTPS=true
```

**Security Enhancements:**
- HTTPS-only cookies
- Secure JWT handling
- Rate limiting enforcement
- Input validation strictness
- Error message sanitization

## API Testing

### Using curl

#### Authentication
```bash
# Login
curl -X POST http://localhost:8009/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo123"}'

# Store token for subsequent requests
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Authenticated request
curl -X GET http://localhost:8009/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

#### Content Generation
```bash
curl -X POST http://localhost:8009/api/v1/content/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Mathematics",
    "grade_level": 8,
    "topic": "Algebra Basics",
    "content_type": "interactive_lesson"
  }'
```

### Using HTTPie

#### Installation
```bash
pip install httpie
```

#### Examples
```bash
# Login
http POST localhost:8009/auth/login email=demo@example.com password=demo123

# Authenticated request with token
http GET localhost:8009/api/v1/users/me Authorization:"Bearer $TOKEN"

# Content generation
http POST localhost:8009/api/v1/content/generate \
  Authorization:"Bearer $TOKEN" \
  subject=Science \
  grade_level:=6 \
  topic="Photosynthesis" \
  content_type=interactive_experiment
```

### Using Postman

#### Environment Setup
Create a Postman environment with these variables:

```json
{
  "base_url": "http://localhost:8009",
  "token": "",
  "user_id": ""
}
```

#### Collection Structure
```
ToolBoxAI API
├── Authentication
│   ├── Login
│   ├── Refresh Token
│   └── Get Current User
├── Content Generation
│   ├── Generate Content
│   └── Get Content
├── User Management
│   ├── Get Profile
│   └── Update Profile
├── Agent Orchestration
│   ├── Execute Agent
│   └── Get Agent Status
└── Health Checks
    ├── Basic Health
    └── Integration Status
```

#### Pre-request Script (for authentication)
```javascript
// Auto-refresh token if expired
if (pm.environment.get("token")) {
    const token = pm.environment.get("token");
    const base64Payload = token.split('.')[1];
    const payload = JSON.parse(atob(base64Payload));

    if (Date.now() >= payload.exp * 1000) {
        console.log("Token expired, need to refresh");
        // Implement refresh logic
    }
}
```

### API Testing Best Practices

1. **Always test authentication first**
2. **Use environment variables for tokens and URLs**
3. **Test both success and error scenarios**
4. **Verify rate limiting behavior**
5. **Test with different user roles**
6. **Monitor response times and patterns**
7. **Validate response schemas**
8. **Test concurrent request handling**

## OpenAPI Documentation

### Interactive Documentation

The API provides interactive documentation through Swagger UI and ReDoc:

- **Swagger UI**: `http://localhost:8009/docs`
- **ReDoc**: `http://localhost:8009/redoc`
- **OpenAPI JSON**: `http://localhost:8009/openapi.json`
- **OpenAPI YAML**: `http://localhost:8009/openapi.yaml`

### API Schema Features

- **Complete endpoint documentation**
- **Request/response examples**
- **Authentication integration**
- **Interactive testing interface**
- **Schema validation**
- **Error response documentation**

### Swagger UI Features

- **Try it out** functionality for live API testing
- **Authentication integration** with bearer token support
- **Model schemas** with example values
- **Response examples** for different status codes
- **Download API specification** in JSON/YAML formats

### Using OpenAPI Specification

#### Generate Client SDKs
```bash
# Install OpenAPI Generator
npm install -g @openapitools/openapi-generator-cli

# Generate Python client
openapi-generator-cli generate \
  -i http://localhost:8009/openapi.json \
  -g python \
  -o ./api-client-python

# Generate TypeScript client
openapi-generator-cli generate \
  -i http://localhost:8009/openapi.json \
  -g typescript-axios \
  -o ./api-client-typescript
```

#### API Validation
```bash
# Install swagger-codegen-cli
brew install swagger-codegen

# Validate API specification
swagger-codegen validate -i http://localhost:8009/openapi.json
```

### Integration with Development Workflow

The OpenAPI specification enables:

- **Automated testing** with schema validation
- **Client library generation** for multiple languages
- **API documentation publishing** to documentation sites
- **Contract testing** between frontend and backend
- **Mocking services** for frontend development
- **CI/CD integration** for API change detection

---

## Quick Reference

### Essential URLs (Development)

- **API Base**: `http://localhost:8009`
- **Health Check**: `http://localhost:8009/health`
- **Documentation**: `http://localhost:8009/docs`
- **Authentication**: `http://localhost:8009/auth/login`
- **User Profile**: `http://localhost:8009/api/v1/users/me`

### Authentication Header Format

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Response Status Quick Check

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8009/health
```

### Rate Limit Check

```bash
curl -I http://localhost:8009/health | grep -i ratelimit
```

This documentation provides comprehensive coverage of the ToolBoxAI API architecture, authentication patterns, endpoint specifications, and practical usage examples. The API is designed to support both development and production environments with appropriate security measures and scalable architecture patterns.