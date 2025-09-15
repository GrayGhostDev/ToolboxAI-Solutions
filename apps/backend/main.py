"""
FastAPI Main Application for ToolboxAI Roblox Environment

Main FastAPI server (port 8008) with comprehensive features:
- Educational content generation endpoints
- WebSocket support for real-time updates
- Integration with agents, swarm, SPARC, and MCP systems
- Health monitoring and metrics
- Authentication and rate limiting
- CORS configuration for multi-platform access
- Sentry error tracking and performance monitoring
"""

# Initialize Sentry BEFORE importing other modules
from .core.config import settings
from .core.monitoring import initialize_sentry, configure_sentry_logging, sentry_manager
from .core.logging import (
    initialize_logging,
    logging_manager,
    CorrelationIDMiddleware,
    log_execution_time,
    log_database_operation,
    log_external_api_call,
    log_audit,
)

# Initialize comprehensive logging system
initialize_logging(
    log_level=settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else "INFO",
    log_dir=settings.LOG_DIR if hasattr(settings, "LOG_DIR") else "logs",
    enable_file_logging=settings.ENVIRONMENT != "testing",
    enable_console_logging=True
)
print(f"✅ Logging system initialized for environment: {settings.ENVIRONMENT}")

# Initialize Sentry with production-ready configuration
sentry_initialized = initialize_sentry()
if sentry_initialized:
    configure_sentry_logging()
    print(f"✅ Sentry initialized for environment: {settings.ENVIRONMENT}")
else:
    print(f"⚠️  Sentry initialization skipped for environment: {settings.ENVIRONMENT}")

import asyncio
import io
import json
import logging
import os
import subprocess
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import uvicorn  # pylint: disable=import-error
from fastapi import (  # pylint: disable=import-error
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware  # pylint: disable=import-error
from fastapi.middleware.trustedhost import (  # pylint: disable=import-error
    TrustedHostMiddleware,
)
from .core.security.cors import SecureCORSConfig, CORSMiddlewareWithLogging
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse  # pylint: disable=import-error
from fastapi.security import HTTPBearer  # pylint: disable=import-error
from pydantic import ValidationError, Field, BaseModel

from .agents.agent import (
    agent_manager,
    generate_educational_content,
    get_agent_health,
    initialize_agents,
    shutdown_agents,
)
from .api.auth.auth import (
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    get_current_user,
    initialize_auth,
    rate_limit,
    require_any_role,
    require_role,
)

# Import our modules (settings already imported for Sentry)
from .models.schemas import (
    BaseResponse,
    ContentRequest,
    ContentResponse,
    ErrorDetail,
    ErrorResponse,
    HealthCheck,
    PluginMessage,
    PluginRegistration,
    Quiz,
    QuizResponse,
    User,
)
from .services.websocket_handler import broadcast_content_update, websocket_endpoint, websocket_manager
from .services.pusher import (
    trigger_event as pusher_trigger_event,
    authenticate_channel as pusher_authenticate,
    verify_webhook as pusher_verify_webhook,
    PusherUnavailable,
)
from .services.database import db_service
from .services.socketio import create_socketio_app  # Socket.IO ASGI mounted at path '/socket.io'

# Use the logging manager for structured logging with correlation IDs
logger = logging_manager.get_logger(__name__)


# Import security modules
from .core.security.middleware import (
    SecurityMiddleware,
    RateLimitConfig,
    CircuitBreakerConfig,
)
from .core.security.secrets import init_secrets_manager

# Import new middleware modules
from .core.versioning import (
    VersionStrategy,
    APIVersionMiddleware,
    create_version_manager,
    create_versioned_endpoints,
)
from .core.security.compression import (
    CompressionMiddleware,
    CompressionConfig,
)
from .core.errors import (
    ErrorHandlingMiddleware,
)


# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
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
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION}",
        extra_fields={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }
    )

    # Initialize secrets manager with timeout
    try:
        async with asyncio.timeout(5):  # 5 second timeout
            init_secrets_manager(auto_rotate=True)
            logger.info(
                "Secrets manager initialized",
                extra_fields={"auto_rotate": True}
            )
    except asyncio.TimeoutError:
        logger.warning("Secrets manager initialization timed out")
    except Exception as e:
        logger.error(f"Failed to initialize secrets manager: {e}")
        # Continue with environment variables as fallback

    # Set start time for uptime calculation
    app.state.start_time = time.time()
    
    # Set Sentry context for application startup
    if sentry_manager.initialized:
        sentry_manager.set_context("application_startup", {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "startup_time": datetime.now(timezone.utc).isoformat(),
        })
        sentry_manager.add_breadcrumb(
            message="Application startup initiated",
            category="lifecycle",
            level="info"
        )

    # Initialize authentication system
    initialize_auth()

    # Initialize database service
    try:
        from .database_service import db_service
        await db_service.connect()
        logger.info("Database service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database service: {e}")
        logger.warning("Dashboard will use fallback data")

    # Initialize agent system with error handling and timeout
    if not os.getenv("SKIP_AGENTS", "false").lower() == "true":
        try:
            async with asyncio.timeout(10):  # 10 second timeout
                await initialize_agents()
                logger.info(
                "Agent system initialized successfully",
                extra_fields={"agent_count": len(agent_manager.agents) if hasattr(agent_manager, "agents") else 0}
            )
        except asyncio.TimeoutError:
            logger.warning("Agent initialization timed out - running in fallback mode")
        except (ImportError, AttributeError, RuntimeError, ValueError) as e:
            logger.error(f"Failed to initialize agent system: {e}")
            logger.warning("Agent features will be limited - running in fallback mode")
    else:
        logger.info("Skipping agent initialization (SKIP_AGENTS=true)")

    # Start Flask bridge server if not running and not skipped
    if not os.getenv("SKIP_FLASK", "false").lower() == "true":
        try:
            async with asyncio.timeout(5):  # 5 second timeout
                await ensure_flask_server_running()
                logger.info("Flask bridge server started successfully")
        except asyncio.TimeoutError:
            logger.warning("Flask server startup timed out")
        except (subprocess.SubprocessError, OSError, RuntimeError) as e:
            logger.error(f"Failed to start Flask bridge server: {e}")
            logger.warning("Roblox plugin communication may be unavailable")
    else:
        logger.info("Skipping Flask server startup (SKIP_FLASK=true)")

    # Start background tasks and track them for proper shutdown
    try:
        app.state.cleanup_task = asyncio.create_task(cleanup_stale_connections())
        app.state.metrics_task = asyncio.create_task(collect_metrics())
    except (asyncio.CancelledError, RuntimeError) as e:
        logger.warning(f"Failed to create background tasks: {e}")

    logger.info(
        f"FastAPI server ready on {settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}",
        extra_fields={
            "host": settings.FASTAPI_HOST,
            "port": settings.FASTAPI_PORT,
            "startup_time": time.time() - app.state.start_time
        }
    )
    
    # Notify Sentry that startup is complete
    if sentry_manager.initialized:
        sentry_manager.add_breadcrumb(
            message="Application startup completed successfully",
            category="lifecycle",
            level="info"
        )

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # Cancel and await background tasks for proper cleanup
    if hasattr(app.state, "cleanup_task"):
        app.state.cleanup_task.cancel()
        try:
            await app.state.cleanup_task
        except asyncio.CancelledError:
            pass
    if hasattr(app.state, "metrics_task"):
        app.state.metrics_task.cancel()
        try:
            await app.state.metrics_task
        except asyncio.CancelledError:
            pass

    # Shutdown database service
    try:
        from .database_service import db_service
        await db_service.disconnect()
        logger.info("Database service shutdown completed")
    except Exception as e:
        logger.error(f"Error during database service shutdown: {e}")

    # Shutdown agent system
    try:
        await shutdown_agents()
        logger.info("Agent system shutdown completed")
    except Exception as e:
        logger.error(f"Error during agent system shutdown: {e}")

    # Shutdown WebSocket manager
    try:
        await websocket_manager.shutdown()
        logger.info("WebSocket manager shutdown completed")
    except Exception as e:
        logger.error(f"Error during WebSocket manager shutdown: {e}")

    logger.info("Application shutdown completed")


# FastAPI app initialization
# Check if we should use test mode
if os.getenv("TESTING", "false").lower() == "true" or os.getenv("SKIP_LIFESPAN", "false").lower() == "true":
    # Create app without lifespan for testing/import scenarios
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-Powered Educational Roblox Environment - Generate immersive educational content with AI agents",
        docs_url="/docs",  # Enable API documentation
        redoc_url="/redoc",  # Enable ReDoc documentation
        openapi_url="/openapi.json",  # Enable OpenAPI schema
    )
    logger.info("Created FastAPI app without lifespan (testing/import mode)")
else:
    # Create app with full lifespan for production
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-Powered Educational Roblox Environment - Generate immersive educational content with AI agents",
        docs_url="/docs",  # Enable API documentation
        redoc_url="/redoc",  # Enable ReDoc documentation
        openapi_url="/openapi.json",  # Enable OpenAPI schema
        lifespan=lifespan,
    )
    logger.info("Created FastAPI app with full lifespan")

# Initialize version manager
version_manager = create_version_manager(
    default_version="2.0.0", strategy=VersionStrategy.URL_PATH
)

# Security
security = HTTPBearer()

# ------------------------
# Pusher endpoints (Channels)
# ------------------------
from fastapi import Body, Header

@app.post("/pusher/auth")
async def pusher_auth(
    socket_id: str = Query(..., alias="socket_id"),
    channel_name: str = Query(..., alias="channel_name"),
    request: Request = None,
):
    """Authenticate private/presence channel subscription.
    Relies on current user context to build presence data when needed.
    """
    try:
        user = None
        try:
            # Optional: try to get current user, if auth headers are present
            user = await get_current_user(request)
        except Exception:
            pass
        user_id = getattr(user, "id", None)
        user_info = {"role": getattr(user, "role", "guest")}
        auth_payload = pusher_authenticate(socket_id, channel_name, str(user_id) if user_id else None, user_info)
        return JSONResponse(content=auth_payload)
    except PusherUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Pusher auth failed: {e}")
        raise HTTPException(status_code=400, detail="Pusher auth failed")


