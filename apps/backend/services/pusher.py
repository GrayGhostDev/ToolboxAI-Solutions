"""
Pusher Channels integration helpers for FastAPI backend.

- Initializes a Pusher client from environment (via settings)
- Provides auth signature generation for Channels subscription
- Provides helper to trigger events and verify webhooks
"""
from __future__ import annotations

import hmac
import json
import logging
from datetime import datetime
from hashlib import sha256
from typing import Any, Dict, Optional, List

try:
    import pusher  # type: ignore
except Exception:  # pragma: no cover-optional import in some environments
    pusher = None  # type: ignore

from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class PusherUnavailable(Exception):
    pass


def _ensure_pusher_available():
    if pusher is None:
        raise PusherUnavailable("The 'pusher' package is not installed. Run: pip install pusher")
    if not (settings.PUSHER_ENABLED and settings.PUSHER_APP_ID and settings.PUSHER_KEY and settings.PUSHER_SECRET):
        raise PusherUnavailable("Pusher configuration missing. Ensure PUSHER_ENABLED, PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET, PUSHER_CLUSTER are set.")


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
            raise PusherUnavailable("Pusher client not initialized. Check pusher package installation and configuration.")

    def trigger(self, channel: str, event: str, data: Dict[str, Any]) -> Dict[str, Any]:
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
                "timestamp": str(datetime.now())
            }
            self.client.trigger(channel, event, safe_data)

        return {"channel": channel, "event": event}

    def trigger_batch(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Trigger multiple events at once."""
        self._ensure_client_available()
        self.client.trigger_batch(events)
        return {"status": "success", "events_count": len(events)}

    def authenticate(self, channel: str, socket_id: str, user_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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

    def channels_info(self, prefix_filter: Optional[str] = None, attributes: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get information about all channels."""
        self._ensure_client_available()

        kwargs = {}
        if prefix_filter:
            kwargs['prefix_filter'] = prefix_filter
        if attributes:
            kwargs['info'] = ','.join(attributes)

        return self.client.channels_info(**kwargs)

    def channel_info(self, channel: str, attributes: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get information about a specific channel."""
        self._ensure_client_available()

        if attributes:
            return self.client.channel_info(channel, info=','.join(attributes))
        else:
            return self.client.channel_info(channel)

    def users_info(self, channel: str) -> Dict[str, Any]:
        """Get users information for a presence channel."""
        self._ensure_client_available()
        return self.client.users_info(channel)

    def validate_webhook(self, key: str, signature: str, body: str) -> bool:
        """Validate a webhook signature."""
        self._ensure_client_available()
        return self.client.validate_webhook(key, signature, body)

    async def async_trigger(self, channel: str, event: str, data: Dict[str, Any]) -> Dict[str, Any]:
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


def trigger_event(channel: str, event: str, data: Dict[str, Any]) -> Dict[str, Any]:
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
            "timestamp": str(datetime.now())
        }
        client.trigger(channel, event, safe_data)
    return {"channel": channel, "event": event}


def authenticate_channel(socket_id: str, channel_name: str, user_id: Optional[str] = None, user_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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


def verify_webhook(headers: Dict[str, str], body: bytes) -> Optional[Dict[str, Any]]:
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


# Export for compatibility with legacy code expecting pusher_service
try:
    pusher_service = get_pusher_client()
except Exception:
    pusher_service = None
