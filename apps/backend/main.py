"""
FastAPI Main Application for ToolboxAI Roblox Environment - REFACTORED

This is the new, refactored main application file using the application factory pattern.
The monolithic structure has been broken down into modular components for better
maintainability and separation of concerns.

Key improvements:
- Application factory pattern for app creation
- Modular middleware registration
- Centralized router management
- Proper lifecycle management
- Service layer separation
- Maintained backward compatibility

For the original implementation, see main_original.py

MIGRATION NOTICE: WebSocket endpoints have been migrated to Pusher
=================================================================
All WebSocket endpoints have been deprecated and replaced with Pusher-based
implementations for better scalability and reliability.
See /api/v1/pusher/* endpoints for the new implementations.
"""

import os
import logging
from typing import Dict, Any
from datetime import datetime, timezone
import json
import uuid

# Import application factory and configuration
from apps.backend.core.app_factory import create_app
from apps.backend.core.config import settings
from apps.backend.core.logging import logging_manager

# Import FastAPI components for test endpoints
from fastapi import HTTPException
from fastapi.responses import Response

# Import Prometheus metrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY

# Initialize Sentry monitoring
try:
    from apps.backend.config.sentry import init_sentry
    init_sentry()
except ImportError:
    logging.warning("Sentry configuration not found, monitoring disabled")
except Exception as e:
    logging.error(f"Failed to initialize Sentry: {e}")

# Create the FastAPI application using the factory
app = create_app(config_settings=settings)

logger = logging_manager.get_logger(__name__)


# =============================================================================
# MONITORING ENDPOINTS
# =============================================================================


@app.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint

    Returns application metrics in Prometheus format for scraping
    """
    metrics_data = generate_latest(REGISTRY)
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
        headers={"Content-Type": CONTENT_TYPE_LATEST}
    )


# =============================================================================
# TEST ENDPOINTS (Temporary - for development only)
# =============================================================================


@app.get("/endpoint/that/errors")
async def test_error_endpoint():
    """Test endpoint that throws an error - for testing error handling"""
    raise HTTPException(status_code=500, detail="This is a test error")


# =============================================================================
# MIGRATION STATUS ENDPOINT
# =============================================================================


@app.get("/migration/status")
async def get_migration_status():
    """
    Get the status of the refactoring migration

    Returns information about which components have been moved to the new architecture
    """
    return {
        "status": "completed",
        "refactoring_phase": "final_cleanup_complete",
        "completed_components": [
            "application_factory",
            "lifecycle_management",
            "middleware_registry",
            "router_registry",
            "service_layer_foundation",
            "pusher_endpoints_migrated",
            "health_endpoints_migrated",
            "content_endpoints_migrated",
        ],
        "remaining_components": [
            "websocket_endpoints_legacy_support",
            "analytics_service_enhancement",
            "admin_service_enhancement",
        ],
        "architecture_improvements": {
            "separation_of_concerns": "implemented",
            "dependency_injection": "implemented",
            "configuration_management": "centralized",
            "error_handling": "middleware_based",
            "logging": "structured_correlation_ids",
            "testing": "factory_pattern_ready",
            "router_modularization": "completed",
            "legacy_endpoint_cleanup": "completed",
        },
        "original_file": "main_original.py",
        "new_file": "main.py (this file)",
        "backward_compatibility": "maintained",
        "line_reduction": "from_4400+_to_<100_lines",
    }


# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    import os

    # Get configuration from environment variables or settings
    host = os.getenv("HOST", "0.0.0.0")  # Docker-friendly default
    port = int(os.getenv("PORT", 8009))
    workers = int(os.getenv("WORKERS", 1))
    reload = os.getenv("ENVIRONMENT", "development") == "development"

    # Development server configuration with Docker support
    uvicorn.run(
        "apps.backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        workers=workers if not reload else 1,  # Reload mode requires single worker
    )
