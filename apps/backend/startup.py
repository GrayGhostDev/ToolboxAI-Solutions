"""
Application startup configuration for ToolboxAI Roblox Environment

This module handles initialization of all server components including
rate limiting, authentication, and other core services.
"""

import logging
import os
from typing import Optional

from .config import settings
from .rate_limit_manager import (
    RateLimitManager,
    RateLimitConfig,
    RateLimitMode,
    get_rate_limit_manager
)

logger = logging.getLogger(__name__)


def initialize_rate_limiting(redis_client: Optional[any] = None) -> RateLimitManager:
    """
    Initialize the centralized rate limiting system
    
    Args:
        redis_client: Optional Redis client for backend storage
        
    Returns:
        RateLimitManager: Configured rate limit manager instance
    """
    # Determine mode based on environment
    if settings.ENVIRONMENT == "testing" or settings.TESTING_MODE:
        mode = RateLimitMode.TESTING if not settings.BYPASS_RATE_LIMIT_IN_TESTS else RateLimitMode.BYPASS
    else:
        mode = RateLimitMode.PRODUCTION
    
    # Create configuration
    config = RateLimitConfig(
        requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
        burst_limit=settings.RATE_LIMIT_BURST,
        window_seconds=60,
        exclude_paths={"/health", "/metrics", "/status"},
        by_endpoint={
            "/generate_content": 30,  # More restrictive for expensive operations
            "/api/v1/agent/execute": 20,
            "/plugin/heartbeat": 120,  # Higher limit for plugin heartbeats
        },
        mode=mode
    )
    
    # Get or create manager instance
    manager = RateLimitManager.get_instance(config=config, redis_client=redis_client)
    manager.set_mode(mode)
    
    logger.info(f"Rate limiting initialized in {mode.value} mode")
    
    return manager


def initialize_application() -> dict:
    """
    Initialize the entire application
    
    Returns:
        dict: Configuration and status information
    """
    logger.info("Initializing ToolboxAI Roblox Environment")
    
    # Initialize Redis client if needed
    redis_client = None
    try:
        import redis
        redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Using in-memory storage.")
        redis_client = None
    
    # Initialize rate limiting
    rate_limit_manager = initialize_rate_limiting(redis_client)
    
    # Initialize authentication system
    try:
        from .auth import initialize_auth
        initialize_auth()
        logger.info("Authentication system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize authentication: {e}")
    
    # Start cleanup tasks
    import asyncio
    try:
        # Start rate limiting cleanup task
        loop = asyncio.get_event_loop()
        loop.create_task(rate_limit_manager.start_cleanup())
        logger.info("Cleanup tasks started")
    except RuntimeError:
        # No event loop running, cleanup will be started later
        logger.info("Cleanup tasks will be started when event loop is available")
    
    return {
        "status": "initialized",
        "components": {
            "rate_limiting": "active" if rate_limit_manager else "failed",
            "redis": "connected" if redis_client else "disconnected",
            "authentication": "active"
        },
        "configuration": {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "rate_limit_mode": rate_limit_manager.config.mode.value if rate_limit_manager else "unknown"
        }
    }


def shutdown_application():
    """
    Gracefully shutdown the application
    """
    logger.info("Shutting down ToolboxAI Roblox Environment")
    
    try:
        # Stop rate limiting cleanup tasks
        manager = get_rate_limit_manager()
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(manager.stop_cleanup())
        
        # Clear rate limiting state
        manager.clear_all_limits()
        
        logger.info("Rate limiting cleanup completed")
    except Exception as e:
        logger.error(f"Error during rate limiting shutdown: {e}")
    
    # Reset singleton for clean shutdown
    RateLimitManager.reset_instance()
    
    logger.info("Application shutdown completed")


# Environment-specific initialization
def setup_development_environment():
    """Setup development-specific configuration"""
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    logger.info("Development environment configured")


def setup_testing_environment():
    """Setup testing-specific configuration"""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["TESTING_MODE"] = "true"
    os.environ["BYPASS_RATE_LIMIT_IN_TESTS"] = "true"
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    logger.info("Testing environment configured")


def setup_production_environment():
    """Setup production-specific configuration"""
    os.environ["ENVIRONMENT"] = "production"
    os.environ["DEBUG"] = "false"
    os.environ["LOG_LEVEL"] = "INFO"
    logger.info("Production environment configured")


__all__ = [
    "initialize_rate_limiting",
    "initialize_application",
    "shutdown_application",
    "setup_development_environment",
    "setup_testing_environment",
    "setup_production_environment"
]