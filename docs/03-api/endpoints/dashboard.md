# Dashboard Endpoints

## Overview

The Dashboard API provides role-based access to educational platform data, analytics, and management features. Different endpoints are available based on user roles (student, teacher, admin, parent).

## Base URL
```
http://127.0.0.1:8008
```

## Role-Based Dashboard Endpoints

### GET /dashboard/overview/{role}
Get dashboard overview data based on user role.

**Authentication:** Required (Bearer token)

**Parameters:**
- `role` (path): User role (`student`, `teacher`, `admin`, `parent`)

**Response for Student:**
```json
{
  "user_info": {
    "name": "John Doe",
    "grade_level": 7,
    "school": "Lincoln Middle School",
    "avatar_url": "https://example.com/avatar.jpg"
  },
  "current_courses": [
    {
      "id": "course_123",
      "name": "7th Grade Mathematics",
      "teacher": "Ms. Smith",
      "progress": 75,
      "next_assignment": {
        "title": "Algebra Quiz",
        "due_date": "2024-01-15T09:00:00Z"
      }
    }
  ],
  "recent_activities": [
    {
      "type": "lesson_completed",
      "title": "Linear Equations",
      "timestamp": "2024-01-10T14:30:00Z",
      "points_earned": 25
    }
  ],
  "achievements": [
    {
      "id": "math_master",
      "title": "Math Master",
      "description": "Completed 10 math lessons",
      "icon_url": "https://example.com/badges/math.png",
      "earned_at": "2024-01-10T16:00:00Z"
    }
  ],
  "weekly_stats": {
    "lessons_completed": 8,
    "time_spent_hours": 12.5,
    "xp_gained": 450,
    "assignments_submitted": 3
  }
}
```

**Response for Teacher:**
```json
{
  "user_info": {
    "name": "Jane Smith",
    "department": "Mathematics",
    "school": "Lincoln Middle School"
  },
  "classes": [
    {
      "id": "class_456",
      "name": "7th Grade Math - Period 3",
      "student_count": 28,
      "recent_activity": "2024-01-11T10:30:00Z",
      "avg_progress": 72
    }
  ],
  "pending_grading": [
    {
      "assignment_id": "assign_789",
      "title": "Algebra Quiz",
      "class": "7th Grade Math",
      "submissions": 25,
      "total_students": 28,
      "due_date": "2024-01-15T09:00:00Z"
    }
  ],
  "recent_content": [
    {
      "id": "content_101",
      "title": "Linear Equations in Roblox",
      "type": "lesson",
      "created_at": "2024-01-09T15:20:00Z",
      "usage_count": 42
    }
  ],
  "analytics_summary": {
    "total_students": 85,
    "avg_engagement": 78,
    "content_created": 12,
    "assignments_graded": 34
  }
}
```

**Response for Admin:**
```json
{
  "system_overview": {
    "total_users": 1250,
    "active_today": 342,
    "content_generated": 156,
    "system_health": "healthy"
  },
  "school_statistics": {
    "total_schools": 15,
    "active_classes": 89,
    "total_lessons": 2340,
    "avg_engagement": 81
  },
  "recent_activities": [
    {
      "type": "user_registered",
      "description": "5 new teacher accounts created",
      "timestamp": "2024-01-11T09:15:00Z"
    }
  ],
  "alerts": [
    {
      "type": "warning",
      "message": "High CPU usage on content generation service",
      "timestamp": "2024-01-11T11:30:00Z",
      "action_required": true
    }
  ],
  "performance_metrics": {
    "response_time_ms": 245,
    "uptime_percentage": 99.8,
    "error_rate": 0.02,
    "active_connections": 156
  }
}
```

### GET /dashboard/student
Get student-specific dashboard data.

**Authentication:** Required (Bearer token) - Student role

