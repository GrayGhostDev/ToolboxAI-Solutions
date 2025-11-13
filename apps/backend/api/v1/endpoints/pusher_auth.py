"""
Pusher authentication endpoint for frontend connections.

This endpoint provides robust JWT-based authentication for Pusher channels,
supporting both private and presence channels with proper user validation.
"""

import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from apps.backend.api.auth.auth import AuthenticationError, JWTManager, get_current_user
from apps.backend.core.config import settings
from apps.backend.models.schemas import User
from apps.backend.services.pusher import PusherUnavailable, authenticate_channel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pusher",
    tags=["pusher"],
)

# Additional router for realtime endpoints
realtime_router = APIRouter(
    prefix="/realtime",
    tags=["realtime"],
)

security = HTTPBearer(auto_error=False)


class PusherAuthRequest(BaseModel):
    socket_id: str
    channel_name: str


class PusherAuthResponse(BaseModel):
    auth: str
    channel_data: Optional[str] = None
    shared_secret: Optional[str] = None


class TriggerEventRequest(BaseModel):
    """Request model for triggering Pusher events"""

    channel: str
    event: str
    data: Dict[str, Any]


async def _get_user_from_auth_header(request: Request) -> Optional[User]:
    """
    Extract and validate user from Authorization header.
    Returns None if no valid token is found.
    """
    try:
        auth_header = request.headers.get("Authorization", "")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")

        # Handle development tokens
        if token.startswith("dev-token-") and settings.DEBUG:
            logger.info("Using development token for Pusher auth")
            return User(
                id="dev-user-001", username="dev_user", email="dev@toolboxai.com", role="teacher"
            )

        # Validate JWT token
        payload = JWTManager.verify_token(token, raise_on_error=False)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        # Create user from JWT payload
        return User(
            id=user_id,
            username=payload.get("username", "unknown"),
            email=payload.get("email", "unknown@example.com"),
            role=payload.get("role", "student"),
        )

    except Exception as e:
        logger.warning(f"Error extracting user from auth header: {e}")
        return None


def _can_access_channel(user: Optional[User], channel_name: str) -> bool:
    """
    Check if user can access a specific Pusher channel.

    Args:
        user: User object (None for public channels)
        channel_name: Name of the channel to access

    Returns:
        bool: True if access is allowed
    """
    # Public channels are accessible without authentication
    if not channel_name.startswith(("private-", "presence-")):
        return True

    # Private/presence channels require authentication
    if not user:
        return False

    user_role = getattr(user, "role", "student")
    user_id = str(user.id)

    # Admin users can access all channels
    if user_role == "admin":
        return True

    # User-specific channels
    if channel_name in [f"private-user-{user_id}", f"presence-user-{user_id}"]:
        return True

    # Role-based channels
    if channel_name in [f"private-{user_role}", f"presence-{user_role}"]:
        return True

    # Teacher-specific channels
    if user_role == "teacher" and channel_name.startswith(("private-class-", "presence-class-")):
        return True

    # Common educational channels
    educational_channels = [
        "private-dashboard-updates",
        "presence-dashboard-updates",
        "private-content-generation",
        "presence-content-generation",
    ]

    if channel_name in educational_channels:
        return True

    logger.warning(f"Access denied for user {user_id} ({user_role}) to channel {channel_name}")
    return False


