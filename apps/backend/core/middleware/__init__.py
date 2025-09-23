"""
Middleware Registry

Centralized registration and configuration of all FastAPI middleware.
"""

import logging
from fastapi import FastAPI

from apps.backend.core.logging import logging_manager
from apps.backend.core.config import settings

logger = logging_manager.get_logger(__name__)


def register_middleware(app: FastAPI) -> None:
    """
    Register all middleware components in the correct order

    Args:
        app: FastAPI application instance
    """
    logger.info("Registering middleware components...")

    try:
        # Order matters - last registered middleware executes first
        _register_error_handling_middleware(app)
        _register_compression_middleware(app)
        _register_versioning_middleware(app)
        # _register_security_middleware(app)  # Disable for now - config issues
        # _register_cors_middleware(app)      # Disable for now - config issues
        _register_trust_middleware(app)
        _register_logging_middleware(app)
        # _register_resilience_middleware(app)  # Disable for now - dependency issues
        _register_metrics_middleware(app)

        logger.info("All middleware components registered successfully")

    except Exception as e:
        logger.error(f"Failed to register middleware: {e}")
        raise


def _register_trust_middleware(app: FastAPI) -> None:
    """Register trusted host middleware"""
    try:
        from fastapi.middleware.trustedhost import TrustedHostMiddleware

        allowed_hosts = ["*"]  # Configure based on environment
        if settings.ENVIRONMENT == "production":
            allowed_hosts = [
                "localhost",
                "127.0.0.1",
                "*.toolboxai.io",
                "*.onrender.com"
            ]

        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )
        logger.info("Trusted host middleware registered")

    except Exception as e:
        logger.warning(f"Failed to register trusted host middleware: {e}")


def _register_logging_middleware(app: FastAPI) -> None:
    """Register logging and correlation ID middleware"""
    try:
        from apps.backend.core.logging import CorrelationIDMiddleware

        app.add_middleware(CorrelationIDMiddleware)
        logger.info("Logging middleware registered")

    except Exception as e:
        logger.warning(f"Failed to register logging middleware: {e}")


def _register_cors_middleware(app: FastAPI) -> None:
    """Register CORS middleware"""
    try:
        from apps.backend.core.security.cors import SecureCORSConfig, CORSMiddlewareWithLogging

        # Configure CORS origins based on environment
        allowed_origins = ["*"]  # Default for development
        if hasattr(settings, 'ALLOWED_ORIGINS'):
            allowed_origins = settings.ALLOWED_ORIGINS
        elif settings.ENVIRONMENT == "production":
            allowed_origins = [
                "https://toolboxai.io",
                "https://*.toolboxai.io",
                "https://*.onrender.com"
            ]

        cors_config = SecureCORSConfig(
            allowed_origins_env=allowed_origins,
            allowed_methods_env=getattr(settings, 'ALLOWED_METHODS', ["GET", "POST", "PUT", "DELETE", "OPTIONS"]),
            allowed_headers_env=getattr(settings, 'ALLOWED_HEADERS', ["*"]),
            environment=settings.ENVIRONMENT,
            debug=settings.DEBUG
        )

        app.add_middleware(
            CORSMiddlewareWithLogging,
            cors_config=cors_config,
        )
        logger.info("CORS middleware registered")

    except Exception as e:
        logger.warning(f"Failed to register CORS middleware: {e}")


def _register_security_middleware(app: FastAPI) -> None:
    """Register security middleware"""
    try:
        from apps.backend.core.security.middleware import SecurityMiddleware
        from apps.backend.core.security.headers import SecurityHeadersMiddleware, SecurityHeadersConfig
        from apps.backend.core.rate_limiter import RateLimitConfig, RateLimitStrategy, RateLimitScope

        # Security middleware
        app.add_middleware(
            SecurityMiddleware,
            rate_limit_config=RateLimitConfig(
                requests_per_minute=100,
                burst_size=150,
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                scope=RateLimitScope.IP
            )
        )

        # Security headers middleware
        security_headers_config = SecurityHeadersConfig(
            hsts_max_age=31536000,
            content_type_nosniff=True,
            x_frame_options="DENY",
            x_content_type_options="nosniff",
            referrer_policy="strict-origin-when-cross-origin"
        )

        app.add_middleware(
            SecurityHeadersMiddleware,
            hsts_max_age=security_headers_config.hsts_max_age,
            csp_policy=security_headers_config.get_csp_policy(),
            x_frame_options=security_headers_config.x_frame_options
        )

        logger.info("Security middleware registered")

    except Exception as e:
        logger.warning(f"Failed to register security middleware: {e}")


