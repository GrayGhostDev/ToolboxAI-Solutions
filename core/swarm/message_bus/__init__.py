"""Message Bus Architecture for Agent Communication

Provides event-driven messaging infrastructure for the agent swarm,
enabling asynchronous communication, event routing, and state synchronization.
"""

from .message_bus import MessageBus, MessageBusConfig
from .event_types import EventType, EventPriority, EventCategory
from .agent_message import AgentMessage, MessageStatus, MessagePattern
from .pubsub_manager import PubSubManager, Subscription, Topic
from .event_router import EventRouter, RoutingRule

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

    # Pub/Sub
    "PubSubManager",
    "Subscription",
    "Topic",

    # Routing
    "EventRouter",
    "RoutingRule",
]