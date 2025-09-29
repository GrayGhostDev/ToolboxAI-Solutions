"""Async and event loop test fixtures.

This module contains fixtures for managing async operations, event loops,
and async context in tests.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session.

    This fixture provides a session-scoped event loop that can be reused
    across all async tests in the session.
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_running_loop()
        logger.info("Using existing event loop")
    except RuntimeError:
        # No event loop running, create a new one
        if sys.platform.startswith("win"):
            # Windows requires ProactorEventLoop for subprocess support
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.new_event_loop()

        asyncio.set_event_loop(loop)
        logger.info("Created new event loop")

    yield loop

    # Cleanup pending tasks
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()

    # Wait for all tasks to complete cancellation
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

    # Close the loop
    try:
        loop.close()
    except Exception as e:
        logger.warning(f"Error closing event loop: {e}")


@pytest.fixture
async def async_context():
    """Provide an async context manager for tests.

    This fixture helps manage async resources in tests, ensuring proper
    setup and teardown of async contexts.
    """
    @asynccontextmanager
    async def _context():
        # Setup
        logger.debug("Setting up async context")
        resources = {}

        try:
            yield resources
        finally:
            # Cleanup
            logger.debug("Tearing down async context")
            for resource_name, resource in resources.items():
                if hasattr(resource, "close"):
                    try:
                        if asyncio.iscoroutinefunction(resource.close):
                            await resource.close()
                        else:
                            resource.close()
                    except Exception as e:
                        logger.warning(f"Error closing {resource_name}: {e}")

    async with _context() as ctx:
        yield ctx


@pytest.fixture(autouse=True)
def handle_event_loop_errors(monkeypatch):
    """Handle event loop errors gracefully in tests.

    This fixture patches event loop error handling to prevent tests from
    failing due to unhandled exceptions in background tasks.
    """
    original_exception_handler = None

    def exception_handler(loop, context):
        exception = context.get("exception")
        if exception:
            logger.error(f"Unhandled exception in event loop: {exception}", exc_info=exception)
        else:
            logger.error(f"Event loop error: {context}")

        # Don't propagate certain expected errors during testing
        if isinstance(exception, (asyncio.CancelledError, ConnectionResetError)):
            return

        # Call original handler for other errors
        if original_exception_handler:
            original_exception_handler(loop, context)

    def setup_handler():
        loop = asyncio.get_event_loop()
        nonlocal original_exception_handler
        original_exception_handler = loop.get_exception_handler()
        loop.set_exception_handler(exception_handler)

    def teardown_handler():
        try:
            loop = asyncio.get_event_loop()
            loop.set_exception_handler(original_exception_handler)
        except RuntimeError:
            pass  # No event loop running

    setup_handler()
    yield
    teardown_handler()


@pytest.fixture(scope="function", autouse=True)
def cleanup_async_tasks(request):
    """Automatically cleanup async tasks after each test.

    This fixture ensures that all async tasks are properly cancelled
    and cleaned up after each test function completes.
    """
    yield

    # Get all tasks for the current event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Can't cleanup while loop is running, schedule for later
            pending = asyncio.all_tasks(loop)
            for task in pending:
                if not task.done() and task != asyncio.current_task():
                    task.cancel()
        else:
            # Loop not running, we can cleanup now
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()

            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except RuntimeError:
        # No event loop
        pass
    except Exception as e:
        logger.warning(f"Error cleaning up async tasks: {e}")


@pytest.fixture(scope="function", autouse=True)
async def enhanced_async_cleanup():
    """Enhanced cleanup for async resources.

    This fixture provides comprehensive cleanup for async resources including
    database connections, Redis connections, and any open async generators.
    """
    # Track resources created during test
    resources = []

    def register_resource(resource):
        resources.append(resource)

    # Make registration function available
    pytest.register_async_resource = register_resource

    yield

    # Cleanup registered resources
    for resource in reversed(resources):
        try:
            if hasattr(resource, "aclose"):
                await resource.aclose()
            elif hasattr(resource, "close"):
                if asyncio.iscoroutinefunction(resource.close):
                    await resource.close()
                else:
                    resource.close()
        except Exception as e:
            logger.warning(f"Error cleaning up resource {resource}: {e}")

    # Clear the registration function
    if hasattr(pytest, "register_async_resource"):
        delattr(pytest, "register_async_resource")