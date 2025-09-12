"""Async utilities for ToolboxAI"""

import asyncio
import threading
from typing import Any, Coroutine
from concurrent.futures import ThreadPoolExecutor


class AsyncRunner:
    """Thread-safe async execution wrapper"""
    
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
        """Run coroutine in background loop"""
        if self._loop is None:
            raise RuntimeError("Event loop not initialized")
        
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=30)


# Global async runner instance
_async_runner = AsyncRunner()


def run_async(coro: Coroutine) -> Any:
    """Run async coroutine from sync context"""
    return _async_runner.run(coro)