**Response:**
```json
{
  "current_lesson": {
    "id": "lesson_123",
    "title": "Introduction to Fractions",
    "progress": 60,
    "estimated_time_remaining": 15,
    "next_activity": "Practice Problems"
  },
  "assignments": {
    "due_soon": [
      {
        "id": "assign_456",
        "title": "Math Homework Ch. 5",
        "due_date": "2024-01-12T23:59:00Z",
        "subject": "Mathematics",
        "status": "not_started"
      }
    ],
    "recently_graded": [
      {
        "id": "assign_789",
        "title": "Science Lab Report",
        "grade": "A-",
        "points": 92,
        "feedback": "Excellent analysis of the experiment results!"
      }
    ]
  },
  "gamification": {
    "total_xp": 1250,
    "level": 8,
    "xp_to_next_level": 150,
    "current_streak": 5,
    "badges_earned": 12
  },
  "social": {
    "study_groups": [
      {
        "id": "group_101",
        "name": "Math Study Group",
        "members": 4,
        "next_session": "2024-01-13T15:00:00Z"
      }
    ],
    "peer_rankings": {
      "position": 15,
      "total_students": 85,
      "percentile": 82
    }
  }
}
```

### GET /dashboard/teacher
Get teacher-specific dashboard data.

**Authentication:** Required (Bearer token) - Teacher role

**Response:**
```json
{
  "classes_overview": [
    {
      "id": "class_201",
      "name": "7th Grade Mathematics",
      "period": "3rd Period",
      "students": 28,
      "engagement_score": 85,
      "avg_grade": "B+",
      "recent_activity": "2024-01-11T14:20:00Z"
    }
  ],
  "grading_queue": {
    "urgent": [
      {
        "assignment_id": "assign_301",
        "title": "Algebra Test",
        "submissions": 25,
        "overdue_hours": 2
      }
    ],
    "pending": [
      {
        "assignment_id": "assign_302",
        "title": "Homework Ch. 6",
        "submissions": 22,
        "due_in_hours": 18
      }
    ]
  },
  "content_analytics": {
    "most_popular": [
      {
        "content_id": "content_401",
        "title": "Fractions in Roblox City",
        "views": 156,
        "avg_rating": 4.7
      }
    ],
    "recently_created": [
      {
        "content_id": "content_402",
        "title": "Geometry Garden",
        "created_at": "2024-01-10T09:30:00Z",
        "status": "published"
      }
    ]
  },
  "student_insights": {
    "struggling_students": [
      {
        "student_id": "student_501",
        "name": "Alice Johnson",
        "avg_grade": "D+",
        "missing_assignments": 3,
        "last_active": "2024-01-09T16:45:00Z"
      }
    ],
    "top_performers": [
      {
        "student_id": "student_502",
        "name": "Bob Smith",
        "avg_grade": "A",
        "streak_days": 15,
        "extra_credit": 25
      }
    ]
  }
}
```

### GET /dashboard/admin
Get admin-specific dashboard data.

**Authentication:** Required (Bearer token) - Admin role

**Response:**
```json
{
  "system_status": {
    "services": {
      "api": "healthy",
      "database": "healthy",
      "ai_agents": "warning",
      "content_generation": "healthy"
    },
    "uptime": "99.8%",
    "last_restart": "2024-01-05T08:00:00Z"
  },
  "user_management": {
    "total_users": 1250,
    "new_registrations_today": 8,
    "active_users_24h": 342,
    "user_distribution": {
      "students": 980,
      "teachers": 245,
      "admins": 15,
      "parents": 10
    }
  },
  "content_statistics": {
    "total_content": 2340,
    "generated_today": 23,
    "most_used_subjects": [
      {"subject": "Mathematics", "count": 856},
      {"subject": "Science", "count": 542}
    ],
    "avg_generation_time": "2.3 minutes"
  },
  "school_management": {
    "total_schools": 15,
    "active_schools": 12,
    "pending_approvals": 3,
    "license_usage": {
      "used": 1180,
      "total": 1500,
      "utilization": 78.7
    }
  },
  "alerts": [
    {
      "id": "alert_701",
      "type": "performance",
      "severity": "medium",
      "message": "AI agent response time above threshold",
      "timestamp": "2024-01-11T10:45:00Z",
      "acknowledged": false
    }
  ]
}
```

