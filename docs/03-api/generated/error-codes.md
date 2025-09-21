# Error Codes Reference

## Overview

The ToolBoxAI API uses standard HTTP status codes and provides detailed error information in a consistent format. This guide covers all error codes, their meanings, and resolution strategies.

## Error Response Format

All API errors follow this consistent structure:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {
      "field": "specific_field_name",
      "issue": "Detailed issue description",
      "suggestion": "How to fix this error"
    }
  },
  "metadata": {
    "timestamp": "2025-01-21T10:00:00Z",
    "request_id": "req_abc123",
    "trace_id": "trace_xyz789",
    "endpoint": "/api/v1/content/generate",
    "method": "POST"
  }
}
```

## HTTP Status Codes

| Status | Description | Usage |
|--------|-------------|-------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request successful, no content returned |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required or failed |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (duplicate, etc.) |
| 422 | Unprocessable Entity | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | External service error |
| 503 | Service Unavailable | Service temporarily unavailable |

---

## Authentication Errors (401)

### AUTHENTICATION_REQUIRED
```json
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Valid JWT token required for this endpoint",
    "details": {
      "endpoint": "/api/v1/classes",
      "required_header": "Authorization: Bearer <token>"
    }
  }
}
```

**Solution**: Include valid JWT token in Authorization header

### INVALID_TOKEN
```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "JWT token is malformed or invalid",
    "details": {
      "issue": "Token signature verification failed",
      "suggestion": "Obtain a new token via /api/v1/auth/login"
    }
  }
}
```

**Solution**: Re-authenticate to get a new token

### TOKEN_EXPIRED
```json
{
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "JWT token has expired",
    "details": {
      "expired_at": "2025-01-21T10:00:00Z",
      "current_time": "2025-01-21T10:30:00Z",
      "suggestion": "Use /api/v1/auth/refresh or re-login"
    }
  }
}
```

**Solution**: Refresh token or re-authenticate

### INVALID_CREDENTIALS
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid username/email or password",
    "details": {
      "attempts_remaining": 4,
      "lockout_duration": "15 minutes"
    }
  }
}
```

**Solution**: Check credentials and retry

---

## Authorization Errors (403)

### INSUFFICIENT_PERMISSIONS
```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "User role lacks required permissions",
    "details": {
      "user_role": "student",
      "required_role": "teacher",
      "required_permissions": ["content:create", "class:manage"]
    }
  }
}
```

**Solution**: Contact admin to upgrade user role or permissions

### RESOURCE_ACCESS_DENIED
```json
{
  "error": {
    "code": "RESOURCE_ACCESS_DENIED",
    "message": "Access denied to this specific resource",
    "details": {
      "resource_type": "class",
      "resource_id": "class_123",
      "reason": "Not a member of this class"
    }
  }
}
```

**Solution**: Request access from resource owner or admin

### FEATURE_NOT_AVAILABLE
```json
{
  "error": {
    "code": "FEATURE_NOT_AVAILABLE",
    "message": "Feature not available in current subscription plan",
    "details": {
      "feature": "ai_content_generation",
      "current_plan": "basic",
      "required_plan": "premium"
    }
  }
}
```

**Solution**: Upgrade subscription plan

---

## Validation Errors (400, 422)

### VALIDATION_ERROR
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field": "grade_level",
      "value": "invalid",
      "expected": "String matching pattern: K-2, 3-5, 6-8, 9-12",
      "suggestion": "Use valid grade level format"
    }
  }
}
```

**Solution**: Fix the invalid field and retry

### MISSING_REQUIRED_FIELD
```json
{
  "error": {
    "code": "MISSING_REQUIRED_FIELD",
    "message": "Required field is missing",
    "details": {
      "field": "learning_objectives",
      "requirement": "Array with 1-10 objectives"
    }
  }
}
```

**Solution**: Include the required field in request

### INVALID_FIELD_TYPE
```json
{
  "error": {
    "code": "INVALID_FIELD_TYPE",
    "message": "Field has incorrect data type",
    "details": {
      "field": "duration_minutes",
      "provided_type": "string",
      "expected_type": "integer",
      "constraints": "Between 5 and 120"
    }
  }
}
```

**Solution**: Provide correct data type

### FIELD_TOO_LONG
```json
{
  "error": {
    "code": "FIELD_TOO_LONG",
    "message": "Field value exceeds maximum length",
    "details": {
      "field": "subject",
      "current_length": 150,
      "max_length": 100
    }
  }
}
```

**Solution**: Shorten the field value

### INVALID_EMAIL_FORMAT
```json
{
  "error": {
    "code": "INVALID_EMAIL_FORMAT",
    "message": "Email address format is invalid",
    "details": {
      "field": "email",
      "value": "invalid-email",
      "pattern": "user@domain.com"
    }
  }
}
```

**Solution**: Provide valid email format

---

## Rate Limiting Errors (429)

### RATE_LIMIT_EXCEEDED
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Request rate limit exceeded",
    "details": {
      "limit": "100 requests per minute",
      "reset_time": "2025-01-21T10:01:00Z",
      "retry_after": 45
    }
  }
}
```

