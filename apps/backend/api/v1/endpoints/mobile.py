"""
Mobile API Module

Provides optimized endpoints and functionality for mobile applications.
Includes push notifications, offline sync, and mobile-specific optimizations.
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.api.auth.auth import create_access_token, get_current_user
from apps.backend.core.cache import cache_result
from apps.backend.core.deps import get_async_db as get_db
from database.models import Content, UserProgress

router = APIRouter(prefix="/api/mobile", tags=["mobile"])


class DeviceType(str, Enum):
    """Supported device types"""

    IOS = "ios"
    ANDROID = "android"
    TABLET = "tablet"


class SyncDirection(str, Enum):
    """Data synchronization direction"""

    UPLOAD = "upload"
    DOWNLOAD = "download"
    BIDIRECTIONAL = "bidirectional"


class DeviceRegistration(BaseModel):
    """Device registration model"""

    device_id: str
    device_type: DeviceType
    push_token: str | None = None
    app_version: str
    os_version: str
    timezone: str | None = "UTC"


class OfflineSyncRequest(BaseModel):
    """Offline sync request model"""

    device_id: str
    last_sync: datetime
    local_changes: list[dict[str, Any]]
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL


class PushNotificationRequest(BaseModel):
    """Push notification request model"""

    user_ids: list[str] | None = None
    device_ids: list[str] | None = None
    title: str
    message: str
    data: dict[str, Any] | None = None
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    schedule_time: datetime | None = None


class MobileContentResponse(BaseModel):
    """Optimized content response for mobile"""

    id: str
    title: str
    summary: str
    content_preview: str
    estimated_time: int
    offline_available: bool
    download_size: int
    last_updated: datetime
    thumbnail_url: str | None = None


class MobileProgressUpdate(BaseModel):
    """Mobile progress update model"""

    content_id: str
    progress_percentage: float
    time_spent: int
    completed: bool
    offline_mode: bool = False
    device_id: str


class MobileOptimizer:
    """Utilities for mobile optimization"""

    @staticmethod
    def compress_response(data: dict[str, Any], quality: str = "medium") -> dict[str, Any]:
        """
        Compress response data for mobile bandwidth optimization

        Args:
            data: Original response data
            quality: Compression quality (low, medium, high)

        Returns:
            Compressed data
        """
        if quality == "low":
            # Remove non-essential fields
            essential_fields = ["id", "title", "summary", "progress"]
            return {k: v for k, v in data.items() if k in essential_fields}
        elif quality == "medium":
            # Truncate long text fields
            compressed = data.copy()
            for key, value in compressed.items():
                if isinstance(value, str) and len(value) > 500:
                    compressed[key] = value[:500] + "..."
            return compressed
        else:
            # High quality - return full data
            return data

    @staticmethod
    def generate_cache_key(endpoint: str, params: dict[str, Any], user_id: str) -> str:
        """Generate cache key for mobile requests"""
        key_data = f"{endpoint}:{user_id}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    @staticmethod
    def calculate_content_size(content: dict[str, Any]) -> int:
        """Calculate approximate download size in bytes"""
        return len(json.dumps(content).encode("utf-8"))


class PushNotificationService:
    """Service for handling push notifications"""

    def __init__(self):
        self.providers = {
            DeviceType.IOS: self._send_apns,
            DeviceType.ANDROID: self._send_fcm,
            DeviceType.TABLET: self._send_fcm,
        }

    async def send_notification(
        self,
        device_token: str,
        device_type: DeviceType,
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """
        Send push notification to device

        Args:
            device_token: Device push token
            device_type: Type of device
            title: Notification title
            message: Notification message
            data: Additional data payload

        Returns:
            Success status
        """
        provider = self.providers.get(device_type)
        if provider:
            return await provider(device_token, title, message, data)
        return False

    async def _send_apns(
        self, token: str, title: str, message: str, data: dict[str, Any] | None
    ) -> bool:
        """Send notification via Apple Push Notification Service"""
        # Implementation would use APNS library
        print(f"APNS: Sending to {token}: {title}")
        return True

    async def _send_fcm(
        self, token: str, title: str, message: str, data: dict[str, Any] | None
    ) -> bool:
        """Send notification via Firebase Cloud Messaging"""
        # Implementation would use FCM library
        print(f"FCM: Sending to {token}: {title}")
        return True


class OfflineSyncManager:
    """Manager for offline data synchronization"""

    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def sync_data(
        self,
        user_id: str,
        device_id: str,
        last_sync: datetime,
        local_changes: list[dict[str, Any]],
        direction: SyncDirection,
    ) -> dict[str, Any]:
        """
        Synchronize offline data

        Args:
            user_id: User ID
            device_id: Device ID
            last_sync: Last synchronization timestamp
            local_changes: Local changes to upload
            direction: Sync direction

        Returns:
            Sync result with conflicts and updates
        """
        result = {
            "status": "success",
            "timestamp": datetime.now(timezone.utc),
            "uploaded": 0,
            "downloaded": 0,
            "conflicts": [],
            "updates": [],
        }

        # Process uploads
        if direction in [SyncDirection.UPLOAD, SyncDirection.BIDIRECTIONAL]:
            for change in local_changes:
                conflict = await self._process_local_change(user_id, change, last_sync)
                if conflict:
                    result["conflicts"].append(conflict)
                else:
                    result["uploaded"] += 1

        # Process downloads
        if direction in [SyncDirection.DOWNLOAD, SyncDirection.BIDIRECTIONAL]:
            updates = await self._get_server_updates(user_id, last_sync)
            result["updates"] = updates
            result["downloaded"] = len(updates)

        # Record sync event
        await self._record_sync_event(user_id, device_id, result)

        return result

    async def _process_local_change(
        self, user_id: str, change: dict[str, Any], last_sync: datetime
    ) -> dict[str, Any] | None:
        """Process a local change from mobile device"""
        # Check for conflicts
        entity_type = change.get("type")
        entity_id = change.get("id")
        # Parse timestamp for server-side validation
        _ = datetime.fromisoformat(change.get("timestamp"))

        # Get server version
        server_version = await self._get_server_version(entity_type, entity_id)

        if server_version and server_version["updated_at"] > last_sync:
            # Conflict detected
            return {
                "type": entity_type,
                "id": entity_id,
                "local_version": change,
                "server_version": server_version,
                "resolution": "manual",  # Or implement auto-resolution
            }

        # Apply change
        await self._apply_change(user_id, change)
        return None

    async def _get_server_updates(self, user_id: str, since: datetime) -> list[dict[str, Any]]:
        """Get updates from server since last sync"""
        updates = []

        # Get updated content
        content_query = select(Content).where(
            and_(Content.updated_at > since, Content.is_published)
        )
        content_result = await self.session.execute(content_query)
        for content in content_result.scalars():
            updates.append(
                {
                    "type": "content",
                    "id": str(content.id),
                    "data": {
                        "title": content.title,
                        "content": content.content,
                        "updated_at": content.updated_at.isoformat(),
                    },
                }
            )

        # Get user progress updates
        progress_query = select(UserProgress).where(
            and_(UserProgress.user_id == user_id, UserProgress.updated_at > since)
        )
        progress_result = await self.session.execute(progress_query)
        for progress in progress_result.scalars():
            updates.append(
                {
                    "type": "progress",
                    "id": str(progress.id),
                    "data": {
                        "content_id": str(progress.content_id),
                        "percentage": progress.completion_percentage,
                        "updated_at": progress.updated_at.isoformat(),
                    },
                }
            )

        return updates

    async def _get_server_version(self, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        """Get server version of an entity"""
        # Implementation would fetch entity from database
        return None

    async def _apply_change(self, user_id: str, change: dict[str, Any]):
        """Apply a change to the server database"""
        # Implementation would update database
        pass

    async def _record_sync_event(self, user_id: str, device_id: str, result: dict[str, Any]):
        """Record synchronization event for audit"""
        # Implementation would log sync event
        pass


# Initialize services
push_service = PushNotificationService()
optimizer = MobileOptimizer()


@router.post("/register-device")
async def register_device(
    registration: DeviceRegistration,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Register a mobile device for push notifications and sync
    """
    # Store device registration
    # Implementation would save to database

    return {
        "status": "registered",
        "device_id": registration.device_id,
        "user_id": current_user["id"],
        "push_enabled": registration.push_token is not None,
    }


