"""
Application Factory for FastAPI ToolboxAI Backend

This module implements the application factory pattern for creating and configuring
FastAPI application instances with proper separation of concerns.
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from apps.backend.core.config import settings
from apps.backend.core.monitoring import initialize_sentry
from apps.backend.core.logging import initialize_logging, logging_manager
# from apps.backend.core.observability.telemetry import telemetry_manager  # Imported locally to avoid circular imports

# Will create these modules in subsequent steps
try:
    from apps.backend.core.lifecycle import register_startup_handlers, register_shutdown_handlers
    from apps.backend.core.middleware import register_middleware
    from apps.backend.api.routers import register_routers

    FACTORY_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Factory components not yet available: {e}")
    FACTORY_COMPONENTS_AVAILABLE = False

logger = logging_manager.get_logger(__name__)


@asynccontextmanager
async def application_lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    # Check if we're in testing mode
    if os.getenv("TESTING", "false").lower() == "true":
        logger.info("Running in testing mode - skipping startup operations")
        yield
        logger.info("Testing mode - skipping shutdown operations")
        return

    # Check if we should skip lifespan operations
    if os.getenv("SKIP_LIFESPAN", "false").lower() == "true":
        logger.info("SKIP_LIFESPAN set - minimal startup")
        yield
        logger.info("SKIP_LIFESPAN set - minimal shutdown")
        return

    # Startup
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION} (environment: {settings.ENVIRONMENT})"
    )

    try:
        # Execute startup handlers if available
        if FACTORY_COMPONENTS_AVAILABLE:
            await register_startup_handlers(app)
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

    yield

    # Shutdown
    try:
        if FACTORY_COMPONENTS_AVAILABLE:
            await register_shutdown_handlers(app)
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Application shutdown failed: {e}")


@asynccontextmanager
async def empty_lifespan(app: FastAPI):
    """Empty lifespan for testing - no startup/shutdown operations"""
    logger.debug("Using empty lifespan context (testing mode)")
    yield
    logger.debug("Empty lifespan context complete")


def create_app(
    skip_lifespan: bool = False,
    skip_sentry: bool = False,
    title: Optional[str] = None,
    version: Optional[str] = None,
    testing_mode: bool = False,
    config_settings: Optional[object] = None,
) -> FastAPI:
    """
    Application factory function to create and configure FastAPI app

    Args:
        skip_lifespan: If True, skip the lifespan context manager (for testing)
        skip_sentry: If True, skip Sentry initialization
        title: App title (defaults to settings.APP_NAME)
        version: App version (defaults to settings.APP_VERSION)
        testing_mode: If True, configure app for testing
        config_settings: Optional configuration settings object

    Returns:
        Configured FastAPI application instance
    """
    # Use provided settings or default
    app_settings = config_settings or settings

    # Determine if we're in testing mode
    if testing_mode or os.getenv("TESTING", "false").lower() == "true":
        skip_lifespan = True
        skip_sentry = True
        logger.info("Creating app in testing mode")

    # Initialize monitoring and logging first (unless skipped)
    if not skip_sentry:
        initialize_sentry()
    initialize_logging()

    # Initialize OpenTelemetry instrumentation (unless in testing mode)
    if not testing_mode and not skip_lifespan:
        try:
            from apps.backend.core.observability.telemetry import telemetry_manager
            telemetry_manager.initialize(
                service_name=app_settings.APP_NAME,
                service_version=app_settings.APP_VERSION,
                otel_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
                enable_logging=True,
                enable_metrics=True,
                enable_tracing=True,
                additional_attributes={
                    "deployment.environment": app_settings.ENVIRONMENT,
                    "service.namespace": "toolboxai",
                }
            )
            logger.info("OpenTelemetry instrumentation initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenTelemetry: {e}")

    # Determine if we should use lifespan
    use_lifespan = not (skip_lifespan or os.getenv("SKIP_LIFESPAN", "false").lower() == "true")

    # Create FastAPI app
    app_kwargs = {
        "title": title or app_settings.APP_NAME,
        "version": version or app_settings.APP_VERSION,
        "description": "AI-Powered Educational Roblox Environment - Generate immersive educational content with AI agents",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
    }

    if use_lifespan:
        app_kwargs["lifespan"] = application_lifespan
        logger.info("Created FastAPI app with full lifespan")
    else:
        app_kwargs["lifespan"] = empty_lifespan
        logger.info("Created FastAPI app without lifespan (testing/import mode)")

    app = FastAPI(**app_kwargs)

    # Store configuration flags in app state
    app.state.testing_mode = testing_mode
    app.state.skip_sentry = skip_sentry
    app.state.skip_lifespan = skip_lifespan

    # Track application start time for uptime calculations
    app.state.start_time = time.time()

    # Instrument FastAPI app with OpenTelemetry (unless in testing mode)
    if not testing_mode and not skip_lifespan:
        try:
            from apps.backend.core.observability.telemetry import telemetry_manager
            telemetry_manager.instrument_fastapi(app)
            logger.info("FastAPI app instrumented with OpenTelemetry")
        except Exception as e:
            logger.warning(f"Failed to instrument FastAPI with OpenTelemetry: {e}")

    # Register middleware and routers if factory components are available
    if FACTORY_COMPONENTS_AVAILABLE:
        register_middleware(app)
        register_routers(app)
        logger.info("Middleware and routers registered successfully")
    else:
        logger.warning(
            "Factory components not available - skipping middleware and router registration"
        )

    logger.info("FastAPI application created and configured successfully")

    return app


def create_test_app() -> FastAPI:
    """
    Create a FastAPI app specifically for testing.

    This app skips all startup operations and external dependencies.
    """
    return create_app(skip_lifespan=True, skip_sentry=True, testing_mode=True)
