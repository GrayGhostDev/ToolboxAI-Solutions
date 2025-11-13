"""
Pusher-based endpoints to replace WebSocket endpoints

These endpoints use Pusher for real-time communication instead of direct WebSocket connections.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from apps.backend.api.auth.auth import get_current_user, require_role
from apps.backend.models.schemas import User
from apps.backend.services.pusher import PusherUnavailable
from apps.backend.services.pusher import trigger_event as pusher_trigger_event
from apps.backend.services.pusher_handler import (
    broadcast_message,
    handle_pusher_message,
    pusher_handler,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pusher", tags=["Pusher"])


class PusherMessageRequest(BaseModel):
    """Request model for sending messages through Pusher"""

    message_type: str = Field(..., description="Type of message to send")
    payload: dict[str, Any] = Field(default={}, description="Message payload")
    channel: str | None = Field(None, description="Specific channel to use")


class EnvironmentCreateRequest(BaseModel):
    """Request model for environment creation"""

    environment_type: str = Field(..., description="Type of environment to create")
    config: dict[str, Any] = Field(default={}, description="Environment configuration")
    spec: dict[str, Any] | None = Field(None, description="Environment specification")


class AnalyticsRequest(BaseModel):
    """Request model for analytics data"""

    metric_type: str = Field(default="all", description="Type of metrics to retrieve")
    include_realtime: bool = Field(default=True, description="Include real-time updates")


class RobloxSyncRequest(BaseModel):
    """Request model for Roblox synchronization"""

    action: str = Field(..., description="Synchronization action")
    data: dict[str, Any] = Field(default={}, description="Synchronization data")


@router.post("/message")
async def send_pusher_message(
    request: PusherMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Send a message through Pusher channels

    Replaces direct WebSocket message sending with Pusher-based messaging.
    """
    try:
        # Handle the message through Pusher
        await handle_pusher_message(
            message_type=request.message_type,
            payload=request.payload,
            user_id=str(current_user.id),
            channel=request.channel,
        )

        return {
            "success": True,
            "message": "Message sent successfully",
            "user_id": str(current_user.id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except PusherUnavailable:
        raise HTTPException(status_code=503, detail="Pusher service temporarily unavailable")
    except Exception as e:
        logger.error(f"Error sending Pusher message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.post("/environment/create")
async def create_environment(
    request: EnvironmentCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Create an environment with real-time progress updates through Pusher

    Replaces WebSocket-based environment creation endpoint.
    """
    try:
        request_id = str(uuid.uuid4())
        user_channel = f"private-user-{current_user.id}"

        # Send initial acknowledgment
        pusher_trigger_event(
            user_channel,
            "environment_creation_started",
            {
                "request_id": request_id,
                "environment_type": request.environment_type,
                "user_id": str(current_user.id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Handle environment creation in background
        background_tasks.add_task(
            handle_pusher_message,
            "environment_create",
            {
                "type": request.environment_type,
                "config": request.config,
                "spec": request.spec,
                "request_id": request_id,
            },
            str(current_user.id),
        )

        return {
            "success": True,
            "request_id": request_id,
            "message": "Environment creation started",
            "channel": user_channel,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error creating environment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create environment: {str(e)}")


@router.post("/analytics/realtime")
async def get_realtime_analytics(
    request: AnalyticsRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Subscribe to real-time analytics updates through Pusher

    Replaces WebSocket-based analytics endpoint.
    """
    try:
        # Check user permissions for analytics
        if current_user.role not in ["admin", "teacher"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions for analytics")

        analytics_channel = "presence-analytics-realtime"

        # Subscribe user to analytics channel
        pusher_handler.subscribe_user_to_channel(str(current_user.id), analytics_channel)

        # Trigger initial analytics data
        background_tasks.add_task(
            handle_pusher_message,
            "analytics_request",
            {"metric_type": request.metric_type, "user_id": str(current_user.id)},
            str(current_user.id),
            analytics_channel,
        )

        return {
            "success": True,
            "channel": analytics_channel,
            "message": "Subscribed to real-time analytics",
            "metric_type": request.metric_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subscribing to analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to subscribe to analytics: {str(e)}")


@router.post("/roblox/sync")
async def sync_roblox_studio(
    request: RobloxSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Synchronize with Roblox Studio through Pusher

    Replaces WebSocket-based Roblox synchronization endpoint.
    """
    try:
        roblox_channel = f"private-roblox-{current_user.id}"

        # Process Roblox synchronization request
        background_tasks.add_task(
            handle_pusher_message,
            "roblox_sync",
            {"action": request.action, "data": request.data, "user_id": str(current_user.id)},
            str(current_user.id),
            roblox_channel,
        )

        # Send acknowledgment
        pusher_trigger_event(
            roblox_channel,
            "sync_acknowledged",
            {
                "action": request.action,
                "status": "processing",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        return {
            "success": True,
            "channel": roblox_channel,
            "action": request.action,
            "status": "synchronizing",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error synchronizing with Roblox: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to synchronize with Roblox: {str(e)}")


@router.post("/subscribe")
async def subscribe_to_channel(
    channel: str,
    current_user: User = Depends(get_current_user),
):
    """
    Subscribe user to a Pusher channel

    Handles channel subscription with proper authentication.
    """
    try:
        # Add user to tracking if not already present
        if not pusher_handler.get_user_info(str(current_user.id)):
            pusher_handler.add_user(
                str(current_user.id),
                {
                    "username": current_user.username,
                    "role": current_user.role,
                    "email": current_user.email,
                },
            )

        # Subscribe to channel
        success = pusher_handler.subscribe_user_to_channel(str(current_user.id), channel)

        if success:
            return {
                "success": True,
                "channel": channel,
                "user_id": str(current_user.id),
                "message": f"Successfully subscribed to {channel}",
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to subscribe to {channel}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subscribing to channel {channel}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to subscribe: {str(e)}")


@router.post("/unsubscribe")
async def unsubscribe_from_channel(
    channel: str,
    current_user: User = Depends(get_current_user),
):
    """
    Unsubscribe user from a Pusher channel
    """
    try:
        success = pusher_handler.unsubscribe_user_from_channel(str(current_user.id), channel)

        if success:
            return {
                "success": True,
                "channel": channel,
                "user_id": str(current_user.id),
                "message": f"Successfully unsubscribed from {channel}",
            }
        else:
            return {
                "success": False,
                "channel": channel,
                "user_id": str(current_user.id),
                "message": "User was not subscribed to this channel",
            }

    except Exception as e:
        logger.error(f"Error unsubscribing from channel {channel}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unsubscribe: {str(e)}")


@router.get("/user/channels")
async def get_user_channels(
    current_user: User = Depends(get_current_user),
):
    """
    Get list of channels the current user is subscribed to
    """
    try:
        user_info = pusher_handler.get_user_info(str(current_user.id))

        if user_info:
            return {
                "success": True,
                "user_id": str(current_user.id),
                "channels": list(user_info.get("channels", set())),
                "connected_at": user_info.get("connected_at"),
            }
        else:
            return {
                "success": True,
                "user_id": str(current_user.id),
                "channels": [],
                "message": "User not currently connected",
            }

    except Exception as e:
        logger.error(f"Error getting user channels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get channels: {str(e)}")


@router.post("/broadcast")
async def broadcast_to_channel(
    channel: str,
    event: str,
    data: dict[str, Any],
    current_user: User = Depends(require_role("admin")),
):
    """
    Broadcast a message to a Pusher channel (admin only)
    """
    try:
        await broadcast_message(channel, event, data)

        return {
            "success": True,
            "channel": channel,
            "event": event,
            "message": "Broadcast sent successfully",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except PusherUnavailable:
        raise HTTPException(status_code=503, detail="Pusher service temporarily unavailable")
    except Exception as e:
        logger.error(f"Error broadcasting to channel {channel}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to broadcast: {str(e)}")


@router.delete("/disconnect")
async def disconnect_user(
    current_user: User = Depends(get_current_user),
):
    """
    Disconnect user from all Pusher channels
    """
    try:
        pusher_handler.remove_user(str(current_user.id))

        return {
            "success": True,
            "user_id": str(current_user.id),
            "message": "User disconnected from all channels",
        }

    except Exception as e:
        logger.error(f"Error disconnecting user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")
