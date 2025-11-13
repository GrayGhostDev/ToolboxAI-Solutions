"""Async utilities for running coroutines from synchronous contexts

This module provides utilities for executing async code from sync contexts,
primarily used by the Roblox service for bridging async content generation.
"""

import asyncio
import threading
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any


class AsyncRunner:
    """Thread-safe async execution wrapper for sync-to-async bridge

    This class manages a background event loop in a separate thread,
    allowing synchronous code to execute async coroutines safely.
    """

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._loop = None
        self._thread = None
        self._start_loop()

    def _start_loop(self):
        """Start event loop in background thread"""

        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()

        # Wait for loop to be ready
        while self._loop is None:
            threading.Event().wait(0.01)

    def run(self, coro: Coroutine) -> Any:
        """Run coroutine in background loop

        Args:
            coro: The coroutine to execute

        Returns:
            The result of the coroutine execution

        Raises:
            RuntimeError: If the event loop is not initialized
            TimeoutError: If the coroutine takes longer than 30 seconds
        """
        if self._loop is None:
            raise RuntimeError("Event loop not initialized")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=30)


# Global async runner instance
_async_runner = AsyncRunner()


def run_async(coro: Coroutine) -> Any:
    """Run async coroutine from sync context

    This is the main entry point for executing async code from
    synchronous contexts like Flask routes or legacy code.

    Args:
        coro: The coroutine to execute

    Returns:
        The result of the coroutine execution

    Example:
        >>> async def fetch_data():
        ...     return await some_async_operation()
        >>> result = run_async(fetch_data())
    """
    return _async_runner.run(coro)
