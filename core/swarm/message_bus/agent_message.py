"""Agent Message Definition for Swarm Communication

Defines the structure and patterns for messages exchanged between agents
in the swarm, including request-response, broadcast, and streaming patterns.
"""

import asyncio
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from .event_types import EventMetadata, EventPriority, EventType


class MessageStatus(Enum):
    """Status of a message in its lifecycle."""

    CREATED = "created"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class MessagePattern(Enum):
    """Communication patterns for agent messages."""

    REQUEST_RESPONSE = "request_response"  # Synchronous request-response
    PUBLISH_SUBSCRIBE = "publish_subscribe"  # Pub/sub pattern
    BROADCAST = "broadcast"  # One-to-many broadcast
    UNICAST = "unicast"  # Direct one-to-one
    MULTICAST = "multicast"  # One-to-specific-group
    STREAMING = "streaming"  # Continuous stream
    WORKFLOW = "workflow"  # Multi-step workflow
    CONSENSUS = "consensus"  # Consensus gathering


@dataclass
class MessageHeader:
    """Header information for agent messages."""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    reply_to: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None  # Time to live in seconds
    priority: EventPriority = EventPriority.NORMAL
    pattern: MessagePattern = MessagePattern.REQUEST_RESPONSE
    version: str = "1.0"

    # Routing information
    source_agent: Optional[str] = None
    target_agent: Optional[str] = None
    target_group: Optional[list[str]] = None
    topic: Optional[str] = None

    # Tracing
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None

    # Security
    auth_token: Optional[str] = None
    encrypted: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert header to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["priority"] = self.priority.value
        data["pattern"] = self.pattern.value
        return data