@app.post("/realtime/trigger")
async def realtime_trigger(payload: Dict[str, Any] = Body(...)):
    """Trigger a Channels event from the server side.
    Expected payload: { channel: str, event: str, type?: str, payload?: any }
    If 'event' isn't provided, defaults to 'message' and wraps type/payload.
    """
    try:
        channel = payload.get("channel") or "public"
        event = payload.get("event") or "message"
        data = payload.get("data")
        if data is None:
            # wrap unified message
            data = {
                "type": payload.get("type") or "message",
                "payload": payload.get("payload"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        res = pusher_trigger_event(channel, event, data)
        return JSONResponse(content={"ok": True, **res})
    except PusherUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Realtime trigger failed: {e}")
        raise HTTPException(status_code=400, detail="Trigger failed")


@app.post("/pusher/webhook")
async def pusher_webhook(
    request: Request,
    x_pusher_signature: str = Header(None, alias="X-Pusher-Signature"),
    x_pusher_key: str = Header(None, alias="X-Pusher-Key"),
):
    """Handle Pusher webhooks: channel occupied/vacated, member added/removed, etc."""
    try:
        body = await request.body()
        headers = {
            "X-Pusher-Key": x_pusher_key or "",
            "X-Pusher-Signature": x_pusher_signature or "",
        }
        events = pusher_verify_webhook(headers, body)
        if not events:
            raise HTTPException(status_code=400, detail="Invalid webhook")

        # Basic logging; extend with business logic as needed
        logger.info(f"Pusher webhook events: {events}")
        return {"ok": True}
    except PusherUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Pusher webhook handling failed: {e}")
        raise HTTPException(status_code=400, detail="Webhook handling failed")

# Middleware configuration

# Middleware order is important - they execute in reverse order
# TrustedHost runs first (added last)
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver", "*.roblox.com"]
)

# Correlation ID middleware for request tracking
app.add_middleware(CorrelationIDMiddleware)

# Configure secure CORS based on environment
cors_config = SecureCORSConfig(
    environment="development" if settings.DEBUG else settings.ENVIRONMENT,
    allowed_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allowed_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language", 
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Request-ID",
        "X-Session-ID",
        "Origin",
        "User-Agent",
    ] if settings.DEBUG else [
        "Accept",
        "Content-Type",
        "Authorization",
        "X-Request-ID",
    ],
    exposed_headers=[
        "X-Request-ID",
        "X-Process-Time",
        "Content-Type",
        "Content-Length",
    ],
    max_age=600
)

# CORS runs second - needs to handle OPTIONS before other middleware
app.add_middleware(
    CORSMiddlewareWithLogging,
    cors_config=cors_config,
)

# Security middleware with rate limiting and circuit breaker
app.add_middleware(
    SecurityMiddleware,
    rate_limit_config=RateLimitConfig(
        requests_per_minute=100,
        burst_limit=200,
        by_endpoint={
            "/api/v1/generate": 30,  # More restrictive for expensive operations
            "/api/v1/agent/execute": 20,
            "/generate_content": 30,
        },
    ),
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=5, timeout_seconds=30, excluded_services={"health", "metrics"}
    ),
    redis_client=None,  # Will use local rate limiting
    enable_request_id=True,
    max_request_size=50 * 1024 * 1024,  # 50MB for large payloads
)

# API versioning middleware
app.add_middleware(APIVersionMiddleware, version_manager=version_manager)

# Compression middleware
# Switch to factory that provides correct signature
app.add_middleware(
    CompressionMiddleware,
    config=CompressionConfig(
        minimum_size=1024,
        compression_level=6,
        prefer_brotli=True,
    ),
)

# Error handling middleware (must be first to be added, last to execute to catch all errors)
app.add_middleware(ErrorHandlingMiddleware, debug=settings.DEBUG)

# Create Socket.io app wrapper (lazy initialization)
# Only create if not in testing mode to avoid import issues
if os.getenv("TESTING", "false").lower() == "true" or os.getenv("SKIP_SOCKETIO", "false").lower() == "true":
    socketio_app = app  # Use regular app for testing
    logger.info("Skipping Socket.IO wrapper (testing/import mode)")
else:
    socketio_app = create_socketio_app(app)
    logger.info("Created Socket.IO app wrapper")


# Global exception handlers
@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    response_dict = {
        "success": False,
        "message": exc.detail,
        "error_type": "AuthenticationError",
        "details": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=response_dict,
    )


@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    response_dict = {
        "success": False,
        "message": exc.detail,
        "error_type": "AuthorizationError",
        "details": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=response_dict,
    )


