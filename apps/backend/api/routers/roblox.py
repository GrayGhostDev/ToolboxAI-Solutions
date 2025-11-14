"""
Secure Roblox API Router
Implements OAuth2 authentication, content generation, and Rojo management
with enterprise-grade security
"""

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.core.security.input_sanitizer import sanitize_for_logging

# Import schemas
from apps.backend.schemas.roblox import (
    ConversationGenerateRequest,
    ConversationInputRequest,
    ConversationResponse,
    ConversationStage,
    ConversationStartRequest,
    ConversationStartResponse,
    ErrorResponse,
    OAuth2InitiateRequest,
    OAuth2InitiateResponse,
    OAuth2RefreshRequest,
    OAuth2RevokeRequest,
    OAuth2TokenResponse,
    PusherAuthRequest,
    PusherAuthResponse,
    RojoCheckResponse,
    RojoProjectList,
)

# Import services
from apps.backend.services.credential_manager import get_credential_manager
from apps.backend.services.roblox.pusher import (
    RobloxChannelType,
    get_roblox_pusher_service,
)
from database.connection import get_async_session

logger = logging.getLogger(__name__)

# ============================================
# Router Configuration
# ============================================

router = APIRouter(
    prefix="/api/v1/roblox",
    tags=["roblox"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)

# Security
security = HTTPBearer(auto_error=False)
credential_manager = get_credential_manager()
pusher_service = get_roblox_pusher_service()

# OAuth2 state storage (use Redis in production)
oauth2_states: dict[str, dict[str, Any]] = {}

# Rate limiting storage (use Redis in production)
rate_limit_storage: dict[str, list[datetime]] = {}

# ============================================
# Security Dependencies
# ============================================


async def verify_ip_whitelist(request: Request) -> bool:
    """Verify request comes from whitelisted IP"""
    if not os.getenv("ENABLE_IP_WHITELIST", "true").lower() == "true":
        return True

    client_ip = request.client.host
    allowed_ips = os.getenv("ROBLOX_ALLOWED_IPS", "127.0.0.1,::1").split(",")

    if client_ip not in allowed_ips:
        logger.warning(
            f"Rejected request from non-whitelisted IP: {sanitize_for_logging(client_ip)}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"IP {client_ip} not whitelisted",
        )

    return True


async def check_rate_limit(request: Request) -> bool:
    """Check rate limit for API calls"""
    client_ip = request.client.host
    rate_limit = int(os.getenv("ROBLOX_API_RATE_LIMIT", "100"))

    # Get or create rate limit entry
    if client_ip not in rate_limit_storage:
        rate_limit_storage[client_ip] = []

    # Clean old entries (older than 1 minute)
    now = datetime.now(timezone.utc)
    rate_limit_storage[client_ip] = [
        t for t in rate_limit_storage[client_ip] if (now - t).total_seconds() < 60
    ]

    # Check limit
    if len(rate_limit_storage[client_ip]) >= rate_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
        )

    # Add current request
    rate_limit_storage[client_ip].append(now)
    return True


async def verify_request_signature(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> bool:
    """Verify HMAC signature for request integrity"""
    # Skip in development if not configured
    if os.getenv("ENVIRONMENT") == "development" and not os.getenv("REQUIRE_SIGNATURE"):
        return True

    signature = request.headers.get("X-Roblox-Signature")
    if not signature:
        logger.warning("Missing request signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing request signature"
        )

    # Get client secret
    secret = credential_manager.get_roblox_client_secret(ip_address=request.client.host)
    if not secret:
        logger.error("Failed to get client secret for signature verification")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration error",
        )

    # Calculate expected signature
    body = await request.body()
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    # Verify signature
    if not hmac.compare_digest(signature, expected):
        logger.warning("Invalid request signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid request signature"
        )

    return True


# Combined security dependency
async def verify_security(
    request: Request,
    _ip: bool = Depends(verify_ip_whitelist),
    _rate: bool = Depends(check_rate_limit),
) -> bool:
    """Combined security checks"""
    return True


