---
title: Roblox API Reference 2025
description: Complete API reference for Roblox integration with Open Cloud API standards, Pusher real-time, and AES-256 encryption
version: 2.1.0
last_updated: 2025-09-28
---

# 🎮 Roblox API Reference 2025

## Overview

This document provides comprehensive API documentation for the ToolboxAI Roblox integration, implementing 2025 Open Cloud API standards, OAuth2 with PKCE authentication, Pusher real-time channels, and AES-256 credential encryption.

## Base URL

```
Production: https://api.toolboxai.com
Development: http://127.0.0.1:8009
```

## API Versioning

All endpoints are versioned under `/api/v1/roblox/`

## 🔐 Authentication

### OAuth2 with PKCE Flow

#### Initiate OAuth2 Flow

```http
POST /api/v1/roblox/auth/initiate
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "redirect_uri": "http://127.0.0.1:8009/api/v1/roblox/auth/callback",
  "scopes": ["openid", "profile", "asset:read", "asset:write"],
  "state": "optional_state_parameter"
}
```

**Response:**
```json
{
  "authorization_url": "https://authorize.roblox.com/v1/authorize?...",
  "state": "generated_state_token",
  "code_verifier": "pkce_verifier_for_secure_flow",
  "expires_at": "2025-09-28T12:00:00Z"
}
```

#### OAuth2 Callback

```http
GET /api/v1/roblox/auth/callback?code={auth_code}&state={state_token}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_value",
  "scope": "openid profile asset:read asset:write",
  "user_info": {
    "user_id": "123456789",
    "username": "RobloxUser",
    "display_name": "User Display Name"
  }
}
```

#### Refresh Token

```http
POST /api/v1/roblox/auth/refresh
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "refresh_token": "refresh_token_value"
}
```

#### Revoke Token

```http
POST /api/v1/roblox/auth/revoke
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "token": "token_to_revoke",
  "token_type_hint": "access_token"
}
```

## 📡 Pusher Real-time

### Authenticate Pusher Channel

```http
POST /api/v1/roblox/pusher/auth
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "socket_id": "12345.67890",
  "channel_name": "private-roblox-conversation-session123",
  "user_data": {
    "user_id": "user_123",
    "username": "RobloxUser"
  }
}
```

**Response:**
```json
{
  "auth": "your_pusher_key:signature_hash",
  "channel_data": "{\"user_id\":\"user_123\",\"user_info\":{\"username\":\"RobloxUser\"}}"
}
```

### Check Pusher Status

```http
GET /api/v1/roblox/pusher/status
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "connected": true,
  "channels_active": 5,
  "cluster": "us2",
  "app_id": "your_app_id"
}
```

## 🎯 Conversation Flow

### Start Conversation

```http
POST /api/v1/roblox/conversation/start
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "user_id": "user_123",
  "initial_message": "I want to create a math learning environment",
  "context": {
    "grade_level": 5,
    "subject": "mathematics",
    "learning_objectives": ["fractions", "decimals"]
  }
}
```

**Response:**
```json
{
  "session_id": "session_abc123",
  "current_stage": "greeting",
  "stage_number": 1,
  "total_stages": 8,
  "message": "Welcome to the ToolboxAI Educational Content Generator!",
  "pusher_channel": "private-roblox-conversation-session_abc123",
  "created_at": "2025-09-28T10:00:00Z"
}
```

### Process User Input

```http
POST /api/v1/roblox/conversation/input
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "session_id": "session_abc123",
  "user_input": "I want students to practice adding fractions",
  "metadata": {
    "input_type": "text",
    "timestamp": "2025-09-28T10:01:00Z"
  }
}
```

### Generate Content

```http
POST /api/v1/roblox/conversation/generate
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "session_id": "session_abc123",
  "requirements": {
    "environment_type": "classroom",
    "interactive_elements": ["quiz_board", "manipulatives"],
    "difficulty": "medium"
  }
}
```

**Response:**
```json
{
  "generation_id": "gen_xyz789",
  "project_id": "proj_456",
  "status": "in_progress",
  "estimated_time": 120,
  "pusher_channel": "private-roblox-generation-session_abc123"
}
```

## 🔧 Rojo Management

### Check Rojo Installation

```http
GET /api/v1/roblox/rojo/check
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "installed": true,
  "version": "7.5.1",
  "path": "/usr/local/bin/rojo",
  "default_port": 34872
}
```

### List Rojo Projects

```http
GET /api/v1/roblox/rojo/projects
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "projects": [
    {
      "project_id": "proj_456",
      "name": "math-environment",
      "path": "/tmp/rojo_projects/math-environment",
      "port": 34872,
      "status": "running",
      "created_at": "2025-09-28T10:00:00Z",
      "user_id": "user_123",
      "files_count": 42
    }
  ],
  "total": 1
}
```

