"""
Pusher Channels integration helpers for FastAPI backend.

- Initializes a Pusher client from environment (via settings)
- Provides auth signature generation for Channels subscription
- Provides helper to trigger events and verify webhooks
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

try:
    import pusher  # type: ignore
except Exception:  # pragma: no cover-optional import in some environments
    pusher = None  # type: ignore

from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class PusherUnavailable(Exception):
    pass


# Agent-specific Pusher channels and events
AGENT_CHANNELS = {
    "agent_status": "agent-status",
    "agent_tasks": "agent-tasks",
    "agent_metrics": "agent-metrics",
    "system_health": "system-health",
    "agent_updates": "agent-updates",
}

AGENT_EVENTS = {
    "agent_started": "agent.started",
    "agent_stopped": "agent.stopped",
    "agent_idle": "agent.idle",
    "agent_busy": "agent.busy",
    "agent_error": "agent.error",
    "task_created": "task.created",
    "task_started": "task.started",
    "task_completed": "task.completed",
    "task_failed": "task.failed",
    "metrics_updated": "metrics.updated",
    "health_updated": "health.updated",
}


def _ensure_pusher_available():
    if pusher is None:
        raise PusherUnavailable("The 'pusher' package is not installed. Run: pip install pusher")
    if not (
        settings.PUSHER_ENABLED
        and settings.PUSHER_APP_ID
        and settings.PUSHER_KEY
        and settings.PUSHER_SECRET
    ):
        raise PusherUnavailable(
            "Pusher configuration missing. Ensure PUSHER_ENABLED, PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET, PUSHER_CLUSTER are set."
        )


class PusherService:
    """
    Pusher service class for managing Pusher client and operations.
    Provides an object-oriented interface to Pusher functionality.
    """

    def __init__(self, app_id: str, key: str, secret: str, cluster: str = "us2", ssl: bool = True):
        """Initialize Pusher service with configuration."""
        self.app_id = app_id
        self.key = key
        self.secret = secret
        self.cluster = cluster
        self.ssl = ssl

        # Initialize client if pusher is available
        if pusher is not None:
            try:
                self.client = pusher.Pusher(  # type: ignore[attr-defined]
                    app_id=app_id,
                    key=key,
                    secret=secret,
                    cluster=cluster,
                    ssl=ssl,
                )
            except (ValueError, TypeError) as e:
                # Handle case where we're in test mode or have invalid credentials
                logger.warning(f"Failed to initialize Pusher client: {e}")
                self.client = None
        else:
            self.client = None

    def _ensure_client_available(self):
        """Ensure the Pusher client is available."""
        if self.client is None:
            raise PusherUnavailable(
                "Pusher client not initialized. Check pusher package installation and configuration."
            )

    def trigger(self, channel: str, event: str, data: dict[str, Any]) -> dict[str, Any]:
        """Trigger an event on a channel."""
        self._ensure_client_available()

        # Custom JSON encoder to handle datetime objects
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)

        # Ensure data is properly serialized to avoid UTF-16 surrogate pair issues
        try:
            # Convert data to JSON string with datetime handling, then back to dict
            # This ensures all non-serializable objects are converted
            json_str = json.dumps(data, cls=DateTimeEncoder, ensure_ascii=False)
            serializable_data = json.loads(json_str)
            self.client.trigger(channel, event, serializable_data)
        except (TypeError, ValueError, UnicodeEncodeError) as e:
            logger.error(f"JSON encoding error in pusher trigger: {e}")
            # Create a safe fallback payload
            safe_data = {
                "error": "Data encoding error",
                "original_type": type(data).__name__,
                "timestamp": str(datetime.now()),
            }
            self.client.trigger(channel, event, safe_data)

        return {"channel": channel, "event": event}

    def trigger_batch(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        """Trigger multiple events at once."""
        self._ensure_client_available()
        self.client.trigger_batch(events)
        return {"status": "success", "events_count": len(events)}

    def authenticate(
        self, channel: str, socket_id: str, user_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Authenticate a channel subscription."""
        self._ensure_client_available()

        if channel.startswith("presence-") and user_data:
            return self.client.authenticate(
                channel=channel,
                socket_id=socket_id,
                custom_data=user_data,
            )
        else:
            return self.client.authenticate(channel=channel, socket_id=socket_id)

    def channels_info(
        self, prefix_filter: str | None = None, attributes: list[str] | None = None
    ) -> dict[str, Any]:
        """Get information about all channels."""
        self._ensure_client_available()

        kwargs = {}
        if prefix_filter:
            kwargs["prefix_filter"] = prefix_filter
        if attributes:
            kwargs["info"] = ",".join(attributes)

        return self.client.channels_info(**kwargs)

    def channel_info(self, channel: str, attributes: list[str] | None = None) -> dict[str, Any]:
        """Get information about a specific channel."""
        self._ensure_client_available()

        if attributes:
            return self.client.channel_info(channel, info=",".join(attributes))
        else:
            return self.client.channel_info(channel)

    def users_info(self, channel: str) -> dict[str, Any]:
        """Get users information for a presence channel."""
        self._ensure_client_available()
        return self.client.users_info(channel)

    def validate_webhook(self, key: str, signature: str, body: str) -> bool:
        """Validate a webhook signature."""
        self._ensure_client_available()
        return self.client.validate_webhook(key, signature, body)

    async def async_trigger(self, channel: str, event: str, data: dict[str, Any]) -> dict[str, Any]:
        """Async version of trigger for compatibility with async tests."""
        return self.trigger(channel, event, data)


