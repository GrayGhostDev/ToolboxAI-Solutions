"""
WebSocket Authentication Helpers for FastAPI WebSocket Endpoints

Provides authentication utilities specifically designed for FastAPI WebSocket
connections, integrating with the existing JWT authentication system.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import WebSocket, Query, Header
from fastapi.websockets import WebSocketState

from .auth import JWTManager, User, AuthenticationError
from .models import Session

logger = logging.getLogger(__name__)


class WebSocketAuthSession:
    """
    Manages authenticated WebSocket session state
    """
    
    def __init__(self, websocket: WebSocket, user: User, token_payload: Dict[str, Any]):
        self.websocket = websocket
        self.user = user
        self.token_payload = token_payload
        self.authenticated_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
        self.is_active = True
        self.session_id = f"ws_{user.id}_{int(self.authenticated_at.timestamp())}"
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now(timezone.utc)
    
    async def send_auth_message(self, message_type: str, data: Dict[str, Any] = None):
        """Send authentication-related message to client"""
        # Only enforce client_state check when attribute exists (Mocks may not have it)
        try:
            state = getattr(self.websocket, "client_state", None)
            if state is not None:
                # If state is a Mock or unknown type, treat as connected in tests
                if isinstance(state, WebSocketState):
                    if state != WebSocketState.CONNECTED:
                        return False
                # else: non-enum types are treated as connected
        except Exception:
            # If client_state is not accessible, proceed
            pass
        
        try:
            message = {
                "type": message_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": self.session_id,
                **(data or {})
            }
            
            await self.websocket.send_text(json.dumps(message))
            return True
            
        except Exception as e:
            logger.error(f"Failed to send auth message: {e}")
            return False
    
    async def close_with_auth_error(self, reason: str, code: int = 4001):
        """Close connection with authentication error"""
        await self.send_auth_message("auth_error", {"reason": reason, "code": code})
        try:
            await self.websocket.close(code=code, reason=reason)
        except Exception:
            pass
        self.is_active = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for logging/monitoring"""
        return {
            "session_id": self.session_id,
            "user_id": self.user.id,
            "username": self.user.username,
            "role": self.user.role,
            "authenticated_at": self.authenticated_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_active": self.is_active
        }


