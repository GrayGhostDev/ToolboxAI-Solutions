"""
WebSocket Authentication Service

Provides authentication and authorization for WebSocket connections.
"""

import jwt
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status

from ..core.config import settings
from ..api.auth.auth import get_current_user, verify_token

logger = logging.getLogger(__name__)


class UserInfo:
    """User information for WebSocket sessions."""
    def __init__(self, user_id: str, username: str, role: str):
        self.id = user_id
        self.username = username
        self.role = role


@dataclass
class WebSocketAuthSession:
    """WebSocket authentication session information."""
    user_id: str
    username: str
    role: str
    connected_at: datetime
    websocket: Optional[WebSocket] = None
    metadata: Optional[Dict[str, Any]] = None
    session_id: str = field(default_factory=lambda: f"ws_{int(datetime.now().timestamp() * 1000)}")
    token_payload: Optional[Dict[str, Any]] = None
    
    @property
    def user(self):
        """Get user info object for compatibility."""
        return UserInfo(self.user_id, self.username, self.role)


class WebSocketAuthManager:
    """Manages WebSocket authentication and session management."""
    
    def __init__(self):
        self.authenticated_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def authenticate_connection(self, websocket: WebSocket) -> Optional[WebSocketAuthSession]:
        """
        Authenticate a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to authenticate
            
        Returns:
            WebSocketAuthSession if authenticated, None otherwise
        """
        # For testing or unauthenticated endpoints, return a default session
        if settings.env_name == "testing" or settings.SKIP_AUTH:
            return WebSocketAuthSession(
                user_id="test_user",
                username="Test User",
                role="admin",
                connected_at=datetime.now(),
                websocket=websocket
            )
        
        # Try to get token from query params or headers
        try:
            # Check query params first
            token = websocket.query_params.get("token")
            if token:
                user_info = await self.authenticate_websocket(websocket, token)
                if user_info:
                    return WebSocketAuthSession(
                        user_id=user_info["user_id"],
                        username=user_info["username"],
                        role=user_info["role"],
                        connected_at=user_info["connected_at"],
                        websocket=websocket
                    )
        except Exception as e:
            logger.error(f"Error during WebSocket authentication: {str(e)}")
        
        return None
    
    async def authenticate_websocket(self, websocket: WebSocket, token: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a WebSocket connection using JWT token.
        
        Args:
            websocket: The WebSocket connection
            token: JWT token for authentication
            
        Returns:
            User information if authenticated, None otherwise
        """
        try:
            # Verify the token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # Store the authenticated connection
            self.authenticated_connections[user_id] = websocket
            self.user_sessions[user_id] = {
                "user_id": user_id,
                "username": payload.get("username"),
                "role": payload.get("role", "student"),
                "connected_at": datetime.now(),
                "websocket": websocket,
                "session_id": f"ws_{int(datetime.now().timestamp() * 1000)}"
            }
            
            logger.info(f"WebSocket authenticated for user: {user_id}")
            return self.user_sessions[user_id]
            
        except jwt.ExpiredSignatureError:
            logger.warning("WebSocket authentication failed: Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"WebSocket authentication failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"WebSocket authentication error: {str(e)}")
            return None
    
    async def disconnect_user(self, user_id: str):
        """
        Disconnect a user's WebSocket connection.
        
        Args:
            user_id: The user ID to disconnect
        """
        if user_id in self.authenticated_connections:
            websocket = self.authenticated_connections[user_id]
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket for user {user_id}: {str(e)}")
            
            del self.authenticated_connections[user_id]
            del self.user_sessions[user_id]
            logger.info(f"WebSocket disconnected for user: {user_id}")
    
    async def close_session(self, session_id: str, reason: str = "Session closed"):
        """
        Close a WebSocket session.
        
        Args:
            session_id: The session ID to close
            reason: Reason for closing
        """
        # Find user by session ID
        for user_id, session in self.user_sessions.items():
            if isinstance(session, dict) and session.get('session_id') == session_id:
                await self.disconnect_user(user_id)
                logger.info(f"Closed session {session_id}: {reason}")
                return
            elif hasattr(session, 'session_id') and getattr(session, 'session_id') == session_id:
                await self.disconnect_user(user_id)
                logger.info(f"Closed session {session_id}: {reason}")
                return
        
        logger.warning(f"Session {session_id} not found for closing")
    
    def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user session information.
        
        Args:
            user_id: The user ID
            
        Returns:
            User session information if exists
        """
        return self.user_sessions.get(user_id)
    
    def is_authenticated(self, user_id: str) -> bool:
        """
        Check if a user is authenticated.
        
        Args:
            user_id: The user ID to check
            
        Returns:
            True if authenticated, False otherwise
        """
        return user_id in self.authenticated_connections
    
    async def broadcast_to_role(self, role: str, message: Dict[str, Any]):
        """
        Broadcast a message to all users with a specific role.
        
        Args:
            role: The role to broadcast to
            message: The message to send
        """
        for user_id, session in self.user_sessions.items():
            if session.get("role") == role:
                websocket = session.get("websocket")
                if websocket:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """
        Send a message to a specific user.
        
        Args:
            user_id: The user ID to send to
            message: The message to send
        """
        if user_id in self.authenticated_connections:
            websocket = self.authenticated_connections[user_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {str(e)}")
                await self.disconnect_user(user_id)


# Create a singleton instance
websocket_auth_manager = WebSocketAuthManager()
# Alias for backward compatibility
websocket_authenticator = websocket_auth_manager


async def require_websocket_auth(websocket: WebSocket, token: str) -> Dict[str, Any]:
    """
    Require WebSocket authentication.
    
    Args:
        websocket: The WebSocket connection
        token: JWT token for authentication
        
    Returns:
        User information if authenticated
        
    Raises:
        WebSocketDisconnect if authentication fails
    """
    user_info = await websocket_auth_manager.authenticate_websocket(websocket, token)
    if not user_info:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)
    
    return user_info


async def get_websocket_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get WebSocket user information.
    
    Args:
        user_id: The user ID
        
    Returns:
        User information if exists
    """
    return websocket_auth_manager.get_user_session(user_id)


def verify_websocket_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a WebSocket authentication token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("WebSocket token verification failed: Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"WebSocket token verification failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"WebSocket token verification error: {str(e)}")
        return None


def get_websocket_session(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get WebSocket session information (synchronous version).
    
    Args:
        user_id: The user ID
        
    Returns:
        User session information if exists
    """
    return websocket_auth_manager.get_user_session(user_id)


async def authenticate_websocket_message(websocket: WebSocket, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Authenticate a WebSocket message.
    
    Args:
        websocket: The WebSocket connection
        message: The message containing authentication data
        
    Returns:
        User information if authenticated, None otherwise
    """
    token = message.get("token") or message.get("auth", {}).get("token")
    if not token:
        logger.warning("WebSocket message authentication failed: No token provided")
        return None
    
    return await websocket_auth_manager.authenticate_websocket(websocket, token)