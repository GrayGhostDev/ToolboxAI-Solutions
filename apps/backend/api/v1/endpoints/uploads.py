"""
Upload API Endpoints for ToolBoxAI Educational Platform

Provides comprehensive file upload operations including single file uploads,
multipart uploads for large files, and upload management with 2025 FastAPI standards.

Features:
- Single file upload with validation
- Multipart upload for large files (>100MB)
- Upload progress tracking via WebSocket
- Upload cancellation and retry
- Quota enforcement and validation
- Multi-tenant isolation

Author: ToolBoxAI Team
Created: 2025-10-02
Version: 1.0.0
Standards: Python 3.12, FastAPI async, Pydantic v2
"""

import asyncio
import logging
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.api.auth.auth import get_current_user
from apps.backend.core.deps import get_async_db
from apps.backend.middleware.tenant import get_tenant_context, TenantContext
from apps.backend.models.schemas import User
from apps.backend.services.storage.storage_service import (
    StorageService,
    UploadOptions,
    UploadResult,
    UploadStatus,
    DownloadPermission,
    QuotaExceededError,
    ValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/uploads",
    tags=["uploads"],
    responses={404: {"description": "Upload not found"}},
)


# === Pydantic v2 Models ===

class SingleFileUploadRequest(BaseModel):
    """Request model for single file upload with Pydantic v2"""

    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: str = Field(default="media_resource")
    tags: list[str] = Field(default_factory=list)
    virus_scan: bool = Field(default=True)
    generate_thumbnails: bool = Field(default=True)
    optimize_images: bool = Field(default=True)
    download_permission: DownloadPermission = Field(default=DownloadPermission.ORGANIZATION)
    retention_days: Optional[int] = Field(None, ge=1, le=3650)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category field"""
        valid_categories = [
            "educational_content",
            "student_submission",
            "assessment",
            "administrative",
            "media_resource",
            "temporary",
            "avatar",
            "report",
        ]
        if v not in valid_categories:
            raise ValueError(f"Invalid category. Must be one of: {valid_categories}")
        return v


class FileUploadResponse(BaseModel):
    """Response model for file upload"""

    model_config = ConfigDict(from_attributes=True)

    file_id: UUID
    upload_id: str
    filename: str
    file_size: int
    mime_type: str
    storage_path: str
    cdn_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: UploadStatus
    created_at: datetime
    warnings: list[str] = Field(default_factory=list)


class MultipartUploadInitRequest(BaseModel):
    """Request to initialize multipart upload"""

    model_config = ConfigDict(from_attributes=True)

    filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0)
    mime_type: str = Field(..., min_length=1)
    part_size: int = Field(default=5 * 1024 * 1024, ge=5 * 1024 * 1024)  # Min 5MB
    category: str = Field(default="media_resource")
    title: Optional[str] = None
    description: Optional[str] = None


class MultipartUploadInitResponse(BaseModel):
    """Response for multipart upload initialization"""

    model_config = ConfigDict(from_attributes=True)

    upload_id: str
    part_count: int
    part_size: int
    expires_at: datetime


class MultipartUploadPartRequest(BaseModel):
    """Request to upload a part"""

    model_config = ConfigDict(from_attributes=True)

    upload_id: str
    part_number: int = Field(..., ge=1)
    checksum: Optional[str] = None


class MultipartUploadPartResponse(BaseModel):
    """Response for part upload"""

    model_config = ConfigDict(from_attributes=True)

    upload_id: str
    part_number: int
    etag: str
    bytes_uploaded: int


class MultipartUploadCompleteRequest(BaseModel):
    """Request to complete multipart upload"""

    model_config = ConfigDict(from_attributes=True)

    upload_id: str
    parts: list[dict[str, int | str]] = Field(
        ...,
        description="List of parts with part_number and etag"
    )


class UploadStatusResponse(BaseModel):
    """Response for upload status check"""

    model_config = ConfigDict(from_attributes=True)

    upload_id: str
    status: UploadStatus
    progress_percentage: float
    bytes_uploaded: int
    total_bytes: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# === Dependency Injection ===

async def get_storage_service(
    session: Annotated[AsyncSession, Depends(get_async_db)],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StorageService:
    """
    Get configured storage service with tenant context.

    Args:
        session: Async database session
        tenant_context: Current tenant context
        current_user: Current authenticated user

    Returns:
        StorageService: Configured storage service instance
    """
    from apps.backend.services.storage.supabase_provider import SupabaseStorageProvider

    storage = SupabaseStorageProvider(
        organization_id=tenant_context.effective_tenant_id,
        user_id=str(current_user.id),
    )

    return storage


# === API Endpoints ===

@router.post(
    "/file",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a single file",
    description="Upload a file with validation, virus scanning, and automatic processing",
)
async def upload_single_file(
    file: Annotated[UploadFile, File(description="File to upload")],
    storage: Annotated[StorageService, Depends(get_storage_service)],
    background_tasks: BackgroundTasks,
    title: Annotated[Optional[str], Form()] = None,
    description: Annotated[Optional[str], Form()] = None,
    category: Annotated[str, Form()] = "media_resource",
    virus_scan: Annotated[bool, Form()] = True,
    generate_thumbnails: Annotated[bool, Form()] = True,
) -> FileUploadResponse:
    """
    Upload a single file to storage.

    Maximum file size: 100MB for single upload.
    Use multipart upload for larger files.

    Args:
        file: File to upload
        storage: Storage service instance
        background_tasks: Background task manager
        title: Optional file title
        description: Optional file description
        category: File category
        virus_scan: Enable virus scanning
        generate_thumbnails: Generate image thumbnails

    Returns:
        FileUploadResponse: Upload result with file metadata

    Raises:
        HTTPException: If upload fails or quota exceeded
    """
    try:
        # Validate file size (100MB limit for single upload)
        if not file.size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size cannot be determined"
            )

        if file.size > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Use multipart upload for files >100MB"
            )

        # Read file content
        file_content = await file.read()

        # Prepare upload options
        upload_options = UploadOptions(
            file_category=category,
            title=title or file.filename,
            description=description,
            virus_scan=virus_scan,
            generate_thumbnails=generate_thumbnails,
        )

        # Upload file
        logger.info(
            f"Uploading file: {file.filename}, "
            f"size: {file.size}, type: {file.content_type}"
        )

        result = await storage.upload_file(
            file_data=file_content,
            filename=file.filename or "unnamed",
            options=upload_options,
        )

        # Schedule background tasks
        if virus_scan:
            background_tasks.add_task(
                _schedule_virus_scan,
                result.file_id,
                storage.organization_id
            )

        logger.info(f"File uploaded successfully: {result.file_id}")

        return FileUploadResponse(
            file_id=result.file_id,
            upload_id=result.upload_id,
            filename=file.filename or "unnamed",
            file_size=file.size,
            mime_type=file.content_type or "application/octet-stream",
            storage_path=result.storage_path,
            cdn_url=result.cdn_url,
            thumbnail_url=result.thumbnail_url,
            status=result.status,
            created_at=datetime.utcnow(),
            warnings=result.warnings,
        )

    except QuotaExceededError as e:
        logger.warning(f"Quota exceeded: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail=e.message
        )
    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed. Please try again."
        )


@router.post(
    "/multipart/init",
    response_model=MultipartUploadInitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize multipart upload",
    description="Initialize a multipart upload session for large files",
)
async def initialize_multipart_upload(
    request: MultipartUploadInitRequest,
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> MultipartUploadInitResponse:
    """
    Initialize a multipart upload for large files.

    Use this for files larger than 100MB. The file will be split into
    parts and uploaded separately, allowing for resume and parallel uploads.

    Args:
        request: Multipart upload initialization request
        storage: Storage service instance

    Returns:
        MultipartUploadInitResponse: Upload session details

    Raises:
        HTTPException: If initialization fails
    """
    try:
        # Calculate part count
        part_count = (request.file_size + request.part_size - 1) // request.part_size

        logger.info(
            f"Initializing multipart upload: {request.filename}, "
            f"size: {request.file_size}, parts: {part_count}"
        )

        # Initialize multipart upload session in Redis for state tracking
        from uuid import uuid4
        from datetime import timedelta
        import json
        from apps.backend.core.cache import cache

        upload_id = str(uuid4())

        # Store multipart upload metadata in cache
        upload_metadata = {
            "upload_id": upload_id,
            "filename": request.filename,
            "file_size": request.file_size,
            "mime_type": request.mime_type,
            "part_size": request.part_size,
            "part_count": part_count,
            "category": request.category,
            "title": request.title,
            "description": request.description,
            "uploaded_parts": [],
            "created_at": datetime.utcnow().isoformat(),
        }

        # Cache for 24 hours
        await cache.set(
            f"multipart_upload:{upload_id}",
            json.dumps(upload_metadata),
            expire=86400
        )

        return MultipartUploadInitResponse(
            upload_id=upload_id,
            part_count=part_count,
            part_size=request.part_size,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )

    except Exception as e:
        logger.error(f"Multipart init failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize multipart upload"
        )


@router.post(
    "/multipart/part",
    response_model=MultipartUploadPartResponse,
    summary="Upload a part",
    description="Upload a single part of a multipart upload",
)
async def upload_multipart_part(
    upload_id: Annotated[str, Form()],
    part_number: Annotated[int, Form(ge=1)],
    file: Annotated[UploadFile, File()],
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> MultipartUploadPartResponse:
    """
    Upload a part of a multipart upload.

    Args:
        upload_id: Upload session ID from initialization
        part_number: Part number (1-indexed)
        file: Part file data
        storage: Storage service instance

    Returns:
        MultipartUploadPartResponse: Part upload result

    Raises:
        HTTPException: If part upload fails
    """
    try:
        file_content = await file.read()

        logger.info(
            f"Uploading part {part_number} for upload {upload_id}, "
            f"size: {len(file_content)}"
        )

        # Store part in temporary storage and update metadata
        import hashlib
        import json
        from apps.backend.core.cache import cache

        # Calculate ETag for the part
        etag = hashlib.md5(file_content).hexdigest()

        # Get upload metadata from cache
        metadata_key = f"multipart_upload:{upload_id}"
        metadata_json = await cache.get(metadata_key)

        if not metadata_json:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found or expired"
            )

        metadata = json.loads(metadata_json)

        # Store part data in cache temporarily
        part_key = f"multipart_part:{upload_id}:{part_number}"
        await cache.set(part_key, file_content, expire=86400)

        # Update uploaded parts list
        if "uploaded_parts" not in metadata:
            metadata["uploaded_parts"] = []

        metadata["uploaded_parts"].append({
            "part_number": part_number,
            "etag": etag,
            "size": len(file_content),
            "uploaded_at": datetime.utcnow().isoformat()
        })

        # Save updated metadata
        await cache.set(metadata_key, json.dumps(metadata), expire=86400)

        logger.info(f"Part {part_number} stored for upload {upload_id}")

        return MultipartUploadPartResponse(
            upload_id=upload_id,
            part_number=part_number,
            etag=etag,
            bytes_uploaded=len(file_content),
        )

    except Exception as e:
        logger.error(f"Part upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Part upload failed"
        )


@router.post(
    "/multipart/complete",
    response_model=FileUploadResponse,
    summary="Complete multipart upload",
    description="Finalize a multipart upload by combining all parts",
)
async def complete_multipart_upload(
    request: MultipartUploadCompleteRequest,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    background_tasks: BackgroundTasks,
) -> FileUploadResponse:
    """
    Complete a multipart upload.

    All parts must be uploaded before completing. The server will
    combine the parts into a single file.

    Args:
        request: Complete request with part information
        storage: Storage service instance
        background_tasks: Background task manager

    Returns:
        FileUploadResponse: Final upload result

    Raises:
        HTTPException: If completion fails
    """
    try:
        logger.info(
            f"Completing multipart upload {request.upload_id}, "
            f"parts: {len(request.parts)}"
        )

        # Complete multipart upload by combining all parts
        from uuid import uuid4
        import json
        from io import BytesIO
        from apps.backend.core.cache import cache

        # Get upload metadata
        metadata_key = f"multipart_upload:{request.upload_id}"
        metadata_json = await cache.get(metadata_key)

        if not metadata_json:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found or expired"
            )

        metadata = json.loads(metadata_json)

        # Verify all parts are uploaded
        uploaded_parts = sorted(metadata.get("uploaded_parts", []), key=lambda x: x["part_number"])
        expected_parts = metadata["part_count"]

        if len(uploaded_parts) != expected_parts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing parts: expected {expected_parts}, got {len(uploaded_parts)}"
            )

        # Combine all parts
        combined_data = BytesIO()
        total_size = 0

        for part in uploaded_parts:
            part_key = f"multipart_part:{request.upload_id}:{part['part_number']}"
            part_data = await cache.get(part_key)

            if not part_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Part {part['part_number']} data not found"
                )

            combined_data.write(part_data if isinstance(part_data, bytes) else part_data.encode())
            total_size += len(part_data if isinstance(part_data, bytes) else part_data.encode())

        combined_data.seek(0)

        # Upload the combined file to storage
        file_id = uuid4()
        upload_options = UploadOptions(
            file_category=metadata.get("category", "media_resource"),
            title=metadata.get("title"),
            description=metadata.get("description"),
            virus_scan=True,
            generate_thumbnails=metadata.get("mime_type", "").startswith("image/"),
        )

        result = await storage.upload_file_multipart(
            file_id=file_id,
            filename=metadata["filename"],
            file_stream=combined_data,
            content_type=metadata["mime_type"],
            options=upload_options
        )

        # Clean up temporary parts from cache
        for part in uploaded_parts:
            part_key = f"multipart_part:{request.upload_id}:{part['part_number']}"
            await cache.delete(part_key)

        await cache.delete(metadata_key)

        # Schedule virus scan if enabled
        if upload_options.virus_scan:
            background_tasks.add_task(_schedule_virus_scan, file_id, metadata.get("organization_id"))

        logger.info(f"Multipart upload {request.upload_id} completed: {file_id}")

        return FileUploadResponse(
            file_id=file_id,
            upload_id=request.upload_id,
            filename=metadata["filename"],
            file_size=total_size,
            mime_type=metadata["mime_type"],
            storage_path=result.storage_path,
            cdn_url=result.cdn_url,
            status=UploadStatus.COMPLETED,
            created_at=datetime.utcnow(),
            warnings=[],
        )

    except Exception as e:
        logger.error(f"Multipart completion failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete multipart upload"
        )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete uploaded file",
    description="Delete an uploaded file (soft delete by default)",
)
async def delete_uploaded_file(
    file_id: UUID,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    permanent: bool = False,
) -> None:
    """
    Delete an uploaded file.

    Args:
        file_id: File identifier
        storage: Storage service instance
        permanent: Whether to permanently delete (default: soft delete)

    Raises:
        HTTPException: If deletion fails
    """
    try:
        logger.info(f"Deleting file {file_id}, permanent: {permanent}")

        success = await storage.delete_file(file_id, permanent=permanent)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        logger.info(f"File deleted: {file_id}")

    except Exception as e:
        logger.error(f"Delete failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )


@router.get(
    "/{file_id}/status",
    response_model=UploadStatusResponse,
    summary="Check upload status",
    description="Get the status of an upload or multipart upload",
)
async def get_upload_status(
    file_id: str,
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> UploadStatusResponse:
    """
    Get upload status and progress.

    Args:
        file_id: Upload or file identifier
        storage: Storage service instance

    Returns:
        UploadStatusResponse: Current upload status

    Raises:
        HTTPException: If status check fails
    """
    try:
        progress = storage.get_upload_progress(file_id)

        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload not found"
            )

        return UploadStatusResponse(
            upload_id=progress.upload_id,
            status=progress.status,
            progress_percentage=progress.progress_percentage,
            bytes_uploaded=progress.bytes_uploaded,
            total_bytes=progress.total_bytes,
            error_message=progress.error_message,
            created_at=progress.created_at,
            updated_at=progress.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get upload status"
        )


# === Background Tasks ===

async def _schedule_virus_scan(file_id: UUID, organization_id: Optional[str]) -> None:
    """
    Schedule virus scan as background task.

    Args:
        file_id: File identifier
        organization_id: Organization ID for tenant isolation
    """
    try:
        logger.info(f"Scheduling virus scan for file {file_id}")

        # Use the virus scanner service
        from apps.backend.services.storage.virus_scanner import VirusScanner

        scanner = VirusScanner()
        scan_result = await scanner.scan_file(str(file_id), organization_id)

        if scan_result.is_infected:
            logger.warning(f"Virus detected in file {file_id}: {scan_result.threat_name}")
            # Quarantine the file
            await scanner.quarantine_file(str(file_id))
        else:
            logger.info(f"Virus scan clean for file {file_id}")

    except Exception as e:
        logger.error(f"Virus scan failed for {file_id}: {str(e)}", exc_info=True)
