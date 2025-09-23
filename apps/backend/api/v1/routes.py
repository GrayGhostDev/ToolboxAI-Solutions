"""
API v1 route registration
"""

from fastapi import APIRouter, FastAPI

from apps.backend.core.logging import logging_manager

# Import endpoint modules
from apps.backend.api.v1.endpoints import (
    auth,
    agents,
    content,
    pusher,
    websocket,
    health,
    admin,
    analytics,
    lms,
    plugins,
    roblox,
    terminal,
    users
)

# Initialize logger
logger = logging_manager.get_logger(__name__)


def register_v1_routes(app: FastAPI) -> None:
    """Register all v1 API routes"""
    logger.info("Registering API v1 routes...")

    # Create v1 router
    v1_router = APIRouter(prefix="/api/v1", tags=["API v1"])

    # Authentication routes
    v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

    # Agent routes
    v1_router.include_router(agents.router, prefix="/agents", tags=["Agent System"])

    # Content routes
    v1_router.include_router(content.router, prefix="/content", tags=["Content API"])

    # User routes
    v1_router.include_router(users.router, prefix="/users", tags=["User Management"])

    # Analytics routes
    v1_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

    # Roblox routes
    v1_router.include_router(roblox.router, prefix="/roblox", tags=["Roblox Integration"])

    # Terminal routes
    v1_router.include_router(terminal.router, prefix="/terminal", tags=["Terminal"])

    # Admin routes
    v1_router.include_router(admin.router, prefix="/admin", tags=["Administration"])

    # LMS routes
    v1_router.include_router(lms.router, prefix="/lms", tags=["LMS Integration"])

    # Plugin routes
    v1_router.include_router(plugins.router, prefix="/plugins", tags=["Plugin Management"])

    # Include v1 router in main app
    app.include_router(v1_router)

    logger.info("API v1 routes registered successfully")


def register_root_routes(app: FastAPI) -> None:
    """Register root-level routes (non-versioned)"""
    logger.info("Registering root-level routes...")

    # Health and system routes
    app.include_router(health.router, tags=["System"])

    # Pusher routes (realtime)
    app.include_router(pusher.router, prefix="/pusher", tags=["Realtime"])

    # WebSocket routes
    app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])

    # Legacy authentication routes (for backward compatibility)
    app.include_router(auth.legacy_router, prefix="/auth", tags=["Authentication (Legacy)"])

    logger.info("Root-level routes registered successfully")


def register_all_routes(app: FastAPI) -> None:
    """Register all routes (v1 and root-level)"""
    register_root_routes(app)
    register_v1_routes(app)
    logger.info("All routes registered successfully")