# API Error Codes

This document describes error codes and responses for ToolBoxAI-Solutions API endpoints.

## Common Error Codes

| Code            | HTTP Status | Description                         |
| --------------- | ----------- | ----------------------------------- |
| `INVALID_INPUT` | 400         | Input data is invalid or missing    |
| `AUTH_FAILED`   | 401         | Authentication failed               |
| `FORBIDDEN`     | 403         | User does not have permission       |
| `NOT_FOUND`     | 404         | Resource not found                  |
| `CONFLICT`      | 409         | Resource conflict (e.g., duplicate) |
| `RATE_LIMIT`    | 429         | Too many requests                   |
| `SERVER_ERROR`  | 500         | Internal server error               |

## Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "Input data is invalid or missing",
    "details": {}
  }
}
```text
## Best Practices

- Always check error codes and messages
- Handle authentication and permission errors gracefully
- Log server errors for debugging