@router.post("/auth", response_model=Dict[str, Any])
async def pusher_auth(request: Request) -> Dict[str, Any]:
    """
    Authenticate Pusher channel subscription.

    This endpoint handles both private and presence channel authentication.
    It supports both JSON and form-encoded requests from Pusher clients.

    Authentication flow:
    1. Extract socket_id and channel_name from request
    2. Validate JWT token from Authorization header
    3. Check channel access permissions
    4. Generate Pusher authentication signature

    For presence channels, user info is included in the authentication.
    """
    try:
        # Parse the request body - handle both JSON and form data
        content_type = request.headers.get("content-type", "")
        body = {}

        if "application/json" in content_type:
            body = await request.json()
        elif "application/x-www-form-urlencoded" in content_type:
            # Handle form data from Pusher JavaScript client
            form_data = await request.form()
            body = {
                "socket_id": form_data.get("socket_id"),
                "channel_name": form_data.get("channel_name"),
            }
        else:
            # Try to parse as JSON anyway (fallback)
            try:
                body = await request.json()
            except:
                raise HTTPException(status_code=400, detail="Invalid request format")

        # Validate required fields
        socket_id = body.get("socket_id")
        channel_name = body.get("channel_name")

        if not socket_id or not channel_name:
            raise HTTPException(
                status_code=400, detail="Missing required fields: socket_id and channel_name"
            )

        logger.info(f"Pusher auth request for channel: {channel_name}")

        # Get user from Authorization header (if present)
        current_user = await _get_user_from_auth_header(request)

        # Check channel access permissions
        if not _can_access_channel(current_user, channel_name):
            raise HTTPException(status_code=403, detail="Insufficient permissions for this channel")

        # Prepare user data for presence channels
        user_id = None
        user_info = None

        if current_user and channel_name.startswith(("private-", "presence-")):
            user_id = str(current_user.id)
            user_info = {
                "id": user_id,
                "name": getattr(current_user, "name", current_user.username),
                "username": current_user.username,
                "email": current_user.email,
                "role": current_user.role,
            }

        # Authenticate the channel with Pusher
        auth_response = authenticate_channel(
            socket_id=socket_id, channel_name=channel_name, user_id=user_id, user_info=user_info
        )

        logger.info(
            f"Successfully authenticated channel {channel_name} for user {user_id or 'anonymous'}"
        )
        return auth_response

    except PusherUnavailable as e:
        logger.error(f"Pusher service unavailable: {e}")
        raise HTTPException(status_code=503, detail="Pusher service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error authenticating Pusher channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to authenticate channel")


