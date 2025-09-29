"""
Roblox WebSocket Handler for Real-time Synchronization
Provides bidirectional communication between Roblox Studio and backend services
"""

import json
import asyncio
import logging
from typing import Dict, Set, Any, Optional
from datetime import datetime
import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import uuid
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types"""
    # Client to Server
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SCRIPT_UPDATE = "script_update"
    DEPLOYMENT_REQUEST = "deployment_request"
    VALIDATION_REQUEST = "validation_request"

    # Server to Client
    CONNECTION_ACK = "connection_ack"
    DEPLOYMENT_STATUS = "deployment_status"
    VALIDATION_RESULT = "validation_result"
    AGENT_UPDATE = "agent_update"
    SCRIPT_GENERATED = "script_generated"
    ERROR = "error"
    BROADCAST = "broadcast"


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    client_id: Optional[str] = None


class RobloxClient(BaseModel):
    """Connected Roblox client information"""
    client_id: str
    websocket: Any  # WebSocket instance
    place_id: Optional[str] = None
    user_id: Optional[str] = None
    subscriptions: Set[str] = Field(default_factory=set)
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)


class RobloxWebSocketHandler:
    """Manages WebSocket connections for Roblox clients"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.redis_pubsub: Optional[redis.client.PubSub] = None
        self.clients: Dict[str, RobloxClient] = {}
        self.subscription_channels = {
            "deployments": "roblox:deployment:updates",
            "agents": "roblox:agent:updates",
            "scripts": "roblox:script:updates",
            "validation": "roblox:validation:updates"
        }
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 90  # seconds

    async def initialize(self):
        """Initialize Redis connection and pub/sub"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self.redis_pubsub = self.redis_client.pubsub()

            # Subscribe to all channels
            for channel in self.subscription_channels.values():
                await self.redis_pubsub.subscribe(channel)

            # Start listening for Redis messages
            asyncio.create_task(self._redis_listener())

            # Start heartbeat monitor
            asyncio.create_task(self._heartbeat_monitor())

            logger.info("WebSocket handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket handler: {e}")
            raise

    async def close(self):
        """Close Redis connections"""
        if self.redis_pubsub:
            await self.redis_pubsub.close()
        if self.redis_client:
            await self.redis_client.close()

    async def handle_connection(self, websocket: WebSocket, token: Optional[str] = None):
        """Handle new WebSocket connection from Roblox client with authentication"""

        # Require authentication token
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            logger.warning("WebSocket connection rejected: No token provided")
            return

        # Verify JWT token
        from apps.backend.core.security.jwt_rotation import get_jwt_manager
        jwt_manager = await get_jwt_manager()
        token_payload = await jwt_manager.verify_token(token)

        if not token_payload:
            await websocket.close(code=1008, reason="Invalid authentication token")
            logger.warning("WebSocket connection rejected: Invalid token")
            return

        # Accept the connection
        await websocket.accept()

        # Generate client ID from user ID
        client_id = f"client_{token_payload.sub}_{str(uuid.uuid4())[:8]}"

        # Create client instance with user info
        client = RobloxClient(
            client_id=client_id,
            websocket=websocket,
            user_id=token_payload.sub
        )

        self.clients[client_id] = client

        # Send connection acknowledgment with auth info
        await self._send_message(client_id, WebSocketMessage(
            type=MessageType.CONNECTION_ACK,
            payload={
                "client_id": client_id,
                "user_id": token_payload.sub,
                "scope": token_payload.scope,
                "server_time": datetime.utcnow().isoformat(),
                "available_subscriptions": list(self.subscription_channels.keys())
            }
        ))

        logger.info(f"Roblox client authenticated and connected: {client_id} (user: {token_payload.sub})")

        try:
            # Handle incoming messages
            while True:
                data = await websocket.receive_text()
                await self._handle_message(client_id, data)

        except WebSocketDisconnect:
            await self._handle_disconnect(client_id)
        except Exception as e:
            logger.error(f"WebSocket error for client {client_id}: {e}")
            await self._handle_disconnect(client_id)

    async def _handle_message(self, client_id: str, data: str):
        """Process incoming WebSocket message"""
        try:
            message = WebSocketMessage.model_validate_json(data)
            message.client_id = client_id

            client = self.clients.get(client_id)
            if not client:
                logger.warning(f"Message from unknown client: {client_id}")
                return

            # Update last activity
            client.last_heartbeat = datetime.utcnow()

            # Route message by type
            if message.type == MessageType.HEARTBEAT:
                await self._handle_heartbeat(client_id)

            elif message.type == MessageType.SUBSCRIBE:
                await self._handle_subscribe(client_id, message.payload)

            elif message.type == MessageType.UNSUBSCRIBE:
                await self._handle_unsubscribe(client_id, message.payload)

            elif message.type == MessageType.SCRIPT_UPDATE:
                await self._handle_script_update(client_id, message.payload)

            elif message.type == MessageType.DEPLOYMENT_REQUEST:
                await self._handle_deployment_request(client_id, message.payload)

            elif message.type == MessageType.VALIDATION_REQUEST:
                await self._handle_validation_request(client_id, message.payload)

            else:
                logger.warning(f"Unknown message type: {message.type}")

        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            await self._send_error(client_id, str(e))

    async def _handle_heartbeat(self, client_id: str):
        """Handle heartbeat message"""
        client = self.clients.get(client_id)
        if client:
            client.last_heartbeat = datetime.utcnow()
            await self._send_message(client_id, WebSocketMessage(
                type=MessageType.HEARTBEAT,
                payload={"status": "alive"}
            ))

    async def _handle_subscribe(self, client_id: str, payload: Dict[str, Any]):
        """Handle subscription request"""
        client = self.clients.get(client_id)
        if not client:
            return

        channels = payload.get("channels", [])
        for channel in channels:
            if channel in self.subscription_channels:
                client.subscriptions.add(channel)
                logger.info(f"Client {client_id} subscribed to {channel}")

        await self._send_message(client_id, WebSocketMessage(
            type=MessageType.CONNECTION_ACK,
            payload={
                "subscribed": list(client.subscriptions)
            }
        ))

    async def _handle_unsubscribe(self, client_id: str, payload: Dict[str, Any]):
        """Handle unsubscribe request"""
        client = self.clients.get(client_id)
        if not client:
            return

        channels = payload.get("channels", [])
        for channel in channels:
            client.subscriptions.discard(channel)
            logger.info(f"Client {client_id} unsubscribed from {channel}")

    async def _handle_script_update(self, client_id: str, payload: Dict[str, Any]):
        """Handle script update from Roblox"""
        try:
            # Publish to Redis for other services
            await self.redis_client.publish(
                self.subscription_channels["scripts"],
                json.dumps({
                    "client_id": client_id,
                    "script_id": payload.get("script_id"),
                    "script_type": payload.get("script_type"),
                    "content": payload.get("content"),
                    "timestamp": datetime.utcnow().isoformat()
                })
            )

            # Acknowledge receipt
            await self._send_message(client_id, WebSocketMessage(
                type=MessageType.SCRIPT_GENERATED,
                payload={
                    "status": "received",
                    "script_id": payload.get("script_id")
                }
            ))

        except Exception as e:
            logger.error(f"Error handling script update: {e}")
            await self._send_error(client_id, str(e))

    async def _handle_deployment_request(self, client_id: str, payload: Dict[str, Any]):
        """Handle deployment request from Roblox"""
        try:
            # Import deployment service
            from apps.backend.services.roblox_deployment import (
                get_deployment_pipeline,
                DeploymentRequest,
                ContentType
            )

            # Get deployment pipeline
            pipeline = await get_deployment_pipeline()

            # Create deployment request
            deployment_request = DeploymentRequest(
                content_type=ContentType(payload.get("content_type", "script")),
                content_data=payload.get("content_data", ""),
                target_place_id=payload.get("target_place_id"),
                priority=payload.get("priority", 5),
                user_id=client_id,
                metadata={
                    "source": "websocket",
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            # Queue deployment
            deployment_id = await pipeline.queue_deployment(deployment_request)

            # Send immediate acknowledgment
            await self._send_message(client_id, WebSocketMessage(
                type=MessageType.DEPLOYMENT_STATUS,
                payload={
                    "deployment_id": deployment_id,
                    "status": "queued"
                }
            ))

        except Exception as e:
            logger.error(f"Error handling deployment request: {e}")
            await self._send_error(client_id, str(e))

    async def _handle_validation_request(self, client_id: str, payload: Dict[str, Any]):
        """Handle validation request from Roblox"""
        try:
            # Publish to validation channel
            await self.redis_client.publish(
                self.subscription_channels["validation"],
                json.dumps({
                    "client_id": client_id,
                    "script": payload.get("script", ""),
                    "script_type": payload.get("script_type", "ServerScript"),
                    "strict_mode": payload.get("strict_mode", True),
                    "timestamp": datetime.utcnow().isoformat()
                })
            )

            # Mock validation result for now
            await self._send_message(client_id, WebSocketMessage(
                type=MessageType.VALIDATION_RESULT,
                payload={
                    "risk_score": 3,
                    "vulnerabilities": [],
                    "recommendations": ["Code looks secure"],
                    "status": "completed"
                }
            ))

        except Exception as e:
            logger.error(f"Error handling validation request: {e}")
            await self._send_error(client_id, str(e))

    async def _handle_disconnect(self, client_id: str):
        """Handle client disconnection"""
        if client_id in self.clients:
            del self.clients[client_id]
            logger.info(f"Roblox client disconnected: {client_id}")

    async def _send_message(self, client_id: str, message: WebSocketMessage):
        """Send message to specific client"""
        client = self.clients.get(client_id)
        if client:
            try:
                await client.websocket.send_text(message.model_dump_json())
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                await self._handle_disconnect(client_id)

    async def _send_error(self, client_id: str, error: str):
        """Send error message to client"""
        await self._send_message(client_id, WebSocketMessage(
            type=MessageType.ERROR,
            payload={"error": error}
        ))

    async def broadcast(self, message: WebSocketMessage, channel: Optional[str] = None):
        """Broadcast message to all clients or channel subscribers"""
        for client_id, client in self.clients.items():
            if channel is None or channel in client.subscriptions:
                await self._send_message(client_id, message)

    async def _redis_listener(self):
        """Listen for Redis pub/sub messages"""
        try:
            async for message in self.redis_pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    data = json.loads(message["data"])

                    # Find subscription type
                    subscription_type = None
                    for sub_type, sub_channel in self.subscription_channels.items():
                        if sub_channel == channel:
                            subscription_type = sub_type
                            break

                    if subscription_type:
                        # Broadcast to subscribed clients
                        ws_message = WebSocketMessage(
                            type=MessageType.BROADCAST,
                            payload={
                                "channel": subscription_type,
                                "data": data
                            }
                        )
                        await self.broadcast(ws_message, subscription_type)

        except Exception as e:
            logger.error(f"Redis listener error: {e}")

    async def _heartbeat_monitor(self):
        """Monitor client heartbeats and disconnect inactive clients"""
        while True:
            try:
                current_time = datetime.utcnow()
                disconnected_clients = []

                for client_id, client in self.clients.items():
                    time_since_heartbeat = (current_time - client.last_heartbeat).total_seconds()

                    if time_since_heartbeat > self.heartbeat_timeout:
                        logger.warning(f"Client {client_id} timed out")
                        disconnected_clients.append(client_id)

                # Disconnect timed-out clients
                for client_id in disconnected_clients:
                    await self._handle_disconnect(client_id)

                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                await asyncio.sleep(self.heartbeat_interval)


# Singleton instance
_websocket_handler: Optional[RobloxWebSocketHandler] = None


async def get_websocket_handler() -> RobloxWebSocketHandler:
    """Get or create WebSocket handler instance"""
    global _websocket_handler

    if _websocket_handler is None:
        _websocket_handler = RobloxWebSocketHandler()
        await _websocket_handler.initialize()

    return _websocket_handler