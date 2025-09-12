"""
WebSocket Authentication Middleware for MCP Server

Provides JWT token validation, extraction, and connection state management
for WebSocket connections in the Model Context Protocol server.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import jwt

logger = logging.getLogger(__name__)


class WebSocketAuthError(Exception):
    """WebSocket authentication error"""
    def __init__(self, message: str, code: int = 4001):
        super().__init__(message)
        self.message = message
        self.code = code


class WebSocketAuthMiddleware:
    """
    Authentication middleware for WebSocket connections
    
    Features:
    - JWT token validation using existing auth system
    - Token extraction from multiple sources (query, headers, cookies)
    - Connection state management
    - Token refresh handling
    - Security validation
    """
    
    def __init__(self, jwt_secret: str, jwt_algorithm: str = "HS256"):
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        
    def extract_token_from_request(self, websocket, path: str) -> Optional[str]:
        """
        Extract JWT token from WebSocket request
        
        Token sources (in order of precedence):
        1. Query parameter: ?token=<jwt>
        2. Authorization header: Authorization: Bearer <jwt>
        3. Cookie: access_token=<jwt>
        
        Args:
            websocket: WebSocket connection object
            path: WebSocket path including query parameters
            
        Returns:
            JWT token string if found, None otherwise
        """
        token = None
        
        try:
            # 1. Extract from query parameters
            if '?' in path:
                query_string = path.split('?', 1)[1]
                query_params = parse_qs(query_string)
                if 'token' in query_params:
                    token = query_params['token'][0]
                    logger.debug("Token extracted from query parameters")
                    return token
            
            # 2. Extract from Authorization header
            if hasattr(websocket, 'request_headers'):
                auth_header = websocket.request_headers.get('authorization', '')
                if not auth_header:
                    # Try lowercase header name
                    auth_header = websocket.request_headers.get('Authorization', '')
                
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header[7:]  # Remove 'Bearer ' prefix
                    logger.debug("Token extracted from Authorization header")
                    return token
            
            # 3. Extract from cookies (if available)
            if hasattr(websocket, 'cookies'):
                cookie_token = websocket.cookies.get('access_token')
                if cookie_token:
                    token = cookie_token
                    logger.debug("Token extracted from cookies")
                    return token
            
            # 4. Try to extract from raw headers if websocket object supports it
            if hasattr(websocket, 'raw_request_headers'):
                for header_name, header_value in websocket.raw_request_headers:
                    if header_name.lower() == b'authorization':
                        auth_value = header_value.decode('utf-8')
                        if auth_value.startswith('Bearer '):
                            token = auth_value[7:]
                            logger.debug("Token extracted from raw headers")
                            return token
            
        except Exception as e:
            logger.error(f"Error extracting token from request: {e}")
        
        return token
    
    async def validate_websocket_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token and return user information
        
        Args:
            token: JWT token to validate
            
        Returns:
            User info dictionary if valid, None if invalid
            
        Raises:
            WebSocketAuthError: If token validation fails with specific error
        """
        if not token:
            raise WebSocketAuthError("Authentication token required", 4001)
        
        # Validate token format (basic check)
        if not self._is_valid_jwt_format(token):
            raise WebSocketAuthError("Invalid token format", 4001)
        
        try:
            # Decode and verify JWT token
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm]
            )
            
            # Check token expiration
            if 'exp' in payload:
                exp_timestamp = payload['exp']
                current_timestamp = datetime.now(timezone.utc).timestamp()
                
                if current_timestamp > exp_timestamp:
                    raise WebSocketAuthError("Token has expired", 4001)
            
            # Extract user information
            user_id = payload.get('sub') or payload.get('user_id')
            if not user_id:
                raise WebSocketAuthError("Invalid token payload: missing user ID", 4001)
            
            user_info = {
                'user_id': user_id,
                'username': payload.get('username', 'unknown'),
                'email': payload.get('email', 'unknown@example.com'),
                'role': payload.get('role', 'student'),
                'token_issued_at': payload.get('iat'),
                'token_expires_at': payload.get('exp'),
                'full_payload': payload
            }
            
            logger.info(f"Token validation successful for user {user_id}")
            return user_info
            
        except jwt.ExpiredSignatureError:
            raise WebSocketAuthError("Token has expired", 4001)
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise WebSocketAuthError("Invalid authentication token", 4001)
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise WebSocketAuthError("Token validation failed", 4001)
    
    def _is_valid_jwt_format(self, token: str) -> bool:
        """
        Check if token has valid JWT format (three base64 parts separated by dots)
        
        Args:
            token: Token to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        try:
            # JWT should have exactly 3 parts separated by dots
            parts = token.split('.')
            if len(parts) != 3:
                return False
            
            # Each part should be valid base64
            import base64
            for part in parts:
                # Add padding if needed
                padded = part + '=' * (4 - len(part) % 4)
                try:
                    base64.urlsafe_b64decode(padded)
                except Exception:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def register_connection(self, client_id: str, user_info: Dict[str, Any], websocket) -> None:
        """
        Register authenticated connection
        
        Args:
            client_id: Unique client identifier
            user_info: User information from token validation
            websocket: WebSocket connection object
        """
        connection_info = {
            'user_info': user_info,
            'websocket': websocket,
            'connected_at': datetime.now(timezone.utc),
            'last_activity': datetime.now(timezone.utc),
            'message_count': 0,
            'is_active': True
        }
        
        self.active_connections[client_id] = connection_info
        logger.info(f"Registered authenticated connection for user {user_info['user_id']} (client {client_id})")
    
    def unregister_connection(self, client_id: str) -> bool:
        """
        Unregister connection
        
        Args:
            client_id: Client identifier to unregister
            
        Returns:
            True if connection was found and removed, False otherwise
        """
        if client_id in self.active_connections:
            user_id = self.active_connections[client_id]['user_info']['user_id']
            del self.active_connections[client_id]
            logger.info(f"Unregistered connection for user {user_id} (client {client_id})")
            return True
        return False
    
    def update_connection_activity(self, client_id: str) -> None:
        """
        Update last activity timestamp for connection
        
        Args:
            client_id: Client identifier
        """
        if client_id in self.active_connections:
            self.active_connections[client_id]['last_activity'] = datetime.now(timezone.utc)
            self.active_connections[client_id]['message_count'] += 1
    
    def get_connection_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get connection information
        
        Args:
            client_id: Client identifier
            
        Returns:
            Connection info if found, None otherwise
        """
        return self.active_connections.get(client_id)
    
    def is_connection_valid(self, client_id: str) -> bool:
        """
        Check if connection is still valid and active
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if connection is valid, False otherwise
        """
        connection = self.active_connections.get(client_id)
        if not connection:
            return False
        
        return connection.get('is_active', False)
    
    async def validate_token_refresh(self, client_id: str, new_token: str) -> bool:
        """
        Validate token refresh request
        
        Args:
            client_id: Client identifier
            new_token: New JWT token
            
        Returns:
            True if refresh is valid, False otherwise
        """
        try:
            # Validate new token
            new_user_info = await self.validate_websocket_token(new_token)
            if not new_user_info:
                return False
            
            # Check if connection exists
            connection = self.active_connections.get(client_id)
            if not connection:
                return False
            
            # Verify user ID matches
            current_user_id = connection['user_info']['user_id']
            new_user_id = new_user_info['user_id']
            
            if current_user_id != new_user_id:
                logger.warning(f"Token refresh user mismatch: {current_user_id} vs {new_user_id}")
                return False
            
            # Update connection with new token info
            connection['user_info'] = new_user_info
            connection['last_activity'] = datetime.now(timezone.utc)
            
            logger.info(f"Token refresh successful for user {new_user_id} (client {client_id})")
            return True
            
        except WebSocketAuthError as e:
            logger.warning(f"Token refresh validation failed: {e.message}")
            return False
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get authentication statistics
        
        Returns:
            Dictionary with connection and authentication stats
        """
        total_connections = len(self.active_connections)
        active_connections = sum(
            1 for conn in self.active_connections.values() 
            if conn.get('is_active', False)
        )
        
        user_roles = {}
        for conn in self.active_connections.values():
            role = conn['user_info'].get('role', 'unknown')
            user_roles[role] = user_roles.get(role, 0) + 1
        
        return {
            'total_connections': total_connections,
            'active_connections': active_connections,
            'user_roles': user_roles,
            'auth_system': 'JWT',
            'algorithm': self.jwt_algorithm
        }
    
    def check_user_permission(self, client_id: str, required_permission: str) -> bool:
        """
        Check if user has required permission
        
        Args:
            client_id: Client identifier
            required_permission: Required permission level
            
        Returns:
            True if user has permission, False otherwise
        """
        connection = self.active_connections.get(client_id)
        if not connection:
            return False
        
        user_role = connection['user_info'].get('role', 'student')
        
        # Define permission hierarchy
        permission_hierarchy = {
            "admin": ["admin", "teacher", "student"],
            "teacher": ["teacher", "student"],
            "student": ["student"]
        }
        
        user_permissions = permission_hierarchy.get(user_role, [])
        return required_permission in user_permissions


# Standalone utility functions for backward compatibility
async def validate_websocket_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Standalone function to validate WebSocket token
    Uses default JWT settings from server config
    """
    try:
        # Try to import server config
        from config.environment import get_environment_config
        settings = get_environment_config()
        jwt_secret = settings.JWT_SECRET_KEY
        jwt_algorithm = settings.JWT_ALGORITHM
    except ImportError:
        # Fallback to default settings
        jwt_secret = "your-mcp-secret-key-change-in-production"
        jwt_algorithm = "HS256"
    
    middleware = WebSocketAuthMiddleware(jwt_secret, jwt_algorithm)
    return await middleware.validate_websocket_token(token)


def extract_token_from_request(websocket, path: str) -> Optional[str]:
    """
    Standalone function to extract token from WebSocket request
    """
    try:
        from config.environment import get_environment_config
        settings = get_environment_config()
        jwt_secret = settings.JWT_SECRET_KEY
        jwt_algorithm = settings.JWT_ALGORITHM
    except ImportError:
        jwt_secret = "your-mcp-secret-key-change-in-production"
        jwt_algorithm = "HS256"
    
    middleware = WebSocketAuthMiddleware(jwt_secret, jwt_algorithm)
    return middleware.extract_token_from_request(websocket, path)


# Export public interface
__all__ = [
    'WebSocketAuthMiddleware',
    'WebSocketAuthError',
    'validate_websocket_token',
    'extract_token_from_request',
]