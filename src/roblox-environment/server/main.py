"""
FastAPI Main Application for ToolboxAI Roblox Environment

Main FastAPI server (port 8008) with comprehensive features:
- Educational content generation endpoints
- WebSocket support for real-time updates
- Integration with agents, swarm, SPARC, and MCP systems
- Health monitoring and metrics
- Authentication and rate limiting
- CORS configuration for multi-platform access
"""

import asyncio
import logging
import subprocess
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from enum import Enum

import requests  # pylint: disable=import-error
import uvicorn  # pylint: disable=import-error
from fastapi import (  # pylint: disable=import-error
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    status,
)
from fastapi.middleware.cors import CORSMiddleware  # pylint: disable=import-error
from fastapi.middleware.trustedhost import (  # pylint: disable=import-error
    TrustedHostMiddleware,
)
from fastapi.responses import JSONResponse  # pylint: disable=import-error
from fastapi.security import HTTPBearer  # pylint: disable=import-error
from pydantic import ValidationError

from .agent import (
    agent_manager,
    generate_educational_content,
    get_agent_health,
    initialize_agents,
    shutdown_agents,
)
from .auth import (
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    get_current_session,
    get_current_user,
    initialize_auth,
    rate_limit,
    require_any_role,
    require_role,
)

# Import our modules
from .config import settings
from .models import (
    BaseResponse,
    ContentRequest,
    ContentResponse,
    ErrorResponse,
    HealthCheck,
    LMSCourse,
    PluginMessage,
    PluginRegistration,
    Quiz,
    QuizResponse,
    UsageMetrics,
    User,
)
from .websocket import broadcast_content_update, websocket_endpoint, websocket_manager

logger = logging.getLogger(__name__)


# Import security modules
from .security_middleware import (
    SecurityMiddleware,
    RateLimitConfig,
    CircuitBreakerConfig,
)
from .secrets_manager import init_secrets_manager, get_required_secret

# Import new middleware modules
from .api_versioning import (
    VersionManager,
    VersionStrategy,
    APIVersionMiddleware,
    create_version_manager,
    create_versioned_endpoints,
)
from .compression_middleware import (
    CompressionMiddleware,
    CompressionConfig,
)
from .error_handling import (
    ErrorHandlingMiddleware,
    create_error_handling_middleware,
)


# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    # Startup
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)

    # Initialize secrets manager
    try:
        init_secrets_manager(auto_rotate=True)
        logger.info("Secrets manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize secrets manager: {e}")
        # Continue with environment variables as fallback

    # Set start time for uptime calculation
    app.state.start_time = time.time()

    # Initialize authentication system
    initialize_auth()

    # Initialize agent system with error handling
    try:
        await initialize_agents()
        logger.info("Agent system initialized successfully")
    except (ImportError, AttributeError, RuntimeError, ValueError) as e:
        logger.error(f"Failed to initialize agent system: {e}")
        logger.warning("Agent features will be limited - running in fallback mode")

    # Start Flask bridge server if not running
    try:
        await ensure_flask_server_running()
        logger.info("Flask bridge server started successfully")
    except (subprocess.SubprocessError, OSError, RuntimeError) as e:
        logger.error(f"Failed to start Flask bridge server: {e}")
        logger.warning("Roblox plugin communication may be unavailable")

    # Start background tasks and track them for proper shutdown
    try:
        app.state.cleanup_task = asyncio.create_task(cleanup_stale_connections())
        app.state.metrics_task = asyncio.create_task(collect_metrics())
    except (asyncio.CancelledError, RuntimeError) as e:
        logger.warning(f"Failed to create background tasks: {e}")

    logger.info(
        f"FastAPI server ready on {settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}"
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
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Educational Roblox Environment - Generate immersive educational content with AI agents",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Initialize version manager
version_manager = create_version_manager(
    default_version="2.0.0", strategy=VersionStrategy.URL_PATH
)

# Security
security = HTTPBearer()

# Middleware configuration

# Add error handling middleware (must be first to catch all errors)
app.add_middleware(ErrorHandlingMiddleware, debug=settings.DEBUG)

# Add compression middleware
app.add_middleware(
    CompressionMiddleware,
    config=CompressionConfig(
        minimum_size=1024,  # Compress responses larger than 1KB
        compression_level=6,
        prefer_brotli=True,
    ),
)

# Add API versioning middleware
app.add_middleware(APIVersionMiddleware, version_manager=version_manager)

# Add security middleware with rate limiting and circuit breaker
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
    max_request_size=10 * 1024 * 1024,  # 10MB
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "*.roblox.com"]
)


# Global exception handlers
@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            message=exc.detail,
            error_type="AuthenticationError",
            details=[],
        ).model_dump(),
    )