**Solution**: Wait for reset time or implement backoff strategy

**Response Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642771260
Retry-After: 45
```

### CONCURRENT_LIMIT_EXCEEDED
```json
{
  "error": {
    "code": "CONCURRENT_LIMIT_EXCEEDED",
    "message": "Too many concurrent requests",
    "details": {
      "concurrent_limit": 10,
      "current_count": 15,
      "suggestion": "Wait for some requests to complete"
    }
  }
}
```

**Solution**: Reduce concurrent requests or implement queuing

---

## Resource Errors (404, 409)

### RESOURCE_NOT_FOUND
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Requested resource does not exist",
    "details": {
      "resource_type": "class",
      "resource_id": "class_999",
      "suggestion": "Check resource ID or use list endpoint"
    }
  }
}
```

**Solution**: Verify resource ID exists

### RESOURCE_ALREADY_EXISTS
```json
{
  "error": {
    "code": "RESOURCE_ALREADY_EXISTS",
    "message": "Resource with this identifier already exists",
    "details": {
      "resource_type": "user",
      "conflicting_field": "email",
      "existing_value": "user@example.com"
    }
  }
}
```

**Solution**: Use different identifier or update existing resource

### RESOURCE_DELETED
```json
{
  "error": {
    "code": "RESOURCE_DELETED",
    "message": "Resource has been deleted",
    "details": {
      "resource_type": "lesson",
      "resource_id": "lesson_123",
      "deleted_at": "2025-01-20T15:30:00Z"
    }
  }
}
```

**Solution**: Use different resource or restore if possible

---

## Content Generation Errors

### GENERATION_FAILED
```json
{
  "error": {
    "code": "GENERATION_FAILED",
    "message": "Content generation process failed",
    "details": {
      "session_id": "gen_abc123",
      "stage": "quiz_generation",
      "failure_reason": "Insufficient context for quiz questions",
      "retry_possible": true
    }
  }
}
```

**Solution**: Retry with more detailed learning objectives

### INVALID_CONTENT_PARAMETERS
```json
{
  "error": {
    "code": "INVALID_CONTENT_PARAMETERS",
    "message": "Content generation parameters are incompatible",
    "details": {
      "issue": "Grade level 'K-2' incompatible with difficulty 'expert'",
      "suggestion": "Use 'easy' or 'medium' difficulty for K-2"
    }
  }
}
```

**Solution**: Adjust parameters to be compatible

### GENERATION_TIMEOUT
```json
{
  "error": {
    "code": "GENERATION_TIMEOUT",
    "message": "Content generation timed out",
    "details": {
      "session_id": "gen_abc123",
      "timeout_duration": "300 seconds",
      "partial_results_available": true
    }
  }
}
```

**Solution**: Try again with simpler parameters

---

## Roblox Integration Errors

### ROBLOX_AUTH_FAILED
```json
{
  "error": {
    "code": "ROBLOX_AUTH_FAILED",
    "message": "Roblox OAuth authentication failed",
    "details": {
      "oauth_error": "invalid_grant",
      "suggestion": "Re-initiate OAuth flow"
    }
  }
}
```

**Solution**: Start new OAuth flow

### ROBLOX_API_ERROR
```json
{
  "error": {
    "code": "ROBLOX_API_ERROR",
    "message": "Roblox Open Cloud API error",
    "details": {
      "api_endpoint": "universes/12345/messaging-service",
      "roblox_error": "UniverseNotFound",
      "suggestion": "Verify universe ID is correct"
    }
  }
}
```

**Solution**: Check Roblox configuration and permissions

### ENVIRONMENT_GENERATION_FAILED
```json
{
  "error": {
    "code": "ENVIRONMENT_GENERATION_FAILED",
    "message": "Roblox environment generation failed",
    "details": {
      "environment_type": "space_station",
      "failure_stage": "script_generation",
      "error": "Insufficient memory for large environment"
    }
  }
}
```

**Solution**: Try smaller environment size or different type

---

## Payment Errors

### PAYMENT_REQUIRED
```json
{
  "error": {
    "code": "PAYMENT_REQUIRED",
    "message": "Payment required to access this feature",
    "details": {
      "feature": "advanced_analytics",
      "required_plan": "premium",
      "upgrade_url": "/billing/upgrade"
    }
  }
}
```

**Solution**: Upgrade subscription plan

### STRIPE_ERROR
```json
{
  "error": {
    "code": "STRIPE_ERROR",
    "message": "Payment processing error",
    "details": {
      "stripe_code": "card_declined",
      "decline_code": "insufficient_funds",
      "suggestion": "Use different payment method"
    }
  }
}
```

**Solution**: Contact payment provider or use different method

---

## WebSocket Errors

### WEBSOCKET_AUTH_REQUIRED
```json
{
  "type": "error",
  "data": {
    "error_code": "WEBSOCKET_AUTH_REQUIRED",
    "message": "Authentication required for WebSocket connection",
    "details": {
      "endpoint": "/ws/content/gen_123",
      "required_message": {
        "type": "auth",
        "token": "Bearer <jwt_token>"
      }
    }
  }
}
```

