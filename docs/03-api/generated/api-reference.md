# API Reference

## Table of Contents

- [Authentication & User Management](#authentication--user-management)
- [Educational Content](#educational-content)
- [Roblox Integration](#roblox-integration)
- [AI & Agent Systems](#ai--agent-systems)
- [Analytics & Reporting](#analytics--reporting)
- [Organization Management](#organization-management)
- [Communication & Real-time](#communication--real-time)
- [System Features](#system-features)
- [Integration & Utilities](#integration--utilities)
- [Payment Processing](#payment-processing)

---

## Authentication & User Management

### Authentication (`/api/v1/auth`)

#### POST `/api/v1/auth/login`
Authenticate user and return JWT access token.

**Request Body:**
```json
{
  "email": "teacher@school.edu",
  "password": "Teacher123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "role": "teacher",
  "user": {
    "id": "123",
    "username": "jane_smith",
    "email": "teacher@school.edu",
    "displayName": "Jane Smith",
    "role": "teacher"
  }
}
```

**Authentication:** None required
**Rate Limit:** 10 requests/minute per IP

#### POST `/api/v1/auth/refresh`
Refresh an existing JWT token.

**Headers:**
```
Authorization: Bearer <current_token>
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "role": "teacher"
}
```

**Authentication:** JWT required
**Rate Limit:** 100 requests/minute

#### POST `/api/v1/auth/logout`
Logout and invalidate token.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

**Authentication:** JWT required
**Rate Limit:** 100 requests/minute

### User Management (`/api/v1/users`)

#### GET `/api/admin/stats/users`
Get user statistics for admin dashboard.

**Response:**
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

**Authentication:** Admin role required
**Rate Limit:** 1000 requests/minute

#### GET `/api/admin/health`
Get system health metrics.

**Response:**
```json
{
  "cpu_usage": 45.2,
  "memory_usage": 62.8,
  "disk_usage": 38.5,
  "api_latency": 125,
  "database_status": "healthy",
  "services": {
    "api": "operational",
    "database": "operational",
    "redis": "operational",
    "websocket": "operational",
    "roblox_bridge": "operational"
  },
  "uptime": "14d 3h 25m"
}
```

**Authentication:** Admin role required
**Rate Limit:** 1000 requests/minute

---

## Educational Content

### Enhanced Content Generation (`/api/v1/content`)

#### POST `/api/v1/content/generate`
Generate educational content using AI agents with SPARC framework integration.

**Request Body:**
```json
{
  "subject": "Science",
  "grade_level": "6-8",
  "content_type": "interactive_lesson",
  "learning_objectives": [
    "Understand the solar system",
    "Learn about planetary orbits",
    "Explore space exploration history"
  ],
  "environment_theme": "space_station",
  "difficulty": "medium",
  "duration_minutes": 45,
  "include_quiz": true,
  "personalization": {
    "learning_style": "visual",
    "previous_knowledge": "basic_astronomy"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "gen_abc123",
    "content_id": "content_456",
    "status": "generating",
    "progress": {
      "stage": "content_analysis",
      "progress_percent": 20,
      "estimated_completion": "2025-01-21T10:05:00Z"
    },
    "websocket_url": "ws://localhost:8009/ws/content/gen_abc123"
  },
  "message": "Content generation started",
  "metadata": {
    "timestamp": "2025-01-21T10:00:00Z",
    "request_id": "req_789"
  }
}
```

**Authentication:** Teacher or Admin role required
**Rate Limit:** 50 requests/hour per user

#### GET `/api/v1/content/generation/{session_id}/status`
Get content generation status and progress.

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "gen_abc123",
    "status": "completed",
    "progress": {
      "stage": "completed",
      "progress_percent": 100,
      "completed_at": "2025-01-21T10:05:30Z"
    },
    "generated_content": {
      "content_id": "content_456",
      "lesson_data": {
        "title": "Exploring the Solar System",
        "description": "Interactive journey through our solar system",
        "duration_minutes": 45,
        "sections": [...]
      },
      "quiz_data": {
        "questions": [...],
        "passing_score": 70
      },
      "environment_data": {
        "terrain": {...},
        "objects": [...],
        "scripts": {...}
      }
    }
  }
}
```

**Authentication:** JWT required
**Rate Limit:** 100 requests/minute

### Lessons (`/api/v1/lessons`)

#### GET `/api/v1/lessons`
Get lessons based on user role and filters.

**Query Parameters:**
- `limit` (int): Number of lessons to return (default: 20, max: 100)
- `offset` (int): Pagination offset (default: 0)
- `subject` (string): Filter by subject
- `grade_level` (string): Filter by grade level
- `status` (string): Filter by status (draft, published, archived)

**Response:**
```json
{
  "success": true,
  "data": {
    "lessons": [
      {
        "id": "lesson_123",
        "title": "Introduction to Photosynthesis",
        "subject": "Science",
        "grade_level": "6-8",
        "duration_minutes": 30,
        "status": "published",
        "created_at": "2025-01-20T10:00:00Z",
        "updated_at": "2025-01-21T09:00:00Z",
        "teacher": {
          "id": "teacher_456",
          "name": "Ms. Johnson"
        },
        "student_count": 25,
        "completion_rate": 85.5
      }
    ],
    "total": 42,
    "page": 1,
    "per_page": 20
  }
}
```

**Authentication:** JWT required
**Rate Limit:** 100 requests/minute

### Assessments (`/api/v1/assessments`)

#### POST `/api/v1/assessments`
Create a new assessment.

**Request Body:**
```json
{
  "title": "Solar System Quiz",
  "description": "Test your knowledge of planets and space",
  "lesson_id": "lesson_123",
  "questions": [
    {
      "type": "multiple_choice",
      "question": "Which planet is closest to the Sun?",
      "options": ["Mercury", "Venus", "Earth", "Mars"],
      "correct_answer": 0,
      "points": 10
    }
  ],
  "time_limit_minutes": 15,
  "passing_score": 70,
  "settings": {
    "shuffle_questions": true,
    "show_results_immediately": true,
    "allow_retakes": 1
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "assessment_id": "assessment_789",
    "title": "Solar System Quiz",
    "question_count": 10,
    "max_points": 100,
    "created_at": "2025-01-21T10:00:00Z"
  }
}
```

**Authentication:** Teacher or Admin role required
**Rate Limit:** 50 requests/hour

---

## Roblox Integration

### Roblox Core Integration (`/api/v1/roblox`)

#### POST `/api/v1/roblox/auth/initiate`
Initiate Roblox OAuth2 authentication flow.

**Request Body:**
```json
{
  "additional_scopes": ["universe-messaging-service:publish"]
}
```

**Response:**
```json
{
  "success": true,
  "authorization_url": "https://authorize.roblox.com/oauth/authorize?client_id=...",
  "state": "random_state_123",
  "expires_at": "2025-01-21T11:00:00Z"
}
```

**Authentication:** JWT required
**Rate Limit:** 10 requests/minute

#### GET `/api/v1/roblox/oauth/callback`
Handle Roblox OAuth2 callback.

**Query Parameters:**
- `code` (string): Authorization code from Roblox
- `state` (string): State parameter for CSRF protection

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "123456789",
    "username": "RobloxUser123",
    "access_token": "roblox_token_...",
    "token_type": "Bearer",
    "scope": ["openid", "profile"]
  }
}
```

**Authentication:** None (callback endpoint)
**Rate Limit:** 100 requests/minute

### Roblox Environment Generation (`/api/v1/roblox-environment`)

#### POST `/api/v1/roblox-environment/generate`
Generate 3D Roblox environment for educational content.

**Request Body:**
```json
{
  "content_id": "content_123",
  "environment_type": "space_station",
  "size": "medium",
  "features": {
    "terrain": true,
    "buildings": true,
    "interactive_objects": true,
    "npcs": true
  },
  "customizations": {
    "theme_color": "#0066cc",
    "lighting": "dramatic",
    "weather": "clear"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "environment_id": "env_456",
    "status": "generating",
    "scripts": {
      "server": "-- Server script content",
      "client": "-- Client script content",
      "shared": "-- Shared modules"
    },
    "assets": {
      "models": [...],
      "textures": [...],
      "sounds": [...]
    },
    "estimated_completion": "2025-01-21T10:03:00Z"
  }
}
```

**Authentication:** Teacher or Admin role required
**Rate Limit:** 20 requests/hour

---

## AI & Agent Systems

### AI Agent Orchestration (`/api/v1/ai-agents`)

#### POST `/api/v1/ai-agents/orchestrate`
Orchestrate multiple AI agents for complex tasks.

**Request Body:**
```json
{
  "task_type": "content_generation",
  "agents": [
    {
      "type": "content_agent",
      "config": {
        "subject": "Science",
        "complexity": "medium"
      }
    },
    {
      "type": "quiz_agent",
      "config": {
        "question_count": 10,
        "difficulty": "medium"
      }
    },
    {
      "type": "terrain_agent",
      "config": {
        "environment": "laboratory"
      }
    }
  ],
  "coordination": {
    "mode": "sequential",
    "dependencies": [
      {"agent": "content_agent", "depends_on": []},
      {"agent": "quiz_agent", "depends_on": ["content_agent"]},
      {"agent": "terrain_agent", "depends_on": ["content_agent"]}
    ]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "orchestration_id": "orch_789",
    "status": "running",
    "agents": [
      {
        "agent_id": "agent_content_123",
        "type": "content_agent",
        "status": "running",
        "progress": 45
      },
      {
        "agent_id": "agent_quiz_456",
        "type": "quiz_agent",
        "status": "waiting",
        "progress": 0
      }
    ],
    "estimated_completion": "2025-01-21T10:08:00Z"
  }
}
```

**Authentication:** Teacher or Admin role required
**Rate Limit:** 30 requests/hour

### AI Chat (`/api/v1/ai-chat`)

#### POST `/api/v1/ai-chat/conversation/start`
Start a new AI conversation session.

**Request Body:**
```json
{
  "initial_message": "Help me create a lesson plan about marine biology",
  "context": {
    "subject": "Science",
    "grade_level": "9-12",
    "lesson_duration": 50
  },
  "agent_type": "educational_assistant"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "conversation_id": "conv_abc123",
    "response": "I'd be happy to help you create a marine biology lesson plan! Let's start by identifying specific learning objectives...",
    "suggestions": [
      "Focus on ocean ecosystems",
      "Include interactive elements",
      "Add visual demonstrations"
    ],
    "metadata": {
      "response_time_ms": 1250,
      "tokens_used": 150
    }
  }
}
```

**Authentication:** JWT required
**Rate Limit:** 100 requests/hour

---

## Analytics & Reporting

### Analytics (`/api/v1/analytics`)

#### GET `/api/v1/analytics/dashboard`
Get comprehensive dashboard analytics.

**Query Parameters:**
- `time_range` (string): Time range for data (7d, 30d, 90d, 1y)
- `role` (string): Filter by user role

**Response:**
```json
{
  "success": true,
  "data": {
    "overview": {
      "total_students": 1324,
      "total_teachers": 87,
      "active_classes": 156,
      "content_generated": 2341
    },
    "engagement": {
      "daily_active_users": 342,
      "average_session_duration": 28.5,
      "completion_rate": 78.2,
      "quiz_participation": 89.1
    },
    "content_metrics": {
      "lessons_created": 423,
      "assessments_completed": 1567,
      "roblox_worlds_generated": 234,
      "ai_interactions": 5678
    },
    "performance": {
      "average_quiz_score": 82.3,
      "improvement_rate": 15.7,
      "time_to_completion": {
        "average_minutes": 22.4,
        "median_minutes": 18.2
      }
    }
  }
}
```

**Authentication:** Teacher or Admin role required
**Rate Limit:** 100 requests/minute

### Reports (`/api/v1/reports`)

#### POST `/api/v1/reports/generate`
Generate custom reports.

**Request Body:**
```json
{
  "report_type": "student_progress",
  "filters": {
    "class_id": "class_123",
    "date_range": {
      "start": "2025-01-01",
      "end": "2025-01-21"
    },
    "subjects": ["Science", "Mathematics"]
  },
  "format": "pdf",
  "include_charts": true,
  "delivery": {
    "method": "email",
    "recipients": ["teacher@school.edu"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "report_id": "report_456",
    "status": "generating",
    "estimated_completion": "2025-01-21T10:05:00Z",
    "download_url": null
  }
}
```

**Authentication:** Teacher or Admin role required
**Rate Limit:** 20 requests/hour

---

## Organization Management

### Classes (`/api/v1/classes`)

#### GET `/api/v1/classes`
Get classes based on user role.

**Query Parameters:**
- `limit` (int): Number of classes to return (default: 20, max: 100)
- `offset` (int): Pagination offset
- `subject` (string): Filter by subject
- `grade_level` (int): Filter by grade level

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "class_123",
      "name": "7th Grade Science",
      "subject": "Science",
      "grade_level": 7,
      "teacher": {
        "id": "teacher_456",
        "name": "Ms. Johnson",
        "email": "johnson@school.edu"
      },
      "student_count": 25,
      "created_at": "2025-01-15T10:00:00Z",
      "status": "active",
      "recent_activity": {
        "last_lesson": "2025-01-20T14:00:00Z",
        "assignments_pending": 3,
        "average_progress": 78.5
      }
    }
  ],
  "total": 12,
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 1
  }
}
```

**Authentication:** JWT required
**Rate Limit:** 100 requests/minute

#### POST `/api/v1/classes`
Create a new class.

**Request Body:**
```json
{
  "name": "8th Grade Physics",
  "subject": "Science",
  "grade_level": 8,
  "description": "Introduction to physics concepts",
  "schedule": {
    "days": ["Monday", "Wednesday", "Friday"],
    "time": "10:00",
    "duration_minutes": 50
  },
  "capacity": 30,
  "settings": {
    "allow_self_enrollment": false,
    "require_parent_approval": true,
    "enable_notifications": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "class_id": "class_789",
    "name": "8th Grade Physics",
    "join_code": "PHYS8G",
    "created_at": "2025-01-21T10:00:00Z"
  }
}
```

**Authentication:** Teacher or Admin role required
**Rate Limit:** 50 requests/hour

### Schools (`/api/v1/schools`)

#### GET `/api/v1/schools`
Get schools (admin only).

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "school_123",
      "name": "Lincoln Elementary",
      "district": "Springfield School District",
      "address": "123 Education St, Springfield, IL 62701",
      "principal": "Dr. Sarah Wilson",
      "student_count": 456,
      "teacher_count": 32,
      "status": "active",
      "subscription": {
        "plan": "premium",
        "expires_at": "2025-12-31T23:59:59Z"
      }
    }
  ]
}
```

**Authentication:** Admin role required
**Rate Limit:** 100 requests/minute

---

## Communication & Real-time

### Messages (`/api/v1/messages`)

#### GET `/api/v1/messages`
Get user messages.

**Query Parameters:**
- `limit` (int): Number of messages to return
- `unread_only` (bool): Show only unread messages
- `conversation_id` (string): Filter by conversation

**Response:**
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": "msg_123",
        "from": {
          "id": "user_456",
          "name": "Ms. Johnson",
          "role": "teacher"
        },
        "to": {
          "id": "user_789",
          "name": "Alex Student",
          "role": "student"
        },
        "subject": "Assignment Feedback",
        "content": "Great work on your solar system project!",
        "sent_at": "2025-01-21T09:30:00Z",
        "read_at": null,
        "priority": "normal"
      }
    ],
    "unread_count": 3,
    "total": 25
  }
}
```

**Authentication:** JWT required
**Rate Limit:** 100 requests/minute

### Pusher Authentication (`/api/v1/pusher`)

#### POST `/api/v1/pusher/auth`
Authenticate Pusher channel subscription.

**Request Body (Form Data):**
```
socket_id=123.456&channel_name=private-dashboard-updates
```

**Response:**
```json
{
  "auth": "app_key:signature",
  "channel_data": "{\"user_id\":\"123\",\"user_info\":{\"name\":\"Jane\"}}"
}
```

**Authentication:** JWT required for private/presence channels
**Rate Limit:** 1000 requests/minute

---

## System Features

### Gamification (`/api/v1/gamification`)

#### GET `/api/v1/gamification/achievements`
Get user achievements.

**Response:**
```json
{
  "success": true,
  "data": {
    "user_achievements": [
      {
        "id": "achievement_123",
        "title": "Quiz Master",
        "description": "Complete 10 quizzes with 90%+ score",
        "icon": "🏆",
        "earned_at": "2025-01-20T15:30:00Z",
        "points": 100,
        "rarity": "rare"
      }
    ],
    "available_achievements": [
      {
        "id": "achievement_456",
        "title": "Science Explorer",
        "description": "Complete 5 science lessons",
        "icon": "🔬",
        "points": 50,
        "progress": {
          "current": 3,
          "required": 5
        }
      }
    ],
    "total_points": 1250,
    "level": 8,
    "next_level_points": 1500
  }
}
```

**Authentication:** JWT required
**Rate Limit:** 100 requests/minute

### Dashboard (`/api/v1/dashboard`)

#### GET `/api/v1/dashboard/data`
Get role-specific dashboard data.

**Response (Teacher):**
```json
{
  "success": true,
  "data": {
    "overview": {
      "total_classes": 4,
      "total_students": 89,
      "pending_assignments": 12,
      "recent_activity_count": 23
    },
    "quick_stats": {
      "lessons_this_week": 8,
      "quizzes_completed": 45,
      "average_score": 82.3,
      "engagement_rate": 78.5
    },
    "recent_classes": [...],
    "pending_tasks": [...],
    "announcements": [...]
  }
}
```

**Authentication:** JWT required
**Rate Limit:** 100 requests/minute

---

## Integration & Utilities

### API Keys (`/api/v1/api-keys`)

#### GET `/api/v1/api-keys`
Get user's API keys.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "key_123",
      "name": "Roblox Plugin Key",
      "key_preview": "tbx_****_****_****_4f2a",
      "permissions": ["roblox:read", "content:generate"],
      "created_at": "2025-01-15T10:00:00Z",
      "last_used": "2025-01-21T09:45:00Z",
      "status": "active"
    }
  ]
}
```