@router.post("/auth/mobile-login")
async def mobile_login(
    email: str,
    password: str,
    device_id: str,
    device_type: DeviceType,
    db: AsyncSession = Depends(get_db),
):
    """
    Mobile-optimized login endpoint with extended token validity
    """
    # Authenticate user (implementation would verify credentials)
    # For mobile, create longer-lived tokens

    access_token = create_access_token(
        data={"sub": email, "device_id": device_id},
        expires_delta=timedelta(days=30),  # Longer for mobile
    )

    refresh_token = create_access_token(
        data={"sub": email, "device_id": device_id, "type": "refresh"},
        expires_delta=timedelta(days=90),
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 30 * 24 * 3600,  # 30 days in seconds
    }


@router.get("/content/mobile-list")
@cache_result(expire=600)
async def get_mobile_content_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=50),
    quality: str = Query(default="medium", regex="^(low|medium|high)$"),
    offline_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[MobileContentResponse]:
    """
    Get optimized content list for mobile devices

    Features:
    - Pagination for efficient loading
    - Quality-based response compression
    - Offline availability filtering
    """
    offset = (page - 1) * page_size

    query = select(Content).where(Content.is_published)

    if offline_only:
        query = query.where(Content.offline_available)

    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    contents = result.scalars().all()

    mobile_contents = []
    for content in contents:
        mobile_content = MobileContentResponse(
            id=str(content.id),
            title=content.title,
            summary=content.summary or content.content[:200],
            content_preview=content.content[:500] if quality != "low" else content.content[:200],
            estimated_time=content.estimated_duration or 10,
            offline_available=content.offline_available or False,
            download_size=optimizer.calculate_content_size(content.__dict__),
            last_updated=content.updated_at,
            thumbnail_url=content.thumbnail_url,
        )

        # Apply quality-based compression
        if quality == "low":
            # Remove preview for low quality
            mobile_content.content_preview = ""

        mobile_contents.append(mobile_content)

    return mobile_contents