**Solution**: Send auth message after WebSocket connection

### WEBSOCKET_CONNECTION_LIMIT
```json
{
  "type": "error",
  "data": {
    "error_code": "WEBSOCKET_CONNECTION_LIMIT",
    "message": "Maximum WebSocket connections exceeded",
    "details": {
      "current_connections": 10,
      "max_connections": 10,
      "suggestion": "Close unused connections"
    }
  }
}
```

**Solution**: Close existing WebSocket connections

---

## Server Errors (500+)

### INTERNAL_SERVER_ERROR
```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred",
    "details": {
      "request_id": "req_abc123",
      "suggestion": "Retry request or contact support if persists"
    }
  }
}
```

**Solution**: Retry request, contact support if persistent

### DATABASE_ERROR
```json
{
  "error": {
    "code": "DATABASE_ERROR",
    "message": "Database operation failed",
    "details": {
      "operation": "SELECT",
      "table": "classes",
      "suggestion": "Retry request in a few moments"
    }
  }
}
```

**Solution**: Retry request after brief delay

### EXTERNAL_SERVICE_ERROR
```json
{
  "error": {
    "code": "EXTERNAL_SERVICE_ERROR",
    "message": "External service unavailable",
    "details": {
      "service": "OpenAI API",
      "status": "503 Service Unavailable",
      "suggestion": "Try again in a few minutes"
    }
  }
}
```

**Solution**: Wait and retry, external service issue

### AI_SERVICE_OVERLOAD
```json
{
  "error": {
    "code": "AI_SERVICE_OVERLOAD",
    "message": "AI service is temporarily overloaded",
    "details": {
      "estimated_wait_time": "2-3 minutes",
      "suggestion": "Queue request for later processing"
    }
  }
}
```

**Solution**: Implement retry with exponential backoff

---

## Error Handling Best Practices

### 1. Retry Logic

```javascript
async function apiCallWithRetry(endpoint, options, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(endpoint, options);

      if (response.ok) {
        return await response.json();
      }

      const errorData = await response.json();

      // Don't retry client errors (4xx)
      if (response.status >= 400 && response.status < 500) {
        throw new Error(errorData.error.message);
      }

      // Retry server errors (5xx) with backoff
      if (attempt < maxRetries) {
        const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }

      throw new Error(errorData.error.message);

    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }
    }
  }
}
```

### 2. Rate Limit Handling

```javascript
async function handleRateLimit(response) {
  if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After');
    const delay = retryAfter ? parseInt(retryAfter) * 1000 : 60000;

    console.log(`Rate limited. Waiting ${delay}ms...`);
    await new Promise(resolve => setTimeout(resolve, delay));

    return true; // Indicates should retry
  }
  return false;
}
```

### 3. Error Classification

```javascript
function classifyError(error) {
  const status = error.status || error.response?.status;

  switch (status) {
    case 401:
      return 'AUTHENTICATION';
    case 403:
      return 'AUTHORIZATION';
    case 404:
      return 'NOT_FOUND';
    case 422:
      return 'VALIDATION';
    case 429:
      return 'RATE_LIMIT';
    case 500:
    case 502:
    case 503:
      return 'SERVER_ERROR';
    default:
      return 'UNKNOWN';
  }
}
```

### 4. User-Friendly Error Messages

```javascript
function getUserFriendlyMessage(errorCode) {
  const messages = {
    'INVALID_CREDENTIALS': 'Please check your email and password.',
    'TOKEN_EXPIRED': 'Your session has expired. Please log in again.',
    'RATE_LIMIT_EXCEEDED': 'Too many requests. Please wait a moment and try again.',
    'VALIDATION_ERROR': 'Please check your input and correct any errors.',
    'GENERATION_FAILED': 'Content generation failed. Please try with different parameters.',
    'PAYMENT_REQUIRED': 'This feature requires a premium subscription.',
    'INTERNAL_SERVER_ERROR': 'Something went wrong. Please try again.'
  };

  return messages[errorCode] || 'An unexpected error occurred.';
}
```

## Monitoring and Debugging

### Error Tracking
- **Request ID**: Use `request_id` from error response for support
- **Trace ID**: Include `trace_id` for distributed tracing
- **Correlation**: Track errors across multiple API calls

### Common Debug Steps
1. **Check Authentication**: Verify JWT token is valid and not expired
2. **Validate Parameters**: Ensure all required fields are present and valid
3. **Review Rate Limits**: Check response headers for rate limit status
4. **Monitor Server Status**: Check `/health` endpoint for system status
5. **Test Connectivity**: Use simple endpoints to verify basic connectivity

### Support Information
When contacting support, include:
- Request ID from error response
- Full error response
- Request parameters (excluding sensitive data)
- Timestamp of error occurrence
- User role and permissions

---

This comprehensive error reference should help you handle all types of errors gracefully and provide a better experience for your users.