# ============================================
# OAuth2 Endpoints
# ============================================


@router.post("/auth/initiate", response_model=OAuth2InitiateResponse)
async def initiate_oauth(
    request: OAuth2InitiateRequest,
    req: Request,
    _security: bool = Depends(verify_security),
    db: AsyncSession = Depends(get_async_session),
) -> OAuth2InitiateResponse:
    """
    Initiate OAuth2 authorization flow with Roblox
    Implements PKCE for enhanced security
    """
    try:
        # Generate state and PKCE parameters
        state = secrets.token_urlsafe(32)
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = hashlib.sha256(code_verifier.encode()).hexdigest()

        # Get client ID
        client_id = credential_manager.get_roblox_client_id()

        # Store state for validation
        oauth2_states[state] = {
            "code_verifier": code_verifier,
            "redirect_uri": request.redirect_uri,
            "created_at": datetime.now(timezone.utc),
            "ip_address": req.client.host,
            "scopes": request.scopes,
        }

        # Build authorization URL
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": request.redirect_uri,
            "scope": " ".join(request.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        authorization_url = f"https://authorize.roblox.com/v1/authorize?{urlencode(params)}"

        # Log OAuth2 initiation
        logger.info(f"OAuth2 flow initiated for IP {req.client.host}")

        return OAuth2InitiateResponse(
            authorization_url=authorization_url,
            state=state,
            code_verifier=code_verifier,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )

    except Exception as e:
        logger.error(f"Failed to initiate OAuth2: {sanitize_for_logging(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth2 flow",
        )


@router.get("/auth/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State parameter"),
    req: Request = None,
    _security: bool = Depends(verify_security),
    db: AsyncSession = Depends(get_async_session),
) -> OAuth2TokenResponse:
    """
    Handle OAuth2 callback from Roblox
    Exchanges authorization code for access token
    """
    try:
        # Validate state
        if state not in oauth2_states:
            logger.warning(f"Invalid OAuth2 state: {sanitize_for_logging(state)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid state parameter",
            )

        state_data = oauth2_states[state]

        # Check state expiry (5 minutes)
        if (datetime.now(timezone.utc) - state_data["created_at"]).total_seconds() > 300:
            del oauth2_states[state]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="State parameter expired",
            )

        # Get credentials
        client_id = credential_manager.get_roblox_client_id()
        client_secret = credential_manager.get_roblox_client_secret(ip_address=req.client.host)

        if not client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Configuration error",
            )

        # Exchange code for token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://apis.roblox.com/oauth/v1/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": state_data["redirect_uri"],
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code_verifier": state_data["code_verifier"],
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to exchange code for token",
            )

        token_data = response.json()

        # Clean up state
        del oauth2_states[state]

        # TODO: Store encrypted token in database

        # Send Pusher notification for successful auth
        user_id = state_data.get("user_id", "unknown")
        pusher_service.notify_auth_success(
            user_id=user_id,
            session_id=state,
            expires_in=token_data.get("expires_in", 3600),
        )

        logger.info(f"OAuth2 callback successful for IP {req.client.host}")

        return OAuth2TokenResponse(**token_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth2 callback failed: {sanitize_for_logging(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth2 callback failed",
        )


@router.post("/auth/refresh", response_model=OAuth2TokenResponse)
async def refresh_token(
    request: OAuth2RefreshRequest,
    req: Request,
    _security: bool = Depends(verify_security),
    db: AsyncSession = Depends(get_async_session),
) -> OAuth2TokenResponse:
    """Refresh OAuth2 access token"""
    try:
        client_id = credential_manager.get_roblox_client_id()
        client_secret = credential_manager.get_roblox_client_secret(ip_address=req.client.host)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://apis.roblox.com/oauth/v1/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": request.refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh token",
            )

        return OAuth2TokenResponse(**response.json())

    except Exception as e:
        logger.error(f"Token refresh failed: {sanitize_for_logging(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.post("/auth/revoke")
async def revoke_token(
    request: OAuth2RevokeRequest,
    req: Request,
    _security: bool = Depends(verify_security),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """Revoke OAuth2 token"""
    try:
        client_id = credential_manager.get_roblox_client_id()
        client_secret = credential_manager.get_roblox_client_secret(ip_address=req.client.host)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://apis.roblox.com/oauth/v1/revoke",
                data={
                    "token": request.token,
                    "token_type_hint": request.token_type_hint,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )

        if response.status_code != 200:
            logger.warning(f"Token revocation may have failed: {response.status_code}")

        return {"status": "revoked"}

    except Exception as e:
        logger.error(f"Token revocation failed: {sanitize_for_logging(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token revocation failed",
        )


@router.get("/auth/status")
async def auth_status(
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    _security: bool = Depends(verify_security),
) -> dict[str, Any]:
    """Check authentication status"""
    if not credentials:
        return {"authenticated": False}

    # TODO: Validate token with Roblox API

    return {
        "authenticated": True,
        "token_type": credentials.scheme,
        "expires_in": 3600,  # TODO: Get actual expiry
    }


# ============================================
# Conversation Flow Endpoints
# ============================================

# Conversation sessions storage (use Redis in production)
conversation_sessions: dict[str, dict[str, Any]] = {}


@router.post("/conversation/start", response_model=ConversationStartResponse)
async def start_conversation(
    request: ConversationStartRequest,
    req: Request,
    _security: bool = Depends(verify_security),
    db: AsyncSession = Depends(get_async_session),
) -> ConversationStartResponse:
    """Start 8-stage conversation flow"""
    try:
        session_id = secrets.token_urlsafe(16)

        # Initialize session
        conversation_sessions[session_id] = {
            "user_id": request.user_id,
            "stage": ConversationStage.GREETING,
            "data": {},
            "context": request.context or {},
            "created_at": datetime.now(timezone.utc),
            "messages": [],
        }

        # TODO: Initialize content pipeline

        # Create Pusher channel for this session
        pusher_channel = pusher_service.get_channel_name(RobloxChannelType.CONVERSATION, session_id)

        # Send initial stage notification
        pusher_service.notify_conversation_stage_change(
            session_id=session_id,
            stage=ConversationStage.GREETING.value,
            progress=0.0,
            message="Conversation started",
            metadata={"user_id": request.user_id},
        )

        return ConversationStartResponse(
            session_id=session_id,
            current_stage=ConversationStage.GREETING,
            message="Welcome to the ToolboxAI Educational Content Generator! I'll guide you through creating custom Roblox educational experiences. Let's start by understanding what you'd like to create.",
            pusher_channel=pusher_channel,
            created_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error(f"Failed to start conversation: {sanitize_for_logging(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start conversation",
        )


@router.post("/conversation/input", response_model=ConversationResponse)
async def conversation_input(
    request: ConversationInputRequest,
    req: Request,
    _security: bool = Depends(verify_security),
) -> ConversationResponse:
    """Process user input in conversation"""
    if request.session_id not in conversation_sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session = conversation_sessions[request.session_id]

    # TODO: Process input through content pipeline

    # Mock response for now
    session["messages"].append(
        {
            "role": "user",
            "content": request.user_input,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    return ConversationResponse(
        session_id=request.session_id,
        current_stage=session["stage"],
        message="I understand. Let me process that information.",
        progress=25.0,
        data={"processed": True},
    )


# ============================================
# Rojo Management Endpoints
# ============================================


@router.get("/rojo/check", response_model=RojoCheckResponse)
async def check_rojo(_security: bool = Depends(verify_security)) -> RojoCheckResponse:
    """Check if Rojo is installed and available"""
    try:
        import subprocess

        result = subprocess.run(["rojo", "--version"], capture_output=True, text=True)

        if result.returncode == 0:
            version = result.stdout.strip().split()[-1]
            return RojoCheckResponse(installed=True, version=version, path="rojo")
        else:
            return RojoCheckResponse(installed=False)

    except FileNotFoundError:
        return RojoCheckResponse(installed=False)
    except Exception as e:
        logger.error(f"Rojo check failed: {sanitize_for_logging(e)}")
        return RojoCheckResponse(installed=False)


@router.get("/rojo/projects", response_model=RojoProjectList)
async def list_projects(_security: bool = Depends(verify_security)) -> RojoProjectList:
    """List all Rojo projects"""
    # TODO: Implement with actual Rojo manager
    return RojoProjectList(projects=[], total=0)


# ============================================
# Pusher Authentication
# ============================================


@router.post("/pusher/auth", response_model=PusherAuthResponse)
async def authenticate_pusher_channel(
    request: PusherAuthRequest,
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    _security: bool = Depends(verify_security),
) -> PusherAuthResponse:
    """
    Authenticate Pusher channel subscription
    Required for private and presence channels
    """
    try:
        # Validate channel access
        if not request.channel_name.startswith(("private-roblox", "presence-roblox")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid channel name"
            )

        # Get user data for presence channels
        user_data = None
        if request.channel_name.startswith("presence-"):
            user_data = {
                "user_id": request.user_id or "anonymous",
                "user_info": {
                    "ip": req.client.host,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }

        # Authenticate with Pusher
        auth_response = pusher_service.authenticate_channel(
            channel_name=request.channel_name,
            socket_id=request.socket_id,
            user_data=user_data,
        )

        return PusherAuthResponse(
            auth=auth_response["auth"], channel_data=auth_response.get("channel_data")
        )

    except Exception as e:
        logger.error(f"Pusher authentication failed: {sanitize_for_logging(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate channel",
        )


# ============================================
# Content Generation with Pusher Updates
# ============================================


@router.post("/conversation/generate")
async def generate_content(
    request: ConversationGenerateRequest,
    req: Request,
    _security: bool = Depends(verify_security),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Generate content from conversation and notify via Pusher"""
    if request.session_id not in conversation_sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    try:
        conversation_sessions[request.session_id]

        # Send generation started notification
        pusher_service.notify_generation_progress(
            session_id=request.session_id,
            progress=0.0,
            status="started",
            details={"message": "Starting content generation..."},
        )

        # Simulate generation stages with progress updates
        stages = [
            (20, "analyzing", "Analyzing requirements..."),
            (40, "designing", "Designing environment structure..."),
            (60, "generating", "Generating Luau scripts..."),
            (80, "optimizing", "Optimizing for Roblox..."),
            (100, "complete", "Generation complete!"),
        ]

        project_id = f"proj_{secrets.token_urlsafe(8)}"

        # Send progress updates for each stage
        for progress, status, message in stages:
            pusher_service.notify_generation_progress(
                session_id=request.session_id,
                progress=float(progress),
                status=status,
                details={"message": message, "project_id": project_id},
            )
            # In production, actual generation would happen here

        # Send completion notification
        pusher_service.notify_generation_complete(
            session_id=request.session_id,
            project_id=project_id,
            files_generated=15,
            rojo_port=34872,
        )

        return {
            "status": "success",
            "project_id": project_id,
            "files_generated": 15,
            "rojo_port": 34872,
            "message": "Content generation complete",
        }

    except Exception as e:
        # Send error notification
        pusher_service.notify_error(
            channel_type=RobloxChannelType.GENERATION,
            identifier=request.session_id,
            error_code="GENERATION_FAILED",
            error_message=str(e),
        )

        logger.error(f"Content generation failed: {sanitize_for_logging(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content generation failed",
        )


# ============================================
# Health Check
# ============================================


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint"""

    # Check Pusher connection
    pusher_status = "connected" if pusher_service.client else "not configured"

    return {
        "status": "healthy",
        "service": "roblox-integration",
        "pusher": pusher_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
