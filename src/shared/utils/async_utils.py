"""Small helper utilities for running async code from sync callsites.

This centralizes the new_event_loop + set_event_loop + run_until_complete + close
pattern used in several bridge modules so the pattern is consistent and easy to
update.

Usage:
    from toolboxai_utils.async_utils import run_async
    result = run_async(some_coroutine(...))
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, TypeVar

T = TypeVar("T")


def run_async(awaitable: Awaitable[T]) -> T:
    """Run an awaitable in a fresh event loop and return its result.

    This function creates a new event loop, sets it as the current loop,
    runs the awaitable, and ensures the loop is closed. It intentionally
    uses a fresh loop to avoid interfering with any running loops (e.g., in
    servers).
    """
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(awaitable)
    finally:
        try:
            loop.close()
        finally:
            # Clear the event loop to avoid leaving a dangling loop set in some
            # environments.
            try:
                asyncio.set_event_loop(None)
            except (RuntimeError, OSError, AttributeError):
                # Suppress specific exceptions from setting the event loop to None
                # RuntimeError: event loop operations
                # OSError: system-level errors
                # AttributeError: missing methods in some Python versions
                pass
