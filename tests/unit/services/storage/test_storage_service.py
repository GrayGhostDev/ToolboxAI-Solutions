"""
Unit Tests for Storage Service

Tests abstract storage service functionality including upload, download, and file management.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock
from uuid import uuid4, UUID
from io import BytesIO

from apps.backend.services.storage.storage_service import (
    StorageService,
    UploadProgress,
    UploadStatus,
    UploadOptions,
    UploadResult,
    DownloadOptions,
    DownloadResult,
    DownloadPermission,
    ListOptions,
    FileInfo,
    StorageError,
    TenantIsolationError,
    QuotaExceededError,
    FileNotFoundError,
    AccessDeniedError,
)


# Mock implementation of StorageService for testing
class MockStorageService(StorageService):
    """Mock storage service for testing abstract class functionality."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._files = {}

    async def upload_file(self, file_data, filename, options=None):
        file_id = uuid4()
        storage_path = self._generate_storage_path(filename)
        checksum = self._calculate_checksum(
            file_data if isinstance(file_data, bytes) else file_data.read()
        )

        return UploadResult(
            file_id=file_id,
            upload_id=str(uuid4()),
            storage_path=storage_path,
            file_size=len(file_data) if isinstance(file_data, bytes) else 0,
            checksum=checksum,
            status=UploadStatus.COMPLETED
        )

    async def upload_file_multipart(self, file_stream, filename, total_size, options=None):
        upload_id = str(uuid4())
        bytes_uploaded = 0

        async for chunk in file_stream:
            bytes_uploaded += len(chunk)
            progress = self._update_upload_progress(
                upload_id, UploadStatus.UPLOADING, bytes_uploaded, total_size
            )
            yield progress

        file_id = uuid4()
        yield UploadResult(
            file_id=file_id,
            upload_id=upload_id,
            storage_path=self._generate_storage_path(filename),
            file_size=total_size,
            status=UploadStatus.COMPLETED
        )

    async def download_file(self, file_id, options=None):
        return DownloadResult(
            file_id=file_id,
            file_url=f"https://storage.example.com/{file_id}",
            content_type="application/octet-stream",
            content_length=1024
        )

    async def get_file_stream(self, file_id, chunk_size=8192):
        data = b"test data"
        yield data

    async def delete_file(self, file_id, permanent=False):
        return True

    async def list_files(self, options=None):
        return []

    async def get_file_info(self, file_id):
        return FileInfo(
            file_id=file_id,
            filename="test.txt",
            original_filename="test.txt",
            file_size=1024,
            mime_type="text/plain",
            storage_path="/path/to/test.txt"
        )

    async def generate_signed_url(self, file_id, expires_in=3600, permission="read"):
        return f"https://storage.example.com/signed/{file_id}"

    async def copy_file(self, source_file_id, destination_path, options=None):
        return UploadResult(
            file_id=uuid4(),
            upload_id=str(uuid4()),
            storage_path=destination_path,
            status=UploadStatus.COMPLETED
        )

    async def move_file(self, file_id, new_path):
        return True


@pytest.fixture
def storage_service():
    """Create mock storage service instance."""
    return MockStorageService(
        organization_id="org_123",
        user_id="user_456"
    )


class TestStorageServiceInitialization:
    """Test storage service initialization."""

    def test_init_with_organization_and_user(self):
        """Test initialization with organization and user context."""
        service = MockStorageService(
            organization_id="org_123",
            user_id="user_456"
        )

        assert service.organization_id == "org_123"
        assert service.user_id == "user_456"

    def test_init_without_context(self):
        """Test initialization without tenant context."""
        service = MockStorageService()

        assert service.organization_id is None
        assert service.user_id is None

    def test_set_tenant_context(self, storage_service):
        """Test updating tenant context."""
        storage_service.set_tenant_context(
            organization_id="org_new",
            user_id="user_new"
        )

        assert storage_service.organization_id == "org_new"
        assert storage_service.user_id == "user_new"


class TestUploadProgress:
    """Test upload progress tracking."""

    def test_upload_progress_percentage(self):
        """Test progress percentage calculation."""
        progress = UploadProgress(
            upload_id="test_upload",
            status=UploadStatus.UPLOADING,
            bytes_uploaded=50,
            total_bytes=100
        )

        assert progress.progress_percentage == 50.0

    def test_upload_progress_zero_total(self):
        """Test progress with zero total bytes."""
        progress = UploadProgress(
            upload_id="test_upload",
            status=UploadStatus.UPLOADING,
            bytes_uploaded=0,
            total_bytes=0
        )

        assert progress.progress_percentage == 0.0

    def test_upload_progress_complete(self):
        """Test complete status check."""
        progress = UploadProgress(
            upload_id="test_upload",
            status=UploadStatus.COMPLETED
        )

        assert progress.is_complete is True
        assert progress.has_failed is False

    def test_upload_progress_failed(self):
        """Test failed status check."""
        progress = UploadProgress(
            upload_id="test_upload",
            status=UploadStatus.FAILED,
            error_message="Upload failed"
        )

        assert progress.has_failed is True
        assert progress.is_complete is False


