"""
FastAPI App Factory

Creates FastAPI application instances with configurable options for testing and production.
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .core.config import settings

logger = logging.getLogger(__name__)


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
    testing_mode: bool = False
) -> FastAPI:
    """
    Create a FastAPI application instance.
    
    Args:
        skip_lifespan: If True, skip the lifespan context manager (for testing)
        skip_sentry: If True, skip Sentry initialization
        title: App title (defaults to settings.APP_NAME)
        version: App version (defaults to settings.APP_VERSION)
        testing_mode: If True, configure app for testing
    
    Returns:
        FastAPI application instance
    """
    # Determine if we're in testing mode
    if testing_mode or os.getenv("TESTING", "false").lower() == "true":
        skip_lifespan = True
        skip_sentry = True
        logger.info("Creating app in testing mode")
    
    # Configure app parameters
    app_config = {
        "title": title or settings.APP_NAME,
        "version": version or settings.APP_VERSION,
        "description": "AI-Powered Educational Roblox Environment - Generate immersive educational content with AI agents",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
    }
    
    # Add lifespan if not skipped
    if not skip_lifespan:
        # Import the actual lifespan from main module
        # This is done here to avoid circular imports
        try:
            from .main import lifespan
            app_config["lifespan"] = lifespan
            logger.debug("Using full lifespan context manager")
        except ImportError as e:
            logger.warning(f"Could not import lifespan: {e}")
            app_config["lifespan"] = empty_lifespan
    else:
        app_config["lifespan"] = empty_lifespan
        logger.debug("Skipping lifespan context manager")
    
    # Create the app
    app = FastAPI(**app_config)
    
    # Store configuration flags in app state
    app.state.testing_mode = testing_mode
    app.state.skip_sentry = skip_sentry
    app.state.skip_lifespan = skip_lifespan
    
    return app


def create_test_app() -> FastAPI:
    """
    Create a FastAPI app specifically for testing.
    
    This app skips all startup operations and external dependencies.
    """
    return create_app(
        skip_lifespan=True,
        skip_sentry=True,
        testing_mode=True
    )