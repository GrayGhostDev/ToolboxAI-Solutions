"""
WebSocket Connection Management for ToolboxAI Roblox Environment

Provides real-time communication capabilities including:
- WebSocket connection management
- Real-time event broadcasting
- Client subscription management
- Message routing and handling
- Connection pooling and monitoring
"""

import asyncio
import json
import logging
import uuid
import weakref
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Set

import redis
from fastapi import WebSocket, WebSocketDisconnect, status
from fastapi.websockets import WebSocketState
from pydantic import BaseModel, ValidationError

from .auth import get_current_session
from .config import settings
from .models import Session, User, WebSocketMessage, WebSocketResponse

logger = logging.getLogger(__name__)

# Redis client for WebSocket coordination across instances
try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connection established for WebSocket coordination")
except Exception as e:
    logger.warning(
        f"Redis connection failed: {e}. Using single-instance WebSocket management."
    )
    redis_client = None


class WebSocketConnection:
    """Represents a WebSocket connection with metadata"""

    # Class-level attribute annotations to help the static analyzer
    connected_at: datetime
    last_ping: datetime
    subscriptions: Set[str]
    metadata: Dict[str, Any]
    message_count: int
    is_active: bool

    def __init__(
        self, websocket: WebSocket, client_id: str, user_id: Optional[str] = None
    ):
        self.websocket = websocket
        self.client_id = client_id
        self.user_id = user_id

        # Initialize commonly accessed attributes
        self.connected_at = datetime.now(timezone.utc)
        self.last_ping = datetime.now(timezone.utc)
        self.subscriptions = set()
        self.metadata = {}
        self.message_count = 0
        self.is_active = True

    async def send(self, message: Dict[str, Any]) -> bool:
        """Send message to client"""
        if (
            not self.is_active
            or self.websocket.client_state != WebSocketState.CONNECTED
        ):
            return False

        try:
            await self.websocket.send_text(json.dumps(message))
            self.message_count += 1
            return True
        except Exception as e:
            logger.error(f"Failed to send message to client {self.client_id}: {e}")
            self.is_active = False
            return False

    async def close(
        self,
        code: int = status.WS_1000_NORMAL_CLOSURE,
        reason: str = "Connection closed",
    ):
        """Close the WebSocket connection"""
        if self.websocket.client_state == WebSocketState.CONNECTED:
            try:
                await self.websocket.close(code=code, reason=reason)
            except Exception as e:
                logger.error(
                    f"Error closing WebSocket for client {self.client_id}: {e}"
                )

        self.is_active = False

    def ping(self):
        """Update last ping timestamp"""
        self.last_ping = datetime.now(timezone.utc)

    def is_stale(self, threshold_minutes: int = 5) -> bool:
        """Check if connection is stale"""
        return (datetime.now(timezone.utc) - self.last_ping) > timedelta(
            minutes=threshold_minutes
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "client_id": self.client_id,
            "user_id": self.user_id,
            "connected_at": self.connected_at.isoformat(),
            "last_ping": self.last_ping.isoformat(),
            "subscriptions": list(self.subscriptions),
            "metadata": self.metadata,
            "message_count": self.message_count,
            "is_active": self.is_active,
        }