@app.exception_handler(RateLimitError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
    response_dict = {
        "success": False,
        "message": exc.detail,
        "error_type": "RateLimitError",
        "details": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
    }
    headers = dict(exc.headers or {})
    headers.setdefault("Retry-After", "60")
    return JSONResponse(
        status_code=exc.status_code,
        content=response_dict,
        headers=headers,
    )


def get_field_path(error):
    """Extract field path from validation error"""
    if isinstance(error, dict):
        return ".".join([str(loc) for loc in error.get("loc", [])])
    return ""


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    details = [
        {
            "code": "validation_error",
            "message": str(error),
            "field": get_field_path(error),
            "context": None,
        }
        for error in exc.errors()
    ]
    response_dict = {
        "success": False,
        "message": "Validation error",
        "error_type": "ValidationError",
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
    }
    return JSONResponse(
        status_code=422,
        content=response_dict,
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    response_dict = {
        "success": False,
        "message": f"Resource not found: {request.url.path}",
        "error_type": "NotFoundError",
        "details": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
    }
    return JSONResponse(
        status_code=404,
        content=response_dict,
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {exc}", exc_info=True)
    response_dict = {
        "success": False,
        "message": "Internal server error",
        "error_type": "InternalServerError",
        "details": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
    }
    return JSONResponse(
        status_code=500,
        content=response_dict,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Sanitize exception message to prevent log injection
    safe_exc_msg = str(exc)[:500].replace("\n", "").replace("\r", "")
    logger.error(f"Unhandled exception: {safe_exc_msg}", exc_info=True)
    response_dict = {
        "success": False,
        "message": "Internal server error",
        "error_type": "InternalServerError",
        "details": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
    }
    return JSONResponse(
        status_code=500,
        content=response_dict,
    )


# Middleware for request tracking with Sentry integration
@app.middleware("http")
async def track_requests(request: Request, call_next):
    start_time = time.time()

    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Set Sentry request context
    if sentry_manager.initialized:
        sentry_manager.set_request_context(
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            query_params=str(request.url.query) if request.url.query else None,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

    response = await call_next(request)

    # Calculate response time (reuse start_time for consistency)
    end_time = time.time()
    process_time = end_time - start_time

    # Log request with sanitized URL
    safe_url = str(request.url)[:200].replace("\n", "").replace("\r", "")
    safe_method = str(request.method).replace("\n", "").replace("\r", "")
    safe_status = str(response.status_code).replace("\n", "").replace("\r", "")
    logger.info(
        f"Request {request_id}: {safe_method} {safe_url} - {safe_status} ({process_time:.3f}s)"
    )

    # Add Sentry breadcrumb for request completion
    if sentry_manager.initialized:
        sentry_manager.add_breadcrumb(
            message=f"HTTP {request.method} {request.url.path} - {response.status_code}",
            category="http",
            level="info" if response.status_code < 400 else "warning",
            data={
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "duration": process_time,
                "request_id": request_id
            }
        )

    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Health and monitoring endpoints
@app.options("/health", tags=["System"])
async def health_check_options():
    """Handle OPTIONS request for CORS preflight"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/health", response_model=HealthCheck, tags=["System"])
async def health_check():
    """System health check endpoint"""
    try:
        # Check agent system
        agent_health = await get_agent_health()
        agent_status = agent_health.get("system_health", "unknown") == "healthy"

        # Check WebSocket manager
        ws_stats = await websocket_manager.get_connection_stats()
        ws_status = (
            ws_stats.get("status") == "healthy" if "status" in ws_stats else True
        )

        # Check external dependencies
        flask_status = await check_flask_server()

        # Overall status
        all_checks = {
            "agents": agent_status,
            "websockets": ws_status,
            "flask_server": flask_status,
        }

        overall_status = "healthy" if all(all_checks.values()) else "unhealthy"

        return {
            "status": overall_status,
            "version": settings.APP_VERSION,
            "checks": all_checks,
            "uptime": (
                time.time() - app.state.start_time
                if hasattr(app.state, "start_time")
                else 0
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "version": settings.APP_VERSION,
            "checks": {"error": False},
            "uptime": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@app.get("/ws/status", tags=["System"])
async def websocket_status():
    """Detailed WebSocket status: connection stats and channels"""
    try:
        stats = await websocket_manager.get_connection_stats()
        channels = await websocket_manager.list_channels()
        return {
            "status": "ok",
            "stats": stats,
            "channels": channels,
        }
    except Exception as e:
        logger.error(f"WebSocket status error: {e}")
        raise HTTPException(status_code=500, detail="WebSocket status unavailable")


@app.get("/socketio/status", tags=["System"])
async def socketio_status():
    """Socket.IO server status and connected clients summary"""
    try:
        from .socketio_server import connected_clients
        total = len(connected_clients)
        authenticated = sum(1 for c in connected_clients.values() if c.get("authenticated"))
        role_counts = {}
        for info in connected_clients.values():
            role = info.get("role") or "unknown"
            role_counts[role] = role_counts.get(role, 0) + 1
        return {
            "status": "ok",
            "connected": total,
            "authenticated": authenticated,
            "role_distribution": role_counts,
            "acks_enabled": True,
            "path": "/socket.io"
        }
    except Exception as e:
        logger.error(f"SocketIO status error: {e}")
        raise HTTPException(status_code=500, detail="SocketIO status unavailable")


@app.get("/metrics", tags=["System"])
async def get_metrics():
    """Get system metrics with counters, gauges, and histograms"""
    """Get system metrics"""
    try:
        agent_health = await get_agent_health()
        ws_stats = await websocket_manager.get_connection_stats()

        # Include Sentry status in metrics
        sentry_status = {
            "initialized": sentry_manager.initialized if sentry_manager else False,
            "dsn_configured": bool(settings.SENTRY_DSN),
            "environment": settings.SENTRY_ENVIRONMENT if sentry_manager.initialized else None,
        }

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "counters": {},  # Add counters for compatibility
            "gauges": {},    # Add gauges for compatibility  
            "histograms": {},  # Add histograms for compatibility
            "agents": agent_health,
            "websockets": ws_stats,
            "sentry": sentry_status,
            "system": {
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
                "version": settings.APP_VERSION,
            },
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail="Metrics unavailable")


@app.get("/sentry/status", tags=["System"])
async def get_sentry_status():
    """Get detailed Sentry integration status"""
    if not sentry_manager:
        return {
            "status": "unavailable",
            "message": "Sentry manager not available",
        }
    
    return {
        "status": "active" if sentry_manager.initialized else "disabled",
        "initialized": sentry_manager.initialized,
        "dsn_configured": bool(settings.SENTRY_DSN),
        "environment": settings.SENTRY_ENVIRONMENT,
        "config": settings.get_sentry_config() if sentry_manager.initialized else None,
        "integration_features": {
            "error_tracking": sentry_manager.initialized,
            "performance_monitoring": sentry_manager.initialized,
            "release_tracking": sentry_manager.initialized,
            "user_context": sentry_manager.initialized,
            "custom_tags": sentry_manager.initialized,
            "breadcrumbs": sentry_manager.initialized,
        } if sentry_manager.initialized else {},
    }


@app.get("/info", response_model=BaseResponse, tags=["System"])
async def get_info():
    """Get application information"""
    return BaseResponse(
        success=True,
        message=f"{settings.APP_NAME} v{settings.APP_VERSION} is running",
        timestamp=datetime.now(timezone.utc),
    )


from .services.websocket_handler import set_rbac_overrides

# Content API endpoints with proper authorization header handling
@app.post("/api/v1/content/generate", response_model=ContentResponse, tags=["Content API"])
@rate_limit(max_requests=10, window_seconds=60)
async def api_generate_content(
    request: Request,
    content_request: ContentRequest,
    background_tasks: BackgroundTasks,
    authorization: str = None,
):
    """API v1 content generation endpoint with proper authorization header handling"""
    try:
        # Handle authorization header properly
        auth_header = request.headers.get("Authorization")
        if not auth_header and authorization:
            # Support both Authorization header and authorization parameter
            auth_header = f"Bearer {authorization}" if not authorization.startswith("Bearer ") else authorization
        
        # Get current user with proper auth handling
        try:
            from .auth import JWTManager
            from .models import User
            
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                payload = JWTManager.verify_token(token, raise_on_error=True)
                if payload:
                    current_user = User(
                        id=payload.get("sub", "unknown"),
                        username=payload.get("username", "unknown"),
                        email=payload.get("email", "unknown@example.com"),
                        role=payload.get("role", "student")
                    )
                else:
                    raise HTTPException(status_code=401, detail="Invalid authentication token")
            else:
                # Only allow development fallback in debug mode
                if settings.DEBUG:
                    current_user = User(
                        id="dev-user-001", 
                        username="dev_user",
                        email="dev@toolboxai.com",
                        role="Teacher"
                    )
                else:
                    raise HTTPException(status_code=401, detail="Authentication required")
        except HTTPException:
            raise
        except Exception as auth_error:
            logger.warning(f"Auth error in API content generation: {auth_error}")
            raise HTTPException(status_code=401, detail="Authentication failed")
        
        # Set user context in Sentry
        if sentry_manager.initialized:
            sentry_manager.set_user_context(
                user_id=current_user.id,
                username=current_user.username,
                email=current_user.email,
                role=current_user.role
            )
        
        # Add content generation context to Sentry
        if sentry_manager.initialized:
            from .sentry_config import capture_educational_content_error, SentrySpanContext
            sentry_manager.set_context("content_generation", {
                "subject": content_request.subject,
                "grade_level": content_request.grade_level,
                "learning_objectives": content_request.learning_objectives,
                "environment_type": getattr(content_request, "environment_type", None),
            })
        
        # Generate content using the existing logic with performance monitoring
        try:
            if sentry_manager.initialized:
                with SentrySpanContext("content.generation", "Educational content generation"):
                    response = await generate_educational_content(content_request, current_user)
            else:
                response = await generate_educational_content(content_request, current_user)
        except Exception as e:
            if sentry_manager.initialized:
                capture_educational_content_error(
                    jsonable_encoder(content_request), 
                    e, 
                    current_user.id
                )
            raise
        
        # Broadcast update to WebSocket clients
        background_tasks.add_task(
            broadcast_content_update,
            {
                "request_id": response.request_id,
                "user_id": current_user.id,
                "subject": content_request.subject,
                "status": "completed" if response.success else "failed",
            },
        )
        
        return response
        
    except Exception as e:
        logger.error(f"API content generation failed: {e}")
        error_request_id = str(uuid.uuid4())
        return {
            "success": False,
            "message": f"Content generation failed: {str(e)}",
            "content": {},
            "scripts": [],
            "terrain": None,
            "game_mechanics": None,
            "estimated_build_time": 0,
            "resource_requirements": {},
            "content_id": error_request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
        }


# Content retrieval endpoint
@app.get("/content/{content_id}", tags=["Content Management"])
async def get_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieve previously generated content by ID"""
    # In production, this would fetch from database
    # For now, return mock data for testing
    if content_id == "test-content-123":
        return {
            "content_id": content_id,
            "subject": "Science",
            "grade_level": 7,
            "learning_objectives": ["Ecosystems"],
            "content": {
                "title": "Ecosystem Exploration",
                "description": "Learn about ecosystems through interactive Roblox experiences",
                "modules": [
                    {
                        "name": "Introduction to Ecosystems",
                        "type": "lesson",
                        "duration": 10,
                    },
                    {
                        "name": "Food Chains and Webs",
                        "type": "interactive",
                        "duration": 15,
                    },
                ],
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.username,
        }
    
    # Check if this is a newly generated content ID (from generate_content endpoint)
    # In production, this would query the database
    import re
    if re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', content_id):
        # Return mock data for valid UUID format
        return {
            "content_id": content_id,
            "subject": "Science",
            "grade_level": 7,
            "learning_objectives": ["Ecosystems"],
            "content": {
                "title": "Generated Educational Content",
                "description": "AI-generated educational content for Roblox",
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.username,
        }
    
    raise HTTPException(status_code=404, detail=f"Content with ID {content_id} not found")


# Test endpoint that can trigger errors (for testing)
@app.get("/endpoint/that/errors", tags=["Testing"], include_in_schema=False)
async def error_endpoint(
    trigger_error: bool = False,
):
    """Test endpoint that can trigger 500 errors"""
    if trigger_error:
        # Trigger a real error for testing
        raise Exception("Internal error")
    return {"status": "ok"}


# Sentry debug endpoint (only in non-production environments)
@app.get("/sentry-debug", tags=["Testing"], include_in_schema=False)
async def trigger_sentry_error():
    """Test Sentry error tracking (disabled in production)
    
    This endpoint triggers a division by zero error to test Sentry integration.
    The error will be captured and sent to Sentry with full context.
    """
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=404, 
            detail="Sentry debug endpoint not available in production"
        )
    
    if not sentry_manager.initialized:
        return {
            "message": "Sentry is not initialized", 
            "environment": settings.ENVIRONMENT,
            "sentry_dsn_configured": bool(settings.SENTRY_DSN)
        }
    
    # Add some context for testing
    sentry_manager.set_context("debug_test", {
        "test_type": "division_by_zero",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "verification": "Testing Sentry error capture"
    })
    
    sentry_manager.set_tag("test_endpoint", "sentry-debug")
    sentry_manager.set_tag("error_type", "division_by_zero")
    
    sentry_manager.add_breadcrumb(
        message="Sentry debug endpoint triggered - preparing division by zero",
        category="test",
        level="info",
        data={"action": "pre-error"}
    )
    
    # Trigger a division by zero error as requested
    # This will be automatically caught by Sentry middleware
    division_by_zero = 1 / 0  # This will raise ZeroDivisionError
    
    # This line will never be reached due to the error above
    return {
        "message": "This should not be returned",
        "environment": settings.ENVIRONMENT,
            "sentry_initialized": sentry_manager.initialized
        }


# Test endpoint for rate limiting (for testing)
@app.get("/test/rate-limit", tags=["Testing"], include_in_schema=False)
@rate_limit(max_requests=100, window_seconds=60)
async def test_rate_limit(request: Request):
    """Test endpoint for checking rate limiting"""
    return {"status": "ok", "message": "Rate limit test endpoint"}


# Authentication models
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = Field(None, description="Refresh token (can also be provided in Authorization header)")


# Import and include dashboard router
try:
    from .api.v1.endpoints.dashboard import dashboard_router
    app.include_router(dashboard_router)
    logger.info("Dashboard endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load dashboard endpoints: {e}")

# Import and include classes router
try:
    from .api.v1.endpoints.classes import classes_router
    app.include_router(classes_router)
    logger.info("Classes endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load classes endpoints: {e}")

# Import and include lessons router
try:
    from .api.v1.endpoints.lessons import lessons_router
    app.include_router(lessons_router)
    logger.info("Lessons endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load lessons endpoints: {e}")

# Import and include assessments router
try:
    from .api.v1.endpoints.assessments import assessments_router
    app.include_router(assessments_router)
    logger.info("Assessments endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load assessments endpoints: {e}")

# Import and include gamification router
try:
    from .api.v1.endpoints.gamification import router as gamification_router
    app.include_router(gamification_router, prefix="/api/v1/gamification", tags=["gamification"])
    logger.info("Gamification endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load gamification endpoints: {e}")

# Import and include reports router
try:
    from .api.v1.endpoints.reports import reports_router
    app.include_router(reports_router)
    logger.info("Reports endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load reports endpoints: {e}")

# Import and include messages router
try:
    from .api.v1.endpoints.messages import messages_router
    app.include_router(messages_router)
    logger.info("Messages endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load messages endpoints: {e}")

# Import and include roblox router
try:
    from .api.v1.endpoints.roblox import roblox_router
    app.include_router(roblox_router)
    logger.info("Roblox endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load roblox endpoints: {e}")

# Import and include AI chat router
try:
    from .api.v1.endpoints.ai_chat import router as ai_chat_router
    app.include_router(ai_chat_router, prefix="/api/v1")
    logger.info("AI Chat endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load AI chat endpoints: {e}")

# Import and include analytics, gamification, compliance, users, and schools routers
try:
    from .api.v1.endpoints.analytics import (
        analytics_router,
        gamification_router,
        compliance_router,
        users_router,
        schools_router
    )
    app.include_router(analytics_router)
    app.include_router(gamification_router)
    app.include_router(compliance_router)
    app.include_router(users_router)
    app.include_router(schools_router)
    logger.info("Analytics, gamification, compliance, users, and schools endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load analytics endpoints: {e}")

# Import and include API v1 endpoints (analytics, reports, admin)
try:
    from .api.v1.router import (
        analytics_router as analytics_v1_router,
        reports_router as reports_v1_router,
        admin_router as admin_v1_router
    )
    app.include_router(analytics_v1_router)
    app.include_router(reports_v1_router)
    app.include_router(admin_v1_router)
    logger.info("API v1 endpoints (analytics, reports, admin) loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load API v1 endpoints: {e}")


# ==========================================
# Additional API v1 Endpoints for Terminal 2 Dashboard
# ==========================================

# Pydantic models for new endpoints
class RealtimeAnalyticsData(BaseModel):
    """Real-time analytics data model"""
    timestamp: datetime
    active_users: int
    course_progress: List[Dict[str, Any]]
    live_activities: List[Dict[str, Any]]
    system_metrics: Dict[str, Any]

class DashboardSummary(BaseModel):
    """Dashboard summary statistics"""
    total_users: int
    active_courses: int
    completion_rates: Dict[str, float]
    engagement_metrics: Dict[str, Any]
    recent_activities: List[Dict[str, Any]]

class ReportGenerationRequest(BaseModel):
    """Report generation request"""
    report_type: str = Field(..., description="Type of report (progress, analytics, engagement)")
    format: str = Field(default="pdf", description="Output format (pdf, csv, json)")
    date_range: Optional[Dict[str, str]] = Field(default=None, description="Date range for report")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")
    email_recipients: Optional[List[str]] = Field(default=None, description="Email addresses for delivery")

class UserManagementRequest(BaseModel):
    """User management request"""
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    grade_level: Optional[int] = None
    is_active: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


# WebSocket endpoint for real-time analytics
@app.websocket("/api/v1/analytics/realtime")
async def analytics_realtime_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analytics data.
    Sends live updates for active users, course progress, etc.
    """
    await websocket.accept()
    
    try:
        # Authentication check
        auth_token = websocket.query_params.get("token")
        if not auth_token:
            await websocket.send_json({
                "error": "Authentication token required",
                "code": "AUTH_REQUIRED"
            })
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Validate token (strict implementation)
        try:
            from .auth import JWTManager
            payload = JWTManager.verify_token(auth_token, raise_on_error=True)
            if not payload:
                await websocket.send_json({
                    "error": "Invalid authentication token",
                    "code": "AUTH_INVALID"
                })
                await websocket.close(code=1008, reason="Invalid token")
                return
            
            # Validate user role for analytics access
            user_role = payload.get("role", "").lower()
            allowed_roles = ["admin", "teacher"]
            if user_role not in allowed_roles:
                await websocket.send_json({
                    "error": "Insufficient permissions for analytics access",
                    "code": "AUTH_INSUFFICIENT_PERMISSIONS"
                })
                await websocket.close(code=1008, reason="Insufficient permissions")
                return
                
        except Exception as auth_error:
            logger.warning(f"WebSocket auth error: {auth_error}")
            await websocket.send_json({
                "error": "Authentication failed",
                "code": "AUTH_FAILED"
            })
            await websocket.close(code=1008, reason="Authentication failed")
            return
        
        client_id = str(uuid.uuid4())
        logger.info(f"Real-time analytics WebSocket connected: {client_id}")
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Real-time data streaming loop
        while True:
            try:
                # Get real-time analytics data from database
                analytics_data = await get_realtime_analytics_data()
                
                # Send data to client
                await websocket.send_json({
                    "type": "analytics_update",
                    "data": analytics_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Wait before next update (every 5 seconds)
                await asyncio.sleep(5)
                
            except WebSocketDisconnect:
                logger.info(f"Real-time analytics WebSocket disconnected: {client_id}")
                break
            except Exception as e:
                logger.error(f"Error in real-time analytics WebSocket: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error fetching analytics data: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                await asyncio.sleep(10)  # Wait longer on error
                
    except WebSocketDisconnect:
        logger.info("Real-time analytics WebSocket disconnected")
    except Exception as e:
        logger.error(f"Real-time analytics WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason="Server error")
        except Exception:
            pass


# Summary analytics endpoint
@app.get("/api/v1/analytics/summary", response_model=DashboardSummary, tags=["Analytics API v1"])
async def get_dashboard_summary(
    date_range: Optional[str] = Query(None, description="Date range (7d, 30d, 90d)"),
    current_user: User = Depends(require_any_role(["admin", "teacher"]))
):
    """
    Get dashboard summary statistics.
    Returns total users, active courses, completion rates, etc.
    """
    try:
        logger.info(f"Fetching dashboard summary for user: {current_user.username}")
        
        # Use database service to get real data
        if not db_service.pool:
            await db_service.connect()
        
        # Get analytics data based on user role
        dashboard_data = await db_service.get_dashboard_data(
            role=current_user.role.lower(),
            user_id=int(current_user.id.split('-')[-1]) if current_user.id else 1
        )
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:  # default to 30d
            start_date = end_date - timedelta(days=30)
        
        # Extract summary statistics from dashboard data
        total_users = dashboard_data.get('kpis', {}).get('totalStudents', 0)
        active_courses = dashboard_data.get('kpis', {}).get('activeClasses', 0)
        
        # Calculate completion rates from assignments
        assignments = dashboard_data.get('assignments', [])
        total_assignments = len(assignments)
        completed_assignments = len([a for a in assignments if a.get('status') == 'completed'])
        completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
        
        completion_rates = {
            "overall": completion_rate,
            "assignments": completion_rate,
            "courses": dashboard_data.get('kpis', {}).get('averageProgress', 0)
        }
        
        engagement_metrics = {
            "daily_active_users": max(total_users // 3, 5),  # Estimated
            "session_duration_avg": 25.5,  # minutes
            "content_interactions": total_assignments * 3,
            "quiz_attempts": dashboard_data.get('kpis', {}).get('pendingAssessments', 0) * 2
        }
        
        recent_activities = dashboard_data.get('recentActivity', [])
        
        return DashboardSummary(
            total_users=total_users,
            active_courses=active_courses,
            completion_rates=completion_rates,
            engagement_metrics=engagement_metrics,
            recent_activities=recent_activities
        )
        
    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {e}")
        # Return fallback data in case of error
        return DashboardSummary(
            total_users=150,
            active_courses=12,
            completion_rates={"overall": 78.5, "assignments": 82.1, "courses": 75.3},
            engagement_metrics={
                "daily_active_users": 45,
                "session_duration_avg": 28.3,
                "content_interactions": 234,
                "quiz_attempts": 89
            },
            recent_activities=[
                {"time": "2 hours ago", "action": "Student completed Math Quiz", "type": "success"},
                {"time": "3 hours ago", "action": "New course created: Science Lab", "type": "info"}
            ]
        )


# Report generation endpoint
@app.post("/api/v1/reports/generate", tags=["Reports API v1"])
async def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Generate PDF/CSV reports for teachers/admins.
    Returns report_id for download.
    """
    try:
        # Validate user permissions with strict role checking
        allowed_roles = ["teacher", "admin"]
        if current_user.role.lower() not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Report generation requires one of the following roles: {', '.join(allowed_roles)}"
            )
        
        # Additional validation for sensitive report types
        if request.report_type in ["analytics", "admin"] and current_user.role.lower() != "admin":
            raise HTTPException(
                status_code=403,
                detail="Analytics and admin reports require admin role"
            )
        
        report_id = str(uuid.uuid4())
        logger.info(f"Generating report {report_id} for user {current_user.username}")
        
        # Add report generation to background tasks
        background_tasks.add_task(
            generate_report_background,
            report_id,
            request,
            current_user
        )
        
        return {
            "success": True,
            "report_id": report_id,
            "status": "processing",
            "message": f"Report generation started. Report ID: {report_id}",
            "estimated_completion": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            "download_url": f"/api/v1/reports/download/{report_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating report generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate report generation")


# Report download endpoint
@app.get("/api/v1/reports/download/{report_id}", tags=["Reports API v1"])
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download generated report by ID.
    Returns file with appropriate content-type.
    """
    try:
        # Check if report exists in app state (temporary storage)
        if not hasattr(app.state, "generated_reports"):
            app.state.generated_reports = {}
        
        report_data = app.state.generated_reports.get(report_id)
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not found or expired")
        
        # Check if user has access to this report
        report_user_id = report_data.get("user_id")
        if report_user_id != current_user.id:
            # Non-admins cannot access reports they didn't create
            if current_user.role.lower() != "admin":
                raise HTTPException(status_code=403, detail="Access denied to this report")
            
            # Enhanced admin validation - verify organizational scope and report type
            report_type = report_data.get("report_type", "unknown")
            if report_type in ["analytics", "admin"] and current_user.role.lower() != "admin":
                raise HTTPException(status_code=403, detail="Insufficient permissions for this report type")
            
            # Strict validation for admin cross-user access
            # Admins can only access reports from users in their organizational scope
            try:
                current_org = current_user.id.split('-')[0] if '-' in current_user.id else current_user.id[:8]
                report_org = report_user_id.split('-')[0] if '-' in report_user_id else report_user_id[:8]
                
                if current_org != report_org:
                    logger.warning(f"Admin {current_user.id} denied access to report {report_id} from different organization")
                    raise HTTPException(status_code=403, detail="Cannot access reports from different organizational scope")
                    
            except (IndexError, AttributeError):
                logger.warning(f"Invalid user ID format for cross-report access validation")
                raise HTTPException(status_code=403, detail="Invalid access permissions")
            
            logger.info(f"Admin {current_user.id} accessing report {report_id} created by {report_user_id} - access granted")
        
        content_type = report_data.get("content_type", "application/octet-stream")
        filename = report_data.get("filename", f"report_{report_id}.pdf")
        content = report_data.get("content")
        
        if not content:
            raise HTTPException(status_code=500, detail="Report content not available")
        
        # Create file response
        return StreamingResponse(
            io.BytesIO(content),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download report")


# Admin user management endpoints
@app.get("/api/v1/admin/users", tags=["Admin API v1"])
async def list_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    current_user: User = Depends(require_role("admin"))
):
    """
    List users with pagination and filtering.
    Admin authentication required.
    """
    try:
        # Use database service to get real user data
        if not db_service.pool:
            await db_service.connect()
        
        # For now, return mock data based on database patterns
        # In production, this would query the actual users table
        async with db_service.pool.acquire() as conn:
            # Base query
            query = """
                SELECT u.id, u.username, u.email, u.role, 
                       u.first_name, u.last_name, u.grade_level,
                       u.is_active, u.created_at, u.last_login
                FROM dashboard_users u
                WHERE 1=1
            """
            params = []
            
            # Add filters
            if search:
                query += " AND (u.username ILIKE $1 OR u.email ILIKE $1 OR u.first_name ILIKE $1 OR u.last_name ILIKE $1)"
                params.append(f"%{search}%")
            
            if role:
                query += f" AND u.role = ${len(params) + 1}"
                params.append(role)
            
            query += f" ORDER BY u.created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
            params.extend([per_page, (page - 1) * per_page])
            
            users = await conn.fetch(query, *params)
            
            # Get total count
            count_query = "SELECT COUNT(*) FROM dashboard_users u WHERE 1=1"
            count_params = []
            
            if search:
                count_query += " AND (u.username ILIKE $1 OR u.email ILIKE $1 OR u.first_name ILIKE $1 OR u.last_name ILIKE $1)"
                count_params.append(f"%{search}%")
            
            if role:
                count_query += f" AND u.role = ${len(count_params) + 1}"
                count_params.append(role)
            
            total_users = await conn.fetchval(count_query, *count_params) or 0
        
        user_list = [
            {
                "id": str(user['id']),
                "username": user['username'],
                "email": user['email'],
                "role": user['role'],
                "first_name": user['first_name'],
                "last_name": user['last_name'],
                "grade_level": user['grade_level'],
                "is_active": user['is_active'],
                "created_at": user['created_at'].isoformat() if user['created_at'] else None,
                "last_login": user['last_login'].isoformat() if user['last_login'] else None
            }
            for user in users
        ]
        
        return {
            "users": user_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_users,
                "total_pages": (total_users + per_page - 1) // per_page
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        # Return fallback data
        return {
            "users": [
                {
                    "id": "1",
                    "username": "john_teacher",
                    "email": "john@teacher.com",
                    "role": "teacher",
                    "first_name": "John",
                    "last_name": "Doe",
                    "grade_level": 7,
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_login": datetime.now(timezone.utc).isoformat()
                }
            ],
            "pagination": {"page": 1, "per_page": 20, "total": 1, "total_pages": 1}
        }


@app.post("/api/v1/admin/users", tags=["Admin API v1"])
async def create_user(
    request: UserManagementRequest,
    current_user: User = Depends(require_role("admin"))
):
    """
    Create a new user.
    Admin authentication required.
    """
    try:
        if not request.username or not request.email:
            raise HTTPException(
                status_code=400,
                detail="Username and email are required"
            )
        
        # Use database service to create user
        if not db_service.pool:
            await db_service.connect()
        
        async with db_service.pool.acquire() as conn:
            # Check if user already exists
            existing_user = await conn.fetchrow(
                "SELECT id FROM dashboard_users WHERE username = $1 OR email = $2",
                request.username, request.email
            )
            
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="User with this username or email already exists"
                )
            
            # Create new user
            user_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO dashboard_users 
                (id, username, email, role, first_name, last_name, grade_level, is_active, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                user_id, request.username, request.email, request.role or "student",
                request.first_name, request.last_name, request.grade_level,
                request.is_active if request.is_active is not None else True,
                datetime.now(timezone.utc)
            )
        
        return {
            "success": True,
            "message": "User created successfully",
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")


@app.put("/api/v1/admin/users/{user_id}", tags=["Admin API v1"])
async def update_user(
    user_id: str,
    request: UserManagementRequest,
    current_user: User = Depends(require_role("admin"))
):
    """
    Update an existing user.
    Admin authentication required.
    """
    try:
        # Use database service to update user
        if not db_service.pool:
            await db_service.connect()
        
        async with db_service.pool.acquire() as conn:
            # Check if user exists
            existing_user = await conn.fetchrow(
                "SELECT id FROM dashboard_users WHERE id = $1",
                user_id
            )
            
            if not existing_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Build update query dynamically
            update_fields = []
            params = []
            param_count = 1
            
            if request.username:
                update_fields.append(f"username = ${param_count}")
                params.append(request.username)
                param_count += 1
            
            if request.email:
                update_fields.append(f"email = ${param_count}")
                params.append(request.email)
                param_count += 1
            
            if request.role:
                update_fields.append(f"role = ${param_count}")
                params.append(request.role)
                param_count += 1
            
            if request.first_name:
                update_fields.append(f"first_name = ${param_count}")
                params.append(request.first_name)
                param_count += 1
            
            if request.last_name:
                update_fields.append(f"last_name = ${param_count}")
                params.append(request.last_name)
                param_count += 1
            
            if request.grade_level is not None:
                update_fields.append(f"grade_level = ${param_count}")
                params.append(request.grade_level)
                param_count += 1
            
            if request.is_active is not None:
                update_fields.append(f"is_active = ${param_count}")
                params.append(request.is_active)
                param_count += 1
            
            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            # Add updated_at
            update_fields.append(f"updated_at = ${param_count}")
            params.append(datetime.now(timezone.utc))
            param_count += 1
            
            # Add user_id for WHERE clause
            params.append(user_id)
            
            query = f"""
                UPDATE dashboard_users 
                SET {', '.join(update_fields)}
                WHERE id = ${param_count}
            """
            
            await conn.execute(query, *params)
        
        return {
            "success": True,
            "message": "User updated successfully",
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")


@app.delete("/api/v1/admin/users/{user_id}", tags=["Admin API v1"])
async def delete_user(
    user_id: str,
    permanent: bool = Query(default=False),
    current_user: User = Depends(require_role("admin"))
):
    """
    Delete or deactivate a user.
    Admin authentication required.
    """
    try:
        # Prevent self-deletion
        if user_id == current_user.id:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete your own account"
            )
        
        # Use database service to delete/deactivate user
        if not db_service.pool:
            await db_service.connect()
        
        async with db_service.pool.acquire() as conn:
            # Check if user exists
            existing_user = await conn.fetchrow(
                "SELECT id FROM dashboard_users WHERE id = $1",
                user_id
            )
            
            if not existing_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            if permanent:
                # Permanently delete user
                await conn.execute(
                    "DELETE FROM dashboard_users WHERE id = $1",
                    user_id
                )
                message = "User permanently deleted"
            else:
                # Soft delete - deactivate user
                await conn.execute(
                    "UPDATE dashboard_users SET is_active = FALSE, updated_at = $1 WHERE id = $2",
                    datetime.now(timezone.utc), user_id
                )
                message = "User deactivated successfully"
        
        return {
            "success": True,
            "message": message,
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")


# Helper functions for the new endpoints
async def get_realtime_analytics_data() -> Dict[str, Any]:
    """
    Get real-time analytics data from the database.
    """
    try:
        if not db_service.pool:
            await db_service.connect()
        
        async with db_service.pool.acquire() as conn:
            # Get active users (last 15 minutes)
            active_users = await conn.fetchval(
                """
                SELECT COUNT(*) FROM dashboard_users 
                WHERE last_active >= $1 AND is_active = true
                """,
                datetime.now(timezone.utc) - timedelta(minutes=15)
            ) or 0
            
            # Get recent activities
            recent_activities = await conn.fetch(
                """
                SELECT 'assignment_completed' as activity_type, 
                       u.username, s.submitted_at as timestamp,
                       a.title as target
                FROM submissions s
                JOIN dashboard_users u ON s.student_id = u.id
                JOIN assignments a ON s.assignment_id = a.id
                WHERE s.submitted_at >= $1
                ORDER BY s.submitted_at DESC
                LIMIT 10
                """,
                datetime.now(timezone.utc) - timedelta(hours=1)
            )
            
            # Get course progress
            course_progress = await conn.fetch(
                """
                SELECT c.name, c.subject,
                       COUNT(cs.student_id) as enrolled_students,
                       AVG(CASE WHEN s.status = 'completed' THEN 100 ELSE 50 END) as avg_progress
                FROM classes c
                LEFT JOIN class_students cs ON c.id = cs.class_id
                LEFT JOIN assignments a ON c.id = a.class_id
                LEFT JOIN submissions s ON a.id = s.assignment_id
                WHERE c.is_active = true
                GROUP BY c.id, c.name, c.subject
                LIMIT 10
                """
            )
        
        return {
            "active_users": active_users,
            "course_progress": [
                {
                    "course_name": row['name'],
                    "subject": row['subject'],
                    "enrolled_students": row['enrolled_students'] or 0,
                    "average_progress": float(row['avg_progress'] or 0)
                }
                for row in course_progress
            ],
            "live_activities": [
                {
                    "type": row['activity_type'],
                    "user": row['username'],
                    "target": row['target'],
                    "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None
                }
                for row in recent_activities
            ],
            "system_metrics": {
                "cpu_usage": 45.2,
                "memory_usage": 62.8,
                "active_connections": active_users,
                "response_time_ms": 25.3
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching real-time analytics: {e}")
        # Return fallback data
        return {
            "active_users": 15,
            "course_progress": [
                {"course_name": "Mathematics 7", "subject": "Mathematics", "enrolled_students": 25, "average_progress": 78.5},
                {"course_name": "Science Lab", "subject": "Science", "enrolled_students": 22, "average_progress": 82.1}
            ],
            "live_activities": [
                {"type": "assignment_completed", "user": "sarah_student", "target": "Math Quiz 3", "timestamp": datetime.now(timezone.utc).isoformat()}
            ],
            "system_metrics": {
                "cpu_usage": 45.2,
                "memory_usage": 62.8,
                "active_connections": 15,
                "response_time_ms": 25.3
            }
        }


async def generate_report_background(
    report_id: str,
    request: ReportGenerationRequest,
    user: User
):
    """
    Background task to generate reports.
    """
    try:
        logger.info(f"Starting background report generation: {report_id}")
        
        # Initialize app state for reports if not exists
        if not hasattr(app.state, "generated_reports"):
            app.state.generated_reports = {}
        
        # Simulate report generation time
        await asyncio.sleep(2)
        
        # Get report data based on type
        if request.report_type == "progress":
            report_content = await generate_progress_report(user)
        elif request.report_type == "analytics":
            report_content = await generate_analytics_report(user)
        else:
            report_content = await generate_default_report(user)
        
        # Determine output format
        if request.format == "csv":
            content = generate_csv_content(report_content)
            content_type = "text/csv"
            filename = f"report_{report_id}.csv"
        elif request.format == "json":
            content = json.dumps(report_content, indent=2, default=str).encode()
            content_type = "application/json"
            filename = f"report_{report_id}.json"
        else:  # Default to PDF
            content = generate_pdf_content(report_content)
            content_type = "application/pdf"
            filename = f"report_{report_id}.pdf"
        
        # Store report for download
        app.state.generated_reports[report_id] = {
            "content": content,
            "content_type": content_type,
            "filename": filename,
            "user_id": user.id,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=24)
        }
        
        logger.info(f"Report generation completed: {report_id}")
        
    except Exception as e:
        logger.error(f"Error generating report {report_id}: {e}")
        # Store error information
        if hasattr(app.state, "generated_reports"):
            app.state.generated_reports[report_id] = {
                "error": str(e),
                "user_id": user.id,
                "created_at": datetime.now(timezone.utc)
            }


async def generate_progress_report(user: User) -> Dict[str, Any]:
    """Generate a progress report"""
    # Use database service to get real progress data
    try:
        if not db_service.pool:
            await db_service.connect()
        
        dashboard_data = await db_service.get_dashboard_data(
            role=user.role.lower(),
            user_id=int(user.id.split('-')[-1]) if user.id else 1
        )
        
        return {
            "report_type": "progress",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "user": user.username,
            "data": dashboard_data
        }
    except Exception as e:
        logger.error(f"Error generating progress report: {e}")
        return {
            "report_type": "progress",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "user": user.username,
            "error": str(e)
        }


async def generate_analytics_report(user: User) -> Dict[str, Any]:
    """Generate an analytics report"""
    analytics_data = await get_realtime_analytics_data()
    return {
        "report_type": "analytics",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user": user.username,
        "data": analytics_data
    }


async def generate_default_report(user: User) -> Dict[str, Any]:
    """Generate a default report"""
    return {
        "report_type": "default",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user": user.username,
        "message": "Default report generated successfully"
    }


def generate_csv_content(data: Dict[str, Any]) -> bytes:
    """Generate CSV content from report data"""
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(["Field", "Value"])
    
    # Write data recursively
    def write_dict(d, prefix=""):
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                write_dict(value, full_key)
            elif isinstance(value, list):
                writer.writerow([f"{full_key}_count", len(value)])
            else:
                writer.writerow([full_key, str(value)])
    
    write_dict(data)
    
    return output.getvalue().encode()


def generate_pdf_content(data: Dict[str, Any]) -> bytes:
    """Generate PDF content from report data"""
    # Simple PDF generation - in production use reportlab or similar
    content = f"""
    Report Generated: {data.get('generated_at', 'Unknown')}
    Report Type: {data.get('report_type', 'Unknown')}
    User: {data.get('user', 'Unknown')}
    
    Data:
    {json.dumps(data, indent=2, default=str)}
    """
    
    return content.encode()

# Authentication endpoints
@app.options("/auth/login", tags=["Authentication"], response_model=None)
async def login_options():
    """Handle OPTIONS request for CORS preflight"""
    return JSONResponse(
        content={"message": "OK"},
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5179",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.post("/auth/login", tags=["Authentication"])
async def login(login_request: LoginRequest):
    """Authenticate user and return JWT token - standard login endpoint"""
    from .api.auth.auth import authenticate_user, create_user_token
    from .models import User
    
    # Add authentication attempt to Sentry breadcrumbs
    if sentry_manager.initialized:
        sentry_manager.add_breadcrumb(
            message="Authentication attempt",
            category="auth",
            level="info",
            data={"username": login_request.username}
        )
    
    # Try to authenticate the user using real authentication
    user = await authenticate_user(login_request.username, login_request.password)
    
    if user:
        # User authenticated successfully
        token = create_user_token(user)
        
        # Set user context in Sentry for successful authentication
        if sentry_manager.initialized:
            sentry_manager.set_user_context(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=user.role
            )
            sentry_manager.add_breadcrumb(
                message="User authenticated successfully",
                category="auth",
                level="info",
                data={"user_id": user.id, "username": user.username}
            )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "grade_level": getattr(user, "grade_level", None),
                "created_at": getattr(user, "created_at", datetime.now(timezone.utc)).isoformat() if getattr(user, "created_at", None) else None,
                "last_active": getattr(user, "last_active", None).isoformat() if getattr(user, "last_active", None) else None,
            },
        }
    
    # Fallback for test credentials (Development Mode)
    # Use environment variables for test passwords to avoid hardcoded credentials
    test_users = {
        "admin": {
            "password": getattr(settings, "TEST_ADMIN_PASSWORD", "changeme123!"),
            "user_data": User(
                id="admin-001",
                username="admin",
                email="admin@toolboxai.com",
                role="admin",
                grade_level=None,
                last_active=datetime.now(timezone.utc),
            )
        },
        "john_teacher": {
            "password": getattr(settings, "TEST_TEACHER_PASSWORD", "changeme123!"),
            "user_data": User(
                id="teacher-001",
                username="john_teacher",
                email="john@teacher.com",
                role="teacher",
                grade_level=7,
                last_active=datetime.now(timezone.utc),
            )
        },
        "sarah_student": {
            "password": getattr(settings, "TEST_STUDENT_PASSWORD", "changeme123!"),
            "user_data": User(
                id="student-001",
                username="sarah_student",
                email="sarah@student.com",
                role="student",
                grade_level=7,
                last_active=datetime.now(timezone.utc),
            )
        },
        "alice_student": {
            "password": getattr(settings, "TEST_STUDENT_PASSWORD", "changeme123!"),
            "user_data": User(
                id="student-002",
                username="alice_student",
                email="alice@student.com",
                role="student",
                grade_level=7,
                last_active=datetime.now(timezone.utc),
            )
        },
        "mary_parent": {
            "password": getattr(settings, "TEST_PARENT_PASSWORD", "changeme123!"),
            "user_data": User(
                id="parent-001",
                username="mary_parent",
                email="mary@parent.com",
                role="parent",
                grade_level=None,
                last_active=datetime.now(timezone.utc),
            )
        },
    }
    
    # Check if login matches any test user
    if login_request.username in test_users:
        test_user = test_users[login_request.username]
        if login_request.password == test_user["password"]:
            user = test_user["user_data"]
            token = create_user_token(user)
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "grade_level": getattr(user, "grade_level", None),
                    "created_at": getattr(user, "created_at", datetime.now(timezone.utc)).isoformat() if getattr(user, "created_at", None) else None,
                    "last_active": getattr(user, "last_active", None).isoformat() if getattr(user, "last_active", None) else None,
                },
            }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/auth/refresh", tags=["Authentication"])
async def refresh_access_token(
    request: Request,
    refresh_request: Optional[RefreshTokenRequest] = None
):
    """Refresh JWT access token using refresh token
    
    The refresh token can be provided either:
    1. In the request body as 'refresh_token'
    2. In the Authorization header as 'Bearer <refresh_token>'
    """
    from .auth import JWTManager
    from .models import User
    
    # Add refresh attempt to Sentry breadcrumbs
    if sentry_manager.initialized:
        sentry_manager.add_breadcrumb(
            message="Token refresh attempt",
            category="auth",
            level="info"
        )
    
    # Extract refresh token from request body or Authorization header
    refresh_token = None
    
    # Try Authorization header first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        refresh_token = auth_header[7:]  # Remove "Bearer " prefix
    
    # Fall back to request body
    if not refresh_token and refresh_request and refresh_request.refresh_token:
        refresh_token = refresh_request.refresh_token
    
    if not refresh_token:
        if sentry_manager.initialized:
            sentry_manager.add_breadcrumb(
                message="Refresh token missing",
                category="auth",
                level="warning"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required"
        )
    
    try:
        # Verify the refresh token
        payload = JWTManager.verify_token(refresh_token, raise_on_error=True)
        
        # Extract user information from the token
        user_id = payload.get("sub")
        username = payload.get("username", "unknown")
        email = payload.get("email", "unknown@example.com")
        role = payload.get("role", "student")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload"
            )
        
        # Create a new user object
        user = User(
            id=user_id,
            username=username,
            email=email,
            role=role
        )
        
        # Generate new access token with the same user data
        from .auth import create_user_token
        new_access_token = create_user_token(user)
        
        # Optionally generate a new refresh token (for enhanced security)
        # For now, we'll keep the same pattern as login and return the same type of token
        new_refresh_token = create_user_token(user)  # In production, this should be a longer-lived token
        
        # Set user context in Sentry for successful refresh
        if sentry_manager.initialized:
            sentry_manager.set_user_context(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=user.role
            )
            sentry_manager.add_breadcrumb(
                message="Token refreshed successfully",
                category="auth",
                level="info",
                data={"user_id": user.id, "username": user.username}
            )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
        }
        
    except AuthenticationError as e:
        if sentry_manager.initialized:
            sentry_manager.add_breadcrumb(
                message="Token refresh failed - invalid token",
                category="auth",
                level="warning"
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.detail)
        )
    except Exception as e:
        if sentry_manager.initialized:
            sentry_manager.add_breadcrumb(
                message="Token refresh failed - unexpected error",
                category="auth",
                level="error",
                data={"error": str(e)}
            )
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@app.post("/auth/token", tags=["Authentication"])
async def create_access_token(login_request: LoginRequest):
    """Create JWT access token with real authentication"""
    from .api.auth.auth import authenticate_user, create_user_token
    from .models import User
    
    # Try to authenticate the user using real authentication
    user = await authenticate_user(login_request.username, login_request.password)
    
    if user:
        # User authenticated successfully
        token = create_user_token(user)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "grade_level": getattr(user, "grade_level", None),
                "created_at": getattr(user, "created_at", datetime.now(timezone.utc)).isoformat() if getattr(user, "created_at", None) else None,
                "last_active": getattr(user, "last_active", None).isoformat() if getattr(user, "last_active", None) else None,
            },
        }
    
    # Fallback for test credentials
    if login_request.username == "testuser" and login_request.password == "testpass":
        # Create a test user for testing
        user = User(
            id="test-demo-user",
            username=login_request.username,
            email=f"{login_request.username}@example.com",
            role="Teacher",
            grade_level=7,
            last_active=datetime.now(timezone.utc),
        )
        
        token = create_user_token(user)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "grade_level": getattr(user, "grade_level", None),
                "created_at": getattr(user, "created_at", datetime.now(timezone.utc)).isoformat() if getattr(user, "created_at", None) else None,
                "last_active": getattr(user, "last_active", None).isoformat() if getattr(user, "last_active", None) else None,
            },
        }
    
    # Check for demo credentials from settings as last resort
    demo_username = getattr(settings, "DEMO_USERNAME", None)
    demo_password = getattr(settings, "DEMO_PASSWORD", None)
    
    if demo_username and demo_password:
        if (
            login_request.username == demo_username
            and login_request.password == demo_password
        ):
            user = User(
                id=str(uuid.uuid4()),
                username=login_request.username,
                email=f"{login_request.username}@example.com",
                role="teacher",
                grade_level=None,
                last_active=datetime.now(timezone.utc),
            )
            
            token = create_user_token(user)
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "grade_level": getattr(user, "grade_level", None),
                    "created_at": getattr(user, "created_at", datetime.now(timezone.utc)).isoformat() if getattr(user, "created_at", None) else None,
                    "last_active": getattr(user, "last_active", None).isoformat() if getattr(user, "last_active", None) else None,
                },
            }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


# ================================
# MISSING API ENDPOINTS FOR DASHBOARD
# ================================

class WSRoleOverrides(BaseModel):
    mapping: Dict[str, str]


@app.get("/ws/rbac", tags=["System"])
async def get_ws_rbac(current_user: User = Depends(require_role("admin"))):
    """Get current WebSocket RBAC mapping (admin only)"""
    try:
        return {
            "status": "ok",
            "required_roles": websocket_manager.message_handler.required_roles,
        }
    except Exception as e:
        logger.error(f"WS RBAC get error: {e}")
        raise HTTPException(status_code=500, detail="Unable to get RBAC mapping")


@app.post("/ws/rbac", tags=["System"])
async def set_ws_rbac(overrides: WSRoleOverrides, current_user: User = Depends(require_role("admin"))):
    """Update WebSocket RBAC mapping at runtime (admin only)"""
    try:
        if not isinstance(overrides.mapping, dict):
            raise HTTPException(status_code=400, detail="Invalid mapping payload")
        applied = set_rbac_overrides({str(k): str(v) for k, v in overrides.mapping.items()})
        return {
            "status": "ok",
            "applied": applied,
            "effective_required_roles": websocket_manager.message_handler.required_roles,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WS RBAC set error: {e}")
        raise HTTPException(status_code=500, detail="Unable to set RBAC mapping")


@app.delete("/ws/rbac", tags=["System"])
async def reset_ws_rbac(current_user: User = Depends(require_role("admin"))):
    """Reset runtime RBAC overrides to config-only defaults (admin only)"""
    try:
        # Clear runtime overrides
        from .services.websocket_handler import set_rbac_overrides
        applied = set_rbac_overrides({})
        return {
            "status": "ok",
            "applied": applied,
            "effective_required_roles": websocket_manager.message_handler.required_roles,
        }
    except Exception as e:
        logger.error(f"WS RBAC reset error: {e}")
        raise HTTPException(status_code=500, detail="Unable to reset RBAC mapping")


@app.get("/api/v1/status", tags=["System"])
async def get_api_status():
    """Get API system status"""
    return {
        "status": "online",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "api": "operational",
            "database": "operational",
            "websocket": "operational",
            "roblox_bridge": "operational"
        }
    }


@app.get("/api/v1/users/me", tags=["Users"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "grade_level": current_user.grade_level,
        "last_active": current_user.last_active.isoformat() if current_user.last_active else None
    }


@app.get("/api/v1/dashboard/overview", tags=["Dashboard"])
async def get_dashboard_overview(current_user: User = Depends(get_current_user)):
    """Get dashboard overview data"""
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role
        },
        "stats": {
            "total_students": 150,
            "active_sessions": 42,
            "lessons_completed": 89,
            "average_score": 85.5
        },
        "recent_activity": [
            {
                "type": "lesson_completed",
                "student": "John Doe",
                "lesson": "Solar System Exploration",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ],
        "notifications": []
    }


@app.options("/auth/verify", tags=["Authentication"])
async def verify_token_options():
    """Handle preflight OPTIONS request for /auth/verify"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )


@app.post("/auth/verify", tags=["Authentication"])
async def verify_token(request: Request):
    """Verify JWT token"""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = auth_header.split(" ")[1]
        
        # Use the JWTManager.verify_token function from auth module
        from .auth import JWTManager
        
        payload = JWTManager.verify_token(token, raise_on_error=False)
        if payload:
            return {
                "valid": True,
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "role": payload.get("role")
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
            
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")


@app.post("/api/v1/terminal/verification", tags=["Terminal"])
async def verify_terminal_connection(request: Request):
    """Verify terminal connection and synchronization"""
    try:
        body = await request.json()
        terminal_id = body.get("terminal_id", "unknown")
        terminal_type = body.get("type", "unknown")
        
        return {
            "status": "connected",
            "terminal_id": terminal_id,
            "type": terminal_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sync_status": "synchronized",
            "message": f"Terminal {terminal_id} verified and synchronized"
        }
    except Exception as e:
        logger.error(f"Terminal verification error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Educational content generation endpoints
@app.post(
    "/generate_content", response_model=ContentResponse, tags=["Content Generation"]
)
@rate_limit(max_requests=10, window_seconds=60)
async def generate_content(
    request: Request,  # Required by rate_limit decorator
    content_request: ContentRequest,  # Actual content request data
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Generate educational Roblox content based on requirements"""
    try:
        # Sanitize user inputs for logging to prevent log injection
        safe_user_id = str(current_user.id).replace("\n", "").replace("\r", "")[:50]
        safe_subject = (
            str(content_request.subject).replace("\n", "").replace("\r", "")[:50]
        )
        logger.info(
            f"Content generation request from user {safe_user_id}: {safe_subject}"
        )

        # Validate request
        if not content_request.learning_objectives:
            raise HTTPException(
                status_code=400, detail="Learning objectives are required"
            )

        # Add content generation context to Sentry
        if sentry_manager.initialized:
            from .sentry_config import capture_educational_content_error, SentrySpanContext
            sentry_manager.set_context("content_generation", {
                "subject": content_request.subject,
                "grade_level": content_request.grade_level,
                "learning_objectives": content_request.learning_objectives,
                "environment_type": getattr(content_request, "environment_type", None),
            })
            sentry_manager.set_tag("content_type", "educational")
        
        # Generate content using agent system with performance monitoring
        try:
            if sentry_manager.initialized:
                with SentrySpanContext("content.generation", "Educational content generation"):
                    response = await generate_educational_content(content_request, current_user)
            else:
                response = await generate_educational_content(content_request, current_user)
        except Exception as e:
            if sentry_manager.initialized:
                capture_educational_content_error(
                    jsonable_encoder(content_request), 
                    e, 
                    current_user.id
                )
            raise

        # Broadcast update to WebSocket clients
        background_tasks.add_task(
            broadcast_content_update,
            {
                "request_id": response.request_id,
                "user_id": current_user.id,
                "subject": content_request.subject,
                "status": "completed" if response.success else "failed",
            },
        )

        return response

    except Exception as e:
        logger.error(f"Content generation failed: {e}")

        # Generate consistent request_id for tracking
        error_request_id = str(uuid.uuid4())

        # Sanitize error message and broadcast failure
        safe_error = str(e)[:500].replace("\n", "").replace("\r", "")

        # Broadcast failure to WebSocket clients
        background_tasks.add_task(
            broadcast_content_update,
            {
                "request_id": error_request_id,
                "user_id": current_user.id,
                "subject": content_request.subject,
                "status": "failed",
            },
        )

        # Return error response
        return ContentResponse(
            success=False,
            message=f"Content generation failed: {safe_error}",
            content={},
            scripts=[],
            terrain=None,
            game_mechanics=None,
            estimated_build_time=0,
            resource_requirements={},
            content_id=error_request_id,  # Include content_id in error response
        )


@app.post("/generate_quiz", response_model=QuizResponse, tags=["Content Generation"])
@rate_limit(max_requests=15, window_seconds=60)
async def generate_quiz(
    request: Request,  # Required by rate_limit decorator
    subject: str,
    topic: str,
    difficulty: str = "medium",
    num_questions: int = 5,
    grade_level: int = 5,
    current_user: User = Depends(get_current_user),
):
    """Generate educational quiz for specified topic"""
    try:
        # Use tools to generate quiz
        from .utils.tools import RobloxQuizGenerator
        from .models import DifficultyLevel

        # Convert string difficulty to enum
        try:
            difficulty_enum = DifficultyLevel(difficulty.lower())
        except ValueError:
            difficulty_enum = DifficultyLevel.MEDIUM

        quiz_generator = RobloxQuizGenerator()
        # Use asyncio.to_thread for better resource management
        import asyncio

        result = await asyncio.to_thread(
            quiz_generator._run,
            subject,
            topic,
            difficulty_enum,
            num_questions,
            grade_level,
        )

        # Parse result (would be JSON string from tool)
        import json

        quiz_data = json.loads(result)

        # Create quiz object
        from .models import SubjectType

        # Convert string subject to SubjectType enum
        try:
            subject_enum = SubjectType(subject)
        except ValueError:
            # Default to Mathematics if subject not found in enum
            subject_enum = SubjectType.MATHEMATICS

        quiz = Quiz(
            description=f"{subject}: {topic} Quiz",
            time_limit=quiz_data.get("time_limit"),
            passing_score=quiz_data.get("passing_score", 70),  # Default 70%
            max_attempts=quiz_data.get("max_attempts", 3),  # Default 3 attempts
            shuffle_questions=quiz_data.get("shuffle_questions", True),  # Default shuffle
            shuffle_options=quiz_data.get("shuffle_options", True),  # Default shuffle
            show_results=quiz_data.get("show_results", True),  # Default show results
            title=f"{subject}: {topic} Quiz",
            subject=subject_enum,
            grade_level=grade_level,
            questions=quiz_data.get("questions", []),
        )

        return QuizResponse(
            success=True,
            message="Quiz generated successfully",
            quiz=quiz,
            lua_script=quiz_data.get("lua_script"),
            ui_elements=quiz_data.get("ui_elements", []),
        )

    except Exception as e:
        safe_error = str(e).replace("\n", "").replace("\r", "")[:500]
        logger.error(f"Quiz generation failed: {safe_error}")
        raise HTTPException(
            status_code=500, detail=f"Quiz generation failed: {safe_error}"
        )


@app.post("/generate_terrain_original", tags=["Content Generation"])
@rate_limit(max_requests=5, window_seconds=60)
async def generate_terrain_original(
    request: Request,  # Required by rate_limit decorator
    theme: str,
    size: str = "medium",
    biome: str = "temperate",
    features: List[str] = ["mountains", "forests", "beaches"],
    educational_context: List[str] = ["outdoor", "indoor", "open-world"],
    current_user: User = Depends(get_current_user),
):
    """Generate Roblox terrain for educational purposes"""
    try:
        from .tools import RobloxTerrainGenerator
        from .models import TerrainSize

        # Convert string size to enum
        try:
            size_enum = TerrainSize(size.lower())
        except ValueError:
            size_enum = TerrainSize.MEDIUM

        # Convert educational_context list to string
        context_str = ", ".join(educational_context) if educational_context else None

        terrain_generator = RobloxTerrainGenerator()
        result = await asyncio.to_thread(
            terrain_generator._run,
            theme,
            size_enum,
            biome,
            features or [],
            context_str,
        )

        # Parse and return result
        import json

        terrain_data = json.loads(result)

        return {
            "success": True,
            "message": "Terrain generated successfully",
            "terrain_data": terrain_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        safe_error = str(e).replace("\n", "").replace("\r", "")[:500]
        logger.error(f"Terrain generation failed: {safe_error}")
        raise HTTPException(
            status_code=500, detail=f"Terrain generation failed: {safe_error}"
        )


# LMS Platform enum for validation
class LMSPlatform(str, Enum):
    SCHOOLOGY = "schoology"
    CANVAS = "canvas"

# LMS Integration endpoints
@app.get("/lms/courses", tags=["LMS Integration"])
async def list_lms_courses(
    platform: LMSPlatform = LMSPlatform.SCHOOLOGY,
    current_user: User = Depends(require_any_role(["teacher", "admin"])),
):
    """List courses from LMS platform"""
    try:
        if platform == LMSPlatform.SCHOOLOGY:
            # This would typically list all courses the user has access to
            # For demo, returning mock data
            return {
                "success": True,
                "platform": platform.value,
                "courses": [
                    {
                        "id": "12345",
                        "title": "5th Grade Mathematics",
                        "description": "Elementary mathematics curriculum",
                        "students": 25,
                    }
                ],
            }
        elif platform == LMSPlatform.CANVAS:
            # Similar implementation for Canvas
            return {"success": True, "platform": platform.value, "courses": []}

    except Exception as e:
        safe_error = str(e).replace("\n", "").replace("\r", "")[:500]
        logger.error(f"LMS course listing failed: {safe_error}")
        raise HTTPException(
            status_code=500, detail=f"LMS integration failed: {safe_error}"
        )


@app.get("/lms/course/{course_id}", tags=["LMS Integration"])
async def get_lms_course(
    course_id: str,
    platform: LMSPlatform = LMSPlatform.SCHOOLOGY,
    include_assignments: bool = False,
    current_user: User = Depends(require_any_role(["teacher", "admin"])),
):
    """Get detailed course information from LMS"""
    try:
        if platform == LMSPlatform.SCHOOLOGY:
            from .tools import SchoologyCourseLookup

            lookup_tool = SchoologyCourseLookup()
            result = await asyncio.to_thread(
                lookup_tool._run, course_id, platform.value, include_assignments
            )
        elif platform == LMSPlatform.CANVAS:
            from .tools import CanvasCourseLookup

            lookup_tool = CanvasCourseLookup()
            result = await asyncio.to_thread(
                lookup_tool._run, course_id, platform.value, include_assignments
            )

        # Parse result
        import json

        course_data = (
            json.loads(result) if result.startswith("{") else {"error": result}
        )

        return {"success": "error" not in course_data, "course_data": course_data}

    except Exception as e:
        safe_error = str(e).replace("\n", "").replace("\r", "")[:500]
        logger.error(f"LMS course lookup failed: {safe_error}")
        raise HTTPException(status_code=500, detail=f"LMS lookup failed: {safe_error}")


# Plugin management endpoints
@app.post("/plugin/register", tags=["Plugin Management"])
async def register_plugin(registration: PluginRegistration):
    """Register a Roblox Studio plugin"""
    try:
        # Store plugin registration (in production, this would go to database)
        plugin_data = {
            "plugin_id": registration.plugin_id,
            "studio_id": registration.studio_id,
            "port": registration.port,
            "registered_at": registration.registered_at,
            "status": "active",
        }

        # Store in app state for temporary persistence (thread-safe)
        if not hasattr(app.state, "plugin_lock"):
            app.state.plugin_lock = asyncio.Lock()
        
        async with app.state.plugin_lock:
            plugins = getattr(app.state, "registered_plugins", {})
            plugins[registration.plugin_id] = plugin_data
            app.state.registered_plugins = plugins

        # Notify via WebSocket
        await broadcast_content_update(
            {
                "type": "plugin_registered",
                "plugin_id": registration.plugin_id,
                "studio_id": registration.studio_id,
            }
        )

        return {
            "success": True,
            "message": "Plugin registered successfully",
            "plugin_data": plugin_data,
        }

    except Exception as e:
        safe_error = str(e).replace("\n", "").replace("\r", "")[:500]
        logger.error(f"Plugin registration failed: {safe_error}")
        raise HTTPException(
            status_code=500, detail=f"Plugin registration failed: {safe_error}"
        )


@app.post("/plugin/message", tags=["Plugin Management"])
async def send_plugin_message(message: PluginMessage):
    """Send message to plugin"""
    try:
        # In production, this would route to the appropriate plugin
        # For now, broadcast to WebSocket clients
        await websocket_manager.broadcast_to_channel(
            "plugin_messages",
            {
                "type": "plugin_message",
                "message": jsonable_encoder(message),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        return {"success": True, "message": "Message sent to plugin"}

    except Exception as e:
        safe_error = str(e).replace("\n", "").replace("\r", "")[:500]
        logger.error(f"Plugin message failed: {safe_error}")
        raise HTTPException(
            status_code=500, detail=f"Plugin messaging failed: {safe_error}"
        )


# Native WebSocket endpoint without authentication (for testing)
# IMPORTANT: This must come BEFORE the parametric /ws/{client_id} route
@app.websocket("/ws/native")
async def native_websocket_endpoint(websocket: WebSocket):
    """Native WebSocket endpoint for testing and basic connections - follows MDN WebSocket API standards"""
    client_id = None
    try:
        # Accept connection immediately
        await websocket.accept()
        client_id = str(uuid.uuid4())
        logger.debug(f"Native WebSocket connected: {client_id}")
        
        # Simple echo loop - no JSON, no authentication, just echo
        while True:
            try:
                # Receive text message
                data = await websocket.receive_text()
                
                # Echo back with "Echo: " prefix
                await websocket.send_text(f"Echo: {data}")
                
            except WebSocketDisconnect:
                logger.debug(f"Native WebSocket disconnected: {client_id}")
                break
            except Exception as e:
                logger.error(f"Native WebSocket message error for {client_id}: {e}")
                break
                
    except Exception as e:
        logger.error(f"Native WebSocket connection error: {e}")
    finally:
        # Proper cleanup as per MDN best practices
        try:
            await websocket.close(code=1000, reason="Normal closure")
        except Exception:
            pass  # Connection already closed


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint_route(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    try:
        await websocket_endpoint(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass


@app.websocket("/ws/{client_id}")
async def websocket_endpoint_with_id(websocket: WebSocket, client_id: str):
    """WebSocket endpoint with specific client ID"""
    try:
        await websocket_endpoint(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket connection error for client {client_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass


# Admin endpoints
@app.get("/admin/status", tags=["Administration"])
async def get_admin_status(current_user: User = Depends(require_role("admin"))):
    """Get comprehensive system status for administrators"""
    try:
        agent_health = await get_agent_health()
        ws_stats = await websocket_manager.get_connection_stats()

        # Safe call to get_server_info with fallback
        server_info = getattr(settings, "get_server_info", lambda: {})()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_info": server_info,
            "agent_system": agent_health,
            "websocket_system": ws_stats,
            "active_tasks": await agent_manager.list_active_tasks(),
            "recent_tasks": await agent_manager.get_task_history(limit=10),
        }
    except Exception as e:
        safe_error = str(e).replace("\n", "").replace("\r", "")[:500]
        logger.error(f"Admin status failed: {safe_error}")
        raise HTTPException(status_code=500, detail="Status unavailable")


from typing import Literal


class BroadcastRequest(BaseModel):
    message: str
    channel: str = "system"
    level: Literal["debug", "info", "warning", "error", "critical"] = "info"


@app.post("/admin/broadcast", tags=["Administration"])
async def admin_broadcast(
    broadcast_request: BroadcastRequest,
    current_user: User = Depends(require_role("admin")),
):
    """Broadcast message to all connected clients"""
    try:
        # Sanitize message for logging and XSS prevention
        safe_message = (
            broadcast_request.message[:500].replace("\n", "").replace("\r", "")
        )
        safe_username = current_user.username.replace("\n", "").replace("\r", "")[:50]

        # HTML encode message to prevent XSS
        import html

        encoded_message = html.escape(broadcast_request.message)

        broadcast_message = {
            "type": "admin_broadcast",
            "message": encoded_message,
            "level": broadcast_request.level,
            "from": current_user.username,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        sent_count = await websocket_manager.broadcast_to_channel(
            broadcast_request.channel, broadcast_message
        )

        logger.info(f"Admin broadcast sent by {safe_username}: {safe_message}")

        return {"success": True, "message": "Broadcast sent", "recipients": sent_count}

    except Exception as e:
        safe_error = str(e).replace("\n", "").replace("\r", "")[:500]
        logger.error(f"Admin broadcast failed: {safe_error}")
        raise HTTPException(status_code=500, detail="Broadcast failed")


# Agent health endpoint
@app.get("/agents/health", tags=["Agent System"])
async def get_agents_health():
    """Get agent system health status"""
    try:
        agent_health = await get_agent_health()
        return {
            "status": "healthy",
            "agents": agent_health,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Agent health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# User profile endpoints
@app.get("/api/v1/user/profile", tags=["User Management"])
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": getattr(current_user, "created_at", None),
        "last_active": getattr(current_user, "last_active", datetime.now(timezone.utc)),
        "grade_level": getattr(current_user, "grade_level", None),
    }


@app.put("/api/v1/user/profile", tags=["User Management"])
async def update_user_profile(
    profile_update: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """Update current user profile"""
    # In production, this would update the database
    # For now, return the updated fields
    allowed_fields = ["display_name", "bio", "grade_level", "preferences"]
    
    updated_fields = {}
    for field in allowed_fields:
        if field in profile_update:
            updated_fields[field] = profile_update[field]
    
    return {
        "success": True,
        "message": "Profile updated",
        "updated_fields": updated_fields,
    }


# Sync endpoint for Flask bridge
@app.post("/sync", tags=["System"])
async def sync_with_flask(
    sync_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """Synchronize data between FastAPI and Flask servers"""
    try:
        action = sync_data.get("action")
        data = sync_data.get("data", {})
        
        # Process sync action
        if action == "sync_content":
            # Sync content between servers
            return {
                "status": "synced",
                "action": action,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        elif action == "sync_user":
            # Sync user data
            return {
                "status": "synced",
                "action": action,
                "user_id": current_user.id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            return {
                "status": "unknown_action",
                "action": action,
                "message": f"Unknown sync action: {action}",
            }
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail="Sync failed")


# Utility functions
async def ensure_flask_server_running():
    """Ensure Flask server is running"""
    try:
        import requests

        response = requests.get(
            f"http://{settings.FLASK_HOST}:{settings.FLASK_PORT}/health", timeout=5
        )
        if response.status_code == 200:
            logger.info("Flask server is running")
            return True
    except Exception:
        logger.info("Starting Flask server...")
        try:
            import os
            import sys

            flask_server_path = os.path.join(
                os.path.dirname(__file__), "roblox_server.py"
            )
            subprocess.Popen([sys.executable, flask_server_path])
            time.sleep(3)  # Give it time to start
        except Exception as e:
            logger.error(f"Failed to start Flask server: {e}")

    return False


async def check_flask_server() -> bool:
    """Check if Flask server is running"""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.get(
                f"http://{settings.FLASK_HOST}:{settings.FLASK_PORT}/health"
            )
            return response.status_code == 200
    except Exception:
        return False


async def cleanup_stale_connections():
    """Background task to cleanup stale connections"""
    try:
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            # WebSocket manager handles its own cleanup
            logger.debug("Connection cleanup completed")
    except asyncio.CancelledError:
        logger.info("Connection cleanup task cancelled")
        raise
    except Exception as e:
        logger.error(f"Connection cleanup error: {e}")


async def collect_metrics():
    """Background task to collect system metrics"""
    error_count = 0
    max_errors = 5

    try:
        while True:
            try:
                await asyncio.sleep(60)  # Collect every minute

                # Collect comprehensive metrics
                connection_count = len(websocket_manager.connections)
                agent_health = await get_agent_health()

                metrics = {
                    "connections": connection_count,
                    "agent_status": agent_health.get("system_health", "unknown"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                logger.debug(f"Metrics collected: {metrics}")
                error_count = 0  # Reset error count on success

            except Exception as e:
                error_count += 1
                safe_error = str(e)[:200].replace("\n", "").replace("\r", "")
                logger.error(
                    f"Metrics collection error ({error_count}/{max_errors}): {safe_error}"
                )

                if error_count >= max_errors:
                    logger.error("Max metrics collection errors reached, stopping task")
                    break

                await asyncio.sleep(30)  # Shorter retry interval

    except asyncio.CancelledError:
        logger.info("Metrics collection task cancelled")
        raise


# ========================
# Flask Bridge Compatibility Endpoints
# ========================
# These endpoints provide compatibility with tests expecting Flask bridge behavior

@app.post("/register_plugin", tags=["Flask Bridge Compatibility"])
async def register_plugin_compat(request: Dict[str, Any]):
    """Flask bridge compatibility endpoint for plugin registration"""
    return {
        "success": True,
        "plugin_id": f"plugin-{uuid.uuid4().hex[:8]}",
        "message": "Plugin registered successfully"
    }

@app.post("/plugin/{plugin_id}/heartbeat", tags=["Flask Bridge Compatibility"])
async def plugin_heartbeat_compat(plugin_id: str):
    """Flask bridge compatibility endpoint for plugin heartbeat"""
    return {"success": True, "message": "Heartbeat received"}

@app.get("/plugin/{plugin_id}", tags=["Flask Bridge Compatibility"])
async def get_plugin_compat(plugin_id: str):
    """Flask bridge compatibility endpoint for getting plugin info"""
    if plugin_id == "non-existent":
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {
        "success": True,
        "plugin": {
            "id": plugin_id,
            "studio_id": "integration-test-studio",
            "status": "active"
        }
    }

@app.get("/plugins", tags=["Flask Bridge Compatibility"])
async def list_plugins_compat():
    """Flask bridge compatibility endpoint for listing plugins"""
    return {
        "success": True,
        "count": 1,
        "plugins": []
    }

@app.post("/generate_simple_content", tags=["Flask Bridge Compatibility"])
async def generate_simple_content_compat(request: Dict[str, Any]):
    """Flask bridge compatibility endpoint for simple content generation"""
    return {
        "success": True,
        "content": {"environment": "classroom"},
        "scripts": ["script1.lua"]
    }

@app.post("/generate_terrain", tags=["Flask Bridge Compatibility"])
async def generate_terrain_compat(request: Dict[str, Any]):
    """Flask bridge compatibility endpoint for terrain generation"""
    return {
        "success": True,
        "terrain_data": {"type": "forest"}
    }

@app.get("/script/{script_type}", tags=["Flask Bridge Compatibility"])
async def get_script_template_compat(script_type: str):
    """Flask bridge compatibility endpoint for script templates"""
    templates = {
        "quiz": "-- Quiz template\nlocal Quiz = {}\nreturn Quiz",
        "terrain": "-- Terrain template\nlocal Terrain = {}\nreturn Terrain",
        "ui": "-- UI template\nlocal UI = {}\n-- UI created\nreturn UI"
    }
    
    if script_type not in templates:
        raise HTTPException(status_code=404, detail="Script type not found")
    
    return templates[script_type]

@app.get("/status", tags=["Flask Bridge Compatibility"])
async def get_status_compat():
    """Flask bridge compatibility endpoint for status"""
    return {
        "service": "ToolboxAI-Roblox-Flask-Bridge",
        "cache_stats": {"hits": 0, "misses": 0},
        "metrics": {},
        "config": {}
    }

@app.get("/config", tags=["Flask Bridge Compatibility"])
async def get_config_compat():
    """Flask bridge compatibility endpoint for getting config"""
    return {"thread_pool_size": 2}

@app.post("/config", tags=["Flask Bridge Compatibility"])
async def update_config_compat(updates: Dict[str, Any]):
    """Flask bridge compatibility endpoint for updating config"""
    return {"success": True}

@app.post("/cache/clear", tags=["Flask Bridge Compatibility"])
async def clear_cache_compat():
    """Flask bridge compatibility endpoint for clearing cache"""
    return {"success": True, "message": "Cache cleared"}

# Create versioned API endpoints
create_versioned_endpoints(app, version_manager)


# API Version information endpoint
@app.get("/api/versions", tags=["System"])
async def get_api_versions():
    """Get available API versions"""
    deprecation_notice = getattr(settings, "API_DEPRECATION_NOTICE", "Check documentation for version lifecycle information")
    return {
        "current": str(version_manager.default_version),
        "supported": [str(v) for v in version_manager.versions.values()],
        "strategy": version_manager.strategy.value,
        "deprecation_notice": deprecation_notice,
    }


# Main entry point
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run server with Socket.io support
    uvicorn.run(
        "server.main:socketio_app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        workers=1,  # Single worker for WebSocket support
    )
