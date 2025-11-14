"""Message Bus Architecture for Agent Communication

Provides event-driven messaging infrastructure for the agent swarm,
enabling asynchronous communication, event routing, and state synchronization.
"""

from .agent_message import AgentMessage, MessageBuilder, MessagePattern, MessageStatus
from .event_types import EventCategory, EventPriority, EventType
from .message_bus import MessageBus, MessageBusConfig

__all__ = [
    # Core message bus
    "MessageBus",
    "MessageBusConfig",
    # Event system
    "EventType",
    "EventPriority",
    "EventCategory",
    # Messaging
    "AgentMessage",
    "MessageStatus",
    "MessagePattern",
    "MessageBuilder",
]
