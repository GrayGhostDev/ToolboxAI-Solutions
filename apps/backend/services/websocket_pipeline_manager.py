"""
WebSocket Pipeline Manager for Real-time Content Generation Updates
Provides live progress tracking during enhanced content pipeline execution
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any, List
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from redis.asyncio import Redis

from database.models import EnhancedContentGeneration, ContentGenerationBatch
from database.connection import get_async_session, get_redis_client
from core.agents.enhanced_content_pipeline import PipelineState, PipelineStage
from apps.backend.services.pusher import pusher_service

logger = logging.getLogger(__name__)


class WebSocketPipelineManager:
    """
    Manages WebSocket connections for real-time pipeline updates.
    Supports multiple concurrent pipelines with graceful error handling.
    """

    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}  # pipeline_id -> connections
        self.pipeline_states: Dict[str, PipelineState] = {}  # Current states
        self.redis: Optional[Redis] = None
        self.background_tasks: Set[asyncio.Task] = set()
        self.heartbeat_interval = 30  # seconds

    async def initialize(self):
        """Initialize manager with Redis connection"""
        self.redis = await get_redis_client()
        logger.info("WebSocket Pipeline Manager initialized")

    async def connect(self, websocket: WebSocket, pipeline_id: str):
        """
        Accept new WebSocket connection for pipeline monitoring

        Args:
            websocket: FastAPI WebSocket instance
            pipeline_id: ID of the pipeline to monitor
        """
        await websocket.accept()

        # Add to connections
        if pipeline_id not in self.connections:
            self.connections[pipeline_id] = set()
        self.connections[pipeline_id].add(websocket)

        # Send current state if exists
        if pipeline_id in self.pipeline_states:
            await self._send_state_update(websocket, pipeline_id)

        # Start heartbeat
        task = asyncio.create_task(self._heartbeat(websocket, pipeline_id))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

        logger.info(f"WebSocket connected for pipeline {pipeline_id}")

    async def disconnect(self, websocket: WebSocket, pipeline_id: str):
        """
        Handle WebSocket disconnection

        Args:
            websocket: FastAPI WebSocket instance
            pipeline_id: ID of the pipeline being monitored
        """
        if pipeline_id in self.connections:
            self.connections[pipeline_id].discard(websocket)
            if not self.connections[pipeline_id]:
                del self.connections[pipeline_id]

        logger.info(f"WebSocket disconnected for pipeline {pipeline_id}")

    async def update_pipeline_state(
        self,
        pipeline_id: str,
        stage: PipelineStage,
        progress: float,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Update pipeline state and notify all connected clients

        Args:
            pipeline_id: ID of the pipeline
            stage: Current pipeline stage
            progress: Progress percentage (0-100)
            message: Status message
            metadata: Additional metadata
        """
        # Update internal state
        if pipeline_id not in self.pipeline_states:
            self.pipeline_states[pipeline_id] = PipelineState(
                pipeline_id=pipeline_id,
                current_stage=stage,
                progress=progress,
                status_message=message,
                metadata=metadata or {}
            )
        else:
            state = self.pipeline_states[pipeline_id]
            state.current_stage = stage
            state.progress = progress
            state.status_message = message
            if metadata:
                state.metadata.update(metadata)

        # Store in Redis for persistence
        if self.redis:
            await self.redis.setex(
                f"pipeline:state:{pipeline_id}",
                3600,  # 1 hour TTL
                json.dumps({
                    "pipeline_id": pipeline_id,
                    "stage": stage.value,
                    "progress": progress,
                    "message": message,
                    "metadata": metadata or {},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            )

        # Notify all connected clients
        await self._broadcast_update(pipeline_id)

        # Also send via Pusher for wider reach
        await pusher_service.trigger_event(
            channel=f"pipeline-{pipeline_id}",
            event="state-update",
            data={
                "stage": stage.value,
                "progress": progress,
                "message": message,
                "metadata": metadata
            }
        )

    async def send_error(
        self,
        pipeline_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ):
        """
        Send error notification to all connected clients

        Args:
            pipeline_id: ID of the pipeline
            error_message: Error message
            error_details: Additional error details
        """
        error_data = {
            "type": "error",
            "pipeline_id": pipeline_id,
            "message": error_message,
            "details": error_details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Broadcast to WebSocket clients
        if pipeline_id in self.connections:
            disconnected = []
            for websocket in self.connections[pipeline_id]:
                try:
                    await websocket.send_json(error_data)
                except Exception as e:
                    logger.error(f"Failed to send error to WebSocket: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                await self.disconnect(ws, pipeline_id)

        # Also send via Pusher
        await pusher_service.trigger_event(
            channel=f"pipeline-{pipeline_id}",
            event="error",
            data=error_data
        )

    async def send_completion(
        self,
        pipeline_id: str,
        result: Dict[str, Any],
        metrics: Optional[Dict[str, Any]] = None
    ):
        """
        Send completion notification with results

        Args:
            pipeline_id: ID of the pipeline
            result: Generation results
            metrics: Performance metrics
        """
        completion_data = {
            "type": "completion",
            "pipeline_id": pipeline_id,
            "result": result,
            "metrics": metrics or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Update state
        if pipeline_id in self.pipeline_states:
            self.pipeline_states[pipeline_id].progress = 100
            self.pipeline_states[pipeline_id].status_message = "Pipeline completed successfully"

        # Broadcast to WebSocket clients
        if pipeline_id in self.connections:
            disconnected = []
            for websocket in self.connections[pipeline_id]:
                try:
                    await websocket.send_json(completion_data)
                except Exception as e:
                    logger.error(f"Failed to send completion to WebSocket: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                await self.disconnect(ws, pipeline_id)

        # Send via Pusher
        await pusher_service.trigger_event(
            channel=f"pipeline-{pipeline_id}",
            event="completion",
            data=completion_data
        )

        # Clean up state after delay
        asyncio.create_task(self._cleanup_pipeline_state(pipeline_id, delay=300))

    async def handle_message(
        self,
        websocket: WebSocket,
        pipeline_id: str,
        message: Dict[str, Any]
    ):
        """
        Handle incoming WebSocket messages from clients

        Args:
            websocket: FastAPI WebSocket instance
            pipeline_id: ID of the pipeline
            message: Received message data
        """
        msg_type = message.get("type")

        if msg_type == "ping":
            # Respond to ping
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        elif msg_type == "get_state":
            # Send current state
            await self._send_state_update(websocket, pipeline_id)

        elif msg_type == "subscribe_metrics":
            # Subscribe to detailed metrics
            await self._subscribe_to_metrics(websocket, pipeline_id)

        else:
            logger.warning(f"Unknown message type: {msg_type}")

    async def batch_update(
        self,
        batch_id: str,
        pipeline_updates: List[Dict[str, Any]]
    ):
        """
        Send batch updates for multiple pipelines

        Args:
            batch_id: Batch generation ID
            pipeline_updates: List of pipeline update dicts
        """
        batch_data = {
            "type": "batch_update",
            "batch_id": batch_id,
            "pipelines": pipeline_updates,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Send to batch channel via Pusher
        await pusher_service.trigger_event(
            channel=f"batch-{batch_id}",
            event="update",
            data=batch_data
        )

        # Update individual pipelines
        for update in pipeline_updates:
            pipeline_id = update.get("pipeline_id")
            if pipeline_id:
                await self.update_pipeline_state(
                    pipeline_id=pipeline_id,
                    stage=PipelineStage(update.get("stage", "processing")),
                    progress=update.get("progress", 0),
                    message=update.get("message", ""),
                    metadata=update.get("metadata")
                )

    # Private helper methods

    async def _broadcast_update(self, pipeline_id: str):
        """Broadcast state update to all connected clients"""
        if pipeline_id not in self.connections:
            return

        state = self.pipeline_states.get(pipeline_id)
        if not state:
            return

        update_data = {
            "type": "state_update",
            "pipeline_id": pipeline_id,
            "stage": state.current_stage.value,
            "progress": state.progress,
            "message": state.status_message,
            "metadata": state.metadata,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        disconnected = []
        for websocket in self.connections[pipeline_id]:
            try:
                await websocket.send_json(update_data)
            except Exception as e:
                logger.error(f"Failed to broadcast update: {e}")
                disconnected.append(websocket)

        # Clean up disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws, pipeline_id)

    async def _send_state_update(self, websocket: WebSocket, pipeline_id: str):
        """Send current state to specific WebSocket"""
        state = self.pipeline_states.get(pipeline_id)
        if state:
            try:
                await websocket.send_json({
                    "type": "current_state",
                    "pipeline_id": pipeline_id,
                    "stage": state.current_stage.value,
                    "progress": state.progress,
                    "message": state.status_message,
                    "metadata": state.metadata,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                logger.error(f"Failed to send state update: {e}")

    async def _heartbeat(self, websocket: WebSocket, pipeline_id: str):
        """Send periodic heartbeat to keep connection alive"""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        except WebSocketDisconnect:
            await self.disconnect(websocket, pipeline_id)
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            await self.disconnect(websocket, pipeline_id)

    async def _cleanup_pipeline_state(self, pipeline_id: str, delay: int = 300):
        """Clean up pipeline state after delay"""
        await asyncio.sleep(delay)

        # Remove from memory
        self.pipeline_states.pop(pipeline_id, None)

        # Remove from Redis
        if self.redis:
            await self.redis.delete(f"pipeline:state:{pipeline_id}")

        logger.info(f"Cleaned up state for pipeline {pipeline_id}")

    async def _subscribe_to_metrics(self, websocket: WebSocket, pipeline_id: str):
        """Subscribe to detailed metrics stream"""
        # Implementation for streaming detailed metrics
        # This could include memory usage, processing times, etc.
        pass

    @asynccontextmanager
    async def monitor_pipeline(self, pipeline_id: str):
        """
        Context manager for monitoring pipeline execution

        Usage:
            async with manager.monitor_pipeline(pipeline_id) as monitor:
                # Pipeline execution code
                await monitor.update(stage, progress, message)
        """
        class PipelineMonitor:
            def __init__(self, manager, pipeline_id):
                self.manager = manager
                self.pipeline_id = pipeline_id

            async def update(self, stage: PipelineStage, progress: float, message: str, **kwargs):
                await self.manager.update_pipeline_state(
                    self.pipeline_id, stage, progress, message, kwargs
                )

            async def error(self, message: str, details: Optional[Dict] = None):
                await self.manager.send_error(self.pipeline_id, message, details)

            async def complete(self, result: Dict, metrics: Optional[Dict] = None):
                await self.manager.send_completion(self.pipeline_id, result, metrics)

        monitor = PipelineMonitor(self, pipeline_id)
        try:
            yield monitor
        except Exception as e:
            await monitor.error(str(e), {"exception_type": type(e).__name__})
            raise
        finally:
            # Ensure cleanup
            pass


# Global instance
websocket_pipeline_manager = WebSocketPipelineManager()