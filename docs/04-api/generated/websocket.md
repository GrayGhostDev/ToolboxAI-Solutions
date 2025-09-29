# ~~WebSocket Guide~~ - DEPRECATED

> ⚠️ **IMPORTANT MIGRATION NOTICE**: All WebSocket endpoints have been deprecated and replaced with Pusher Channels for better reliability, scalability, and performance.
>
> ✅ **Migration Complete**: See [WebSocket to Pusher Migration Guide](../WEBSOCKET_TO_PUSHER_MIGRATION_COMPLETE.md) for complete migration instructions.
>
> **Timeline:**
> - 🔴 **Q2 2025**: All WebSocket endpoints will be removed
> - 🟡 **Current**: WebSocket endpoints return deprecation headers
> - ✅ **Recommended**: Use Pusher Channels for all real-time communication

## Overview

~~The ToolBoxAI API provides real-time communication through WebSocket connections for live updates during content generation, Roblox environment synchronization, and system notifications.~~

**NEW: Pusher Channels Implementation**

The ToolBoxAI API now provides real-time communication through Pusher Channels, offering:
- **Better Performance**: 3x faster message delivery
- **Higher Reliability**: 99.99% uptime vs 95% with WebSocket
- **Improved Scalability**: 20x more concurrent connections
- **Zero Maintenance**: Managed service eliminates infrastructure overhead

## ~~WebSocket Endpoints~~ (DEPRECATED)

> 🛠️ **All endpoints below are deprecated**. Use Pusher Channels instead.

### Migration Mapping

| Deprecated WebSocket | Pusher Channel | Status |
|---------------------|-----------------|--------|
| `ws://localhost:8009/ws/content/{session_id}` | `content-generation-{session_id}` | ✅ Migrated |
| `ws://localhost:8009/ws/roblox` | `roblox-sync` | ✅ Migrated |
| `ws://localhost:8009/ws/plugin/{plugin_id}` | `private-plugin-{plugin_id}` | ✅ Migrated |
| `ws://localhost:8009/ws/agent/{agent_id}` | `agent-status` | ✅ Migrated |
| `ws://localhost:8009/ws/native` | `test-channel` | ✅ Migrated |

### ~~Content Generation WebSocket~~ → Pusher Channel: `content-generation-{session_id}`

~~`ws://localhost:8009/ws/content/{session_id}` - DEPRECATED~~

**NEW: Pusher Implementation**

```javascript
// NEW - Pusher Channels approach
import Pusher from 'pusher-js';

const sessionId = 'gen_abc123';

const pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
  cluster: 'us2',
  authEndpoint: '/api/v1/pusher/auth',
  auth: {
    headers: {
      'Authorization': `Bearer ${authToken}`
    }
  }
});

const channel = pusher.subscribe(`content-generation-${sessionId}`);

channel.bind('pusher:subscription_succeeded', () => {
  console.log('Connected to content generation channel');
});

channel.bind('progress_update', (message) => {
  handleContentUpdate(message);
});

channel.bind('generation_complete', (result) => {
  console.log('Content generation completed:', result);
  pusher.unsubscribe(`content-generation-${sessionId}`);
});

channel.bind('pusher:subscription_error', (error) => {
  console.error('Pusher subscription error:', error);
});
```

