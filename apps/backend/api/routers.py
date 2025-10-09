"""
Router Registration for ToolboxAI Backend
Centralized router management for all API endpoints
"""

from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)


def register_routers(app: FastAPI) -> None:
    """
    Register all API routers with the FastAPI application
    """
    logger.info("Registering API routers...")

    # Import routers
    try:
        # Educational Platform Routes (NEW)
        from apps.backend.routers.courses import router as courses_router
        app.include_router(courses_router, tags=["courses"])
        logger.info("✓ Registered courses router at /api/v1/courses")
    except ImportError as e:
        logger.warning(f"Could not import courses router: {e}")
    except Exception as e:
        logger.error(f"Error registering courses router: {e}")

    logger.info("Custom router registration complete")