class MessageHandler:
    """Handles different types of WebSocket messages"""

    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.handlers: Dict[str, Callable] = {
            "ping": self._handle_ping,
            "subscribe": self._handle_subscribe,
            "unsubscribe": self._handle_unsubscribe,
            "broadcast": self._handle_broadcast,
            "user_message": self._handle_user_message,
            "content_request": self._handle_content_request,
            "quiz_response": self._handle_quiz_response,
            "progress_update": self._handle_progress_update,
            "roblox_event": self._handle_roblox_event,
        }

    async def handle_message(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Route message to appropriate handler"""
        message_type = message.get("type")
        if not isinstance(message_type, str):
            await self._send_error(connection, "Invalid message type")
            return

        handler = self.handlers.get(message_type, self._handle_unknown)

        try:
            await handler(connection, message)
        except Exception as e:
            logger.error(f"Error handling message type '{message_type}': {e}")
            await self._send_error(connection, f"Error processing message: {str(e)}")

    async def _handle_ping(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle ping message"""
        connection.ping()
        await connection.send(
            {
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "client_id": connection.client_id,
            }
        )

    async def _handle_subscribe(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle subscription request"""
        channels = message.get("channels", [])

        for channel in channels:
            connection.subscriptions.add(channel)
            await self.connection_manager.add_to_channel(channel, connection.client_id)

        await connection.send(
            {
                "type": "subscribed",
                "channels": channels,
                "total_subscriptions": len(connection.subscriptions),
            }
        )

        logger.info(f"Client {connection.client_id} subscribed to channels: {channels}")

    async def _handle_unsubscribe(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle unsubscription request"""
        channels = message.get("channels", [])

        for channel in channels:
            connection.subscriptions.discard(channel)
            await self.connection_manager.remove_from_channel(
                channel, connection.client_id
            )

        await connection.send(
            {
                "type": "unsubscribed",
                "channels": channels,
                "total_subscriptions": len(connection.subscriptions),
            }
        )

        logger.info(
            f"Client {connection.client_id} unsubscribed from channels: {channels}"
        )

    async def _handle_broadcast(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle broadcast request"""
        channel = message.get("channel")
        data = message.get("data", {})

        if not channel:
            await self._send_error(connection, "Channel required for broadcast")
            return

        # Add sender information
        broadcast_message = {
            "type": "broadcast",
            "channel": channel,
            "data": data,
            "sender": connection.client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self.connection_manager.broadcast_to_channel(
            channel, broadcast_message, exclude=connection.client_id
        )

        # Confirm broadcast
        await connection.send(
            {
                "type": "broadcast_sent",
                "channel": channel,
                "recipients": await self.connection_manager.get_channel_size(channel)
                - 1,
            }
        )

    async def _handle_user_message(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle user-to-user message"""
        target_user = message.get("target_user")
        data = message.get("data", {})

        if not target_user:
            await self._send_error(connection, "Target user required")
            return

        user_message = {
            "type": "user_message",
            "from": connection.user_id,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        sent = await self.connection_manager.send_to_user(target_user, user_message)

        await connection.send(
            {"type": "message_sent", "target_user": target_user, "delivered": sent}
        )

    async def _handle_content_request(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle content generation request"""
        request_data = message.get("data", {})

        # Forward to content generation system
        # This would integrate with the agent system
        response_message = {
            "type": "content_response",
            "request_id": message.get("request_id"),
            "status": "processing",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await connection.send(response_message)

        # Ensure request_id is a string before scheduling background processing
        request_id = message.get("request_id") or str(uuid.uuid4())
        request_id = str(request_id)

        # Simulate async content generation
        asyncio.create_task(
            self._process_content_request(connection, request_data, request_id)
        )

    async def _handle_quiz_response(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle quiz response from student"""
        quiz_data = message.get("data", {})

        # Process quiz response
        # This would integrate with the educational tracking system

        feedback_message = {
            "type": "quiz_feedback",
            "quiz_id": quiz_data.get("quiz_id"),
            "correct": True,  # This would be calculated
            "score": quiz_data.get("score", 0),
            "feedback": "Great job!",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await connection.send(feedback_message)

    async def _handle_progress_update(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle student progress update"""
        progress_data = message.get("data", {})

        # Broadcast progress to teachers/observers
        progress_message = {
            "type": "student_progress",
            "student_id": connection.user_id,
            "progress": progress_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self.connection_manager.broadcast_to_channel(
            "teacher_updates", progress_message
        )

        # Confirm update received
        await connection.send({"type": "progress_updated", "status": "success"})

    async def _handle_roblox_event(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle events from Roblox environment"""
        event_data = message.get("data", {})
        event_type = event_data.get("event_type")

        # Route Roblox events to appropriate channels
        roblox_message = {
            "type": "roblox_event",
            "event_type": event_type,
            "data": event_data,
            "source": connection.client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Broadcast to relevant channels
        channels = ["roblox_events", f"user_{connection.user_id}"]
        for channel in channels:
            await self.connection_manager.broadcast_to_channel(channel, roblox_message)

    async def _handle_unknown(
        self, connection: WebSocketConnection, message: Dict[str, Any]
    ):
        """Handle unknown message types"""
        await self._send_error(
            connection, f"Unknown message type: {message.get('type')}"
        )

    async def _send_error(self, connection: WebSocketConnection, error_message: str):
        """Send error message to client"""
        await connection.send(
            {
                "type": "error",
                "error": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def _process_content_request(
        self,
        connection: WebSocketConnection,
        request_data: Dict[str, Any],
        request_id: str,
    ):
        """Process content generation request asynchronously"""
        try:
            # Simulate content generation delay
            await asyncio.sleep(2)

            # This would call the actual agent system
            response = {
                "type": "content_response",
                "request_id": request_id,
                "status": "completed",
                "content": {
                    "scripts": ["-- Generated Lua script"],
                    "terrain": "Forest environment created",
                    "quiz": "Math quiz with 5 questions",
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await connection.send(response)

        except Exception as e:
            error_response = {
                "type": "content_response",
                "request_id": request_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await connection.send(error_response)


class WebSocketManager:
    """Manages WebSocket connections and message routing"""

    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(
            set
        )  # user_id -> client_ids
        self.channels: Dict[str, Set[str]] = defaultdict(set)  # channel -> client_ids
        self.message_handler = MessageHandler(self)

        # Connection monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "channels_active": 0,
        }

        logger.info("WebSocketManager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        client_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Accept and manage new WebSocket connection"""
        await websocket.accept()

        # Generate client ID if not provided
        if not client_id:
            client_id = str(uuid.uuid4())

        # Create connection object
        connection = WebSocketConnection(websocket, client_id, user_id)

        # Store connection
        self.connections[client_id] = connection
        if user_id:
            self.user_connections[user_id].add(client_id)

        # Update stats
        self._stats["total_connections"] += 1
        self._stats["active_connections"] = len(self.connections)

        # Send welcome message
        welcome_message = {
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "server_info": {
                "version": "1.0.0",
                "features": ["real_time_updates", "multi_channel", "user_messaging"],
            },
        }

        await connection.send(welcome_message)

        # Start connection monitoring if not already running
        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitor_connections())

        logger.info(f"WebSocket connected: {client_id} (user: {user_id})")
        return client_id

    async def disconnect(
        self,
        client_id: str,
        code: int = status.WS_1000_NORMAL_CLOSURE,
        reason: str = "Connection closed",
    ):
        """Disconnect and cleanup WebSocket connection"""
        connection = self.connections.get(client_id)
        if not connection:
            return

        # Remove from user connections
        if connection.user_id:
            self.user_connections[connection.user_id].discard(client_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]

        # Remove from all channels
        for channel in list(connection.subscriptions):
            await self.remove_from_channel(channel, client_id)

        # Close connection
        await connection.close(code, reason)

        # Remove from connections
        del self.connections[client_id]

        # Update stats
        self._stats["active_connections"] = len(self.connections)

        logger.info(f"WebSocket disconnected: {client_id} (reason: {reason})")

    async def handle_message(self, client_id: str, message_data: str):
        """Handle incoming WebSocket message"""
        connection = self.connections.get(client_id)
        if not connection:
            logger.warning(f"Message received from unknown client: {client_id}")
            return

        try:
            message = json.loads(message_data)
            self._stats["messages_received"] += 1

            # Validate message structure
            if not isinstance(message, dict) or "type" not in message:
                await self.message_handler._send_error(
                    connection, "Invalid message format"
                )
                return

            # Handle the message
            await self.message_handler.handle_message(connection, message)

        except json.JSONDecodeError:
            await self.message_handler._send_error(connection, "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            await self.message_handler._send_error(connection, "Internal server error")

    async def send_to_client(self, client_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific client"""
        connection = self.connections.get(client_id)
        if not connection:
            return False

        success = await connection.send(message)
        if success:
            self._stats["messages_sent"] += 1

        return success

    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """Send message to all connections of a user"""
        client_ids = self.user_connections.get(user_id, set())
        if not client_ids:
            return False

        success_count = 0
        for client_id in list(
            client_ids
        ):  # Use list to avoid modification during iteration
            if await self.send_to_client(client_id, message):
                success_count += 1

        return success_count > 0

    async def broadcast(
        self, message: Dict[str, Any], exclude: Optional[str] = None
    ) -> int:
        """Broadcast message to all connected clients"""
        sent_count = 0

        for client_id in list(self.connections.keys()):
            if client_id != exclude:
                if await self.send_to_client(client_id, message):
                    sent_count += 1

        return sent_count

    async def add_to_channel(self, channel: str, client_id: str):
        """Add client to a channel"""
        if client_id in self.connections:
            self.channels[channel].add(client_id)
            self.connections[client_id].subscriptions.add(channel)
            self._stats["channels_active"] = len(self.channels)

    async def remove_from_channel(self, channel: str, client_id: str):
        """Remove client from a channel"""
        self.channels[channel].discard(client_id)
        if not self.channels[channel]:
            del self.channels[channel]

        if client_id in self.connections:
            self.connections[client_id].subscriptions.discard(channel)

        self._stats["channels_active"] = len(self.channels)

    async def broadcast_to_channel(
        self, channel: str, message: Dict[str, Any], exclude: Optional[str] = None
    ) -> int:
        """Broadcast message to all clients in a channel"""
        client_ids = self.channels.get(channel, set())
        sent_count = 0

        for client_id in list(client_ids):
            if client_id != exclude:
                if await self.send_to_client(client_id, message):
                    sent_count += 1

        return sent_count

    async def get_channel_size(self, channel: str) -> int:
        """Get number of clients in a channel"""
        return len(self.channels.get(channel, set()))

    async def list_channels(self) -> List[Dict[str, Any]]:
        """List all channels with their sizes"""
        return [
            {
                "channel": channel,
                "client_count": len(client_ids),
                "clients": list(client_ids),
            }
            for channel, client_ids in self.channels.items()
        ]

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            **self._stats,
            "channels": len(self.channels),
            "users_connected": len(self.user_connections),
            "uptime": datetime.now(timezone.utc).isoformat(),
        }

    async def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific client"""
        connection = self.connections.get(client_id)
        if not connection:
            return None

        return connection.to_dict()

    async def _monitor_connections(self):
        """Monitor connections for health and cleanup stale connections"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                # Find stale connections
                stale_connections = []
                for client_id, connection in self.connections.items():
                    if connection.is_stale() or not connection.is_active:
                        stale_connections.append(client_id)

                # Cleanup stale connections
                for client_id in stale_connections:
                    await self.disconnect(client_id, reason="Stale connection cleanup")

                if stale_connections:
                    logger.info(
                        f"Cleaned up {len(stale_connections)} stale connections"
                    )

            except Exception as e:
                logger.error(f"Connection monitoring error: {e}")

    async def shutdown(self):
        """Graceful shutdown of WebSocket manager"""
        logger.info("Shutting down WebSocketManager...")

        # Cancel monitoring task
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        disconnect_tasks = []
        for client_id in list(self.connections.keys()):
            task = asyncio.create_task(
                self.disconnect(client_id, reason="Server shutdown")
            )
            disconnect_tasks.append(task)

        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        logger.info("WebSocketManager shutdown completed")


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


# WebSocket endpoint handler
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    """Main WebSocket endpoint handler"""
    connection_id = None

    try:
        # Extract user info if available (from query params, headers, etc.)
        user_id = websocket.query_params.get("user_id")

        # Connect client
        connection_id = await websocket_manager.connect(websocket, client_id, user_id)

        # Handle messages
        while True:
            try:
                message = await websocket.receive_text()
                await websocket_manager.handle_message(connection_id, message)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(
                    f"Error in WebSocket message loop for {connection_id}: {e}"
                )
                break

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")

    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id, reason="Connection ended")


# Utility functions for broadcasting events


async def broadcast_content_update(content_data: Dict[str, Any]):
    """Broadcast content generation updates"""
    message = {
        "type": "content_update",
        "data": content_data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    await websocket_manager.broadcast_to_channel("content_updates", message)


async def broadcast_quiz_event(quiz_data: Dict[str, Any]):
    """Broadcast quiz-related events"""
    message = {
        "type": "quiz_event",
        "data": quiz_data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    await websocket_manager.broadcast_to_channel("quiz_events", message)


async def broadcast_system_notification(notification: str, level: str = "info"):
    """Broadcast system notifications"""
    message = {
        "type": "system_notification",
        "level": level,
        "message": notification,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    await websocket_manager.broadcast(message)


# Export public interface
__all__ = [
    "WebSocketManager",
    "WebSocketConnection",
    "MessageHandler",
    "websocket_manager",
    "websocket_endpoint",
    "broadcast_content_update",
    "broadcast_quiz_event",
    "broadcast_system_notification",
]
