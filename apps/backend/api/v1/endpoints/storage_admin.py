"""
Storage Admin API for ToolBoxAI Educational Platform

Provides administrative storage operations including usage monitoring,
quota management, security scanning, and maintenance operations.

Features:
- Organization storage usage analytics
- Quota management and enforcement
- Security scanning and virus detection
- Cleanup operations for expired files
- Storage optimization and maintenance
- Admin-level permissions required

Author: ToolBoxAI Team
Created: 2025-01-27
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    Query
)
from pydantic import BaseModel, Field, validator

from apps.backend.api.auth.auth import get_current_user
from apps.backend.dependencies.tenant import (
    require_tenant_admin,
    get_current_tenant,
    TenantContext
)
from apps.backend.models.schemas import User
from apps.backend.services.storage.storage_service import StorageService, StorageError
from apps.backend.workers.tasks.storage_tasks import (
    virus_scan_file,
    cleanup_expired_files,
    calculate_storage_usage,
    send_quota_alerts,
    optimize_storage,
    generate_storage_report
)

logger = logging.getLogger(__name__)

router = APIRouter()


# === REQUEST/RESPONSE MODELS ===

class OrganizationUsageStats(BaseModel):
    """Organization storage usage statistics"""
    organization_id: UUID
    organization_name: str
    total_quota_bytes: int
    used_storage_bytes: int
    available_storage_bytes: int
    used_percentage: float
    file_count: int
    active_file_count: int
    deleted_file_count: int
    shared_file_count: int
    user_count: int
    last_activity_at: Optional[datetime] = None

    # Category breakdown
    category_breakdown: Dict[str, int] = Field(default_factory=dict)

    # File type breakdown
    file_type_breakdown: Dict[str, int] = Field(default_factory=dict)

    # Usage trends
    daily_upload_bytes: int = 0
    weekly_upload_bytes: int = 0
    monthly_upload_bytes: int = 0

    # Security stats
    virus_scan_count: int = 0
    quarantined_file_count: int = 0

    # Sharing stats
    public_share_count: int = 0
    private_share_count: int = 0
    expired_share_count: int = 0


class StorageUsageResponse(BaseModel):
    """Response for storage usage endpoint"""
    organizations: List[OrganizationUsageStats]
    total_organizations: int
    global_stats: Dict[str, Any]
    generated_at: datetime


class VirusScanRequest(BaseModel):
    """Request for virus scan operation"""
    target_type: str = Field(..., regex="^(organization|file|all_files)$")
    organization_id: Optional[UUID] = None
    file_id: Optional[UUID] = None
    force_rescan: bool = False
    scan_priority: str = Field(default="normal", regex="^(low|normal|high|urgent)$")

    @validator('organization_id')
    def validate_organization_required(cls, v, values):
        if values.get('target_type') == 'organization' and not v:
            raise ValueError("organization_id required when target_type is 'organization'")
        return v

    @validator('file_id')
    def validate_file_required(cls, v, values):
        if values.get('target_type') == 'file' and not v:
            raise ValueError("file_id required when target_type is 'file'")
        return v


class VirusScanResponse(BaseModel):
    """Response for virus scan operation"""
    scan_id: str
    target_type: str
    target_id: Optional[str] = None
    status: str  # "queued", "in_progress", "completed", "failed"
    files_to_scan: int
    files_scanned: int = 0
    threats_found: int = 0
    quarantined_files: int = 0
    scan_priority: str
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class CleanupRequest(BaseModel):
    """Request for cleanup operation"""
    cleanup_type: str = Field(..., regex="^(expired_files|deleted_files|orphaned_shares|temp_files|all)$")
    organization_id: Optional[UUID] = None
    older_than_days: int = Field(default=30, ge=1, le=365)
    dry_run: bool = False
    force_cleanup: bool = False

    @validator('older_than_days')
    def validate_retention_period(cls, v, values):
        cleanup_type = values.get('cleanup_type')
        if cleanup_type == 'deleted_files' and v < 7:
            raise ValueError("Deleted files must be older than 7 days for cleanup")
        return v


class CleanupResponse(BaseModel):
    """Response for cleanup operation"""
    cleanup_id: str
    cleanup_type: str
    target_organization: Optional[str] = None
    status: str  # "queued", "in_progress", "completed", "failed"
    dry_run: bool
    older_than_days: int
    files_processed: int = 0
    files_deleted: int = 0
    space_freed_bytes: int = 0
    errors_encountered: int = 0
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_summary: Optional[str] = None


class QuotaUpdateRequest(BaseModel):
    """Request for quota update"""
    organization_id: UUID
    total_quota_bytes: Optional[int] = Field(None, ge=1024*1024)  # Min 1MB
    max_files: Optional[int] = Field(None, ge=1)
    max_file_size_mb: Optional[int] = Field(None, ge=1, le=5000)  # Max 5GB
    max_video_size_mb: Optional[int] = Field(None, ge=1, le=10000)  # Max 10GB
    max_image_size_mb: Optional[int] = Field(None, ge=1, le=100)  # Max 100MB
    max_document_size_mb: Optional[int] = Field(None, ge=1, le=500)  # Max 500MB
    warning_threshold_percent: Optional[int] = Field(None, ge=50, le=95)
    critical_threshold_percent: Optional[int] = Field(None, ge=80, le=99)
    reason: str = Field(..., min_length=10, max_length=500)

    @validator('critical_threshold_percent')
    def validate_thresholds(cls, v, values):
        warning = values.get('warning_threshold_percent')
        if warning and v and v <= warning:
            raise ValueError("Critical threshold must be higher than warning threshold")
        return v


class QuotaUpdateResponse(BaseModel):
    """Response for quota update"""
    organization_id: UUID
    previous_quota: Dict[str, Any]
    new_quota: Dict[str, Any]
    updated_by: UUID
    updated_at: datetime
    reason: str
    effective_immediately: bool = True


# === DEPENDENCIES ===

async def get_storage_service(
    user_tenant: tuple[User, TenantContext] = Depends(require_tenant_admin)
) -> StorageService:
    """Get storage service with admin context"""
    user, tenant_context = user_tenant

    from apps.backend.services.storage.supabase_provider import SupabaseStorageProvider

    service = SupabaseStorageProvider(
        organization_id=tenant_context.effective_tenant_id,
        user_id=str(user.id)
    )

    return service


# === USAGE MONITORING ENDPOINTS ===

@router.get("/usage", response_model=StorageUsageResponse)
async def get_organization_usage_stats(
    organization_ids: Optional[str] = Query(None, description="Comma-separated organization IDs"),
    include_trends: bool = Query(True, description="Include usage trends"),
    include_breakdown: bool = Query(True, description="Include category/type breakdown"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum organizations to return"),
    offset: int = Query(0, ge=0, description="Number of organizations to skip"),
    user_tenant: tuple[User, TenantContext] = Depends(require_tenant_admin)
):
    """
    Get comprehensive storage usage statistics for organizations.

    Admin endpoint that provides detailed analytics including:
    - Storage quota and usage
    - File counts and categories
    - User activity metrics
    - Security scan results
    - Sharing statistics
    """
    user, tenant_context = user_tenant

    try:
        # Parse organization IDs if provided
        target_org_ids = []
        if organization_ids:
            target_org_ids = [oid.strip() for oid in organization_ids.split(",")]

        # In production, this would query the database for real statistics
        # Mock comprehensive usage data
        mock_org_stats = OrganizationUsageStats(
            organization_id=UUID(tenant_context.effective_tenant_id),
            organization_name="Example School District",
            total_quota_bytes=5368709120,  # 5GB
            used_storage_bytes=2147483648,  # 2GB
            available_storage_bytes=3221225472,  # 3GB
            used_percentage=40.0,
            file_count=1250,
            active_file_count=1100,
            deleted_file_count=150,
            shared_file_count=320,
            user_count=85,
            last_activity_at=datetime.utcnow() - timedelta(hours=2),
            category_breakdown={
                "educational_content": 650,
                "student_submission": 400,
                "assessment": 120,
                "media_resource": 50,
                "administrative": 30
            },
            file_type_breakdown={
                "application/pdf": 500,
                "image/jpeg": 300,
                "image/png": 200,
                "video/mp4": 150,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": 100
            },
            daily_upload_bytes=104857600,  # 100MB
            weekly_upload_bytes=734003200,  # 700MB
            monthly_upload_bytes=3221225472,  # 3GB
            virus_scan_count=1250,
            quarantined_file_count=2,
            public_share_count=45,
            private_share_count=275,
            expired_share_count=18
        )

        global_stats = {
            "total_storage_allocated": 53687091200,  # 50GB
            "total_storage_used": 21474836480,  # 20GB
            "total_files": 12500,
            "total_organizations": 10,
            "average_usage_percentage": 42.5,
            "most_used_file_type": "application/pdf",
            "security_scans_today": 450,
            "threats_detected_today": 0
        }

        return StorageUsageResponse(
            organizations=[mock_org_stats],
            total_organizations=1,
            global_stats=global_stats,
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Error getting usage statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )


@router.get("/usage/{organization_id}/detailed")
async def get_detailed_organization_usage(
    organization_id: UUID,
    date_from: Optional[datetime] = Query(None, description="Start date for trends"),
    date_to: Optional[datetime] = Query(None, description="End date for trends"),
    include_user_breakdown: bool = Query(False, description="Include per-user breakdown"),
    user_tenant: tuple[User, TenantContext] = Depends(require_tenant_admin)
):
    """Get detailed usage statistics for a specific organization"""
    user, tenant_context = user_tenant

    try:
        # In production, this would query detailed database statistics
        # Mock detailed response
        detailed_stats = {
            "organization_id": str(organization_id),
            "usage_summary": {
                "current_usage_bytes": 2147483648,
                "quota_bytes": 5368709120,
                "usage_percentage": 40.0,
                "files_count": 1250,
                "users_count": 85
            },
            "daily_trends": [
                {
                    "date": (datetime.utcnow() - timedelta(days=i)).date(),
                    "uploads_bytes": 50000000 + (i * 1000000),
                    "downloads_count": 150 + (i * 5),
                    "files_added": 25 + i,
                    "files_deleted": 2 + (i // 2)
                }
                for i in range(30)
            ],
            "user_breakdown": [
                {
                    "user_id": f"user-{i}",
                    "user_name": f"User {i}",
                    "files_count": 15 + i,
                    "storage_used_bytes": 25000000 + (i * 1000000),
                    "last_upload": datetime.utcnow() - timedelta(days=i % 7)
                }
                for i in range(10)
            ] if include_user_breakdown else [],
            "category_trends": {
                "educational_content": {"files": 650, "bytes": 1000000000},
                "student_submission": {"files": 400, "bytes": 800000000},
                "assessment": {"files": 120, "bytes": 200000000},
                "media_resource": {"files": 50, "bytes": 100000000},
                "administrative": {"files": 30, "bytes": 47483648}
            },
            "security_summary": {
                "total_scans": 1250,
                "threats_found": 2,
                "quarantined_files": 2,
                "last_scan": datetime.utcnow() - timedelta(hours=1)
            }
        }

        return detailed_stats

    except Exception as e:
        logger.error(f"Error getting detailed usage for {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve detailed usage statistics"
        )


# === SECURITY SCANNING ENDPOINTS ===

@router.post("/scan", response_model=VirusScanResponse)
async def trigger_virus_scan(
    scan_request: VirusScanRequest,
    background_tasks: BackgroundTasks,
    user_tenant: tuple[User, TenantContext] = Depends(require_tenant_admin)
):
    """
    Trigger virus scanning operation.

    Scan types:
    - organization: Scan all files in an organization
    - file: Scan a specific file
    - all_files: Scan all files (super admin only)
    """
    user, tenant_context = user_tenant

    try:
        from uuid import uuid4

        scan_id = str(uuid4())
        started_at = datetime.utcnow()

        # Validate permissions
        if scan_request.target_type == "all_files" and not tenant_context.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin privileges required for global scan"
            )

        # Estimate scan scope
        if scan_request.target_type == "file":
            files_to_scan = 1
            estimated_completion = started_at + timedelta(minutes=2)
        elif scan_request.target_type == "organization":
            files_to_scan = 1250  # Mock organization file count
            estimated_completion = started_at + timedelta(hours=2)
        else:  # all_files
            files_to_scan = 12500  # Mock total file count
            estimated_completion = started_at + timedelta(hours=8)

        # Schedule scan task
        if scan_request.target_type == "file" and scan_request.file_id:
            background_tasks.add_task(
                virus_scan_file.delay,
                str(scan_request.file_id),
                tenant_context.effective_tenant_id,
                scan_request.force_rescan
            )
        else:
            # Schedule bulk scan (would be implemented as a separate task)
            logger.info(
                f"Bulk virus scan scheduled: scan_id={scan_id}, "
                f"target_type={scan_request.target_type}, "
                f"organization_id={scan_request.organization_id}, "
                f"priority={scan_request.scan_priority}"
            )

        return VirusScanResponse(
            scan_id=scan_id,
            target_type=scan_request.target_type,
            target_id=str(scan_request.organization_id or scan_request.file_id or "all"),
            status="queued",
            files_to_scan=files_to_scan,
            scan_priority=scan_request.scan_priority,
            started_at=started_at,
            estimated_completion=estimated_completion
        )

    except Exception as e:
        logger.error(f"Error triggering virus scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger virus scan"
        )


@router.get("/scan/{scan_id}/status")
async def get_virus_scan_status(
    scan_id: str,
    user_tenant: tuple[User, TenantContext] = Depends(require_tenant_admin)
):
    """Get status of a virus scan operation"""
    user, tenant_context = user_tenant

    # In production, this would query the scan status from database
    # Mock scan status
    return {
        "scan_id": scan_id,
        "target_type": "organization",
        "status": "in_progress",
        "files_to_scan": 1250,
        "files_scanned": 850,
        "progress_percentage": 68.0,
        "threats_found": 1,
        "quarantined_files": 1,
        "scan_priority": "normal",
        "started_at": datetime.utcnow() - timedelta(minutes=45),
        "estimated_completion": datetime.utcnow() + timedelta(minutes=25),
        "current_file": "document_analysis_report.pdf"
    }


# === CLEANUP OPERATIONS ===

@router.post("/cleanup", response_model=CleanupResponse)
async def trigger_cleanup_operation(
    cleanup_request: CleanupRequest,
    background_tasks: BackgroundTasks,
    user_tenant: tuple[User, TenantContext] = Depends(require_tenant_admin)
):
    """
    Trigger storage cleanup operation.

    Cleanup types:
    - expired_files: Remove files past retention date
    - deleted_files: Permanently delete soft-deleted files
    - orphaned_shares: Remove expired share links
    - temp_files: Clean temporary upload files
    - all: Perform all cleanup operations
    """
    user, tenant_context = user_tenant

    try:
        from uuid import uuid4

        cleanup_id = str(uuid4())
        started_at = datetime.utcnow()

        # Validate organization access
        target_org_id = cleanup_request.organization_id or tenant_context.effective_tenant_id

        if cleanup_request.cleanup_type in ["deleted_files", "all"] and not cleanup_request.force_cleanup:
            if cleanup_request.older_than_days < 30:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Permanent deletion requires files to be older than 30 days or force_cleanup=true"
                )

        # Schedule cleanup task
        background_tasks.add_task(
            cleanup_expired_files.delay,
            target_org_id,
            cleanup_request.cleanup_type,
            cleanup_request.older_than_days,
            cleanup_request.dry_run
        )

        logger.info(
            f"Cleanup operation scheduled: cleanup_id={cleanup_id}, "
            f"type={cleanup_request.cleanup_type}, "
            f"organization_id={target_org_id}, "
            f"older_than_days={cleanup_request.older_than_days}, "
            f"dry_run={cleanup_request.dry_run}"
        )

        return CleanupResponse(
            cleanup_id=cleanup_id,
            cleanup_type=cleanup_request.cleanup_type,
            target_organization=str(target_org_id),
            status="queued",
            dry_run=cleanup_request.dry_run,
            older_than_days=cleanup_request.older_than_days,
            started_at=started_at
        )

    except Exception as e:
        logger.error(f"Error triggering cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger cleanup operation"
        )


@router.get("/cleanup/{cleanup_id}/status")
async def get_cleanup_status(
    cleanup_id: str,
    user_tenant: tuple[User, TenantContext] = Depends(require_tenant_admin)
):
    """Get status of a cleanup operation"""
    user, tenant_context = user_tenant

    # In production, this would query the cleanup status from database
    # Mock cleanup status
    return {
        "cleanup_id": cleanup_id,
        "cleanup_type": "expired_files",
        "status": "completed",
        "dry_run": False,
        "older_than_days": 30,
        "files_processed": 156,
        "files_deleted": 45,
        "space_freed_bytes": 524288000,  # 500MB
        "errors_encountered": 2,
        "started_at": datetime.utcnow() - timedelta(minutes=15),
        "completed_at": datetime.utcnow() - timedelta(minutes=2),
        "summary": "Cleanup completed successfully. 45 expired files removed, 500MB freed."
    }


# === QUOTA MANAGEMENT ===

@router.patch("/quota", response_model=QuotaUpdateResponse)
async def update_organization_quota(
    quota_request: QuotaUpdateRequest,
    background_tasks: BackgroundTasks,
    user_tenant: tuple[User, TenantContext] = Depends(require_tenant_admin)
):
    """
    Update storage quota for an organization.

    Allows administrators to:
    - Increase or decrease storage quotas
    - Adjust file count limits
    - Set file size limits by type
    - Configure alert thresholds
    """
    user, tenant_context = user_tenant

    try:
        # Validate organization access
        if not tenant_context.is_super_admin:
            # Non-super admins can only modify their own organization
            if str(quota_request.organization_id) != tenant_context.effective_tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot modify quota for other organizations"
                )

        # In production, this would query and update the StorageQuota table
        # Mock current quota
        previous_quota = {
            "total_quota_bytes": 5368709120,  # 5GB
            "max_files": 10000,
            "max_file_size_mb": 100,
            "max_video_size_mb": 500,
            "max_image_size_mb": 50,
            "max_document_size_mb": 100,
            "warning_threshold_percent": 80,
            "critical_threshold_percent": 95
        }

        # Apply updates
        new_quota = previous_quota.copy()
        if quota_request.total_quota_bytes:
            new_quota["total_quota_bytes"] = quota_request.total_quota_bytes
        if quota_request.max_files:
            new_quota["max_files"] = quota_request.max_files
        if quota_request.max_file_size_mb:
            new_quota["max_file_size_mb"] = quota_request.max_file_size_mb
        if quota_request.max_video_size_mb:
            new_quota["max_video_size_mb"] = quota_request.max_video_size_mb
        if quota_request.max_image_size_mb:
            new_quota["max_image_size_mb"] = quota_request.max_image_size_mb
        if quota_request.max_document_size_mb:
            new_quota["max_document_size_mb"] = quota_request.max_document_size_mb
        if quota_request.warning_threshold_percent:
            new_quota["warning_threshold_percent"] = quota_request.warning_threshold_percent
        if quota_request.critical_threshold_percent:
            new_quota["critical_threshold_percent"] = quota_request.critical_threshold_percent

        # Log quota change
        logger.info(
            f"Quota updated: organization_id={quota_request.organization_id}, "
            f"updated_by={user.id}, reason={quota_request.reason}, "
            f"changes={new_quota}"
        )

        # Recalculate usage and send alerts if necessary
        background_tasks.add_task(
            calculate_storage_usage.delay,
            str(quota_request.organization_id)
        )

        return QuotaUpdateResponse(
            organization_id=quota_request.organization_id,
            previous_quota=previous_quota,
            new_quota=new_quota,
            updated_by=user.id,
            updated_at=datetime.utcnow(),
            reason=quota_request.reason
        )

    except Exception as e:
        logger.error(f"Error updating quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization quota"
        )


@router.get("/quota/{organization_id}")
async def get_organization_quota_details(
    organization_id: UUID,
    include_history: bool = Query(False, description="Include quota change history"),
    user_tenant: tuple[User, TenantContext] = Depends(require_tenant_admin)
):
    """Get detailed quota information for an organization"""
    user, tenant_context = user_tenant

    try:
        # Validate organization access
        if not tenant_context.is_super_admin:
            if str(organization_id) != tenant_context.effective_tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot access quota for other organizations"
                )

        # In production, this would query the StorageQuota table
        quota_details = {
            "organization_id": str(organization_id),
            "current_quota": {
                "total_quota_bytes": 5368709120,
                "used_storage_bytes": 2147483648,
                "available_storage_bytes": 3221225472,
                "used_percentage": 40.0,
                "max_files": 10000,
                "current_file_count": 1250,
                "max_file_size_mb": 100,
                "max_video_size_mb": 500,
                "max_image_size_mb": 50,
                "max_document_size_mb": 100,
                "warning_threshold_percent": 80,
                "critical_threshold_percent": 95,
                "last_calculated_at": datetime.utcnow()
            },
            "alerts": {
                "is_warning_reached": False,
                "is_critical_reached": False,
                "last_warning_sent": None,
                "next_alert_check": datetime.utcnow() + timedelta(hours=1)
            },
            "quota_history": [
                {
                    "change_date": datetime.utcnow() - timedelta(days=30),
                    "changed_by": "admin-user-id",
                    "previous_quota": 1073741824,  # 1GB
                    "new_quota": 5368709120,  # 5GB
                    "reason": "Organization growth - increased user count"
                },
                {
                    "change_date": datetime.utcnow() - timedelta(days=60),
                    "changed_by": "system",
                    "previous_quota": 536870912,  # 512MB
                    "new_quota": 1073741824,  # 1GB
                    "reason": "Automatic upgrade based on usage patterns"
                }
            ] if include_history else []
        }

        return quota_details

    except Exception as e:
        logger.error(f"Error getting quota details for {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quota details"
        )