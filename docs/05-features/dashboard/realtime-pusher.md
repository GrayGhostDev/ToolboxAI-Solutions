# Realtime (Pusher) Integration for Dashboard

This document explains how the Dashboard uses Pusher Channels for realtime features and how to run it locally.

Prerequisites
- Pusher Channels app (App ID, Key, Secret, Cluster)
- FastAPI backend running locally on 127.0.0.1:8008
- Node 20.x for the dashboard
- Python 3.11+ for backend

Environment variables

Backend (apps/backend/.env):
- PUSHER_ENABLED=true
- PUSHER_APP_ID=<your-app-id>
- PUSHER_KEY=<your-key>
- PUSHER_SECRET=<your-secret>
- PUSHER_CLUSTER=us2

Frontend (apps/dashboard/.env):
- VITE_API_BASE_URL=http://localhost:8008
- VITE_WS_URL=http://localhost:8008
- VITE_PUSHER_KEY=<your-key>
- VITE_PUSHER_CLUSTER=us2
- VITE_PUSHER_AUTH_ENDPOINT=http://localhost:8008/pusher/auth
- VITE_ENABLE_WEBSOCKET=true

Key endpoints (backend)
- POST /pusher/auth — Authenticates private/presence channel subscriptions
- POST /realtime/trigger — Triggers a Channels event server-side
- POST /pusher/webhook — Handles Pusher webhooks (occupied, vacated, presence, etc.)

Frontend usage
- The dashboard wraps realtime usage in a WebSocketService that uses pusher-js under the hood.
- Subscribe:
  - subscribeToChannel('public', handler, (msg) => msg.type === 'some_event')
- Send (server trigger):
  - sendWebSocketMessage('some_event', { any: 'payload' }, { channel: 'public' })

Testing notes
- Unit tests mock the WebSocketContext provider and hooks to avoid network.
- For jsdom, chart libraries requiring canvas or ResizeObserver should be mocked (see src/test/setup.ts) to prevent errors.

Troubleshooting
- If connect fails with Missing Pusher key configuration, ensure VITE_PUSHER_KEY is set during build/test or mock the service.
- If events don’t arrive, verify:
  - Backend env has PUSHER_* set and PUSHER_ENABLED=true
  - /realtime/trigger returns 200
  - Pusher dashboard shows connections and events