**Authentication:** JWT required
**Rate Limit:** 100 requests/minute

#### POST `/api/v1/api-keys`
Create a new API key.

**Request Body:**
```json
{
  "name": "Mobile App Key",
  "permissions": ["content:read", "progress:read"],
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "key_456",
    "name": "Mobile App Key",
    "api_key": "tbx_1234567890abcdef1234567890abcdef",
    "permissions": ["content:read", "progress:read"],
    "created_at": "2025-01-21T10:00:00Z"
  },
  "message": "API key created successfully. Save this key securely - it won't be shown again."
}
```

**Authentication:** JWT required
**Rate Limit:** 10 requests/hour

---

## Payment Processing

### Stripe Checkout (`/api/v1/stripe/checkout`)

#### POST `/api/v1/stripe/checkout/session`
Create Stripe checkout session.

**Request Body:**
```json
{
  "price_id": "price_premium_monthly",
  "quantity": 1,
  "success_url": "https://app.toolboxai.com/success",
  "cancel_url": "https://app.toolboxai.com/cancel",
  "metadata": {
    "school_id": "school_123",
    "user_id": "user_456"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "cs_1234567890",
    "checkout_url": "https://checkout.stripe.com/pay/cs_1234567890"
  }
}
```

**Authentication:** Admin role required
**Rate Limit:** 50 requests/hour

