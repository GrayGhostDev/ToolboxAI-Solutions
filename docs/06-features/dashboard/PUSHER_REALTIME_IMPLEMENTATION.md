# Pusher.io Realtime Implementation

## Overview

As of September 2025, ToolBoxAI uses **Pusher.io** for all realtime communication features, replacing WebSocket connections that were causing issues in Docker environments.

## Configuration

### Pusher Credentials (Production)

```bash
PUSHER_APP_ID=2050001
PUSHER_KEY=487b104d996aaa9ef148
PUSHER_SECRET=45e89fd91f50fe615235
PUSHER_CLUSTER=us2
```

### Environment Files

1. **Backend (.env)**
   - Contains Pusher app credentials
   - Located at: `/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.env`

2. **Frontend (.env.local)**
   - Contains public Pusher key
   - Located at: `/apps/dashboard/.env.local`

3. **Docker (docker-compose.dev.yml)**
   - Automatically configured with Pusher credentials
   - HMR disabled in Docker to prevent WebSocket conflicts

## Channels

### Public Channels
- `dashboard-updates` - General dashboard notifications
- `content-generation` - Content creation progress
- `agent-status` - Agent activity monitoring

### Private Channels
- `private-user-{userId}` - User-specific notifications
- `private-class-{classId}` - Class-specific updates

### Presence Channels
- `presence-classroom-{roomId}` - Track online users in classrooms
- `presence-admin` - Track online administrators

## API Endpoints

### Authentication
```
POST /api/v1/pusher/auth
```
Authenticates private and presence channels

### Webhook
```
POST /pusher/webhook
```
Handles Pusher webhook events (channel occupied/vacated, member added/removed)

### Webhook Configuration in Pusher Dashboard

1. Go to https://dashboard.pusher.com/
2. Select app (ID: 2050001)
3. Navigate to **Webhooks**
4. Add webhook URL:
   - Development: `http://localhost:8009/pusher/webhook`
   - Production: `https://your-domain.com/pusher/webhook`
5. Enable events:
   - ✅ Channel occupied
   - ✅ Channel vacated
   - ✅ Member added
   - ✅ Member removed

## Docker Configuration

### Key Changes
1. **HMR Disabled**: Hot Module Replacement is disabled in Docker (`DOCKER_ENV=true`)
2. **Pusher Only**: All realtime features use Pusher, no WebSocket connections
3. **No Port Conflicts**: Pusher uses external infrastructure, eliminating port issues

### Environment Variables in Docker
```yaml
# Frontend
VITE_PUSHER_KEY: 487b104d996aaa9ef148
VITE_PUSHER_CLUSTER: us2
VITE_PUSHER_AUTH_ENDPOINT: http://fastapi-main:8009/api/v1/pusher/auth

# Backend
PUSHER_APP_ID: 2050001
PUSHER_KEY: 487b104d996aaa9ef148
PUSHER_SECRET: 45e89fd91f50fe615235
PUSHER_CLUSTER: us2
```

## Frontend Usage

### Service Location
`/apps/dashboard/src/services/pusher.ts`

### Example Usage
```typescript
import { pusherService } from '@/services/pusher';

// Subscribe to a channel
pusherService.subscribe('dashboard-updates', (data) => {
  console.log('Update received:', data);
});

// Trigger an event (via backend API)
await api.post('/api/v1/realtime/trigger', {
  channel: 'dashboard-updates',
  event: 'notification',
  data: { message: 'Hello World' }
});
```

## Backend Usage

### Service Location
`/apps/backend/services/pusher.py`

### Example Usage
```python
from apps.backend.services.pusher import pusher_client

# Trigger an event
pusher_client.trigger(
    'dashboard-updates',
    'notification',
    {'message': 'Hello from backend'}
)

# Trigger to multiple channels
pusher_client.trigger(
    ['channel-1', 'channel-2'],
    'event-name',
    {'data': 'payload'}
)
```

## Benefits of Using Pusher

1. **No WebSocket Issues**: Eliminates Docker WebSocket connection problems
2. **Managed Infrastructure**: Pusher handles scaling and reliability
3. **Built-in Features**: Presence channels, webhooks, and authentication
4. **Better Debugging**: Pusher Dashboard for monitoring events
5. **Cross-Platform**: Works seamlessly across Docker, local, and production

## Migration from WebSocket

### Previous Issues
- WebSocket HMR connection failures in Docker
- Port conflicts and network isolation issues
- Complex proxy configuration requirements

### Current Solution
- Pusher.io handles all realtime communication
- No local WebSocket servers required
- Simplified Docker configuration
- Reliable message delivery

## Monitoring

1. **Pusher Dashboard**: https://dashboard.pusher.com/
   - View real-time connections
   - Monitor message throughput
   - Debug channel subscriptions

2. **Application Logs**
   - Frontend: Browser console shows Pusher events
   - Backend: Check Docker logs for Pusher activity

## Troubleshooting

### Issue: Authentication Failures
- Verify `PUSHER_SECRET` matches in backend and Pusher Dashboard
- Check CORS settings allow your domain
- Ensure auth endpoint is accessible

### Issue: Messages Not Received
- Verify channel subscription in Pusher Dashboard
- Check if events are being triggered (visible in Dashboard)
- Ensure correct channel names (case-sensitive)

### Issue: Docker Connection Issues
- Pusher connections go through external infrastructure
- No Docker networking issues as with WebSockets
- Check internet connectivity from container

## Security Notes

1. **Never expose `PUSHER_SECRET`** in frontend code
2. **Use private channels** for sensitive data
3. **Implement proper authentication** for private/presence channels
4. **Validate webhook signatures** from Pusher

## Future Considerations

- Consider implementing end-to-end encryption for sensitive messages
- Set up cluster-specific configurations for global deployment
- Implement rate limiting on trigger endpoints
- Add monitoring and alerting for Pusher quota usage

---

*Last Updated: September 21, 2025*
*Configuration verified and tested in Docker environment*