@router.post("/sync")
async def sync_offline_data(
    sync_request: OfflineSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Synchronize offline data between mobile device and server

    Handles:
    - Bidirectional sync
    - Conflict resolution
    - Delta updates
    """
    sync_manager = OfflineSyncManager(db)

    result = await sync_manager.sync_data(
        user_id=current_user["id"],
        device_id=sync_request.device_id,
        last_sync=sync_request.last_sync,
        local_changes=sync_request.local_changes,
        direction=sync_request.sync_direction,
    )

    return result


@router.post("/progress/batch-update")
async def batch_update_progress(
    updates: list[MobileProgressUpdate],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Batch update progress from mobile device

    Optimized for offline usage - accepts multiple progress updates at once
    """
    success_count = 0
    failed_updates = []

    for update in updates:
        try:
            # Update progress in database
            # Implementation would update UserProgress model
            success_count += 1
        except Exception as e:
            failed_updates.append({"content_id": update.content_id, "error": str(e)})

    return {
        "success_count": success_count,
        "failed_count": len(failed_updates),
        "failed_updates": failed_updates,
        "sync_timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/push/send")
async def send_push_notification(
    notification: PushNotificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Send push notifications to mobile devices

    Requires admin or teacher role
    """
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Get device tokens
    device_tokens = []

    if notification.user_ids:
        # Get devices for specified users
        # Implementation would query device registrations
        pass

    if notification.device_ids:
        # Use specified device IDs
        device_tokens.extend(notification.device_ids)

    # Schedule or send immediately
    if notification.schedule_time:
        # Schedule for later
        background_tasks.add_task(
            send_scheduled_notification,
            device_tokens,
            notification,
            notification.schedule_time,
        )
        return {"status": "scheduled", "delivery_time": notification.schedule_time}
    else:
        # Send immediately
        sent_count = 0
        for token in device_tokens:
            success = await push_service.send_notification(
                device_token=token,
                device_type=DeviceType.IOS,  # Would be determined from registration
                title=notification.title,
                message=notification.message,
                data=notification.data,
            )
            if success:
                sent_count += 1

        return {
            "status": "sent",
            "sent_count": sent_count,
            "total_devices": len(device_tokens),
        }


@router.get("/content/{content_id}/download")
async def download_content_for_offline(
    content_id: str,
    quality: str = Query(default="high", regex="^(low|medium|high)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Download content for offline usage

    Returns optimized content package based on quality setting
    """
    # Get content
    content = await db.get(Content, content_id)

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Prepare offline package
    offline_package = {
        "id": str(content.id),
        "title": content.title,
        "content": content.content,
        "quizzes": [],
        "resources": [],
        "metadata": {
            "version": content.version or 1,
            "last_updated": content.updated_at.isoformat(),
            "expires": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        },
    }

    # Get associated quizzes
    if content.quizzes:
        for quiz in content.quizzes:
            quiz_data = {
                "id": str(quiz.id),
                "title": quiz.title,
                "questions": quiz.questions,
            }
            if quality == "low":
                # Remove explanations for low quality
                for q in quiz_data["questions"]:
                    q.pop("explanation", None)
            offline_package["quizzes"].append(quiz_data)

    # Apply compression based on quality
    compressed_package = optimizer.compress_response(offline_package, quality)

    return JSONResponse(
        content=compressed_package,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": f"max-age={7 * 24 * 3600}",  # Cache for 7 days
            "X-Content-Version": str(content.version or 1),
        },
    )


@router.get("/network-status")
async def check_network_optimization(
    user_agent: str | None = Header(None), accept_encoding: str | None = Header(None)
):
    """
    Check network status and recommend optimization settings

    Helps mobile apps determine best quality settings
    """
    recommendations = {
        "compression_supported": False,
        "recommended_quality": "medium",
        "batch_size": 20,
        "cache_duration": 3600,
        "offline_sync_interval": 300,  # 5 minutes
    }

    # Check compression support
    if accept_encoding and "gzip" in accept_encoding:
        recommendations["compression_supported"] = True

    # Analyze user agent for device type
    if user_agent:
        if "iPhone" in user_agent or "iPad" in user_agent:
            recommendations["recommended_quality"] = "high"
            recommendations["batch_size"] = 30
        elif "Android" in user_agent:
            if "Mobile" in user_agent:
                recommendations["recommended_quality"] = "medium"
                recommendations["batch_size"] = 20
            else:  # Tablet
                recommendations["recommended_quality"] = "high"
                recommendations["batch_size"] = 30

    return recommendations


@router.get("/data-usage")
async def get_data_usage_stats(
    device_id: str,
    period_days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get data usage statistics for mobile device

    Helps users monitor their data consumption
    """
    # Calculate data usage
    # Implementation would track API calls and data transfers

    return {
        "device_id": device_id,
        "period_days": period_days,
        "total_downloaded_mb": 150.5,
        "total_uploaded_mb": 12.3,
        "api_calls": 1234,
        "cached_requests": 456,
        "cache_hit_rate": 0.37,
        "average_response_size_kb": 15.2,
        "recommendations": [
            "Enable offline mode during low connectivity",
            "Use 'low' quality setting to reduce data usage",
            "Sync during Wi-Fi connection",
        ],
    }


async def send_scheduled_notification(
    device_tokens: list[str],
    notification: PushNotificationRequest,
    scheduled_time: datetime,
):
    """Background task to send scheduled notifications"""
    # Wait until scheduled time
    wait_seconds = (scheduled_time - datetime.now(timezone.utc)).total_seconds()
    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)

    # Send notifications
    for token in device_tokens:
        await push_service.send_notification(
            device_token=token,
            device_type=DeviceType.IOS,  # Would be determined
            title=notification.title,
            message=notification.message,
            data=notification.data,
        )
