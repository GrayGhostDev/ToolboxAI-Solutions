# File Upload System

The ToolBoxAI File Upload System provides comprehensive file handling capabilities with support for small files, large multipart uploads, batch operations, and real-time progress tracking. The system is optimized for educational content with built-in compliance and security features.

## Table of Contents
- [Upload Strategies](#upload-strategies)
- [Resumable Uploads with TUS Protocol](#resumable-uploads-with-tus-protocol)
- [Progress Tracking Implementation](#progress-tracking-implementation)
- [Error Handling and Retry Logic](#error-handling-and-retry-logic)
- [Multi-file Uploads](#multi-file-uploads)
- [Upload Validation](#upload-validation)
- [Performance Optimization](#performance-optimization)
- [Security Considerations](#security-considerations)

## Upload Strategies

The system employs different upload strategies based on file size and type to optimize performance and user experience:

### Strategy Selection

```python
class UploadStrategy(Enum):
    DIRECT = "direct"           # Files < 10MB
    CHUNKED = "chunked"         # Files 10MB - 100MB
    RESUMABLE = "resumable"     # Files > 100MB
    STREAMING = "streaming"     # Very large files or streaming content

def determine_upload_strategy(file_size: int, mime_type: str) -> UploadStrategy:
    """Determine optimal upload strategy based on file characteristics"""

    if file_size < 10 * 1024 * 1024:  # 10MB
        return UploadStrategy.DIRECT
    elif file_size < 100 * 1024 * 1024:  # 100MB
        return UploadStrategy.CHUNKED
    else:
        return UploadStrategy.RESUMABLE
```

### Direct Upload (Small Files)

For files under 10MB, use direct upload for optimal speed:

```python
async def direct_upload(
    self,
    file_data: bytes,
    filename: str,
    options: UploadOptions
) -> UploadResult:
    """Direct upload for small files with immediate processing"""

    # Validate file first
    validation_result = await self.file_validator.validate_file(
        file_data, filename, options.file_category
    )

    if not validation_result.is_valid:
        raise ValidationError(validation_result.errors)

    # Generate metadata
    file_id = uuid4()
    storage_path = self._generate_storage_path(file_id, filename, options.file_category)
    checksum = hashlib.sha256(file_data).hexdigest()

    # Create database record
    file_record = await self._create_file_record(
        file_id=file_id,
        filename=filename,
        file_data=file_data,
        storage_path=storage_path,
        options=options
    )

    try:
        # Upload to Supabase Storage
        upload_response = self.supabase.storage.from_(self.bucket_name).upload(
            path=storage_path,
            file=file_data,
            file_options={
                "content-type": validation_result.detected_mime_type,
                "cache-control": "public, max-age=3600",
                "upsert": False
            }
        )

        if upload_response.get("error"):
            raise StorageError(f"Upload failed: {upload_response['error']}")

        # Immediate virus scan for small files
        if options.virus_scan:
            scan_result = await self.virus_scanner.scan_data(file_data, filename)

            if not scan_result.is_clean:
                await self._quarantine_file(file_id, scan_result)
                raise VirusDetectedError(scan_result.threat_name)

        # Update file status
        await self._update_file_status(file_id, FileStatus.AVAILABLE)

        # Generate CDN URL
        cdn_url = await self.cdn_manager.get_file_url(self.bucket_name, storage_path)

        return UploadResult(
            file_id=file_id,
            filename=file_record.filename,
            file_size=len(file_data),
            mime_type=validation_result.detected_mime_type,
            status="available",
            cdn_url=cdn_url,
            checksum=checksum
        )

    except Exception as e:
        await self._handle_upload_error(file_id, e)
        raise
```

### Chunked Upload (Medium Files)

For files between 10MB and 100MB, use chunked upload:

```python
@dataclass
class ChunkedUploadSession:
    upload_id: str
    file_id: UUID
    total_size: int
    chunk_size: int
    chunks_uploaded: int
    total_chunks: int
    upload_urls: List[str]
    expires_at: datetime

async def create_chunked_upload(
    self,
    filename: str,
    file_size: int,
    options: UploadOptions,
    chunk_size: int = 10 * 1024 * 1024  # 10MB chunks
) -> ChunkedUploadSession:
    """Initialize chunked upload session"""

    upload_id = str(uuid4())
    file_id = uuid4()
    total_chunks = math.ceil(file_size / chunk_size)

    # Create file record in pending state
    await self._create_file_record(
        file_id=file_id,
        filename=filename,
        file_size=file_size,
        status=FileStatus.PENDING,
        options=options
    )

    # Generate signed URLs for each chunk
    upload_urls = []
    for chunk_index in range(total_chunks):
        chunk_path = f"{self._get_storage_path(file_id, filename)}.chunk.{chunk_index}"

        signed_url = self.supabase.storage.from_(self.bucket_name).create_signed_upload_url(
            path=chunk_path,
            expires_in=3600  # 1 hour
        )

        upload_urls.append(signed_url["signedURL"])

    # Store upload session
    session = ChunkedUploadSession(
        upload_id=upload_id,
        file_id=file_id,
        total_size=file_size,
        chunk_size=chunk_size,
        chunks_uploaded=0,
        total_chunks=total_chunks,
        upload_urls=upload_urls,
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )

    await self._store_upload_session(session)

    return session

async def upload_chunk(
    self,
    upload_id: str,
    chunk_index: int,
    chunk_data: bytes,
    content_range: str
) -> Dict[str, Any]:
    """Upload a single chunk"""

    session = await self._get_upload_session(upload_id)

    if not session:
        raise ValueError(f"Upload session not found: {upload_id}")

    if session.expires_at < datetime.utcnow():
        raise ValueError("Upload session expired")

    if chunk_index >= session.total_chunks:
        raise ValueError(f"Invalid chunk index: {chunk_index}")

    try:
        # Upload chunk to designated URL
        upload_url = session.upload_urls[chunk_index]

        async with aiohttp.ClientSession() as client:
            async with client.put(
                upload_url,
                data=chunk_data,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Range": content_range
                }
            ) as response:
                if response.status not in [200, 201]:
                    raise StorageError(f"Chunk upload failed: {response.status}")

        # Update session progress
        session.chunks_uploaded += 1
        await self._update_upload_session(session)

        # Check if upload is complete
        if session.chunks_uploaded == session.total_chunks:
            await self._finalize_chunked_upload(session)

        return {
            "upload_id": upload_id,
            "chunk_index": chunk_index,
            "chunks_uploaded": session.chunks_uploaded,
            "total_chunks": session.total_chunks,
            "progress_percentage": (session.chunks_uploaded / session.total_chunks) * 100,
            "completed": session.chunks_uploaded == session.total_chunks
        }

    except Exception as e:
        logger.error(f"Chunk upload failed: {e}")
        raise

async def _finalize_chunked_upload(self, session: ChunkedUploadSession):
    """Combine chunks into final file"""

    # Combine all chunks
    combined_data = b""

    for chunk_index in range(session.total_chunks):
        chunk_path = f"{self._get_storage_path(session.file_id, '')}.chunk.{chunk_index}"

        # Download chunk
        chunk_response = self.supabase.storage.from_(self.bucket_name).download(chunk_path)
        combined_data += chunk_response

        # Delete chunk file
        self.supabase.storage.from_(self.bucket_name).remove([chunk_path])

    # Upload final combined file
    final_path = self._get_storage_path(session.file_id, "")

    self.supabase.storage.from_(self.bucket_name).upload(
        path=final_path,
        file=combined_data,
        file_options={
            "content-type": "application/octet-stream",
            "upsert": True
        }
    )

    # Update file record
    await self._update_file_status(session.file_id, FileStatus.PROCESSING)

    # Schedule background processing
    await self._schedule_background_processing(session.file_id, combined_data)

    # Clean up session
    await self._cleanup_upload_session(session.upload_id)
```

## Resumable Uploads with TUS Protocol

For large files over 100MB, implement TUS (Transloadit Upload Service) protocol for resumable uploads:

```python
from tusclient import client as tus_client

class TUSUploadHandler:
    """Handles TUS protocol resumable uploads"""

    def __init__(self, storage_provider: SupabaseStorageProvider):
        self.storage_provider = storage_provider
        self.tus_endpoint = f"{settings.API_BASE_URL}/api/v1/storage/tus"

    async def create_resumable_upload(
        self,
        filename: str,
        file_size: int,
        options: UploadOptions
    ) -> Dict[str, Any]:
        """Create resumable upload session"""

        file_id = uuid4()

        # Create TUS upload
        upload_metadata = {
            "filename": filename,
            "file_id": str(file_id),
            "organization_id": str(self.storage_provider.organization_id),
            "user_id": str(self.storage_provider.user_id),
            "category": options.file_category,
            "title": options.title or filename
        }

        client = tus_client.TusClient(self.tus_endpoint)
        uploader = client.uploader(
            file_size=file_size,
            metadata=upload_metadata,
            chunk_size=10 * 1024 * 1024  # 10MB chunks
        )

        # Get upload URL
        upload_url = uploader.get_upload_url()

        # Store upload session
        session_data = {
            "file_id": file_id,
            "upload_url": upload_url,
            "file_size": file_size,
            "filename": filename,
            "options": options.dict(),
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=1)  # 24 hour expiry
        }

        await self._store_resumable_session(str(file_id), session_data)

        return {
            "file_id": file_id,
            "upload_url": upload_url,
            "chunk_size": 10 * 1024 * 1024,
            "expires_at": session_data["expires_at"]
        }

    async def handle_tus_upload_chunk(
        self,
        upload_id: str,
        offset: int,
        chunk_data: bytes,
        upload_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """Handle TUS PATCH request for chunk upload"""

        session = await self._get_resumable_session(upload_id)
        if not session:
            raise ValueError(f"Upload session not found: {upload_id}")

        # Validate offset
        current_offset = await self._get_current_offset(upload_id)
        if offset != current_offset:
            raise ValueError(f"Invalid offset. Expected {current_offset}, got {offset}")

        # Store chunk
        await self._store_upload_chunk(upload_id, offset, chunk_data)

        new_offset = offset + len(chunk_data)
        await self._update_upload_offset(upload_id, new_offset)

        # Check if upload is complete
        if upload_length and new_offset >= upload_length:
            await self._complete_resumable_upload(upload_id, session)

        return {
            "upload_id": upload_id,
            "offset": new_offset,
            "complete": upload_length and new_offset >= upload_length
        }

    async def get_upload_progress(self, file_id: UUID) -> Dict[str, Any]:
        """Get current upload progress"""

        session = await self._get_resumable_session(str(file_id))
        if not session:
            raise ValueError(f"Upload session not found: {file_id}")

        current_offset = await self._get_current_offset(str(file_id))
        total_size = session["file_size"]

        progress_percentage = (current_offset / total_size) * 100 if total_size > 0 else 0

        return {
            "file_id": file_id,
            "bytes_uploaded": current_offset,
            "total_bytes": total_size,
            "progress_percentage": progress_percentage,
            "status": "uploading" if current_offset < total_size else "processing"
        }

    async def resume_upload(self, file_id: UUID) -> Dict[str, Any]:
        """Resume an interrupted upload"""

        session = await self._get_resumable_session(str(file_id))
        if not session:
            raise ValueError(f"Upload session not found: {file_id}")

        # Check if session has expired
        if datetime.fromisoformat(session["expires_at"]) < datetime.utcnow():
            raise ValueError("Upload session has expired")

        current_offset = await self._get_current_offset(str(file_id))

        return {
            "file_id": file_id,
            "upload_url": session["upload_url"],
            "current_offset": current_offset,
            "total_size": session["file_size"],
            "chunk_size": 10 * 1024 * 1024
        }
```

## Progress Tracking Implementation

Real-time progress tracking using WebSockets and Redis:

```python
class UploadProgressTracker:
    """Tracks and broadcasts upload progress"""

    def __init__(self, redis_client, websocket_manager):
        self.redis = redis_client
        self.websocket_manager = websocket_manager

    async def update_progress(
        self,
        file_id: UUID,
        user_id: UUID,
        bytes_uploaded: int,
        total_bytes: int,
        status: str = "uploading"
    ):
        """Update upload progress and notify clients"""

        progress_data = {
            "file_id": str(file_id),
            "user_id": str(user_id),
            "bytes_uploaded": bytes_uploaded,
            "total_bytes": total_bytes,
            "progress_percentage": (bytes_uploaded / total_bytes) * 100 if total_bytes > 0 else 0,
            "status": status,
            "estimated_time_remaining": self._calculate_eta(file_id, bytes_uploaded, total_bytes),
            "upload_speed": await self._calculate_upload_speed(file_id, bytes_uploaded),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Store in Redis
        await self.redis.setex(
            f"upload_progress:{file_id}",
            3600,  # 1 hour expiry
            json.dumps(progress_data)
        )

        # Broadcast to WebSocket clients
        await self.websocket_manager.send_to_user(
            user_id,
            {
                "type": "upload_progress",
                "data": progress_data
            }
        )

        # Store progress history for analytics
        await self._store_progress_history(file_id, progress_data)

    async def _calculate_upload_speed(self, file_id: UUID, bytes_uploaded: int) -> float:
        """Calculate current upload speed in bytes per second"""

        # Get recent progress history
        history_key = f"upload_history:{file_id}"
        history = await self.redis.lrange(history_key, -5, -1)  # Last 5 updates

        if len(history) < 2:
            return 0.0

        # Calculate speed based on recent progress
        recent_updates = [json.loads(h) for h in history]

        time_diff = datetime.fromisoformat(recent_updates[-1]["timestamp"]) - \
                   datetime.fromisoformat(recent_updates[0]["timestamp"])

        bytes_diff = recent_updates[-1]["bytes_uploaded"] - recent_updates[0]["bytes_uploaded"]

        if time_diff.total_seconds() > 0:
            return bytes_diff / time_diff.total_seconds()

        return 0.0

    def _calculate_eta(self, file_id: UUID, bytes_uploaded: int, total_bytes: int) -> Optional[int]:
        """Calculate estimated time remaining in seconds"""

        if bytes_uploaded == 0:
            return None

        # Get upload speed
        speed = asyncio.create_task(self._calculate_upload_speed(file_id, bytes_uploaded))

        if speed <= 0:
            return None

        remaining_bytes = total_bytes - bytes_uploaded
        eta_seconds = remaining_bytes / speed

        return max(0, int(eta_seconds))

    async def get_progress(self, file_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current progress for a file"""

        progress_data = await self.redis.get(f"upload_progress:{file_id}")

        if progress_data:
            return json.loads(progress_data)

        return None

    async def cleanup_progress(self, file_id: UUID):
        """Clean up progress tracking data"""

        await self.redis.delete(f"upload_progress:{file_id}")
        await self.redis.delete(f"upload_history:{file_id}")

# WebSocket endpoint for real-time progress
@router.websocket("/ws/upload/{file_id}")
async def upload_progress_websocket(
    websocket: WebSocket,
    file_id: UUID,
    current_user: User = Depends(get_current_user_ws),
    progress_tracker: UploadProgressTracker = Depends(get_progress_tracker)
):
    await websocket.accept()

    try:
        # Send current progress
        current_progress = await progress_tracker.get_progress(file_id)
        if current_progress:
            await websocket.send_json({
                "type": "progress_update",
                "data": current_progress
            })

        # Keep connection alive and send updates
        while True:
            # Check for new progress every second
            await asyncio.sleep(1)

            progress = await progress_tracker.get_progress(file_id)
            if progress:
                await websocket.send_json({
                    "type": "progress_update",
                    "data": progress
                })

                # Close connection when upload is complete
                if progress["status"] in ["completed", "failed"]:
                    break

    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
```

## Error Handling and Retry Logic

Comprehensive error handling with automatic retry capabilities:

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class UploadError(Exception):
    """Base upload error"""
    pass

class RetryableUploadError(UploadError):
    """Upload error that can be retried"""
    pass

class FatalUploadError(UploadError):
    """Upload error that should not be retried"""
    pass

class NetworkError(RetryableUploadError):
    """Network-related upload error"""
    pass

class UploadErrorHandler:
    """Handles upload errors with retry logic"""

    def __init__(self, storage_provider: SupabaseStorageProvider):
        self.storage_provider = storage_provider
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    @retry(
        retry=retry_if_exception_type(RetryableUploadError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def upload_with_retry(
        self,
        file_data: bytes,
        filename: str,
        options: UploadOptions
    ) -> UploadResult:
        """Upload with automatic retry logic"""

        try:
            return await self.storage_provider.upload_file(file_data, filename, options)

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error during upload: {e}")

        except Exception as e:
            # Categorize error
            if self._is_retryable_error(e):
                raise RetryableUploadError(f"Retryable upload error: {e}")
            else:
                raise FatalUploadError(f"Fatal upload error: {e}")

    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error is retryable"""

        retryable_errors = [
            "timeout",
            "connection reset",
            "temporary failure",
            "service unavailable",
            "rate limit",
            "503",
            "502",
            "504"
        ]

        error_message = str(error).lower()

        return any(retryable_error in error_message for retryable_error in retryable_errors)

    async def handle_upload_failure(
        self,
        file_id: UUID,
        error: Exception,
        attempt_number: int = 1
    ) -> Dict[str, Any]:
        """Handle upload failure with appropriate response"""

        error_details = {
            "file_id": str(file_id),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "attempt_number": attempt_number,
            "timestamp": datetime.utcnow().isoformat(),
            "is_retryable": isinstance(error, RetryableUploadError)
        }

        # Log error
        logger.error(f"Upload failed for file {file_id}: {error_details}")

        # Update file status
        await self.storage_provider._update_file_status(
            file_id,
            FileStatus.ERROR,
            error_message=str(error)
        )

        # Store error details
        await self._store_error_details(file_id, error_details)

        # Notify user
        await self._notify_upload_failure(file_id, error_details)

        return error_details

    async def retry_failed_upload(self, file_id: UUID) -> Dict[str, Any]:
        """Retry a failed upload"""

        # Get original upload details
        file_record = await self._get_file_record(file_id)
        if not file_record:
            raise ValueError(f"File record not found: {file_id}")

        # Check if retry is allowed
        error_details = await self._get_error_details(file_id)
        if not error_details or not error_details.get("is_retryable"):
            raise FatalUploadError("Upload cannot be retried")

        # Reset file status
        await self.storage_provider._update_file_status(file_id, FileStatus.PENDING)

        try:
            # Attempt retry
            # This would typically involve re-uploading the file
            # Implementation depends on how the original file data is stored/retrieved

            return {
                "file_id": str(file_id),
                "status": "retrying",
                "message": "Upload retry initiated"
            }

        except Exception as e:
            await self.handle_upload_failure(file_id, e, attempt_number=2)
            raise

# Usage in upload endpoints
@router.post("/files/upload")
async def upload_file_with_error_handling(
    file: UploadFile,
    storage: SupabaseStorageProvider = Depends(get_storage_service),
    error_handler: UploadErrorHandler = Depends(get_error_handler)
):
    try:
        file_data = await file.read()
        options = UploadOptions(file_category="educational_content")

        result = await error_handler.upload_with_retry(file_data, file.filename, options)

        return {
            "status": "success",
            "data": result,
            "message": "File uploaded successfully"
        }

    except FatalUploadError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload failed: {e}"
        )

    except RetryableUploadError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Upload temporarily unavailable: {e}"
        )

    except Exception as e:
        logger.error(f"Unexpected upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during upload"
        )
```

## Multi-file Uploads

Efficient batch upload handling with parallel processing:

```python
from asyncio import Semaphore
from typing import List, Callable, Optional

@dataclass
class BatchUploadItem:
    file_data: bytes
    filename: str
    options: UploadOptions

@dataclass
class BatchUploadResult:
    batch_id: str
    total_files: int
    successful_uploads: int
    failed_uploads: int
    results: List[Dict[str, Any]]
    processing_time: float

class BatchUploadManager:
    """Manages batch file uploads with parallel processing"""

    def __init__(
        self,
        storage_provider: SupabaseStorageProvider,
        max_concurrent_uploads: int = 5
    ):
        self.storage_provider = storage_provider
        self.semaphore = Semaphore(max_concurrent_uploads)
        self.progress_callbacks: Dict[str, Callable] = {}

    async def upload_batch(
        self,
        files: List[BatchUploadItem],
        progress_callback: Optional[Callable] = None
    ) -> BatchUploadResult:
        """Upload multiple files in parallel"""

        batch_id = str(uuid4())
        start_time = time.time()

        if progress_callback:
            self.progress_callbacks[batch_id] = progress_callback

        # Create upload tasks
        upload_tasks = [
            self._upload_single_file_in_batch(batch_id, index, item)
            for index, item in enumerate(files)
        ]

        # Execute uploads in parallel
        results = await asyncio.gather(*upload_tasks, return_exceptions=True)

        # Process results
        successful_uploads = 0
        failed_uploads = 0
        processed_results = []

        for index, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "index": index,
                    "filename": files[index].filename,
                    "status": "failed",
                    "error": str(result)
                })
                failed_uploads += 1
            else:
                processed_results.append({
                    "index": index,
                    "filename": result.filename,
                    "status": "success",
                    "file_id": str(result.file_id),
                    "cdn_url": result.cdn_url
                })
                successful_uploads += 1

        processing_time = time.time() - start_time

        # Final progress update
        if progress_callback:
            await progress_callback({
                "batch_id": batch_id,
                "completed": len(files),
                "total": len(files),
                "successful": successful_uploads,
                "failed": failed_uploads,
                "finished": True
            })

        # Cleanup
        if batch_id in self.progress_callbacks:
            del self.progress_callbacks[batch_id]

        return BatchUploadResult(
            batch_id=batch_id,
            total_files=len(files),
            successful_uploads=successful_uploads,
            failed_uploads=failed_uploads,
            results=processed_results,
            processing_time=processing_time
        )

    async def _upload_single_file_in_batch(
        self,
        batch_id: str,
        index: int,
        item: BatchUploadItem
    ) -> UploadResult:
        """Upload a single file as part of a batch"""

        async with self.semaphore:  # Limit concurrent uploads
            try:
                # Update progress
                await self._update_batch_progress(batch_id, index, "uploading")

                # Perform upload
                result = await self.storage_provider.upload_file(
                    item.file_data,
                    item.filename,
                    item.options
                )

                # Update progress
                await self._update_batch_progress(batch_id, index, "completed")

                return result

            except Exception as e:
                await self._update_batch_progress(batch_id, index, "failed", str(e))
                raise

    async def _update_batch_progress(
        self,
        batch_id: str,
        file_index: int,
        status: str,
        error: Optional[str] = None
    ):
        """Update batch upload progress"""

        callback = self.progress_callbacks.get(batch_id)
        if callback:
            progress_data = {
                "batch_id": batch_id,
                "file_index": file_index,
                "status": status,
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            }

            await callback(progress_data)

# FastAPI endpoint for batch upload
@router.post("/files/upload/batch")
async def upload_files_batch(
    files: List[UploadFile],
    manifest: str = Form(...),  # JSON string with file metadata
    storage: SupabaseStorageProvider = Depends(get_storage_service),
    current_user: User = Depends(get_current_user)
):
    try:
        # Parse manifest
        file_metadata = json.loads(manifest)

        if len(files) != len(file_metadata):
            raise HTTPException(
                status_code=400,
                detail="Number of files must match manifest entries"
            )

        # Prepare batch items
        batch_items = []
        for file, metadata in zip(files, file_metadata):
            file_data = await file.read()
            options = UploadOptions(
                file_category=metadata.get("category", "media_resource"),
                title=metadata.get("title", file.filename),
                description=metadata.get("description"),
                tags=metadata.get("tags", [])
            )

            batch_items.append(BatchUploadItem(
                file_data=file_data,
                filename=file.filename,
                options=options
            ))

        # Create batch upload manager
        batch_manager = BatchUploadManager(storage, max_concurrent_uploads=3)

        # Upload files
        result = await batch_manager.upload_batch(batch_items)

        return {
            "status": "success",
            "data": {
                "batch_id": result.batch_id,
                "total_files": result.total_files,
                "successful_uploads": result.successful_uploads,
                "failed_uploads": result.failed_uploads,
                "results": result.results,
                "processing_time": result.processing_time
            }
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid manifest JSON"
        )

    except Exception as e:
        logger.error(f"Batch upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Batch upload failed"
        )
```

## Upload Validation

Comprehensive validation before and during upload:

```python
class UploadValidator:
    """Validates uploads before processing"""

    def __init__(self):
        self.max_file_sizes = {
            "educational_content": 100 * 1024 * 1024,    # 100MB
            "student_submission": 50 * 1024 * 1024,      # 50MB
            "assessment": 25 * 1024 * 1024,              # 25MB
            "media_resource": 500 * 1024 * 1024,         # 500MB
            "avatar": 10 * 1024 * 1024,                  # 10MB
            "administrative": 100 * 1024 * 1024,         # 100MB
            "temporary": 1024 * 1024 * 1024,             # 1GB
            "report": 50 * 1024 * 1024                   # 50MB
        }

        self.allowed_mime_types = {
            "educational_content": [
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain",
                "text/html"
            ],
            "student_submission": [
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain",
                "image/jpeg",
                "image/png"
            ],
            "media_resource": [
                "image/jpeg",
                "image/png",
                "image/webp",
                "video/mp4",
                "video/webm",
                "audio/mp3",
                "audio/wav"
            ],
            "avatar": [
                "image/jpeg",
                "image/png",
                "image/webp"
            ]
        }

    async def validate_upload(
        self,
        file_data: bytes,
        filename: str,
        category: str,
        user_context: Dict[str, Any]
    ) -> ValidationResult:
        """Comprehensive upload validation"""

        errors = []
        warnings = []

        # File size validation
        file_size = len(file_data)
        max_size = self.max_file_sizes.get(category, 100 * 1024 * 1024)

        if file_size > max_size:
            errors.append(f"File size {file_size} exceeds maximum {max_size} for category {category}")

        # MIME type detection and validation
        detected_mime_type = magic.from_buffer(file_data, mime=True)

        allowed_types = self.allowed_mime_types.get(category, [])
        if allowed_types and detected_mime_type not in allowed_types:
            errors.append(f"MIME type {detected_mime_type} not allowed for category {category}")

        # Filename validation
        if not self._is_safe_filename(filename):
            errors.append("Filename contains unsafe characters")

        # Content validation
        content_validation = await self._validate_file_content(file_data, detected_mime_type)
        if not content_validation.is_valid:
            errors.extend(content_validation.errors)

        # Quota validation
        quota_check = await self._check_storage_quota(
            user_context["organization_id"],
            file_size
        )
        if not quota_check.has_space:
            errors.append(f"Insufficient storage quota. Available: {quota_check.available_bytes}")

        # Educational compliance validation
        compliance_check = await self._validate_educational_compliance(
            file_data,
            category,
            user_context
        )
        if compliance_check.warnings:
            warnings.extend(compliance_check.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            detected_mime_type=detected_mime_type,
            file_size=file_size,
            compliance_requirements=compliance_check.requirements
        )

    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe"""

        # Check for dangerous patterns
        dangerous_patterns = [
            r'\.\./',  # Path traversal
            r'[<>:"|?*]',  # Windows invalid chars
            r'^\.',  # Hidden files
            r'\.exe$|\.bat$|\.cmd$|\.scr$',  # Executable files
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return False

        # Check length
        if len(filename) > 255:
            return False

        return True

    async def _validate_file_content(
        self,
        file_data: bytes,
        mime_type: str
    ) -> ValidationResult:
        """Validate file content integrity"""

        try:
            if mime_type.startswith('image/'):
                # Validate image file
                return await self._validate_image_content(file_data)
            elif mime_type == 'application/pdf':
                # Validate PDF file
                return await self._validate_pdf_content(file_data)
            elif mime_type.startswith('video/'):
                # Validate video file
                return await self._validate_video_content(file_data)
            else:
                # Basic validation for other files
                return ValidationResult(is_valid=True)

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Content validation failed: {e}"]
            )

    async def _validate_image_content(self, file_data: bytes) -> ValidationResult:
        """Validate image file content"""

        try:
            from PIL import Image

            # Try to open image
            image = Image.open(io.BytesIO(file_data))

            # Check image properties
            if image.width > 10000 or image.height > 10000:
                return ValidationResult(
                    is_valid=False,
                    errors=["Image dimensions too large"]
                )

            # Verify image format
            if image.format not in ['JPEG', 'PNG', 'WebP', 'GIF']:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Unsupported image format: {image.format}"]
                )

            return ValidationResult(is_valid=True)

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid image file: {e}"]
            )
```

## Performance Optimization

Upload performance optimization strategies:

```python
class UploadOptimizer:
    """Optimizes upload performance based on file characteristics"""

    def __init__(self):
        self.compression_thresholds = {
            "image": 1 * 1024 * 1024,  # 1MB
            "document": 5 * 1024 * 1024,  # 5MB
            "video": 50 * 1024 * 1024,  # 50MB
        }

    async def optimize_for_upload(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str
    ) -> tuple[bytes, Dict[str, Any]]:
        """Optimize file for upload"""

        optimization_info = {
            "original_size": len(file_data),
            "optimized": False,
            "compression_ratio": 1.0,
            "optimization_type": None
        }

        try:
            if mime_type.startswith('image/'):
                optimized_data, info = await self._optimize_image(file_data, mime_type)
                optimization_info.update(info)
                return optimized_data, optimization_info

            elif mime_type == 'application/pdf':
                optimized_data, info = await self._optimize_pdf(file_data)
                optimization_info.update(info)
                return optimized_data, optimization_info

            elif mime_type.startswith('video/'):
                # For videos, we might want to transcode or compress
                # This would typically be done in background processing
                return file_data, optimization_info

            else:
                # Try general compression for other files
                if len(file_data) > self.compression_thresholds.get("document", 5 * 1024 * 1024):
                    optimized_data, info = await self._compress_generic(file_data)
                    optimization_info.update(info)
                    return optimized_data, optimization_info

        except Exception as e:
            logger.warning(f"Optimization failed: {e}")

        return file_data, optimization_info

    async def _optimize_image(
        self,
        file_data: bytes,
        mime_type: str
    ) -> tuple[bytes, Dict[str, Any]]:
        """Optimize image file"""

        from PIL import Image

        original_size = len(file_data)

        if original_size < self.compression_thresholds["image"]:
            return file_data, {"optimized": False}

        try:
            image = Image.open(io.BytesIO(file_data))

            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background

            # Optimize quality based on size
            if original_size > 5 * 1024 * 1024:  # > 5MB
                quality = 75
            elif original_size > 2 * 1024 * 1024:  # > 2MB
                quality = 80
            else:
                quality = 85

            # Save optimized version
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            optimized_data = output.getvalue()

            optimized_size = len(optimized_data)
            compression_ratio = optimized_size / original_size

            # Only use optimized version if it's significantly smaller
            if compression_ratio < 0.9:
                return optimized_data, {
                    "optimized": True,
                    "optimization_type": "image_compression",
                    "optimized_size": optimized_size,
                    "compression_ratio": compression_ratio,
                    "quality": quality
                }

        except Exception as e:
            logger.warning(f"Image optimization failed: {e}")

        return file_data, {"optimized": False}

    async def determine_optimal_chunk_size(
        self,
        file_size: int,
        connection_speed: Optional[float] = None
    ) -> int:
        """Determine optimal chunk size based on file size and connection"""

        # Base chunk sizes
        if file_size < 50 * 1024 * 1024:  # < 50MB
            base_chunk_size = 5 * 1024 * 1024  # 5MB
        elif file_size < 500 * 1024 * 1024:  # < 500MB
            base_chunk_size = 10 * 1024 * 1024  # 10MB
        else:
            base_chunk_size = 25 * 1024 * 1024  # 25MB

        # Adjust based on connection speed if available
        if connection_speed:
            # Aim for chunks that take 30-60 seconds to upload
            target_upload_time = 45  # seconds
            optimal_chunk_size = int(connection_speed * target_upload_time)

            # Clamp to reasonable bounds
            optimal_chunk_size = max(1 * 1024 * 1024, optimal_chunk_size)  # Min 1MB
            optimal_chunk_size = min(50 * 1024 * 1024, optimal_chunk_size)  # Max 50MB

            return optimal_chunk_size

        return base_chunk_size
```

## Security Considerations

Security measures implemented in the upload system:

```python
class UploadSecurity:
    """Security measures for file uploads"""

    async def validate_upload_security(
        self,
        file_data: bytes,
        filename: str,
        user_context: Dict[str, Any]
    ) -> SecurityValidationResult:
        """Comprehensive security validation"""

        security_issues = []
        risk_level = "low"

        # File type validation
        mime_type = magic.from_buffer(file_data, mime=True)

        # Check for executable files
        if self._is_executable_file(filename, mime_type):
            security_issues.append("Executable file upload not allowed")
            risk_level = "high"

        # Check for script files
        if self._contains_scripts(file_data, mime_type):
            security_issues.append("File contains executable scripts")
            risk_level = "high"

        # File size bomb check
        if self._is_compression_bomb(file_data, mime_type):
            security_issues.append("Potential compression bomb detected")
            risk_level = "high"

        # Metadata examination
        metadata_issues = await self._examine_file_metadata(file_data, mime_type)
        security_issues.extend(metadata_issues)

        # Rate limiting check
        if await self._check_upload_rate_limits(user_context["user_id"]):
            security_issues.append("Upload rate limit exceeded")
            risk_level = "medium"

        # User reputation check
        user_risk = await self._assess_user_risk(user_context)
        if user_risk.is_high_risk:
            security_issues.extend(user_risk.concerns)
            risk_level = max(risk_level, "medium")

        return SecurityValidationResult(
            is_safe=len(security_issues) == 0,
            security_issues=security_issues,
            risk_level=risk_level,
            requires_manual_review=risk_level == "high",
            quarantine_recommended=risk_level == "high"
        )

    def _is_executable_file(self, filename: str, mime_type: str) -> bool:
        """Check if file is executable"""

        executable_extensions = [
            '.exe', '.bat', '.cmd', '.com', '.scr', '.pif',
            '.msi', '.dll', '.jar', '.app', '.deb', '.rpm'
        ]

        executable_mime_types = [
            'application/x-executable',
            'application/x-msdos-program',
            'application/x-msdownload',
            'application/java-archive'
        ]

        _, ext = os.path.splitext(filename.lower())

        return ext in executable_extensions or mime_type in executable_mime_types

    def _contains_scripts(self, file_data: bytes, mime_type: str) -> bool:
        """Check if file contains executable scripts"""

        if mime_type in ['text/html', 'application/xml', 'text/xml']:
            # Check for script tags in HTML/XML
            content = file_data.decode('utf-8', errors='ignore').lower()
            script_patterns = [
                r'<script[^>]*>',
                r'javascript:',
                r'vbscript:',
                r'onload=',
                r'onerror='
            ]

            for pattern in script_patterns:
                if re.search(pattern, content):
                    return True

        elif mime_type == 'application/pdf':
            # Check for JavaScript in PDF
            content = file_data.decode('utf-8', errors='ignore').lower()
            if '/javascript' in content or '/js' in content:
                return True

        return False

    def _is_compression_bomb(self, file_data: bytes, mime_type: str) -> bool:
        """Detect potential compression bombs"""

        if mime_type in ['application/zip', 'application/x-rar', 'application/x-7z-compressed']:
            # Check compression ratio
            try:
                if mime_type == 'application/zip':
                    import zipfile
                    with zipfile.ZipFile(io.BytesIO(file_data)) as z:
                        total_size = sum(info.file_size for info in z.infolist())
                        compression_ratio = total_size / len(file_data)

                        # Suspicious if compression ratio > 100:1
                        if compression_ratio > 100:
                            return True
            except:
                pass

        return False

    async def _examine_file_metadata(
        self,
        file_data: bytes,
        mime_type: str
    ) -> List[str]:
        """Examine file metadata for security issues"""

        issues = []

        try:
            if mime_type.startswith('image/'):
                from PIL import Image
                from PIL.ExifTags import TAGS

                image = Image.open(io.BytesIO(file_data))
                exif_data = image._getexif()

                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)

                        # Check for suspicious metadata
                        if isinstance(value, str) and len(value) > 1000:
                            issues.append("Suspicious metadata found in image")
                            break

        except Exception:
            pass

        return issues

# Integration with upload pipeline
async def secure_upload_file(
    file_data: bytes,
    filename: str,
    options: UploadOptions,
    user_context: Dict[str, Any]
) -> UploadResult:
    """Secure file upload with comprehensive validation"""

    security = UploadSecurity()

    # Security validation
    security_result = await security.validate_upload_security(
        file_data, filename, user_context
    )

    if not security_result.is_safe:
        if security_result.requires_manual_review:
            # Queue for manual review
            await queue_for_manual_review(file_data, filename, security_result)
            raise SecurityError("File requires manual security review")
        else:
            raise SecurityError(f"Security validation failed: {security_result.security_issues}")

    # Proceed with regular upload if security checks pass
    return await upload_file(file_data, filename, options)
```

This comprehensive file upload system provides robust handling of various file sizes and types while maintaining security, performance, and compliance requirements specific to educational platforms.