@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            message=exc.detail,
            error_type="AuthorizationError",
            details=[],
        ).model_dump(),
    )


@app.exception_handler(RateLimitError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False, message=exc.detail, error_type="RateLimitError", details=[]
        ).model_dump(),
        headers=exc.headers,
    )


def get_field_path(error):
    """Extract field path from validation error"""
    if isinstance(error, dict):
        return ".".join([str(loc) for loc in error.get("loc", [])])
    return ""


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            success=False,
            message="Validation error",
            error_type="ValidationError",
            details=[
                {
                    "code": "validation_error",
                    "message": str(error),
                    "field": get_field_path(error),
                }
                for error in exc.errors()
            ],
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Sanitize exception message to prevent log injection
    safe_exc_msg = str(exc)[:500].replace("\n", "").replace("\r", "")
    logger.error(f"Unhandled exception: {safe_exc_msg}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            message="Internal server error",
            error_type="InternalServerError",
            details=[],
        ).model_dump(),
    )


# Middleware for request tracking
@app.middleware("http")
async def track_requests(request: Request, call_next):
    start_time = time.time()

    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

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

    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Health and monitoring endpoints
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

        return HealthCheck(
            status=overall_status,
            version=settings.APP_VERSION,
            checks=all_checks,
            uptime=(
                time.time() - app.state.start_time
                if hasattr(app.state, "start_time")
                else 0
            ),
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status="unhealthy",
            version=settings.APP_VERSION,
            checks={"error": False},
            uptime=0,
        )


@app.get("/metrics", tags=["System"])
async def get_metrics():
    """Get system metrics"""
    try:
        agent_health = await get_agent_health()
        ws_stats = await websocket_manager.get_connection_stats()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": agent_health,
            "websockets": ws_stats,
            "system": {
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
                "version": settings.APP_VERSION,
            },
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail="Metrics unavailable")


@app.get("/info", response_model=BaseResponse, tags=["System"])
async def get_info():
    """Get application information"""
    return BaseResponse(
        success=True,
        message=f"{settings.APP_NAME} v{settings.APP_VERSION} is running",
        timestamp=datetime.now(timezone.utc),
    )


# Authentication models
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


# Authentication endpoints
@app.post("/auth/token", tags=["Authentication"])
async def create_access_token(login_request: LoginRequest):
    """Create JWT access token (simplified for demo)"""
    # In production, this would validate against a database
    demo_username = getattr(settings, "DEMO_USERNAME", None)
    demo_password = getattr(settings, "DEMO_PASSWORD", None)

    if not demo_username or not demo_password:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

    if (
        login_request.username == demo_username
        and login_request.password == demo_password
    ):
        from .auth import create_user_token
        from .models import User

        user = User(
            id=str(uuid.uuid4()),
            username=login_request.username,
            email=f"{login_request.username}@example.com",
            role="teacher",
        )

        token = create_user_token(user)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user.model_dump(),
        }

    raise HTTPException(status_code=401, detail="Invalid credentials")


# Educational content generation endpoints
@app.post(
    "/generate_content", response_model=ContentResponse, tags=["Content Generation"]
)
@rate_limit(max_requests=10, window_seconds=60)
async def generate_content(
    request: Request,  # FastAPI Request for rate limiting
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

        # Generate content using agent system
        response = await generate_educational_content(content_request, current_user)

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
        )


@app.post("/generate_quiz", response_model=QuizResponse, tags=["Content Generation"])
@rate_limit(max_requests=15, window_seconds=60)
async def generate_quiz(
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
        from .tools import RobloxQuizGenerator

        quiz_generator = RobloxQuizGenerator()
        # Use asyncio.to_thread for better resource management
        import asyncio

        result = await asyncio.to_thread(
            quiz_generator._run,
            subject,
            topic,
            difficulty,
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
            passing_score=quiz_data.get("passing_score"),
            max_attempts=quiz_data.get("max_attempts"),
            shuffle_questions=quiz_data.get("shuffle_questions"),
            shuffle_options=quiz_data.get("shuffle_options"),
            show_results=quiz_data.get("show_results"),
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


@app.post("/generate_terrain", tags=["Content Generation"])
@rate_limit(max_requests=5, window_seconds=60)
async def generate_terrain(
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

        terrain_generator = RobloxTerrainGenerator()
        result = await asyncio.to_thread(
            terrain_generator._run,
            theme,
            size,
            biome,
            features or [],
            educational_context,
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
                "message": message.model_dump(),
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


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint_route(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket_endpoint(websocket)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint_with_id(websocket: WebSocket, client_id: str):
    """WebSocket endpoint with specific client ID"""
    await websocket_endpoint(websocket, client_id)


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

    # Run server
    uvicorn.run(
        "server.main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        workers=1,  # Single worker for WebSocket support
    )
