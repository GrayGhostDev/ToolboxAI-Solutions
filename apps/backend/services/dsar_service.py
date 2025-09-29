"""
DSAR Export Service using Redis (async)

Stores user export bundles keyed by ticket with TTL and provides status checks.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

import redis.asyncio as redis  # type: ignore

try:
    from apps.backend.core.config import settings
except Exception:  # pragma: no cover
    from ...core.config import settings  # type: ignore

logger = logging.getLogger(__name__)

EXPORT_TTL_SECONDS = 24 * 3600
KEY_EXPORT = "dsar:export:{ticket}"
KEY_STATUS = "dsar:status:{ticket}"


async def _get_redis() -> redis.Redis:
    return await redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)


async def set_status(ticket: str, status: str) -> None:
    client = await _get_redis()
    await client.set(KEY_STATUS.format(ticket=ticket), status, ex=EXPORT_TTL_SECONDS)


async def get_status(ticket: str) -> Optional[str]:
    client = await _get_redis()
    return await client.get(KEY_STATUS.format(ticket=ticket))


async def store_export(ticket: str, data: Dict[str, Any]) -> None:
    client = await _get_redis()
    payload = json.dumps(data, default=str)
    await client.set(KEY_EXPORT.format(ticket=ticket), payload, ex=EXPORT_TTL_SECONDS)


async def get_export(ticket: str) -> Optional[Dict[str, Any]]:
    client = await _get_redis()
    payload = await client.get(KEY_EXPORT.format(ticket=ticket))
    if not payload:
        return None
    try:
        return json.loads(payload)
    except Exception:
        return None


async def generate_export(ticket: str, user: Any) -> None:
    """
    Assemble a minimal export for the current user and store in Redis.
    Replace with real database aggregation.
    """
    await set_status(ticket, "pending")

    # Simulate processing time
    await asyncio.sleep(0.1)

    now = datetime.now(timezone.utc).isoformat()
    export_bundle = {
        "ticket": ticket,
        "generated_at": now,
        "user": {
            "id": getattr(user, "id", None),
            "username": getattr(user, "username", None),
            "email": getattr(user, "email", None),
            "role": getattr(user, "role", None),
        },
        "records": {
            # TODO: Fetch real records from DB/services
            "progress": [],
            "assignments": [],
            "messages": [],
        },
        "note": "Demo export. Replace with actual export generation from DB.",
    }

    await store_export(ticket, export_bundle)
    await set_status(ticket, "ready")
