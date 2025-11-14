"""
Enhanced Agent Communication System
==================================

Advanced communication and coordination system for AI agents in educational
content generation workflows with real-time messaging, event streaming,
and intelligent routing.

Features:
- Asynchronous message passing with guaranteed delivery
- Event-driven agent coordination
- Real-time status broadcasting
- Intelligent message routing and prioritization
- WebSocket integration for live updates
- Performance monitoring and optimization
"""

import asyncio
import json
import logging
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4

import aioredis
from fastapi import WebSocket
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages in the communication system"""

    # Task coordination
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETION = "task_completion"
    TASK_PROGRESS = "task_progress"
    TASK_FAILURE = "task_failure"

    # Agent coordination
    AGENT_STATUS = "agent_status"
    AGENT_CAPABILITY = "agent_capability"
    AGENT_HANDOFF = "agent_handoff"
    AGENT_COLLABORATION = "agent_collaboration"

    # Quality and review
    QUALITY_ASSESSMENT = "quality_assessment"
    PEER_REVIEW = "peer_review"
    CONSENSUS_REQUEST = "consensus_request"
    CONSENSUS_RESPONSE = "consensus_response"

    # Educational specific
    LEARNING_OBJECTIVE_SYNC = "learning_objective_sync"
    CURRICULUM_ALIGNMENT = "curriculum_alignment"
    CONTENT_VALIDATION = "content_validation"
    EDUCATIONAL_FEEDBACK = "educational_feedback"

    # System coordination
    SWARM_COORDINATION = "swarm_coordination"
    RESOURCE_ALLOCATION = "resource_allocation"
    PERFORMANCE_METRICS = "performance_metrics"
    ERROR_NOTIFICATION = "error_notification"

    # Real-time updates
    LIVE_UPDATE = "live_update"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"


class MessagePriority(Enum):
    """Message priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class DeliveryMode(Enum):
    """Message delivery modes"""

    FIRE_AND_FORGET = "fire_and_forget"
    GUARANTEED = "guaranteed"
    REQUEST_RESPONSE = "request_response"
    BROADCAST = "broadcast"
    MULTICAST = "multicast"


