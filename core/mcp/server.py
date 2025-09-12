"""
MCP Server - Model Context Protocol WebSocket Server

Manages real-time context synchronization between agents and services.
"""

import asyncio
import websockets
import json
import logging
import jwt
from typing import Dict, Set, Optional, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
import hashlib
from urllib.parse import parse_qs
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import authentication middleware
from .auth_middleware import WebSocketAuthMiddleware, WebSocketAuthError, extract_token_from_request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ContextEntry:
    """Represents a single context entry"""

    timestamp: str
    content: Dict[str, Any]
    tokens: int
    source: str
    priority: int = 1

    def to_dict(self):
        return asdict(self)


@dataclass
class AuthenticatedClient:
    """Represents an authenticated WebSocket client"""
    websocket: Any
    client_id: str
    user_id: Optional[str]
    token_payload: Dict[str, Any]
    authenticated_at: datetime
    last_activity: datetime

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now(timezone.utc)


class MCPServer:
    """
    Model Context Protocol server for managing agent context.

    Features:
    - WebSocket communication for real-time updates
    - JWT authentication for secure connections
    - Token-aware context management (128K limit)
    - Priority-based context pruning
    - Multi-client synchronization
    - Token refresh handling
    """

    DEFAULT_PORT = 9876
    DEFAULT_MAX_TOKENS = 128000
    JWT_SECRET_KEY = os.getenv("MCP_JWT_SECRET_KEY", os.getenv("JWT_SECRET_KEY", None))
    JWT_ALGORITHM = "HS256"

    def __init__(self, port: int = DEFAULT_PORT, max_tokens: int = DEFAULT_MAX_TOKENS, jwt_secret: str = None):
        self.port = port
        self.max_tokens = max_tokens
        self.jwt_secret = jwt_secret or self.JWT_SECRET_KEY or os.urandom(32).hex()
        self.authenticated_clients: Dict[str, AuthenticatedClient] = {}  # client_id -> AuthenticatedClient
        self.context_store: Dict[str, ContextEntry] = {}
        self.connection_timeout = timedelta(hours=24)  # Token refresh needed after 24h
        
        # Load JWT secret from environment or config if available
        try:
            from config.environment import get_environment_config
            settings = get_environment_config()
            self.jwt_secret = settings.JWT_SECRET_KEY
            self.jwt_algorithm = settings.JWT_ALGORITHM
            logger.info("Loaded JWT configuration from server settings")
        except ImportError:
            logger.warning("Could not load server config, using default JWT settings")
            self.jwt_algorithm = self.JWT_ALGORITHM
        
        # Initialize authentication middleware
        self.auth_middleware = WebSocketAuthMiddleware(self.jwt_secret, self.jwt_algorithm)

    async def authenticate_client(self, websocket, path) -> Optional[AuthenticatedClient]:
        """Authenticate client connection using JWT token"""
        try:
            # Extract token using authentication middleware
            token = self.auth_middleware.extract_token_from_request(websocket, path or '')
            if not token:
                logger.warning("No authentication token provided")
                await websocket.close(code=4001, reason="Authentication token required")
                return None
            
            # Validate token using authentication middleware
            user_info = await self.auth_middleware.validate_websocket_token(token)
            if not user_info:
                logger.warning("Invalid authentication token")
                await websocket.close(code=4001, reason="Invalid authentication token")
                return None
            
            # Create authenticated client
            client_id = self._get_client_id(websocket)
            user_id = user_info['user_id']
            
            authenticated_client = AuthenticatedClient(
                websocket=websocket,
                client_id=client_id,
                user_id=user_id,
                token_payload=user_info['full_payload'],
                authenticated_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc)
            )
            
            # Register with auth middleware
            self.auth_middleware.register_connection(client_id, user_info, websocket)
            
            logger.info(f"Client {client_id} authenticated for user {user_id}")
            return authenticated_client
            
        except WebSocketAuthError as e:
            logger.warning(f"Authentication error: {e.message}")
            await websocket.close(code=e.code, reason=e.message)
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            await websocket.close(code=4001, reason="Authentication failed")
            return None

    async def register(self, websocket, path=None):
        """Register a new authenticated client connection"""
        # Authenticate client first
        authenticated_client = await self.authenticate_client(websocket, path or '')
        if not authenticated_client:
            return False
        
        # Store authenticated client
        self.authenticated_clients[authenticated_client.client_id] = authenticated_client
        logger.info(f"Client {authenticated_client.client_id} registered (user: {authenticated_client.user_id})")

        # Send current context to new client
        await self.send_context(websocket)
        
        # Send authentication success message
        await self.send_auth_success(authenticated_client)
        return True

    async def unregister(self, websocket):
        """Unregister a client connection"""
        # Find authenticated client by websocket
        client_to_remove = None
        for client_id, client in self.authenticated_clients.items():
            if client.websocket == websocket:
                client_to_remove = client_id
                break
        
        if client_to_remove:
            # Unregister from auth middleware
            self.auth_middleware.unregister_connection(client_to_remove)
            del self.authenticated_clients[client_to_remove]
            logger.info(f"Authenticated client {client_to_remove} disconnected")
        else:
            logger.warning("Attempted to unregister unknown client")

    def _get_client_id(self, websocket) -> str:
        """Generate unique client ID"""
        # Safely handle remote_address to avoid null pointer (SonarQube: S2259)
        if websocket.remote_address and len(websocket.remote_address) >= 2:
            remote_address = (
                f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
            )
        else:
            # Fallback to a unique identifier if remote_address is not available
            remote_address = f"unknown_{id(websocket)}"
        # Use SHA256 instead of MD5 for better security (SonarQube: S4790)
        return hashlib.sha256(remote_address.encode()).hexdigest()[:8]

    async def handle_message(
        self, websocket, message: str
    ):
        """Process incoming messages from authenticated clients"""
        # Find authenticated client
        authenticated_client = None
        for client in self.authenticated_clients.values():
            if client.websocket == websocket:
                authenticated_client = client
                break
        
        if not authenticated_client:
            await self._send_error(websocket, "Client not authenticated")
            await websocket.close(code=4001, reason="Not authenticated")
            return
        
        # Update activity timestamp
        authenticated_client.update_activity()
        # Update auth middleware activity
        self.auth_middleware.update_connection_activity(authenticated_client.client_id)
        
        try:
            data = json.loads(message)
            message_type = data.get("type")

            # Handle authentication-specific messages
            if message_type == "refresh_token":
                await self._handle_token_refresh(data, authenticated_client)
            elif message_type == "update_context":
                await self._handle_update_context(data, websocket, authenticated_client)
            elif message_type == "get_context":
                await self.send_context(websocket)
            elif message_type == "clear_context":
                await self._handle_clear_context(data, authenticated_client)
            elif message_type == "query_context":
                await self._handle_query_context(data, websocket)
            elif message_type == "set_priority":
                await self._handle_set_priority(data)
            else:
                await self._send_error(
                    websocket, f"Unknown message type: {message_type}"
                )

        except json.JSONDecodeError as e:
            await self._send_error(websocket, f"Invalid JSON: {e}")
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error(f"Error handling message: {e}")
            await self._send_error(websocket, str(e))

    async def _handle_update_context(
        self, data: Dict, websocket, authenticated_client: AuthenticatedClient
    ):
        """Handle context update request from authenticated client"""
        context = data.get("context", {})
        source = data.get("source", f"{authenticated_client.user_id}_{authenticated_client.client_id}")
        priority = data.get("priority", 1)

        # Calculate token count (simplified - in production use tiktoken)
        tokens = len(json.dumps(context))

        # Create context entry
        entry = ContextEntry(
            timestamp=datetime.now().isoformat(),
            content=context,
            tokens=tokens,
            source=source,
            priority=priority,
        )

        # Store with unique key
        context_key = f"{source}_{datetime.now().timestamp()}"
        self.context_store[context_key] = entry

        # Prune if necessary
        self._prune_context()

        # Broadcast update to all authenticated clients
        await self.broadcast_context()
        
        logger.info(f"Context updated by user {authenticated_client.user_id} (client {authenticated_client.client_id})")

    async def _handle_clear_context(self, data: Dict, authenticated_client: AuthenticatedClient):
        """Handle context clear request from authenticated client"""
        source = data.get("source")
        user_id = authenticated_client.user_id

        if source:
            # Clear context from specific source, but only if user owns it or has permission
            keys_to_remove = []
            for k, v in self.context_store.items():
                if v.source == source:
                    # Check if user owns this context or has permission
                    if self._user_can_modify_context(user_id, v.source):
                        keys_to_remove.append(k)
            
            for key in keys_to_remove:
                del self.context_store[key]
                
            logger.info(f"User {user_id} cleared {len(keys_to_remove)} context entries for source {source}")
        else:
            # Clear user's own context only
            user_prefix = f"{user_id}_"
            keys_to_remove = [
                k for k, v in self.context_store.items() 
                if v.source.startswith(user_prefix)
            ]
            for key in keys_to_remove:
                del self.context_store[key]
                
            logger.info(f"User {user_id} cleared {len(keys_to_remove)} of their own context entries")

        await self.broadcast_context()

    async def _handle_query_context(
        self, data: Dict, websocket
    ):
        """Handle context query request"""
        query = data.get("query", {})
        source_filter = query.get("source")
        priority_filter = query.get("min_priority", 0)

        filtered_context = {}
        for key, entry in self.context_store.items():
            if source_filter and entry.source != source_filter:
                continue
            if entry.priority < priority_filter:
                continue
            filtered_context[key] = entry.to_dict()

        await websocket.send(
            json.dumps({"type": "query_response", "data": filtered_context})
        )

    async def _handle_set_priority(self, data: Dict):
        """Handle priority update for existing context"""
        context_key = data.get("key")
        new_priority = data.get("priority", 1)

        if context_key in self.context_store:
            self.context_store[context_key].priority = new_priority
            self._prune_context()
            await self.broadcast_context()

    def _prune_context(self):
        """
        Remove old context to stay within token limit.
        Prioritizes keeping high-priority and recent context.
        """
        total_tokens = sum(entry.tokens for entry in self.context_store.values())

        if total_tokens <= self.max_tokens:
            return

        # Sort by priority (descending) and timestamp (descending)
        sorted_entries = sorted(
            self.context_store.items(),
            key=lambda x: (
                -x[1].priority,
                -float(datetime.fromisoformat(x[1].timestamp).timestamp()),
            ),
        )

        # Keep entries until we exceed token limit
        kept_entries = {}
        current_tokens = 0

        for key, entry in sorted_entries:
            if current_tokens + entry.tokens <= self.max_tokens:
                kept_entries[key] = entry
                current_tokens += entry.tokens
            else:
                break

        self.context_store = kept_entries
        logger.info(f"Pruned context to {current_tokens} tokens")

    async def send_context(self, websocket):
        """Send current context to a specific client"""
        context_data = {
            key: entry.to_dict() for key, entry in self.context_store.items()
        }

        await websocket.send(
            json.dumps(
                {
                    "type": "context",
                    "data": context_data,
                    "metadata": {
                        "total_tokens": sum(
                            e.tokens for e in self.context_store.values()
                        ),
                        "max_tokens": self.max_tokens,
                        "entry_count": len(self.context_store),
                    },
                }
            )
        )

    async def broadcast_context(self):
        """Broadcast current context to all authenticated clients"""
        if not self.authenticated_clients:
            return

        # Prepare message once
        context_data = {
            key: entry.to_dict() for key, entry in self.context_store.items()
        }
        message = json.dumps(
            {
                "type": "context_update",
                "data": context_data,
                "metadata": {
                    "total_tokens": sum(e.tokens for e in self.context_store.values()),
                    "max_tokens": self.max_tokens,
                    "entry_count": len(self.context_store),
                },
            }
        )

        # Send to all authenticated clients concurrently
        disconnected_clients = []
        for client_id, authenticated_client in self.authenticated_clients.items():
            try:
                await authenticated_client.websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(authenticated_client.websocket)

        # Clean up disconnected clients
        for client in disconnected_clients:
            await self.unregister(client)

    async def _send_error(
        self, websocket, error_message: str
    ):
        """Send error message to client"""
        await websocket.send(json.dumps({"type": "error", "message": error_message}))

    async def handler(self, websocket, path=None):
        """WebSocket connection handler with authentication - compatible with both old and new websockets versions"""
        # Attempt to register (authenticate) the client
        if not await self.register(websocket, path):
            # Registration failed, connection is already closed
            return
            
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

    async def start(self):
        """Start the MCP server"""
        logger.info(f"Starting MCP server on port {self.port}")
        logger.info(f"Max context tokens: {self.max_tokens}")

        async with websockets.serve(self.handler, "localhost", self.port):
            logger.info(f"MCP server listening on ws://localhost:{self.port}")
            await asyncio.Future()  # Run forever

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            # Check token expiration
            if 'exp' in payload:
                if datetime.now(timezone.utc).timestamp() > payload['exp']:
                    logger.warning("Token has expired")
                    return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def _user_can_modify_context(self, user_id: str, context_source: str) -> bool:
        """Check if user can modify context from given source"""
        # Users can modify their own context
        if context_source.startswith(f"{user_id}_"):
            return True
        
        # TODO: Add role-based permissions (teachers can modify student context, etc.)
        # For now, only allow users to modify their own context
        return False

    async def send_auth_success(self, authenticated_client: AuthenticatedClient):
        """Send authentication success message to client"""
        message = {
            "type": "auth_success",
            "client_id": authenticated_client.client_id,
            "user_id": authenticated_client.user_id,
            "authenticated_at": authenticated_client.authenticated_at.isoformat(),
            "server_info": {
                "version": "1.0.0",
                "max_tokens": self.max_tokens,
                "features": ["jwt_auth", "token_refresh", "context_management"]
            }
        }
        await authenticated_client.websocket.send(json.dumps(message))

    async def _handle_token_refresh(self, data: Dict, authenticated_client: AuthenticatedClient):
        """Handle token refresh request"""
        new_token = data.get("token")
        if not new_token:
            await self._send_error(authenticated_client.websocket, "New token required for refresh")
            return

        # Use auth middleware to validate token refresh
        success = await self.auth_middleware.validate_token_refresh(authenticated_client.client_id, new_token)
        if not success:
            await self._send_error(authenticated_client.websocket, "Invalid refresh token")
            await authenticated_client.websocket.close(code=4001, reason="Invalid refresh token")
            return

        # Update client with new token info from middleware
        connection_info = self.auth_middleware.get_connection_info(authenticated_client.client_id)
        if connection_info:
            authenticated_client.token_payload = connection_info['user_info']['full_payload']
            authenticated_client.update_activity()
        
        # Send refresh success
        await authenticated_client.websocket.send(json.dumps({
            "type": "token_refreshed",
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
        
        logger.info(f"Token refreshed for user {authenticated_client.user_id} (client {authenticated_client.client_id})")

    async def cleanup_stale_connections(self):
        """Clean up stale authenticated connections"""
        current_time = datetime.now(timezone.utc)
        stale_clients = []
        
        for client_id, client in self.authenticated_clients.items():
            # Check if connection is too old
            time_since_activity = current_time - client.last_activity
            if time_since_activity > self.connection_timeout:
                stale_clients.append(client_id)
        
        for client_id in stale_clients:
            client = self.authenticated_clients[client_id]
            logger.info(f"Closing stale connection for client {client_id}")
            try:
                await client.websocket.close(code=4002, reason="Connection timeout")
            except Exception as e:
                logger.error(f"Error closing stale connection: {e}")
            finally:
                await self.unregister(client.websocket)

    def get_status(self) -> Dict:
        """Get current server status"""
        auth_stats = self.auth_middleware.get_connection_stats()
        
        return {
            "connected_clients": len(self.authenticated_clients),
            "context_entries": len(self.context_store),
            "total_tokens": sum(e.tokens for e in self.context_store.values()),
            "max_tokens": self.max_tokens,
            "authenticated_clients": [
                {
                    "client_id": client.client_id,
                    "user_id": client.user_id,
                    "authenticated_at": client.authenticated_at.isoformat(),
                    "last_activity": client.last_activity.isoformat()
                }
                for client in self.authenticated_clients.values()
            ],
            "authentication": auth_stats,
            "server_info": {
                "version": "1.0.0",
                "features": ["jwt_auth", "token_refresh", "context_management", "secure_connections"]
            }
        }


async def main():
    """Main entry point for running the MCP server"""
    server = MCPServer(
        port=MCPServer.DEFAULT_PORT, max_tokens=MCPServer.DEFAULT_MAX_TOKENS
    )
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
