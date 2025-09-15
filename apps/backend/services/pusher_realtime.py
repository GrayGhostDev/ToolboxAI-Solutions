"""
Pusher Channels Realtime Service - Replacement for Socket.IO
Provides full realtime communication using Pusher Channels
"""

import logging
import json
from typing import Any, Dict, Optional, List, Set
from datetime import datetime, timezone
import asyncio
from functools import wraps

from apps.backend.core.config import settings
from apps.backend.services.pusher import (
    get_pusher_client,
    trigger_event,
    authenticate_channel,
    PusherUnavailable
)
from apps.backend.services.rate_limit_manager import get_rate_limit_manager

logger = logging.getLogger(__name__)

# Channel name conventions
CHANNEL_PREFIX = {
    "public": "public-",
    "private": "private-",
    "presence": "presence-"
}

# Default channels
DEFAULT_CHANNELS = [
    "public-dashboard",
    "public-notifications",
    "private-admin",
    "private-teacher",
    "private-student"
]

# Track connected users (via presence channels)
connected_users: Dict[str, Dict[str, Any]] = {}

# Channel subscriptions
channel_subscriptions: Dict[str, Set[str]] = {}

# RBAC helpers
_role_hierarchy = {"student": 1, "teacher": 2, "admin": 3}


def _get_required_roles() -> Dict[str, str]:
    """Get required roles for channels from settings"""
    try:
        mapping = getattr(settings, "PUSHER_RBAC_REQUIRED_ROLES", None)
        if isinstance(mapping, dict):
            return {str(k): str(v) for k, v in mapping.items()}
    except Exception:
        pass
    # Fallback to default mapping
    return {
        "admin": "admin",
        "teacher": "teacher",
        "student": "student",
        "dashboard": "student",
        "notifications": "student"
    }


def _check_channel_access(channel: str, user_role: str) -> bool:
    """Check if user has access to channel based on RBAC"""
    required_roles = _get_required_roles()

    # Extract channel type from name
    channel_type = channel.split("-")[-1] if "-" in channel else channel

    required_role = required_roles.get(channel_type, "student")

    # Check role hierarchy
    user_level = _role_hierarchy.get(user_role, 0)
    required_level = _role_hierarchy.get(required_role, 0)

    return user_level >= required_level


