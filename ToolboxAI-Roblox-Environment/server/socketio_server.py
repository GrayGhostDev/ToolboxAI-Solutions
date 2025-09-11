"""
Socket.io Server Integration for FastAPI
Provides Socket.io protocol support for dashboard WebSocket connections
"""

import logging
from typing import Any, Dict, Optional, Tuple
import socketio
from fastapi import FastAPI
import json
from datetime import datetime, timezone

from .config import settings
from .rate_limit_manager import get_rate_limit_manager

logger = logging.getLogger(__name__)

# Socket.IO path contract (no trailing slash); must match dashboard and proxy config
SIO_PATH = "/socket.io"
assert not SIO_PATH.endswith("/"), "SIO_PATH must not end with a slash"

# Create Socket.io server with asyncio support
# Allow all origins in development, restrict in production
cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:5176",
    "http://127.0.0.1:5176",
    "http://localhost:5177",
    "http://127.0.0.1:5177",
    "http://localhost:5178",
    "http://127.0.0.1:5178",
    "http://localhost:5179",
    "http://127.0.0.1:5179",
    "http://localhost:5180",  # Current dashboard port
    "http://127.0.0.1:5180",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    "*"  # Allow all in development
]

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=cors_origins,
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1000000,
    allow_upgrades=True,
    http_compression=True,
    compression_threshold=1024,
    cookie=None,
    cors_credentials=True
)

# Optional: Debug namespace implementation to follow official namespacing pattern
class DebugNamespace(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ):
        try:
            safe_sid = str(sid)[:20].replace('\n', '').replace('\r', '')
            logger.info(f"[debug] Client {safe_sid} connected to /debug")
        except Exception:
            pass

    async def on_disconnect(self, sid):
        try:
            safe_sid = str(sid)[:20].replace('\n', '').replace('\r', '')
            logger.info(f"[debug] Client {safe_sid} disconnected from /debug")
        except Exception:
            pass

# Register namespace
sio.register_namespace(DebugNamespace('/debug'))

# Track connected clients
connected_clients: Dict[str, Dict[str, Any]] = {}

# RBAC helpers
_role_hierarchy = {"student": 1, "teacher": 2, "admin": 3}

def _get_required_roles() -> Dict[str, str]:
    try:
        mapping = getattr(settings, "SIO_RBAC_REQUIRED_ROLES", None)
        if isinstance(mapping, dict):
            return {str(k): str(v) for k, v in mapping.items()}
    except Exception:
        pass
    # Fallback to WS mapping if SIO mapping not defined
    try:
        mapping = getattr(settings, "WS_RBAC_REQUIRED_ROLES", {}) or {}
        if isinstance(mapping, dict):
            return {str(k): str(v) for k, v in mapping.items()}
    except Exception:
        pass
    return {}

def _get_user_role(sid: str) -> str:
    info = connected_clients.get(sid) or {}
    return info.get("role") or ("teacher" if info.get("authenticated") else "student")

def _is_authorized_for_event(sid: str, event: str) -> Tuple[bool, Optional[str]]:
    req_roles = _get_required_roles()
    required = req_roles.get(event)
    if not required:
        return True, None
    role = _get_user_role(sid)
    if _role_hierarchy.get(role, 0) < _role_hierarchy.get(required, 0):
        return False, required
    return True, None

async def _check_sio_rate_limit(sid: str, event: str) -> Tuple[bool, int]:
    try:
        rlm = get_rate_limit_manager()
        identifier = f"sio:{connected_clients.get(sid, {}).get('user_id') or sid}"
        endpoint = f"event:{event}"
        limit = getattr(settings, "SIO_RATE_LIMIT_PER_MINUTE", None) or settings.RATE_LIMIT_PER_MINUTE
        allowed, retry_after = await rlm.check_rate_limit(
            identifier=identifier,
            endpoint=endpoint,
            max_requests=limit,
            window_seconds=60,
            source="socketio",
        )
        return allowed, retry_after
    except Exception:
        return True, 0

