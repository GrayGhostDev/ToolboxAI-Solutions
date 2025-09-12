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
from hashlib import sha256
from typing import Any, Dict, Optional

try:
    import pusher  # type: ignore
except Exception:  # pragma: no cover-optional import in some environments
    pusher = None  # type: ignore

from ..core.config import settings

logger = logging.getLogger(__name__)


class PusherUnavailable(Exception):
    pass


def _ensure_pusher_available():
    if pusher is None:
        raise PusherUnavailable("The 'pusher' package is not installed. Run: pip install pusher")
    if not (settings.PUSHER_ENABLED and settings.PUSHER_APP_ID and settings.PUSHER_KEY and settings.PUSHER_SECRET):
        raise PusherUnavailable("Pusher configuration missing. Ensure PUSHER_ENABLED, PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET, PUSHER_CLUSTER are set.")


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
    client.trigger(channel, event, data)
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
