"""
Pusher and Realtime Communication Router

Handles Pusher authentication, webhooks, and realtime event triggering.
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from apps.backend.api.auth.auth import get_current_user
from apps.backend.core.logging import log_audit, logging_manager
from apps.backend.models.schemas import User

logger = logging_manager.get_logger(__name__)

router = APIRouter(tags=["Realtime"])


@router.post("/pusher/auth")
async def authenticate_pusher_channel(
    request: Request, current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Authenticate Pusher channel access

    Args:
        request: Request object containing channel and socket_id
        current_user: Authenticated user

    Returns:
        JSONResponse: Pusher authentication response
    """
    try:
        # Parse request body
        body = await request.body()
        form_data = {}

        if body:
            # Parse form data
            content_type = request.headers.get("content-type", "")
            if "application/x-www-form-urlencoded" in content_type:
                from urllib.parse import parse_qs

                parsed = parse_qs(body.decode())
                form_data = {k: v[0] if v else "" for k, v in parsed.items()}
            elif "application/json" in content_type:
                form_data = json.loads(body.decode())

        # Extract channel name and socket ID
        channel_name = form_data.get("channel_name", "")
        socket_id = form_data.get("socket_id", "")

        if not channel_name or not socket_id:
            raise HTTPException(status_code=400, detail="Missing channel_name or socket_id")

        # Validate channel access permissions
        if not _can_access_channel(current_user, channel_name):
            raise HTTPException(status_code=403, detail="Insufficient permissions for this channel")

        # Authenticate with Pusher
        from apps.backend.services.pusher import (
            authenticate_channel as pusher_authenticate,
        )

        auth_response = pusher_authenticate(
            socket_id=socket_id,
            channel_name=channel_name,
            user_data={
                "user_id": current_user.id,
                "user_info": {
                    "id": current_user.id,
                    "name": getattr(current_user, "name", "Unknown"),
                    "role": getattr(current_user, "role", "student"),
                },
            },
        )

        # Log successful authentication
        log_audit(
            action="pusher_channel_authenticated",
            user_id=current_user.id,
            resource_type="pusher_channel",
            resource_id=channel_name,
            details={"socket_id": socket_id, "channel_name": channel_name},
        )

        return JSONResponse(content=auth_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pusher authentication failed: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.post("/pusher/webhook")
async def handle_pusher_webhook(request: Request) -> JSONResponse:
    """
    Handle Pusher webhook events

    Args:
        request: Request object containing webhook data

    Returns:
        JSONResponse: Webhook processing result
    """
    try:
        # Parse webhook body
        body = await request.body()
        webhook_data = json.loads(body.decode())

        # Verify webhook signature
        from apps.backend.services.pusher import verify_webhook as pusher_verify_webhook

        if not pusher_verify_webhook(
            key=request.headers.get("X-Pusher-Key", ""),
            signature=request.headers.get("X-Pusher-Signature", ""),
            body=body,
        ):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Process webhook events
        events = webhook_data.get("events", [])
        processed_events = []

        for event in events:
            try:
                result = await _process_webhook_event(event)
                processed_events.append(
                    {
                        "event": event.get("name"),
                        "channel": event.get("channel"),
                        "status": "processed",
                        "result": result,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to process webhook event: {e}")
                processed_events.append(
                    {
                        "event": event.get("name"),
                        "channel": event.get("channel"),
                        "status": "failed",
                        "error": str(e),
                    }
                )

        logger.info(f"Processed {len(processed_events)} webhook events")

        return JSONResponse(
            content={
                "status": "success",
                "data": {"events_processed": len(processed_events), "results": processed_events},
                "message": "Webhook processed successfully",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@router.post("/realtime/trigger")
async def trigger_realtime_event(
    request: Request, current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Trigger a realtime event via Pusher

    Args:
        request: Request object containing event data
        current_user: Authenticated user

    Returns:
        JSONResponse: Event trigger result
    """
    try:
        # Parse request body
        event_data = await request.json()

        # Extract event parameters
        channel = event_data.get("channel")
        event = event_data.get("event")
        data = event_data.get("data", {})

        if not channel or not event:
            raise HTTPException(status_code=400, detail="Missing required fields: channel, event")

        # Validate channel access permissions
        if not _can_trigger_event(current_user, channel, event):
            raise HTTPException(
                status_code=403, detail="Insufficient permissions to trigger this event"
            )

        # Trigger event via Pusher
        from apps.backend.services.pusher import trigger_event as pusher_trigger_event

        result = pusher_trigger_event(channel=channel, event=event, data=data)

        # Log event trigger
        log_audit(
            action="realtime_event_triggered",
            user_id=current_user.id,
            resource_type="pusher_event",
            resource_id=f"{channel}:{event}",
            details={"channel": channel, "event": event, "data_size": len(str(data))},
        )

        return JSONResponse(
            content={
                "status": "success",
                "data": {"channel": channel, "event": event, "triggered": True, "result": result},
                "message": "Event triggered successfully",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger realtime event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger event: {str(e)}")


@router.get("/pusher/stats")
async def get_pusher_stats(current_user: User = Depends(get_current_user)) -> JSONResponse:
    """
    Get Pusher service statistics

    Args:
        current_user: Authenticated user

    Returns:
        JSONResponse: Pusher statistics
    """
    try:
        # Only allow admin users to view stats
        if not _user_has_role(current_user, ["admin"]):
            raise HTTPException(status_code=403, detail="Admin access required")

        from apps.backend.services.pusher_realtime import get_pusher_status

        stats = get_pusher_status()

        return JSONResponse(
            content={
                "status": "success",
                "data": stats,
                "message": "Pusher statistics retrieved successfully",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Pusher stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve Pusher statistics: {str(e)}"
        )


def _can_access_channel(user: User, channel_name: str) -> bool:
    """
    Check if user can access a specific channel

    Args:
        user: User object
        channel_name: Name of the channel

    Returns:
        bool: True if user can access the channel
    """
    # Public channels are accessible to all authenticated users
    if not channel_name.startswith("private-") and not channel_name.startswith("presence-"):
        return True

    # Private channels require specific permissions
    user_role = getattr(user, "role", "student")

    # Admin users can access all channels
    if user_role == "admin":
        return True

    # User-specific private channels
    if channel_name == f"private-user-{user.id}":
        return True

    # Role-based channels
    if channel_name == f"private-{user_role}":
        return True

    # Teachers can access teacher and student channels
    if user_role == "teacher" and (
        channel_name.startswith("private-student-") or channel_name.startswith("private-class-")
    ):
        return True

    return False


def _can_trigger_event(user: User, channel: str, event: str) -> bool:
    """
    Check if user can trigger an event on a channel

    Args:
        user: User object
        channel: Channel name
        event: Event name

    Returns:
        bool: True if user can trigger the event
    """
    user_role = getattr(user, "role", "student")

    # Admin users can trigger any event
    if user_role == "admin":
        return True

    # Teachers can trigger educational events
    if user_role == "teacher" and (
        event.startswith("content-")
        or event.startswith("lesson-")
        or event.startswith("assessment-")
    ):
        return True

    # Users can trigger events on their own channels
    if channel == f"private-user-{user.id}":
        return True

    return False


def _user_has_role(user: User, required_roles: list) -> bool:
    """
    Check if user has any of the required roles

    Args:
        user: User object
        required_roles: List of required roles

    Returns:
        bool: True if user has any required role
    """
    user_role = getattr(user, "role", None)
    return user_role in required_roles if user_role else False


async def _process_webhook_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    Process a single webhook event

    Args:
        event: Webhook event data

    Returns:
        Dict: Processing result
    """
    event_name = event.get("name", "")
    channel = event.get("channel", "")
    data = event.get("data", {})

    # Log the event
    logger.info(f"Processing webhook event: {event_name} on {channel}")

    # Handle different event types
    if event_name == "channel_occupied":
        return {"action": "channel_occupied", "channel": channel}
    elif event_name == "channel_vacated":
        return {"action": "channel_vacated", "channel": channel}
    elif event_name == "member_added":
        return {"action": "member_added", "channel": channel, "data": data}
    elif event_name == "member_removed":
        return {"action": "member_removed", "channel": channel, "data": data}
    else:
        return {"action": "unknown_event", "event": event_name}
