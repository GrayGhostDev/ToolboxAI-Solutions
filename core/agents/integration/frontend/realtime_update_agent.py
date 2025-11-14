"""
Realtime Update Agent - Manages Pusher channels and WebSocket communications

This agent handles:
- Pusher channel subscription management
- Real-time event broadcasting
- WebSocket connection fallback
- Event filtering and routing
- Connection health monitoring
- Message queuing and delivery guarantees
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

from core.agents.base_agent import AgentConfig

from ..base_integration_agent import (
    BaseIntegrationAgent,
    IntegrationEvent,
    IntegrationPlatform,
    TaskResult,
)

logger = logging.getLogger(__name__)


class ChannelType(Enum):
    """Pusher channel types"""

    PUBLIC = "public"
    PRIVATE = "private"
    PRESENCE = "presence"


class ConnectionState(Enum):
    """Connection states"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class Channel:
    """Pusher channel definition"""

    channel_name: str
    channel_type: ChannelType
    subscribed: bool = False
    subscribers: set[str] = field(default_factory=set)
    event_handlers: dict[str, list[Callable]] = field(default_factory=lambda: defaultdict(list))
    last_activity: Optional[datetime] = None
    message_count: int = 0


@dataclass
class RealtimeMessage:
    """Realtime message wrapper"""

    message_id: str
    channel: str
    event: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retries: int = 0
    delivered: bool = False
    acknowledgment_required: bool = False


@dataclass
class ConnectionMetrics:
    """Connection health metrics"""

    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    connected_at: Optional[datetime] = None
    disconnected_at: Optional[datetime] = None
    reconnection_attempts: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    messages_failed: int = 0
    average_latency_ms: float = 0.0
    last_error: Optional[str] = None


class MessageQueue:
    """Queue for reliable message delivery"""

    def __init__(self, max_size: int = 1000):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self.pending: dict[str, RealtimeMessage] = {}
        self.delivered: set[str] = set()

    async def enqueue(self, message: RealtimeMessage):
        """Add message to queue"""
        await self.queue.put(message)
        if message.acknowledgment_required:
            self.pending[message.message_id] = message

    async def dequeue(self) -> Optional[RealtimeMessage]:
        """Get next message from queue"""
        try:
            return await self.queue.get()
        except asyncio.QueueEmpty:
            return None

    def acknowledge(self, message_id: str):
        """Acknowledge message delivery"""
        if message_id in self.pending:
            message = self.pending.pop(message_id)
            message.delivered = True
            self.delivered.add(message_id)

    def get_undelivered(self) -> list[RealtimeMessage]:
        """Get undelivered messages for retry"""
        return [msg for msg in self.pending.values() if not msg.delivered]