### GET /dashboard/parent
Get parent-specific dashboard data.

**Authentication:** Required (Bearer token) - Parent role

**Response:**
```json
{
  "children": [
    {
      "student_id": "student_801",
      "name": "Emma Wilson",
      "grade_level": 6,
      "school": "Roosevelt Elementary",
      "overall_progress": 78,
      "recent_grades": [
        {
          "subject": "Mathematics",
          "assignment": "Fractions Quiz",
          "grade": "B+",
          "date": "2024-01-10T14:30:00Z"
        }
      ],
      "attendance": {
        "days_present": 18,
        "days_total": 20,
        "percentage": 90
      },
      "upcoming_events": [
        {
          "type": "parent_conference",
          "date": "2024-01-18T15:00:00Z",
          "teacher": "Ms. Johnson"
        }
      ]
    }
  ],
  "communications": [
    {
      "from": "Ms. Johnson",
      "subject": "Emma's Progress Update",
      "preview": "Emma is doing excellent work in mathematics...",
      "timestamp": "2024-01-10T16:20:00Z",
      "read": false
    }
  ],
  "school_announcements": [
    {
      "title": "Science Fair Registration",
      "message": "Registration for the annual science fair opens next week",
      "date": "2024-01-15T09:00:00Z",
      "priority": "normal"
    }
  ]
}
```

## General Dashboard Endpoints

### GET /dashboard/metrics
Get general metrics for the dashboard.

**Authentication:** Required (Bearer token)

**Response:**
```json
{
  "user_metrics": {
    "login_frequency": "daily",
    "avg_session_duration": "45 minutes",
    "favorite_subjects": ["Mathematics", "Science"],
    "completion_rate": 82
  },
  "engagement_metrics": {
    "lessons_per_week": 8.5,
    "assignments_submitted": 15,
    "forum_posts": 3,
    "peer_interactions": 12
  },
  "learning_analytics": {
    "mastery_levels": {
      "Mathematics": 75,
      "Science": 68,
      "History": 82
    },
    "learning_pace": "above_average",
    "preferred_learning_style": "visual"
  }
}
```

### GET /dashboard/notifications
Get user notifications.

**Authentication:** Required (Bearer token)

**Response:**
```json
[
  {
    "id": "notif_901",
    "type": "assignment",
    "title": "New Assignment Posted",
    "message": "Your teacher has posted a new math assignment",
    "timestamp": "2024-01-11T09:15:00Z",
    "read": false,
    "action_url": "/assignments/assign_123",
    "priority": "normal"
  },
  {
    "id": "notif_902",
    "type": "grade",
    "title": "Grade Updated",
    "message": "Your science quiz has been graded",
    "timestamp": "2024-01-10T15:30:00Z",
    "read": true,
    "data": {
      "assignment_id": "assign_456",
      "grade": "A-",
      "points": 92
    }
  }
]
```

### GET /dashboard/quick-stats
Get quick statistics for the dashboard header.

**Authentication:** Required (Bearer token)

**Response:**
```json
{
  "unread_notifications": 3,
  "pending_assignments": 2,
  "current_streak": 7,
  "today_xp": 75,
  "online_friends": 8,
  "active_lessons": 1,
  "upcoming_deadlines": [
    {
      "title": "Math Quiz",
      "due_in_hours": 18,
      "priority": "high"
    }
  ]
}
```

## Integration Examples