class TestFileUpload:
    """Test file upload functionality."""

    @pytest.mark.asyncio
    async def test_upload_file_bytes(self, storage_service):
        """Test uploading file as bytes."""
        file_data = b"test file content"
        filename = "test.txt"

        result = await storage_service.upload_file(file_data, filename)

        assert isinstance(result, UploadResult)
        assert result.file_id is not None
        assert result.storage_path is not None
        assert result.status == UploadStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_upload_file_with_options(self, storage_service):
        """Test uploading file with custom options."""
        file_data = b"test content"
        options = UploadOptions(
            file_category="documents",
            title="Test Document",
            tags=["test", "document"]
        )

        result = await storage_service.upload_file(
            file_data,
            "document.pdf",
            options=options
        )

        assert result.status == UploadStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_upload_file_calculates_checksum(self, storage_service):
        """Test that file checksum is calculated."""
        file_data = b"test content"

        result = await storage_service.upload_file(file_data, "test.txt")

        assert result.checksum is not None
        assert len(result.checksum) == 64  # SHA256 hex length

    @pytest.mark.asyncio
    async def test_upload_multipart_tracks_progress(self, storage_service):
        """Test multipart upload with progress tracking."""
        async def file_chunks():
            chunks = [b"chunk1", b"chunk2", b"chunk3"]
            for chunk in chunks:
                yield chunk

        total_size = len(b"chunk1chunk2chunk3")
        results = []

        async for item in storage_service.upload_file_multipart(
            file_chunks(), "large_file.dat", total_size
        ):
            results.append(item)

        # Should have progress updates + final result
        assert len(results) > 0
        # Last item should be UploadResult
        assert isinstance(results[-1], UploadResult)
        # Other items should be UploadProgress
        for item in results[:-1]:
            assert isinstance(item, UploadProgress)


class TestFileDownload:
    """Test file download functionality."""

    @pytest.mark.asyncio
    async def test_download_file(self, storage_service):
        """Test downloading file."""
        file_id = uuid4()

        result = await storage_service.download_file(file_id)

        assert isinstance(result, DownloadResult)
        assert result.file_id == file_id
        assert result.file_url is not None

    @pytest.mark.asyncio
    async def test_download_file_with_options(self, storage_service):
        """Test downloading with custom options."""
        file_id = uuid4()
        options = DownloadOptions(
            include_metadata=True,
            signed_url_expires_in=7200
        )

        result = await storage_service.download_file(file_id, options=options)

        assert result.file_url is not None

    @pytest.mark.asyncio
    async def test_get_file_stream(self, storage_service):
        """Test streaming file content."""
        file_id = uuid4()
        chunks = []

        async for chunk in storage_service.get_file_stream(file_id):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert all(isinstance(chunk, bytes) for chunk in chunks)


