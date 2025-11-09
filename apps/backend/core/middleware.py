"""
Centralized middleware configuration for the FastAPI application
"""

import time
import uuid
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from apps.backend.core.config import settings
from apps.backend.core.logging import logging_manager, CorrelationIDMiddleware
from apps.backend.core.security.cors import SecureCORSConfig, CORSMiddlewareWithLogging
from apps.backend.core.security.headers import SecurityHeadersMiddleware, SecurityHeadersConfig
from apps.backend.core.security.compression import CompressionMiddleware, CompressionConfig
from apps.backend.core.errors import ErrorHandlingMiddleware
from apps.backend.core.versioning import (
    APIVersionMiddleware,
    create_version_manager,
    VersionStrategy,
)

# Initialize logger
logger = logging_manager.get_logger(__name__)

# Import resilience middleware if available
try:
    from apps.backend.api.middleware.resilience import (
        ResilienceMiddleware,
        RetryMiddleware,
        BulkheadMiddleware,
    )
    from apps.backend.core.rate_limiter import RateLimitMiddleware, RateLimitConfig

    RESILIENCE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Resilience middleware not available: {e}")
    RESILIENCE_AVAILABLE = False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Start timing
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra_fields={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra_fields={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "response_size": response.headers.get("content-length", "unknown"),
                },
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time

            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra_fields={
                    "request_id": request_id,
                    "process_time": process_time,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            raise


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting application metrics"""

    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.total_processing_time = 0.0
        self.error_count = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Increment request counter
        self.request_count += 1

        start_time = time.time()

        try:
            response = await call_next(request)

            # Update metrics
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time

            # Log metrics periodically (every 100 requests)
            if self.request_count % 100 == 0:
                avg_response_time = self.total_processing_time / self.request_count
                logger.info(
                    "Application metrics update",
                    extra_fields={
                        "total_requests": self.request_count,
                        "total_errors": self.error_count,
                        "avg_response_time": avg_response_time,
                        "error_rate": self.error_count / self.request_count,
                    },
                )

            return response

        except Exception as e:
            self.error_count += 1
            raise


def configure_cors_middleware(app: FastAPI) -> None:
    """Configure CORS middleware with support for Vercel and Render deployments"""
    try:
        # Parse CORS origins from settings
        cors_origins = []
        if hasattr(settings, 'CORS_ORIGINS'):
            if isinstance(settings.CORS_ORIGINS, str):
                cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(',') if origin.strip()]
            elif isinstance(settings.CORS_ORIGINS, list):
                cors_origins = settings.CORS_ORIGINS

        # Always include development origins
        development_origins = [
            "http://localhost:5179",
            "http://127.0.0.1:5179",
            "http://localhost:5180",
            "http://127.0.0.1:5180",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8009",
            "http://127.0.0.1:8009",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
        cors_origins.extend(development_origins)

        # Add deployment URLs
        deployment_origins = [
            "https://toolboxai-backend-8j12.onrender.com",
            "https://toolboxai-dashboard.vercel.app",
            "https://toolboxai.com",
            "https://app.toolboxai.com",
        ]
        cors_origins.extend(deployment_origins)

        # Check for wildcard Vercel domains
        has_vercel_wildcard = any('*.vercel.app' in origin for origin in cors_origins)

        # Remove wildcards (CORS doesn't support them, we'll use allow_origin_regex instead)
        cors_origins = [origin for origin in cors_origins if '*' not in origin]

        # Remove duplicates while preserving order
        cors_origins = list(dict.fromkeys(cors_origins))

        logger.info(f"Configuring CORS with {len(cors_origins)} origins")
        if has_vercel_wildcard:
            logger.info("Vercel wildcard detected - will use allow_origin_regex for *.vercel.app")

        # Use secure CORS configuration with wildcard support for Vercel
        middleware_kwargs = {
            "allow_origins": cors_origins,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
            "allow_headers": [
                "Authorization",
                "Content-Type",
                "X-Requested-With",
                "Accept",
                "Origin",
                "Access-Control-Request-Method",
                "Access-Control-Request-Headers",
                "X-Request-ID",
                "X-Correlation-ID",
                "X-CSRF-Token",
                "X-API-Key",
                "Cache-Control",
                "Pragma",
            ],
            "expose_headers": [
                "X-Request-ID",
                "X-Process-Time",
                "X-Rate-Limit-Remaining",
                "X-Rate-Limit-Reset",
                "X-Total-Count",
                "Content-Length",
                "Content-Type",
            ],
            "max_age": 3600,  # 1 hour for preflight caching (reduced for dev)
        }

        # Add regex pattern for Vercel deployments if needed
        if has_vercel_wildcard:
            middleware_kwargs["allow_origin_regex"] = r"https://.*\.vercel\.app"

        app.add_middleware(CORSMiddleware, **middleware_kwargs)
        logger.info("✅ CORS middleware configured successfully")
    except Exception as e:
        logger.error(f"❌ Failed to configure CORS middleware: {e}")
        # Fallback to permissive CORS for development
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins in fallback
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.warning("⚠️ Using permissive fallback CORS configuration")


def configure_security_middleware(app: FastAPI) -> None:
    """Configure security middleware"""
    try:
        # Security headers
        security_config = SecurityHeadersConfig(
            csp_policy="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            hsts_max_age=31536000,
            frame_options="SAMEORIGIN",
        )
        app.add_middleware(SecurityHeadersMiddleware, config=security_config)

        # Trusted host middleware
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=(
                ["*"] if settings.DEBUG else ["localhost", "127.0.0.1", settings.FASTAPI_HOST]
            ),
        )

        logger.info("Security middleware configured")
    except Exception as e:
        logger.error(f"Failed to configure security middleware: {e}")


def configure_compression_middleware(app: FastAPI) -> None:
    """Configure compression middleware"""
    try:
        compression_config = CompressionConfig(minimum_size=1000, compression_level=6)
        app.add_middleware(CompressionMiddleware, config=compression_config)
        logger.info("Compression middleware configured")
    except Exception as e:
        logger.error(f"Failed to configure compression middleware: {e}")


def configure_resilience_middleware(app: FastAPI) -> None:
    """Configure resilience middleware if available"""
    if not RESILIENCE_AVAILABLE:
        logger.warning("Resilience middleware not available")
        return

    try:
        # Rate limiting
        rate_limit_config = RateLimitConfig(
            requests_per_minute=settings.RATE_LIMIT_PER_MINUTE, burst_size=100
        )
        app.add_middleware(RateLimitMiddleware, config=rate_limit_config)

        # Resilience patterns
        app.add_middleware(ResilienceMiddleware)
        app.add_middleware(RetryMiddleware, max_retries=3)
        app.add_middleware(BulkheadMiddleware, max_concurrent=100)

        logger.info("Resilience middleware configured")
    except Exception as e:
        logger.error(f"Failed to configure resilience middleware: {e}")


def configure_versioning_middleware(app: FastAPI) -> None:
    """Configure API versioning middleware"""
    try:
        version_manager = create_version_manager(
            default_version="2.0.0", strategy=VersionStrategy.URL_PATH
        )
        app.add_middleware(APIVersionMiddleware, version_manager=version_manager)
        logger.info("API versioning middleware configured")
    except Exception as e:
        logger.error(f"Failed to configure versioning middleware: {e}")


def configure_all_middleware(app: FastAPI) -> None:
    """Configure all middleware in the correct order"""
    logger.info("Configuring application middleware...")

    # 1. CORS (MUST be first to handle preflight OPTIONS requests)
    configure_cors_middleware(app)

    # 2. Error handling
    app.add_middleware(ErrorHandlingMiddleware, debug=settings.DEBUG)

    # 3. API Gateway (routing, versioning, circuit breakers)
    try:
        from apps.backend.middleware.api_gateway import APIGatewayMiddleware
        app.add_middleware(APIGatewayMiddleware)
        logger.info("API Gateway middleware configured")
    except ImportError as e:
        logger.warning(f"API Gateway middleware not available: {e}")

    # 4. Request Validation (security checks, input sanitization)
    try:
        from apps.backend.middleware.request_validator import RequestValidatorMiddleware
        app.add_middleware(RequestValidatorMiddleware)
        logger.info("Request Validator middleware configured")
    except ImportError as e:
        logger.warning(f"Request Validator middleware not available: {e}")

    # 5. Tenant Middleware
    try:
        from apps.backend.middleware.tenant_middleware import TenantMiddleware
        app.add_middleware(TenantMiddleware)
        logger.info("Tenant middleware configured")
    except ImportError as e:
        logger.warning(f"Tenant middleware not available: {e}")

    # 6. Security middleware
    configure_security_middleware(app)

    # 6. Logging and correlation ID
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # 7. Metrics collection (including Prometheus)
    app.add_middleware(MetricsMiddleware)

    # Add Prometheus middleware if available
    try:
        from apps.backend.middleware.prometheus_middleware import PrometheusMiddleware
        app.add_middleware(PrometheusMiddleware)
        logger.info("Prometheus middleware configured")
    except ImportError as e:
        logger.warning(f"Prometheus middleware not available: {e}")

    # 8. Versioning
    configure_versioning_middleware(app)

    # 9. Response Transformation (should be late for final formatting)
    try:
        from apps.backend.middleware.response_transformer import ResponseTransformerMiddleware
        app.add_middleware(ResponseTransformerMiddleware)
        logger.info("Response Transformer middleware configured")
    except ImportError as e:
        logger.warning(f"Response Transformer middleware not available: {e}")

    # 10. Compression (should be late in chain)
    configure_compression_middleware(app)

    # 11. Resilience (rate limiting, circuit breakers, etc.)
    configure_resilience_middleware(app)

    logger.info("All middleware configured successfully")


# Optional: Middleware health check
def get_middleware_status() -> dict:
    """Get status of all configured middleware"""
    return {
        "cors": True,
        "security": True,
        "logging": True,
        "metrics": True,
        "compression": True,
        "versioning": True,
        "resilience": RESILIENCE_AVAILABLE,
        "error_handling": True,
        "api_gateway": True,
        "request_validation": True,
        "response_transformation": True,
    }


# Alias for app_factory compatibility
register_middleware = configure_all_middleware
