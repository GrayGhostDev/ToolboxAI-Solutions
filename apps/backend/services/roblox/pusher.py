"""
Pusher Service for Roblox Real-time Communication
Manages Pusher channels for Roblox Bridge integration
"""

import logging
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import pusher
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RobloxChannelType(str, Enum):
    """Types of Pusher channels for Roblox integration"""

    CONVERSATION = "private-roblox-conversation"
    GENERATION = "private-roblox-generation"
    SYNC = "private-roblox-sync"
    AUTH = "private-roblox-auth"
    STUDIO = "private-roblox-studio"
    PRESENCE = "presence-roblox-workspace"


class RobloxEventType(str, Enum):
    """Event types for Roblox Pusher channels"""

    # Conversation events
    STAGE_CHANGED = "stage-changed"
    INPUT_PROCESSED = "input-processed"
    GENERATION_STARTED = "generation-started"
    GENERATION_PROGRESS = "generation-progress"
    GENERATION_COMPLETE = "generation-complete"

    # Sync events
    ROJO_CONNECTED = "rojo-connected"
    ROJO_DISCONNECTED = "rojo-disconnected"
    ROJO_SYNC_UPDATE = "rojo-sync-update"
    ROJO_BUILD_COMPLETE = "rojo-build-complete"

    # Auth events
    AUTH_SUCCESS = "auth-success"
    AUTH_FAILED = "auth-failed"
    TOKEN_REFRESHED = "token-refreshed"
    TOKEN_REVOKED = "token-revoked"

    # Studio events
    PLUGIN_CONNECTED = "plugin-connected"
    PLUGIN_DISCONNECTED = "plugin-disconnected"
    CONTENT_DEPLOYED = "content-deployed"
    ASSET_UPLOADED = "asset-uploaded"

    # Error events
    ERROR_OCCURRED = "error-occurred"


class PusherEvent(BaseModel):
    """Base model for Pusher events"""

    event_type: str = Field(description="Type of event")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict[str, Any] = Field(description="Event data")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")


