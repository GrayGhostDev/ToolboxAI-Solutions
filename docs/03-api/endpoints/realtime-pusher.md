# Realtime Communication (Pusher) Endpoints

## Overview

ToolBoxAI uses Pusher Channels for real-time communication between the server and clients. This enables live updates for content generation, user notifications, dashboard updates, and collaborative features.

## Base URL
```
http://127.0.0.1:8008
```

## Pusher Configuration

### Connection Details
- **Pusher Key:** Configured via `VITE_PUSHER_KEY` environment variable
- **Cluster:** Configured via `VITE_PUSHER_CLUSTER` environment variable
- **Auth Endpoint:** `/pusher/auth`
- **Webhook Endpoint:** `/pusher/webhook`

## Authentication Endpoints

### POST /pusher/auth
Authenticate client for private/presence channels.

**Authentication:** Required (Bearer token)

**Request Body:**
```json
{
  "socket_id": "123456.789012",
  "channel_name": "private-user-12345"
}
```

**Response:**
```json
{
  "auth": "1234567890abcdef:signature_here",
  "channel_data": "{\"user_id\":\"12345\",\"user_info\":{\"name\":\"John Doe\",\"role\":\"student\"}}"
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8008/pusher/auth" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "socket_id": "123456.789012",
    "channel_name": "private-user-12345"
  }'
```

### POST /pusher/webhook
Receive webhooks from Pusher (internal endpoint).

**Authentication:** Webhook signature validation

**Request Body:**
```json
{
  "time_ms": 1234567890123,
  "events": [
    {
      "name": "channel_occupied",
      "channel": "presence-classroom-101",
      "data": {...}
    }
  ]
}
```

## Trigger Events

### POST /realtime/trigger
Manually trigger events to Pusher channels (admin only).

**Authentication:** Required (Bearer token) - Admin role

**Request Body:**
```json
{
  "channel": "dashboard-updates",
  "event": "notification",
  "data": {
    "type": "success",
    "message": "System update completed",
    "timestamp": "2024-01-01T12:00:00Z"
  },
  "socket_id": "123456.789012"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Event triggered successfully"
}
```

## Channel Types and Events

### Public Channels

#### dashboard-updates
Global dashboard notifications and system announcements.

**Events:**
- `system_notification` - System-wide announcements
- `maintenance_alert` - Scheduled maintenance notifications
- `feature_update` - New feature announcements

**Event Data Example:**
```json
{
  "type": "info|success|warning|error",
  "title": "System Update",
  "message": "New features have been deployed",
  "timestamp": "2024-01-01T12:00:00Z",
  "action_url": "/features/new",
  "expires_at": "2024-01-02T12:00:00Z"
}
```

#### content-generation
Content generation progress and status updates.

**Events:**
- `generation_started` - Content generation initiated
- `progress_update` - Generation progress updates
- `generation_completed` - Content generation finished
- `generation_failed` - Generation error occurred

**Event Data Example:**
```json
{
  "content_id": "content_12345",
  "user_id": "user_67890",
  "progress": 75,
  "stage": "generating_scripts",
  "estimated_completion": "2024-01-01T12:05:00Z",
  "error": null
}
```

#### agent-status
AI agent system status and activity monitoring.

**Events:**
- `agent_started` - Agent began processing
- `agent_completed` - Agent finished task
- `agent_error` - Agent encountered error
- `system_health` - Overall system health update

**Event Data Example:**
```json
{
  "agent_id": "content_agent_001",
  "agent_type": "content_generation",
  "status": "active|idle|error",
  "task_id": "task_12345",
  "performance_metrics": {
    "cpu_usage": 45,
    "memory_usage": 67,
    "tasks_completed": 123
  }
}
```

### Private Channels

#### private-user-{user_id}
User-specific notifications and updates.

**Events:**
- `personal_notification` - Direct user notifications
- `progress_update` - Personal progress updates
- `assignment_due` - Assignment deadline reminders
- `grade_posted` - New grade notifications

