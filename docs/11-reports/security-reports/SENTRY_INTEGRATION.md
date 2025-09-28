# Sentry Integration Documentation

## Overview

This document describes the comprehensive Sentry integration implemented for the ToolboxAI FastAPI application. Sentry provides error tracking, performance monitoring, and user experience insights for production applications.

## Features Implemented

### ✅ Error Tracking and Performance Monitoring
- **Automatic error capture** with full stack traces
- **Performance transaction monitoring** for API endpoints
- **Custom spans** for educational content generation
- **Database operation monitoring** (SQLAlchemy integration)
- **External API call monitoring** (HTTP client integration)
- **WebSocket connection tracking**

### ✅ User Context and Authentication
- **User context tracking** for authenticated requests
- **Authentication breadcrumbs** for login attempts
- **Role-based error categorization**
- **Request correlation** with user sessions

### ✅ Custom Context and Breadcrumbs
- **Educational content context** with subject, grade level, and objectives
- **Request lifecycle breadcrumbs** with performance metrics
- **Application startup/shutdown tracking**
- **Custom error categorization** by component (AI agents, Roblox plugin, etc.)

### ✅ Production-Ready Configuration
- **Environment-based sampling rates** (100% for dev, 10% for production)
- **PII (Personally Identifiable Information) filtering**
- **Sensitive data sanitization** in error reports
- **Circuit breaker integration** with error reporting

### ✅ Comprehensive Logging Integration
- **Python logging forwarding** to Sentry
- **Log level filtering** (INFO and above)
- **Structured logging** with context

## Configuration

### Environment Variables

```bash
# Required
SENTRY_DSN=https://af64bfdc2bd0cd6cd870bfeb7f26c22c@o4509912543199232.ingest.us.sentry.io/4509991438581760

# Optional (with defaults)
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=1.0  # Use 0.1 for production
SENTRY_PROFILES_SAMPLE_RATE=1.0  # Use 0.1 for production
SENTRY_SEND_DEFAULT_PII=false
SENTRY_ENABLE_LOGS=true
SENTRY_RELEASE=1.0.0  # Defaults to APP_VERSION
SENTRY_SERVER_NAME=toolboxai-server  # Defaults to hostname
```

### Production vs Development Configuration

| Setting | Development | Production |
|---------|-------------|------------|
| `SENTRY_TRACES_SAMPLE_RATE` | 1.0 (100%) | 0.1 (10%) |
| `SENTRY_PROFILES_SAMPLE_RATE` | 1.0 (100%) | 0.1 (10%) |
| `SENTRY_SEND_DEFAULT_PII` | false | false |
| `SENTRY_ENABLE_LOGS` | true | true |
| Debug endpoint `/sentry-debug` | Enabled | Disabled |

## Usage Examples

### 1. Monitoring Educational Content Generation

```python
from server.sentry_config import sentry_performance_monitor, capture_educational_content_error

@sentry_performance_monitor(operation="content.generation", description="Generate educational content")
async def generate_educational_content(content_request, user):
    try:
        # Content generation logic
        return result
    except Exception as e:
        capture_educational_content_error(
            content_request.model_dump(),
            e,
            user.id
        )
        raise
```

### 2. Database Operation Monitoring

```python
from server.sentry_config import sentry_database_monitor

@sentry_database_monitor(operation="db.user_lookup")
async def get_user_by_id(user_id: str):
    # Database query logic
    pass
```

### 3. External API Monitoring

```python
from server.sentry_config import sentry_external_api_monitor

@sentry_external_api_monitor(service_name="openai")
async def call_openai_api(prompt: str):
    # OpenAI API call logic
    pass
```

### 4. Manual Context and Breadcrumbs

```python
from server.sentry_config import sentry_manager

# Set user context
sentry_manager.set_user_context(
    user_id="user-123",
    username="john_doe",
    email="john@example.com",
    role="teacher"
)

# Add custom context
sentry_manager.set_context("quiz_generation", {
    "subject": "Mathematics",
    "difficulty": "medium",
    "question_count": 10
})

# Add breadcrumb
sentry_manager.add_breadcrumb(
    message="Quiz generation started",
    category="quiz",
    level="info",
    data={"subject": "Mathematics"}
)
```

## API Endpoints

### Health and Status Endpoints

1. **`GET /sentry/status`** - Detailed Sentry integration status
   ```json
   {
     "status": "active",
     "initialized": true,
     "dsn_configured": true,
     "environment": "development",
     "integration_features": {
       "error_tracking": true,
       "performance_monitoring": true,
       "release_tracking": true,
       "user_context": true,
       "custom_tags": true,
       "breadcrumbs": true
     }
   }
   ```

2. **`GET /metrics`** - System metrics including Sentry status
   ```json
   {
     "sentry": {
       "initialized": true,
       "dsn_configured": true,
       "environment": "development"
     }
   }
   ```

3. **`GET /sentry-debug`** - Test endpoint (development only)
   - Triggers a test error to verify Sentry integration
   - Returns error details and confirmation

## Error Categories and Context

### Automatic Context Enrichment

1. **Request Context**
   - Request ID, method, path
   - User agent, client IP
   - Query parameters
   - Response time and status

2. **User Context** (when authenticated)
   - User ID, username, email
   - Role and permissions
   - Last active timestamp

3. **Application Context**
   - Environment (development, staging, production)
   - Application version and release
   - Server hostname
   - Debug mode status

4. **Educational Content Context**
   - Subject and grade level
   - Learning objectives
   - Content type and complexity
   - Generation parameters

### Error Categorization

- **Authentication Errors**: Login failures, token validation
- **Content Generation Errors**: AI model failures, parameter validation
- **Database Errors**: Connection issues, query failures
- **External API Errors**: OpenAI, LMS integrations
- **Roblox Plugin Errors**: Communication failures, script generation
- **WebSocket Errors**: Connection drops, message failures