async def _emit_message_to_sid(sid: str, msg_type: str, payload: Any = None, channel: Optional[str] = None):
    """Emit a typed message to a specific client using the unified 'message' event."""
    message = {
        'type': msg_type,
        'payload': payload,
        'channel': channel,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    await sio.emit('message', message, room=sid)


def _ack(ok: bool, **kwargs) -> Dict[str, Any]:
    """Small, consistent acknowledgment payload for Socket.IO callbacks.

    Returning a dict from an event handler will be delivered to the client's
    acknowledgment callback. Keep payload minimal to reduce bandwidth.
    """
    return {"ok": bool(ok), **kwargs, "ts": datetime.now(timezone.utc).isoformat()}

@sio.event
async def connect(sid: str, environ: dict, auth: Optional[Dict] = None):
    """Handle client connection"""
    try:
        # Sanitize remote address for logging to prevent log injection
        raw_addr = str(environ.get('REMOTE_ADDR', 'unknown'))
        remote_addr = ''.join(c for c in raw_addr if c.isalnum() or c in '.:[]')[:50]
        logger.info(f"Client {sid[:20]} connected from {remote_addr}")

        # Extract token from multiple sources
        token = None
        if auth and isinstance(auth, dict):
            token = auth.get('token')

        # Also check query parameters for token
        if not token:
            query_string = environ.get('QUERY_STRING', '')
            if 'token=' in query_string:
                # Simple token extraction from query string
                for param in query_string.split('&'):
                    if param.startswith('token='):
                        token = param.split('=', 1)[1]
                        break

        # Store client info with timezone-aware datetime
        from datetime import datetime, timezone
        connected_clients[sid] = {
            'connected_at': datetime.now(timezone.utc).isoformat(),
            'auth': auth,
            'token': token,
            'authenticated': False,
            'remote_addr': remote_addr
        }

        # If token exists, try light validation to set initial role/authenticated
        if token:
            try:
                from .auth import JWTManager
                payload = JWTManager.verify_token(token, raise_on_error=False)
                if payload:
                    connected_clients[sid]['authenticated'] = True
                    connected_clients[sid]['user_id'] = payload.get('sub')
                    connected_clients[sid]['username'] = payload.get('username')
                    connected_clients[sid]['role'] = payload.get('role', 'student')
            except Exception:
                # Ignore errors here, allow explicit authenticate event to finalize
                pass

        # Send connection acknowledgment (optional informational event)
        await sio.emit('connected', {
            'message': 'Successfully connected to Socket.io server',
            'sid': sid,
            'authenticated': connected_clients[sid]['authenticated'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, room=sid)

        # Sanitize sid for logging to prevent log injection
        safe_sid = ''.join(c for c in str(sid) if c.isalnum() or c in '-_')[:20]
        logger.info(f"Client {safe_sid} connection established successfully")
        return True

    except Exception as e:
        # Sanitize error message for logging
        safe_error = str(e)[:200].replace('\n', '').replace('\r', '')
        logger.error(f"Connection error for {sid[:20]}: {safe_error}")

        # Send error response to client
        try:
            await sio.emit('connect_error', {
                'error': 'Connection failed',
                'message': 'Unable to establish connection'
            }, room=sid)
        except:
            pass

        return False

@sio.event
async def disconnect(sid: str):
    """Handle client disconnection"""
    safe_sid = str(sid)[:20].replace('\n', '').replace('\r', '')
    logger.info(f"Client {safe_sid} disconnected")

    # Remove client from tracking
    if sid in connected_clients:
        del connected_clients[sid]

@sio.event
async def authenticate(sid: str, data: Dict[str, Any]):
    """Handle authentication"""
    try:
        # Sanitize sid for logging
        safe_sid = str(sid)[:20].replace('\n', '').replace('\r', '')
        logger.debug(f"Authentication request from {safe_sid}")

        if not isinstance(data, dict):
            await sio.emit('auth_failed', {
                'error': 'Invalid authentication data format'
            }, room=sid)
            return False

        token = data.get('token')
        if not token or not isinstance(token, str):
            await sio.emit('auth_failed', {
                'error': 'No valid token provided'
            }, room=sid)
            return False

        # Validate token with auth service
        try:
            from .auth import JWTManager
            payload = JWTManager.verify_token(token, raise_on_error=False)

            if not payload:
                await sio.emit('auth_failed', {
                    'error': 'Invalid or expired token'
                }, room=sid)
                return False

            # Update client info if exists
            if sid in connected_clients:
                connected_clients[sid]['authenticated'] = True
                connected_clients[sid]['user_id'] = payload.get('sub')
                connected_clients[sid]['username'] = payload.get('username')
                connected_clients[sid]['role'] = payload.get('role', 'student')
            else:
                logger.warning(f"Authentication for unknown client {safe_sid}")
                return False

            await sio.emit('auth_success', {
                'message': 'Authentication successful',
                'user_id': payload.get('sub'),
                'username': payload.get('username')
            }, room=sid)

            logger.info(f"Client {safe_sid} authenticated successfully")
            return True

        except ImportError:
            # Fallback for development - accept any token
            logger.warning("Auth service not available, using development mode")

            if sid in connected_clients:
                connected_clients[sid]['authenticated'] = True
                connected_clients[sid]['user_id'] = data.get('user_id', 'dev-user')

            await sio.emit('auth_success', {
                'message': 'Authentication successful (dev mode)',
                'user_id': data.get('user_id', 'dev-user')
            }, room=sid)

            return True

    except Exception as e:
        # Sanitize error for logging
        safe_error = str(e)[:200].replace('\n', '').replace('\r', '')
        logger.error(f"Authentication error for {sid[:20]}: {safe_error}")

        await sio.emit('auth_failed', {
            'error': 'Authentication failed'
        }, room=sid)

        return False

@sio.event
async def refresh_token(sid: str, data: Dict[str, Any]):
    """Handle token refresh from client"""
    try:
        if not isinstance(data, dict) or not data.get('token'):
            await sio.emit('token_refreshed', {'success': False, 'error': 'No token provided'}, room=sid)
            return {'success': False, 'error': 'No token provided'}

        new_token = data['token']
        from .auth import JWTManager
        payload = JWTManager.verify_token(new_token, raise_on_error=False)
        if not payload:
            await sio.emit('token_refreshed', {'success': False, 'error': 'Invalid token'}, room=sid)
            return {'success': False, 'error': 'Invalid token'}

        # Update client info
        if sid in connected_clients:
            connected_clients[sid]['authenticated'] = True
            connected_clients[sid]['user_id'] = payload.get('sub')
            connected_clients[sid]['username'] = payload.get('username')
            connected_clients[sid]['role'] = payload.get('role', 'student')

        await sio.emit('token_refreshed', {
            'success': True,
            'expires_at': payload.get('exp')
        }, room=sid)
        return {'success': True}
    except Exception as e:
        safe_error = str(e)[:200].replace('\n', '').replace('\r', '')
        logger.error(f"Token refresh error for {sid[:20]}: {safe_error}")
        await sio.emit('token_refreshed', {'success': False, 'error': 'Token refresh failed'}, room=sid)
        return {'success': False, 'error': 'Token refresh failed'}

@sio.event
async def message(sid: str, data: Any):
    """Handle generic typed message from client and route by 'type'"""
    try:
        # Ensure data is a dict
        if not isinstance(data, dict):
            await _emit_message_to_sid(sid, 'error', {'error': 'Invalid message format'})
            return _ack(False, error='invalid_format')

        msg_type = str(data.get('type', '')).lower()
        payload = data.get('payload')

        # Rate limit check per message type
        allowed, retry_after = await _check_sio_rate_limit(sid, msg_type or 'message')
        if not allowed:
            await _emit_message_to_sid(sid, 'error', {
                'error': f'Rate limit exceeded. Retry after {retry_after} seconds',
                'event': msg_type
            })
            return _ack(False, error='rate_limited', retry_after=retry_after, event=msg_type)

        # RBAC check (use message type)
        authorized, required = _is_authorized_for_event(sid, msg_type)
        if not authorized:
            await _emit_message_to_sid(sid, 'error', {
                'error': f"Forbidden: requires role '{required}'",
                'event': msg_type
            })
            return _ack(False, error='forbidden', required_role=required, event=msg_type)

        # Dispatch by message type
        if msg_type == 'ping':
            # Use engine-style pong event to satisfy client handler
            await sio.emit('pong', {'timestamp': datetime.now(timezone.utc).isoformat()}, room=sid)
            return _ack(True, type='ping')

        if msg_type == 'subscribe':
            channels = []
            # Accept payload as {channels: [..]} or string channel for flexibility
            if isinstance(payload, dict) and isinstance(payload.get('channels'), list):
                channels = [str(c) for c in payload.get('channels')]
            elif isinstance(payload, str):
                channels = [payload]
            # Validate and enter rooms
            subscribed = []
            for channel in channels:
                if not channel or len(channel) > 100 or not str(channel).replace('_', '').replace('-', '').isalnum():
                    continue
                # Channel RBAC by prefix
                try:
                    prefix_map = getattr(settings, "WS_CHANNEL_ROLE_PREFIXES", {}) or {}
                    required_for_channel = None
                    for prefix, req_role in prefix_map.items():
                        if channel.startswith(prefix):
                            required_for_channel = str(req_role)
                            break
                    if required_for_channel:
                        user_role = (connected_clients.get(sid) or {}).get('role', 'student')
                        if _role_hierarchy.get(user_role, 0) < _role_hierarchy.get(required_for_channel, 0):
                            # Skip forbidden channel
                            continue
                except Exception:
                    pass
                await sio.enter_room(sid, channel)
                subscribed.append(channel)
            # Acknowledge
            await _emit_message_to_sid(sid, 'subscribed', {'channels': subscribed, 'total': len(subscribed)})
            return _ack(True, action='subscribe', channels=subscribed, total=len(subscribed))

        if msg_type == 'unsubscribe':
            channels = []
            if isinstance(payload, dict) and isinstance(payload.get('channels'), list):
                channels = [str(c) for c in payload.get('channels')]
            elif isinstance(payload, str):
                channels = [payload]
            for channel in channels:
                try:
                    await sio.leave_room(sid, channel)
                except Exception:
                    pass
            await _emit_message_to_sid(sid, 'unsubscribed', {'channels': channels})
            return _ack(True, action='unsubscribe', channels=channels)

        if msg_type == 'broadcast':
            # Accept either payload { channel, data } or top-level message.channel with any payload
            channel = None
            data_to_send = None
            if isinstance(payload, dict) and ('channel' in payload or 'data' in payload):
                channel = payload.get('channel')
                data_to_send = payload.get('data')
            # Fallbacks
            if not channel:
                channel = data.get('channel') if isinstance(data, dict) else None
            if data_to_send is None:
                data_to_send = payload
            if isinstance(channel, str) and channel:
                await sio.emit('message', {
                    'type': 'broadcast',
                    'channel': channel,
                    'payload': data_to_send,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'sender': sid
                }, room=channel, skip_sid=sid)
                await _emit_message_to_sid(sid, 'broadcast_sent', {
                    'channel': channel
                })
                return _ack(True, action='broadcast', channel=channel)
            await _emit_message_to_sid(sid, 'error', {'error': 'Invalid broadcast payload'})
            return _ack(False, error='invalid_broadcast_payload')

        if msg_type in ('content_request', 'quiz_response', 'progress_update', 'collaboration_message', 'user_message'):
            # For now, just echo an acknowledgment as typed message; existing dedicated events remain for backward compatibility
            await _emit_message_to_sid(sid, f'{msg_type}_received', payload)
            return _ack(True, type=msg_type)

        # Default: echo original as acknowledgment
        await _emit_message_to_sid(sid, 'ack', {'received': True, 'type': msg_type})
        return _ack(True, type=msg_type)

    except Exception as e:
        safe_error = str(e)[:200].replace('\n', '').replace('\r', '')
        logger.error(f"Message handling error for {sid[:20]}: {safe_error}")
        await _emit_message_to_sid(sid, 'error', {'error': 'Message handling failed'})
        return _ack(False, error='message_handling_failed')

@sio.event
async def ping(sid: str, data: Optional[Dict] = None):
    """Handle ping from client (legacy event)"""
    # Rate limit check
    allowed, retry_after = await _check_sio_rate_limit(sid, 'ping')
    if not allowed:
        await sio.emit('error', {
            'error': f'Rate limit exceeded. Retry after {retry_after} seconds',
            'event': 'ping'
        }, room=sid)
        return
    await sio.emit('pong', {
        'timestamp': datetime.now(timezone.utc).isoformat()
    }, room=sid)
    return _ack(True, event='ping')

@sio.event
async def subscribe(sid: str, data: Dict[str, Any]):
    """Handle channel subscription (legacy event)"""
    try:
        # Rate limit check
        allowed, retry_after = await _check_sio_rate_limit(sid, 'subscribe')
        if not allowed:
            await sio.emit('subscription_error', {
                'error': f'Rate limit exceeded. Retry after {retry_after} seconds'
            }, room=sid)
            return

        if not isinstance(data, dict):
            await sio.emit('subscription_error', {
                'error': 'Invalid subscription data format'
            }, room=sid)
            return

        channel = data.get('channel')
        if not channel or not isinstance(channel, str):
            await sio.emit('subscription_error', {
                'error': 'Invalid channel name'
            }, room=sid)
            return

        # Validate channel name (basic security)
        if len(channel) > 100 or not channel.replace('_', '').replace('-', '').isalnum():
            await sio.emit('subscription_error', {
                'error': 'Invalid channel format'
            }, room=sid)
            return

        # Check if client is authenticated for protected channels
        if sid in connected_clients and not connected_clients[sid].get('authenticated', False):
            if channel.startswith('private_') or channel.startswith('user_'):
                await sio.emit('subscription_error', {
                    'error': 'Authentication required for this channel'
                }, room=sid)
                return

        # Role-based restrictions by channel prefix
        try:
            from .config import settings
            prefix_map = getattr(settings, "WS_CHANNEL_ROLE_PREFIXES", {}) or {}
            required_for_channel = None
            for prefix, req_role in prefix_map.items():
                if channel.startswith(prefix):
                    required_for_channel = str(req_role)
                    break
            if required_for_channel:
                user_role = (connected_clients.get(sid) or {}).get('role', 'student')
                role_hierarchy = {"student": 1, "teacher": 2, "admin": 3}
                if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_for_channel, 0):
                    await sio.emit('subscription_error', {
                        'error': f"Forbidden: channel requires role '{required_for_channel}'"
                    }, room=sid)
                    return
        except Exception:
            pass

        await sio.enter_room(sid, channel)

        # Sanitize for logging
        safe_sid = str(sid)[:20].replace('\n', '').replace('\r', '')
        safe_channel = str(channel)[:50].replace('\n', '').replace('\r', '')
        logger.info(f"Client {safe_sid} subscribed to channel: {safe_channel}")

        await sio.emit('subscribed', {
            'channel': channel,
            'message': f'Successfully subscribed to {channel}'
        }, room=sid)
        return _ack(True, action='subscribe', channel=channel)

    except Exception as e:
        safe_error = str(e)[:200].replace('\n', '').replace('\r', '')
        logger.error(f"Subscription error for {sid[:20]}: {safe_error}")

        await sio.emit('subscription_error', {
            'error': 'Subscription failed'
        }, room=sid)

@sio.event
async def unsubscribe(sid: str, data: Dict[str, Any]):
    """Handle channel unsubscription (legacy event)"""
    channel = data.get('channel')
    if channel:
        sio.leave_room(sid, channel)
        safe_sid = str(sid)[:20].replace('\n', '').replace('\r', '')
        safe_channel = str(channel)[:50].replace('\n', '').replace('\r', '')
        logger.info(f"Client {safe_sid} unsubscribed from channel: {safe_channel}")

        await sio.emit('unsubscribed', {
            'channel': channel,
            'message': f'Successfully unsubscribed from {channel}'
        }, room=sid)
        return _ack(True, action='unsubscribe', channel=channel)

# WebSocket message types from dashboard (legacy dedicated events retained)
@sio.event
async def content_request(sid: str, data: Dict[str, Any]):
    """Handle content generation request"""
    safe_sid = str(sid)[:20].replace('\n', '').replace('\r', '')
    logger.info(f"Content request from {safe_sid}")

    # RBAC check
    authorized, required = _is_authorized_for_event(sid, 'content_request')
    if not authorized:
        await sio.emit('error', {
            'error': f"Forbidden: requires role '{required}'",
            'event': 'content_request'
        }, room=sid)
        return _ack(False, error='forbidden', required_role=required, event='content_request')

    # Rate limit check
    allowed, retry_after = await _check_sio_rate_limit(sid, 'content_request')
    if not allowed:
        await sio.emit('error', {
            'error': f'Rate limit exceeded. Retry after {retry_after} seconds',
            'event': 'content_request'
        }, room=sid)
        return _ack(False, error='rate_limited', retry_after=retry_after, event='content_request')

    # TODO: Integrate with content generation service
    await sio.emit('content_progress', {
        'status': 'processing',
        'progress': 0,
        'message': 'Content generation started'
    }, room=sid)
    return _ack(True, event='content_request')

@sio.event
async def quiz_response(sid: str, data: Dict[str, Any]):
    """Handle quiz response from student"""
    safe_sid = str(sid)[:20].replace('\n', '').replace('\r', '')
    logger.info(f"Quiz response from {safe_sid}")

    # RBAC check
    authorized, required = _is_authorized_for_event(sid, 'quiz_response')
    if not authorized:
        await sio.emit('error', {
            'error': f"Forbidden: requires role '{required}'",
            'event': 'quiz_response'
        }, room=sid)
        return

    # Rate limit check
    allowed, retry_after = await _check_sio_rate_limit(sid, 'quiz_response')
    if not allowed:
        await sio.emit('error', {
            'error': f'Rate limit exceeded. Retry after {retry_after} seconds',
            'event': 'quiz_response'
        }, room=sid)
        return

    # Process quiz response with actual logic
    quiz_id = data.get('quiz_id')
    answers = data.get('answers', [])

    # Basic quiz evaluation
    correct_count = 0
    total_questions = len(answers)

    for answer in answers:
        if answer.get('selected') == answer.get('correct'):
            correct_count += 1

    score = (correct_count / total_questions * 100) if total_questions > 0 else 0
    is_correct = score >= 70

    await sio.emit('quiz_feedback', {
        'correct': is_correct,
        'feedback': 'Great work!' if is_correct else 'Keep practicing!',
        'score': score
    }, room=sid)
    return _ack(True, event='quiz_response', score=score)

@sio.event
async def progress_update(sid: str, data: Dict[str, Any]):
    """Handle progress update"""
    safe_sid = str(sid)[:20].replace('\n', '').replace('\r', '')
    logger.info(f"Progress update from {safe_sid}")

    # RBAC check
    authorized, required = _is_authorized_for_event(sid, 'progress_update')
    if not authorized:
        await sio.emit('error', {
            'error': f"Forbidden: requires role '{required}'",
            'event': 'progress_update'
        }, room=sid)
        return

    # Rate limit check
    allowed, retry_after = await _check_sio_rate_limit(sid, 'progress_update')
    if not allowed:
        await sio.emit('error', {
            'error': f'Rate limit exceeded. Retry after {retry_after} seconds',
            'event': 'progress_update'
        }, room=sid)
        return

    # Broadcast to relevant channels (e.g., teacher dashboard)
    await sio.emit('student_progress', data, room='teacher_updates')
    return _ack(True, event='progress_update')

@sio.event
async def collaboration_message(sid: str, data: Dict[str, Any]):
    """Handle collaboration message"""
    # RBAC check
    authorized, required = _is_authorized_for_event(sid, 'collaboration_message')
    if not authorized:
        await sio.emit('error', {
            'error': f"Forbidden: requires role '{required}'",
            'event': 'collaboration_message'
        }, room=sid)
        return

    # Rate limit check
    allowed, retry_after = await _check_sio_rate_limit(sid, 'collaboration_message')
    if not allowed:
        await sio.emit('error', {
            'error': f'Rate limit exceeded. Retry after {retry_after} seconds',
            'event': 'collaboration_message'
        }, room=sid)
        return

    room_id = data.get('roomId')
    if room_id:
        # Broadcast to all users in the collaboration room
        await sio.emit('collaboration_event', {
            'from': sid,
            'message': data.get('message'),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, room=f'collaboration_{room_id}', skip_sid=sid)
        return _ack(True, event='collaboration_message', room_id=room_id)
    return _ack(False, error='invalid_room_id')

# Public functions for other services to emit events
async def emit_to_user(user_id: str, event: str, data: Any):
    """Emit event to specific user"""
    # Find sid by user_id
    for sid, client_info in connected_clients.items():
        if client_info.get('user_id') == user_id:
            await sio.emit(event, data, room=sid)
            break

async def emit_to_channel(channel: str, event: str, data: Any):
    """Emit event to all users in a channel"""
    await sio.emit(event, data, room=channel)

async def broadcast_event(event: str, data: Any):
    """Broadcast event to all connected clients"""
    await sio.emit(event, data)

def create_socketio_app(app: FastAPI) -> socketio.ASGIApp:
    """
    Create Socket.io ASGI app and mount it on FastAPI

    Args:
        app: FastAPI application instance

    Returns:
        Socket.io ASGI app
    """
    # Create Socket.io ASGI app
    socketio_app = socketio.ASGIApp(
        sio,
        other_asgi_app=app,
        socketio_path=SIO_PATH
    )

    logger.info("Socket.io server initialized on /socket.io")

    return socketio_app

# Export for use in main.py
__all__ = [
    'sio',
    'create_socketio_app',
    'emit_to_user',
    'emit_to_channel',
    'broadcast_event',
    'connected_clients'
]