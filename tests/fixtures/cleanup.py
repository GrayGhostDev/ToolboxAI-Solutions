"""Cleanup and teardown test fixtures.

This module contains fixtures for managing test cleanup, including
database cleanup, file cleanup, and resource management.
"""

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function", autouse=True)
async def cleanup_database_pools():
    """Cleanup database connection pools after each test.

    This fixture ensures that all database connections are properly
    closed and pools are cleaned up after each test.
    """
    yield

    # Import here to avoid circular imports
    try:
        from database.connection import async_engine, engine

        # Close sync engine connections
        if engine:
            try:
                engine.dispose()
                logger.debug("Disposed sync database engine")
            except Exception as e:
                logger.warning(f"Error disposing sync engine: {e}")

        # Close async engine connections
        if async_engine:
            try:
                await async_engine.dispose()
                logger.debug("Disposed async database engine")
            except Exception as e:
                logger.warning(f"Error disposing async engine: {e}")
    except ImportError:
        pass  # Database module not available


@pytest.fixture(scope="function", autouse=True)
def cleanup_temp_files():
    """Cleanup temporary files created during tests.

    This fixture tracks and cleans up any temporary files or directories
    created during test execution.
    """
    temp_paths: set[Path] = set()

    def register_temp_path(path: Path):
        """Register a temporary path for cleanup."""
        temp_paths.add(path)

    # Make registration function available
    pytest.register_temp_path = register_temp_path

    yield

    # Cleanup registered paths
    for path in temp_paths:
        try:
            if path.is_file():
                path.unlink()
                logger.debug(f"Removed temporary file: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                logger.debug(f"Removed temporary directory: {path}")
        except Exception as e:
            logger.warning(f"Error cleaning up {path}: {e}")

    # Clear registration function
    if hasattr(pytest, "register_temp_path"):
        delattr(pytest, "register_temp_path")


@pytest.fixture
def temp_directory():
    """Provide a temporary directory for testing.

    This fixture creates a temporary directory that is automatically
    cleaned up after the test completes.
    """
    temp_dir = tempfile.mkdtemp(prefix="test_")
    logger.debug(f"Created temporary directory: {temp_dir}")

    yield Path(temp_dir)

    # Cleanup
    try:
        shutil.rmtree(temp_dir)
        logger.debug(f"Removed temporary directory: {temp_dir}")
    except Exception as e:
        logger.warning(f"Error removing temporary directory {temp_dir}: {e}")


@pytest.fixture
def temp_file():
    """Provide a temporary file for testing.

    Returns a function that creates temporary files with optional content.
    """

    temp_files: list[Path] = []

    def _create_temp_file(
        suffix: str = ".txt",
        prefix: str = "test_",
        content: str = None,
        dir: Path = None,
    ) -> Path:
        """Create a temporary file."""
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
        os.close(fd)  # Close the file descriptor

        path = Path(path)
        temp_files.append(path)

        if content:
            path.write_text(content)

        return path

    yield _create_temp_file

    # Cleanup all created files
    for file_path in temp_files:
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Removed temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Error removing temporary file {file_path}: {e}")


@pytest.fixture(scope="function", autouse=True)
def cleanup_mock_data(monkeypatch):
    """Cleanup mock data and patches after tests.

    This fixture helps ensure that mocks and patches don't leak
    between tests.
    """
    # Track original values that might be modified
    original_env = os.environ.copy()

    yield

    # Restore original environment variables
    os.environ.clear()
    os.environ.update(original_env)

    # Note: monkeypatch automatically undoes all patches after the test


@pytest.fixture(scope="function", autouse=True)
async def cleanup_redis_data():
    """Cleanup Redis data after each test.

    This fixture ensures that test data in Redis is cleaned up
    after each test to prevent data leakage between tests.
    """
    yield

    # Import here to avoid circular imports
    try:
        from database.redis_client import get_redis_client

        redis_client = await get_redis_client()
        if redis_client:
            try:
                # Clear test-specific keys (keys with test_ prefix)
                async for key in redis_client.scan_iter("test_*"):
                    await redis_client.delete(key)
                logger.debug("Cleaned up Redis test data")
            except Exception as e:
                logger.warning(f"Error cleaning up Redis data: {e}")
            finally:
                await redis_client.close()
    except ImportError:
        pass  # Redis module not available


@pytest.fixture(scope="function", autouse=True)
def cleanup_log_handlers():
    """Cleanup log handlers after tests.

    This fixture ensures that log handlers added during tests
    are properly removed to prevent memory leaks.
    """
    # Get initial handlers
    root_logger = logging.getLogger()
    initial_handlers = list(root_logger.handlers)

    yield

    # Remove any handlers added during the test
    current_handlers = list(root_logger.handlers)
    for handler in current_handlers:
        if handler not in initial_handlers:
            root_logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass  # Some handlers don't have close()


@pytest.fixture
def cleanup_on_failure(request):
    """Perform cleanup only if the test fails.

    This fixture allows you to register cleanup functions that
    only run if the test fails.
    """
    cleanup_functions = []

    def register_cleanup(func, *args, **kwargs):
        """Register a cleanup function."""
        cleanup_functions.append((func, args, kwargs))

    yield register_cleanup

    # Check if test failed
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        logger.info("Test failed, running cleanup functions")
        for func, args, kwargs in cleanup_functions:
            try:
                if asyncio.iscoroutinefunction(func):
                    asyncio.run(func(*args, **kwargs))
                else:
                    func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in cleanup function {func.__name__}: {e}")


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts(request):
    """Cleanup test artifacts at the end of the test session.

    This fixture performs final cleanup of any test artifacts
    that might have been left behind during the test session.
    """

    def cleanup():
        """Perform final cleanup."""
        # Clean up test output directories
        test_output_dirs = [
            "test-results",
            "test_output",
            ".pytest_cache/test_artifacts",
            "htmlcov",  # Coverage reports
        ]

        for dir_name in test_output_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists() and dir_path.is_dir():
                try:
                    # Only remove if it contains test data
                    if any(file.name.startswith("test_") for file in dir_path.rglob("*")):
                        shutil.rmtree(dir_path)
                        logger.info(f"Cleaned up test artifacts in {dir_path}")
                except Exception as e:
                    logger.warning(f"Could not clean up {dir_path}: {e}")

    # Register cleanup to run at session end
    request.addfinalizer(cleanup)

    yield
