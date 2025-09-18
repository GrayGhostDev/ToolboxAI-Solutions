# API Error Codes and Handling

## Overview

The ToolBoxAI API uses standard HTTP status codes and provides detailed error information to help developers handle errors gracefully. All error responses follow a consistent format with specific error codes for different scenarios.

## Error Response Format

### Standard Error Response
```json
{
  "error": "Error Type",
  "message": "Human-readable error description",
  "code": "SPECIFIC_ERROR_CODE",
  "details": {
    "field": "additional context",
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_12345"
  },
  "suggestions": [
    "Check your authentication token",
    "Verify the request parameters"
  ]
}
```

### Validation Error Response (422)
```json
{
  "detail": [
    {
      "loc": ["body", "grade_level"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge",
      "ctx": {"limit_value": 1}
    },
    {
      "loc": ["body", "subject"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "error_code": "VALIDATION_ERROR"
}
```

## HTTP Status Codes

### 2xx Success Codes

#### 200 OK
Request completed successfully.

#### 201 Created
Resource created successfully.

#### 202 Accepted
Request accepted for asynchronous processing.

#### 204 No Content
Request successful, no content returned.

### 4xx Client Error Codes

#### 400 Bad Request
**Common Causes:**
- Invalid request format
- Missing required parameters
- Invalid parameter values

**Error Codes:**
- `INVALID_REQUEST_FORMAT`
- `MISSING_PARAMETERS`
- `INVALID_PARAMETER_VALUE`
- `UNSUPPORTED_OPERATION`

**Example:**
```json
{
  "error": "Bad Request",
  "message": "Subject 'InvalidSubject' is not supported",
  "code": "INVALID_SUBJECT",
  "details": {
    "provided_subject": "InvalidSubject",
    "supported_subjects": ["Mathematics", "Science", "History", "English", "Art", "Geography", "Computer Science", "Physics", "Chemistry", "Biology"]
  }
}
```

#### 401 Unauthorized
**Common Causes:**
- Missing authentication token
- Invalid or expired token
- Token format errors

**Error Codes:**
- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `EXPIRED_TOKEN`
- `MALFORMED_TOKEN`

**Example:**
```json
{
  "error": "Unauthorized",
  "message": "JWT token has expired",
  "code": "EXPIRED_TOKEN",
  "details": {
    "expired_at": "2024-01-01T11:00:00Z",
    "current_time": "2024-01-01T12:00:00Z"
  },
  "suggestions": [
    "Refresh your authentication token",
    "Re-authenticate using /auth/login"
  ]
}
```

#### 403 Forbidden
**Common Causes:**
- Insufficient permissions
- Role-based access restrictions
- Feature access limitations

**Error Codes:**
- `INSUFFICIENT_PERMISSIONS`
- `ROLE_ACCESS_DENIED`
- `FEATURE_NOT_AVAILABLE`
- `ACCOUNT_SUSPENDED`

**Example:**
```json
{
  "error": "Forbidden",
  "message": "Admin role required for this operation",
  "code": "INSUFFICIENT_PERMISSIONS",
  "details": {
    "required_role": "admin",
    "current_role": "teacher",
    "endpoint": "/api/v1/admin/users"
  }
}
```

#### 404 Not Found
**Common Causes:**
- Resource doesn't exist
- Invalid endpoint URL
- Content not accessible

**Error Codes:**
- `RESOURCE_NOT_FOUND`
- `ENDPOINT_NOT_FOUND`
- `CONTENT_UNAVAILABLE`
- `USER_NOT_FOUND`

**Example:**
```json
{
  "error": "Not Found",
  "message": "Content with ID 'content_12345' not found",
  "code": "CONTENT_NOT_FOUND",
  "details": {
    "content_id": "content_12345",
    "searched_in": ["active", "archived"]
  }
}
```

#### 422 Unprocessable Entity
**Common Causes:**
- Validation errors
- Business logic violations
- Data consistency issues

**Error Codes:**
- `VALIDATION_ERROR`
- `BUSINESS_RULE_VIOLATION`
- `DATA_CONSISTENCY_ERROR`

#### 429 Too Many Requests
**Common Causes:**
- Rate limit exceeded
- API quota exhausted
- Concurrent request limits

**Error Codes:**
- `RATE_LIMIT_EXCEEDED`
- `QUOTA_EXHAUSTED`
- `CONCURRENT_LIMIT_EXCEEDED`

**Example:**
```json
{
  "error": "Too Many Requests",
  "message": "Content generation rate limit exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "limit": 5,
    "window": "1 hour",
    "reset_time": "2024-01-01T13:00:00Z",
    "retry_after": 1800
  }
}
```

### 5xx Server Error Codes

#### 500 Internal Server Error
**Common Causes:**
- Unexpected server errors
- Database connection issues
- External service failures

