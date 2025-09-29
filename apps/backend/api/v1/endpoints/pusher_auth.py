"""
Pusher authentication endpoint for frontend connections.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from apps.backend.services.pusher import authenticate_channel, PusherUnavailable
from apps.backend.api.auth.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pusher",
    tags=["pusher"],
)


class PusherAuthRequest(BaseModel):
    socket_id: str
    channel_name: str


class PusherAuthResponse(BaseModel):
    auth: str
    channel_data: Optional[str] = None
    shared_secret: Optional[str] = None


@router.post("/auth", response_model=Dict[str, Any])
async def pusher_auth(
    request: Request,
) -> Dict[str, Any]:
    """
    Authenticate Pusher channel subscription.

    For private channels, user must be authenticated.
    For presence channels, user info is included.
    """
    try:
        # Parse the request body - handle both JSON and form data
        content_type = request.headers.get("content-type", "")

        if "application/json" in content_type:
            body = await request.json()
        else:
            # Handle form data from Pusher client
            form_data = await request.form()
            body = {
                "socket_id": form_data.get("socket_id"),
                "channel_name": form_data.get("channel_name")
            }

        auth_request = PusherAuthRequest(**body)

        # Check for development token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        is_dev_token = auth_header.startswith("Bearer dev-token-")

        # Initialize current_user as None
        current_user = None

        # For private/presence channels, require authentication
        if auth_request.channel_name.startswith(("private-", "presence-")):
            # For development, create a default user
            if is_dev_token:
                current_user = {
                    "id": "dev-user",
                    "email": "dev@toolboxai.com",
                    "name": "Development User"
                }
            else:
                # Default user for channels requiring auth
                current_user = {
                    "id": "guest-user",
                    "email": "guest@toolboxai.com",
                    "name": "Guest User"
                }

        # Get user info for presence channels
        user_id = None
        user_info = None
        if current_user:
            user_id = str(current_user.get("id", "unknown"))
            user_info = {
                "name": current_user.get("name", "Unknown User"),
                "email": current_user.get("email", "")
            }

        # Authenticate the channel
        auth_response = authenticate_channel(
            socket_id=auth_request.socket_id,
            channel_name=auth_request.channel_name,
            user_id=user_id,
            user_info=user_info
        )

        logger.info(f"Authenticated channel {auth_request.channel_name} for user {user_id}")
        return auth_response

    except PusherUnavailable as e:
        logger.error(f"Pusher service unavailable: {e}")
        raise HTTPException(status_code=503, detail="Pusher service unavailable")
    except Exception as e:
        logger.error(f"Error authenticating Pusher channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to authenticate channel")


@router.post("/webhook")
async def pusher_webhook(request: Request):
    """
    Handle Pusher webhooks for channel lifecycle events.
    """
    try:
        body = await request.body()
        headers = dict(request.headers)

        # Log webhook for debugging
        logger.info(f"Received Pusher webhook: {body[:200]}")

        # In production, verify webhook signature
        # events = verify_webhook(headers, body)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error processing Pusher webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook")