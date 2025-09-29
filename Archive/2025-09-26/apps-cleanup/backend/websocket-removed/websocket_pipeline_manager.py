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
        try:
            # Start metrics streaming task
            metrics_task = asyncio.create_task(
                self._stream_detailed_metrics(websocket, pipeline_id)
            )
            self.background_tasks.add(metrics_task)
            metrics_task.add_done_callback(self.background_tasks.discard)

            # Send subscription confirmation
            await websocket.send_json({
                "type": "metrics_subscription_active",
                "pipeline_id": pipeline_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            logger.info(f"Started metrics streaming for pipeline {pipeline_id}")

        except Exception as e:
            logger.error(f"Failed to subscribe to metrics: {e}")
            await websocket.send_json({
                "type": "metrics_subscription_error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    async def _stream_detailed_metrics(self, websocket: WebSocket, pipeline_id: str):
        """Stream detailed metrics for pipeline execution"""
        try:
            while True:
                await asyncio.sleep(5)  # Stream every 5 seconds

                # Collect detailed metrics
                metrics = await self._collect_pipeline_metrics(pipeline_id)

                # Send metrics update
                await websocket.send_json({
                    "type": "detailed_metrics",
                    "pipeline_id": pipeline_id,
                    "metrics": metrics,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        except WebSocketDisconnect:
            logger.info(f"Metrics streaming disconnected for pipeline {pipeline_id}")
        except Exception as e:
            logger.error(f"Metrics streaming error for pipeline {pipeline_id}: {e}")

    async def _collect_pipeline_metrics(self, pipeline_id: str) -> Dict[str, Any]:
        """Collect comprehensive pipeline metrics"""
        metrics = {
            "execution_metrics": {
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "tokens_processed": 0,
                "api_calls_made": 0,
                "cache_hits": 0,
                "cache_misses": 0
            },
            "quality_metrics": {
                "content_quality_score": 0.0,
                "educational_alignment": 0.0,
                "engagement_potential": 0.0,
                "accessibility_score": 0.0
            },
            "performance_metrics": {
                "average_response_time": 0.0,
                "throughput_per_minute": 0.0,
                "error_rate": 0.0,
                "retry_count": 0
            },
            "educational_metrics": {
                "learning_objectives_covered": 0,
                "curriculum_alignment_score": 0.0,
                "grade_level_appropriateness": 0.0,
                "subject_area_relevance": 0.0
            }
        }

        # Get metrics from Redis if available
        if self.redis:
            try:
                cached_metrics = await self.redis.get(f"pipeline:metrics:{pipeline_id}")
                if cached_metrics:
                    stored_metrics = json.loads(cached_metrics)
                    metrics.update(stored_metrics)
            except Exception as e:
                logger.debug(f"Could not retrieve cached metrics: {e}")

        # Add real-time system metrics
        import psutil
        metrics["execution_metrics"]["cpu_usage"] = psutil.cpu_percent()
        metrics["execution_metrics"]["memory_usage"] = psutil.virtual_memory().percent / 100.0

        return metrics

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


    async def send_agent_status_update(
        self,
        pipeline_id: str,
        agent_id: str,
        status: str,
        progress: float,
        details: Optional[Dict[str, Any]] = None
    ):
        """Send agent-specific status update"""
        agent_data = {
            "type": "agent_status",
            "pipeline_id": pipeline_id,
            "agent_id": agent_id,
            "status": status,
            "progress": progress,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Broadcast to WebSocket clients
        if pipeline_id in self.connections:
            disconnected = []
            for websocket in self.connections[pipeline_id]:
                try:
                    await websocket.send_json(agent_data)
                except Exception as e:
                    logger.error(f"Failed to send agent status: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                await self.disconnect(ws, pipeline_id)

        # Send via Pusher
        await pusher_service.trigger_event(
            channel=f"pipeline-{pipeline_id}",
            event="agent-status",
            data=agent_data
        )

    async def send_quality_assessment(
        self,
        pipeline_id: str,
        quality_metrics: Dict[str, float],
        assessment_details: Optional[Dict[str, Any]] = None
    ):
        """Send real-time quality assessment"""
        quality_data = {
            "type": "quality_assessment",
            "pipeline_id": pipeline_id,
            "quality_metrics": quality_metrics,
            "assessment_details": assessment_details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Store quality metrics in Redis
        if self.redis:
            await self.redis.setex(
                f"pipeline:quality:{pipeline_id}",
                3600,
                json.dumps(quality_data)
            )

        # Broadcast to WebSocket clients
        if pipeline_id in self.connections:
            disconnected = []
            for websocket in self.connections[pipeline_id]:
                try:
                    await websocket.send_json(quality_data)
                except Exception as e:
                    logger.error(f"Failed to send quality assessment: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                await self.disconnect(ws, pipeline_id)

        # Send via Pusher
        await pusher_service.trigger_event(
            channel=f"pipeline-{pipeline_id}",
            event="quality-assessment",
            data=quality_data
        )

    async def send_swarm_coordination_update(
        self,
        pipeline_id: str,
        swarm_status: Dict[str, Any],
        coordination_metrics: Optional[Dict[str, Any]] = None
    ):
        """Send swarm coordination status update"""
        swarm_data = {
            "type": "swarm_coordination",
            "pipeline_id": pipeline_id,
            "swarm_status": swarm_status,
            "coordination_metrics": coordination_metrics or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Store swarm status in Redis
        if self.redis:
            await self.redis.setex(
                f"pipeline:swarm:{pipeline_id}",
                3600,
                json.dumps(swarm_data)
            )

        # Broadcast to WebSocket clients
        if pipeline_id in self.connections:
            disconnected = []
            for websocket in self.connections[pipeline_id]:
                try:
                    await websocket.send_json(swarm_data)
                except Exception as e:
                    logger.error(f"Failed to send swarm update: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                await self.disconnect(ws, pipeline_id)

        # Send via Pusher
        await pusher_service.trigger_event(
            channel=f"pipeline-{pipeline_id}",
            event="swarm-coordination",
            data=swarm_data
        )

    async def send_educational_analytics(
        self,
        pipeline_id: str,
        analytics: Dict[str, Any],
        insights: Optional[List[str]] = None
    ):
        """Send educational analytics and insights"""
        analytics_data = {
            "type": "educational_analytics",
            "pipeline_id": pipeline_id,
            "analytics": analytics,
            "insights": insights or [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Store analytics in Redis
        if self.redis:
            await self.redis.setex(
                f"pipeline:analytics:{pipeline_id}",
                7200,  # 2 hours TTL for analytics
                json.dumps(analytics_data)
            )

        # Broadcast to WebSocket clients
        if pipeline_id in self.connections:
            disconnected = []
            for websocket in self.connections[pipeline_id]:
                try:
                    await websocket.send_json(analytics_data)
                except Exception as e:
                    logger.error(f"Failed to send analytics: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                await self.disconnect(ws, pipeline_id)

        # Send via Pusher
        await pusher_service.trigger_event(
            channel=f"pipeline-{pipeline_id}",
            event="educational-analytics",
            data=analytics_data
        )

    async def get_pipeline_metrics_history(
        self,
        pipeline_id: str,
        metric_type: str = "all"
    ) -> List[Dict[str, Any]]:
        """Get historical metrics for a pipeline"""
        history = []

        if not self.redis:
            return history

        try:
            # Get metrics from Redis based on type
            keys_pattern = f"pipeline:{metric_type}:{pipeline_id}:*" if metric_type != "all" else f"pipeline:*:{pipeline_id}:*"

            # For now, return recent cached metrics
            # In production, this would query a time-series database
            recent_metrics = await self.redis.get(f"pipeline:metrics:{pipeline_id}")
            if recent_metrics:
                history.append(json.loads(recent_metrics))

        except Exception as e:
            logger.error(f"Failed to retrieve metrics history: {e}")

        return history

    async def optimize_websocket_performance(self):
        """Optimize WebSocket performance based on usage patterns"""
        try:
            # Analyze connection patterns
            active_connections = sum(len(conns) for conns in self.connections.values())
            total_pipelines = len(self.pipeline_states)

            # Adjust heartbeat interval based on load
            if active_connections > 50:
                self.heartbeat_interval = 60  # Reduce frequency under high load
            elif active_connections < 10:
                self.heartbeat_interval = 15  # More frequent for better responsiveness
            else:
                self.heartbeat_interval = 30  # Default

            # Clean up stale pipeline states
            now = datetime.now(timezone.utc)
            stale_pipelines = []

            for pipeline_id, state in self.pipeline_states.items():
                if hasattr(state, 'last_update'):
                    time_since_update = (now - state.last_update).total_seconds()
                    if time_since_update > 3600:  # 1 hour
                        stale_pipelines.append(pipeline_id)

            # Remove stale states
            for pipeline_id in stale_pipelines:
                del self.pipeline_states[pipeline_id]
                if self.redis:
                    await self.redis.delete(f"pipeline:state:{pipeline_id}")

            logger.info(
                f"WebSocket optimization complete: {active_connections} connections, "
                f"{total_pipelines} pipelines, {len(stale_pipelines)} stale states cleaned"
            )

        except Exception as e:
            logger.error(f"WebSocket optimization failed: {e}")

    async def get_connection_statistics(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics"""
        stats = {
            "active_connections": sum(len(conns) for conns in self.connections.values()),
            "active_pipelines": len(self.pipeline_states),
            "background_tasks": len(self.background_tasks),
            "heartbeat_interval": self.heartbeat_interval,
            "pipeline_distribution": {
                pipeline_id: len(conns) for pipeline_id, conns in self.connections.items()
            },
            "pipeline_stages": {
                pipeline_id: state.current_stage.value if hasattr(state, 'current_stage') else 'unknown'
                for pipeline_id, state in self.pipeline_states.items()
            }
        }

        # Add Redis connection status
        if self.redis:
            try:
                await self.redis.ping()
                stats["redis_connected"] = True
            except:
                stats["redis_connected"] = False
        else:
            stats["redis_connected"] = False

        return stats

    async def shutdown(self):
        """Gracefully shutdown the WebSocket pipeline manager"""
        logger.info("Shutting down WebSocket Pipeline Manager")

        # Cancel all background tasks
        for task in self.background_tasks:
            task.cancel()

        # Close all connections
        for pipeline_id, connections in self.connections.items():
            for websocket in connections.copy():
                try:
                    await websocket.close(code=1001, reason="Server shutdown")
                except:
                    pass

        # Clear state
        self.connections.clear()
        self.pipeline_states.clear()
        self.background_tasks.clear()

        # Close Redis connection
        if self.redis:
            await self.redis.close()

        logger.info("WebSocket Pipeline Manager shutdown complete")


# Global instance
websocket_pipeline_manager = WebSocketPipelineManager()