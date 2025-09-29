"""
Router Registry

Centralized registration of all FastAPI routers and endpoints.
"""

import logging
from fastapi import FastAPI

from apps.backend.core.logging import logging_manager

logger = logging_manager.get_logger(__name__)


def register_routers(app: FastAPI) -> None:
    """
    Register all router components

    Args:
        app: FastAPI application instance
    """
    logger.info("Registering router components...")

    try:
        # Register core routers
        _register_core_routers(app)

        # Register API v1 routers
        _register_v1_routers(app)

        # Register webhook routers
        _register_webhook_routers(app)

        # Register legacy routers for backward compatibility
        _register_legacy_routers(app)

        logger.info("All router components registered successfully")

    except Exception as e:
        logger.error(f"Failed to register routers: {e}")
        raise


def _register_core_routers(app: FastAPI) -> None:
    """Register core system routers"""
    try:
        # Health and system status routers
        try:
            from apps.backend.api.routers.health import router as health_router

            app.include_router(health_router)
            logger.info("Health check endpoints loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load health check endpoints: {e}")

        # Secure Roblox Integration Router (Priority - loads first)
        try:
            from apps.backend.routers.roblox import router as secure_roblox_router

            app.include_router(secure_roblox_router)
            logger.info("✅ Secure Roblox integration endpoints loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load secure Roblox integration endpoints: {e}")

        # Pusher and realtime communication routers
        try:
            from apps.backend.api.routers.pusher import router as pusher_router

            app.include_router(pusher_router)
            logger.info("Pusher endpoints loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load Pusher endpoints: {e}")

        # Content generation routers
        try:
            from apps.backend.api.routers.content import router as content_router

            app.include_router(content_router)
            logger.info("Content generation endpoints loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load content generation endpoints: {e}")

        # Legacy health check routers (fallback)
        try:
            from apps.backend.api.health.health_checks import router as health_checks_router
            from apps.backend.api.health.integrations import router as integrations_router

            app.include_router(health_checks_router, prefix="/api/v1")
            app.include_router(integrations_router, prefix="/api/v1")
            logger.info("Legacy health check endpoints loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load legacy health check endpoints: {e}")

        # Legacy Pusher authentication endpoints (fallback)
        try:
            from apps.backend.api.v1.endpoints.pusher_auth import router as pusher_auth_router
            from apps.backend.api.v1.pusher_endpoints import router as pusher_replacement_router

            app.include_router(pusher_auth_router, prefix="/api/v1")
            app.include_router(pusher_replacement_router)
            logger.info("Legacy Pusher endpoints loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load legacy Pusher endpoints: {e}")

    except Exception as e:
        logger.warning(f"Failed to register core routers: {e}")


