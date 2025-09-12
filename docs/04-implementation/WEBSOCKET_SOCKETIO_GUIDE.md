# WebSocket & Socket.IO Integration Guide

This guide documents the ToolboxAI Socket.IO and WebSocket implementation for the dashboard and FastAPI backend. It captures the path contracts, client usage, reverse proxy configuration, and acknowledgment behavior.

## Path contract

- Socket.IO path (engine endpoint): `/socket.io` (no trailing slash)
- Do not use `/socket.io/` — the trailing slash can break the handshake in some environments.
- In code, the backend defines a single constant `SIO_PATH = "/socket.io"` and uses it in the ASGI mount.

## Client usage (official guidance)

- Use the same path `/socket.io` on the client.
- Pass namespaces in the URL, not as a separate option.

Example (dashboard):

```ts path=null start=null
import { io } from 'socket.io-client';
import { WS_URL, SIO_PATH } from '../config';

// default namespace ("/")
const socket = io(WS_URL, { path: SIO_PATH, transports: ['websocket', 'polling'] });

// debug namespace
const debugSocket = io(`${WS_URL}/debug`, { path: SIO_PATH });
```

## Backend (FastAPI + python-socketio)

- The server creates an `AsyncServer` and mounts it with `socketio.ASGIApp` at `SIO_PATH`.
- Acks: returning a value from a Socket.IO event handler is delivered to the client acknowledgment callback.

Example excerpt:

```python path=/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/server/socketio_server.py start=110
async def _emit_message_to_sid(sid: str, msg_type: str, payload: Any = None, channel: Optional[str] = None):
    # ...

def _ack(ok: bool, **kwargs) -> Dict[str, Any]:
    return {"ok": bool(ok), **kwargs, "ts": datetime.now(timezone.utc).isoformat()}

@sio.event
async def message(sid: str, data: Any):
    # ... validations ...
    return _ack(True, type=msg_type)
```

### Namespaces

- Namespaces are registered with `sio.register_namespace(...)`. We include a `DebugNamespace('/debug')` as a template.

## Reverse proxy (Nginx)

- Add a dedicated location that proxies `/socket.io` to the FastAPI backend with upgrade headers and long timeouts:

```nginx path=/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/config/production/nginx.conf start=109
location /socket.io {
    proxy_pass http://fastapi_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 86400;
    proxy_send_timeout 86400;
    proxy_buffering off;
}
```

## Health & diagnostics

- The backend exposes `GET /socketio/status` with keys like `connected`, `authenticated`, `acks_enabled`, and `path`.
- In debug mode, the dashboard’s ConnectionStatus widget fetches this endpoint every 30s to display diagnostics.

## Acknowledgment contract

- The dashboard uses optional awaitAcknowledgment when emitting events.
- The backend returns a small ack payload for `message`, `ping`, `subscribe`, `unsubscribe`, `broadcast`, `content_request`, `quiz_response`, `progress_update`, and `collaboration_message`.

Ack shape (example):

```json path=null start=null
{ "ok": true, "event": "progress_update", "ts": "2025-09-11T21:00:00Z" }
```

## Security

- Pass tokens via `auth: { token }` and (optionally) `Authorization` header. Server performs JWT validation where needed.
- Enforce RBAC and rate limiting on server handlers; return negative acks on violations.
- Keep origins restricted in production and enforce `TrustedHostMiddleware` with production domains.

## Testing

- We include basic tests for status and ack behavior:
  - `tests/integration/test_socketio_status.py` — verifies `/socketio/status` returns `path` and `acks_enabled`.
  - `tests/integration/test_socketio.py` — connects to Socket.IO and asserts ack on a typed message.

