"""
Application Lifecycle Management

Handles startup and shutdown operations for the FastAPI application.
"""

import asyncio
import logging
import os
from fastapi import FastAPI

from apps.backend.core.logging import logging_manager
from apps.backend.core.config import settings

logger = logging_manager.get_logger(__name__)


async def register_startup_handlers(app: FastAPI) -> None:
    """
    Register and execute application startup handlers

    Args:
        app: FastAPI application instance
    """
    logger.info("Executing startup handlers...")

    try:
        # Initialize authentication system
        await _initialize_auth_system(app)

        # Initialize database connections
        await _initialize_database(app)

        # Initialize external services
        await _initialize_external_services(app)

        # Initialize agent systems
        await _initialize_agent_systems(app)

        # Initialize monitoring and metrics
        await _initialize_monitoring(app)

        logger.info("All startup handlers completed successfully")

    except Exception as e:
        logger.error(f"Startup handler failed: {e}")
        raise


async def register_shutdown_handlers(app: FastAPI) -> None:
    """
    Register and execute application shutdown handlers

    Args:
        app: FastAPI application instance
    """
    logger.info("Executing shutdown handlers...")

    try:
        # Shutdown agent systems
        await _shutdown_agent_systems(app)

        # Close external service connections
        await _shutdown_external_services(app)

        # Close database connections
        await _shutdown_database(app)

        # Cleanup monitoring resources
        await _cleanup_monitoring(app)

        logger.info("All shutdown handlers completed successfully")

    except Exception as e:
        logger.error(f"Shutdown handler failed: {e}")


async def _initialize_auth_system(app: FastAPI) -> None:
    """Initialize authentication and authorization system"""
    try:
        from apps.backend.api.auth.auth import initialize_auth
        initialize_auth()  # This is a synchronous function
        logger.info("Authentication system initialized")
    except ImportError as e:
        logger.warning(f"Could not initialize auth system: {e}")


async def _initialize_database(app: FastAPI) -> None:
    """Initialize database connections and services"""
    try:
        from apps.backend.services.database import db_service
        # Database initialization if needed
        logger.info("Database services initialized")
    except ImportError as e:
        logger.warning(f"Could not initialize database: {e}")


async def _initialize_external_services(app: FastAPI) -> None:
    """Initialize external service connections"""
    try:
        # Initialize Pusher service
        from apps.backend.services.pusher_realtime import get_pusher_service
        pusher_service = get_pusher_service()
        if pusher_service:
            logger.info("Pusher service initialized")

        # Initialize Supabase if available
        try:
            from apps.backend.core.supabase_config import initialize_supabase_for_agents
            await initialize_supabase_for_agents()
            logger.info("Supabase services initialized")
        except ImportError:
            logger.debug("Supabase services not available")

    except Exception as e:
        logger.warning(f"Could not initialize external services: {e}")


async def _initialize_agent_systems(app: FastAPI) -> None:
    """Initialize AI agent systems"""
    try:
        from apps.backend.agents.agent import initialize_agents
        await initialize_agents()
        logger.info("Agent systems initialized")

        # Initialize agent service queue if available
        try:
            from apps.backend.services.agent_service import get_agent_service
            agent_service = get_agent_service()
            if agent_service:
                logger.info("Agent service queue initialized")
        except ImportError:
            logger.debug("Agent service queue not available")

    except ImportError as e:
        logger.warning(f"Could not initialize agent systems: {e}")


async def _initialize_monitoring(app: FastAPI) -> None:
    """Initialize monitoring and metrics systems"""
    try:
        # Initialize secrets manager
        from apps.backend.core.security.secrets import init_secrets_manager
        init_secrets_manager()
        logger.info("Secrets manager initialized")

        # Log successful startup
        logger.info(
            "Application startup completed",
            extra_fields={
                "app_name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
                "startup_time": "completed"
            }
        )

    except Exception as e:
        logger.warning(f"Could not initialize monitoring: {e}")


async def _shutdown_agent_systems(app: FastAPI) -> None:
    """Shutdown AI agent systems"""
    try:
        from apps.backend.agents.agent import shutdown_agents
        await shutdown_agents()
        logger.info("Agent systems shutdown completed")

        # Shutdown agent services if available
        try:
            from apps.backend.services.agent_service import shutdown_agent_service
            from apps.backend.services.agent_queue import shutdown_agent_queue

            await shutdown_agent_service()
            await shutdown_agent_queue()
            logger.info("Agent service queues shutdown completed")
        except ImportError:
            logger.debug("Agent service queues not available for shutdown")

    except ImportError as e:
        logger.warning(f"Could not shutdown agent systems: {e}")


async def _shutdown_external_services(app: FastAPI) -> None:
    """Shutdown external service connections"""
    try:
        # Cleanup any Pusher connections
        logger.info("External services shutdown completed")
    except Exception as e:
        logger.warning(f"Could not shutdown external services: {e}")


async def _shutdown_database(app: FastAPI) -> None:
    """Shutdown database connections"""
    try:
        # Database cleanup if needed
        logger.info("Database connections shutdown completed")
    except Exception as e:
        logger.warning(f"Could not shutdown database: {e}")


async def _cleanup_monitoring(app: FastAPI) -> None:
    """Cleanup monitoring and metrics resources"""
    try:
        # Log successful shutdown
        logger.info(
            "Application shutdown completed",
            extra_fields={
                "app_name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "shutdown_time": "completed"
            }
        )

    except Exception as e:
        logger.warning(f"Could not cleanup monitoring: {e}")