def get_pusher_service() -> PusherService:
    """Return configured PusherService instance using settings."""
    _ensure_pusher_available()
    return PusherService(
        app_id=settings.PUSHER_APP_ID,
        key=settings.PUSHER_KEY,
        secret=settings.PUSHER_SECRET,
        cluster=settings.PUSHER_CLUSTER,
        ssl=settings.PUSHER_SSL,
    )


def get_pusher_client():
    """Return configured Pusher client instance."""
    _ensure_pusher_available()
    client = pusher.Pusher(  # type: ignore[attr-defined]
        app_id=settings.PUSHER_APP_ID,
        key=settings.PUSHER_KEY,
        secret=settings.PUSHER_SECRET,
        cluster=settings.PUSHER_CLUSTER,
        ssl=True,
    )
    return client


def trigger_event(channel: str, event: str, data: dict[str, Any]) -> dict[str, Any]:
    client = get_pusher_client()

    # Custom JSON encoder to handle datetime objects
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    # Ensure data is properly serialized to avoid UTF-16 surrogate pair issues
    try:
        # Convert data to JSON string with datetime handling, then back to dict
        # This ensures all non-serializable objects are converted
        json_str = json.dumps(data, cls=DateTimeEncoder, ensure_ascii=False)
        serializable_data = json.loads(json_str)
        client.trigger(channel, event, serializable_data)
    except (TypeError, ValueError, UnicodeEncodeError) as e:
        logger.error(f"JSON encoding error in pusher trigger: {e}")
        # Create a safe fallback payload
        safe_data = {
            "error": "Data encoding error",
            "original_type": type(data).__name__,
            "timestamp": str(datetime.now()),
        }
        client.trigger(channel, event, safe_data)
    return {"channel": channel, "event": event}


