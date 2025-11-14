"""Message Bus Core Implementation

Provides event-driven messaging infrastructure for agent communication.
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Optional

from .agent_message import AgentMessage, MessageStatus
from .event_types import EventType


@dataclass
class MessageBusConfig:
    """Configuration for message bus."""

    max_queue_size: int = 1000
    processing_timeout: int = 30
    retry_attempts: int = 3
    enable_logging: bool = True


class MessageBus:
    """
    Core message bus for agent communication.

    Handles message routing, queuing, and delivery between agents.
    """

    def __init__(self, config: Optional[MessageBusConfig] = None):
        """Initialize message bus."""
        self.config = config or MessageBusConfig()
        self.logger = logging.getLogger(__name__)

        # Message queues by topic
        self.queues: dict[str, asyncio.Queue] = {}

        # Subscribers by event type
        self.subscribers: dict[EventType, list[Callable]] = defaultdict(list)

        # Message history
        self.message_history: list[AgentMessage] = []

        # Statistics
        self.stats = {"messages_sent": 0, "messages_received": 0, "messages_failed": 0}

    async def publish(self, message: AgentMessage) -> bool:
        """
        Publish a message to the bus.

        Args:
            message: The message to publish

        Returns:
            True if published successfully
        """
        try:
            # Update message status
            message.status = MessageStatus.SENT

            # Get subscribers for this event type
            event_type = message.metadata.get("event_type")
            if event_type and event_type in self.subscribers:
                for subscriber in self.subscribers[event_type]:
                    try:
                        await subscriber(message)
                    except Exception as e:
                        self.logger.error(f"Subscriber error: {e}")

            # Add to history
            if self.config.enable_logging:
                self.message_history.append(message)
                if len(self.message_history) > 1000:
                    self.message_history = self.message_history[-500:]

            # Update stats
            self.stats["messages_sent"] += 1

            return True

        except Exception as e:
            self.logger.error(f"Failed to publish message: {e}")
            self.stats["messages_failed"] += 1
            return False

    async def subscribe(self, event_type: EventType, handler: Callable) -> bool:
        """
        Subscribe to an event type.

        Args:
            event_type: The event type to subscribe to
            handler: Async function to handle messages

        Returns:
            True if subscribed successfully
        """
        try:
            self.subscribers[event_type].append(handler)
            self.logger.info(f"Subscribed to {event_type}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to subscribe: {e}")
            return False

    async def unsubscribe(self, event_type: EventType, handler: Callable) -> bool:
        """
        Unsubscribe from an event type.

        Args:
            event_type: The event type to unsubscribe from
            handler: The handler to remove

        Returns:
            True if unsubscribed successfully
        """
        try:
            if handler in self.subscribers[event_type]:
                self.subscribers[event_type].remove(handler)
                self.logger.info(f"Unsubscribed from {event_type}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get message bus statistics."""
        return {
            **self.stats,
            "active_subscriptions": sum(len(handlers) for handlers in self.subscribers.values()),
            "queued_messages": sum(q.qsize() for q in self.queues.values()),
            "history_size": len(self.message_history),
        }

    def clear_history(self):
        """Clear message history."""
        self.message_history.clear()