**Error Codes:**
- `INTERNAL_SERVER_ERROR`
- `DATABASE_ERROR`
- `EXTERNAL_SERVICE_ERROR`

#### 502 Bad Gateway
**Common Causes:**
- Upstream service unavailable
- Roblox API issues
- AI service connection problems

**Error Codes:**
- `UPSTREAM_SERVICE_ERROR`
- `ROBLOX_API_ERROR`
- `AI_SERVICE_UNAVAILABLE`

#### 503 Service Unavailable
**Common Causes:**
- Maintenance mode
- Service overload
- Temporary shutdowns

**Error Codes:**
- `SERVICE_MAINTENANCE`
- `SERVICE_OVERLOADED`
- `TEMPORARY_UNAVAILABLE`

#### 504 Gateway Timeout
**Common Causes:**
- Content generation timeout
- Long-running operations
- Network connectivity issues

**Error Codes:**
- `CONTENT_GENERATION_TIMEOUT`
- `OPERATION_TIMEOUT`
- `NETWORK_TIMEOUT`

## Specific Error Scenarios

### Authentication Errors

#### Invalid Login Credentials
```json
{
  "error": "Authentication Failed",
  "message": "Invalid username or password",
  "code": "INVALID_CREDENTIALS",
  "details": {
    "username": "user@example.com",
    "failed_attempts": 3,
    "lockout_time": null
  }
}
```

#### Account Locked
```json
{
  "error": "Account Locked",
  "message": "Account temporarily locked due to multiple failed login attempts",
  "code": "ACCOUNT_LOCKED",
  "details": {
    "lockout_until": "2024-01-01T13:00:00Z",
    "failed_attempts": 5,
    "unlock_methods": ["wait", "contact_admin"]
  }
}
```

### Content Generation Errors

#### Generation Failed
```json
{
  "error": "Content Generation Failed",
  "message": "AI service encountered an error during content generation",
  "code": "GENERATION_FAILED",
  "details": {
    "content_id": "content_12345",
    "stage": "script_generation",
    "ai_error": "Token limit exceeded",
    "retry_possible": true
  }
}
```

#### Unsupported Content Type
```json
{
  "error": "Unsupported Content",
  "message": "The requested combination of subject and environment is not supported",
  "code": "UNSUPPORTED_CONTENT_TYPE",
  "details": {
    "subject": "Mathematics",
    "environment": "underwater",
    "supported_combinations": [...]
  }
}
```

### Roblox Integration Errors

#### Invalid Place ID
```json
{
  "error": "Invalid Roblox Place",
  "message": "The specified Roblox place ID is invalid or inaccessible",
  "code": "INVALID_PLACE_ID",
  "details": {
    "place_id": "123456789",
    "roblox_error": "Place not found",
    "user_has_access": false
  }
}
```

#### Deployment Failed
```json
{
  "error": "Deployment Failed",
  "message": "Failed to deploy content to Roblox place",
  "code": "DEPLOYMENT_FAILED",
  "details": {
    "deployment_id": "deploy_abc123",
    "place_id": "123456789",
    "stage": "uploading_scripts",
    "roblox_error": "Rate limit exceeded"
  }
}
```

### Real-time Communication Errors

#### Pusher Authentication Failed
```json
{
  "error": "Channel Authentication Failed",
  "message": "Unable to authenticate for private channel",
  "code": "PUSHER_AUTH_FAILED",
  "details": {
    "channel": "private-user-12345",
    "socket_id": "123456.789012",
    "user_id": "12345"
  }
}
```

#### WebSocket Connection Error
```json
{
  "error": "WebSocket Connection Failed",
  "message": "Unable to establish WebSocket connection",
  "code": "WEBSOCKET_CONNECTION_ERROR",
  "details": {
    "endpoint": "ws://127.0.0.1:8008/ws/content",
    "reason": "Authentication failed"
  }
}
```

## Error Handling Best Practices

### Client-Side Error Handling

#### JavaScript/TypeScript Example
```typescript
interface APIError {
  error: string;
  message: string;
  code: string;
  details?: any;
  suggestions?: string[];
}

class APIClient {
  async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData: APIError = await response.json();
      throw new APIError(errorData);
    }
    return response.json();
  }

  async makeRequest<T>(url: string, options: RequestInit): Promise<T> {
    try {
      const response = await fetch(url, options);
      return await this.handleResponse<T>(response);
    } catch (error) {
      if (error instanceof APIError) {
        this.handleAPIError(error);
      }
      throw error;
    }
  }

  private handleAPIError(error: APIError): void {
    switch (error.code) {
      case 'EXPIRED_TOKEN':
        this.refreshToken();
        break;
      case 'RATE_LIMIT_EXCEEDED':
        this.scheduleRetry(error.details?.retry_after);
        break;
      case 'VALIDATION_ERROR':
        this.showValidationErrors(error.details);
        break;
      default:
        this.showGenericError(error.message);
    }
  }
}

class APIError extends Error {
  constructor(public errorData: APIError) {
    super(errorData.message);
    this.name = 'APIError';
  }
}
```