class RobloxPusherService:
    """
    Service for managing Pusher channels for Roblox integration
    Provides real-time communication between backend, Studio, and dashboard
    """

    def __init__(self):
        """Initialize Pusher client with configuration from environment"""
        self.app_id = os.getenv("PUSHER_APP_ID")
        self.key = os.getenv("PUSHER_KEY")
        self.secret = os.getenv("PUSHER_SECRET")
        self.cluster = os.getenv("PUSHER_CLUSTER", "us2")

        if not all([self.app_id, self.key, self.secret]):
            logger.warning("Pusher credentials not fully configured - real-time features disabled")
            self.client = None
        else:
            self.client = pusher.Pusher(
                app_id=self.app_id, key=self.key, secret=self.secret, cluster=self.cluster, ssl=True
            )
            logger.info(f"Pusher client initialized for cluster {self.cluster}")

        # Track active channels
        self.active_channels: dict[str, dict[str, Any]] = {}

    def get_channel_name(self, channel_type: RobloxChannelType, identifier: str) -> str:
        """
        Get full channel name with prefix and identifier

        Args:
            channel_type: Type of channel
            identifier: Unique identifier (session_id, project_id, etc.)

        Returns:
            Full channel name
        """
        return f"{channel_type.value}-{identifier}"

    def authenticate_channel(
        self, channel_name: str, socket_id: str, user_data: dict[str, Any] | None = None
    ) -> dict[str, str]:
        """
        Authenticate a private or presence channel

        Args:
            channel_name: Name of the channel
            socket_id: Pusher socket ID
            user_data: Optional user data for presence channels

        Returns:
            Authentication response with signature
        """
        if not self.client:
            raise ValueError("Pusher client not configured")

        try:
            # Check if it's a presence channel
            if channel_name.startswith("presence-"):
                if not user_data:
                    user_data = {"user_id": "anonymous"}

                auth = self.client.authenticate(
                    channel=channel_name, socket_id=socket_id, custom_data=user_data
                )
            else:
                # Private channel authentication
                auth = self.client.authenticate(channel=channel_name, socket_id=socket_id)

            logger.info(f"Authenticated channel {channel_name} for socket {socket_id}")
            return auth

        except Exception as e:
            logger.error(f"Failed to authenticate channel {channel_name}: {e}")
            raise

    def trigger_event(
        self, channel: str, event: str, data: dict[str, Any], socket_id: str | None = None
    ) -> bool:
        """
        Trigger an event on a channel

        Args:
            channel: Channel name
            event: Event name
            data: Event data
            socket_id: Optional socket ID to exclude from receiving the event

        Returns:
            Success status
        """
        if not self.client:
            logger.warning("Pusher client not configured - event not sent")
            return False

        try:
            self.client.trigger(channels=channel, event_name=event, data=data, socket_id=socket_id)

            logger.debug(f"Triggered event {event} on channel {channel}")
            return True

        except Exception as e:
            logger.error(f"Failed to trigger event {event} on {channel}: {e}")
            return False

    def batch_trigger(self, events: list[dict[str, Any]]) -> bool:
        """
        Trigger multiple events in a single request

        Args:
            events: List of event dictionaries with channel, name, and data

        Returns:
            Success status
        """
        if not self.client:
            logger.warning("Pusher client not configured - batch not sent")
            return False

        try:
            self.client.trigger_batch(events)
            logger.debug(f"Triggered batch of {len(events)} events")
            return True

        except Exception as e:
            logger.error(f"Failed to trigger batch events: {e}")
            return False

    # ========================================
    # Conversation Flow Events
    # ========================================

    def notify_conversation_stage_change(
        self,
        session_id: str,
        stage: str,
        progress: float,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Notify stage change in conversation flow"""
        channel = self.get_channel_name(RobloxChannelType.CONVERSATION, session_id)

        data = {
            "session_id": session_id,
            "stage": stage,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if metadata:
            data["metadata"] = metadata

        return self.trigger_event(
            channel=channel, event=RobloxEventType.STAGE_CHANGED.value, data=data
        )

    def notify_generation_progress(
        self,
        session_id: str,
        progress: float,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> bool:
        """Notify content generation progress"""
        channel = self.get_channel_name(RobloxChannelType.GENERATION, session_id)

        data = {
            "session_id": session_id,
            "progress": progress,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if details:
            data["details"] = details

        return self.trigger_event(
            channel=channel, event=RobloxEventType.GENERATION_PROGRESS.value, data=data
        )

    def notify_generation_complete(
        self, session_id: str, project_id: str, files_generated: int, rojo_port: int
    ) -> bool:
        """Notify that content generation is complete"""
        channel = self.get_channel_name(RobloxChannelType.GENERATION, session_id)

        data = {
            "session_id": session_id,
            "project_id": project_id,
            "files_generated": files_generated,
            "rojo_port": rojo_port,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "complete",
        }

        return self.trigger_event(
            channel=channel, event=RobloxEventType.GENERATION_COMPLETE.value, data=data
        )

    # ========================================
    # Rojo Sync Events
    # ========================================

    def notify_rojo_connected(
        self, project_id: str, port: int, studio_session_id: str | None = None
    ) -> bool:
        """Notify that Rojo has connected to Studio"""
        channel = self.get_channel_name(RobloxChannelType.SYNC, project_id)

        data = {
            "project_id": project_id,
            "port": port,
            "studio_session_id": studio_session_id,
            "connected_at": datetime.now(timezone.utc).isoformat(),
        }

        return self.trigger_event(
            channel=channel, event=RobloxEventType.ROJO_CONNECTED.value, data=data
        )

    def notify_rojo_sync_update(
        self, project_id: str, files_synced: int, files_pending: int, sync_status: str
    ) -> bool:
        """Notify Rojo sync progress"""
        channel = self.get_channel_name(RobloxChannelType.SYNC, project_id)

        data = {
            "project_id": project_id,
            "files_synced": files_synced,
            "files_pending": files_pending,
            "sync_status": sync_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return self.trigger_event(
            channel=channel, event=RobloxEventType.ROJO_SYNC_UPDATE.value, data=data
        )

    # ========================================
    # Authentication Events
    # ========================================

    def notify_auth_success(self, user_id: str, session_id: str, expires_in: int) -> bool:
        """Notify successful authentication"""
        channel = self.get_channel_name(RobloxChannelType.AUTH, user_id)

        data = {
            "user_id": user_id,
            "session_id": session_id,
            "expires_in": expires_in,
            "authenticated_at": datetime.now(timezone.utc).isoformat(),
        }

        return self.trigger_event(
            channel=channel, event=RobloxEventType.AUTH_SUCCESS.value, data=data
        )

    def notify_auth_failed(self, user_id: str, reason: str, error_code: str | None = None) -> bool:
        """Notify failed authentication"""
        channel = self.get_channel_name(RobloxChannelType.AUTH, user_id)

        data = {
            "user_id": user_id,
            "reason": reason,
            "error_code": error_code,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }

        return self.trigger_event(
            channel=channel, event=RobloxEventType.AUTH_FAILED.value, data=data
        )

    # ========================================
    # Studio Plugin Events
    # ========================================

    def notify_plugin_connected(self, studio_id: str, plugin_version: str, user_id: str) -> bool:
        """Notify that Studio plugin has connected"""
        channel = self.get_channel_name(RobloxChannelType.STUDIO, studio_id)

        data = {
            "studio_id": studio_id,
            "plugin_version": plugin_version,
            "user_id": user_id,
            "connected_at": datetime.now(timezone.utc).isoformat(),
        }

        return self.trigger_event(
            channel=channel, event=RobloxEventType.PLUGIN_CONNECTED.value, data=data
        )

    def notify_content_deployed(
        self, studio_id: str, project_id: str, asset_count: int, deployment_time: float
    ) -> bool:
        """Notify that content has been deployed to Studio"""
        channel = self.get_channel_name(RobloxChannelType.STUDIO, studio_id)

        data = {
            "studio_id": studio_id,
            "project_id": project_id,
            "asset_count": asset_count,
            "deployment_time": deployment_time,
            "deployed_at": datetime.now(timezone.utc).isoformat(),
        }

        return self.trigger_event(
            channel=channel, event=RobloxEventType.CONTENT_DEPLOYED.value, data=data
        )

    def notify_asset_uploaded(
        self, studio_id: str, asset_id: str, asset_type: str, asset_name: str
    ) -> bool:
        """Notify that an asset has been uploaded"""
        channel = self.get_channel_name(RobloxChannelType.STUDIO, studio_id)

        data = {
            "studio_id": studio_id,
            "asset_id": asset_id,
            "asset_type": asset_type,
            "asset_name": asset_name,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }

        return self.trigger_event(
            channel=channel, event=RobloxEventType.ASSET_UPLOADED.value, data=data
        )

    # ========================================
    # Error Events
    # ========================================

    def notify_error(
        self,
        channel_type: RobloxChannelType,
        identifier: str,
        error_code: str,
        error_message: str,
        details: dict[str, Any] | None = None,
    ) -> bool:
        """Notify that an error has occurred"""
        channel = self.get_channel_name(channel_type, identifier)

        data = {
            "error_code": error_code,
            "error_message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if details:
            data["details"] = details

        return self.trigger_event(
            channel=channel, event=RobloxEventType.ERROR_OCCURRED.value, data=data
        )

    # ========================================
    # Presence Channel Management
    # ========================================

    def get_workspace_members(self, workspace_id: str) -> dict[str, Any] | None:
        """
        Get members currently in a workspace presence channel

        Args:
            workspace_id: Workspace identifier

        Returns:
            Dictionary of member data or None
        """
        if not self.client:
            return None

        try:
            channel = f"presence-roblox-workspace-{workspace_id}"
            response = self.client.channels_info(channel, ["user_count", "subscription_count"])
            return response

        except Exception as e:
            logger.error(f"Failed to get workspace members: {e}")
            return None

    def terminate_channel(self, channel_name: str) -> bool:
        """
        Terminate all connections to a channel (admin only)

        Args:
            channel_name: Name of channel to terminate

        Returns:
            Success status
        """
        if not self.client:
            return False

        try:
            # Note: This requires additional Pusher API permissions
            self.client.terminate(channel_name)
            logger.info(f"Terminated channel {channel_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to terminate channel {channel_name}: {e}")
            return False

    def get_channel_stats(self) -> dict[str, Any] | None:
        """
        Get statistics for all active channels

        Returns:
            Channel statistics or None
        """
        if not self.client:
            return None

        try:
            stats = self.client.channels_info()
            return stats

        except Exception as e:
            logger.error(f"Failed to get channel stats: {e}")
            return None


# Singleton instance
_pusher_service = None


def get_roblox_pusher_service() -> RobloxPusherService:
    """Get singleton Pusher service instance"""
    global _pusher_service
    if _pusher_service is None:
        _pusher_service = RobloxPusherService()
    return _pusher_service