**Event Data Example:**
```json
{
  "notification_id": "notif_12345",
  "type": "grade|assignment|message|system",
  "title": "New Grade Posted",
  "message": "Your math quiz has been graded",
  "data": {
    "assignment_id": "assign_67890",
    "grade": "85%",
    "feedback": "Good work on problem solving!"
  },
  "read": false,
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### private-class-{class_id}
Class-specific updates for teachers and students.

**Events:**
- `class_announcement` - Teacher announcements
- `assignment_posted` - New assignments
- `student_joined` - Student enrollment
- `lesson_started` - Live lesson beginning

### Presence Channels

#### presence-classroom-{class_id}
Real-time classroom presence for active lessons.

**Events:**
- `user_joined` - Student/teacher joined classroom
- `user_left` - User left classroom
- `activity_update` - User activity in lesson
- `collaboration_event` - Collaborative activities

**Presence Data:**
```json
{
  "user_id": "12345",
  "name": "John Doe",
  "role": "student|teacher",
  "avatar_url": "https://example.com/avatar.jpg",
  "status": "active|away|busy",
  "current_activity": "solving_problem_3"
}
```

#### presence-lesson-{lesson_id}
Individual lesson presence tracking.

**Events:**
- `progress_shared` - Student progress updates
- `help_requested` - Student needs assistance
- `collaboration_started` - Group work initiated
- `assessment_submitted` - Quiz/assignment submission

## Client Integration

### JavaScript/TypeScript Integration

```typescript
import Pusher from 'pusher-js';

interface PusherConfig {
  key: string;
  cluster: string;
  authEndpoint: string;
  authHeaders: { [key: string]: string };
}

class ToolBoxAIPusher {
  private pusher: Pusher;
  private channels: { [key: string]: Pusher.Channel } = {};

  constructor(config: PusherConfig) {
    this.pusher = new Pusher(config.key, {
      cluster: config.cluster,
      authEndpoint: config.authEndpoint,
      auth: {
        headers: config.authHeaders
      }
    });

    // Enable debugging in development
    if (process.env.NODE_ENV === 'development') {
      Pusher.logToConsole = true;
    }
  }

  // Subscribe to public channel
  subscribeToPublic(channelName: string): Pusher.Channel {
    if (this.channels[channelName]) {
      return this.channels[channelName];
    }

    const channel = this.pusher.subscribe(channelName);
    this.channels[channelName] = channel;
    return channel;
  }

  // Subscribe to private channel
  subscribeToPrivate(channelName: string): Pusher.Channel {
    const privateChannelName = `private-${channelName}`;
    if (this.channels[privateChannelName]) {
      return this.channels[privateChannelName];
    }

    const channel = this.pusher.subscribe(privateChannelName);
    this.channels[privateChannelName] = channel;
    return channel;
  }

  // Subscribe to presence channel
  subscribeToPresence(channelName: string): Pusher.PresenceChannel {
    const presenceChannelName = `presence-${channelName}`;
    if (this.channels[presenceChannelName]) {
      return this.channels[presenceChannelName] as Pusher.PresenceChannel;
    }

    const channel = this.pusher.subscribe(presenceChannelName) as Pusher.PresenceChannel;
    this.channels[presenceChannelName] = channel;
    return channel;
  }

  // Unsubscribe from channel
  unsubscribe(channelName: string): void {
    if (this.channels[channelName]) {
      this.pusher.unsubscribe(channelName);
      delete this.channels[channelName];
    }
  }

  // Disconnect from Pusher
  disconnect(): void {
    this.pusher.disconnect();
    this.channels = {};
  }
}

// Usage example
const pusherClient = new ToolBoxAIPusher({
  key: process.env.VITE_PUSHER_KEY!,
  cluster: process.env.VITE_PUSHER_CLUSTER!,
  authEndpoint: 'http://127.0.0.1:8008/pusher/auth',
  authHeaders: {
    'Authorization': `Bearer ${getAuthToken()}`
  }
});