## 🗂️ Roblox OAuth2 Flow

```http
POST https://apis.roblox.com/oauth/v1/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&client_id=your_client_id
&client_secret=your_client_secret
&code=authorization_code
&redirect_uri=http://localhost:64989/oauth/callback
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_here",
  "scope": "openid profile"
}
```

### Token Refresh

```http
POST https://apis.roblox.com/oauth/v1/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&client_id=your_client_id
&client_secret=your_client_secret
&refresh_token=refresh_token_here
```

## 🌐 Open Cloud API Endpoints

### Asset Management

#### Create Asset

```http
POST https://apis.roblox.com/cloud/v1/assets
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Educational Content",
  "description": "AI-generated educational content",
  "assetType": "Model",
  "file": "base64_encoded_file_data"
}
```

**Response:**
```json
{
  "id": "asset_id_here",
  "name": "Educational Content",
  "description": "AI-generated educational content",
  "assetType": "Model",
  "status": "Processing",
  "created": "2025-09-14T10:30:00Z",
  "updated": "2025-09-14T10:30:00Z"
}
```

#### Get Asset

```http
GET https://apis.roblox.com/cloud/v1/assets/{asset_id}
Authorization: Bearer {access_token}
```

#### Update Asset

```http
PATCH https://apis.roblox.com/cloud/v1/assets/{asset_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Updated Educational Content",
  "description": "Updated description"
}
```

#### Delete Asset

```http
DELETE https://apis.roblox.com/cloud/v1/assets/{asset_id}
Authorization: Bearer {access_token}
```

### Data Store Operations

#### Get Data

```http
GET https://apis.roblox.com/cloud/v1/data-stores/{datastore_name}/entries/{entry_key}
Authorization: Bearer {access_token}
X-Roblox-Entry-Version: {version}
```

**Response:**
```json
{
  "data": {
    "playerId": "123456789",
    "progress": 75,
    "achievements": ["first_quiz", "perfect_score"]
  },
  "version": "version_string_here"
}
```

#### Set Data

```http
POST https://apis.roblox.com/cloud/v1/data-stores/{datastore_name}/entries/{entry_key}
Authorization: Bearer {access_token}
Content-Type: application/json
X-Roblox-Entry-Version: {version}

{
  "playerId": "123456789",
  "progress": 80,
  "achievements": ["first_quiz", "perfect_score", "speed_learner"]
}
```

#### List Data Store Keys

```http
GET https://apis.roblox.com/cloud/v1/data-stores/{datastore_name}/entries
Authorization: Bearer {access_token}
X-Roblox-Entry-User-Ids: {user_id}
```

### Place Management

#### Get Place Details

```http
GET https://apis.roblox.com/cloud/v1/places/{place_id}
Authorization: Bearer {access_token}
```

#### Update Place

```http
PATCH https://apis.roblox.com/cloud/v1/places/{place_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Updated Educational Place",
  "description": "Updated description",
  "maxPlayers": 30
}
```

## 🎮 Plugin API Endpoints

### Content Generation

#### Generate Educational Content

```http
POST https://api.toolboxai.com/v2/roblox/generate-content
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "subject": "Mathematics",
  "gradeLevel": 5,
  "learningObjectives": [
    "Understand basic algebra",
    "Solve linear equations"
  ],
  "environmentType": "classroom",
  "includeQuiz": true,
  "maxQuestions": 10
}
```

**Response:**
```json
{
  "contentId": "content_12345",
  "status": "generated",
  "content": {
    "terrain": {
      "type": "classroom",
      "materials": ["concrete", "wood"],
      "lighting": "bright"
    },
    "objects": [
      {
        "type": "blackboard",
        "position": [0, 5, 0],
        "properties": {
          "text": "Welcome to Algebra!",
          "color": "black"
        }
      }
    ],
    "quiz": {
      "questions": [
        {
          "id": "q1",
          "text": "What is 2x + 3 = 7?",
          "options": ["x = 2", "x = 3", "x = 4", "x = 5"],
          "correct": 0,
          "points": 10
        }
      ]
    }
  },
  "generatedAt": "2025-09-14T10:30:00Z"
}
```

#### Apply Content to Game

```http
POST https://api.toolboxai.com/v2/roblox/apply-content
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "contentId": "content_12345",
  "placeId": "place_67890",
  "applyTerrain": true,
  "applyObjects": true,
  "applyQuiz": true
}
```

### Session Management

#### Create Session

```http
POST https://api.toolboxai.com/v2/roblox/sessions
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "contentId": "content_12345",
  "maxPlayers": 30,
  "settings": {
    "allowHints": true,
    "timeLimit": 3600,
    "difficulty": "medium"
  }
}
```