@dataclass
class MessagePayload:
    """Payload container for agent messages."""

    event_type: EventType
    data: dict[str, Any]
    metadata: Optional[EventMetadata] = None
    attachments: list[dict[str, Any]] = field(default_factory=list)
    encoding: str = "json"
    compressed: bool = False
    checksum: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary."""
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "metadata": asdict(self.metadata) if self.metadata else None,
            "attachments": self.attachments,
            "encoding": self.encoding,
            "compressed": self.compressed,
            "checksum": self.checksum,
        }

    def validate_checksum(self) -> bool:
        """Validate payload checksum if present."""
        if not self.checksum:
            return True

        # Calculate checksum of data
        import hashlib

        data_str = json.dumps(self.data, sort_keys=True)
        calculated = hashlib.sha256(data_str.encode()).hexdigest()
        return calculated == self.checksum


@dataclass
class AgentMessage:
    """
    Complete message structure for agent communication.

    This is the primary message format used throughout the swarm for
    all agent-to-agent and agent-to-system communication.
    """

    header: MessageHeader
    payload: MessagePayload
    status: MessageStatus = MessageStatus.CREATED
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Tracking
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Response handling
    response_handler: Optional[Callable] = field(default=None, compare=False)
    error_handler: Optional[Callable] = field(default=None, compare=False)
    timeout_handler: Optional[Callable] = field(default=None, compare=False)

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary format for serialization."""
        return {
            "header": self.header.to_dict(),
            "payload": self.payload.to_dict(),
            "status": self.status.value,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary."""
        # Parse header
        header_data = data.get("header", {})
        header = MessageHeader(
            message_id=header_data.get("message_id"),
            correlation_id=header_data.get("correlation_id"),
            priority=EventPriority(header_data.get("priority", 3)),
            pattern=MessagePattern(header_data.get("pattern", "request_response")),
            source_agent=header_data.get("source_agent"),
            target_agent=header_data.get("target_agent"),
        )

        # Parse payload
        payload_data = data.get("payload", {})
        payload = MessagePayload(
            event_type=EventType(payload_data.get("event_type")),
            data=payload_data.get("data", {}),
            attachments=payload_data.get("attachments", []),
        )

        # Create message
        return cls(
            header=header,
            payload=payload,
            status=MessageStatus(data.get("status", "created")),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
        )

    def to_json(self) -> str:
        """Serialize message to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "AgentMessage":
        """Deserialize message from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def is_expired(self) -> bool:
        """Check if message has expired based on TTL."""
        if not self.header.ttl:
            return False

        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.header.ttl

    def should_retry(self) -> bool:
        """Check if message should be retried on failure."""
        return self.retry_count < self.max_retries

    def increment_retry(self):
        """Increment retry counter."""
        self.retry_count += 1

    def mark_sent(self):
        """Mark message as sent."""
        self.status = MessageStatus.SENT
        self.sent_at = datetime.now()

    def mark_delivered(self):
        """Mark message as delivered."""
        self.status = MessageStatus.DELIVERED
        self.delivered_at = datetime.now()

    def mark_completed(self, result: Optional[Any] = None):
        """Mark message as completed."""
        self.status = MessageStatus.COMPLETED
        self.completed_at = datetime.now()
        if result and self.response_handler:
            self.response_handler(result)

    def mark_failed(self, error: str):
        """Mark message as failed."""
        self.status = MessageStatus.FAILED
        self.error = error
        if self.error_handler:
            self.error_handler(error)

    async def wait_for_completion(self, timeout: float = 30.0) -> bool:
        """
        Wait for message to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if completed, False if timeout
        """
        start_time = asyncio.get_event_loop().time()

        while self.status not in [
            MessageStatus.COMPLETED,
            MessageStatus.FAILED,
            MessageStatus.CANCELLED,
        ]:
            if asyncio.get_event_loop().time() - start_time > timeout:
                if self.timeout_handler:
                    self.timeout_handler()
                return False

            await asyncio.sleep(0.1)

        return self.status == MessageStatus.COMPLETED


class MessageBuilder:
    """Builder pattern for constructing agent messages."""

    def __init__(self):
        """Initialize message builder."""
        self._header = MessageHeader()
        self._payload_data = {}
        self._event_type = None
        self._attachments = []
        self._metadata = None

    def with_event(self, event_type: EventType) -> "MessageBuilder":
        """Set event type."""
        self._event_type = event_type
        return self

    def with_data(self, data: dict[str, Any]) -> "MessageBuilder":
        """Set payload data."""
        self._payload_data = data
        return self

    def from_agent(self, agent_id: str) -> "MessageBuilder":
        """Set source agent."""
        self._header.source_agent = agent_id
        return self

    def to_agent(self, agent_id: str) -> "MessageBuilder":
        """Set target agent."""
        self._header.target_agent = agent_id
        self._header.pattern = MessagePattern.UNICAST
        return self

    def to_agents(self, agent_ids: list[str]) -> "MessageBuilder":
        """Set multiple target agents."""
        self._header.target_group = agent_ids
        self._header.pattern = MessagePattern.MULTICAST
        return self

    def broadcast(self) -> "MessageBuilder":
        """Set as broadcast message."""
        self._header.pattern = MessagePattern.BROADCAST
        return self

    def with_priority(self, priority: EventPriority) -> "MessageBuilder":
        """Set message priority."""
        self._header.priority = priority
        return self

    def with_correlation(self, correlation_id: str) -> "MessageBuilder":
        """Set correlation ID."""
        self._header.correlation_id = correlation_id
        return self

    def reply_to(self, message: AgentMessage) -> "MessageBuilder":
        """Configure as reply to another message."""
        self._header.correlation_id = message.header.message_id
        self._header.causation_id = message.header.message_id
        self._header.reply_to = message.header.source_agent
        self._header.target_agent = message.header.source_agent
        return self

    def with_ttl(self, seconds: int) -> "MessageBuilder":
        """Set time to live."""
        self._header.ttl = seconds
        return self

    def with_attachment(
        self, name: str, data: Any, mime_type: str = "application/octet-stream"
    ) -> "MessageBuilder":
        """Add attachment."""
        self._attachments.append(
            {"name": name, "data": data, "mime_type": mime_type, "size": len(str(data))}
        )
        return self

    def with_metadata(self, metadata: EventMetadata) -> "MessageBuilder":
        """Set event metadata."""
        self._metadata = metadata
        return self

    def build(self) -> AgentMessage:
        """Build the message."""
        if not self._event_type:
            raise ValueError("Event type is required")

        payload = MessagePayload(
            event_type=self._event_type,
            data=self._payload_data,
            metadata=self._metadata,
            attachments=self._attachments,
        )

        return AgentMessage(header=self._header, payload=payload)


def create_request(event_type: EventType, data: dict[str, Any], **kwargs) -> AgentMessage:
    """Helper function to create a request message."""
    builder = MessageBuilder()
    builder.with_event(event_type).with_data(data)

    for key, value in kwargs.items():
        if key == "from_agent":
            builder.from_agent(value)
        elif key == "to_agent":
            builder.to_agent(value)
        elif key == "priority":
            builder.with_priority(value)
        elif key == "correlation_id":
            builder.with_correlation(value)
        elif key == "ttl":
            builder.with_ttl(value)

    return builder.build()


def create_response(
    request: AgentMessage, data: dict[str, Any], success: bool = True
) -> AgentMessage:
    """Helper function to create a response message."""
    event_type = EventType.AGENT_RESPONSE if success else EventType.AGENT_ERROR

    return MessageBuilder().with_event(event_type).with_data(data).reply_to(request).build()


def create_broadcast(event_type: EventType, data: dict[str, Any], **kwargs) -> AgentMessage:
    """Helper function to create a broadcast message."""
    return (
        MessageBuilder()
        .with_event(event_type)
        .with_data(data)
        .broadcast()
        .with_priority(kwargs.get("priority", EventPriority.NORMAL))
        .from_agent(kwargs.get("from_agent", "system"))
        .build()
    )
