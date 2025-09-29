# Pusher Integration in App.tsx Documentation

## Overview

The main App component (`apps/dashboard/src/App.tsx`) integrates Pusher Channels for real-time functionality, replacing the legacy WebSocket implementation. This document details how Pusher is integrated and used within the application's root component.

## Integration Points

### 1. Service Import

```typescript
// Line 23
import { pusherService } from "./services/pusher";
```

The `pusherService` is imported from the centralized Pusher service module that provides a singleton instance for managing all Pusher connections.

### 2. Connection Lifecycle Management

```typescript
// Lines 85-106
React.useEffect(() => {
  let isConnected = false;

  if (isAuthenticated) {
    // Small delay to allow component to stabilize
    const connectTimer = setTimeout(() => {
      pusherService.connect();
      isConnected = true;
      logger.info('Pusher connected for real-time updates');
    }, 100);

    return () => {
      clearTimeout(connectTimer);
      // Only disconnect if we actually connected
      if (isConnected) {
        pusherService.disconnect();
      }
    };
  }
  return undefined; // Explicit return for when not authenticated
}, [isAuthenticated]);
```

#### Key Features:

- **Authentication-based Connection**: Pusher only connects when the user is authenticated
- **Delayed Connection**: 100ms delay ensures component stability before connecting
- **Proper Cleanup**: Disconnects on unmount or when authentication status changes
- **Connection State Tracking**: Uses `isConnected` flag to prevent unnecessary disconnect attempts

### 3. Real-time Components

The app includes several components that leverage Pusher for real-time features:

```typescript
// Line 186
<RealtimeToast />
```

The `RealtimeToast` component subscribes to Pusher channels to display real-time notifications.

### 4. WebSocket Context Compatibility

```typescript
// Line 160
<WebSocketProvider autoConnect={true} debug={process.env.NODE_ENV === 'development'}>
```

The WebSocketProvider wrapper maintains backward compatibility for components that haven't been migrated to Pusher yet. It provides a context that can bridge between WebSocket and Pusher implementations.

## Pusher Service Configuration

### Connection Parameters

The Pusher service uses the following environment variables:

```env
VITE_PUSHER_KEY=your-pusher-key
VITE_PUSHER_CLUSTER=your-cluster
VITE_PUSHER_AUTH_ENDPOINT=/api/v1/pusher/auth
```

### Available Channels

Based on the service configuration, the app uses these Pusher channels:

1. **Public Channels**:
   - `dashboard-updates` - General dashboard notifications
   - `content-generation` - Content creation progress
   - `agent-status` - AI agent activity monitoring

2. **Private Channels** (authenticated):
   - `private-user-{userId}` - User-specific notifications
   - `private-classroom-{classId}` - Classroom-specific updates

3. **Presence Channels** (authenticated with presence):
   - `presence-classroom-{classId}` - Live classroom participants
   - `presence-collaboration-{sessionId}` - Collaborative editing sessions

## Event Handling

### Subscribing to Events

Components can subscribe to Pusher events using the `usePusherEvents` hook:

```typescript
import { usePusherEvents } from './hooks/usePusherEvents';

function MyComponent() {
  const { subscribe, unsubscribe } = usePusherEvents();

  React.useEffect(() => {
    const handler = (data) => {
      console.log('Received event:', data);
    };

    subscribe('dashboard-updates', 'new-content', handler);

    return () => {
      unsubscribe('dashboard-updates', 'new-content', handler);
    };
  }, [subscribe, unsubscribe]);
}
```

### Common Events

| Channel | Event | Description | Payload |
|---------|-------|-------------|---------|
| `dashboard-updates` | `content-updated` | Content has been modified | `{ contentId, changes }` |
| `dashboard-updates` | `user-joined` | User joined dashboard | `{ userId, username }` |
| `content-generation` | `progress` | AI generation progress | `{ taskId, progress, message }` |
| `content-generation` | `complete` | Generation completed | `{ taskId, result }` |
| `agent-status` | `agent-started` | AI agent task started | `{ agentId, taskId }` |
| `agent-status` | `agent-completed` | AI agent task finished | `{ agentId, taskId, result }` |

## Authentication Flow

### Private Channel Authorization

When subscribing to private channels, Pusher automatically calls the auth endpoint:

```typescript
// Backend endpoint: POST /api/v1/pusher/auth
{
  socket_id: "12345.67890",
  channel_name: "private-user-123"
}

// Response:
{
  auth: "key:signature"
}
```

### Presence Channel Authorization

For presence channels, additional user data is included:

```typescript
// Response for presence channels:
{
  auth: "key:signature",
  channel_data: {
    user_id: "123",
    user_info: {
      name: "John Doe",
      role: "student"
    }
  }
}
```

## Migration from WebSocket

### Legacy WebSocket Compatibility

The app maintains backward compatibility through:

1. **WebSocketProvider Context**: Wraps the app to provide WebSocket-like interface
2. **Adapter Pattern**: `pusherService` can emulate WebSocket methods
3. **Gradual Migration**: Components can be migrated one at a time

### Migration Checklist

When migrating a component from WebSocket to Pusher:

- [ ] Replace WebSocket event listeners with Pusher subscriptions
- [ ] Update event names to match Pusher convention
- [ ] Handle authentication for private channels
- [ ] Test real-time features with multiple clients
- [ ] Remove WebSocket-specific error handling
- [ ] Update component tests to mock Pusher instead of WebSocket

## Performance Considerations

### Connection Optimization

1. **Single Connection**: The app maintains one Pusher connection for all channels
2. **Lazy Channel Subscription**: Channels are only subscribed when needed
3. **Automatic Reconnection**: Pusher handles reconnection automatically
4. **Connection State Management**: Tracks connection state to prevent redundant operations

### Resource Management

```typescript
// Pusher automatically manages:
- Connection pooling
- Message batching
- Automatic fallback from WebSocket to HTTP long-polling
- Exponential backoff for reconnection attempts
```

## Error Handling

### Connection Errors

The app handles Pusher errors gracefully:

```typescript
pusherService.client.connection.bind('error', (error) => {
  logger.error('Pusher connection error:', error);
  // Show user-friendly error message
  showNotification('Real-time updates temporarily unavailable');
});
```

### State Change Monitoring

```typescript
pusherService.client.connection.bind('state_change', (states) => {
  logger.info(`Pusher state: ${states.previous} -> ${states.current}`);

  if (states.current === 'connected') {
    // Enable real-time features
  } else if (states.current === 'disconnected') {
    // Show offline indicator
  }
});
```

## Development Tools

### Debug Mode

In development, Pusher debug logging is enabled:

```typescript
if (process.env.NODE_ENV === 'development') {
  window.Pusher.logToConsole = true;
}
```

### Chrome DevTools Integration

The Pusher Debug Console Chrome extension can be used to:
- Monitor all Pusher events
- Inspect channel subscriptions
- Simulate connection issues
- Replay events for testing

## Testing

### Mocking Pusher in Tests

```typescript
// __mocks__/pusher-js.ts
export const mockPusher = {
  subscribe: jest.fn().mockReturnValue({
    bind: jest.fn(),
    unbind: jest.fn(),
    unsubscribe: jest.fn(),
  }),
  unsubscribe: jest.fn(),
  connection: {
    bind: jest.fn(),
    state: 'connected',
  },
};

jest.mock('pusher-js', () => mockPusher);
```

### Integration Tests

```typescript
describe('Pusher Integration', () => {
  it('connects when user is authenticated', async () => {
    const { result } = renderHook(() => useAuth());

    act(() => {
      result.current.login({ username: 'test', password: 'test' });
    });

    await waitFor(() => {
      expect(pusherService.connect).toHaveBeenCalled();
    });
  });

  it('disconnects when user logs out', async () => {
    const { result } = renderHook(() => useAuth());

    act(() => {
      result.current.logout();
    });

    await waitFor(() => {
      expect(pusherService.disconnect).toHaveBeenCalled();
    });
  });
});
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check VITE_PUSHER_KEY and VITE_PUSHER_CLUSTER are set
   - Verify network allows WebSocket connections
   - Check firewall rules for port 443 (WSS)

2. **Authentication Failed**
   - Ensure JWT token is valid
   - Verify auth endpoint returns correct format
   - Check CORS configuration on backend

3. **Events Not Received**
   - Confirm channel subscription successful
   - Verify event names match exactly
   - Check Pusher Debug Console for activity

4. **Performance Issues**
   - Reduce number of active channels
   - Implement message throttling
   - Use presence channels sparingly

## Best Practices

1. **Channel Naming**:
   - Use descriptive, hierarchical names
   - Include resource IDs for private channels
   - Follow Pusher naming conventions

2. **Event Payloads**:
   - Keep payloads small (< 10KB)
   - Use compression for large data
   - Implement pagination for lists

3. **Security**:
   - Always authenticate private channels
   - Validate user permissions server-side
   - Never expose sensitive data in public channels

4. **Scalability**:
   - Use channel presence sparingly
   - Implement client-side deduplication
   - Cache frequently accessed data

## Future Enhancements

### Planned Improvements

1. **Pusher Beams Integration**: Push notifications to mobile/desktop
2. **Channel Encryption**: End-to-end encryption for sensitive data
3. **Webhook Processing**: Handle Pusher webhooks for channel lifecycle events
4. **Analytics Integration**: Track real-time engagement metrics
5. **Fallback Mechanisms**: Implement polling fallback for restricted networks

### Migration Roadmap

| Phase | Components | Timeline | Status |
|-------|------------|----------|--------|
| 1 | Core notifications | Complete | ✅ |
| 2 | Dashboard updates | Complete | ✅ |
| 3 | Content generation | In Progress | 🔄 |
| 4 | Collaborative features | Planned | 📅 |
| 5 | Legacy WebSocket removal | Future | ⏳ |

## Related Documentation

- [Pusher Service Implementation](./pusher-service.md)
- [Real-time Features Guide](./realtime-features.md)
- [WebSocket Migration Guide](./websocket-migration.md)
- [Authentication Flow](../authentication/auth-flow.md)
- [Error Handling Patterns](../patterns/error-handling.md)