**Response:**
```json
{
  "sessionId": "session_abc123",
  "status": "active",
  "maxPlayers": 30,
  "currentPlayers": 0,
  "createdAt": "2025-09-14T10:30:00Z",
  "expiresAt": "2025-09-14T11:30:00Z"
}
```

#### Join Session

```http
POST https://api.toolboxai.com/v2/roblox/sessions/{session_id}/join
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "playerId": "player_12345",
  "playerName": "StudentName"
}
```

#### Leave Session

```http
POST https://api.toolboxai.com/v2/roblox/sessions/{session_id}/leave
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "playerId": "player_12345"
}
```

### Progress Tracking

#### Update Progress

```http
POST https://api.toolboxai.com/v2/roblox/progress
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "playerId": "player_12345",
  "sessionId": "session_abc123",
  "lessonId": "lesson_xyz789",
  "progress": 75,
  "score": 850,
  "achievements": ["first_quiz", "perfect_score"],
  "timestamp": "2025-09-14T10:45:00Z"
}
```

#### Get Player Progress

```http
GET https://api.toolboxai.com/v2/roblox/progress/{player_id}
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "playerId": "player_12345",
  "totalScore": 1250,
  "completedLessons": 5,
  "achievements": [
    {
      "id": "first_quiz",
      "name": "First Quiz",
      "unlockedAt": "2025-09-14T10:30:00Z"
    }
  ],
  "currentSession": {
    "sessionId": "session_abc123",
    "progress": 75,
    "timeSpent": 1800
  }
}
```

### Quiz System

#### Submit Quiz Answer

```http
POST https://api.toolboxai.com/v2/roblox/quiz/answer
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "playerId": "player_12345",
  "sessionId": "session_abc123",
  "questionId": "q1",
  "answer": "x = 2",
  "timestamp": "2025-09-14T10:45:00Z"
}
```

**Response:**
```json
{
  "correct": true,
  "points": 10,
  "explanation": "Great job! You correctly solved the equation.",
  "nextQuestion": {
    "id": "q2",
    "text": "What is 3x - 2 = 10?",
    "options": ["x = 4", "x = 3", "x = 5", "x = 6"]
  }
}
```

#### Get Quiz Results

```http
GET https://api.toolboxai.com/v2/roblox/quiz/{session_id}/results
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "sessionId": "session_abc123",
  "totalQuestions": 10,
  "playerResults": [
    {
      "playerId": "player_12345",
      "correctAnswers": 8,
      "totalScore": 80,
      "timeSpent": 300
    }
  ],
  "averageScore": 75,
  "completedAt": "2025-09-14T11:00:00Z"
}
```

## 🔌 WebSocket API

### Connection

```javascript
const ws = new WebSocket('wss://api.toolboxai.com/v2/roblox/ws');
```

### Authentication

```json
{
  "type": "auth",
  "token": "your_access_token",
  "clientType": "plugin"
}
```

### Content Generation Events

#### Request Content Generation

```json
{
  "type": "generate_content",
  "requestId": "req_12345",
  "data": {
    "subject": "Mathematics",
    "gradeLevel": 5,
    "learningObjectives": ["Understand basic algebra"]
  }
}
```

#### Content Generation Progress

```json
{
  "type": "generation_progress",
  "requestId": "req_12345",
  "progress": 75,
  "stage": "applying_terrain",
  "message": "Applying terrain changes..."
}
```

#### Content Generation Complete

```json
{
  "type": "generation_complete",
  "requestId": "req_12345",
  "contentId": "content_12345",
  "content": {
    "terrain": {...},
    "objects": [...],
    "quiz": {...}
  }
}
```

### Real-time Updates

#### Player Joined

```json
{
  "type": "player_joined",
  "sessionId": "session_abc123",
  "player": {
    "id": "player_12345",
    "name": "StudentName"
  }
}
```

#### Progress Updated

```json
{
  "type": "progress_updated",
  "sessionId": "session_abc123",
  "playerId": "player_12345",
  "progress": 80,
  "score": 900
}
```

## 📊 Analytics API

### Get Session Analytics

```http
GET https://api.toolboxai.com/v2/roblox/analytics/sessions/{session_id}
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "sessionId": "session_abc123",
  "duration": 3600,
  "totalPlayers": 25,
  "averageProgress": 78,
  "quizResults": {
    "totalQuestions": 10,
    "averageScore": 75,
    "completionRate": 85
  },
  "engagement": {
    "averageTimePerPlayer": 1800,
    "mostActiveTime": "10:30-11:00",
    "dropoffRate": 15
  }
}
```