#### Python Example
```python
import requests
from typing import Dict, Any, Optional
import time

class ToolBoxAIError(Exception):
    def __init__(self, error_data: Dict[str, Any]):
        self.error_data = error_data
        super().__init__(error_data.get('message', 'Unknown error'))

    @property
    def code(self) -> str:
        return self.error_data.get('code', 'UNKNOWN_ERROR')

    @property
    def details(self) -> Optional[Dict[str, Any]]:
        return self.error_data.get('details')

    @property
    def suggestions(self) -> list:
        return self.error_data.get('suggestions', [])

class APIClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        if response.ok:
            return response.json()

        try:
            error_data = response.json()
        except ValueError:
            error_data = {
                'error': 'HTTP Error',
                'message': f'HTTP {response.status_code}',
                'code': f'HTTP_{response.status_code}'
            }

        raise ToolBoxAIError(error_data)

    def make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self.token}'

        try:
            response = self.session.request(method, url, headers=headers, **kwargs)
            return self._handle_response(response)
        except ToolBoxAIError as e:
            self._handle_api_error(e)
            raise

    def _handle_api_error(self, error: ToolBoxAIError):
        if error.code == 'EXPIRED_TOKEN':
            # Attempt to refresh token
            self._refresh_token()
        elif error.code == 'RATE_LIMIT_EXCEEDED':
            # Wait and retry
            retry_after = error.details.get('retry_after', 60)
            time.sleep(retry_after)
        elif error.code == 'VALIDATION_ERROR':
            # Log validation details
            print(f"Validation errors: {error.details}")

    def _refresh_token(self):
        # Implement token refresh logic
        pass
```

### Retry Logic

#### Exponential Backoff
```python
import time
import random

def retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0
):
    for attempt in range(max_retries + 1):
        try:
            return func()
        except ToolBoxAIError as e:
            if attempt == max_retries:
                raise

            # Don't retry certain errors
            if e.code in ['INVALID_TOKEN', 'FORBIDDEN', 'NOT_FOUND']:
                raise

            # Calculate delay with jitter
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            jitter = random.uniform(0, 0.1) * delay
            time.sleep(delay + jitter)
```

### Error Monitoring

#### Logging Errors
```python
import logging

logger = logging.getLogger(__name__)

def log_api_error(error: ToolBoxAIError, context: Dict[str, Any]):
    logger.error(
        "API Error occurred",
        extra={
            'error_code': error.code,
            'error_message': error.message,
            'error_details': error.details,
            'context': context,
            'suggestions': error.suggestions
        }
    )
```

#### Error Metrics
```javascript
// Track error rates
const errorMetrics = {
  track(errorCode: string, endpoint: string) {
    // Send to analytics service
    analytics.track('api_error', {
      error_code: errorCode,
      endpoint: endpoint,
      timestamp: new Date().toISOString()
    });
  }
};
```

## Error Recovery Strategies

### Token Management
- Implement automatic token refresh
- Cache tokens with expiration tracking
- Handle token revocation gracefully

### Content Generation
- Save intermediate progress for recovery
- Implement resume functionality for failed generations
- Provide manual retry options with modified parameters

### Network Resilience
- Implement circuit breaker patterns
- Use connection pooling for better reliability
- Handle temporary network failures gracefully

### User Experience
- Show meaningful error messages to users
- Provide actionable suggestions when possible
- Implement graceful degradation for non-critical features
- Use loading states and progress indicators

## Testing Error Scenarios

### Error Simulation Endpoints
```bash
# Trigger various error conditions for testing
curl -X GET "http://127.0.0.1:8008/test/error/401"
curl -X GET "http://127.0.0.1:8008/test/error/rate-limit"
curl -X GET "http://127.0.0.1:8008/test/error/validation"
```

### Mock Error Responses
```javascript
// Mock API for testing error handling
const mockErrorResponses = {
  401: {
    error: "Unauthorized",
    message: "Invalid token",
    code: "INVALID_TOKEN"
  },
  429: {
    error: "Too Many Requests",
    message: "Rate limit exceeded",
    code: "RATE_LIMIT_EXCEEDED",
    details: { retry_after: 60 }
  }
};
```

## Error Documentation Updates

This error documentation is updated regularly to include:
- New error codes and scenarios
- Updated retry strategies
- Performance optimization tips
- User experience improvements

For the most current error codes and handling strategies, refer to the OpenAPI specification at `/docs` or contact the API support team.