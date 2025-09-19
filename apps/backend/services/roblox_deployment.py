"""
Roblox Content Deployment Pipeline
Manages queuing and deployment of content to Roblox environments using Redis
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import redis.asyncio as redis
from pydantic import BaseModel, Field
import hashlib
import uuid

logger = logging.getLogger(__name__)


class DeploymentStatus(str, Enum):
    """Deployment status states"""
    QUEUED = "queued"
    PROCESSING = "processing"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ContentType(str, Enum):
    """Types of deployable content"""
    SCRIPT = "script"
    MODEL = "model"
    PLACE = "place"
    ASSET = "asset"
    PLUGIN = "plugin"


class DeploymentRequest(BaseModel):
    """Deployment request model"""
    deployment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_type: ContentType
    content_data: str
    target_place_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    checksum: Optional[str] = None


class DeploymentResult(BaseModel):
    """Deployment result model"""
    deployment_id: str
    status: DeploymentStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    deployment_url: Optional[str] = None
    version: Optional[str] = None


class RobloxDeploymentPipeline:
    """Manages content deployment to Roblox using Redis queue"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.deployment_queue = "roblox:deployment:queue"
        self.deployment_status = "roblox:deployment:status"
        self.deployment_history = "roblox:deployment:history"
        self.deployment_channel = "roblox:deployment:updates"
        self.processing_lock = "roblox:deployment:lock"
        self.worker_running = False

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis connection established for deployment pipeline")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    def _calculate_checksum(self, content: str) -> str:
        """Calculate SHA256 checksum of content"""
        return hashlib.sha256(content.encode()).hexdigest()

    async def queue_deployment(self, request: DeploymentRequest) -> str:
        """Queue a deployment request"""
        try:
            # Calculate checksum if not provided
            if not request.checksum:
                request.checksum = self._calculate_checksum(request.content_data)

            # Serialize request
            request_data = request.model_dump_json()

            # Add to priority queue (higher priority = processed first)
            score = -request.priority  # Negative for proper ordering
            await self.redis_client.zadd(
                self.deployment_queue,
                {request_data: score}
            )

            # Set initial status
            status = DeploymentResult(
                deployment_id=request.deployment_id,
                status=DeploymentStatus.QUEUED
            )
            await self.redis_client.hset(
                self.deployment_status,
                request.deployment_id,
                status.model_dump_json()
            )

            # Publish update
            await self._publish_update(request.deployment_id, DeploymentStatus.QUEUED)

            logger.info(f"Deployment {request.deployment_id} queued with priority {request.priority}")
            return request.deployment_id

        except Exception as e:
            logger.error(f"Failed to queue deployment: {e}")
            raise

    async def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentResult]:
        """Get current deployment status"""
        try:
            status_data = await self.redis_client.hget(
                self.deployment_status,
                deployment_id
            )

            if status_data:
                return DeploymentResult.model_validate_json(status_data)
            return None

        except Exception as e:
            logger.error(f"Failed to get deployment status: {e}")
            return None

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        try:
            # Get queue length
            queue_length = await self.redis_client.zcard(self.deployment_queue)

            # Get processing status
            lock_value = await self.redis_client.get(self.processing_lock)
            is_processing = lock_value is not None

            # Get recent deployments
            all_deployments = await self.redis_client.hgetall(self.deployment_status)

            status_counts = {
                DeploymentStatus.QUEUED: 0,
                DeploymentStatus.PROCESSING: 0,
                DeploymentStatus.COMPLETED: 0,
                DeploymentStatus.FAILED: 0
            }

            for deployment_data in all_deployments.values():
                deployment = DeploymentResult.model_validate_json(deployment_data)
                if deployment.status in status_counts:
                    status_counts[deployment.status] += 1

            return {
                "queue_length": queue_length,
                "is_processing": is_processing,
                "status_counts": status_counts,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {}

    async def cancel_deployment(self, deployment_id: str) -> bool:
        """Cancel a queued deployment"""
        try:
            # Get current status
            status = await self.get_deployment_status(deployment_id)
            if not status:
                return False

            # Only cancel if queued
            if status.status != DeploymentStatus.QUEUED:
                logger.warning(f"Cannot cancel deployment {deployment_id} with status {status.status}")
                return False

            # Remove from queue
            all_items = await self.redis_client.zrange(
                self.deployment_queue,
                0,
                -1,
                withscores=False
            )

            for item in all_items:
                request = DeploymentRequest.model_validate_json(item)
                if request.deployment_id == deployment_id:
                    await self.redis_client.zrem(self.deployment_queue, item)
                    break

            # Update status
            status.status = DeploymentStatus.CANCELLED
            status.completed_at = datetime.utcnow()
            await self.redis_client.hset(
                self.deployment_status,
                deployment_id,
                status.model_dump_json()
            )

            # Publish update
            await self._publish_update(deployment_id, DeploymentStatus.CANCELLED)

            logger.info(f"Deployment {deployment_id} cancelled")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel deployment: {e}")
            return False

    async def _publish_update(self, deployment_id: str, status: DeploymentStatus,
                            message: Optional[str] = None):
        """Publish deployment status update"""
        try:
            update = {
                "deployment_id": deployment_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "message": message
            }
            await self.redis_client.publish(
                self.deployment_channel,
                json.dumps(update)
            )
        except Exception as e:
            logger.error(f"Failed to publish update: {e}")

    async def process_deployments(self):
        """Worker to process deployment queue"""
        self.worker_running = True
        logger.info("Deployment worker started")

        while self.worker_running:
            try:
                # Try to acquire processing lock
                lock_acquired = await self.redis_client.set(
                    self.processing_lock,
                    "worker",
                    nx=True,
                    ex=60  # Lock expires after 60 seconds
                )

                if not lock_acquired:
                    # Another worker is processing
                    await asyncio.sleep(5)
                    continue

                # Get next item from priority queue
                items = await self.redis_client.zrange(
                    self.deployment_queue,
                    0,
                    0,
                    withscores=False
                )

                if not items:
                    # Queue is empty
                    await self.redis_client.delete(self.processing_lock)
                    await asyncio.sleep(5)
                    continue

                # Process the deployment
                request_data = items[0]
                request = DeploymentRequest.model_validate_json(request_data)

                # Remove from queue
                await self.redis_client.zrem(self.deployment_queue, request_data)

                # Update status to processing
                status = DeploymentResult(
                    deployment_id=request.deployment_id,
                    status=DeploymentStatus.PROCESSING,
                    started_at=datetime.utcnow()
                )
                await self.redis_client.hset(
                    self.deployment_status,
                    request.deployment_id,
                    status.model_dump_json()
                )
                await self._publish_update(request.deployment_id, DeploymentStatus.PROCESSING)

                # Process the deployment
                success = await self._deploy_content(request)

                # Update final status
                if success:
                    status.status = DeploymentStatus.COMPLETED
                    status.deployment_url = f"https://www.roblox.com/games/{request.target_place_id}"
                    status.version = f"v{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                else:
                    status.status = DeploymentStatus.FAILED
                    status.error_message = "Deployment failed (mock implementation)"

                status.completed_at = datetime.utcnow()
                await self.redis_client.hset(
                    self.deployment_status,
                    request.deployment_id,
                    status.model_dump_json()
                )

                # Add to history
                await self.redis_client.lpush(
                    self.deployment_history,
                    status.model_dump_json()
                )
                # Keep only last 1000 deployments in history
                await self.redis_client.ltrim(self.deployment_history, 0, 999)

                # Publish final update
                await self._publish_update(request.deployment_id, status.status)

                # Release lock
                await self.redis_client.delete(self.processing_lock)

                logger.info(f"Deployment {request.deployment_id} completed with status {status.status}")

            except Exception as e:
                logger.error(f"Error processing deployment: {e}")
                # Release lock on error
                await self.redis_client.delete(self.processing_lock)
                await asyncio.sleep(5)

    async def _deploy_content(self, request: DeploymentRequest) -> bool:
        """
        Deploy content to Roblox
        TODO: Implement actual Roblox Open Cloud API integration
        """
        try:
            logger.info(f"Deploying {request.content_type} to place {request.target_place_id}")

            # Simulate deployment time
            await asyncio.sleep(3)

            # TODO: Actual deployment logic here
            # 1. Authenticate with Roblox Open Cloud API
            # 2. Upload content based on type
            # 3. Verify deployment
            # 4. Return success/failure

            # For now, return mock success
            return True

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

    async def get_deployment_history(self, limit: int = 10) -> List[DeploymentResult]:
        """Get recent deployment history"""
        try:
            history_data = await self.redis_client.lrange(
                self.deployment_history,
                0,
                limit - 1
            )

            history = []
            for item in history_data:
                history.append(DeploymentResult.model_validate_json(item))

            return history

        except Exception as e:
            logger.error(f"Failed to get deployment history: {e}")
            return []

    async def cleanup_old_deployments(self, days: int = 7):
        """Clean up old deployment records"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            all_deployments = await self.redis_client.hgetall(self.deployment_status)
            removed_count = 0

            for deployment_id, deployment_data in all_deployments.items():
                deployment = DeploymentResult.model_validate_json(deployment_data)

                # Only clean up completed/failed/cancelled deployments
                if deployment.status in [DeploymentStatus.COMPLETED,
                                        DeploymentStatus.FAILED,
                                        DeploymentStatus.CANCELLED]:
                    if deployment.completed_at and deployment.completed_at < cutoff_date:
                        await self.redis_client.hdel(self.deployment_status, deployment_id)
                        removed_count += 1

            logger.info(f"Cleaned up {removed_count} old deployments")
            return removed_count

        except Exception as e:
            logger.error(f"Failed to cleanup old deployments: {e}")
            return 0


# Singleton instance
_deployment_pipeline: Optional[RobloxDeploymentPipeline] = None


async def get_deployment_pipeline() -> RobloxDeploymentPipeline:
    """Get or create deployment pipeline instance"""
    global _deployment_pipeline

    if _deployment_pipeline is None:
        _deployment_pipeline = RobloxDeploymentPipeline()
        await _deployment_pipeline.initialize()

    return _deployment_pipeline