// Subscribe to content generation updates
const contentChannel = pusherClient.subscribeToPublic('content-generation');
contentChannel.bind('generation_started', (data) => {
  console.log('Content generation started:', data);
});

contentChannel.bind('progress_update', (data) => {
  updateProgressBar(data.progress);
});

contentChannel.bind('generation_completed', (data) => {
  showCompletionNotification(data);
});

// Subscribe to user notifications
const userChannel = pusherClient.subscribeToPrivate(`user-${userId}`);
userChannel.bind('personal_notification', (data) => {
  showNotification(data);
});

// Subscribe to classroom presence
const classroomChannel = pusherClient.subscribeToPresence(`classroom-${classId}`);
classroomChannel.bind('pusher:subscription_succeeded', (members) => {
  updateOnlineUsers(members);
});

classroomChannel.bind('pusher:member_added', (member) => {
  addUserToList(member);
});

classroomChannel.bind('pusher:member_removed', (member) => {
  removeUserFromList(member);
});
```

### React Hook Example

```typescript
import { useEffect, useState } from 'react';
import { pusherClient } from './pusher-client';

interface NotificationData {
  id: string;
  type: string;
  title: string;
  message: string;
  timestamp: string;
}

export function useRealtimeNotifications(userId: string) {
  const [notifications, setNotifications] = useState<NotificationData[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Subscribe to user notifications
    const channel = pusherClient.subscribeToPrivate(`user-${userId}`);

    channel.bind('pusher:subscription_succeeded', () => {
      setConnected(true);
    });

    channel.bind('personal_notification', (data: NotificationData) => {
      setNotifications(prev => [data, ...prev]);
    });

    // Cleanup
    return () => {
      pusherClient.unsubscribe(`private-user-${userId}`);
      setConnected(false);
    };
  }, [userId]);

  return { notifications, connected };
}

export function useContentGeneration(contentId?: string) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'idle' | 'generating' | 'completed' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const channel = pusherClient.subscribeToPublic('content-generation');

    channel.bind('generation_started', (data) => {
      if (!contentId || data.content_id === contentId) {
        setStatus('generating');
        setProgress(0);
        setError(null);
      }
    });

    channel.bind('progress_update', (data) => {
      if (!contentId || data.content_id === contentId) {
        setProgress(data.progress);
      }
    });

    channel.bind('generation_completed', (data) => {
      if (!contentId || data.content_id === contentId) {
        setStatus('completed');
        setProgress(100);
      }
    });

    channel.bind('generation_failed', (data) => {
      if (!contentId || data.content_id === contentId) {
        setStatus('error');
        setError(data.error);
      }
    });

    return () => {
      pusherClient.unsubscribe('content-generation');
    };
  }, [contentId]);

  return { progress, status, error };
}
```

### Python Integration

```python
import pusher
import json
from typing import Dict, Any, Callable

class ToolBoxAIPusherClient:
    def __init__(self, pusher_config: Dict[str, str]):
        self.pusher_client = pusher.Pusher(
            app_id=pusher_config['app_id'],
            key=pusher_config['key'],
            secret=pusher_config['secret'],
            cluster=pusher_config['cluster'],
            ssl=True
        )

    def trigger_event(
        self,
        channel: str,
        event: str,
        data: Dict[str, Any],
        socket_id: str = None
    ) -> bool:
        """Trigger an event on a Pusher channel."""
        try:
            result = self.pusher_client.trigger(
                channel,
                event,
                data,
                socket_id
            )
            return result['status'] == 200
        except Exception as e:
            print(f"Failed to trigger event: {e}")
            return False

    def notify_user(self, user_id: str, notification: Dict[str, Any]) -> bool:
        """Send notification to specific user."""
        return self.trigger_event(
            f"private-user-{user_id}",
            "personal_notification",
            notification
        )

    def broadcast_system_message(self, message: Dict[str, Any]) -> bool:
        """Broadcast system-wide message."""
        return self.trigger_event(
            "dashboard-updates",
            "system_notification",
            message
        )

    def update_content_progress(
        self,
        content_id: str,
        progress: int,
        stage: str
    ) -> bool:
        """Update content generation progress."""
        return self.trigger_event(
            "content-generation",
            "progress_update",
            {
                "content_id": content_id,
                "progress": progress,
                "stage": stage
            }
        )