def authenticate_channel(
    socket_id: str,
    channel_name: str,
    user_id: str | None = None,
    user_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return auth payload for private/presence channels."""
    client = get_pusher_client()
    if channel_name.startswith("presence-") and user_id:
        auth = client.authenticate(
            channel=channel_name,
            socket_id=socket_id,
            custom_data={
                "user_id": user_id,
                "user_info": user_info or {},
            },
        )
    else:
        auth = client.authenticate(channel=channel_name, socket_id=socket_id)
    return auth


def verify_webhook(headers: dict[str, str], body: bytes) -> dict[str, Any] | None:
    """Verify webhook signature and return parsed events if valid."""
    _ensure_pusher_available()
    webhook = pusher.Webhook(  # type: ignore[attr-defined]
        key=settings.PUSHER_KEY,
        secret=settings.PUSHER_SECRET,
    )
    try:
        return webhook.validate(body, headers)
    except Exception as e:
        logger.warning(f"Invalid Pusher webhook: {e}")
        return None


# Agent-specific Pusher helper functions


async def trigger_agent_event(
    event_type: str, agent_id: str, data: dict[str, Any], user_id: str | None = None
) -> None:
    """
    Trigger an agent-specific event via Pusher.

    Args:
        event_type: Type of event (from AGENT_EVENTS)
        agent_id: ID of the agent
        data: Event data
        user_id: Optional user ID for user-specific events
    """
    try:
        event_name = AGENT_EVENTS.get(event_type, event_type)

        # Prepare event data
        event_data = {
            "agent_id": agent_id,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }

        if user_id:
            event_data["user_id"] = user_id

        # Trigger on agent-updates channel
        trigger_event(AGENT_CHANNELS["agent_updates"], event_name, event_data)

        # Also trigger on agent-specific channel
        agent_channel = f"agent-{agent_id}"
        trigger_event(agent_channel, event_name, event_data)

        logger.debug(f"Triggered agent event: {event_name} for agent {agent_id}")

    except Exception as e:
        logger.error(f"Error triggering agent event: {e}")


async def trigger_task_event(
    event_type: str,
    task_id: str,
    agent_id: str,
    data: dict[str, Any],
    user_id: str | None = None,
) -> None:
    """
    Trigger a task-specific event via Pusher.

    Args:
        event_type: Type of event (task_created, task_started, task_completed, task_failed)
        task_id: ID of the task
        agent_id: ID of the agent handling the task
        data: Event data
        user_id: Optional user ID for user-specific events
    """
    try:
        event_name = AGENT_EVENTS.get(event_type, event_type)

        # Prepare event data
        event_data = {
            "task_id": task_id,
            "agent_id": agent_id,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }

        if user_id:
            event_data["user_id"] = user_id

        # Trigger on agent-tasks channel
        trigger_event(AGENT_CHANNELS["agent_tasks"], event_name, event_data)

        # Also trigger on agent-specific channel
        agent_channel = f"agent-{agent_id}"
        trigger_event(agent_channel, event_name, event_data)

        # If user-specific, also trigger on user channel
        if user_id:
            user_channel = f"user-{user_id}"
            trigger_event(user_channel, event_name, event_data)

        logger.debug(f"Triggered task event: {event_name} for task {task_id}")

    except Exception as e:
        logger.error(f"Error triggering task event: {e}")


async def trigger_metrics_update(metrics_data: dict[str, Any], agent_id: str | None = None) -> None:
    """
    Trigger metrics update event via Pusher.

    Args:
        metrics_data: Metrics data to broadcast
        agent_id: Optional specific agent ID
    """
    try:
        event_data = {"timestamp": datetime.now().isoformat(), "metrics": metrics_data}

        if agent_id:
            event_data["agent_id"] = agent_id

        # Trigger on agent-metrics channel
        trigger_event(AGENT_CHANNELS["agent_metrics"], AGENT_EVENTS["metrics_updated"], event_data)

        # If agent-specific, also trigger on agent channel
        if agent_id:
            agent_channel = f"agent-{agent_id}"
            trigger_event(agent_channel, AGENT_EVENTS["metrics_updated"], event_data)

        logger.debug(f"Triggered metrics update for agent {agent_id or 'system'}")

    except Exception as e:
        logger.error(f"Error triggering metrics update: {e}")


async def trigger_health_update(health_data: dict[str, Any]) -> None:
    """
    Trigger system health update event via Pusher.

    Args:
        health_data: System health data to broadcast
    """
    try:
        event_data = {"timestamp": datetime.now().isoformat(), "health": health_data}

        # Trigger on system-health channel
        trigger_event(AGENT_CHANNELS["system_health"], AGENT_EVENTS["health_updated"], event_data)

        logger.debug("Triggered system health update")

    except Exception as e:
        logger.error(f"Error triggering health update: {e}")


async def trigger_agent_status_change(
    agent_id: str,
    old_status: str,
    new_status: str,
    additional_data: dict[str, Any] | None = None,
) -> None:
    """
    Trigger agent status change event via Pusher.

    Args:
        agent_id: ID of the agent
        old_status: Previous status
        new_status: New status
        additional_data: Additional data to include
    """
    try:
        event_data = {
            "agent_id": agent_id,
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.now().isoformat(),
        }

        if additional_data:
            event_data.update(additional_data)

        # Map status to event type
        status_event_map = {
            "idle": "agent_idle",
            "busy": "agent_busy",
            "error": "agent_error",
            "offline": "agent_stopped",
        }

        event_type = status_event_map.get(new_status, "agent_idle")
        await trigger_agent_event(event_type, agent_id, event_data)

        logger.debug(f"Triggered status change for agent {agent_id}: {old_status} -> {new_status}")

    except Exception as e:
        logger.error(f"Error triggering agent status change: {e}")


def get_agent_channels() -> dict[str, str]:
    """Get available agent channels."""
    return AGENT_CHANNELS.copy()


def get_agent_events() -> dict[str, str]:
    """Get available agent events."""
    return AGENT_EVENTS.copy()


# Export for compatibility with legacy code expecting pusher_service
try:
    pusher_service = get_pusher_client()
except Exception:
    pusher_service = None