### Stripe Webhooks (`/api/v1/payments/stripe`)

#### POST `/api/v1/payments/stripe/webhook`
Handle Stripe webhook events.

**Headers:**
```
Stripe-Signature: t=1642771200,v1=signature
```

**Request Body (Stripe Event):**
```json
{
  "id": "evt_1234567890",
  "object": "event",
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_1234567890",
      "amount_total": 2999,
      "currency": "usd",
      "metadata": {
        "school_id": "school_123"
      }
    }
  }
}
```

**Response:**
```json
{
  "received": true
}
```

**Authentication:** Stripe signature verification
**Rate Limit:** 1000 requests/minute

---

## WebSocket Endpoints

### Content Generation WebSocket (`/ws/content/{session_id}`)
Real-time content generation updates.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8009/ws/content/gen_abc123');
```

**Authentication:**
Send auth message after connection:
```json
{
  "type": "auth",
  "token": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Messages Received:**
```json
{
  "type": "progress_update",
  "data": {
    "session_id": "gen_abc123",
    "stage": "quiz_generation",
    "progress_percent": 75,
    "message": "Generating quiz questions..."
  }
}
```

### Roblox WebSocket (`/ws/roblox`)
Roblox environment synchronization.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8009/ws/roblox');
```

**Messages:**
```json
{
  "type": "environment_update",
  "data": {
    "environment_id": "env_456",
    "status": "ready",
    "scripts": { ... },
    "assets": { ... }
  }
}
```

---

## Error Handling

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `AUTHENTICATION_REQUIRED` | 401 | Valid JWT token required |
| `INSUFFICIENT_PERMISSIONS` | 403 | User role lacks required permissions |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource doesn't exist |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "grade_level",
      "issue": "Must be between 1 and 12"
    }
  },
  "metadata": {
    "timestamp": "2025-01-21T10:00:00Z",
    "request_id": "req_abc123",
    "trace_id": "trace_xyz789"
  }
}
```

---

*This API reference covers all 39 endpoint modules in the ToolBoxAI platform. For additional details, see the OpenAPI specification and authentication guide.*