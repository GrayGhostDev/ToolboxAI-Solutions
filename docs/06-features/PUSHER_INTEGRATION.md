# Pusher Channels Integration

**Last Updated:** November 9, 2025
**Status:** ✅ Fully Integrated and Configured
**Service:** Real-time WebSocket communication via Pusher Channels

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Configuration](#configuration)
3. [Architecture](#architecture)
4. [Channels & Events](#channels--events)
5. [Authentication](#authentication)
6. [Usage Examples](#usage-examples)
7. [Frontend Integration](#frontend-integration)
8. [Testing](#testing)
9. [Monitoring](#monitoring)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## Overview

ToolBoxAI uses **Pusher Channels** for all real-time communication features, replacing traditional WebSocket servers. Pusher provides:

- ✅ **Managed WebSocket Infrastructure** - No server maintenance required
- ✅ **Global Edge Network** - Low latency worldwide
- ✅ **Automatic Fallback** - HTTP polling when WebSockets unavailable
- ✅ **Presence Detection** - Track who's online
- ✅ **Message History** - Retrieve recent messages
- ✅ **RBAC Integration** - Role-based channel access

### Why Pusher?

| Feature | Self-Hosted WebSocket | Pusher Channels |
|---------|----------------------|-----------------|
| Setup Complexity | High | Low |
| Scaling | Manual | Automatic |
| Global Distribution | Complex | Built-in |
| Fallback Support | Manual | Automatic |
| Connection Limits | Server dependent | 100 (free) - 1M+ (paid) |
| Message Rate | Server dependent | 200k/day (free) - unlimited (paid) |
| Maintenance | Required | Managed |

---

## Configuration

### Backend Configuration

**Location:** `/apps/backend/core/config.py`

```python
# Environment variables
PUSHER_ENABLED=true                    # Enable/disable Pusher
PUSHER_APP_ID=2050003                  # Your Pusher app ID
PUSHER_KEY=your_public_key             # Public key (safe to expose)
PUSHER_SECRET=your_secret_key          # Private key (keep secure!)
PUSHER_CLUSTER=us2                     # Geographic cluster
PUSHER_SSL=true                        # Use TLS (recommended)
```

**Available Clusters:**
- `us2` - United States (Oregon)
- `us3` - United States (Ohio)
- `eu` - Europe (Ireland)
- `ap1` - Asia Pacific (Singapore)
- `ap2` - Asia Pacific (Mumbai)
- `ap3` - Asia Pacific (Tokyo)
- `ap4` - Asia Pacific (Sydney)

### Frontend Configuration

**Location:** `/apps/dashboard/.env`

```bash
# Must match backend configuration
VITE_PUSHER_KEY=your_public_key
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=/api/v1/pusher/auth
```

### Obtaining Credentials

1. **Sign up** at [https://pusher.com](https://pusher.com)
2. **Create app** named "ToolBoxAI-Development" or "ToolBoxAI-Production"
3. **Copy credentials** from App Keys section:
   - App ID
   - Key (public)
   - Secret (private)
   - Cluster

4. **Update configuration**:
   ```bash
   # Backend
   cp .env.example .env
   # Edit PUSHER_* variables

   # Frontend
   cd apps/dashboard
   cp .env.example .env
   # Edit VITE_PUSHER_* variables
   ```

5. **Enable Pusher**:
   ```bash
   PUSHER_ENABLED=true
   ```

---

## Architecture

### Service Components

```
┌─────────────────────────────────────────────────┐
│           Pusher Channels Cloud                 │
│  ┌──────────────────────────────────────────┐  │
│  │  Channel: public-dashboard               │  │
│  │  Channel: public-notifications           │  │
│  │  Channel: private-admin                  │  │
│  │  Channel: private-teacher                │  │
│  │  Channel: private-student                │  │
│  │  Channel: presence-classroom-{id}        │  │
│  │  Channel: agent-{agent_id}               │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
         ▲                           │
         │                           │
    ┌────┴────┐                 ┌────▼────┐
    │         │                 │         │
┌───▼─────────▼───┐       ┌─────▼─────────▼───┐
│   Dashboard      │       │   Backend API      │
│   (React)        │       │   (FastAPI)        │
│                  │       │                    │
│  - Pusher Client │       │  - PusherService   │
│  - Subscribe     │       │  - Trigger Events  │
│  - Listen Events │       │  - Authenticate    │
└──────────────────┘       └────────────────────┘
```

### Backend Services

**1. PusherService** (`/apps/backend/services/pusher.py`)
- Core Pusher client wrapper
- Event triggering
- Channel authentication
- Webhook validation

**2. PusherRealtimeService** (`/apps/backend/services/pusher_realtime.py`)
- High-level real-time API
- RBAC enforcement
- User presence tracking
- Subscription management

**3. Health Check** (`/apps/backend/api/routers/health.py`)
- Pusher status monitoring
- Connection verification
- Metrics collection

---

## Channels & Events

### Channel Types

#### 1. Public Channels
**Prefix:** `public-`
**Authentication:** None required
**Usage:** Broadcast to all connected clients

```python
# Backend
from apps.backend.services.pusher import trigger_event

trigger_event(
    channel="public-dashboard",
    event="system-update",
    data={"message": "System maintenance in 10 minutes"}
)
```

```javascript
// Frontend
const pusher = new Pusher(PUSHER_KEY, { cluster: PUSHER_CLUSTER });
const channel = pusher.subscribe('public-dashboard');
channel.bind('system-update', (data) => {
    console.log('System update:', data.message);
});
```

#### 2. Private Channels
**Prefix:** `private-`
**Authentication:** Required (JWT or session)
**Usage:** User-specific or role-based communication

```python
# Backend
trigger_event(
    channel="private-teacher",
    event="new-assignment",
    data={"assignment_id": "123", "title": "Quiz 1"}
)
```

```javascript
// Frontend (auth handled automatically)
const channel = pusher.subscribe('private-teacher');
channel.bind('new-assignment', (data) => {
    showNotification(`New assignment: ${data.title}`);
});
```

#### 3. Presence Channels
**Prefix:** `presence-`
**Authentication:** Required + user info
**Usage:** Track who's online, see member list

```python
# Backend authentication endpoint
@router.post("/pusher/auth")
async def pusher_auth(request: PusherAuthRequest, user: User = Depends(get_current_user)):
    from apps.backend.services.pusher import authenticate_channel

    auth = authenticate_channel(
        socket_id=request.socket_id,
        channel_name=request.channel_name,
        user_id=str(user.id),
        user_info={
            "name": user.name,
            "role": user.role,
            "avatar": user.avatar_url
        }
    )
    return auth
```

```javascript
// Frontend
const channel = pusher.subscribe('presence-classroom-101');

channel.bind('pusher:subscription_succeeded', (members) => {
    console.log(`${members.count} users online`);
    members.each((member) => {
        console.log(member.id, member.info.name);
    });
});

channel.bind('pusher:member_added', (member) => {
    console.log(`${member.info.name} joined`);
});

channel.bind('pusher:member_removed', (member) => {
    console.log(`${member.info.name} left`);
});
```

### Pre-Configured Channels

| Channel Name | Type | Purpose | Required Role |
|--------------|------|---------|---------------|
| `public-dashboard` | Public | General dashboard updates | None |
| `public-notifications` | Public | System notifications | None |
| `private-admin` | Private | Admin-only events | Admin |
| `private-teacher` | Private | Teacher-specific updates | Teacher |
| `private-student` | Private | Student-specific updates | Student |
| `presence-classroom-{id}` | Presence | Classroom activity | Student |
| `agent-{agent_id}` | Private | AI agent status | Admin |
| `agent-status` | Public | Agent system status | None |
| `agent-tasks` | Private | Agent task updates | Teacher |
| `agent-metrics` | Private | Agent metrics | Admin |
| `system-health` | Private | System health updates | Admin |

### Pre-Configured Events

**Agent Events:**
```python
AGENT_EVENTS = {
    "agent_started": "agent.started",
    "agent_stopped": "agent.stopped",
    "agent_idle": "agent.idle",
    "agent_busy": "agent.busy",
    "agent_error": "agent.error",
    "task_created": "task.created",
    "task_started": "task.started",
    "task_completed": "task.completed",
    "task_failed": "task.failed",
    "metrics_updated": "metrics.updated",
    "health_updated": "health.updated",
}
```

---

## Authentication

### Private Channel Authentication

**Backend Endpoint:** `/api/v1/pusher/auth`

```python
# apps/backend/api/routers/realtime.py
from apps.backend.services.pusher import authenticate_channel

@router.post("/pusher/auth")
async def pusher_auth(
    socket_id: str = Form(...),
    channel_name: str = Form(...),
    user: User = Depends(get_current_user)
):
    """Authenticate private/presence channel subscription"""

    # Check if user has access to this channel
    if not _check_channel_access(channel_name, user.role):
        raise HTTPException(403, "Access denied to this channel")

    # Generate authentication signature
    auth = authenticate_channel(
        socket_id=socket_id,
        channel_name=channel_name,
        user_id=str(user.id),
        user_info={
            "name": user.name,
            "role": user.role
        } if channel_name.startswith("presence-") else None
    )

    return auth
```

### RBAC Enforcement

```python
# Role hierarchy
_role_hierarchy = {
    "student": 1,
    "teacher": 2,
    "admin": 3
}

# Channel access mapping
_required_roles = {
    "admin": "admin",          # private-admin requires admin role
    "teacher": "teacher",      # private-teacher requires teacher+ role
    "student": "student",      # private-student requires student+ role
    "dashboard": "student",    # public-dashboard requires student+ role
}

def _check_channel_access(channel: str, user_role: str) -> bool:
    """Check if user role has access to channel"""
    channel_type = channel.split("-")[-1]
    required_role = _required_roles.get(channel_type, "student")

    user_level = _role_hierarchy.get(user_role, 0)
    required_level = _role_hierarchy.get(required_role, 0)

    return user_level >= required_level
```

---

## Usage Examples

### Example 1: Send Notification to User

```python
# Backend
from apps.backend.services.pusher_realtime import get_pusher_service

async def notify_quiz_result(user_id: str, quiz_id: str, score: float):
    service = get_pusher_service()

    await service.send_to_user(
        user_id=user_id,
        event="quiz-result",
        data={
            "quiz_id": quiz_id,
            "score": score,
            "grade": "A" if score >= 90 else "B" if score >= 80 else "C",
            "timestamp": datetime.now().isoformat()
        }
    )
```

### Example 2: Broadcast Agent Status

```python
# Backend
from apps.backend.services.pusher_realtime import emit_agent_status

async def update_agent_status(agent_name: str, status: str):
    await emit_agent_status(
        agent_name=agent_name,
        status=status,
        details={
            "tasks_pending": 5,
            "tasks_completed": 120,
            "uptime": "24h 15m"
        }
    )
```

### Example 3: Live Quiz Progress

```python
# Backend - Teacher submits quiz
@router.post("/quiz/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, student_id: str, answers: List[Answer]):
    score = grade_quiz(quiz_id, answers)

    # Notify teacher
    await pusher_service.broadcast_event(
        channel="private-teacher",
        event="quiz-submitted",
        data={
            "quiz_id": quiz_id,
            "student_id": student_id,
            "score": score
        }
    )

    # Notify student
    await pusher_service.send_to_user(
        user_id=student_id,
        event="quiz-result",
        data={
            "quiz_id": quiz_id,
            "score": score,
            "status": "graded"
        }
    )

    return {"score": score}
```

### Example 4: Classroom Presence

```javascript
// Frontend - Teacher dashboard
const classroomChannel = pusher.subscribe('presence-classroom-101');

classroomChannel.bind('pusher:subscription_succeeded', (members) => {
    updateStudentCount(members.count);
    updateStudentList(members);
});

classroomChannel.bind('pusher:member_added', (member) => {
    showNotification(`${member.info.name} joined the classroom`);
    updateStudentList();
});

classroomChannel.bind('pusher:member_removed', (member) => {
    showNotification(`${member.info.name} left the classroom`);
    updateStudentList();
});
```

---

## Frontend Integration

### Installation

```bash
cd apps/dashboard
npm install pusher-js
```

### Setup Pusher Client

```typescript
// src/services/pusher.ts
import Pusher from 'pusher-js';

const pusherKey = import.meta.env.VITE_PUSHER_KEY;
const pusherCluster = import.meta.env.VITE_PUSHER_CLUSTER;
const authEndpoint = import.meta.env.VITE_PUSHER_AUTH_ENDPOINT;

export const pusher = new Pusher(pusherKey, {
    cluster: pusherCluster,
    authEndpoint: authEndpoint,
    auth: {
        headers: {
            'Authorization': `Bearer ${getAccessToken()}`
        }
    }
});
```

### React Hook Example

```typescript
// src/hooks/usePusher.ts
import { useEffect, useState } from 'react';
import { pusher } from '../services/pusher';

export function usePusherChannel(channelName: string) {
    const [channel, setChannel] = useState(null);

    useEffect(() => {
        const ch = pusher.subscribe(channelName);
        setChannel(ch);

        return () => {
            pusher.unsubscribe(channelName);
        };
    }, [channelName]);

    return channel;
}

export function usePusherEvent(channelName: string, eventName: string, callback: (data: any) => void) {
    const channel = usePusherChannel(channelName);

    useEffect(() => {
        if (channel) {
            channel.bind(eventName, callback);

            return () => {
                channel.unbind(eventName, callback);
            };
        }
    }, [channel, eventName, callback]);
}
```

### Usage in Components

```typescript
// src/components/NotificationListener.tsx
import { usePusherEvent } from '../hooks/usePusher';

export function NotificationListener({ userId }) {
    usePusherEvent(
        `user-${userId}`,
        'notification',
        (data) => {
            showToast(data.message, data.type);
        }
    );

    return null; // This is a listener component
}
```

---

## Testing

### Manual Testing

**1. Test Health Check:**
```bash
curl http://localhost:8009/health | jq .services.pusher
```

Expected output:
```json
{
  "status": "healthy",
  "connected_users": 0,
  "total_channels": 0,
  "active_channels": []
}
```

**2. Test Event Triggering:**
```python
# Python interactive shell
from apps.backend.services.pusher import trigger_event

trigger_event(
    channel="public-dashboard",
    event="test-event",
    data={"message": "Hello from backend!"}
)
```

**3. Test Frontend Connection:**
```javascript
// Browser console
const pusher = new Pusher('your_key', { cluster: 'us2' });
const channel = pusher.subscribe('public-dashboard');

channel.bind('test-event', (data) => {
    console.log('Received:', data);
});

pusher.connection.bind('connected', () => {
    console.log('Pusher connected!');
});
```

### Automated Tests

```python
# tests/test_pusher_integration.py
import pytest
from apps.backend.services.pusher import PusherService, trigger_event

@pytest.mark.asyncio
async def test_pusher_trigger_event():
    """Test triggering event via Pusher"""
    result = trigger_event(
        channel="test-channel",
        event="test-event",
        data={"test": "data"}
    )
    assert result["channel"] == "test-channel"
    assert result["event"] == "test-event"

@pytest.mark.asyncio
async def test_pusher_service_initialization():
    """Test Pusher service initializes correctly"""
    service = PusherService(
        app_id="test_app_id",
        key="test_key",
        secret="test_secret",
        cluster="us2"
    )
    assert service.app_id == "test_app_id"
    assert service.cluster == "us2"
```

---

## Monitoring

### Health Check Endpoint

**Endpoint:** `GET /health/pusher/status`

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "connected_users": 42,
    "total_channels": 15,
    "active_channels": [
      "public-dashboard",
      "private-teacher",
      "agent-status"
    ],
    "rate_limit_remaining": 1850,
    "pusher_enabled": true
  }
}
```

### Pusher Dashboard

Access your Pusher dashboard at: `https://dashboard.pusher.com/apps/{app_id}`

**Metrics Available:**
- Connection count
- Message rate
- Channel activity
- Error rate
- API usage

### Logging

```python
# Backend logs Pusher events
logger.debug(f"Triggered event: {event_name} on channel {channel}")
logger.error(f"Error triggering event: {e}")
```

---

## Troubleshooting

### Issue: Pusher Not Connecting

**Symptoms:**
- Frontend shows "Connecting..." indefinitely
- Browser console shows connection errors

**Solutions:**

1. **Check configuration:**
   ```javascript
   console.log('Pusher Key:', import.meta.env.VITE_PUSHER_KEY);
   console.log('Cluster:', import.meta.env.VITE_PUSHER_CLUSTER);
   ```

2. **Verify CORS:**
   - Pusher requires CORS for authentication endpoint
   - Check backend CORS configuration includes frontend URL

3. **Check network:**
   - WebSockets may be blocked by firewall/proxy
   - Test from different network
   - Check browser console for blocked requests

### Issue: Authentication Failed (Private Channels)

**Symptoms:**
- Error: "Failed to subscribe to private-* channel"
- 403 errors in network tab

**Solutions:**

1. **Verify JWT token:**
   ```javascript
   // Check Authorization header is set
   pusher.config.auth.headers.Authorization
   ```

2. **Check backend auth endpoint:**
   ```bash
   curl -X POST http://localhost:8009/api/v1/pusher/auth \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d "socket_id=123.456" \
     -d "channel_name=private-teacher"
   ```

3. **Verify user role:**
   - User must have required role for channel
   - Check RBAC configuration

### Issue: Events Not Received

**Symptoms:**
- Backend triggers event successfully
- Frontend doesn't receive event

**Solutions:**

1. **Verify subscription:**
   ```javascript
   const channel = pusher.subscribe('public-dashboard');
   console.log('Subscribed to:', channel.name);
   ```

2. **Check event name:**
   - Must match exactly (case-sensitive)
   - No typos in event binding

3. **Verify channel state:**
   ```javascript
   console.log('Channel state:', channel.subscribed);
   ```

### Issue: Rate Limit Exceeded

**Symptoms:**
- Error: "Rate limit exceeded"
- Events not triggering

**Solutions:**

1. **Check current usage:**
   - Visit Pusher dashboard
   - Check messages per day count

2. **Optimize event triggering:**
   - Batch events when possible
   - Use `trigger_batch()` for multiple events
   - Implement throttling/debouncing

3. **Upgrade plan:**
   - Free tier: 200k messages/day
   - Paid plans: Higher limits

---

## Best Practices

### 1. Event Design

✅ **Do:**
- Use descriptive event names: `quiz-submitted`, `agent-status-changed`
- Include timestamps in event data
- Keep payloads small (<10 KB)
- Use consistent data structures

❌ **Don't:**
- Use generic names: `update`, `data`, `event`
- Send large payloads (>10 KB)
- Send sensitive data (passwords, tokens)
- Over-trigger events

### 2. Channel Organization

✅ **Do:**
- Use prefixes consistently: `public-`, `private-`, `presence-`
- Create user-specific channels: `user-{user_id}`
- Use resource-based channels: `classroom-{id}`, `agent-{id}`
- Clean up unused subscriptions

❌ **Don't:**
- Create too many channels (>100 per user)
- Use random channel names
- Keep all users on one channel
- Forget to unsubscribe

### 3. Security

✅ **Do:**
- Always use TLS/SSL in production
- Validate channel access in backend
- Use authentication for private channels
- Rotate Pusher secret keys periodically

❌ **Don't:**
- Expose Pusher secret in frontend
- Allow unauthorized channel access
- Send authentication tokens via Pusher
- Use public channels for sensitive data

### 4. Performance

✅ **Do:**
- Batch multiple events with `trigger_batch()`
- Use presence channels only when needed
- Implement client-side throttling
- Monitor message rate

❌ **Don't:**
- Trigger events in tight loops
- Send events on every keystroke
- Ignore rate limits
- Use presence channels for large groups (>100 users)

### 5. Error Handling

✅ **Do:**
- Handle connection failures gracefully
- Implement retry logic with exponential backoff
- Log errors for debugging
- Show connection status to users

❌ **Don't:**
- Assume connection is always available
- Retry indefinitely without backoff
- Ignore error events
- Hide connection issues from users

---

## Reference

### Environment Variables

See [`/.env.example`](../../.env.example) for complete Pusher configuration.

### Related Documentation

- [Real-Time Architecture](../02-architecture/REALTIME_ARCHITECTURE.md)
- [API Documentation](../04-api/PUSHER_API.md)
- [Security Guide](../10-security/REALTIME_SECURITY.md)
- [Troubleshooting Guide](../08-operations/troubleshooting/PUSHER_TROUBLESHOOTING.md)

### External Resources

- [Pusher Channels Documentation](https://pusher.com/docs/channels)
- [Pusher JavaScript Client](https://github.com/pusher/pusher-js)
- [Pusher Python Library](https://github.com/pusher/pusher-http-python)
- [Pusher Pricing](https://pusher.com/channels/pricing)

---

**ToolBoxAI-Solutions Development Team**
*Building real-time, AI-powered educational experiences*

Last Updated: November 9, 2025