# Usage example
pusher_client = ToolBoxAIPusherClient({
    'app_id': 'your_app_id',
    'key': 'your_key',
    'secret': 'your_secret',
    'cluster': 'your_cluster'
})

# Notify user of new grade
pusher_client.notify_user('user_12345', {
    'type': 'grade',
    'title': 'New Grade Posted',
    'message': 'Your math quiz has been graded',
    'data': {
        'assignment_id': 'assign_67890',
        'grade': '85%'
    }
})

# Update content generation progress
pusher_client.update_content_progress(
    'content_12345',
    75,
    'generating_scripts'
)
```

## Security Considerations

### Authentication
- Private channels require authentication via `/pusher/auth`
- Auth endpoint validates JWT tokens
- User permissions verified for channel access

### Channel Security
- Private channels: `private-*` prefix
- Presence channels: `presence-*` prefix
- Public channels: No authentication required

### Rate Limiting
- Connection limits: 100 concurrent connections per user
- Event rate limits: 1000 events per minute per channel
- Authentication rate limits: 10 auth requests per minute per user

## Error Handling

### Connection Errors
```javascript
pusher.connection.bind('error', (error) => {
  console.error('Pusher connection error:', error);
  // Implement retry logic
});

pusher.connection.bind('disconnected', () => {
  console.log('Pusher disconnected');
  // Update UI to show offline status
});
```

### Subscription Errors
```javascript
channel.bind('pusher:subscription_error', (error) => {
  console.error('Subscription error:', error);
  // Handle authentication failures
});
```

### Event Handling Errors
```javascript
channel.bind('pusher:error', (error) => {
  console.error('Channel error:', error);
  // Handle event processing errors
});
```

## Monitoring and Debugging

### Debug Mode
```javascript
// Enable debug logging
Pusher.logToConsole = true;

// Custom logging
pusher.connection.bind('state_change', (states) => {
  console.log(`Connection state: ${states.previous} → ${states.current}`);
});
```

### Performance Monitoring
- Track connection latency
- Monitor event delivery rates
- Log subscription success/failure rates
- Monitor channel member counts

### Webhook Processing
The `/pusher/webhook` endpoint processes events for:
- Channel occupancy tracking
- Member join/leave events
- Connection statistics
- Security incident logging

## Migration from Socket.IO

### Key Differences
- Pusher uses channels instead of rooms
- Authentication handled via HTTP endpoint
- Built-in presence channel support
- Better scaling and reliability

### Migration Steps
1. Replace Socket.IO client with Pusher client
2. Update event names and data structures
3. Implement new authentication flow
4. Update server-side event triggers
5. Test channel subscriptions and presence

### Compatibility Layer
A compatibility layer is maintained for gradual migration:
```javascript
// Legacy WebSocket endpoints still available
const ws = new WebSocket('ws://127.0.0.1:8008/ws/content');
```

## Best Practices

### Connection Management
- Reuse Pusher instances across components
- Implement reconnection logic
- Handle network state changes
- Clean up subscriptions on unmount

### Event Naming
- Use clear, descriptive event names
- Follow consistent naming conventions
- Include action type in event name
- Version events when structure changes

### Data Structure
- Keep event data lightweight
- Include timestamp and correlation IDs
- Use consistent data schemas
- Validate event data on both ends

### Performance
- Batch related events when possible
- Use appropriate channel types
- Implement client-side caching
- Monitor connection and event metrics