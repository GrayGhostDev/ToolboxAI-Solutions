# ToolBoxAI Solutions API Reference

## Overview

This document provides comprehensive documentation for the 10 most critical API endpoints in the ToolBoxAI Solutions educational platform. The platform is a Roblox-integrated educational system with AI capabilities for content generation, student management, and real-time collaboration.

**Base URL**: `http://127.0.0.1:8008`
**API Version**: v1
**Documentation Version**: 1.0.0
**Last Updated**: January 19, 2025

## Authentication

All endpoints require JWT authentication via the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

Obtain tokens through the login endpoint. Tokens expire after 30 minutes by default.

## Rate Limiting

- **General endpoints**: 100 requests per minute
- **Content generation**: 5 requests per minute
- **Authentication**: 10 requests per minute
- **Burst limit**: 10 requests per second

## Error Handling

Standard HTTP status codes are used. Error responses follow this format:

```json
{
  "status": "error",
  "message": "Error description",
  "detail": "Detailed error information",
  "timestamp": "2025-01-19T10:30:00Z",
  "request_id": "req_abc123"
}
```

## Content Type

All requests and responses use `application/json` unless otherwise specified.

---

## 1. POST /api/v1/auth/login

**Description**: Authenticate users and obtain JWT access tokens. Supports both username and email login.

**Authentication**: None required
**Rate Limit**: 10 requests per minute

### Request Body

```json
{
  "username": "string (optional)",
  "email": "string (optional)",
  "password": "string (required, min: 1, max: 5000)"
}
```

**Note**: Either `username` or `email` must be provided.

### Request Example

```json
{
  "email": "jane.smith@school.edu",
  "password": "Teacher123!"
}
```

### Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "role": "teacher",
  "user": {
    "id": 1,
    "username": "jane_smith",
    "email": "jane.smith@school.edu",
    "displayName": "jane_smith",
    "role": "teacher"
  }
}
```

### Error Responses

- **401 Unauthorized**: Invalid credentials
- **422 Unprocessable Entity**: Validation errors
- **429 Too Many Requests**: Rate limit exceeded

### Demo Accounts

```json
{
  "admin": {
    "email": "admin@toolboxai.com",
    "password": "Admin123!"
  },
  "teacher": {
    "email": "jane.smith@school.edu",
    "password": "Teacher123!"
  },
  "student": {
    "email": "alex.johnson@student.edu",
    "password": "Student123!"
  }
}
```

---

## 2. GET /api/v1/users/profile

**Description**: Retrieve user profile information based on role. Returns role-specific data and statistics.

**Authentication**: Required
**Roles**: All

### Query Parameters

None required. Data is filtered based on authenticated user's role.

### Response Examples

#### Teacher Profile (200 OK)
```json
{
  "total_users": 1523,
  "active_users": 1245,
  "new_users_today": 23,
  "new_users_week": 145,
  "by_role": {
    "teachers": 87,
    "students": 1324,
    "parents": 98,
    "admins": 14
  },
  "growth_rate": 12.5,
  "active_sessions": 342
}
```

#### Student Profile (200 OK)
```json
{
  "current_xp": 3250,
  "current_level": 12,
  "xp_to_next_level": 750,
  "total_xp_for_next": 4000,
  "rank_in_class": 5,
  "rank_in_school": 42,
  "recent_xp_gains": [
    {
      "source": "Quiz completion",
      "xp": 100,
      "date": "2025-01-19T08:30:00Z"
    }
  ]
}
```

### Error Responses

- **401 Unauthorized**: Invalid or missing token
- **403 Forbidden**: Insufficient permissions

---

## 3. POST /api/v1/ai-chat/generate

**Description**: Generate AI responses for educational content creation with streaming support. Integrates with Anthropic Claude and OpenAI for intelligent conversation.

**Authentication**: Required
**Roles**: Teacher, Admin
**Rate Limit**: 5 requests per minute

### Request Body

```json
{
  "message": "string (required, min: 1, max: 5000)",
  "attachments": [
    {
      "type": "string",
      "url": "string",
      "name": "string"
    }
  ]
}
```

### Request Example

```json
{
  "message": "Create a 5th grade solar system lesson with interactive Roblox elements",
  "attachments": []
}
```

### Response (200 OK - Streaming)

Returns Server-Sent Events (SSE) in `application/x-ndjson` format:

```json
{"type": "start", "id": "msg_abc123", "timestamp": "2025-01-19T10:30:00Z"}
{"type": "token", "content": "I'll"}
{"type": "token", "content": " help"}
{"type": "token", "content": " you"}
{"type": "complete", "message": {...}}
```

### Complete Message Response

```json
{
  "type": "complete",
  "message": {
    "id": "msg_abc123",
    "role": "assistant",
    "content": "🎯 GOT IT! I'll create an amazing 5th grade solar system exploration experience...",
    "timestamp": "2025-01-19T10:30:00Z",
    "metadata": {
      "generated": true,
      "streaming": true
    }
  }
}
```

### Error Responses

- **403 Forbidden**: Only teachers and admins can generate content
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: AI service unavailable

### Integration Notes

- Uses Anthropic Claude Opus/Sonnet models
- Fallback to OpenAI GPT-4o if Anthropic unavailable
- Context-aware conversation memory
- Automatic completion after 3-4 exchanges
- Supports creative delegation ("you choose")

---

## 4. POST /api/v1/roblox/game/create

**Description**: Create new educational game instances in Roblox with specified configuration and templates.

**Authentication**: Required
**Roles**: Teacher, Admin
**Rate Limit**: 10 requests per minute

### Request Body

```json
{
  "title": "string (required, min: 3, max: 100)",
  "description": "string (optional, max: 500)",
  "subject": "string (required)",
  "grade_level": "integer (required, min: 1, max: 12)",
  "max_players": "integer (optional, default: 30, min: 1, max: 50)",
  "template_id": "string (optional)",
  "settings": {
    "enable_voice_chat": "boolean",
    "difficulty": "string"
  }
}
```

### Request Example

```json
{
  "title": "Solar System Explorer",
  "description": "Interactive space exploration game",
  "subject": "Science",
  "grade_level": 7,
  "max_players": 25,
  "template_id": "space_station",
  "settings": {
    "enable_voice_chat": false,
    "difficulty": "medium"
  }
}
```

### Response (201 Created)

```json
{
  "game_id": "game_abc123456789",
  "title": "Solar System Explorer",
  "description": "Interactive space exploration game",
  "subject": "Science",
  "grade_level": 7,
  "status": "creating",
  "roblox_place_id": "place_12345678",
  "roblox_universe_id": "8505376973",
  "max_players": 25,
  "current_players": 0,
  "created_by": "teacher@school.edu",
  "created_at": "2025-01-19T10:30:00Z",
  "updated_at": "2025-01-19T10:30:00Z",
  "settings": {
    "enable_voice_chat": false,
    "difficulty": "medium"
  },
  "join_url": "https://www.roblox.com/games/place_12345678/"
}
```

### Background Processing

Game setup occurs asynchronously. Monitor status via WebSocket or polling:

```javascript
// WebSocket updates
ws://127.0.0.1:8008/api/v1/roblox/ws/game/{game_id}

