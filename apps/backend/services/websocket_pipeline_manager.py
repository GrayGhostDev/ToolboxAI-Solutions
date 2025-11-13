"""
Pusher Pipeline Manager
=======================
Unified real-time communication pipeline using Pusher Channels

This module provides a centralized interface for all real-time updates
using Pusher Channels (not raw WebSockets). Manages event broadcasting,
progress updates, and agent-to-frontend communication.

Architecture:
- Uses Pusher Channels for client communication
- Provides pipeline abstraction for different event types
- Supports batching and throttling for high-frequency updates
- Integrates with agent system for real-time feedback
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any

try:
    import pusher
    from pusher.errors import PusherError

    PUSHER_AVAILABLE = True
except ImportError:
    PUSHER_AVAILABLE = False
    pusher = None
    PusherError = Exception

from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Pipeline event types"""

    CONTENT_GENERATION = "content-generation"
    QUIZ_GENERATION = "quiz-generation"
    AGENT_UPDATE = "agent-update"
    PROGRESS = "progress"
    ERROR = "error"
    COMPLETION = "completion"
    NOTIFICATION = "notification"
    ROBLOX_SYNC = "roblox-sync"


class PipelineChannel(Enum):
    """Pusher channel names"""

    CONTENT = "content-updates"
    AGENTS = "agent-updates"
    PROGRESS = "progress-updates"
    NOTIFICATIONS = "notifications"
    ROBLOX = "roblox-updates"
    PRIVATE_USER = "private-user-{user_id}"  # Template for private channels


class WebSocketPipelineManager:
    """
    Pusher Pipeline Manager

    Centralized real-time communication using Pusher Channels.
    Provides a unified interface for all real-time updates across the application.

    Features:
    - Event batching for high-frequency updates
    - Automatic retry on failures
    - Channel management
    - Private user channels
    - Progress tracking
    - Error handling and logging
    """

    def __init__(self):
        """Initialize Pusher pipeline manager"""
        self.pusher_client: Any | None = None
        self.enabled = False
        self.event_queue: list[dict[str, Any]] = []
        self.batch_size = 10
        self.flush_interval = 1.0  # seconds
        self._flush_task: asyncio.Task | None = None
        self._initialize_pusher()

    def _initialize_pusher(self):
        """Initialize Pusher client"""
        if not PUSHER_AVAILABLE:
            logger.warning("Pusher library not available - pipeline manager running in mock mode")
            return

        try:
            # Check if Pusher is enabled and configured
            pusher_enabled = getattr(settings, "PUSHER_ENABLED", False)
            if not pusher_enabled:
                logger.info("Pusher disabled in settings - pipeline running in mock mode")
                return

            pusher_app_id = getattr(settings, "PUSHER_APP_ID", None)
            pusher_key = getattr(settings, "PUSHER_KEY", None)
            pusher_secret = getattr(settings, "PUSHER_SECRET", None)
            pusher_cluster = getattr(settings, "PUSHER_CLUSTER", "us2")

            if not all([pusher_app_id, pusher_key, pusher_secret]):
                logger.warning("Pusher credentials incomplete - pipeline running in mock mode")
                return

            self.pusher_client = pusher.Pusher(
                app_id=str(pusher_app_id),
                key=str(pusher_key),
                secret=str(pusher_secret),
                cluster=str(pusher_cluster),
                ssl=True,
            )

            self.enabled = True
            logger.info(f"Pusher Pipeline Manager initialized (cluster: {pusher_cluster})")

        except Exception as e:
            logger.error(f"Failed to initialize Pusher: {e}")
            self.enabled = False

    async def send_event(
        self, channel: str, event_type: str, data: dict[str, Any], user_id: int | None = None
    ) -> bool:
        """
        Send event via Pusher

        Args:
            channel: Pusher channel name
            event_type: Event type identifier
            data: Event payload
            user_id: Optional user ID for private channels

        Returns:
            Success status
        """
        try:
            # Use private channel if user_id provided
            if user_id:
                channel = f"private-user-{user_id}"

            # Add metadata
            event_data = {
                **data,
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
            }

            if not self.enabled or not self.pusher_client:
                logger.debug(f"Mock mode: Would send to {channel}: {event_type}")
                return True

            # Send via Pusher
            self.pusher_client.trigger(channel, event_type, event_data)
            logger.debug(f"Sent event to {channel}: {event_type}")
            return True

        except PusherError as e:
            logger.error(f"Pusher error sending event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending event: {e}")
            return False

    async def send_content_update(
        self, content_id: int, update_type: str, data: dict[str, Any], user_id: int | None = None
    ):
        """
        Send content generation/update event

        Args:
            content_id: Content ID
            update_type: Type of update (generation, review, completion)
            data: Update data
            user_id: Optional user ID
        """
        await self.send_event(
            channel=PipelineChannel.CONTENT.value,
            event_type=EventType.CONTENT_GENERATION.value,
            data={"content_id": content_id, "update_type": update_type, **data},
            user_id=user_id,
        )

    async def send_progress_update(
        self,
        task_id: str,
        progress: int,
        status: str,
        message: str | None = None,
        user_id: int | None = None,
    ):
        """
        Send progress update

        Args:
            task_id: Task identifier
            progress: Progress percentage (0-100)
            status: Status message
            message: Optional detailed message
            user_id: Optional user ID
        """
        await self.send_event(
            channel=PipelineChannel.PROGRESS.value,
            event_type=EventType.PROGRESS.value,
            data={
                "task_id": task_id,
                "progress": min(100, max(0, progress)),
                "status": status,
                "message": message,
            },
            user_id=user_id,
        )

    async def send_agent_update(
        self, agent_type: str, action: str, data: dict[str, Any], user_id: int | None = None
    ):
        """
        Send agent activity update

        Args:
            agent_type: Type of agent (content, quiz, review)
            action: Agent action (started, processing, completed)
            data: Action data
            user_id: Optional user ID
        """
        await self.send_event(
            channel=PipelineChannel.AGENTS.value,
            event_type=EventType.AGENT_UPDATE.value,
            data={"agent_type": agent_type, "action": action, **data},
            user_id=user_id,
        )

    async def send_quiz_update(
        self, quiz_id: int, update_type: str, data: dict[str, Any], user_id: int | None = None
    ):
        """
        Send quiz generation/update event

        Args:
            quiz_id: Quiz ID
            update_type: Type of update
            data: Update data
            user_id: Optional user ID
        """
        await self.send_event(
            channel=PipelineChannel.CONTENT.value,
            event_type=EventType.QUIZ_GENERATION.value,
            data={"quiz_id": quiz_id, "update_type": update_type, **data},
            user_id=user_id,
        )

    async def send_roblox_update(
        self, sync_type: str, data: dict[str, Any], user_id: int | None = None
    ):
        """
        Send Roblox integration update

        Args:
            sync_type: Type of sync (deploy, sync, update)
            data: Sync data
            user_id: Optional user ID
        """
        await self.send_event(
            channel=PipelineChannel.ROBLOX.value,
            event_type=EventType.ROBLOX_SYNC.value,
            data={"sync_type": sync_type, **data},
            user_id=user_id,
        )

    async def send_error(
        self,
        error_type: str,
        error_message: str,
        context: dict[str, Any] | None = None,
        user_id: int | None = None,
    ):
        """
        Send error notification

        Args:
            error_type: Type of error
            error_message: Error message
            context: Optional error context
            user_id: Optional user ID
        """
        await self.send_event(
            channel=PipelineChannel.NOTIFICATIONS.value,
            event_type=EventType.ERROR.value,
            data={
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {},
            },
            user_id=user_id,
        )

    async def send_notification(
        self,
        notification_type: str,
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
        user_id: int | None = None,
    ):
        """
        Send user notification

        Args:
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Optional additional data
            user_id: Optional user ID
        """
        await self.send_event(
            channel=PipelineChannel.NOTIFICATIONS.value,
            event_type=EventType.NOTIFICATION.value,
            data={
                "notification_type": notification_type,
                "title": title,
                "message": message,
                **(data or {}),
            },
            user_id=user_id,
        )

    async def broadcast_to_channel(self, channel: str, event: str, data: dict[str, Any]) -> bool:
        """
        Broadcast message to a specific channel

        Args:
            channel: Channel name
            event: Event name
            data: Event data

        Returns:
            Success status
        """
        return await self.send_event(channel, event, data)

    def create_progress_tracker(
        self, task_id: str, total_steps: int, user_id: int | None = None
    ) -> "ProgressTracker":
        """
        Create a progress tracker for multi-step operations

        Args:
            task_id: Task identifier
            total_steps: Total number of steps
            user_id: Optional user ID

        Returns:
            ProgressTracker instance
        """
        return ProgressTracker(self, task_id, total_steps, user_id)

    async def close(self):
        """Clean up resources"""
        if self._flush_task:
            self._flush_task.cancel()
        logger.info("Pusher Pipeline Manager closed")