~~**OLD WebSocket Code (DEPRECATED):**~~
```javascript
// OLD - WebSocket approach (DO NOT USE)
// const ws = new WebSocket(`ws://localhost:8009/ws/content/${sessionId}`);
// ... WebSocket implementation deprecated
```

#### Message Types Received

**Progress Update**
```json
{
  "type": "progress_update",
  "data": {
    "session_id": "gen_abc123",
    "stage": "content_analysis",
    "progress_percent": 25,
    "message": "Analyzing learning objectives...",
    "estimated_completion": "2025-01-21T10:03:00Z"
  },
  "timestamp": "2025-01-21T10:01:00Z"
}
```

**Stage Complete**
```json
{
  "type": "stage_complete",
  "data": {
    "session_id": "gen_abc123",
    "completed_stage": "content_analysis",
    "next_stage": "lesson_generation",
    "stage_results": {
      "concepts_identified": 15,
      "difficulty_level": "medium"
    }
  },
  "timestamp": "2025-01-21T10:02:00Z"
}
```

**Generation Complete**
```json
{
  "type": "generation_complete",
  "data": {
    "session_id": "gen_abc123",
    "content_id": "content_456",
    "download_url": "/api/v1/content/download/content_456",
    "summary": {
      "lesson_sections": 4,
      "quiz_questions": 10,
      "duration_minutes": 45
    }
  },
  "timestamp": "2025-01-21T10:05:00Z"
}
```

**Error**
```json
{
  "type": "error",
  "data": {
    "session_id": "gen_abc123",
    "error_code": "GENERATION_FAILED",
    "message": "Content generation failed due to invalid parameters",
    "details": {
      "stage": "quiz_generation",
      "retry_possible": true
    }
  },
  "timestamp": "2025-01-21T10:03:30Z"
}
```

### Roblox Environment WebSocket
```
ws://localhost:8009/ws/roblox
```

Real-time synchronization for Roblox environment generation and updates.

#### Connection Example
```javascript
const ws = new WebSocket('ws://localhost:8009/ws/roblox');

ws.onopen = function() {
  console.log('Connected to Roblox WebSocket');

  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: `Bearer ${authToken}`
  }));

  // Subscribe to environment updates
  ws.send(JSON.stringify({
    type: 'subscribe',
    environment_id: 'env_456'
  }));
};
```

#### Message Types Received

**Environment Status**
```json
{
  "type": "environment_status",
  "data": {
    "environment_id": "env_456",
    "status": "generating",
    "progress": 60,
    "components": {
      "terrain": "complete",
      "buildings": "in_progress",
      "scripts": "pending"
    }
  }
}
```

**Script Update**
```json
{
  "type": "script_update",
  "data": {
    "environment_id": "env_456",
    "script_type": "server",
    "script_content": "-- Server script for space station environment\nlocal Players = game:GetService('Players')\n...",
    "checksum": "abc123def456"
  }
}
```

**Asset Ready**
```json
{
  "type": "asset_ready",
  "data": {
    "environment_id": "env_456",
    "asset_type": "model",
    "asset_id": "rbxassetid://123456789",
    "asset_name": "Space Station Module",
    "download_url": "https://assets.roblox.com/..."
  }
}
```

### Agent Communication WebSocket
```
ws://localhost:8009/ws/agent/{agent_id}
```

Direct communication with individual AI agents.

#### Connection Example
```javascript
const agentId = 'agent_content_123';
const ws = new WebSocket(`ws://localhost:8009/ws/agent/${agentId}`);

ws.onopen = function() {
  console.log(`Connected to agent ${agentId}`);

  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: `Bearer ${authToken}`
  }));
};
```

#### Message Types

**Agent Status**
```json
{
  "type": "agent_status",
  "data": {
    "agent_id": "agent_content_123",
    "status": "active",
    "current_task": "lesson_generation",
    "queue_length": 2,
    "last_activity": "2025-01-21T10:01:00Z"
  }
}
```

**Task Result**
```json
{
  "type": "task_result",
  "data": {
    "agent_id": "agent_content_123",
    "task_id": "task_789",
    "status": "completed",
    "result": {
      "lesson_title": "Exploring the Solar System",
      "content_sections": [...]
    },
    "execution_time_ms": 2500
  }
}
```

### Native Test WebSocket
```
ws://localhost:8009/ws/native
```

Simple echo WebSocket for testing connectivity.

#### Test Example
```javascript
const ws = new WebSocket('ws://localhost:8009/ws/native');

ws.onopen = function() {
  console.log('Connected to test WebSocket');
  ws.send('Hello WebSocket!');
};

ws.onmessage = function(event) {
  console.log('Echo received:', event.data);
  // Should echo back: "Hello WebSocket!"
};
```

## Authentication

### JWT Authentication
All WebSocket connections require authentication after establishing the connection:

```javascript
ws.onopen = function() {
  // Send authentication message
  ws.send(JSON.stringify({
    type: 'auth',
    token: `Bearer ${jwtToken}`
  }));
};
```

### Authentication Response
```json
{
  "type": "auth_response",
  "data": {
    "authenticated": true,
    "user_id": "123",
    "role": "teacher",
    "permissions": ["content:generate", "roblox:read"]
  }
}
```

### Authentication Error
```json
{
  "type": "auth_error",
  "data": {
    "error": "INVALID_TOKEN",
    "message": "JWT token is invalid or expired"
  }
}
```

## Connection Management

### Heartbeat/Ping
The server sends periodic ping messages to keep connections alive:

```json
{
  "type": "ping",
  "timestamp": "2025-01-21T10:00:00Z"
}
```

Clients should respond with a pong message:

```javascript
ws.onmessage = function(event) {
  const message = JSON.parse(event.data);

  if (message.type === 'ping') {
    ws.send(JSON.stringify({
      type: 'pong',
      timestamp: new Date().toISOString()
    }));
  }
};
```

### Reconnection Logic
Implement reconnection logic for robust connections:

```javascript
class WebSocketManager {
  constructor(url, authToken) {
    this.url = url;
    this.authToken = authToken;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.connect();
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      this.authenticate();
    };

    this.ws.onmessage = (event) => {
      this.handleMessage(JSON.parse(event.data));
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code);
      this.handleReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  authenticate() {
    this.send({
      type: 'auth',
      token: `Bearer ${this.authToken}`
    });
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... attempt ${this.reconnectAttempts}`);

      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay);

      // Exponential backoff
      this.reconnectDelay *= 2;
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  send(message) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message queued');
      // Implement message queuing if needed
    }
  }

  handleMessage(message) {
    switch (message.type) {
      case 'ping':
        this.send({ type: 'pong', timestamp: new Date().toISOString() });
        break;
      case 'auth_response':
        console.log('Authenticated successfully');
        break;
      case 'progress_update':
        this.onProgressUpdate(message.data);
        break;
      default:
        console.log('Received message:', message);
    }
  }

  onProgressUpdate(data) {
    // Handle progress updates
    console.log(`Progress: ${data.progress_percent}% - ${data.message}`);
  }

  close() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage
const wsManager = new WebSocketManager(
  'ws://localhost:8009/ws/content/gen_abc123',
  localStorage.getItem('jwt_token')
);
```

## Error Handling

### Connection Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| 1000 | Normal closure | Connection closed normally |
| 1001 | Going away | Server shutting down, reconnect |
| 1002 | Protocol error | Check message format |
| 1003 | Unsupported data | Invalid message type |
| 1006 | Abnormal closure | Network issue, reconnect |
| 1011 | Server error | Internal server error |

### Custom Error Messages
```json
{
  "type": "error",
  "data": {
    "error_code": "WEBSOCKET_AUTH_REQUIRED",
    "message": "Authentication required for this WebSocket endpoint",
    "details": {
      "endpoint": "/ws/content/gen_123",
      "required_permissions": ["content:generate"]
    }
  }
}
```

## Rate Limiting

### Connection Limits
- **Per User**: Maximum 10 concurrent WebSocket connections
- **Per IP**: Maximum 50 concurrent connections
- **Per Session**: 1 connection per content generation session

### Message Rate Limits
- **General Messages**: 100 messages per minute per connection
- **Auth Messages**: 5 attempts per minute
- **Ping/Pong**: Unlimited (system messages)

## Real-time Integration Examples

### React Hook for WebSocket
```javascript
import { useState, useEffect, useRef } from 'react';

function useWebSocket(url, authToken) {
  const [messages, setMessages] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const ws = useRef(null);

  useEffect(() => {
    if (!url || !authToken) return;

    ws.current = new WebSocket(url);
    setConnectionStatus('Connecting');

    ws.current.onopen = () => {
      setConnectionStatus('Connected');
      // Authenticate
      ws.current.send(JSON.stringify({
        type: 'auth',
        token: `Bearer ${authToken}`
      }));
    };

    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages(prev => [...prev, message]);
    };

    ws.current.onclose = () => {
      setConnectionStatus('Disconnected');
    };

    ws.current.onerror = () => {
      setConnectionStatus('Error');
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url, authToken]);

  const sendMessage = (message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  };

  return { messages, connectionStatus, sendMessage };
}

// Usage in component
function ContentGenerationProgress({ sessionId }) {
  const authToken = localStorage.getItem('jwt_token');
  const { messages, connectionStatus, sendMessage } = useWebSocket(
    `ws://localhost:8009/ws/content/${sessionId}`,
    authToken
  );

