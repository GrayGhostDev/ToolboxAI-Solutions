"""
Roblox Content Deployment Pipeline
Manages queuing and deployment of content to Roblox environments using Redis
"""

import json
import asyncio
import logging
import os
import base64
import mimetypes
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import redis.asyncio as redis
from pydantic import BaseModel, Field
import hashlib
import uuid
import aiofiles
import httpx

from apps.backend.core.config import settings
from apps.backend.services.supabase_service import SupabaseService

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
    TEXTURE = "texture"
    SOUND = "sound"
    ANIMATION = "animation"
    MESH = "mesh"
    DECAL = "decal"
    PARTICLE = "particle"
    GUI = "gui"


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


class AssetMetadata(BaseModel):
    """Asset metadata for Roblox deployments"""

    asset_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    content_type: ContentType
    file_size: int
    file_hash: str
    mime_type: Optional[str] = None
    dimensions: Optional[Dict[str, int]] = None  # For images/models
    duration: Optional[float] = None  # For sounds/animations
    tags: List[str] = Field(default_factory=list)
    creator_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    version: int = 1
    parent_asset_id: Optional[str] = None  # For versioning
    roblox_asset_id: Optional[str] = None  # After upload to Roblox
    storage_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssetBundle(BaseModel):
    """Collection of related assets for deployment"""

    bundle_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    assets: List[AssetMetadata] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)  # asset_name: asset_id
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_size: int = 0
    deployment_order: List[str] = Field(default_factory=list)  # Ordered asset IDs


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
                self.redis_url, encoding="utf-8", decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis connection established for deployment pipeline")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.aclose()
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
            await self.redis_client.zadd(self.deployment_queue, {request_data: score})

            # Set initial status
            status = DeploymentResult(
                deployment_id=request.deployment_id, status=DeploymentStatus.QUEUED
            )
            await self.redis_client.hset(
                self.deployment_status, request.deployment_id, status.model_dump_json()
            )

            # Publish update
            await self._publish_update(request.deployment_id, DeploymentStatus.QUEUED)

            logger.info(
                f"Deployment {request.deployment_id} queued with priority {request.priority}"
            )
            return request.deployment_id

        except Exception as e:
            logger.error(f"Failed to queue deployment: {e}")
            raise

    async def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentResult]:
        """Get current deployment status"""
        try:
            status_data = await self.redis_client.hget(self.deployment_status, deployment_id)

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
                DeploymentStatus.FAILED: 0,
            }

            for deployment_data in all_deployments.values():
                deployment = DeploymentResult.model_validate_json(deployment_data)
                if deployment.status in status_counts:
                    status_counts[deployment.status] += 1

            return {
                "queue_length": queue_length,
                "is_processing": is_processing,
                "status_counts": status_counts,
                "timestamp": datetime.utcnow().isoformat(),
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
                logger.warning(
                    f"Cannot cancel deployment {deployment_id} with status {status.status}"
                )
                return False

            # Remove from queue
            all_items = await self.redis_client.zrange(
                self.deployment_queue, 0, -1, withscores=False
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
                self.deployment_status, deployment_id, status.model_dump_json()
            )

            # Publish update
            await self._publish_update(deployment_id, DeploymentStatus.CANCELLED)

            logger.info(f"Deployment {deployment_id} cancelled")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel deployment: {e}")
            return False

    async def _publish_update(
        self, deployment_id: str, status: DeploymentStatus, message: Optional[str] = None
    ):
        """Publish deployment status update"""
        try:
            update = {
                "deployment_id": deployment_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "message": message,
            }
            await self.redis_client.publish(self.deployment_channel, json.dumps(update))
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
                    self.processing_lock, "worker", nx=True, ex=60  # Lock expires after 60 seconds
                )

                if not lock_acquired:
                    # Another worker is processing
                    await asyncio.sleep(5)
                    continue

                # Get next item from priority queue
                items = await self.redis_client.zrange(
                    self.deployment_queue, 0, 0, withscores=False
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
                    started_at=datetime.utcnow(),
                )
                await self.redis_client.hset(
                    self.deployment_status, request.deployment_id, status.model_dump_json()
                )
                await self._publish_update(request.deployment_id, DeploymentStatus.PROCESSING)

                # Process the deployment
                success = await self._deploy_content(request)

                # Update final status
                if success:
                    status.status = DeploymentStatus.COMPLETED
                    status.deployment_url = (
                        f"https://www.roblox.com/games/{request.target_place_id}"
                    )
                    status.version = f"v{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                else:
                    status.status = DeploymentStatus.FAILED
                    status.error_message = "Deployment failed (mock implementation)"

                status.completed_at = datetime.utcnow()
                await self.redis_client.hset(
                    self.deployment_status, request.deployment_id, status.model_dump_json()
                )

                # Add to history
                await self.redis_client.lpush(self.deployment_history, status.model_dump_json())
                # Keep only last 1000 deployments in history
                await self.redis_client.ltrim(self.deployment_history, 0, 999)

                # Publish final update
                await self._publish_update(request.deployment_id, status.status)

                # Release lock
                await self.redis_client.delete(self.processing_lock)

                logger.info(
                    f"Deployment {request.deployment_id} completed with status {status.status}"
                )

            except Exception as e:
                logger.error(f"Error processing deployment: {e}")
                # Release lock on error
                await self.redis_client.delete(self.processing_lock)
                await asyncio.sleep(5)

    async def _deploy_content(self, request: DeploymentRequest) -> bool:
        """
        Deploy content to Roblox with enhanced asset management
        """
        try:
            logger.info(f"Deploying {request.content_type} to place {request.target_place_id}")

            # Check content type and route to appropriate handler
            if request.content_type in [ContentType.TEXTURE, ContentType.SOUND, ContentType.MESH]:
                return await self._deploy_asset(request)
            elif request.content_type == ContentType.SCRIPT:
                return await self._deploy_script(request)
            elif request.content_type == ContentType.MODEL:
                return await self._deploy_model(request)
            else:
                # Default deployment
                await asyncio.sleep(3)  # Simulate deployment
                return True

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

    async def _deploy_asset(self, request: DeploymentRequest) -> bool:
        """Deploy asset to Roblox using Open Cloud API"""
        try:
            # TODO: Implement actual Roblox Open Cloud API integration
            # For now, simulate deployment
            logger.info(f"Deploying asset {request.content_type}")
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Asset deployment failed: {e}")
            return False

    async def _deploy_script(self, request: DeploymentRequest) -> bool:
        """Deploy script to Roblox place"""
        try:
            logger.info("Deploying script to Roblox")
            # TODO: Use Roblox Open Cloud API to update script
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Script deployment failed: {e}")
            return False

    async def _deploy_model(self, request: DeploymentRequest) -> bool:
        """Deploy model to Roblox place"""
        try:
            logger.info("Deploying model to Roblox")
            # TODO: Use Roblox Open Cloud API to insert model
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Model deployment failed: {e}")
            return False

    async def get_deployment_history(self, limit: int = 10) -> List[DeploymentResult]:
        """Get recent deployment history"""
        try:
            history_data = await self.redis_client.lrange(self.deployment_history, 0, limit - 1)

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
                if deployment.status in [
                    DeploymentStatus.COMPLETED,
                    DeploymentStatus.FAILED,
                    DeploymentStatus.CANCELLED,
                ]:
                    if deployment.completed_at and deployment.completed_at < cutoff_date:
                        await self.redis_client.hdel(self.deployment_status, deployment_id)
                        removed_count += 1

            logger.info(f"Cleaned up {removed_count} old deployments")
            return removed_count

        except Exception as e:
            logger.error(f"Failed to cleanup old deployments: {e}")
            return 0

    # ==================== Asset Management Methods ====================

    async def upload_asset(
        self,
        file_path: str,
        content_type: ContentType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AssetMetadata:
        """
        Upload an asset file for deployment

        Args:
            file_path: Path to the asset file
            content_type: Type of content
            metadata: Optional metadata

        Returns:
            AssetMetadata object
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                raise FileNotFoundError(f"Asset file not found: {file_path}")

            # Calculate file hash
            file_hash = await self._calculate_file_hash(file_path)

            # Get file info
            file_size = file_path.stat().st_size
            mime_type, _ = mimetypes.guess_type(str(file_path))

            # Create asset metadata
            asset = AssetMetadata(
                name=file_path.stem,
                content_type=content_type,
                file_size=file_size,
                file_hash=file_hash,
                mime_type=mime_type,
                metadata=metadata or {}
            )

            # Store file in Supabase storage
            storage_path = await self._store_asset_file(file_path, asset)
            asset.storage_path = storage_path

            # Store metadata in Redis
            await self._store_asset_metadata(asset)

            logger.info(f"Uploaded asset {asset.asset_id}: {asset.name}")
            return asset

        except Exception as e:
            logger.error(f"Failed to upload asset: {e}")
            raise

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()

        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_sha256.update(chunk)

        return hash_sha256.hexdigest()

    async def _store_asset_file(self, file_path: Path, asset: AssetMetadata) -> str:
        """Store asset file in Supabase storage"""
        try:
            # Create storage path
            storage_path = f"roblox_assets/{asset.content_type.value}/{asset.asset_id}/{file_path.name}"

            # TODO: Implement actual Supabase storage upload
            # For now, just return the path
            logger.info(f"Would store file at: {storage_path}")

            return storage_path

        except Exception as e:
            logger.error(f"Failed to store asset file: {e}")
            raise

    async def _store_asset_metadata(self, asset: AssetMetadata):
        """Store asset metadata in Redis"""
        try:
            asset_key = f"roblox:assets:{asset.asset_id}"
            await self.redis_client.hset(
                asset_key,
                mapping={"metadata": asset.model_dump_json()}
            )

            # Add to asset index by type
            index_key = f"roblox:assets:index:{asset.content_type.value}"
            await self.redis_client.sadd(index_key, asset.asset_id)

            # Set TTL (30 days)
            await self.redis_client.expire(asset_key, 2592000)

        except Exception as e:
            logger.error(f"Failed to store asset metadata: {e}")

    async def get_asset(self, asset_id: str) -> Optional[AssetMetadata]:
        """Get asset metadata by ID"""
        try:
            asset_key = f"roblox:assets:{asset_id}"
            data = await self.redis_client.hget(asset_key, "metadata")

            if data:
                return AssetMetadata.model_validate_json(data)

            return None

        except Exception as e:
            logger.error(f"Failed to get asset: {e}")
            return None

    async def list_assets(
        self,
        content_type: Optional[ContentType] = None,
        limit: int = 50
    ) -> List[AssetMetadata]:
        """List assets with optional filtering"""
        try:
            assets = []

            if content_type:
                # Get assets by type
                index_key = f"roblox:assets:index:{content_type.value}"
                asset_ids = await self.redis_client.smembers(index_key)
            else:
                # Get all assets
                pattern = "roblox:assets:*"
                keys = await self.redis_client.keys(pattern)
                asset_ids = [key.split(":")[-1] for key in keys if "index" not in key]

            # Fetch metadata for each asset
            for asset_id in list(asset_ids)[:limit]:
                asset = await self.get_asset(asset_id)
                if asset:
                    assets.append(asset)

            return assets

        except Exception as e:
            logger.error(f"Failed to list assets: {e}")
            return []

    async def create_asset_bundle(
        self,
        name: str,
        asset_ids: List[str],
        description: Optional[str] = None
    ) -> AssetBundle:
        """Create a bundle of related assets"""
        try:
            bundle = AssetBundle(
                name=name,
                description=description
            )

            # Fetch assets and add to bundle
            total_size = 0
            for asset_id in asset_ids:
                asset = await self.get_asset(asset_id)
                if asset:
                    bundle.assets.append(asset)
                    total_size += asset.file_size
                    bundle.deployment_order.append(asset_id)

            bundle.total_size = total_size

            # Store bundle in Redis
            bundle_key = f"roblox:bundles:{bundle.bundle_id}"
            await self.redis_client.hset(
                bundle_key,
                mapping={"bundle": bundle.model_dump_json()}
            )

            # Add to bundle index
            await self.redis_client.sadd("roblox:bundles:index", bundle.bundle_id)

            logger.info(f"Created asset bundle {bundle.bundle_id}: {bundle.name}")
            return bundle

        except Exception as e:
            logger.error(f"Failed to create asset bundle: {e}")
            raise

    async def deploy_asset_bundle(
        self,
        bundle_id: str,
        target_place_id: str,
        priority: int = 5
    ) -> str:
        """Deploy an entire asset bundle"""
        try:
            # Get bundle
            bundle_key = f"roblox:bundles:{bundle_id}"
            data = await self.redis_client.hget(bundle_key, "bundle")

            if not data:
                raise ValueError(f"Bundle {bundle_id} not found")

            bundle = AssetBundle.model_validate_json(data)

            # Queue deployment for each asset in order
            deployment_ids = []
            for asset_id in bundle.deployment_order:
                asset = next((a for a in bundle.assets if a.asset_id == asset_id), None)
                if asset:
                    # Create deployment request
                    request = DeploymentRequest(
                        content_type=asset.content_type,
                        content_data=asset.storage_path or "",
                        target_place_id=target_place_id,
                        priority=priority,
                        metadata={
                            "bundle_id": bundle_id,
                            "asset_id": asset_id,
                            "asset_name": asset.name
                        }
                    )

                    # Queue deployment
                    await self.queue_deployment(request)
                    deployment_ids.append(request.deployment_id)

            logger.info(f"Queued bundle deployment {bundle_id} with {len(deployment_ids)} assets")
            return bundle_id

        except Exception as e:
            logger.error(f"Failed to deploy asset bundle: {e}")
            raise

    async def get_asset_versions(self, asset_name: str) -> List[AssetMetadata]:
        """Get all versions of an asset"""
        try:
            versions = []

            # Search for assets with matching name
            pattern = "roblox:assets:*"
            keys = await self.redis_client.keys(pattern)

            for key in keys:
                if "index" not in key:
                    asset_id = key.split(":")[-1]
                    asset = await self.get_asset(asset_id)
                    if asset and asset.name == asset_name:
                        versions.append(asset)

            # Sort by version number
            versions.sort(key=lambda x: x.version, reverse=True)

            return versions

        except Exception as e:
            logger.error(f"Failed to get asset versions: {e}")
            return []

    async def validate_asset_deployment(
        self,
        asset_id: str,
        place_id: str
    ) -> bool:
        """Validate that an asset was successfully deployed"""
        try:
            # TODO: Implement actual validation using Roblox API
            # Check if asset exists in the place
            logger.info(f"Validating deployment of asset {asset_id} to place {place_id}")

            # For now, return True
            return True

        except Exception as e:
            logger.error(f"Failed to validate asset deployment: {e}")
            return False

    async def rollback_asset_deployment(
        self,
        asset_id: str,
        place_id: str,
        previous_version: Optional[str] = None
    ) -> bool:
        """Rollback an asset deployment"""
        try:
            logger.info(f"Rolling back asset {asset_id} in place {place_id}")

            if previous_version:
                # Deploy previous version
                previous_asset = await self.get_asset(previous_version)
                if previous_asset:
                    request = DeploymentRequest(
                        content_type=previous_asset.content_type,
                        content_data=previous_asset.storage_path or "",
                        target_place_id=place_id,
                        priority=10,  # High priority for rollback
                        metadata={
                            "rollback": True,
                            "original_asset": asset_id,
                            "previous_version": previous_version
                        }
                    )
                    await self.queue_deployment(request)
                    return True
            else:
                # Remove asset from place
                # TODO: Implement asset removal
                logger.info(f"Would remove asset {asset_id} from place {place_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to rollback asset deployment: {e}")
            return False


# Asset Manager class for standalone asset operations
class RobloxAssetManager:
    """Manages Roblox assets independently from deployment pipeline"""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client: Optional[redis.Redis] = None
        self.supabase = SupabaseService() if hasattr(SupabaseService, '__init__') else None

        # Roblox API configuration
        self.roblox_api_key = os.getenv("ROBLOX_API_KEY")
        self.roblox_universe_id = os.getenv("ROBLOX_UNIVERSE_ID")

    async def initialize(self):
        """Initialize connections"""
        self.redis_client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await self.redis_client.ping()
        logger.info("Asset manager initialized")

    async def import_from_roblox(
        self,
        asset_id: str,
        asset_type: ContentType
    ) -> AssetMetadata:
        """Import an existing Roblox asset"""
        try:
            # TODO: Use Roblox API to fetch asset details
            logger.info(f"Importing Roblox asset {asset_id}")

            # Create metadata
            metadata = AssetMetadata(
                name=f"imported_asset_{asset_id}",
                content_type=asset_type,
                file_size=0,  # Will be updated after download
                file_hash="",  # Will be calculated
                roblox_asset_id=asset_id
            )

            return metadata

        except Exception as e:
            logger.error(f"Failed to import Roblox asset: {e}")
            raise

    async def export_to_roblox(
        self,
        asset: AssetMetadata,
        place_id: str
    ) -> str:
        """Export asset to Roblox"""
        try:
            # TODO: Implement actual Roblox API upload
            logger.info(f"Exporting asset {asset.asset_id} to Roblox place {place_id}")

            # Return mock Roblox asset ID
            return f"rbxasset://{uuid.uuid4()}"

        except Exception as e:
            logger.error(f"Failed to export asset to Roblox: {e}")
            raise


# Singleton instances
_deployment_pipeline: Optional[RobloxDeploymentPipeline] = None
_asset_manager: Optional[RobloxAssetManager] = None


async def get_deployment_pipeline() -> RobloxDeploymentPipeline:
    """Get or create deployment pipeline instance"""
    global _deployment_pipeline

    if _deployment_pipeline is None:
        _deployment_pipeline = RobloxDeploymentPipeline()
        await _deployment_pipeline.initialize()

    return _deployment_pipeline


async def get_asset_manager() -> RobloxAssetManager:
    """Get or create asset manager instance"""
    global _asset_manager

    if _asset_manager is None:
        _asset_manager = RobloxAssetManager()
        await _asset_manager.initialize()

    return _asset_manager