class RealtimeUpdateAgent(BaseIntegrationAgent):
    """
    Realtime Update Agent for managing Pusher and WebSocket communications
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize Realtime Update Agent"""
        if config is None:
            config = AgentConfig(
                name="RealtimeUpdateAgent",
                system_prompt="""You are a Realtime Update Agent responsible for:
                - Managing Pusher channel subscriptions
                - Broadcasting real-time events to connected clients
                - Handling WebSocket fallback connections
                - Routing and filtering events
                - Ensuring reliable message delivery
                - Monitoring connection health
                """,
            )
        super().__init__(config)

        # Channel management
        self.channels: dict[str, Channel] = {}
        self.user_channels: dict[str, set[str]] = defaultdict(set)  # user_id -> channels

        # Connection management
        self.connection_metrics = ConnectionMetrics()
        self.pusher_client = None
        self.websocket_connections: dict[str, Any] = {}

        # Message handling
        self.message_queue = MessageQueue()
        self.event_filters: dict[str, Callable] = {}

        # Presence tracking
        self.presence_data: dict[str, dict[str, Any]] = {}  # channel -> user data

        # Performance
        self.latency_samples: list[float] = []
        self.max_retry_attempts = 3
        self.retry_delay = 1.0  # seconds

    async def initialize_pusher(
        self, app_id: str, key: str, secret: str, cluster: str
    ) -> TaskResult:
        """Initialize Pusher client"""
        try:
            # Import pusher client (would use actual pusher library)
            # from pusher import Pusher
            # self.pusher_client = Pusher(
            #     app_id=app_id,
            #     key=key,
            #     secret=secret,
            #     cluster=cluster,
            #     ssl=True
            # )

            # Simulated initialization
            self.pusher_client = {
                "app_id": app_id,
                "key": key,
                "cluster": cluster,
                "initialized": True,
            }

            self.connection_metrics.connection_state = ConnectionState.CONNECTED
            self.connection_metrics.connected_at = datetime.utcnow()

            logger.info("Pusher client initialized successfully")

            return TaskResult(success=True, output={"pusher_initialized": True, "cluster": cluster})

        except Exception as e:
            logger.error(f"Error initializing Pusher: {e}")
            self.connection_metrics.connection_state = ConnectionState.FAILED
            self.connection_metrics.last_error = str(e)
            return TaskResult(success=False, output=None, error=str(e))

    async def subscribe_channel(
        self,
        channel_name: str,
        channel_type: ChannelType = ChannelType.PUBLIC,
        user_id: Optional[str] = None,
        user_info: Optional[dict[str, Any]] = None,
    ) -> TaskResult:
        """Subscribe to a Pusher channel"""
        try:
            if channel_name in self.channels:
                channel = self.channels[channel_name]
                if user_id:
                    channel.subscribers.add(user_id)
                    self.user_channels[user_id].add(channel_name)

                return TaskResult(
                    success=True,
                    output={"channel": channel_name, "already_subscribed": True},
                )

            # Create channel
            channel = Channel(channel_name=channel_name, channel_type=channel_type, subscribed=True)

            if user_id:
                channel.subscribers.add(user_id)
                self.user_channels[user_id].add(channel_name)

            # Handle presence channel
            if channel_type == ChannelType.PRESENCE and user_id and user_info:
                self.presence_data[channel_name] = self.presence_data.get(channel_name, {})
                self.presence_data[channel_name][user_id] = user_info

            self.channels[channel_name] = channel
            channel.last_activity = datetime.utcnow()

            # Emit subscription event
            await self.emit_event(
                IntegrationEvent(
                    event_id=f"channel_subscribed_{channel_name}",
                    event_type="channel_subscribed",
                    source_platform=IntegrationPlatform.MESSAGING,
                    payload={
                        "channel": channel_name,
                        "type": channel_type.value,
                        "user_id": user_id,
                        "subscriber_count": len(channel.subscribers),
                    },
                )
            )

            logger.info(f"Subscribed to channel: {channel_name}")

            return TaskResult(
                success=True,
                output={
                    "channel": channel_name,
                    "subscribed": True,
                    "type": channel_type.value,
                },
            )

        except Exception as e:
            logger.error(f"Error subscribing to channel: {e}")
            return TaskResult(success=False, output=None, error=str(e))

    async def unsubscribe_channel(
        self, channel_name: str, user_id: Optional[str] = None
    ) -> TaskResult:
        """Unsubscribe from a channel"""
        try:
            if channel_name not in self.channels:
                return TaskResult(
                    success=False,
                    output=None,
                    error=f"Channel not found: {channel_name}",
                )

            channel = self.channels[channel_name]

            if user_id:
                channel.subscribers.discard(user_id)
                self.user_channels[user_id].discard(channel_name)

                # Remove from presence data
                if channel.channel_type == ChannelType.PRESENCE:
                    if channel_name in self.presence_data:
                        self.presence_data[channel_name].pop(user_id, None)

                # If no more subscribers, remove channel
                if not channel.subscribers:
                    del self.channels[channel_name]
                    logger.info(f"Channel {channel_name} removed (no subscribers)")
            else:
                # Unsubscribe all
                for uid in list(channel.subscribers):
                    self.user_channels[uid].discard(channel_name)
                del self.channels[channel_name]
                if channel_name in self.presence_data:
                    del self.presence_data[channel_name]

            logger.info(f"Unsubscribed from channel: {channel_name}")

            return TaskResult(success=True, output={"channel": channel_name, "unsubscribed": True})

        except Exception as e:
            logger.error(f"Error unsubscribing from channel: {e}")
            return TaskResult(success=False, output=None, error=str(e))

    async def broadcast_event(
        self,
        channel_name: str,
        event_name: str,
        data: Any,
        exclude_user: Optional[str] = None,
    ) -> TaskResult:
        """Broadcast an event to a channel"""
        try:
            if channel_name not in self.channels:
                return TaskResult(
                    success=False,
                    output=None,
                    error=f"Channel not found: {channel_name}",
                )

            channel = self.channels[channel_name]

            # Create message
            message = RealtimeMessage(
                message_id=f"msg_{datetime.utcnow().timestamp()}",
                channel=channel_name,
                event=event_name,
                data=data,
                acknowledgment_required=(channel.channel_type != ChannelType.PUBLIC),
            )

            # Queue message
            await self.message_queue.enqueue(message)

            # Send via Pusher (simulated)
            if self.pusher_client:
                # self.pusher_client.trigger(channel_name, event_name, data)
                pass

            # Update metrics
            channel.message_count += 1
            channel.last_activity = datetime.utcnow()
            self.connection_metrics.messages_sent += 1

            # Call event handlers
            if event_name in channel.event_handlers:
                for handler in channel.event_handlers[event_name]:
                    try:
                        await handler(data)
                    except Exception as handler_error:
                        logger.error(f"Event handler error: {handler_error}")

            # Emit broadcast event
            await self.emit_event(
                IntegrationEvent(
                    event_id=message.message_id,
                    event_type="event_broadcast",
                    source_platform=IntegrationPlatform.MESSAGING,
                    payload={
                        "channel": channel_name,
                        "event": event_name,
                        "recipients": len(channel.subscribers) - (1 if exclude_user else 0),
                    },
                )
            )

            return TaskResult(
                success=True,
                output={
                    "message_id": message.message_id,
                    "channel": channel_name,
                    "event": event_name,
                    "recipients": len(channel.subscribers),
                },
            )

        except Exception as e:
            logger.error(f"Error broadcasting event: {e}")
            self.connection_metrics.messages_failed += 1
            return TaskResult(success=False, output=None, error=str(e))

    async def register_event_handler(
        self, channel_name: str, event_name: str, handler: Callable
    ) -> TaskResult:
        """Register an event handler for a channel event"""
        try:
            if channel_name not in self.channels:
                # Auto-create channel if needed
                await self.subscribe_channel(channel_name)

            channel = self.channels[channel_name]
            channel.event_handlers[event_name].append(handler)

            logger.info(f"Registered handler for {event_name} on {channel_name}")

            return TaskResult(
                success=True,
                output={
                    "channel": channel_name,
                    "event": event_name,
                    "handler_registered": True,
                },
            )

        except Exception as e:
            logger.error(f"Error registering event handler: {e}")
            return TaskResult(success=False, output=None, error=str(e))

    async def handle_websocket_fallback(self, ws_id: str, ws_connection: Any) -> TaskResult:
        """Handle WebSocket fallback connection"""
        try:
            self.websocket_connections[ws_id] = ws_connection

            # Process queued messages for this connection
            undelivered = self.message_queue.get_undelivered()
            for message in undelivered:
                if message.retries < self.max_retry_attempts:
                    # Attempt delivery via WebSocket
                    try:
                        # await ws_connection.send_json(message.data)
                        self.message_queue.acknowledge(message.message_id)
                    except Exception:
                        message.retries += 1
                        await asyncio.sleep(self.retry_delay * message.retries)

            return TaskResult(
                success=True,
                output={
                    "ws_id": ws_id,
                    "connected": True,
                    "undelivered_processed": len(undelivered),
                },
            )

        except Exception as e:
            logger.error(f"Error handling WebSocket fallback: {e}")
            return TaskResult(success=False, output=None, error=str(e))

    async def get_presence_members(self, channel_name: str) -> TaskResult:
        """Get members in a presence channel"""
        try:
            if channel_name not in self.channels:
                return TaskResult(
                    success=False,
                    output=None,
                    error=f"Channel not found: {channel_name}",
                )

            channel = self.channels[channel_name]
            if channel.channel_type != ChannelType.PRESENCE:
                return TaskResult(success=False, output=None, error="Not a presence channel")

            members = self.presence_data.get(channel_name, {})

            return TaskResult(
                success=True,
                output={
                    "channel": channel_name,
                    "members": list(members.values()),
                    "count": len(members),
                },
            )

        except Exception as e:
            logger.error(f"Error getting presence members: {e}")
            return TaskResult(success=False, output=None, error=str(e))

    async def monitor_connection_health(self) -> TaskResult:
        """Monitor realtime connection health"""
        try:
            health_status = {
                "connection_state": self.connection_metrics.connection_state.value,
                "connected": self.connection_metrics.connection_state == ConnectionState.CONNECTED,
                "channels": {
                    "total": len(self.channels),
                    "active": sum(
                        1
                        for c in self.channels.values()
                        if c.last_activity
                        and (datetime.utcnow() - c.last_activity).total_seconds() < 300
                    ),
                },
                "messages": {
                    "sent": self.connection_metrics.messages_sent,
                    "received": self.connection_metrics.messages_received,
                    "failed": self.connection_metrics.messages_failed,
                    "queued": self.message_queue.queue.qsize(),
                    "pending": len(self.message_queue.pending),
                },
                "websocket_fallbacks": len(self.websocket_connections),
            }

            # Calculate message delivery rate
            if self.connection_metrics.messages_sent > 0:
                delivery_rate = (
                    self.connection_metrics.messages_sent - self.connection_metrics.messages_failed
                ) / self.connection_metrics.messages_sent
                health_status["delivery_rate"] = delivery_rate
            else:
                health_status["delivery_rate"] = 1.0

            # Check if reconnection needed
            if self.connection_metrics.connection_state in [
                ConnectionState.DISCONNECTED,
                ConnectionState.FAILED,
            ]:
                health_status["action_required"] = "reconnection_needed"

            # Calculate average latency
            if self.latency_samples:
                avg_latency = sum(self.latency_samples) / len(self.latency_samples)
                health_status["average_latency_ms"] = avg_latency

                if avg_latency > 500:  # More than 500ms
                    health_status["warning"] = "High latency detected"

            return TaskResult(success=True, output=health_status)

        except Exception as e:
            logger.error(f"Error monitoring connection health: {e}")
            return TaskResult(success=False, output=None, error=str(e))

    async def cleanup_idle_channels(self, idle_threshold_minutes: int = 30) -> TaskResult:
        """Clean up idle channels"""
        try:
            idle_threshold = timedelta(minutes=idle_threshold_minutes)
            now = datetime.utcnow()
            cleaned_channels = []

            for channel_name in list(self.channels.keys()):
                channel = self.channels[channel_name]

                # Check if channel is idle
                if channel.last_activity:
                    idle_time = now - channel.last_activity
                    if idle_time > idle_threshold and not channel.subscribers:
                        del self.channels[channel_name]
                        cleaned_channels.append(channel_name)
                        logger.info(f"Cleaned up idle channel: {channel_name}")

            return TaskResult(
                success=True,
                output={
                    "cleaned_channels": cleaned_channels,
                    "count": len(cleaned_channels),
                },
            )

        except Exception as e:
            logger.error(f"Error cleaning up idle channels: {e}")
            return TaskResult(success=False, output=None, error=str(e))

    async def _process_integration_event(self, event: IntegrationEvent):
        """Process integration events for realtime updates"""
        if event.event_type == "broadcast_request":
            # Broadcast event to channel
            await self.broadcast_event(
                channel_name=event.payload["channel"],
                event_name=event.payload["event"],
                data=event.payload["data"],
                exclude_user=event.payload.get("exclude_user"),
            )

        elif event.event_type == "subscribe_request":
            # Subscribe to channel
            await self.subscribe_channel(
                channel_name=event.payload["channel"],
                channel_type=ChannelType[event.payload.get("type", "PUBLIC")],
                user_id=event.payload.get("user_id"),
                user_info=event.payload.get("user_info"),
            )

        elif event.event_type == "unsubscribe_request":
            # Unsubscribe from channel
            await self.unsubscribe_channel(
                channel_name=event.payload["channel"],
                user_id=event.payload.get("user_id"),
            )

    async def execute_task(self, task: str, context: Optional[dict[str, Any]] = None) -> TaskResult:
        """Execute realtime update specific tasks"""
        if task == "initialize_pusher":
            return await self.initialize_pusher(
                app_id=context["app_id"],
                key=context["key"],
                secret=context["secret"],
                cluster=context["cluster"],
            )
        elif task == "subscribe":
            return await self.subscribe_channel(
                channel_name=context["channel"],
                channel_type=ChannelType[context.get("type", "PUBLIC")],
                user_id=context.get("user_id"),
                user_info=context.get("user_info"),
            )
        elif task == "unsubscribe":
            return await self.unsubscribe_channel(
                channel_name=context["channel"], user_id=context.get("user_id")
            )
        elif task == "broadcast":
            return await self.broadcast_event(
                channel_name=context["channel"],
                event_name=context["event"],
                data=context["data"],
                exclude_user=context.get("exclude_user"),
            )
        elif task == "get_presence":
            return await self.get_presence_members(context["channel"])
        elif task == "monitor_health":
            return await self.monitor_connection_health()
        elif task == "cleanup_channels":
            return await self.cleanup_idle_channels(
                idle_threshold_minutes=context.get("idle_threshold", 30)
            )
        else:
            return await super().execute_task(task, context)
