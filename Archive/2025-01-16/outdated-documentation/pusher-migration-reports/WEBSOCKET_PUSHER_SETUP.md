# WebSocket and Pusher Integration Setup Guide

## 🚀 Overview

This guide explains how to enable and configure WebSocket and Pusher real-time communication in the ToolboxAI platform.

## ✅ Current Status

- **Backend Configuration**: ✅ Complete
- **Frontend Configuration**: ✅ Complete  
- **Pusher Service**: ✅ Complete
- **WebSocket Context**: ✅ Complete
- **API Endpoints**: ✅ Working
- **Real-time Features**: ✅ Ready

## 🔧 Configuration

### Backend Configuration

The backend is configured with the following environment variables:

```bash
# Pusher Configuration
PUSHER_ENABLED=true
PUSHER_APP_ID=your_pusher_app_id
PUSHER_KEY=your_pusher_key
PUSHER_SECRET=your_pusher_secret
PUSHER_CLUSTER=us2
PUSHER_SSL=true

# WebSocket Configuration
WS_ENABLED=true
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=1000
```

### Frontend Configuration

The frontend is configured with the following environment variables:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8008
VITE_WS_URL=http://localhost:8008

# Pusher Configuration
VITE_PUSHER_KEY=your_pusher_key
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=http://localhost:8008/pusher/auth

# WebSocket Configuration
VITE_ENABLE_WEBSOCKET=true
```

## 🌐 API Endpoints

### 1. Pusher Authentication
```
POST /pusher/auth?socket_id={socket_id}&channel_name={channel_name}
```
Authenticates private/presence channel subscriptions.

### 2. Realtime Trigger
```
POST /realtime/trigger
Content-Type: application/json

{
  "channel": "channel-name",
  "event": "event-name",
  "data": {
    "message": "Hello World"
  }
}
```
Triggers real-time events from the server.

### 3. Pusher Webhook
```
POST /pusher/webhook
```
Handles Pusher webhooks for channel events.

## 🔌 Frontend Integration

### Using the WebSocket Context

```tsx
import { useWebSocket } from '../contexts/WebSocketContext';

function MyComponent() {
  const { 
    state, 
    isConnected, 
    connect, 
    disconnect, 
    send, 
    subscribe, 
    unsubscribe 
  } = useWebSocket();

  useEffect(() => {
    // Connect when component mounts
    connect();
    
    // Subscribe to a channel
    const subscriptionId = subscribe('my-channel', (message) => {
      console.log('Received message:', message);
    });

    return () => {
      // Cleanup
      unsubscribe(subscriptionId);
      disconnect();
    };
  }, []);

  const handleSendMessage = () => {
    send('MESSAGE', { text: 'Hello World' });
  };

  return (
    <div>
      <p>Status: {state}</p>
      <p>Connected: {isConnected ? 'Yes' : 'No'}</p>
      <button onClick={handleSendMessage}>Send Message</button>
    </div>
  );
}
```

### Using the Pusher Service Directly

```tsx
import { pusherService } from '../services/pusher';

// Connect
await pusherService.connect(token);

// Subscribe to channel
const subscriptionId = pusherService.subscribe('my-channel', (message) => {
  console.log('Message received:', message);
});

// Send message
await pusherService.send('MESSAGE', { text: 'Hello' });

// Disconnect
pusherService.disconnect();
```

## 🧪 Testing

### 1. Test Backend Endpoints

```bash
# Test realtime trigger
curl -X POST http://localhost:8008/realtime/trigger \
  -H "Content-Type: application/json" \
  -d '{"channel": "test", "event": "message", "data": {"text": "Hello"}}'

# Test Pusher auth (will fail without proper config)
curl -X POST "http://localhost:8008/pusher/auth?socket_id=test&channel_name=test"
```

### 2. Test Frontend Connection

```tsx
// In browser console
import { pusherService } from './src/services/pusher';

