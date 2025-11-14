"""
Storage WebSocket API for ToolBoxAI Educational Platform

Provides real-time updates for storage operations including upload progress,
quota alerts, processing status, and file operations via WebSocket connections.

Features:
- Real-time upload progress tracking
- Storage quota threshold alerts
- File processing status updates
- Virus scan result notifications
- Bulk operation progress
- Administrative alerts

Author: ToolBoxAI Team
Created: 2025-01-27
Version: 1.0.0
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


# === CONNECTION MANAGER ===


class StorageWebSocketManager:
    """
    Manages WebSocket connections for storage-related real-time updates.

    Supports:
    - Per-organization connection pools
    - User-specific upload progress tracking
    - Broadcast messaging for quota alerts
    - Connection lifecycle management
    """

    def __init__(self):
        # Organization-based connection pools
        self.organization_connections: dict[str, list[WebSocket]] = {}

        # User-specific connections for upload progress
        self.user_connections: dict[str, list[WebSocket]] = {}

        # Upload-specific connections for progress tracking
        self.upload_connections: dict[str, list[WebSocket]] = {}

        # Admin connections for system-wide alerts
        self.admin_connections: list[WebSocket] = []

    async def connect_organization(self, websocket: WebSocket, organization_id: str, user_id: str):
        """Connect a user to organization storage updates"""
        await websocket.accept()

        # Add to organization pool
        if organization_id not in self.organization_connections:
            self.organization_connections[organization_id] = []
        self.organization_connections[organization_id].append(websocket)

        # Add to user pool
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)

        logger.info(f"WebSocket connected: user={user_id}, org={organization_id}")

        # Send initial quota status
        await self.send_quota_status(organization_id)

    async def connect_upload_tracking(self, websocket: WebSocket, upload_id: str, user_id: str):
        """Connect to track specific upload progress"""
        await websocket.accept()

        # Add to upload tracking pool
        if upload_id not in self.upload_connections:
            self.upload_connections[upload_id] = []
        self.upload_connections[upload_id].append(websocket)

        # Also add to user pool
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)

        logger.info(f"Upload tracking connected: upload_id={upload_id}, user={user_id}")

    async def connect_admin(self, websocket: WebSocket, user_id: str):
        """Connect admin user for system-wide storage alerts"""
        await websocket.accept()
        self.admin_connections.append(websocket)

        logger.info(f"Admin WebSocket connected: user={user_id}")

    def disconnect(self, websocket: WebSocket):
        """Disconnect and clean up WebSocket"""
        # Remove from all connection pools
        for org_connections in self.organization_connections.values():
            if websocket in org_connections:
                org_connections.remove(websocket)

        for user_connections in self.user_connections.values():
            if websocket in user_connections:
                user_connections.remove(websocket)

        for upload_connections in self.upload_connections.values():
            if websocket in upload_connections:
                upload_connections.remove(websocket)

        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)

        logger.info("WebSocket disconnected and cleaned up")

    async def send_to_organization(self, organization_id: str, message: dict[str, Any]):
        """Send message to all connections in an organization"""
        if organization_id in self.organization_connections:
            connections = self.organization_connections[organization_id].copy()
            disconnected = []

            for connection in connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send to organization connection: {e}")
                    disconnected.append(connection)

            # Clean up disconnected connections
            for connection in disconnected:
                self.organization_connections[organization_id].remove(connection)

    async def send_to_user(self, user_id: str, message: dict[str, Any]):
        """Send message to all connections for a specific user"""
        if user_id in self.user_connections:
            connections = self.user_connections[user_id].copy()
            disconnected = []

            for connection in connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send to user connection: {e}")
                    disconnected.append(connection)

            # Clean up disconnected connections
            for connection in disconnected:
                self.user_connections[user_id].remove(connection)

    async def send_to_upload(self, upload_id: str, message: dict[str, Any]):
        """Send message to all connections tracking a specific upload"""
        if upload_id in self.upload_connections:
            connections = self.upload_connections[upload_id].copy()
            disconnected = []

            for connection in connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send to upload connection: {e}")
                    disconnected.append(connection)

            # Clean up disconnected connections
            for connection in disconnected:
                self.upload_connections[upload_id].remove(connection)

    async def send_to_admins(self, message: dict[str, Any]):
        """Send message to all admin connections"""
        disconnected = []

        for connection in self.admin_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send to admin connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.admin_connections.remove(connection)

    async def broadcast_quota_alert(self, organization_id: str, alert_data: dict[str, Any]):
        """Broadcast quota alert to organization and admins"""
        alert_message = {
            "type": "quota_alert",
            "organization_id": organization_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": alert_data,
        }

        # Send to organization
        await self.send_to_organization(organization_id, alert_message)

        # Send to admins
        await self.send_to_admins(alert_message)

    async def send_upload_progress(self, upload_id: str, progress_data: dict[str, Any]):
        """Send upload progress update"""
        progress_message = {
            "type": "upload_progress",
            "upload_id": upload_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": progress_data,
        }

        await self.send_to_upload(upload_id, progress_message)

    async def send_processing_status(self, file_id: str, user_id: str, status_data: dict[str, Any]):
        """Send file processing status update"""
        status_message = {
            "type": "processing_status",
            "file_id": file_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": status_data,
        }

        await self.send_to_user(user_id, status_message)

    async def send_quota_status(self, organization_id: str):
        """Send current quota status to organization"""
        # In production, this would query the actual quota from database
        quota_status = {
            "organization_id": organization_id,
            "total_quota_bytes": 5368709120,  # 5GB
            "used_storage_bytes": 2147483648,  # 2GB
            "used_percentage": 40.0,
            "available_bytes": 3221225472,
            "warning_threshold": 80,
            "critical_threshold": 95,
            "is_warning_reached": False,
            "is_critical_reached": False,
            "last_updated": datetime.utcnow().isoformat(),
        }

        quota_message = {
            "type": "quota_status",
            "organization_id": organization_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": quota_status,
        }

        await self.send_to_organization(organization_id, quota_message)


# Global WebSocket manager instance
ws_manager = StorageWebSocketManager()


# === WEBSOCKET ENDPOINTS ===


@router.websocket("/ws/storage/{organization_id}")
async def websocket_storage_updates(
    websocket: WebSocket,
    organization_id: str,
    # In production, would validate WebSocket authentication
    # current_user: User = Depends(get_current_user_ws),
    # tenant_context: TenantContext = Depends(get_current_tenant)
):
    """
    WebSocket endpoint for organization storage updates.

    Provides real-time updates for:
    - Storage quota changes
    - File upload/delete operations
    - Quota threshold alerts
    - Storage optimization results
    """
    # Mock user authentication for WebSocket
    user_id = "mock-user-id"  # Would come from authentication

    await ws_manager.connect_organization(websocket, organization_id, user_id)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "request_quota_status":
                await ws_manager.send_quota_status(organization_id)

            elif message_type == "ping":
                await websocket.send_text(
                    json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                )

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info(f"Storage WebSocket disconnected: org={organization_id}, user={user_id}")


@router.websocket("/ws/upload/{upload_id}")
async def websocket_upload_progress(
    websocket: WebSocket,
    upload_id: str,
    # current_user: User = Depends(get_current_user_ws)
):
    """
    WebSocket endpoint for upload progress tracking.

    Provides real-time updates for:
    - Upload progress percentage
    - Processing status (virus scan, optimization)
    - Error notifications
    - Completion status
    """
    # Mock user authentication for WebSocket
    user_id = "mock-user-id"  # Would come from authentication

    await ws_manager.connect_upload_tracking(websocket, upload_id, user_id)

    try:
        # Send initial progress if available
        await ws_manager.send_upload_progress(
            upload_id,
            {
                "status": "connected",
                "progress_percentage": 0.0,
                "message": "Upload tracking connected",
            },
        )

        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "request_status":
                # In production, would query actual upload status
                await ws_manager.send_upload_progress(
                    upload_id,
                    {
                        "status": "in_progress",
                        "progress_percentage": 45.0,
                        "bytes_uploaded": 1048576,
                        "total_bytes": 2097152,
                        "estimated_completion": (
                            datetime.utcnow() + timedelta(minutes=2)
                        ).isoformat(),
                    },
                )

            elif message_type == "ping":
                await websocket.send_text(
                    json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                )

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info(f"Upload WebSocket disconnected: upload_id={upload_id}, user={user_id}")


@router.websocket("/ws/storage/admin")
async def websocket_admin_alerts(
    websocket: WebSocket,
    # current_user: User = Depends(get_current_user_ws)
):
    """
    WebSocket endpoint for administrative storage alerts.

    Provides real-time updates for:
    - System-wide quota alerts
    - Security threats detected
    - Storage optimization results
    - System maintenance notifications
    """
    # Mock admin authentication
    user_id = "mock-admin-id"  # Would come from authentication

    await ws_manager.connect_admin(websocket, user_id)

    try:
        # Send initial admin status
        await websocket.send_text(
            json.dumps(
                {
                    "type": "admin_connected",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Connected to admin storage alerts",
                }
            )
        )

        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "request_system_status":
                # Send system-wide storage status
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "system_status",
                            "timestamp": datetime.utcnow().isoformat(),
                            "data": {
                                "total_organizations": 10,
                                "organizations_over_quota": 1,
                                "active_uploads": 5,
                                "pending_virus_scans": 12,
                                "storage_optimization_running": False,
                                "last_cleanup": (
                                    datetime.utcnow() - timedelta(hours=6)
                                ).isoformat(),
                            },
                        }
                    )
                )

            elif message_type == "ping":
                await websocket.send_text(
                    json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                )

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info(f"Admin WebSocket disconnected: user={user_id}")


# === UTILITY FUNCTIONS FOR TRIGGERING UPDATES ===


async def trigger_upload_progress_update(upload_id: str, progress_data: dict[str, Any]):
    """Trigger upload progress update via WebSocket"""
    await ws_manager.send_upload_progress(upload_id, progress_data)


async def trigger_quota_alert(organization_id: str, alert_data: dict[str, Any]):
    """Trigger quota alert via WebSocket"""
    await ws_manager.broadcast_quota_alert(organization_id, alert_data)


async def trigger_processing_status_update(file_id: str, user_id: str, status_data: dict[str, Any]):
    """Trigger file processing status update via WebSocket"""
    await ws_manager.send_processing_status(file_id, user_id, status_data)


async def trigger_admin_alert(alert_data: dict[str, Any]):
    """Trigger admin alert via WebSocket"""
    admin_message = {
        "type": "admin_alert",
        "timestamp": datetime.utcnow().isoformat(),
        "data": alert_data,
    }
    await ws_manager.send_to_admins(admin_message)


# === BACKGROUND TASK INTEGRATION ===

# These functions would be called from Celery tasks to send real-time updates


def notify_upload_progress(upload_id: str, progress_percentage: float, status: str, **kwargs):
    """
    Notify WebSocket clients of upload progress.
    Called from upload tasks.
    """
    progress_data = {
        "status": status,
        "progress_percentage": progress_percentage,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs,
    }

    # Schedule WebSocket update
    asyncio.create_task(trigger_upload_progress_update(upload_id, progress_data))


def notify_virus_scan_result(file_id: str, user_id: str, scan_result: dict[str, Any]):
    """
    Notify WebSocket clients of virus scan results.
    Called from virus scan tasks.
    """
    status_data = {
        "type": "virus_scan_complete",
        "file_id": file_id,
        "scan_result": scan_result,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Schedule WebSocket update
    asyncio.create_task(trigger_processing_status_update(file_id, user_id, status_data))


def notify_quota_threshold_exceeded(
    organization_id: str, threshold_type: str, usage_data: dict[str, Any]
):
    """
    Notify WebSocket clients of quota threshold exceeded.
    Called from quota monitoring tasks.
    """
    alert_data = {
        "alert_type": "quota_threshold_exceeded",
        "threshold_type": threshold_type,  # "warning" or "critical"
        "usage_data": usage_data,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Schedule WebSocket update
    asyncio.create_task(trigger_quota_alert(organization_id, alert_data))


def notify_security_threat(organization_id: str, file_id: str, threat_data: dict[str, Any]):
    """
    Notify WebSocket clients of security threat detected.
    Called from virus scan tasks.
    """
    alert_data = {
        "alert_type": "security_threat",
        "file_id": file_id,
        "organization_id": organization_id,
        "threat_data": threat_data,
        "timestamp": datetime.utcnow().isoformat(),
        "severity": "high",
    }

    # Schedule WebSocket update
    asyncio.create_task(trigger_admin_alert(alert_data))


def notify_storage_optimization_complete(
    organization_id: str, optimization_results: dict[str, Any]
):
    """
    Notify WebSocket clients of storage optimization completion.
    Called from optimization tasks.
    """
    alert_data = {
        "alert_type": "optimization_complete",
        "organization_id": organization_id,
        "results": optimization_results,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Schedule WebSocket update
    asyncio.create_task(trigger_admin_alert(alert_data))


# Export the WebSocket manager for use by other modules
__all__ = [
    "ws_manager",
    "trigger_upload_progress_update",
    "trigger_quota_alert",
    "trigger_processing_status_update",
    "trigger_admin_alert",
    "notify_upload_progress",
    "notify_virus_scan_result",
    "notify_quota_threshold_exceeded",
    "notify_security_threat",
    "notify_storage_optimization_complete",
]