// Polling endpoint
GET /api/v1/roblox/game/{game_id}
```

### Error Responses

- **403 Forbidden**: Only teachers and admins can create games
- **422 Unprocessable Entity**: Validation errors
- **500 Internal Server Error**: Game creation failed

---

## 5. POST /api/v1/roblox/content/generate

**Description**: Generate AI-powered educational content including lessons, quizzes, terrain, and scripts for Roblox environments.

**Authentication**: Required
**Roles**: Teacher, Admin
**Rate Limit**: 5 requests per minute

### Request Body

```json
{
  "content_type": "lesson|quiz|activity|terrain|script",
  "subject": "string (required)",
  "grade_level": "integer (required, min: 1, max: 12)",
  "learning_objectives": ["string", "..."],
  "environment_type": "string (required)",
  "difficulty": "easy|medium|hard (default: medium)",
  "duration_minutes": "integer (default: 30, min: 5, max: 120)",
  "include_quiz": "boolean (default: true)",
  "custom_requirements": "string (optional, max: 1000)"
}
```

### Request Example

```json
{
  "content_type": "lesson",
  "subject": "Science",
  "grade_level": 5,
  "learning_objectives": [
    "Identify planets in correct order from sun",
    "Understand basic properties of each planet",
    "Explain concept of orbital periods"
  ],
  "environment_type": "space_station",
  "difficulty": "medium",
  "duration_minutes": 45,
  "include_quiz": true,
  "custom_requirements": "Include interactive planet scale comparison"
}
```

### Response (202 Accepted)

```json
{
  "content_id": "content_xyz789012345",
  "content_type": "lesson",
  "status": "generating",
  "generated_at": "2025-01-19T10:30:00Z",
  "metadata": {
    "estimated_time_minutes": 8
  }
}
```

### Complete Content Response

After generation completes (monitor via WebSocket):

```json
{
  "content_id": "content_xyz789012345",
  "content_type": "lesson",
  "status": "completed",
  "lesson_content": {
    "title": "Solar System Exploration",
    "objectives": ["Identify planets...", "Understand properties..."],
    "content": "Welcome to our solar system adventure...",
    "activities": ["Planet Size Comparison", "Orbital Speed Challenge"]
  },
  "quiz_content": {
    "questions": [
      {
        "question": "Which planet is closest to the Sun?",
        "type": "multiple_choice",
        "options": ["Mercury", "Venus", "Earth", "Mars"],
        "correct_answer": "Mercury"
      }
    ]
  },
  "terrain_config": {
    "environment_type": "space_station",
    "size": "large",
    "features": ["observation_deck", "planet_models", "control_room"]
  },
  "metadata": {
    "generation_time_seconds": 480,
    "ai_model": "claude-opus-4",
    "tokens_used": 3247
  }
}
```

### Error Responses

- **403 Forbidden**: Only teachers and admins can generate content
- **422 Unprocessable Entity**: Invalid learning objectives or parameters
- **429 Too Many Requests**: Rate limit exceeded

---

## 6. GET /api/v1/lessons

**Description**: Retrieve lessons with role-based filtering and pagination. Returns different data structures based on user role.

**Authentication**: Required
**Roles**: All

### Query Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `class_id` | integer | Filter by class ID | None |
| `subject` | string | Filter by subject | None |
| `limit` | integer | Items per page (max: 100) | 20 |
| `offset` | integer | Items to skip | 0 |

### Request Example

```
GET /api/v1/lessons?class_id=123&subject=Mathematics&limit=10&offset=0
```

### Response Examples

#### Teacher Response (200 OK)
```json
[
  {
    "id": 1,
    "title": "Introduction to Algebra",
    "class_name": "Mathematics 101",
    "subject": "Mathematics",
    "duration": 45,
    "difficulty": "beginner",
    "completion_count": 22,
    "total_students": 28,
    "status": "published",
    "created_at": "2025-01-01T09:00:00Z"
  },
  {
    "id": 2,
    "title": "Solving Linear Equations",
    "class_name": "Mathematics 101",
    "subject": "Mathematics",
    "duration": 50,
    "difficulty": "intermediate",
    "completion_count": 18,
    "total_students": 28,
    "status": "published",
    "created_at": "2025-01-03T09:00:00Z"
  }
]
```

#### Student Response (200 OK)
```json
[
  {
    "id": 1,
    "title": "Introduction to Algebra",
    "class_name": "Mathematics 101",
    "subject": "Mathematics",
    "duration": 45,
    "difficulty": "beginner",
    "progress": 100,
    "completed": true,
    "last_accessed": "2025-01-06T14:30:00Z",
    "xp_reward": 50
  },
  {
    "id": 2,
    "title": "Solving Linear Equations",
    "class_name": "Mathematics 101",
    "subject": "Mathematics",
    "duration": 50,
    "difficulty": "intermediate",
    "progress": 65,
    "completed": false,
    "last_accessed": "2025-01-07T10:15:00Z",
    "xp_reward": 75
  }
]
```

### Error Responses

- **401 Unauthorized**: Invalid or missing token
- **422 Unprocessable Entity**: Invalid query parameters

---

## 7. POST /api/v1/assessments/submit

**Description**: Submit student assessment responses with automatic scoring and progress tracking.

**Authentication**: Required
**Roles**: Student only

### URL Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `assessment_id` | integer | Assessment identifier |

### Request Body

```json
{
  "answers": {
    "1": "Mercury",
    "2": "Earth rotates on its axis",
    "3": ["Mars", "Jupiter"]
  },
  "score": "number (optional)",
  "time_spent": "integer (minutes)",
  "metadata": {
    "browser": "string",
    "completion_percentage": "number"
  }
}
```

### Request Example

```json
{
  "answers": {
    "1": "Mercury",
    "2": "The Earth rotates on its axis once every 24 hours",
    "3": ["Mars", "Jupiter", "Saturn"]
  },
  "score": 85,
  "time_spent": 23,
  "metadata": {
    "browser": "Chrome",
    "completion_percentage": 100
  }
}
```

### Response (200 OK)

```json
{
  "submission_id": "sub_abc123",
  "assessment_id": 456,
  "student_id": "student_xyz789",
  "score": 85,
  "max_score": 100,
  "percentage": 85.0,
  "completed_at": "2025-01-19T11:45:00Z",
  "time_spent_minutes": 23,
  "attempts_used": 1,
  "max_attempts": 2,
  "status": "completed",
  "feedback": {
    "overall": "Good work! You demonstrated strong understanding of planetary science.",
    "areas_for_improvement": ["Review orbital mechanics", "Study asteroid belt location"]
  },
  "question_feedback": [
    {
      "question_id": 1,
      "correct": true,
      "points_earned": 10,
      "points_possible": 10
    },
    {
      "question_id": 2,
      "correct": true,
      "points_earned": 15,
      "points_possible": 15
    }
  ]
}
```

### Error Responses

- **400 Bad Request**: Maximum attempts exceeded
- **403 Forbidden**: Only students can submit assessments
- **404 Not Found**: Assessment not found or not accessible
- **422 Unprocessable Entity**: Invalid submission data

### Submission Rules

- Students can only submit their own assessments
- Respects `max_attempts` limit per assessment
- Automatic scoring for multiple choice questions
- Manual grading required for essay/open-ended responses
- Progress tracking and XP rewards calculated

---

## 8. GET /api/v1/classes

**Description**: Retrieve class information with role-based access control and student enrollment data.

**Authentication**: Required
**Roles**: All

### Query Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `limit` | integer | Items per page (max: 100) | 20 |
| `offset` | integer | Items to skip | 0 |
| `subject` | string | Filter by subject | None |
| `grade_level` | integer | Filter by grade level | None |

### Request Example

```
GET /api/v1/classes?subject=Mathematics&grade_level=7&limit=5
```

### Response Examples

#### Teacher Response (200 OK)
```json
[
  {
    "id": "class_abc123",
    "name": "Mathematics 101",
    "teacher_id": "teacher_xyz789",
    "grade_level": 7,
    "subject": "Mathematics",
    "room": "Room 203",
    "schedule": "Mon/Wed/Fri 10:00 AM",
    "description": "Introduction to algebraic concepts",
    "start_time": "10:00:00",
    "end_time": "10:50:00",
    "max_students": 30,
    "is_active": true,
    "student_count": 28,
    "average_xp": 0,
    "created_at": "2024-09-01T08:00:00Z",
    "updated_at": "2025-01-19T10:30:00Z"
  }
]
```

#### Student Response (200 OK)
```json
[
  {
    "id": "class_abc123",
    "name": "Mathematics 101",
    "teacher_id": "teacher_xyz789",
    "grade_level": 7,
    "subject": "Mathematics",
    "room": "Room 203",
    "schedule": "Mon/Wed/Fri 10:00 AM",
    "description": "Introduction to algebraic concepts",
    "start_time": "10:00:00",
    "end_time": "10:50:00",
    "max_students": 30,
    "is_active": true,
    "student_count": 0,
    "average_xp": 0,
    "created_at": "2024-09-01T08:00:00Z",
    "updated_at": "2025-01-19T10:30:00Z"
  }
]
```

### Access Control

- **Teachers**: See classes they teach with student counts
- **Students**: See classes they're enrolled in
- **Admins**: See all classes with comprehensive metrics
- **Parents**: See classes their children are enrolled in

### Error Responses

- **401 Unauthorized**: Invalid or missing token
- **422 Unprocessable Entity**: Invalid query parameters

---

## 9. POST /api/v1/pusher/auth

**Description**: Authenticate Pusher Channels subscriptions for real-time features. Required for private and presence channels.

**Authentication**: Required
**Roles**: All

### Request Body

```json
{
  "socket_id": "string (required)",
  "channel_name": "string (required)"
}
```

### Request Example

```json
{
  "socket_id": "1234.5678",
  "channel_name": "private-user-123"
}
```

### Response (200 OK)

#### Private Channel Response
```json
{
  "auth": "user123:signature_hash_here"
}
```

#### Presence Channel Response
```json
{
  "auth": "user123:signature_hash_here",
  "channel_data": "{\"user_id\":\"user123\",\"user_info\":{\"name\":\"John Doe\",\"role\":\"teacher\"}}"
}
```

### Channel Types

#### Public Channels
- `dashboard-updates` - General dashboard notifications
- `content-generation` - Content creation progress
- `public-announcements` - System-wide announcements

#### Private Channels (require auth)
- `private-user-{user_id}` - Personal notifications
- `private-class-{class_id}` - Class-specific updates
- `private-admin-alerts` - Admin-only notifications

#### Presence Channels (require auth + user data)
- `presence-game-{game_id}` - Live game participants
- `presence-class-{class_id}` - Active class members

### Error Responses

- **401 Unauthorized**: Invalid or missing token
- **403 Forbidden**: Access denied to channel
- **422 Unprocessable Entity**: Invalid socket_id or channel_name

### Integration Example

```javascript
// Frontend Pusher integration
const pusher = new Pusher('your-pusher-key', {
  cluster: 'us2',
  authEndpoint: '/api/v1/pusher/auth',
  auth: {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
});

const channel = pusher.subscribe('private-user-123');
channel.bind('notification', (data) => {
  console.log('Received notification:', data);
});
```

---

## 10. GET /api/v1/dashboard/stats

**Description**: Retrieve comprehensive dashboard statistics and metrics based on user role. Provides real-time data for dashboard widgets.

**Authentication**: Required
**Roles**: All

### Query Parameters

None required. Data is filtered based on authenticated user's role.

### Response Examples

#### Teacher Dashboard (200 OK)
```json
{
  "timestamp": "2025-01-19T10:30:00Z",
  "user": {
    "id": "teacher_123",
    "name": "jane_smith",
    "role": "teacher",
    "lastLogin": "2025-01-19T08:00:00Z"
  },
  "stats": {
    "totalStudents": 32,
    "activeClasses": 4,
    "assignmentsDue": 7,
    "averageGrade": 85.5,
    "lessonsToday": 3,
    "pendingGrading": 12
  },
  "recentActivity": [
    {
      "id": 1,
      "type": "submission",
      "student": "Alex Johnson",
      "assignment": "Math Problem Set 3",
      "time": "2 hours ago",
      "status": "submitted"
    }
  ],
  "upcomingClasses": [
    {
      "id": 1,
      "name": "Mathematics 101",
      "time": "10:00 AM",
      "room": "Room 203",
      "students": 28
    }
  ],
  "performanceData": {
    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
    "datasets": [
      {
        "label": "Class Average",
        "data": [82, 85, 83, 88, 86]
      }
    ]
  }
}
```

#### Student Dashboard (200 OK)
```json
{
  "timestamp": "2025-01-19T10:30:00Z",
  "user": {
    "id": "student_456",
    "name": "alex_johnson",
    "role": "student",
    "lastLogin": "2025-01-19T08:30:00Z"
  },
  "stats": {
    "xp": 1250,
    "level": 12,
    "nextLevelXP": 1500,
    "completedMissions": 24,
    "currentStreak": 7,
    "rank": 5,
    "totalPoints": 890,
    "badges": 8
  },
  "todaySchedule": [
    {
      "id": 1,
      "subject": "Mathematics",
      "time": "9:00 AM",
      "teacher": "Mr. Smith",
      "room": "Room 203"
    }
  ],
  "assignments": [
    {
      "id": 1,
      "title": "Math Problem Set 3",
      "subject": "Mathematics",
      "dueDate": "2025-01-12",
      "status": "in_progress",
      "progress": 60
    }
  ],
  "achievements": [
    {
      "id": 1,
      "name": "Fast Learner",
      "description": "Complete 5 lessons in one day",
      "icon": "⚡",
      "unlockedAt": "2025-01-05"
    }
  ],
  "leaderboard": [
    {"rank": 1, "name": "Sarah Wilson", "xp": 1850, "level": 15},
    {"rank": 5, "name": "You", "xp": 1250, "level": 12, "isCurrentUser": true}
  ]
}
```

#### Admin Dashboard (200 OK)
```json
{
  "timestamp": "2025-01-19T10:30:00Z",
  "user": {
    "id": "admin_789",
    "name": "admin",
    "role": "admin",
    "lastLogin": "2025-01-19T07:00:00Z"
  },
  "stats": {
    "totalUsers": 1523,
    "activeUsers": 1245,
    "totalSchools": 12,
    "totalClasses": 156,
    "systemHealth": 98.5,
    "storageUsed": 67.3,
    "apiCalls": 45231,
    "uptime": "99.98%"
  },
  "systemMetrics": {
    "cpu": 45.2,
    "memory": 62.8,
    "disk": 67.3,
    "network": 23.5,
    "activeConnections": 234,
    "requestsPerMinute": 1250
  },
  "recentEvents": [
    {
      "id": 1,
      "type": "user_registration",
      "message": "New teacher registered: Emily Brown",
      "time": "1 hour ago",
      "severity": "info"
    }
  ],
  "userGrowth": {
    "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "datasets": [
      {
        "label": "Students",
        "data": [850, 920, 980, 1050, 1120, 1200]
      }
    ]
  }
}
```

### Error Responses

- **401 Unauthorized**: Invalid or missing token
- **500 Internal Server Error**: Database connection issues

### Caching

Dashboard stats are cached for 5 minutes to improve performance. Real-time updates are provided via Pusher channels:

- `dashboard-updates` - General updates
- `private-user-{user_id}` - Personal metrics
- `private-admin-metrics` - Admin system metrics

---

## WebSocket Endpoints

### Real-time Game Updates
```
ws://127.0.0.1:8008/api/v1/roblox/ws/game/{game_id}
```

**Events**:
- `game_state` - Initial game state
- `player_joined` - Student joins game
- `player_left` - Student leaves game
- `student_action` - Student performs action
- `content_updated` - New content deployed

### AI Chat Streaming
```
ws://127.0.0.1:8008/api/v1/ai-chat/ws/{conversation_id}
```

**Events**:
- `stream_start` - Response generation begins
- `stream_token` - Incremental response token
- `stream_end` - Response generation complete

## SDKs and Examples

### JavaScript/TypeScript
```javascript
// API Client Setup
const client = axios.create({
  baseURL: 'http://127.0.0.1:8008/api/v1',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

// Login Example
const login = async (email, password) => {
  const response = await client.post('/auth/login', {
    email,
    password
  });
  return response.data;
};

// Create Game Example
const createGame = async (gameData) => {
  const response = await client.post('/roblox/game/create', gameData);
  return response.data;
};
```

### Python
```python
import requests

class ToolBoxAIClient:
    def __init__(self, base_url="http://127.0.0.1:8008/api/v1"):
        self.base_url = base_url
        self.token = None

    def login(self, email, password):
        response = requests.post(f"{self.base_url}/auth/login", json={
            "email": email,
            "password": password
        })
        data = response.json()
        self.token = data["access_token"]
        return data

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get_dashboard_stats(self):
        response = requests.get(
            f"{self.base_url}/dashboard/stats",
            headers=self.get_headers()
        )
        return response.json()
```

## Changelog

### Version 1.0.0 (2025-01-19)
- Initial API documentation
- 10 critical endpoints documented
- Authentication and rate limiting specifications
- WebSocket endpoint documentation
- SDK examples added

## Support

For API support and questions:
- **Documentation**: `/docs/03-api/`
- **Issues**: Create GitHub issue with `api` label
- **Rate Limit**: Contact admin for increase requests

---

*Last updated: January 19, 2025*
*API Version: 1.0.0*
*Documentation maintained by: ToolBoxAI Development Team*