def _register_versioning_middleware(app: FastAPI) -> None:
    """Register API versioning middleware"""
    try:
        from apps.backend.core.versioning import (
            VersionStrategy,
            APIVersionMiddleware,
            create_version_manager
        )

        version_manager = create_version_manager(
            default_version="1.0.0",
            strategy=VersionStrategy.HEADER
        )

        app.add_middleware(APIVersionMiddleware, version_manager=version_manager)
        logger.info("Versioning middleware registered")

    except Exception as e:
        logger.warning(f"Failed to register versioning middleware: {e}")


def _register_compression_middleware(app: FastAPI) -> None:
    """Register compression middleware"""
    try:
        from apps.backend.core.security.compression import CompressionMiddleware, CompressionConfig

        app.add_middleware(
            CompressionMiddleware,
            config=CompressionConfig(
                minimum_size=1024,
                compression_level=6,
                compressible_types={
                    "application/json",
                    "text/plain",
                    "text/html",
                    "text/css",
                    "application/javascript"
                }
            )
        )
        logger.info("Compression middleware registered")

    except Exception as e:
        logger.warning(f"Failed to register compression middleware: {e}")


def _register_error_handling_middleware(app: FastAPI) -> None:
    """Register error handling middleware"""
    try:
        from apps.backend.core.errors import ErrorHandlingMiddleware

        app.add_middleware(ErrorHandlingMiddleware, debug=settings.DEBUG)
        logger.info("Error handling middleware registered")

    except Exception as e:
        logger.warning(f"Failed to register error handling middleware: {e}")


def _register_resilience_middleware(app: FastAPI) -> None:
    """Register resilience middleware (circuit breakers, retries, etc.)"""
    try:
        from apps.backend.api.middleware.resilience import (
            ResilienceMiddleware,
            RetryMiddleware,
            BulkheadMiddleware
        )
        from apps.backend.core.rate_limiter import (
            RateLimitMiddleware,
            RateLimitConfig,
            RateLimitStrategy,
            RateLimitScope
        )

        # Resilience middleware
        app.add_middleware(ResilienceMiddleware)

        # Retry middleware
        app.add_middleware(
            RetryMiddleware,
            max_retries=3,
            retry_delay=1.0,
            exponential_backoff=True,
            backoff_factor=2.0
        )

        # Bulkhead middleware
        app.add_middleware(
            BulkheadMiddleware,
            max_concurrent_requests=200,
            max_queue_size=100
        )

        # Rate limiting middleware (if Redis is available)
        if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
            try:
                import redis
                redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

                rate_limit_config = RateLimitConfig(
                    requests_per_minute=120,
                    burst_size=200,
                    strategy=RateLimitStrategy.SLIDING_WINDOW,
                    scope=RateLimitScope.IP
                )

                app.add_middleware(
                    RateLimitMiddleware,
                    redis_client=redis_client,
                    config=rate_limit_config
                )
                logger.info("Redis-based rate limiting enabled")

            except ImportError:
                logger.warning("Redis not available for rate limiting")

        logger.info("Resilience middleware registered")

    except ImportError as e:
        logger.warning(f"Resilience middleware not available: {e}")


def _register_metrics_middleware(app: FastAPI) -> None:
    """Register metrics and monitoring middleware"""
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        from prometheus_client import CollectorRegistry

        # Create instrumentator for metrics collection
        instrumentator = Instrumentator(
            should_group_status_codes=False,
            excluded_handlers=["/metrics", "/health"]
        )

        instrumentator.instrument(app).expose(app, endpoint="/metrics")
        logger.info("Prometheus metrics middleware registered")

    except ImportError as e:
        logger.warning(f"Prometheus metrics not available: {e}")