class TestFileManagement:
    """Test file management operations."""

    @pytest.mark.asyncio
    async def test_delete_file(self, storage_service):
        """Test file deletion."""
        file_id = uuid4()

        result = await storage_service.delete_file(file_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_file_permanent(self, storage_service):
        """Test permanent file deletion."""
        file_id = uuid4()

        result = await storage_service.delete_file(file_id, permanent=True)

        assert result is True

    @pytest.mark.asyncio
    async def test_list_files(self, storage_service):
        """Test listing files."""
        result = await storage_service.list_files()

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_files_with_options(self, storage_service):
        """Test listing files with filter options."""
        options = ListOptions(
            file_types=["image/png"],
            limit=50,
            sort_by="created_at"
        )

        result = await storage_service.list_files(options=options)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_file_info(self, storage_service):
        """Test getting file information."""
        file_id = uuid4()

        info = await storage_service.get_file_info(file_id)

        assert isinstance(info, FileInfo)
        assert info.file_id == file_id

    @pytest.mark.asyncio
    async def test_copy_file(self, storage_service):
        """Test file copy operation."""
        source_id = uuid4()
        dest_path = "/new/path/copied_file.txt"

        result = await storage_service.copy_file(source_id, dest_path)

        assert isinstance(result, UploadResult)
        assert result.storage_path == dest_path

    @pytest.mark.asyncio
    async def test_move_file(self, storage_service):
        """Test file move operation."""
        file_id = uuid4()
        new_path = "/new/location/file.txt"

        result = await storage_service.move_file(file_id, new_path)

        assert result is True


class TestSignedURLs:
    """Test signed URL generation."""

    @pytest.mark.asyncio
    async def test_generate_signed_url(self, storage_service):
        """Test generating signed URL."""
        file_id = uuid4()

        url = await storage_service.generate_signed_url(file_id)

        assert isinstance(url, str)
        assert len(url) > 0
        assert "signed" in url

    @pytest.mark.asyncio
    async def test_generate_signed_url_with_custom_expiry(self, storage_service):
        """Test signed URL with custom expiration."""
        file_id = uuid4()

        url = await storage_service.generate_signed_url(
            file_id,
            expires_in=7200
        )

        assert isinstance(url, str)

    @pytest.mark.asyncio
    async def test_generate_signed_url_with_write_permission(self, storage_service):
        """Test signed URL with write permission."""
        file_id = uuid4()

        url = await storage_service.generate_signed_url(
            file_id,
            permission="write"
        )

        assert isinstance(url, str)


class TestStoragePaths:
    """Test storage path generation."""

    def test_generate_storage_path(self, storage_service):
        """Test storage path generation."""
        filename = "test_document.pdf"

        path = storage_service._generate_storage_path(filename)

        assert isinstance(path, str)
        assert "org_123" in path  # Organization ID
        assert ".pdf" in path  # File extension preserved

    def test_generate_storage_path_without_timestamp(self, storage_service):
        """Test path generation without timestamp."""
        filename = "file.txt"

        path = storage_service._generate_storage_path(
            filename,
            include_timestamp=False
        )

        assert isinstance(path, str)
        assert "file" in path or ".txt" in path

    def test_generate_storage_path_with_category(self, storage_service):
        """Test path generation with file category."""
        filename = "image.png"
        category = "user_uploads"

        path = storage_service._generate_storage_path(
            filename,
            file_category=category
        )

        assert category in path


class TestChecksums:
    """Test checksum calculation."""

    def test_calculate_checksum(self, storage_service):
        """Test SHA256 checksum calculation."""
        data = b"test data for checksum"

        checksum = storage_service._calculate_checksum(data)

        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length

    def test_calculate_checksum_deterministic(self, storage_service):
        """Test that same data produces same checksum."""
        data = b"consistent data"

        checksum1 = storage_service._calculate_checksum(data)
        checksum2 = storage_service._calculate_checksum(data)

        assert checksum1 == checksum2

    def test_calculate_checksum_different_data(self, storage_service):
        """Test that different data produces different checksums."""
        checksum1 = storage_service._calculate_checksum(b"data1")
        checksum2 = storage_service._calculate_checksum(b"data2")

        assert checksum1 != checksum2


class TestTenantIsolation:
    """Test tenant isolation features."""

    @pytest.mark.asyncio
    async def test_tenant_access_validation(self, storage_service):
        """Test tenant access validation."""
        file_id = uuid4()

        result = await storage_service._validate_tenant_access(file_id)

        assert isinstance(result, bool)

    def test_storage_path_includes_organization(self):
        """Test that storage paths include organization ID."""
        service = MockStorageService(organization_id="org_456")

        path = service._generate_storage_path("file.txt")

        assert "org_456" in path

    def test_storage_without_organization(self):
        """Test storage path without organization."""
        service = MockStorageService()  # No organization

        path = service._generate_storage_path("file.txt")

        # Should still generate valid path
        assert isinstance(path, str)
        assert "org_" not in path


class TestProgressTracking:
    """Test upload progress tracking."""

    def test_update_upload_progress(self, storage_service):
        """Test updating upload progress."""
        upload_id = "test_upload_123"

        progress = storage_service._update_upload_progress(
            upload_id,
            UploadStatus.UPLOADING,
            bytes_uploaded=500,
            total_bytes=1000
        )

        assert progress.upload_id == upload_id
        assert progress.status == UploadStatus.UPLOADING
        assert progress.bytes_uploaded == 500
        assert progress.total_bytes == 1000

    def test_get_upload_progress(self, storage_service):
        """Test retrieving upload progress."""
        upload_id = "test_upload_456"

        # Create progress
        storage_service._update_upload_progress(
            upload_id,
            UploadStatus.UPLOADING,
            bytes_uploaded=100,
            total_bytes=200
        )

        # Retrieve progress
        progress = storage_service.get_upload_progress(upload_id)

        assert progress is not None
        assert progress.upload_id == upload_id

    def test_get_nonexistent_upload_progress(self, storage_service):
        """Test retrieving non-existent upload progress."""
        result = storage_service.get_upload_progress("nonexistent")

        assert result is None


class TestStorageErrors:
    """Test storage error classes."""

    def test_storage_error_basic(self):
        """Test basic storage error."""
        error = StorageError("Test error")

        assert error.message == "Test error"
        assert error.error_code is None

    def test_storage_error_with_code(self):
        """Test storage error with code."""
        error = StorageError(
            "Test error",
            error_code="ERR_001",
            details={"file_id": "123"}
        )

        assert error.message == "Test error"
        assert error.error_code == "ERR_001"
        assert error.details["file_id"] == "123"

    def test_tenant_isolation_error(self):
        """Test tenant isolation error."""
        error = TenantIsolationError("Access denied")

        assert isinstance(error, StorageError)

    def test_quota_exceeded_error(self):
        """Test quota exceeded error."""
        error = QuotaExceededError("Storage quota exceeded")

        assert isinstance(error, StorageError)

    def test_file_not_found_error(self):
        """Test file not found error."""
        error = FileNotFoundError("File not found")

        assert isinstance(error, StorageError)

    def test_access_denied_error(self):
        """Test access denied error."""
        error = AccessDeniedError("Access denied")

        assert isinstance(error, StorageError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
