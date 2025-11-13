"""
Tenant Storage Manager for ToolBoxAI Educational Platform

Manages organization-specific storage buckets, quota enforcement,
usage tracking, and storage analytics with multi-tenant isolation.

Author: ToolBoxAI Team
Created: 2025-01-27
Version: 1.0.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from storage3.utils import StorageException

from supabase import Client

logger = logging.getLogger(__name__)


@dataclass
class StorageUsage:
    """Storage usage statistics"""

    organization_id: str
    total_files: int = 0
    total_size_bytes: int = 0
    used_quota_percentage: float = 0.0
    files_by_category: dict[str, int] = field(default_factory=dict)
    size_by_category: dict[str, int] = field(default_factory=dict)
    largest_files: list[dict[str, Any]] = field(default_factory=list)
    oldest_files: list[dict[str, Any]] = field(default_factory=list)
    recent_activity: list[dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_size_mb(self) -> float:
        """Get total size in MB"""
        return self.total_size_bytes / (1024 * 1024)

    @property
    def total_size_gb(self) -> float:
        """Get total size in GB"""
        return self.total_size_bytes / (1024 * 1024 * 1024)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "organization_id": self.organization_id,
            "total_files": self.total_files,
            "total_size_bytes": self.total_size_bytes,
            "total_size_mb": self.total_size_mb,
            "total_size_gb": self.total_size_gb,
            "used_quota_percentage": self.used_quota_percentage,
            "files_by_category": self.files_by_category,
            "size_by_category": self.size_by_category,
            "largest_files": self.largest_files,
            "oldest_files": self.oldest_files,
            "recent_activity": self.recent_activity,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class QuotaAlert:
    """Storage quota alert"""

    organization_id: str
    alert_type: str  # warning, critical, exceeded
    current_usage: int
    quota_limit: int
    percentage_used: float
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "organization_id": self.organization_id,
            "alert_type": self.alert_type,
            "current_usage": current_usage,
            "quota_limit": self.quota_limit,
            "percentage_used": self.percentage_used,
            "triggered_at": self.triggered_at.isoformat(),
            "message": self.message,
        }


class TenantStorageManager:
    """
    Multi-tenant storage management with quota enforcement and analytics.

    Features:
    - Organization-specific bucket management
    - Storage quota enforcement
    - Usage tracking and analytics
    - Automated cleanup policies
    - Alert management
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize tenant storage manager.

        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client
        self.bucket_prefix = "org"
        self.default_quota_gb = 10  # 10GB default quota
        self.warning_threshold = 80  # 80% usage warning
        self.critical_threshold = 95  # 95% usage critical

        # Cache for bucket existence and quota info
        self._bucket_cache: dict[str, bool] = {}
        self._quota_cache: dict[str, dict[str, Any]] = {}
        self._usage_cache: dict[str, StorageUsage] = {}

        logger.info("TenantStorageManager initialized")

    async def get_or_create_bucket(self, organization_id: str) -> str:
        """
        Get or create organization-specific storage bucket.

        Args:
            organization_id: Organization identifier

        Returns:
            str: Bucket name

        Raises:
            StorageException: If bucket operations fail
        """
        if not organization_id:
            raise ValueError("Organization ID is required")

        bucket_name = f"{self.bucket_prefix}_{organization_id.replace('-', '_')}"

        # Check cache first
        if bucket_name in self._bucket_cache:
            return bucket_name

        try:
            # Check if bucket exists
            buckets = self.supabase.storage.list_buckets()
            existing_buckets = {bucket["name"] for bucket in buckets}

            if bucket_name not in existing_buckets:
                # Create new bucket
                await self._create_organization_bucket(bucket_name, organization_id)

            # Cache the result
            self._bucket_cache[bucket_name] = True

            logger.info(f"Bucket ready for organization {organization_id}: {bucket_name}")
            return bucket_name

        except Exception as e:
            logger.error(f"Bucket management failed for org {organization_id}: {e}")
            raise StorageException(f"Bucket management failed: {str(e)}")

    async def check_quota(self, organization_id: str, additional_size: int = 0) -> bool:
        """
        Check if organization has available quota for file upload.

        Args:
            organization_id: Organization identifier
            additional_size: Additional size to check (in bytes)

        Returns:
            bool: True if quota available, False otherwise
        """
        try:
            # Get current quota info
            quota_info = await self._get_quota_info(organization_id)

            current_usage = quota_info.get("used_storage", 0)
            quota_limit = quota_info.get("total_quota", self.default_quota_gb * 1024 * 1024 * 1024)

            # Check if additional size would exceed quota
            projected_usage = current_usage + additional_size

            if projected_usage > quota_limit:
                logger.warning(
                    f"Quota would be exceeded for org {organization_id}: "
                    f"{projected_usage} > {quota_limit}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Quota check failed for org {organization_id}: {e}")
            # Default to allowing upload if quota check fails
            return True

    async def get_storage_usage(
        self, organization_id: str, force_refresh: bool = False
    ) -> StorageUsage:
        """
        Get comprehensive storage usage statistics.

        Args:
            organization_id: Organization identifier
            force_refresh: Force refresh of cached data

        Returns:
            StorageUsage: Usage statistics
        """
        # Check cache first
        if not force_refresh and organization_id in self._usage_cache:
            cached_usage = self._usage_cache[organization_id]
            # Return cached data if less than 5 minutes old
            if (datetime.utcnow() - cached_usage.last_updated).seconds < 300:
                return cached_usage

        try:
            usage = StorageUsage(organization_id=organization_id)

            # Get files from database
            files_data = await self._get_organization_files(organization_id)

            # Calculate totals
            usage.total_files = len(files_data)
            usage.total_size_bytes = sum(file_data.get("file_size", 0) for file_data in files_data)

            # Group by category
            for file_data in files_data:
                category = file_data.get("category", "unknown")
                file_size = file_data.get("file_size", 0)

                usage.files_by_category[category] = usage.files_by_category.get(category, 0) + 1
                usage.size_by_category[category] = (
                    usage.size_by_category.get(category, 0) + file_size
                )

            # Get quota info
            quota_info = await self._get_quota_info(organization_id)
            quota_limit = quota_info.get("total_quota", self.default_quota_gb * 1024 * 1024 * 1024)

            if quota_limit > 0:
                usage.used_quota_percentage = (usage.total_size_bytes / quota_limit) * 100

            # Get largest files (top 10)
            sorted_files = sorted(files_data, key=lambda x: x.get("file_size", 0), reverse=True)
            usage.largest_files = [
                {
                    "id": file_data["id"],
                    "filename": file_data.get("filename", "unknown"),
                    "size": file_data.get("file_size", 0),
                    "category": file_data.get("category", "unknown"),
                    "created_at": file_data.get("created_at"),
                }
                for file_data in sorted_files[:10]
            ]

            # Get oldest files (top 10)
            sorted_by_date = sorted(
                files_data, key=lambda x: x.get("created_at", ""), reverse=False
            )
            usage.oldest_files = [
                {
                    "id": file_data["id"],
                    "filename": file_data.get("filename", "unknown"),
                    "age_days": self._calculate_age_days(file_data.get("created_at")),
                    "category": file_data.get("category", "unknown"),
                    "size": file_data.get("file_size", 0),
                }
                for file_data in sorted_by_date[:10]
            ]

            # Get recent activity (last 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_files = [
                file_data
                for file_data in files_data
                if self._parse_date(file_data.get("created_at")) > recent_cutoff
            ]

            usage.recent_activity = [
                {
                    "action": "upload",
                    "filename": file_data.get("filename", "unknown"),
                    "size": file_data.get("file_size", 0),
                    "date": file_data.get("created_at"),
                }
                for file_data in recent_files[-10:]  # Last 10 recent activities
            ]

            # Cache the result
            self._usage_cache[organization_id] = usage

            logger.info(
                f"Storage usage calculated for org {organization_id}: {usage.total_size_mb:.2f}MB"
            )
            return usage

        except Exception as e:
            logger.error(f"Storage usage calculation failed for org {organization_id}: {e}")
            # Return empty usage on error
            return StorageUsage(organization_id=organization_id)

    async def update_quota(
        self, organization_id: str, new_quota_gb: float, updated_by: str | None = None
    ) -> bool:
        """
        Update storage quota for organization.

        Args:
            organization_id: Organization identifier
            new_quota_gb: New quota in GB
            updated_by: User who updated the quota

        Returns:
            bool: True if update successful
        """
        try:
            new_quota_bytes = int(new_quota_gb * 1024 * 1024 * 1024)

            # Update quota in database
            quota_data = {
                "organization_id": organization_id,
                "total_quota": new_quota_bytes,
                "updated_at": datetime.utcnow().isoformat(),
                "updated_by": updated_by,
            }

            success = await self._update_quota_record(organization_id, quota_data)

            if success:
                # Clear cache
                self._quota_cache.pop(organization_id, None)
                self._usage_cache.pop(organization_id, None)

                logger.info(f"Quota updated for org {organization_id}: {new_quota_gb}GB")

            return success

        except Exception as e:
            logger.error(f"Quota update failed for org {organization_id}: {e}")
            return False

    async def check_quota_alerts(self, organization_id: str) -> list[QuotaAlert]:
        """
        Check for quota alerts and return any triggered alerts.

        Args:
            organization_id: Organization identifier

        Returns:
            List[QuotaAlert]: List of triggered alerts
        """
        alerts = []

        try:
            usage = await self.get_storage_usage(organization_id)
            quota_info = await self._get_quota_info(organization_id)

            quota_limit = quota_info.get("total_quota", self.default_quota_gb * 1024 * 1024 * 1024)
            percentage_used = usage.used_quota_percentage

            # Check for alerts
            if percentage_used >= 100:
                alerts.append(
                    QuotaAlert(
                        organization_id=organization_id,
                        alert_type="exceeded",
                        current_usage=usage.total_size_bytes,
                        quota_limit=quota_limit,
                        percentage_used=percentage_used,
                        message=f"Storage quota exceeded: {percentage_used:.1f}%",
                    )
                )
            elif percentage_used >= self.critical_threshold:
                alerts.append(
                    QuotaAlert(
                        organization_id=organization_id,
                        alert_type="critical",
                        current_usage=usage.total_size_bytes,
                        quota_limit=quota_limit,
                        percentage_used=percentage_used,
                        message=f"Critical storage usage: {percentage_used:.1f}%",
                    )
                )
            elif percentage_used >= self.warning_threshold:
                alerts.append(
                    QuotaAlert(
                        organization_id=organization_id,
                        alert_type="warning",
                        current_usage=usage.total_size_bytes,
                        quota_limit=quota_limit,
                        percentage_used=percentage_used,
                        message=f"Storage usage warning: {percentage_used:.1f}%",
                    )
                )

            return alerts

        except Exception as e:
            logger.error(f"Quota alert check failed for org {organization_id}: {e}")
            return []

    async def cleanup_old_files(
        self, organization_id: str, max_age_days: int = 365, categories: list[str] | None = None
    ) -> int:
        """
        Clean up old files based on retention policies.

        Args:
            organization_id: Organization identifier
            max_age_days: Maximum age in days before cleanup
            categories: File categories to clean up (None for all)

        Returns:
            int: Number of files cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
            cleanup_count = 0

            # Get old files
            files_data = await self._get_organization_files(organization_id)

            old_files = [
                file_data
                for file_data in files_data
                if (
                    self._parse_date(file_data.get("created_at", "")) < cutoff_date
                    and (categories is None or file_data.get("category") in categories)
                )
            ]

            # Clean up files
            for file_data in old_files:
                try:
                    file_id = UUID(file_data["id"])
                    if await self._delete_old_file(file_id, organization_id):
                        cleanup_count += 1
                except Exception as e:
                    logger.warning(f"Failed to clean up file {file_data.get('id')}: {e}")

            if cleanup_count > 0:
                # Clear usage cache to reflect changes
                self._usage_cache.pop(organization_id, None)

                logger.info(f"Cleaned up {cleanup_count} old files for org {organization_id}")

            return cleanup_count

        except Exception as e:
            logger.error(f"File cleanup failed for org {organization_id}: {e}")
            return 0

    async def get_storage_analytics(self, organization_id: str, days: int = 30) -> dict[str, Any]:
        """
        Get storage analytics for the specified period.

        Args:
            organization_id: Organization identifier
            days: Number of days to analyze

        Returns:
            Dict[str, Any]: Analytics data
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get usage data
            usage = await self.get_storage_usage(organization_id)

            # Get historical data (would be from a time-series database in production)
            analytics = {
                "organization_id": organization_id,
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "current_usage": usage.to_dict(),
                "trends": {
                    "daily_uploads": await self._get_daily_upload_trends(organization_id, days),
                    "category_growth": await self._get_category_growth(organization_id, days),
                    "size_trends": await self._get_size_trends(organization_id, days),
                },
                "recommendations": await self._generate_recommendations(usage),
            }

            return analytics

        except Exception as e:
            logger.error(f"Storage analytics failed for org {organization_id}: {e}")
            return {"error": str(e)}

    # Private helper methods

    async def _create_organization_bucket(self, bucket_name: str, organization_id: str) -> None:
        """Create a new organization bucket with proper policies"""
        try:
            # Create bucket
            bucket_response = self.supabase.storage.create_bucket(
                bucket_name,
                {
                    "public": False,
                    "allowed_mime_types": [
                        "image/*",
                        "video/*",
                        "audio/*",
                        "application/pdf",
                        "application/msword",
                        "application/vnd.openxmlformats-officedocument.*",
                        "text/*",
                    ],
                    "file_size_limit": 100 * 1024 * 1024,  # 100MB per file
                },
            )

            # Set up bucket policies (RLS)
            await self._setup_bucket_policies(bucket_name, organization_id)

            logger.info(f"Created bucket {bucket_name} for organization {organization_id}")

        except StorageException as e:
            if "already exists" in str(e).lower():
                logger.info(f"Bucket {bucket_name} already exists")
            else:
                raise

    async def _setup_bucket_policies(self, bucket_name: str, organization_id: str) -> None:
        """Set up RLS policies for organization bucket"""
        # This would set up Row Level Security policies in Supabase
        # to ensure organization isolation
        logger.info(f"Setting up policies for bucket {bucket_name}")

    async def _get_quota_info(self, organization_id: str) -> dict[str, Any]:
        """Get quota information from database"""
        # Check cache first
        if organization_id in self._quota_cache:
            return self._quota_cache[organization_id]

        # This would query your StorageQuota model
        quota_info = {
            "organization_id": organization_id,
            "total_quota": self.default_quota_gb * 1024 * 1024 * 1024,  # Default 10GB
            "used_storage": 0,
            "file_count": 0,
        }

        # Cache the result
        self._quota_cache[organization_id] = quota_info
        return quota_info

    async def _get_organization_files(self, organization_id: str) -> list[dict[str, Any]]:
        """Get all files for organization from database"""
        # This would query your File model with organization filter
        # For now, return mock data
        return []

    async def _update_quota_record(self, organization_id: str, quota_data: dict[str, Any]) -> bool:
        """Update quota record in database"""
        # This would update your StorageQuota model
        return True

    async def _delete_old_file(self, file_id: UUID, organization_id: str) -> bool:
        """Delete old file from storage and database"""
        # This would delete file from Supabase Storage and update database
        return True

    async def _get_daily_upload_trends(
        self, organization_id: str, days: int
    ) -> list[dict[str, Any]]:
        """Get daily upload trends"""
        # This would aggregate daily upload data
        return []

    async def _get_category_growth(self, organization_id: str, days: int) -> dict[str, Any]:
        """Get category growth trends"""
        # This would analyze growth by file category
        return {}

    async def _get_size_trends(self, organization_id: str, days: int) -> list[dict[str, Any]]:
        """Get storage size trends"""
        # This would track storage size over time
        return []

    async def _generate_recommendations(self, usage: StorageUsage) -> list[str]:
        """Generate storage optimization recommendations"""
        recommendations = []

        # Check for cleanup opportunities
        if usage.used_quota_percentage > 80:
            recommendations.append("Consider cleaning up old files to free up space")

        # Check for large files
        if usage.largest_files:
            large_file_count = len([f for f in usage.largest_files if f["size"] > 50 * 1024 * 1024])
            if large_file_count > 0:
                recommendations.append(
                    f"You have {large_file_count} files larger than 50MB that could be optimized"
                )

        # Check category distribution
        if "temporary" in usage.files_by_category and usage.files_by_category["temporary"] > 10:
            recommendations.append("Clean up temporary files to optimize storage")

        return recommendations

    def _calculate_age_days(self, date_str: str | None) -> int:
        """Calculate age in days from date string"""
        if not date_str:
            return 0

        try:
            file_date = self._parse_date(date_str)
            return (datetime.utcnow() - file_date).days
        except Exception:
            return 0

    def _parse_date(self, date_str: str | None) -> datetime:
        """Parse date string to datetime"""
        if not date_str:
            return datetime.utcnow()

        try:
            # Handle ISO format
            if "T" in date_str:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                return datetime.fromisoformat(date_str)
        except Exception:
            return datetime.utcnow()