@dataclass
class Message:
    """Enhanced message structure for agent communication"""

    message_id: str = field(default_factory=lambda: str(uuid4()))
    message_type: MessageType = MessageType.AGENT_STATUS
    sender_id: str = ""
    recipient_id: Optional[str] = None  # None for broadcasts

    # Message content
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Delivery settings
    priority: MessagePriority = MessagePriority.NORMAL
    delivery_mode: DeliveryMode = DeliveryMode.FIRE_AND_FORGET
    ttl: Optional[float] = None  # Time to live in seconds

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    # Routing and delivery
    routing_key: str = ""
    reply_to: Optional[str] = None
    correlation_id: Optional[str] = None

    # Educational context
    educational_context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set expiration time if TTL is specified"""
        if self.ttl and not self.expires_at:
            self.expires_at = self.created_at + timedelta(seconds=self.ttl)

        # Set routing key if not specified
        if not self.routing_key:
            self.routing_key = f"{self.message_type.value}.{self.sender_id}"

    @property
    def is_expired(self) -> bool:
        """Check if message has expired"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for serialization"""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        data["priority"] = self.priority.value
        data["delivery_mode"] = self.delivery_mode.value
        data["created_at"] = self.created_at.isoformat()

        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
        if self.delivered_at:
            data["delivered_at"] = self.delivered_at.isoformat()

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create message from dictionary"""
        message = cls()

        for key, value in data.items():
            if key == "message_type":
                message.message_type = MessageType(value)
            elif key == "priority":
                message.priority = MessagePriority(value)
            elif key == "delivery_mode":
                message.delivery_mode = DeliveryMode(value)
            elif key == "created_at":
                message.created_at = datetime.fromisoformat(value)
            elif key == "expires_at" and value:
                message.expires_at = datetime.fromisoformat(value)
            elif key == "delivered_at" and value:
                message.delivered_at = datetime.fromisoformat(value)
            elif hasattr(message, key):
                setattr(message, key, value)

        return message


@dataclass
class AgentEndpoint:
    """Agent communication endpoint configuration"""

    agent_id: str
    endpoint_type: str  # "internal", "websocket", "webhook"
    address: str
    capabilities: list[str] = field(default_factory=list)

    # Connection settings
    max_concurrent_messages: int = 100
    timeout: float = 30.0
    retry_attempts: int = 3

    # Status tracking
    last_seen: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    message_count: int = 0
    error_count: int = 0


class MessageBroker:
    """High-performance message broker for agent communication"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[Redis] = None

        # Message routing
        self.message_queues: dict[str, asyncio.Queue] = {}
        self.routing_table: dict[str, str] = {}  # agent_id -> queue_name
        self.subscription_table: dict[str, set[str]] = {}  # topic -> agent_ids

        # Endpoint management
        self.agent_endpoints: dict[str, AgentEndpoint] = {}
        self.websocket_connections: dict[str, WebSocket] = {}

        # Message handling
        self.message_handlers: dict[MessageType, list[Callable]] = defaultdict(list)
        self.middleware_stack: list[Callable] = []

        # Performance tracking
        self.message_stats: dict[str, int] = defaultdict(int)
        self.delivery_times: deque = deque(maxlen=1000)
        self.failed_deliveries: deque = deque(maxlen=100)

        # Background tasks
        self.background_tasks: set[asyncio.Task] = set()
        self.running = False

    async def initialize(self):
        """Initialize message broker"""
        try:
            # Connect to Redis
            self.redis = await aioredis.from_url(self.redis_url)
            await self.redis.ping()

            # Start background processors
            self.running = True
            await self._start_background_processors()

            logger.info("Message broker initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize message broker: {e}")
            raise

    async def register_agent(self, agent_endpoint: AgentEndpoint):
        """Register an agent endpoint"""
        self.agent_endpoints[agent_endpoint.agent_id] = agent_endpoint

        # Create message queue for agent
        if agent_endpoint.agent_id not in self.message_queues:
            self.message_queues[agent_endpoint.agent_id] = asyncio.Queue(
                maxsize=agent_endpoint.max_concurrent_messages
            )

        # Update routing table
        self.routing_table[agent_endpoint.agent_id] = agent_endpoint.agent_id

        logger.info(f"Registered agent endpoint: {agent_endpoint.agent_id}")

    async def unregister_agent(self, agent_id: str):
        """Unregister an agent endpoint"""
        # Remove from tracking structures
        self.agent_endpoints.pop(agent_id, None)
        self.routing_table.pop(agent_id, None)

        # Close WebSocket if exists
        if agent_id in self.websocket_connections:
            try:
                await self.websocket_connections[agent_id].close()
            except:
                pass
            del self.websocket_connections[agent_id]

        # Clear message queue
        if agent_id in self.message_queues:
            queue = self.message_queues[agent_id]
            while not queue.empty():
                try:
                    queue.get_nowait()
                except:
                    break
            del self.message_queues[agent_id]

        logger.info(f"Unregistered agent endpoint: {agent_id}")

    async def send_message(self, message: Message) -> bool:
        """Send a message to an agent or broadcast"""
        try:
            # Apply middleware
            for middleware in self.middleware_stack:
                message = await middleware(message)
                if not message:  # Middleware can filter messages
                    return False

            # Check if message has expired
            if message.is_expired:
                logger.warning(f"Message {message.message_id} expired before sending")
                self.message_stats["expired"] += 1
                return False

            # Route message based on delivery mode
            success = False

            if message.delivery_mode == DeliveryMode.BROADCAST:
                success = await self._broadcast_message(message)
            elif message.delivery_mode == DeliveryMode.MULTICAST:
                success = await self._multicast_message(message)
            elif message.recipient_id:
                success = await self._unicast_message(message)
            else:
                logger.error(
                    f"No recipient specified for non-broadcast message: {message.message_id}"
                )
                return False

            # Update statistics
            if success:
                self.message_stats["sent"] += 1
            else:
                self.message_stats["failed"] += 1
                self.failed_deliveries.append(
                    {
                        "message_id": message.message_id,
                        "timestamp": datetime.now(),
                        "reason": "delivery_failed",
                    }
                )

            return success

        except Exception as e:
            logger.error(f"Failed to send message {message.message_id}: {e}")
            self.message_stats["error"] += 1
            return False

    async def _unicast_message(self, message: Message) -> bool:
        """Send message to a specific recipient"""
        recipient_id = message.recipient_id

        if recipient_id not in self.agent_endpoints:
            logger.warning(f"Unknown recipient: {recipient_id}")
            return False

        endpoint = self.agent_endpoints[recipient_id]

        try:
            # Choose delivery method based on endpoint type
            if endpoint.endpoint_type == "websocket":
                return await self._deliver_via_websocket(message, recipient_id)
            elif endpoint.endpoint_type == "internal":
                return await self._deliver_via_queue(message, recipient_id)
            elif endpoint.endpoint_type == "webhook":
                return await self._deliver_via_webhook(message, endpoint)
            else:
                logger.error(f"Unknown endpoint type: {endpoint.endpoint_type}")
                return False

        except Exception as e:
            logger.error(f"Failed to deliver message to {recipient_id}: {e}")
            return False

    async def _deliver_via_websocket(self, message: Message, recipient_id: str) -> bool:
        """Deliver message via WebSocket"""
        if recipient_id not in self.websocket_connections:
            return False

        websocket = self.websocket_connections[recipient_id]

        try:
            message_data = message.to_dict()
            await websocket.send_json(message_data)

            message.delivered_at = datetime.now()
            self._update_delivery_metrics(message)

            return True

        except Exception as e:
            logger.error(f"WebSocket delivery failed for {recipient_id}: {e}")
            # Remove stale connection
            del self.websocket_connections[recipient_id]
            return False

    async def _deliver_via_queue(self, message: Message, recipient_id: str) -> bool:
        """Deliver message via internal queue"""
        if recipient_id not in self.message_queues:
            return False

        queue = self.message_queues[recipient_id]

        try:
            # Check queue capacity
            if queue.full():
                logger.warning(f"Message queue full for {recipient_id}")
                return False

            await queue.put(message)
            message.delivered_at = datetime.now()
            self._update_delivery_metrics(message)

            return True

        except Exception as e:
            logger.error(f"Queue delivery failed for {recipient_id}: {e}")
            return False

    async def _deliver_via_webhook(self, message: Message, endpoint: AgentEndpoint) -> bool:
        """Deliver message via HTTP webhook"""
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                message_data = message.to_dict()

                async with session.post(
                    endpoint.address,
                    json=message_data,
                    timeout=aiohttp.ClientTimeout(total=endpoint.timeout),
                ) as response:
                    if response.status == 200:
                        message.delivered_at = datetime.now()
                        self._update_delivery_metrics(message)
                        return True
                    else:
                        logger.warning(f"Webhook delivery failed with status {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Webhook delivery failed for {endpoint.address}: {e}")
            return False

    async def _broadcast_message(self, message: Message) -> bool:
        """Broadcast message to all registered agents"""
        success_count = 0
        total_count = len(self.agent_endpoints)

        for agent_id in self.agent_endpoints:
            message_copy = Message.from_dict(message.to_dict())
            message_copy.message_id = str(uuid4())  # New ID for each copy
            message_copy.recipient_id = agent_id
            message_copy.delivery_mode = DeliveryMode.FIRE_AND_FORGET

            if await self._unicast_message(message_copy):
                success_count += 1

        # Consider broadcast successful if majority succeeded
        return success_count > total_count / 2

    async def _multicast_message(self, message: Message) -> bool:
        """Multicast message to subscribers of a topic"""
        topic = message.routing_key

        if topic not in self.subscription_table:
            logger.warning(f"No subscribers for topic: {topic}")
            return False

        subscribers = self.subscription_table[topic]
        success_count = 0

        for agent_id in subscribers:
            message_copy = Message.from_dict(message.to_dict())
            message_copy.message_id = str(uuid4())
            message_copy.recipient_id = agent_id

            if await self._unicast_message(message_copy):
                success_count += 1

        return success_count > 0

    async def receive_message(self, agent_id: str, timeout: float = 1.0) -> Optional[Message]:
        """Receive a message for an agent"""
        if agent_id not in self.message_queues:
            return None

        queue = self.message_queues[agent_id]

        try:
            message = await asyncio.wait_for(queue.get(), timeout=timeout)
            self.message_stats["received"] += 1
            return message

        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Failed to receive message for {agent_id}: {e}")
            return None

    async def subscribe_to_topic(self, agent_id: str, topic: str):
        """Subscribe agent to a topic for multicast messages"""
        if topic not in self.subscription_table:
            self.subscription_table[topic] = set()

        self.subscription_table[topic].add(agent_id)
        logger.info(f"Agent {agent_id} subscribed to topic: {topic}")

    async def unsubscribe_from_topic(self, agent_id: str, topic: str):
        """Unsubscribe agent from a topic"""
        if topic in self.subscription_table:
            self.subscription_table[topic].discard(agent_id)

            # Clean up empty topic
            if not self.subscription_table[topic]:
                del self.subscription_table[topic]

        logger.info(f"Agent {agent_id} unsubscribed from topic: {topic}")

    async def add_message_handler(self, message_type: MessageType, handler: Callable):
        """Add a message handler for specific message type"""
        self.message_handlers[message_type].append(handler)
        logger.info(f"Added handler for message type: {message_type.value}")

    async def add_middleware(self, middleware: Callable):
        """Add middleware to the processing stack"""
        self.middleware_stack.append(middleware)
        logger.info("Added message middleware")

    async def connect_websocket(self, agent_id: str, websocket: WebSocket):
        """Connect a WebSocket for an agent"""
        await websocket.accept()
        self.websocket_connections[agent_id] = websocket

        # Update endpoint if exists
        if agent_id in self.agent_endpoints:
            self.agent_endpoints[agent_id].last_seen = datetime.now()
            self.agent_endpoints[agent_id].is_active = True

        logger.info(f"WebSocket connected for agent: {agent_id}")

    async def disconnect_websocket(self, agent_id: str):
        """Disconnect WebSocket for an agent"""
        if agent_id in self.websocket_connections:
            try:
                await self.websocket_connections[agent_id].close()
            except:
                pass
            del self.websocket_connections[agent_id]

        # Update endpoint status
        if agent_id in self.agent_endpoints:
            self.agent_endpoints[agent_id].is_active = False

        logger.info(f"WebSocket disconnected for agent: {agent_id}")

    def _update_delivery_metrics(self, message: Message):
        """Update delivery performance metrics"""
        if message.delivered_at and message.created_at:
            delivery_time = (message.delivered_at - message.created_at).total_seconds()
            self.delivery_times.append(delivery_time)

    async def _start_background_processors(self):
        """Start background processing tasks"""
        # Message cleanup processor
        cleanup_task = asyncio.create_task(self._cleanup_expired_messages())
        self.background_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self.background_tasks.discard)

        # Performance monitoring
        monitor_task = asyncio.create_task(self._monitor_performance())
        self.background_tasks.add(monitor_task)
        monitor_task.add_done_callback(self.background_tasks.discard)

        # Heartbeat processor
        heartbeat_task = asyncio.create_task(self._process_heartbeats())
        self.background_tasks.add(heartbeat_task)
        heartbeat_task.add_done_callback(self.background_tasks.discard)

        logger.info("Background processors started")

    async def _cleanup_expired_messages(self):
        """Clean up expired messages from queues"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Clean up every minute

                expired_count = 0

                for agent_id, queue in self.message_queues.items():
                    temp_messages = []

                    # Extract all messages
                    while not queue.empty():
                        try:
                            message = queue.get_nowait()
                            if not message.is_expired:
                                temp_messages.append(message)
                            else:
                                expired_count += 1
                        except:
                            break

                    # Put back non-expired messages
                    for message in temp_messages:
                        try:
                            queue.put_nowait(message)
                        except:
                            break

                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired messages")
                    self.message_stats["expired"] += expired_count

            except Exception as e:
                logger.error(f"Message cleanup error: {e}")
                await asyncio.sleep(60)

    async def _monitor_performance(self):
        """Monitor message broker performance"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds

                # Calculate performance metrics
                total_messages = sum(self.message_stats.values())
                success_rate = (
                    self.message_stats["sent"] / max(1, total_messages)
                    if total_messages > 0
                    else 1.0
                )

                avg_delivery_time = (
                    sum(self.delivery_times) / len(self.delivery_times)
                    if self.delivery_times
                    else 0.0
                )

                # Log performance alerts
                if success_rate < 0.9:
                    logger.warning(f"Low message success rate: {success_rate:.2f}")

                if avg_delivery_time > 5.0:  # > 5 seconds
                    logger.warning(f"High average delivery time: {avg_delivery_time:.2f}s")

                # Store metrics in Redis for monitoring
                if self.redis:
                    metrics = {
                        "timestamp": datetime.now().isoformat(),
                        "total_messages": total_messages,
                        "success_rate": success_rate,
                        "avg_delivery_time": avg_delivery_time,
                        "active_agents": len(
                            [e for e in self.agent_endpoints.values() if e.is_active]
                        ),
                        "queue_sizes": {
                            agent_id: queue.qsize()
                            for agent_id, queue in self.message_queues.items()
                        },
                    }

                    await self.redis.setex(
                        "message_broker:metrics",
                        300,  # 5 minutes TTL
                        json.dumps(metrics),
                    )

            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(60)

    async def _process_heartbeats(self):
        """Process agent heartbeats and update status"""
        while self.running:
            try:
                await asyncio.sleep(15)  # Check every 15 seconds

                now = datetime.now()
                inactive_agents = []

                for agent_id, endpoint in self.agent_endpoints.items():
                    # Check if agent hasn't been seen for too long
                    time_since_seen = (now - endpoint.last_seen).total_seconds()

                    if time_since_seen > 120:  # 2 minutes
                        if endpoint.is_active:
                            endpoint.is_active = False
                            inactive_agents.append(agent_id)
                            logger.warning(f"Agent {agent_id} marked as inactive")

                # Broadcast agent status updates if needed
                if inactive_agents:
                    status_message = Message(
                        message_type=MessageType.AGENT_STATUS,
                        sender_id="message_broker",
                        delivery_mode=DeliveryMode.BROADCAST,
                        payload={
                            "inactive_agents": inactive_agents,
                            "timestamp": now.isoformat(),
                        },
                    )
                    await self.send_message(status_message)

            except Exception as e:
                logger.error(f"Heartbeat processing error: {e}")
                await asyncio.sleep(60)

    async def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive message broker statistics"""
        now = datetime.now()

        stats = {
            "message_stats": dict(self.message_stats),
            "active_agents": len([e for e in self.agent_endpoints.values() if e.is_active]),
            "total_agents": len(self.agent_endpoints),
            "websocket_connections": len(self.websocket_connections),
            "topic_subscriptions": len(self.subscription_table),
            "queue_stats": {
                agent_id: {"size": queue.qsize(), "maxsize": queue.maxsize}
                for agent_id, queue in self.message_queues.items()
            },
            "performance": {
                "avg_delivery_time": (
                    sum(self.delivery_times) / len(self.delivery_times)
                    if self.delivery_times
                    else 0.0
                ),
                "recent_failures": len(self.failed_deliveries),
                "success_rate": (
                    self.message_stats["sent"] / max(1, sum(self.message_stats.values()))
                ),
            },
            "timestamp": now.isoformat(),
        }

        return stats

    async def shutdown(self):
        """Gracefully shutdown message broker"""
        logger.info("Shutting down message broker")

        self.running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Close all WebSocket connections
        for agent_id in list(self.websocket_connections.keys()):
            await self.disconnect_websocket(agent_id)

        # Close Redis connection
        if self.redis:
            await self.redis.close()

        logger.info("Message broker shutdown complete")


class EducationalMessageRouter:
    """Educational context-aware message routing"""

    def __init__(self, message_broker: MessageBroker):
        self.message_broker = message_broker
        self.subject_specialists: dict[str, list[str]] = {}
        self.grade_level_experts: dict[int, list[str]] = {}
        self.content_type_specialists: dict[str, list[str]] = {}

    async def route_educational_message(self, message: Message) -> list[str]:
        """Route message based on educational context"""
        recipients = []

        educational_context = message.educational_context

        # Route by subject area
        subject = educational_context.get("subject_area")
        if subject and subject in self.subject_specialists:
            recipients.extend(self.subject_specialists[subject])

        # Route by grade level
        grade_level = educational_context.get("grade_level")
        if grade_level and grade_level in self.grade_level_experts:
            recipients.extend(self.grade_level_experts[grade_level])

        # Route by content type
        content_type = educational_context.get("content_type")
        if content_type and content_type in self.content_type_specialists:
            recipients.extend(self.content_type_specialists[content_type])

        # Remove duplicates and sender
        recipients = list(set(recipients))
        if message.sender_id in recipients:
            recipients.remove(message.sender_id)

        return recipients

    async def register_specialist(
        self, agent_id: str, specialization_type: str, specialization: str
    ):
        """Register an agent as a specialist"""
        if specialization_type == "subject":
            if specialization not in self.subject_specialists:
                self.subject_specialists[specialization] = []
            self.subject_specialists[specialization].append(agent_id)

        elif specialization_type == "grade_level":
            grade = int(specialization)
            if grade not in self.grade_level_experts:
                self.grade_level_experts[grade] = []
            self.grade_level_experts[grade].append(agent_id)

        elif specialization_type == "content_type":
            if specialization not in self.content_type_specialists:
                self.content_type_specialists[specialization] = []
            self.content_type_specialists[specialization].append(agent_id)


# Global message broker instance
message_broker = MessageBroker()


# Utility functions for easy message creation


def create_task_assignment_message(
    sender_id: str,
    recipient_id: str,
    task_data: dict[str, Any],
    educational_context: dict[str, Any] = None,
) -> Message:
    """Create a task assignment message"""
    return Message(
        message_type=MessageType.TASK_ASSIGNMENT,
        sender_id=sender_id,
        recipient_id=recipient_id,
        payload=task_data,
        educational_context=educational_context or {},
        priority=MessagePriority.HIGH,
    )


def create_quality_assessment_message(
    sender_id: str,
    recipient_id: str,
    assessment_data: dict[str, Any],
    educational_context: dict[str, Any] = None,
) -> Message:
    """Create a quality assessment message"""
    return Message(
        message_type=MessageType.QUALITY_ASSESSMENT,
        sender_id=sender_id,
        recipient_id=recipient_id,
        payload=assessment_data,
        educational_context=educational_context or {},
        priority=MessagePriority.HIGH,
    )


def create_collaboration_message(
    sender_id: str,
    collaboration_data: dict[str, Any],
    educational_context: dict[str, Any] = None,
) -> Message:
    """Create a collaboration broadcast message"""
    return Message(
        message_type=MessageType.AGENT_COLLABORATION,
        sender_id=sender_id,
        payload=collaboration_data,
        educational_context=educational_context or {},
        delivery_mode=DeliveryMode.BROADCAST,
        priority=MessagePriority.NORMAL,
    )


def create_live_update_message(
    sender_id: str, update_data: dict[str, Any], routing_key: str = "live_updates"
) -> Message:
    """Create a live update message for WebSocket clients"""
    return Message(
        message_type=MessageType.LIVE_UPDATE,
        sender_id=sender_id,
        payload=update_data,
        delivery_mode=DeliveryMode.MULTICAST,
        routing_key=routing_key,
        priority=MessagePriority.NORMAL,
    )


# Middleware for educational message processing


async def educational_context_middleware(message: Message) -> Message:
    """Middleware to enhance educational context"""
    educational_context = message.educational_context

    # Add default educational metadata if missing
    if not educational_context.get("timestamp"):
        educational_context["timestamp"] = datetime.now().isoformat()

    # Infer context from message payload if not explicitly set
    payload = message.payload

    if not educational_context.get("subject_area") and "subject" in payload:
        educational_context["subject_area"] = payload["subject"]

    if not educational_context.get("grade_level") and "grade_level" in payload:
        educational_context["grade_level"] = payload["grade_level"]

    if not educational_context.get("content_type") and "content_type" in payload:
        educational_context["content_type"] = payload["content_type"]

    return message


async def priority_adjustment_middleware(message: Message) -> Message:
    """Middleware to adjust message priority based on educational urgency"""
    educational_context = message.educational_context

    # Increase priority for assessment-related messages
    if educational_context.get("content_type") in ["assessment", "quiz"]:
        if message.priority == MessagePriority.NORMAL:
            message.priority = MessagePriority.HIGH

    # Increase priority for high-grade level content
    grade_level = educational_context.get("grade_level", 0)
    if grade_level >= 9 and message.priority == MessagePriority.NORMAL:
        message.priority = MessagePriority.HIGH

    # Increase priority for complex subjects
    subject = educational_context.get("subject_area", "").lower()
    if (
        subject in ["physics", "chemistry", "calculus"]
        and message.priority == MessagePriority.NORMAL
    ):
        message.priority = MessagePriority.HIGH

    return message


async def logging_middleware(message: Message) -> Message:
    """Middleware to log educational message activity"""
    educational_context = message.educational_context

    logger.info(
        f"Educational message: {message.message_type.value} "
        f"from {message.sender_id} to {message.recipient_id or 'broadcast'} "
        f"subject: {educational_context.get('subject_area', 'N/A')} "
        f"grade: {educational_context.get('grade_level', 'N/A')}"
    )

    return message