## Performance Monitoring

### Tracked Operations

1. **Content Generation Pipeline**
   - Educational content creation
   - Quiz generation
   - Terrain generation
   - Lua script compilation

2. **Database Operations**
   - User authentication
   - Data persistence
   - Query performance

3. **External API Calls**
   - OpenAI GPT-4 requests
   - LMS platform integrations
   - Roblox API interactions

4. **Real-time Communications**
   - WebSocket message processing
   - Live content updates

### Performance Metrics

- **Response Times**: API endpoint performance
- **Throughput**: Requests per second
- **Error Rates**: By endpoint and operation type
- **User Experience**: Real user monitoring

## Security and Privacy

### Data Sanitization

Sensitive information is automatically filtered from Sentry reports:

- **Authentication tokens** (JWT, Bearer tokens)
- **API keys** (OpenAI, third-party services)
- **Passwords** and security credentials
- **Session cookies** and CSRF tokens
- **User PII** (when `SENTRY_SEND_DEFAULT_PII=false`)

### Error Filtering

Production environments filter out:

- **Client validation errors** (4xx status codes)
- **Health check requests** (`/health`, `/metrics`)
- **Rate limit errors** (logged but not always sent to Sentry)

## Deployment and Operations

### Installation Steps

1. **Install Sentry SDK** (already in requirements.txt)
   ```bash
   pip install sentry-sdk[fastapi,sqlalchemy,redis,pure_eval]==2.21.0
   ```

2. **Configure Environment Variables**
   ```bash
   cp .env.sentry.example .env
   # Edit .env with your Sentry DSN and configuration
   ```

3. **Verify Integration**
   ```bash
   # Start the application
   python -m uvicorn server.main:app --reload
   
   # Test Sentry integration (development only)
   curl http://localhost:8008/sentry-debug
   
   # Check status
   curl http://localhost:8008/sentry/status
   ```

### Production Checklist

- [ ] Set production Sentry DSN
- [ ] Configure appropriate sample rates (0.1 recommended)
- [ ] Set `SENTRY_ENVIRONMENT=production`
- [ ] Ensure `SENTRY_SEND_DEFAULT_PII=false`
- [ ] Set up Sentry alerts and notifications
- [ ] Configure Sentry release tracking
- [ ] Test error reporting in staging environment

### Monitoring and Alerts

Recommended Sentry alert configurations:

1. **Error Rate Alerts**: > 5% error rate in 5-minute window
2. **Performance Alerts**: 95th percentile response time > 2 seconds
3. **Volume Alerts**: Unusual traffic spikes or drops
4. **New Issue Alerts**: First occurrence of new error types

## Troubleshooting

### Common Issues

1. **Sentry Not Initialized**
   - Check `SENTRY_DSN` environment variable
   - Verify DSN format and validity
   - Check application startup logs

2. **Missing Error Context**
   - Ensure user is authenticated for user context
   - Verify custom context is set before error occurs
   - Check middleware execution order

3. **Performance Data Missing**
   - Verify `SENTRY_TRACES_SAMPLE_RATE > 0`
   - Check transaction naming and spans
   - Ensure performance monitoring is enabled

4. **Too Many Events**
   - Reduce sample rates in production
   - Implement better error filtering
   - Use rate limiting for high-volume operations

### Debug Commands

```bash
# Check Sentry status
curl http://localhost:8008/sentry/status

# Trigger test error (development)
curl http://localhost:8008/sentry-debug

# View application metrics
curl http://localhost:8008/metrics

# Check application health
curl http://localhost:8008/health
```

## Integration Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Sentry Manager │    │   Sentry.io     │
│                 │    │                 │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Request       │────│ • Error Capture │────│ • Error         │
│   Middleware    │    │ • Performance   │    │   Tracking      │
│ • Error         │    │   Monitoring    │    │ • Performance   │
│   Handlers      │    │ • User Context  │    │   Monitoring    │
│ • Auth System   │    │ • Custom Tags   │    │ • Alerting      │
│ • Content Gen   │    │ • Breadcrumbs   │    │ • Dashboards    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│ Local Logging   │──────────────┘
                        │ • File logs     │
                        │ • Console logs  │
                        │ • Structured    │
                        └─────────────────┘
```

## Support and Resources

- **Sentry Documentation**: https://docs.sentry.io/
- **FastAPI Integration**: https://docs.sentry.io/platforms/python/guides/fastapi/
- **Performance Monitoring**: https://docs.sentry.io/product/performance/
- **Error Tracking**: https://docs.sentry.io/product/issues/

## Implementation Checklist

### ✅ Completed Features

- [x] Sentry SDK integration with FastAPI
- [x] Error tracking with automatic capture
- [x] Performance monitoring with custom spans
- [x] User context enrichment
- [x] Request correlation and breadcrumbs
- [x] Educational content error categorization
- [x] Production-ready configuration
- [x] Environment-based sampling
- [x] PII and sensitive data filtering
- [x] Comprehensive logging integration
- [x] Health check and status endpoints
- [x] Debug endpoint for testing
- [x] Authentication tracking
- [x] Custom error context

### 🔄 Future Enhancements

- [ ] Custom Sentry dashboard for educational metrics
- [ ] Integration with Sentry alerts and notifications
- [ ] Advanced performance profiling
- [ ] Custom error grouping rules
- [ ] Sentry release automation with CI/CD
- [ ] User feedback collection
- [ ] Session replay integration

---

**Note**: This integration provides comprehensive error tracking and performance monitoring for the ToolboxAI educational platform. All sensitive data is filtered and the configuration is optimized for both development and production environments.