class PusherRealtimeService:
    """
    Service for managing Pusher Channels realtime communication
    Replaces Socket.IO functionality
    """

    def __init__(self):
        self.client = None
        self.rate_limiter = get_rate_limit_manager()
        self.initialized = False

        try:
            self.client = get_pusher_client()
            self.initialized = True
            logger.info("Pusher Realtime Service initialized")
        except PusherUnavailable as e:
            logger.warning(f"Pusher not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Pusher: {e}")

    async def authenticate_user(self, socket_id: str, channel: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate user for private/presence channel access
        """
        if not self.initialized:
            raise PusherUnavailable("Pusher service not initialized")

        user_id = user_data.get("id")
        user_role = user_data.get("role", "student")

        # Check RBAC
        if not _check_channel_access(channel, user_role):
            raise PermissionError(f"User {user_id} with role {user_role} cannot access channel {channel}")

        # Check rate limit
        if not await self.rate_limiter.check_rate_limit(f"pusher_auth:{user_id}", 10, 60):
            raise Exception("Rate limit exceeded for channel authentication")

        # Authenticate with Pusher
        if channel.startswith("presence-"):
            auth_data = authenticate_channel(
                socket_id=socket_id,
                channel_name=channel,
                user_id=str(user_id),
                user_info={
                    "name": user_data.get("name", "Unknown"),
                    "role": user_role,
                    "avatar": user_data.get("avatar", None)
                }
            )
        else:
            auth_data = authenticate_channel(
                socket_id=socket_id,
                channel_name=channel
            )

        # Track subscription
        if user_id not in channel_subscriptions:
            channel_subscriptions[user_id] = set()
        channel_subscriptions[user_id].add(channel)

        return auth_data

    async def broadcast_event(
        self,
        channel: str,
        event: str,
        data: Dict[str, Any],
        exclude_socket_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Broadcast event to a channel
        """
        if not self.initialized:
            raise PusherUnavailable("Pusher service not initialized")

        # Add metadata
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
        data["server_id"] = settings.SERVER_ID if hasattr(settings, "SERVER_ID") else "main"

        # Trigger event
        result = trigger_event(channel, event, data)

        logger.debug(f"Broadcast event '{event}' to channel '{channel}'")
        return result

    async def send_to_user(
        self,
        user_id: str,
        event: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send event to specific user via their private channel
        """
        channel = f"private-user-{user_id}"
        return await self.broadcast_event(channel, event, data)

    async def send_to_role(
        self,
        role: str,
        event: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send event to all users with specific role
        """
        channel = f"private-{role}"
        return await self.broadcast_event(channel, event, data)

    async def handle_presence_event(
        self,
        channel: str,
        event: str,
        user_data: Dict[str, Any]
    ):
        """
        Handle presence channel events (member_added, member_removed)
        """
        user_id = user_data.get("id")

        if event == "member_added":
            connected_users[user_id] = {
                **user_data,
                "connected_at": datetime.now(timezone.utc).isoformat(),
                "channels": channel_subscriptions.get(user_id, set())
            }
            logger.info(f"User {user_id} joined presence channel {channel}")

        elif event == "member_removed":
            if user_id in connected_users:
                del connected_users[user_id]
            if user_id in channel_subscriptions:
                channel_subscriptions[user_id].discard(channel)
            logger.info(f"User {user_id} left presence channel {channel}")

    def get_connected_users(self) -> List[Dict[str, Any]]:
        """
        Get list of connected users
        """
        return list(connected_users.values())

    def get_user_channels(self, user_id: str) -> List[str]:
        """
        Get channels a user is subscribed to
        """
        return list(channel_subscriptions.get(user_id, set()))

    async def cleanup_user(self, user_id: str):
        """
        Clean up user data on disconnect
        """
        if user_id in connected_users:
            del connected_users[user_id]
        if user_id in channel_subscriptions:
            del channel_subscriptions[user_id]
        logger.debug(f"Cleaned up data for user {user_id}")


# Global instance
_pusher_service: Optional[PusherRealtimeService] = None


def get_pusher_service() -> PusherRealtimeService:
    """
    Get or create the global Pusher service instance
    """
    global _pusher_service
    if _pusher_service is None:
        _pusher_service = PusherRealtimeService()
    return _pusher_service


# Event handlers for common operations
async def emit_dashboard_update(data: Dict[str, Any]):
    """Emit dashboard update to all connected clients"""
    service = get_pusher_service()
    return await service.broadcast_event(
        "public-dashboard",
        "dashboard-update",
        data
    )


async def emit_content_generated(content_id: str, content_data: Dict[str, Any]):
    """Emit content generation completion"""
    service = get_pusher_service()
    return await service.broadcast_event(
        "public-notifications",
        "content-generated",
        {
            "content_id": content_id,
            "data": content_data,
            "status": "completed"
        }
    )


async def emit_quiz_submitted(quiz_id: str, student_id: str, score: float):
    """Emit quiz submission event"""
    service = get_pusher_service()

    # Notify teachers
    await service.send_to_role(
        "teacher",
        "quiz-submitted",
        {
            "quiz_id": quiz_id,
            "student_id": student_id,
            "score": score
        }
    )

    # Notify the student
    await service.send_to_user(
        student_id,
        "quiz-result",
        {
            "quiz_id": quiz_id,
            "score": score,
            "status": "graded"
        }
    )


async def emit_agent_status(agent_name: str, status: str, details: Optional[Dict[str, Any]] = None):
    """Emit agent status update"""
    service = get_pusher_service()
    return await service.broadcast_event(
        "public-notifications",
        "agent-status",
        {
            "agent": agent_name,
            "status": status,
            "details": details or {}
        }
    )


# Status endpoint data
def get_pusher_status() -> Dict[str, Any]:
    """
    Get Pusher service status for monitoring
    """
    service = get_pusher_service()

    if not service.initialized:
        return {
            "status": "unavailable",
            "message": "Pusher service not initialized",
            "connected_users": 0
        }

    connected = len(connected_users)
    total_channels = sum(len(channels) for channels in channel_subscriptions.values())

    return {
        "status": "healthy",
        "connected_users": connected,
        "total_channels": total_channels,
        "active_channels": list(set().union(*channel_subscriptions.values())) if channel_subscriptions else [],
        "users": [
            {
                "id": user_id,
                "role": user_data.get("role"),
                "connected_at": user_data.get("connected_at"),
                "channels": list(channel_subscriptions.get(user_id, set()))
            }
            for user_id, user_data in connected_users.items()
        ]
    }