// Test connection
pusherService.connect().then(() => {
  console.log('Connected!');
}).catch(err => {
  console.error('Connection failed:', err);
});
```

## 🚀 Getting Started with Real Pusher

### 1. Create Pusher App

1. Go to [pusher.com](https://pusher.com)
2. Create a new app
3. Note your App ID, Key, Secret, and Cluster

### 2. Configure Environment

Create `.env` files with your Pusher credentials:

**Backend (.env):**
```bash
PUSHER_ENABLED=true
PUSHER_APP_ID=your_app_id
PUSHER_KEY=your_key
PUSHER_SECRET=your_secret
PUSHER_CLUSTER=your_cluster
```

**Frontend (.env):**
```bash
VITE_PUSHER_KEY=your_key
VITE_PUSHER_CLUSTER=your_cluster
VITE_PUSHER_AUTH_ENDPOINT=http://localhost:8008/pusher/auth
```

### 3. Test Real-time Features

```tsx
// Example: Real-time notifications
const { subscribe } = useWebSocket();

useEffect(() => {
  const subscriptionId = subscribe('notifications', (message) => {
    if (message.type === 'NOTIFICATION') {
      showNotification(message.payload);
    }
  });

  return () => unsubscribe(subscriptionId);
}, []);
```

## 🔄 Real-time Features Available

### 1. User Presence
- Track online/offline users
- Show active users in real-time

### 2. Live Notifications
- System notifications
- User mentions
- Content updates

### 3. Collaborative Features
- Real-time chat
- Live document editing
- Shared whiteboards

### 4. Content Generation
- Progress updates
- Completion notifications
- Error handling

### 5. Quiz and Assessment
- Live quiz updates
- Real-time scoring
- Leaderboard updates

## 🛠️ Development Mode

In development mode, the system gracefully handles missing Pusher configuration:

- Real-time endpoints return mock responses
- Frontend continues to work without WebSocket
- No errors are thrown for missing configuration

## 📊 Monitoring

### WebSocket Stats

```tsx
const { stats } = useWebSocket();

console.log('Messages sent:', stats.messagesSent);
console.log('Messages received:', stats.messagesReceived);
console.log('Reconnection attempts:', stats.reconnectionAttempts);
```

### Connection Status

```tsx
const { state, isConnected, error } = useWebSocket();

// States: CONNECTING, CONNECTED, DISCONNECTED, ERROR
console.log('Connection state:', state);
console.log('Is connected:', isConnected);
console.log('Last error:', error);
```

## 🔒 Security

- JWT authentication for WebSocket connections
- Channel-based access control
- Rate limiting on WebSocket endpoints
- Secure token refresh mechanism

## 🚨 Troubleshooting

### Common Issues

1. **"Pusher configuration missing"**
   - Ensure all Pusher environment variables are set
   - Check that PUSHER_ENABLED=true

2. **"Authentication token required"**
   - Ensure user is logged in
   - Check JWT token validity

3. **"Connection failed"**
   - Check network connectivity
   - Verify Pusher credentials
   - Check CORS configuration

### Debug Mode

Enable debug logging:

```tsx
// Frontend
const pusherService = new PusherService({ debug: true });

// Backend
import logging
logging.getLogger('apps.backend.services.pusher').setLevel(logging.DEBUG)
```

## 📈 Performance

- Automatic reconnection with exponential backoff
- Message queuing during disconnection
- Efficient channel subscription management
- Connection pooling and reuse

## 🎯 Next Steps

1. **Set up Pusher account** and configure credentials
2. **Test real-time features** in development
3. **Implement specific use cases** (chat, notifications, etc.)
4. **Monitor performance** and optimize as needed
5. **Deploy with production Pusher configuration**

---

## 📝 Summary

The WebSocket and Pusher integration is fully implemented and ready for use. The system provides:

- ✅ Complete backend API endpoints
- ✅ Robust frontend service layer
- ✅ React context for easy integration
- ✅ Graceful fallback for development
- ✅ Comprehensive error handling
- ✅ Security and authentication
- ✅ Performance optimizations

Simply configure your Pusher credentials and start building real-time features!
