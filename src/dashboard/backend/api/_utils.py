"""Small helpers for API modules."""

import json
from typing import Any, Dict


def safe_json_loads(value: Any, default: Any):
    """Safely parse JSON if input is a string; otherwise return default or value when appropriate.

    This avoids passing non-str objects to json.loads which causes static-checker errors.
    """
    if value is None:
        return default
    if isinstance(value, (str, bytes, bytearray)):
        try:
            return json.loads(value)
        except Exception:
            return default
    # Already parsed Python object
    return value


def now():
    """Return timezone-aware current UTC datetime.

    Use this helper instead of datetime.utcnow() to produce tz-aware datetimes
    and satisfy linters that prefer timezone-aware timestamps.
    """
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)