def _register_v1_routers(app: FastAPI) -> None:
    """Register API v1 routers"""
    routers_config = [
        # Educational content routers
        ("apps.backend.api.v1.endpoints.classes", "classes_router", "/api/v1"),
        ("apps.backend.api.v1.endpoints.lessons", "lessons_router", "/api/v1"),
        ("apps.backend.api.v1.endpoints.assessments", "assessments_router", "/api/v1"),
        ("apps.backend.api.v1.endpoints.educational_content", "router", "/api/v1"),
        # User management routers
        ("apps.backend.api.v1.endpoints.auth", "auth_router", "/api/v1"),
        ("apps.backend.api.v1.endpoints.users", "router", "/api/v1"),

        # Background tasks and Celery management
        ("apps.backend.api.v1.endpoints.tasks", "router", "/api/v1"),
        ("apps.backend.api.v1.endpoints.user_profile", "router", ""),  # User profile endpoints
        # Content and AI routers
        ("apps.backend.api.v1.endpoints.ai_chat", "router", "/api/v1"),
        ("apps.backend.api.v1.endpoints.enhanced_content", "router", ""),
        ("apps.backend.api.v1.endpoints.prompt_templates", "router", "/api/v1"),
        ("apps.backend.api.v1.endpoints.agent_swarm", "router", ""),
        # Roblox integration routers
        ("apps.backend.api.v1.endpoints.roblox", "roblox_router", "/api/v1"),
        ("apps.backend.api.v1.endpoints.roblox_environment", "router", "/api/v1"),
        ("apps.backend.api.v1.endpoints.roblox_integration", "router", "/api/v1"),
        ("apps.backend.api.v1.endpoints.roblox_ai", "router", "/api/v1"),
        # Analytics and reporting
        ("apps.backend.api.v1.endpoints.analytics_reporting", "router", "/api/v1"),
        ("apps.backend.api.v1.endpoints.reports", "reports_router", "/api/v1"),
        # Communication routers
        ("apps.backend.api.v1.endpoints.messages", "messages_router", "/api/v1"),
        # Gamification and engagement
        ("apps.backend.api.v1.endpoints.gamification", "router", "/api/v1/gamification"),
        # Integration and API management
        ("apps.backend.api.v1.endpoints.api_keys", "router", "/api/v1"),
        ("apps.backend.api.v1.endpoints.integration", "router", "/api/v1"),
        # Privacy and compliance
        ("apps.backend.api.v1.endpoints.privacy", "router", ""),
        ("apps.backend.api.v1.endpoints.compliance", "router", "/api/v1"),
        # Payment and billing
        ("apps.backend.api.v1.endpoints.stripe_checkout", "router", ""),
        # Mobile and specialized endpoints
        ("apps.backend.api.v1.endpoints.mobile", "router", "/api/v1"),
        # Database and system management
        ("apps.backend.api.v1.endpoints.database_swarm", "router", "/api/v1"),
        ("apps.backend.api.v1.endpoints.gpt4_migration_monitoring", "router", "/api/v1"),
        # Dashboard endpoints
        ("apps.backend.api.v1.endpoints.dashboard", "dashboard_router", ""),
    ]

    for module_path, router_name, prefix in routers_config:
        try:
            module = __import__(module_path, fromlist=[router_name])
            router = getattr(module, router_name)

            if prefix:
                app.include_router(router, prefix=prefix)
            else:
                app.include_router(router)

            logger.info(f"Router {router_name} from {module_path} loaded successfully")

        except ImportError as e:
            logger.warning(f"Could not load router {router_name} from {module_path}: {e}")
        except AttributeError as e:
            logger.warning(f"Router {router_name} not found in {module_path}: {e}")


def _register_webhook_routers(app: FastAPI) -> None:
    """Register webhook routers"""
    try:
        # Clerk webhooks
        try:
            from apps.backend.api.webhooks.clerk_webhooks import router as clerk_webhook_router

            app.include_router(clerk_webhook_router)
            logger.info("Clerk webhook endpoints loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load Clerk webhook endpoints: {e}")

        # Stripe webhooks
        try:
            from apps.backend.api.v1.endpoints.stripe_webhook import router as stripe_router

            app.include_router(stripe_router)
            logger.info("Stripe webhook endpoints loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load Stripe webhook endpoints: {e}")

    except Exception as e:
        logger.warning(f"Failed to register webhook routers: {e}")


def _register_legacy_routers(app: FastAPI) -> None:
    """Register legacy routers for backward compatibility"""
    try:
        # Legacy API v1 router
        try:
            from apps.backend.api.v1.router import api_router

            app.include_router(api_router, prefix="/api/v1")
            logger.info("Legacy API v1 endpoints loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load legacy API v1 endpoints: {e}")

        # Legacy analytics routers (bulk import)
        try:
            from apps.backend.api.v1.endpoints.analytics import (
                analytics_router,
                gamification_router,
                compliance_router,
                users_router,
                schools_router,
            )

            app.include_router(analytics_router)
            app.include_router(gamification_router)
            app.include_router(compliance_router)
            app.include_router(users_router)
            app.include_router(schools_router)
            logger.info("Legacy analytics endpoints loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load legacy analytics endpoints: {e}")

    except Exception as e:
        logger.warning(f"Failed to register legacy routers: {e}")


def register_additional_endpoints(app: FastAPI) -> None:
    """
    Register additional endpoints that are defined inline in main.py
    This is a transitional function to handle endpoints not yet moved to routers
    """
    logger.info("Registering additional inline endpoints...")

    # This function will be populated as we migrate inline endpoints from main.py
    # to proper router modules in subsequent refactoring steps

    logger.info("Additional inline endpoints registration completed")