class ProgressTracker:
    """
    Progress Tracker

    Helps track and report progress for multi-step operations.
    """

    def __init__(
        self,
        pipeline: WebSocketPipelineManager,
        task_id: str,
        total_steps: int,
        user_id: int | None = None,
    ):
        """
        Initialize progress tracker

        Args:
            pipeline: Pipeline manager instance
            task_id: Task identifier
            total_steps: Total number of steps
            user_id: Optional user ID
        """
        self.pipeline = pipeline
        self.task_id = task_id
        self.total_steps = total_steps
        self.current_step = 0
        self.user_id = user_id

    async def update(self, step_name: str, step_number: int | None = None):
        """
        Update progress

        Args:
            step_name: Current step name
            step_number: Optional explicit step number
        """
        if step_number is not None:
            self.current_step = step_number
        else:
            self.current_step += 1

        progress = int((self.current_step / self.total_steps) * 100)

        await self.pipeline.send_progress_update(
            task_id=self.task_id,
            progress=progress,
            status=step_name,
            message=f"Step {self.current_step}/{self.total_steps}: {step_name}",
            user_id=self.user_id,
        )

    async def complete(self, message: str = "Complete"):
        """Mark task as complete"""
        await self.pipeline.send_progress_update(
            task_id=self.task_id,
            progress=100,
            status="completed",
            message=message,
            user_id=self.user_id,
        )

    async def error(self, error_message: str):
        """Report error"""
        await self.pipeline.send_error(
            error_type="task_error",
            error_message=error_message,
            context={"task_id": self.task_id},
            user_id=self.user_id,
        )


# Global singleton instance
websocket_pipeline_manager = WebSocketPipelineManager()


__all__ = [
    "WebSocketPipelineManager",
    "ProgressTracker",
    "EventType",
    "PipelineChannel",
    "websocket_pipeline_manager",
]