### Get Player Analytics

```http
GET https://api.toolboxai.com/v2/roblox/analytics/players/{player_id}
Authorization: Bearer {access_token}
```

## 🚨 Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request is invalid",
    "details": {
      "field": "gradeLevel",
      "issue": "Must be between 1 and 12"
    },
    "timestamp": "2025-09-14T10:30:00Z",
    "requestId": "req_12345"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## 🔒 Rate Limiting

### Limits

- **Authentication**: 10 requests per minute
- **Content Generation**: 5 requests per minute
- **Data Operations**: 100 requests per minute
- **Analytics**: 20 requests per minute

### Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## 📝 SDK Examples

### Lua (Roblox Studio)

```lua
-- Initialize API client
local APIClient = require(script.APIClient)
local client = APIClient.new("your_access_token")

-- Generate content
local content = client:GenerateContent({
    subject = "Mathematics",
    gradeLevel = 5,
    learningObjectives = {"Understand basic algebra"}
})

-- Apply content
client:ApplyContent(content.id, game.PlaceId)
```

### JavaScript (Dashboard)

```javascript
// Initialize API client
const apiClient = new RobloxAPIClient('your_access_token');

// Generate content
const content = await apiClient.generateContent({
    subject: 'Mathematics',
    gradeLevel: 5,
    learningObjectives: ['Understand basic algebra']
});

// Apply content
await apiClient.applyContent(content.id, placeId);
```

### Python (Backend)

```python
from toolboxai.roblox import RobloxAPIClient

# Initialize client
client = RobloxAPIClient(access_token='your_access_token')

# Generate content
content = client.generate_content(
    subject='Mathematics',
    grade_level=5,
    learning_objectives=['Understand basic algebra']
)

# Apply content
client.apply_content(content.id, place_id)
```

## 🔒 Security

### Request Headers

All API requests must include:

```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
X-Request-ID: {unique_request_id}
X-Client-Version: 2.1.0
```

### Rate Limiting

- Default: 100 requests per minute per user
- Burst: 10 requests per second
- Headers returned:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Unix timestamp for rate limit reset

### IP Whitelisting

When enabled, only requests from whitelisted IPs are accepted:
- Development: `127.0.0.1`, `::1`
- Production: Configure via environment variables

### HMAC Signature (Optional)

For enhanced security, enable HMAC signatures:

```http
X-Signature: sha256={hmac_signature}
X-Timestamp: {unix_timestamp}
```

## 🚨 Error Responses

### Standard Error Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request parameters are invalid",
    "details": {
      "field": "session_id",
      "reason": "Session not found or expired"
    },
    "request_id": "req_abc123",
    "timestamp": "2025-09-28T10:00:00Z"
  }
}
```

### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Invalid request parameters |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Resource conflict (e.g., duplicate) |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

### OAuth2 Specific Errors

| Error Code | Description |
|------------|-------------|
| `invalid_request` | Missing required parameters |
| `invalid_client` | Client authentication failed |
| `invalid_grant` | Invalid authorization code or refresh token |
| `unauthorized_client` | Client not authorized for grant type |
| `unsupported_grant_type` | Grant type not supported |
| `invalid_scope` | Invalid or missing scope |

## 📊 Webhooks

### Configure Webhook

```http
POST /api/v1/roblox/webhooks
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "url": "https://your-domain.com/webhook",
  "events": [
    "generation.complete",
    "rojo.connected",
    "auth.revoked"
  ],
  "secret": "webhook_secret_key"
}
```

### Webhook Payload

```json
{
  "event": "generation.complete",
  "data": {
    "session_id": "session_abc123",
    "project_id": "proj_456",
    "files_generated": 42,
    "status": "success"
  },
  "timestamp": "2025-09-28T10:00:00Z",
  "signature": "sha256=..."
}
```

## 🔄 Pusher Events Reference

### Event Subscriptions

```javascript
// JavaScript/TypeScript Client
const pusher = new Pusher('your_key', {
  cluster: 'us2',
  auth: {
    endpoint: '/api/v1/roblox/pusher/auth',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
});

// Subscribe to conversation channel
const channel = pusher.subscribe(`private-roblox-conversation-${sessionId}`);

// Listen to events
channel.bind('stage-changed', (data) => {
  console.log('Stage:', data.stage, 'Progress:', data.progress);
});

channel.bind('generation-progress', (data) => {
  updateProgressBar(data.progress);
});

channel.bind('generation-complete', (data) => {
  console.log('Complete! Project:', data.project_id);
});

channel.bind('error-occurred', (data) => {
  console.error('Error:', data.error_message);
});
```

---

*Last Updated: 2025-09-28*
*Version: 2.1.0*
*API Version: v1*