### React Dashboard Hook
```typescript
import { useState, useEffect } from 'react';

interface DashboardData {
  [key: string]: any;
}

export function useDashboard(role: string) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/dashboard/overview/${role}`, {
          headers: {
            'Authorization': `Bearer ${getToken()}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch dashboard data');
        }

        const dashboardData = await response.json();
        setData(dashboardData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [role]);

  return { data, loading, error };
}
```

### Python Dashboard Client
```python
import requests
from typing import Dict, Any, Optional

class DashboardAPI:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def get_overview(self, role: str) -> Dict[str, Any]:
        """Get dashboard overview for specific role."""
        response = requests.get(
            f"{self.base_url}/dashboard/overview/{role}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_metrics(self) -> Dict[str, Any]:
        """Get dashboard metrics."""
        response = requests.get(
            f"{self.base_url}/dashboard/metrics",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_notifications(self) -> list:
        """Get user notifications."""
        response = requests.get(
            f"{self.base_url}/dashboard/notifications",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_quick_stats(self) -> Dict[str, Any]:
        """Get quick statistics."""
        response = requests.get(
            f"{self.base_url}/dashboard/quick-stats",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage example
dashboard = DashboardAPI("http://127.0.0.1:8008", "your_token")

# Get student dashboard
student_data = dashboard.get_overview("student")
print(f"Current XP: {student_data['gamification']['total_xp']}")

# Get notifications
notifications = dashboard.get_notifications()
unread_count = len([n for n in notifications if not n['read']])
print(f"Unread notifications: {unread_count}")
```

## Real-time Updates

Dashboard data can be updated in real-time using Pusher channels:

### JavaScript Real-time Integration
```javascript
// Subscribe to dashboard updates
const dashboardChannel = pusher.subscribe('dashboard-updates');

dashboardChannel.bind('notification_update', (data) => {
  updateNotificationCount(data.count);
});

dashboardChannel.bind('stats_update', (data) => {
  updateQuickStats(data);
});

// Subscribe to user-specific updates
const userChannel = pusher.subscribe(`private-user-${userId}`);

userChannel.bind('grade_posted', (data) => {
  showGradeNotification(data);
  refreshDashboard();
});
```

## Caching and Performance

### Client-side Caching
```typescript
class DashboardCache {
  private cache = new Map<string, { data: any; expiry: number }>();
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  set(key: string, data: any): void {
    this.cache.set(key, {
      data,
      expiry: Date.now() + this.CACHE_DURATION
    });
  }

  get(key: string): any | null {
    const entry = this.cache.get(key);
    if (!entry || Date.now() > entry.expiry) {
      this.cache.delete(key);
      return null;
    }
    return entry.data;
  }

  clear(): void {
    this.cache.clear();
  }
}
```

### Polling Strategy
```typescript
// Implement smart polling for dashboard updates
export function useDashboardPolling(role: string, interval: number = 30000) {
  const [data, setData] = useState(null);

  useEffect(() => {
    const pollData = async () => {
      try {
        const response = await fetch(`/dashboard/overview/${role}`);
        const newData = await response.json();
        setData(newData);
      } catch (error) {
        console.error('Polling failed:', error);
      }
    };

    // Initial fetch
    pollData();

    // Set up polling
    const intervalId = setInterval(pollData, interval);

    return () => clearInterval(intervalId);
  }, [role, interval]);

  return data;
}
```

## Error Handling

### Common Error Responses

#### 403 Forbidden - Insufficient Role
```json
{
  "detail": "Access denied. Required role: teacher",
  "error_code": "INSUFFICIENT_ROLE",
  "current_role": "student"
}
```

#### 404 Not Found - Invalid Role
```json
{
  "detail": "Invalid role specified",
  "error_code": "INVALID_ROLE",
  "valid_roles": ["student", "teacher", "admin", "parent"]
}
```

## Performance Considerations

### Data Optimization
- Dashboard endpoints return paginated results where applicable
- Use query parameters to limit data scope
- Implement client-side caching for frequently accessed data
- Use real-time updates to minimize polling

### Rate Limiting
- Dashboard endpoints: 60 requests per minute per user
- Quick stats endpoint: 120 requests per minute per user
- Notifications endpoint: 30 requests per minute per user