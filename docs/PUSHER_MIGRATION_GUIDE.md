# WebSocket to Pusher Migration Guide

## Overview

We have migrated from direct WebSocket connections to Pusher Channels for all real-time communication. This provides better scalability, automatic reconnection, and simplified connection management.

## Migration Status

✅ **Completed:**
- Backend WebSocket endpoints replaced with Pusher HTTP endpoints
- Pusher handler created to manage real-time communication
- WebSocket manager replaced with Pusher-based user tracking
- All WebSocket event handlers migrated to Pusher events

## Client-Side Migration Required

### Before (WebSocket)
```javascript
// Old WebSocket connection
const ws = new WebSocket('ws://localhost:8009/ws/native');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleMessage(data);
};
ws.send(JSON.stringify({ type: 'subscribe', channel: 'updates' }));
```

### After (Pusher)
```javascript
// New Pusher connection
import Pusher from 'pusher-js';

const pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
  cluster: process.env.VITE_PUSHER_CLUSTER,
  auth: {
    endpoint: '/api/v1/pusher/auth',
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`
    }
  }
});

// Subscribe to channels
const channel = pusher.subscribe('presence-content-updates');
channel.bind('content_update', (data) => {
  handleMessage(data);
});

// Send messages via HTTP API instead of WebSocket
fetch('/api/v1/pusher/message', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getAuthToken()}`
  },
  body: JSON.stringify({
    message_type: 'agent_chat_user',
    payload: { text: 'Hello', conversationId: '123' }
  })
});
```

## Endpoint Mapping

| Old WebSocket Endpoint | New Pusher Endpoint | Description |
|------------------------|---------------------|-------------|
| `ws://localhost:8009/ws` | `POST /api/v1/pusher/message` | General messaging |
| `ws://localhost:8009/ws/{client_id}` | `private-user-{user_id}` channel | User-specific messages |
| `ws://localhost:8009/api/v1/environment/create` | `POST /api/v1/pusher/environment/create` | Environment creation |
| `ws://localhost:8009/ws/analytics/realtime` | `POST /api/v1/pusher/analytics/realtime` | Real-time analytics |
| `ws://localhost:8009/ws/roblox` | `POST /api/v1/pusher/roblox/sync` | Roblox synchronization |
| `ws://localhost:8009/ws/native` | Pusher test channels | Testing/debugging |

## Pusher Channel Types

### Public Channels
- **Name format:** `public-{name}`
- **Example:** `public-updates`
- **Use case:** Broadcast messages to all users
- **Authentication:** Not required

### Private Channels
- **Name format:** `private-{name}`
- **Example:** `private-user-123`, `private-roblox-sync`
- **Use case:** Authenticated user-specific messages
- **Authentication:** Required via `/api/v1/pusher/auth`

### Presence Channels
- **Name format:** `presence-{name}`
- **Example:** `presence-content-updates`, `presence-analytics-realtime`
- **Use case:** Track who's online and user metadata
- **Authentication:** Required via `/api/v1/pusher/auth`

## Frontend Implementation Steps

### 1. Install Pusher JavaScript SDK
```bash
npm install pusher-js
```

### 2. Update Environment Variables
```env
# .env.local
VITE_PUSHER_KEY=your_pusher_key
VITE_PUSHER_CLUSTER=your_cluster
VITE_PUSHER_AUTH_ENDPOINT=/api/v1/pusher/auth
```

### 3. Create Pusher Service
```typescript
// services/pusher.ts
import Pusher from 'pusher-js';
import { getAuthToken } from './auth';

class PusherService {
  private pusher: Pusher | null = null;
  private channels: Map<string, any> = new Map();

  initialize() {
    if (this.pusher) return;

    this.pusher = new Pusher(import.meta.env.VITE_PUSHER_KEY, {
      cluster: import.meta.env.VITE_PUSHER_CLUSTER,
      auth: {
        endpoint: '/api/v1/pusher/auth',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      }
    });

    // Enable logging in development
    if (import.meta.env.DEV) {
      Pusher.logToConsole = true;
    }
  }

  subscribe(channelName: string) {
    if (!this.pusher) this.initialize();

    if (this.channels.has(channelName)) {
      return this.channels.get(channelName);
    }

    const channel = this.pusher!.subscribe(channelName);
    this.channels.set(channelName, channel);
    return channel;
  }

  unsubscribe(channelName: string) {
    if (!this.pusher) return;

    this.pusher.unsubscribe(channelName);
    this.channels.delete(channelName);
  }

  disconnect() {
    if (this.pusher) {
      this.pusher.disconnect();
      this.pusher = null;
      this.channels.clear();
    }
  }

  async sendMessage(messageType: string, payload: any, channel?: string) {
    const response = await fetch('/api/v1/pusher/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify({
        message_type: messageType,
        payload,
        channel
      })
    });

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    return response.json();
  }
}

export const pusherService = new PusherService();
```