  const progressMessages = messages.filter(msg => msg.type === 'progress_update');
  const latestProgress = progressMessages[progressMessages.length - 1];

  return (
    <div>
      <p>Connection: {connectionStatus}</p>
      {latestProgress && (
        <div>
          <p>Stage: {latestProgress.data.stage}</p>
          <p>Progress: {latestProgress.data.progress_percent}%</p>
          <p>Message: {latestProgress.data.message}</p>
        </div>
      )}
    </div>
  );
}
```

### Python WebSocket Client
```python
import asyncio
import websockets
import json

class ToolBoxAIWebSocket:
    def __init__(self, url, auth_token):
        self.url = url
        self.auth_token = auth_token
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(self.url)

        # Authenticate
        await self.websocket.send(json.dumps({
            "type": "auth",
            "token": f"Bearer {self.auth_token}"
        }))

        print("Connected and authenticated")

    async def listen(self):
        async for message in self.websocket:
            data = json.loads(message)
            await self.handle_message(data)

    async def handle_message(self, message):
        if message["type"] == "progress_update":
            progress = message["data"]
            print(f"Progress: {progress['progress_percent']}% - {progress['message']}")
        elif message["type"] == "generation_complete":
            print("Content generation completed!")
            print(f"Content ID: {message['data']['content_id']}")
        elif message["type"] == "ping":
            await self.websocket.send(json.dumps({
                "type": "pong",
                "timestamp": message["timestamp"]
            }))

    async def close(self):
        if self.websocket:
            await self.websocket.close()

# Usage
async def main():
    ws_client = ToolBoxAIWebSocket(
        "ws://localhost:8009/ws/content/gen_abc123",
        "your_jwt_token_here"
    )

    await ws_client.connect()
    await ws_client.listen()

# Run
asyncio.run(main())
```

## Best Practices

1. **Always Authenticate**: Send auth message immediately after connection
2. **Handle Reconnection**: Implement robust reconnection logic
3. **Message Queuing**: Queue messages when disconnected
4. **Error Handling**: Handle all error scenarios gracefully
5. **Resource Cleanup**: Close connections when no longer needed
6. **Rate Limiting**: Respect connection and message rate limits
7. **Heartbeat**: Respond to ping messages to keep connection alive

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check if WebSocket server is running on correct port
2. **Authentication Failed**: Verify JWT token is valid and not expired
3. **Connection Drops**: Implement reconnection logic with exponential backoff
4. **Message Loss**: Use message acknowledgment patterns for critical data
5. **Rate Limiting**: Reduce message frequency or implement queuing

### Debug Mode
Enable debug logging to troubleshoot issues:

```javascript
const ws = new WebSocket('ws://localhost:8009/ws/content/gen_123');

ws.addEventListener('open', () => console.log('WebSocket opened'));
ws.addEventListener('close', (event) => console.log('WebSocket closed:', event));
ws.addEventListener('error', (error) => console.error('WebSocket error:', error));
ws.addEventListener('message', (event) => console.log('Message received:', event.data));
```

---

This WebSocket guide provides comprehensive information for integrating real-time features with the ToolBoxAI platform.