"""
Abstract Storage Service for ToolBoxAI Educational Platform

Provides the base interface and common functionality for file storage
operations with multi-tenant support, progress tracking, and security.

Author: ToolBoxAI Team
Created: 2025-01-27
Version: 1.0.0
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, BinaryIO
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class UploadStatus(str, Enum):
    """Upload status enumeration"""

    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadPermission(str, Enum):
    """Download permission levels"""

    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    ORGANIZATION = "organization"
    SPECIFIC_USERS = "specific_users"
    PRIVATE = "private"


@dataclass
class UploadProgress:
    """Progress tracking for file uploads"""

    upload_id: str
    status: UploadStatus
    bytes_uploaded: int = 0
    total_bytes: int = 0
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def progress_percentage(self) -> float:
        """Calculate upload progress percentage"""
        if self.total_bytes == 0:
            return 0.0
        return min(100.0, (self.bytes_uploaded / self.total_bytes) * 100)

    @property
    def is_complete(self) -> bool:
        """Check if upload is complete"""
        return self.status == UploadStatus.COMPLETED

    @property
    def has_failed(self) -> bool:
        """Check if upload has failed"""
        return self.status == UploadStatus.FAILED


class UploadOptions(BaseModel):
    """Options for file upload operations"""

    file_category: str = "media_resource"
    title: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Security options
    virus_scan: bool = True
    content_validation: bool = True
    require_consent: bool = False

    # Processing options
    generate_thumbnails: bool = True
    optimize_images: bool = True
    extract_metadata: bool = True

    # Access control
    download_permission: DownloadPermission = DownloadPermission.ORGANIZATION
    allowed_user_ids: list[str] = Field(default_factory=list)

    # Retention
    retention_days: int | None = None
    auto_delete_after_days: int | None = None


@dataclass
class UploadResult:
    """Result of a file upload operation"""

    file_id: UUID
    upload_id: str
    storage_path: str
    cdn_url: str | None = None
    thumbnail_url: str | None = None
    file_size: int = 0
    mime_type: str = ""
    checksum: str = ""
    status: UploadStatus = UploadStatus.COMPLETED
    warnings: list[str] = field(default_factory=list)
    processing_metadata: dict[str, Any] = field(default_factory=dict)


class DownloadOptions(BaseModel):
    """Options for file download operations"""

    include_metadata: bool = False
    track_access: bool = True
    signed_url_expires_in: int = 3600  # 1 hour default
    transformation: dict[str, Any] | None = None  # Image transformations


@dataclass
class DownloadResult:
    """Result of a file download operation"""

    file_id: UUID
    file_url: str
    expires_at: datetime | None = None
    content_type: str = ""
    content_length: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class ListOptions(BaseModel):
    """Options for listing files"""

    prefix: str | None = None
    limit: int = 100
    offset: int = 0
    file_types: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    include_metadata: bool = False
    sort_by: str = "created_at"
    sort_order: str = "desc"  # "asc" or "desc"


@dataclass
class FileInfo:
    """Information about a stored file"""

    file_id: UUID
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    storage_path: str
    cdn_url: str | None = None
    thumbnail_url: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


class StorageService(ABC):
    """
    Abstract base class for file storage services.

    Provides the interface for file upload, download, deletion, and management
    operations with multi-tenant support and security features.
    """

    def __init__(self, organization_id: str | None = None, user_id: str | None = None, **kwargs):
        """
        Initialize storage service.

        Args:
            organization_id: Current organization ID for tenant isolation
            user_id: Current user ID for access control
            **kwargs: Additional configuration options
        """
        self.organization_id = organization_id
        self.user_id = user_id
        self.config = kwargs
        self._upload_progress: dict[str, UploadProgress] = {}

        logger.info(
            f"Storage service initialized for organization: {organization_id}, " f"user: {user_id}"
        )

    # Abstract methods that must be implemented by providers

    @abstractmethod
    async def upload_file(
        self,
        file_data: bytes | BinaryIO,
        filename: str,
        options: UploadOptions | None = None,
    ) -> UploadResult:
        """
        Upload a file to storage.

        Args:
            file_data: File content as bytes or file-like object
            filename: Original filename
            options: Upload options and metadata

        Returns:
            UploadResult: Result of upload operation

        Raises:
            StorageError: If upload fails
        """
        pass

    @abstractmethod
    async def upload_file_multipart(
        self,
        file_stream: AsyncGenerator[bytes, None],
        filename: str,
        total_size: int,
        options: UploadOptions | None = None,
    ) -> AsyncGenerator[UploadProgress, UploadResult]:
        """
        Upload a large file using multipart upload with progress tracking.

        Args:
            file_stream: Async generator yielding file chunks
            filename: Original filename
            total_size: Total file size in bytes
            options: Upload options and metadata

        Yields:
            UploadProgress: Progress updates during upload

        Returns:
            UploadResult: Final upload result

        Raises:
            StorageError: If upload fails
        """
        pass

    @abstractmethod
    async def download_file(
        self, file_id: UUID, options: DownloadOptions | None = None
    ) -> DownloadResult:
        """
        Download a file from storage.

        Args:
            file_id: File identifier
            options: Download options

        Returns:
            DownloadResult: Download information and signed URL

        Raises:
            StorageError: If file not found or access denied
        """
        pass

    @abstractmethod
    async def get_file_stream(
        self, file_id: UUID, chunk_size: int = 8192
    ) -> AsyncGenerator[bytes, None]:
        """
        Get file content as a stream.

        Args:
            file_id: File identifier
            chunk_size: Size of chunks to yield

        Yields:
            bytes: File content chunks

        Raises:
            StorageError: If file not found or access denied
        """
        pass

    @abstractmethod
    async def delete_file(self, file_id: UUID, permanent: bool = False) -> bool:
        """
        Delete a file from storage.

        Args:
            file_id: File identifier
            permanent: Whether to permanently delete (vs soft delete)

        Returns:
            bool: True if deletion successful

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    async def list_files(self, options: ListOptions | None = None) -> list[FileInfo]:
        """
        List files in storage.

        Args:
            options: Listing options and filters

        Returns:
            List[FileInfo]: List of file information

        Raises:
            StorageError: If listing fails
        """
        pass

    @abstractmethod
    async def get_file_info(self, file_id: UUID) -> FileInfo | None:
        """
        Get information about a specific file.

        Args:
            file_id: File identifier

        Returns:
            FileInfo: File information or None if not found

        Raises:
            StorageError: If operation fails
        """
        pass

    @abstractmethod
    async def generate_signed_url(
        self, file_id: UUID, expires_in: int = 3600, permission: str = "read"
    ) -> str:
        """
        Generate a signed URL for file access.

        Args:
            file_id: File identifier
            expires_in: URL expiration time in seconds
            permission: Access permission ("read", "write")

        Returns:
            str: Signed URL

        Raises:
            StorageError: If URL generation fails
        """
        pass

    @abstractmethod
    async def copy_file(
        self, source_file_id: UUID, destination_path: str, options: UploadOptions | None = None
    ) -> UploadResult:
        """
        Copy a file to a new location.

        Args:
            source_file_id: Source file identifier
            destination_path: Destination path
            options: Copy options

        Returns:
            UploadResult: Result of copy operation

        Raises:
            StorageError: If copy fails
        """
        pass

    @abstractmethod
    async def move_file(self, file_id: UUID, new_path: str) -> bool:
        """
        Move a file to a new location.

        Args:
            file_id: File identifier
            new_path: New file path

        Returns:
            bool: True if move successful

        Raises:
            StorageError: If move fails
        """
        pass

    # Common utility methods

    def get_upload_progress(self, upload_id: str) -> UploadProgress | None:
        """
        Get upload progress for a specific upload.

        Args:
            upload_id: Upload identifier

        Returns:
            UploadProgress: Progress information or None if not found
        """
        return self._upload_progress.get(upload_id)

    def _update_upload_progress(
        self,
        upload_id: str,
        status: UploadStatus,
        bytes_uploaded: int = 0,
        total_bytes: int = 0,
        error_message: str | None = None,
    ) -> UploadProgress:
        """
        Update upload progress tracking.

        Args:
            upload_id: Upload identifier
            status: Current upload status
            bytes_uploaded: Number of bytes uploaded
            total_bytes: Total file size
            error_message: Error message if failed

        Returns:
            UploadProgress: Updated progress object
        """
        if upload_id not in self._upload_progress:
            self._upload_progress[upload_id] = UploadProgress(
                upload_id=upload_id, status=status, total_bytes=total_bytes
            )

        progress = self._upload_progress[upload_id]
        progress.status = status
        progress.bytes_uploaded = bytes_uploaded
        progress.total_bytes = max(progress.total_bytes, total_bytes)
        progress.error_message = error_message
        progress.updated_at = datetime.utcnow()

        return progress

    def _generate_storage_path(
        self, filename: str, file_category: str = "media_resource", include_timestamp: bool = True
    ) -> str:
        """
        Generate a storage path for a file.

        Args:
            filename: Original filename
            file_category: File category
            include_timestamp: Whether to include timestamp in path

        Returns:
            str: Generated storage path
        """
        # Clean filename
        safe_filename = Path(filename).name
        file_stem = Path(safe_filename).stem
        file_suffix = Path(safe_filename).suffix

        # Generate unique filename
        if include_timestamp:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid4())[:8]
            new_filename = f"{file_stem}_{timestamp}_{unique_id}{file_suffix}"
        else:
            unique_id = str(uuid4())[:8]
            new_filename = f"{file_stem}_{unique_id}{file_suffix}"

        # Build path with organization isolation
        path_parts = []

        if self.organization_id:
            path_parts.append(f"org_{self.organization_id}")

        path_parts.extend([file_category, datetime.utcnow().strftime("%Y/%m"), new_filename])

        return "/".join(path_parts)

    def _calculate_checksum(self, data: bytes) -> str:
        """
        Calculate SHA256 checksum of file data.

        Args:
            data: File data

        Returns:
            str: SHA256 checksum
        """
        import hashlib

        return hashlib.sha256(data).hexdigest()

    async def _validate_tenant_access(self, file_id: UUID) -> bool:
        """
        Validate that current tenant can access the specified file.

        Args:
            file_id: File identifier

        Returns:
            bool: True if access is allowed
        """
        # This would typically check database for file ownership
        # For now, assume access is allowed if organization_id is set
        return self.organization_id is not None

    def set_tenant_context(
        self, organization_id: str | None = None, user_id: str | None = None
    ) -> None:
        """
        Update tenant context for the storage service.

        Args:
            organization_id: Organization ID
            user_id: User ID
        """
        self.organization_id = organization_id
        self.user_id = user_id

        logger.debug(
            f"Storage service tenant context updated: "
            f"org_id={organization_id}, user_id={user_id}"
        )


class StorageError(Exception):
    """Base exception for storage operations"""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class TenantIsolationError(StorageError):
    """Error when tenant isolation is violated"""

    pass


class QuotaExceededError(StorageError):
    """Error when storage quota is exceeded"""

    pass


class FileNotFoundError(StorageError):
    """Error when file is not found"""

    pass


class AccessDeniedError(StorageError):
    """Error when access is denied"""

    pass


class ValidationError(StorageError):
    """Error during file validation"""

    pass


class VirusScanError(StorageError):
    """Error during virus scanning"""

    pass