@router.post("/trigger")
async def trigger_pusher_event(
    request: TriggerEventRequest, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Trigger a Pusher event on a specified channel.

    This endpoint allows authenticated users to trigger events via Pusher,
    with proper authorization checks based on user role and channel permissions.

    Authentication required: JWT token in Authorization header
    """
    try:
        # Import here to avoid circular imports
        from apps.backend.services.pusher import trigger_event

        # Validate channel access permissions
        if not _can_trigger_event(current_user, request.channel, request.event):
            raise HTTPException(
                status_code=403, detail="Insufficient permissions to trigger this event"
            )

        # Add user context to event data
        event_data = {
            **request.data,
            "_meta": {
                "triggered_by": str(current_user.id),
                "user_role": current_user.role,
                "timestamp": "utc_now",
            },
        }

        # Trigger the event
        result = trigger_event(channel=request.channel, event=request.event, data=event_data)

        logger.info(
            f"Event '{request.event}' triggered on channel '{request.channel}' "
            f"by user {current_user.id} ({current_user.role})"
        )

        return {
            "success": True,
            "channel": request.channel,
            "event": request.event,
            "triggered_by": str(current_user.id),
            "result": result,
        }

    except PusherUnavailable as e:
        logger.error(f"Pusher service unavailable: {e}")
        raise HTTPException(status_code=503, detail="Pusher service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering Pusher event: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger event")


def _can_trigger_event(user: User, channel: str, event: str) -> bool:
    """
    Check if user can trigger an event on a specific channel.

    Args:
        user: User object
        channel: Channel name
        event: Event name

    Returns:
        bool: True if user can trigger the event
    """
    user_role = getattr(user, "role", "student")
    user_id = str(user.id)

    # Admin users can trigger any event
    if user_role == "admin":
        return True

    # Teachers can trigger educational events
    if user_role == "teacher":
        teacher_events = [
            "content-created",
            "content-updated",
            "content-deleted",
            "lesson-started",
            "lesson-completed",
            "lesson-updated",
            "assessment-created",
            "assessment-updated",
            "assessment-graded",
            "class-announcement",
            "homework-assigned",
        ]
        if any(event.startswith(prefix) for prefix in teacher_events):
            return True

    # Users can trigger events on their personal channels
    personal_channels = [f"private-user-{user_id}", f"presence-user-{user_id}"]
    if channel in personal_channels:
        # Allow most personal events but restrict dangerous ones
        dangerous_events = ["admin-", "system-", "delete-user", "modify-permissions"]
        if not any(event.startswith(prefix) for prefix in dangerous_events):
            return True

    # Students can trigger student-specific events
    if user_role == "student":
        student_events = [
            "progress-updated",
            "assignment-submitted",
            "question-asked",
            "activity-completed",
            "badge-earned",
        ]
        if any(event.startswith(prefix) for prefix in student_events):
            return True

    # Common events that all authenticated users can trigger
    common_events = ["user-status-updated", "typing-indicator", "user-joined", "user-left"]
    if event in common_events:
        return True

    logger.warning(
        f"Event trigger denied: user {user_id} ({user_role}) "
        f"cannot trigger '{event}' on channel '{channel}'"
    )
    return False


@router.post("/webhook")
async def pusher_webhook(request: Request):
    """
    Handle Pusher webhooks for channel lifecycle events.

    This endpoint processes webhooks from Pusher for events like:
    - channel_occupied: When the first user joins a channel
    - channel_vacated: When the last user leaves a channel
    - member_added: When a user joins a presence channel
    - member_removed: When a user leaves a presence channel
    """
    try:
        body = await request.body()
        headers = dict(request.headers)

        # Log webhook for debugging
        logger.info(f"Received Pusher webhook: {body[:200]}")

        # In production, verify webhook signature
        from apps.backend.services.pusher import verify_webhook

        webhook_events = verify_webhook(headers, body.decode())
        if webhook_events is None:
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Process webhook events
        processed = []
        for event in webhook_events.get("events", []):
            event_name = event.get("name")
            channel = event.get("channel")

            logger.info(f"Processing webhook event: {event_name} on {channel}")
            processed.append({"event": event_name, "channel": channel, "processed": True})

        return {"status": "success", "events_processed": len(processed), "events": processed}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Pusher webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook")


# Realtime endpoints
@realtime_router.post("/trigger")
async def realtime_trigger_event(
    request: TriggerEventRequest, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Trigger a realtime event via Pusher.

    This endpoint provides the same functionality as `/pusher/trigger` but
    under the `/realtime` namespace for API consistency.

    POST /realtime/trigger
    {
        "channel": "my-channel",
        "event": "my-event",
        "data": {"message": "Hello World"}
    }

    Authentication required: JWT token in Authorization header
    """
    try:
        # Import here to avoid circular imports
        from datetime import datetime, timezone

        from apps.backend.services.pusher import trigger_event

        # Validate channel access permissions
        if not _can_trigger_event(current_user, request.channel, request.event):
            raise HTTPException(
                status_code=403, detail="Insufficient permissions to trigger this event"
            )

        # Add user context and timestamp to event data
        event_data = {
            **request.data,
            "_meta": {
                "triggered_by": str(current_user.id),
                "user_role": current_user.role,
                "username": current_user.username,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        # Trigger the event
        result = trigger_event(channel=request.channel, event=request.event, data=event_data)

        logger.info(
            f"Realtime event '{request.event}' triggered on channel '{request.channel}' "
            f"by user {current_user.id} ({current_user.role})"
        )

        return {
            "status": "success",
            "message": "Event triggered successfully",
            "data": {
                "channel": request.channel,
                "event": request.event,
                "triggered_by": str(current_user.id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "result": result,
        }

    except PusherUnavailable as e:
        logger.error(f"Pusher service unavailable: {e}")
        raise HTTPException(status_code=503, detail="Pusher service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering realtime event: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger event")


@realtime_router.get("/status")
async def realtime_status(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get the status of the realtime system (Pusher).

    Returns information about Pusher configuration and connectivity.
    """
    try:
        from apps.backend.services.pusher import get_pusher_service

        # Only admins can view detailed status
        if current_user.role != "admin":
            return {
                "status": "success",
                "message": "Realtime system operational",
                "service": "pusher",
                "user_access": True,
            }

        # Get Pusher service status for admin users
        pusher_service = get_pusher_service()

        return {
            "status": "success",
            "message": "Realtime system status retrieved",
            "service": "pusher",
            "configuration": {
                "cluster": settings.PUSHER_CLUSTER,
                "ssl": settings.PUSHER_SSL,
                "app_id": settings.PUSHER_APP_ID[:8] + "..." if settings.PUSHER_APP_ID else None,
                "key": settings.PUSHER_KEY[:8] + "..." if settings.PUSHER_KEY else None,
            },
            "user_access": True,
            "admin_access": True,
        }

    except PusherUnavailable as e:
        logger.error(f"Pusher service unavailable: {e}")
        raise HTTPException(status_code=503, detail="Realtime service unavailable")
    except Exception as e:
        logger.error(f"Error getting realtime status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")


# Export both routers for registration
__all__ = ["router", "realtime_router"]