class FastAPIWebSocketAuthenticator:
    """
    FastAPI WebSocket authentication manager
    
    Features:
    - JWT token validation using existing auth system
    - Session management for WebSocket connections
    - Token refresh handling
    - Authentication middleware integration
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, WebSocketAuthSession] = {}
    
    async def authenticate_connection(
        self,
        websocket: WebSocket,
        token: Optional[str] = None
    ) -> Optional[WebSocketAuthSession]:
        """
        Authenticate WebSocket connection using JWT token
        
        Args:
            websocket: FastAPI WebSocket instance
            token: JWT token (optional, will be extracted if not provided)
            
        Returns:
            WebSocketAuthSession if authentication successful, None otherwise
        """
        try:
            # Extract token if not provided
            if not token:
                token = await self._extract_token_from_websocket(websocket)
            
            if not token:
                logger.warning("No authentication token provided for WebSocket connection")
                await self._send_auth_error(websocket, "Authentication token required", 4001)
                return None
            
            # Validate token using existing JWT manager
            try:
                payload = JWTManager.verify_token(token, raise_on_error=False)
                if not payload:
                    logger.warning("Invalid JWT token for WebSocket connection")
                    await self._send_auth_error(websocket, "Invalid authentication token", 4001)
                    return None
            except AuthenticationError as e:
                logger.warning(f"JWT validation failed: {e.detail}")
                await self._send_auth_error(websocket, e.detail, 4001)
                return None
            
            # Extract user information from payload
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("No user ID in JWT token payload")
                await self._send_auth_error(websocket, "Invalid token payload", 4001)
                return None
            
            # Create user object
            user = User(
                id=user_id,
                username=payload.get("username", "unknown"),
                email=payload.get("email", "unknown@example.com"),
                role=payload.get("role", "student")
            )
            
            # Create authenticated session
            session = WebSocketAuthSession(websocket, user, payload)
            self.active_sessions[session.session_id] = session
            
            # Send authentication success message
            await session.send_auth_message("auth_success", {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role
                },
                "features": ["token_refresh", "real_time_updates", "secure_messaging"]
            })
            
            logger.info(f"WebSocket authentication successful for user {user_id} (session {session.session_id})")
            return session
            
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            await self._send_auth_error(websocket, "Authentication failed", 4001)
            return None
    
    async def _extract_token_from_websocket(self, websocket: WebSocket) -> Optional[str]:
        """
        Extract JWT token from WebSocket connection
        
        Token sources (in order of precedence):
        1. Query parameter: ?token=<jwt>
        2. Authorization header: Authorization: Bearer <jwt>
        3. Cookie: access_token=<jwt>
        """
        try:
            # 1. Check query parameters
            if "token" in websocket.query_params:
                token = websocket.query_params["token"]
                if token:
                    logger.debug("Token extracted from query parameters")
                    return token
            
            # 2. Check Authorization header
            auth_header = websocket.headers.get("authorization", "")
            if not auth_header:
                auth_header = websocket.headers.get("Authorization", "")
            
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]  # Remove 'Bearer ' prefix
                logger.debug("Token extracted from Authorization header")
                return token
            
            # 3. Check cookies
            access_token = websocket.cookies.get("access_token")
            if access_token:
                logger.debug("Token extracted from cookies")
                return access_token
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting token from WebSocket: {e}")
            return None
    
    async def _send_auth_error(self, websocket: WebSocket, message: str, code: int = 4001):
        """Send authentication error message to client"""
        try:
            error_message = {
                "type": "auth_error",
                "message": message,
                "code": code,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await websocket.send_text(json.dumps(error_message))
            await websocket.close(code=code, reason=message)
            
        except Exception as e:
            logger.error(f"Failed to send auth error: {e}")
    
    async def refresh_session_token(
        self,
        session_id: str,
        new_token: str
    ) -> bool:
        """
        Refresh token for existing session
        
        Args:
            session_id: Session identifier
            new_token: New JWT token
            
        Returns:
            True if refresh successful, False otherwise
        """
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                logger.warning(f"Session not found for token refresh: {session_id}")
                return False
            
            # Validate new token
            try:
                payload = JWTManager.verify_token(new_token, raise_on_error=False)
                if not payload:
                    logger.warning("Invalid token for refresh")
                    return False
            except AuthenticationError:
                logger.warning("Token validation failed during refresh")
                return False
            
            # Verify user ID matches
            new_user_id = payload.get("sub")
            if new_user_id != session.user.id:
                logger.warning(f"User ID mismatch during token refresh: {session.user.id} vs {new_user_id}")
                await session.close_with_auth_error("Token user mismatch", 4001)
                return False
            
            # Update session with new token
            session.token_payload = payload
            session.update_activity()
            
            # Send refresh confirmation
            await session.send_auth_message("token_refreshed", {
                "success": True,
                "expires_at": payload.get("exp")
            })
            
            logger.info(f"Token refreshed for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[WebSocketAuthSession]:
        """Get session by ID"""
        return self.active_sessions.get(session_id)
    
    def get_user_sessions(self, user_id: str) -> list[WebSocketAuthSession]:
        """Get all sessions for a user"""
        return [
            session for session in self.active_sessions.values()
            if session.user.id == user_id and session.is_active
        ]
    
    async def close_session(self, session_id: str, reason: str = "Session closed"):
        """Close and cleanup session"""
        session = self.active_sessions.get(session_id)
        if session:
            await session.close_with_auth_error(reason)
            del self.active_sessions[session_id]
            logger.info(f"Session {session_id} closed: {reason}")
    
    async def cleanup_stale_sessions(self, max_idle_minutes: int = 30):
        """Clean up stale sessions"""
        current_time = datetime.now(timezone.utc)
        stale_sessions = []
        
        for session_id, session in self.active_sessions.items():
            idle_time = current_time - session.last_activity
            if idle_time.total_seconds() > (max_idle_minutes * 60):
                stale_sessions.append(session_id)
        
        for session_id in stale_sessions:
            await self.close_session(session_id, "Session timeout")
        
        if stale_sessions:
            logger.info(f"Cleaned up {len(stale_sessions)} stale WebSocket sessions")
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        active_count = sum(1 for s in self.active_sessions.values() if s.is_active)
        
        role_counts = {}
        for session in self.active_sessions.values():
            if session.is_active:
                role = session.user.role
                role_counts[role] = role_counts.get(role, 0) + 1
        
        return {
            "total_sessions": len(self.active_sessions),
            "active_sessions": active_count,
            "role_distribution": role_counts,
            "auth_method": "JWT",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global authenticator instance
websocket_authenticator = FastAPIWebSocketAuthenticator()


# Dependency functions for FastAPI WebSocket endpoints
async def verify_websocket_token(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT authentication token")
) -> Optional[User]:
    """
    FastAPI dependency for WebSocket authentication
    
    Usage:
        @app.websocket("/ws")
        async def websocket_endpoint(
            websocket: WebSocket,
            user: User = Depends(verify_websocket_token)
        ):
            # user will be None if authentication fails
            if not user:
                return  # Connection already closed by dependency
    """
    try:
        session = await websocket_authenticator.authenticate_connection(websocket, token)
        if session:
            return session.user
        return None
        
    except Exception as e:
        logger.error(f"WebSocket authentication dependency error: {e}")
        return None


async def get_websocket_session(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
) -> Optional[WebSocketAuthSession]:
    """
    FastAPI dependency that returns the full WebSocket session
    
    Usage:
        @app.websocket("/ws")
        async def websocket_endpoint(
            websocket: WebSocket,
            session: WebSocketAuthSession = Depends(get_websocket_session)
        ):
            # session will be None if authentication fails
    """
    try:
        return await websocket_authenticator.authenticate_connection(websocket, token)
        
    except Exception as e:
        logger.error(f"WebSocket session dependency error: {e}")
        return None


# Utility functions for WebSocket authentication
async def authenticate_websocket_message(
    session: WebSocketAuthSession,
    message: Dict[str, Any]
) -> bool:
    """
    Authenticate individual WebSocket message
    
    Args:
        session: Authenticated WebSocket session
        message: Message to authenticate
        
    Returns:
        True if message is authenticated, False otherwise
    """
    try:
        # Update session activity
        session.update_activity()
        
        # Enforce token expiry on each message
        try:
            exp = session.token_payload.get("exp") if session and session.token_payload else None
            if exp is not None:
                # exp typically seconds since epoch (UTC)
                now_ts = datetime.now(timezone.utc).timestamp()
                if now_ts >= float(exp):
                    # Mark inactive and deny
                    session.is_active = False
                    logger.warning(f"WebSocket token expired for user {session.user.id}")
                    return False
        except Exception as _:
            # If payload malformed, deny for safety
            logger.warning("WebSocket token payload missing/invalid 'exp'")
            return False
        
        # Handle token refresh messages
        if message.get("type") == "refresh_token":
            new_token = message.get("token")
            if new_token:
                return await websocket_authenticator.refresh_session_token(
                    session.session_id, new_token
                )
        
        # All other messages are authenticated if session is valid
        return session.is_active
        
    except Exception as e:
        logger.error(f"Message authentication error: {e}")
        return False


def require_websocket_role(required_role: str):
    """
    Create a role requirement checker for WebSocket sessions
    
    Args:
        required_role: Required role (admin, teacher, student)
        
    Returns:
        Function that checks if session user has required role
    """
    def check_role(session: WebSocketAuthSession) -> bool:
        if not session or not session.is_active:
            return False
        
        # Permission hierarchy
        role_hierarchy = {
            "admin": ["admin", "teacher", "student"],
            "teacher": ["teacher", "student"],
            "student": ["student"]
        }
        
        user_permissions = role_hierarchy.get(session.user.role, [])
        return required_role in user_permissions
    
    return check_role


# Export public interface
__all__ = [
    'WebSocketAuthSession',
    'FastAPIWebSocketAuthenticator',
    'websocket_authenticator',
    'verify_websocket_token',
    'get_websocket_session',
    'authenticate_websocket_message',
    'require_websocket_role',
]