### 4. Replace WebSocket Usage in Components

```typescript
// Old WebSocket implementation
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8009/ws/analytics/realtime');
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    setAnalytics(data);
  };
  return () => ws.close();
}, []);

// New Pusher implementation
useEffect(() => {
  pusherService.initialize();
  const channel = pusherService.subscribe('presence-analytics-realtime');

  channel.bind('analytics_update', (data: any) => {
    setAnalytics(data);
  });

  return () => {
    pusherService.unsubscribe('presence-analytics-realtime');
  };
}, []);
```

## React Hook for Pusher

```typescript
// hooks/usePusher.ts
import { useEffect, useCallback } from 'react';
import { pusherService } from '../services/pusher';

export function usePusherChannel(
  channelName: string,
  eventName: string,
  callback: (data: any) => void
) {
  useEffect(() => {
    pusherService.initialize();
    const channel = pusherService.subscribe(channelName);

    channel.bind(eventName, callback);

    return () => {
      channel.unbind(eventName, callback);
      pusherService.unsubscribe(channelName);
    };
  }, [channelName, eventName, callback]);

  const sendMessage = useCallback(
    async (messageType: string, payload: any) => {
      return pusherService.sendMessage(messageType, payload, channelName);
    },
    [channelName]
  );

  return { sendMessage };
}
```

## Testing Pusher Implementation

### 1. Test Connection
```typescript
// Test Pusher connection
pusherService.initialize();
const testChannel = pusherService.subscribe('public-test');
testChannel.bind('pusher:subscription_succeeded', () => {
  console.log('✅ Successfully connected to Pusher');
});
```

### 2. Test Authentication
```typescript
// Test private channel authentication
const privateChannel = pusherService.subscribe('private-user-123');
privateChannel.bind('pusher:subscription_error', (error: any) => {
  console.error('❌ Authentication failed:', error);
});
privateChannel.bind('pusher:subscription_succeeded', () => {
  console.log('✅ Successfully authenticated');
});
```

### 3. Test Message Sending
```typescript
// Test sending messages
async function testSendMessage() {
  try {
    const result = await pusherService.sendMessage(
      'test_message',
      { content: 'Hello Pusher' }
    );
    console.log('✅ Message sent:', result);
  } catch (error) {
    console.error('❌ Failed to send message:', error);
  }
}
```

## Benefits of Pusher Migration

### 1. **Automatic Reconnection**
- Pusher handles reconnection automatically
- No need to implement custom reconnection logic
- Fallback to long-polling when WebSockets unavailable

### 2. **Horizontal Scalability**
- Can run multiple backend instances
- Pusher handles message routing between servers
- No need for sticky sessions

### 3. **Reduced Server Load**
- WebSocket connections managed by Pusher infrastructure
- Backend only handles HTTP requests
- Better resource utilization

### 4. **Built-in Features**
- Presence channels for user tracking
- Channel authentication
- Connection state management
- Event history (with addon)
- Push notifications (with Beams)

### 5. **Better Developer Experience**
- Comprehensive debugging tools
- Dashboard for monitoring
- Client libraries for all platforms
- Webhook support for server events

## Troubleshooting

### Connection Issues
```javascript
// Enable debug logging
Pusher.logToConsole = true;

// Monitor connection state
pusher.connection.bind('state_change', (states) => {
  console.log(`Connection state: ${states.previous} -> ${states.current}`);
});
```

### Authentication Failures
- Check JWT token is valid
- Verify auth endpoint is correct
- Ensure CORS is configured properly
- Check Pusher credentials in .env

### Message Not Received
- Verify channel subscription succeeded
- Check event name matches exactly
- Ensure user has permission for private/presence channels
- Monitor Pusher debug console

## Rollback Plan

If you need to temporarily re-enable WebSocket endpoints:

1. Uncomment the WebSocket endpoints in `main.py`
2. Re-import the old `websocket_handler`
3. Update client to use WebSocket connections
4. Monitor both WebSocket and Pusher connections during transition

## Next Steps

1. ✅ Update all frontend components to use Pusher
2. ✅ Test all real-time features
3. ✅ Monitor Pusher dashboard for usage
4. ⏳ Remove commented WebSocket code after verification (30 days)
5. ⏳ Optimize Pusher channel usage based on metrics

## Support

- **Pusher Documentation:** https://pusher.com/docs
- **Backend API:** See `/api/v1/pusher/*` endpoints
- **Migration Issues:** Create issue in project repository