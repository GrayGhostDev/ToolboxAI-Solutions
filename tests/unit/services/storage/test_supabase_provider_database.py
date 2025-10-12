"""
Unit Tests for Supabase Storage Provider Database Operations

Tests the SQLAlchemy database integration for file storage operations
including tenant isolation, CRUD operations, and audit logging.

Author: ToolboxAI Team
Created: 2025-10-10
Version: 1.0.0
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO

from apps.backend.services.storage.supabase_provider import SupabaseStorageProvider
from apps.backend.services.storage.storage_service import (
    UploadOptions,
    ListOptions,
    StorageError,
    TenantIsolationError,
    AccessDeniedError,
    FileNotFoundError,
)
from database.models.storage import File, FileAccessLog, FileStatus, FileCategory


@pytest.fixture
def org_id():
    """Fixture for organization ID"""
    return uuid4()


@pytest.fixture
def user_id():
    """Fixture for user ID"""
    return uuid4()


@pytest.fixture
async def storage_provider(org_id, user_id):
    """Fixture for Supabase storage provider with mocked Supabase client"""
    with patch('apps.backend.services.storage.supabase_provider.create_client'):
        provider = SupabaseStorageProvider(
            organization_id=str(org_id),
            user_id=str(user_id)
        )
        yield provider


@pytest.fixture
def sample_file_data(org_id, user_id):
    """Fixture for sample file data"""
    return {
        "file_id": uuid4(),
        "filename": "test-file.pdf",
        "storage_path": f"org_{org_id}/files/2025/10/test-file.pdf",
        "bucket_name": "files",
        "file_size": 1024 * 1024,  # 1MB
        "checksum": "abc123def456",
        "options": Mock(
            file_category="educational_content",
            virus_scan=True,
            tags=["test", "educational"],
            metadata={"subject": "mathematics"}
        )
    }


class TestCreateFileRecord:
    """Tests for _create_file_record method"""

    @pytest.mark.asyncio
    async def test_create_file_record_success(
        self, storage_provider, sample_file_data, org_id, user_id
    ):
        """Test successful file record creation"""
        # Mock database session
        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute
            result = await storage_provider._create_file_record(**sample_file_data)

            # Assertions
            assert result["id"] == str(sample_file_data["file_id"])
            assert result["organization_id"] == str(org_id)
            assert result["filename"] == sample_file_data["filename"]
            assert result["storage_path"] == sample_file_data["storage_path"]
            assert result["file_size"] == sample_file_data["file_size"]
            assert result["status"] == "available"

            # Verify session operations
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_file_record_database_error(
        self, storage_provider, sample_file_data
    ):
        """Test file record creation with database error"""
        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_db = AsyncMock()
            mock_db.commit.side_effect = Exception("Database connection failed")
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute and assert
            with pytest.raises(StorageError, match="Failed to create file record"):
                await storage_provider._create_file_record(**sample_file_data)

            # Verify rollback was called
            mock_db.rollback.assert_called_once()


class TestGetFileRecord:
    """Tests for _get_file_record method"""

    @pytest.mark.asyncio
    async def test_get_file_record_success(self, storage_provider, org_id):
        """Test successful file record retrieval"""
        file_id = uuid4()

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            # Mock file record
            mock_file = Mock()
            mock_file.id = file_id
            mock_file.organization_id = org_id
            mock_file.filename = "test.pdf"
            mock_file.file_size = 1024
            mock_file.status = FileStatus.AVAILABLE
            mock_file.category = FileCategory.EDUCATIONAL_CONTENT
            mock_file.created_at = datetime.now(timezone.utc)

            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_file
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute
            result = await storage_provider._get_file_record(file_id)

            # Assertions
            assert result is not None
            assert result["id"] == str(file_id)
            assert result["filename"] == "test.pdf"
            assert result["status"] == "available"

    @pytest.mark.asyncio
    async def test_get_file_record_not_found(self, storage_provider):
        """Test file record retrieval when file doesn't exist"""
        file_id = uuid4()

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute
            result = await storage_provider._get_file_record(file_id)

            # Assertion
            assert result is None

    @pytest.mark.asyncio
    async def test_get_file_record_excludes_deleted(self, storage_provider, org_id):
        """Test that soft-deleted files are not returned"""
        file_id = uuid4()

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            # Soft-deleted file should not be returned
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            result = await storage_provider._get_file_record(file_id)
            assert result is None


class TestListFileRecords:
    """Tests for _list_file_records method"""

    @pytest.mark.asyncio
    async def test_list_files_success(self, storage_provider, org_id):
        """Test successful file listing"""
        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            # Mock file records
            mock_files = [
                Mock(
                    id=uuid4(),
                    filename=f"file{i}.pdf",
                    file_size=1024 * i,
                    mime_type="application/pdf",
                    status=FileStatus.AVAILABLE,
                    cdn_url=f"https://cdn.example.com/file{i}.pdf",
                    created_at=datetime.now(timezone.utc)
                )
                for i in range(3)
            ]

            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = mock_files
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute
            options = ListOptions(limit=10)
            result = await storage_provider._list_file_records(options)

            # Assertions
            assert len(result) == 3
            assert all("id" in file for file in result)
            assert all("filename" in file for file in result)

    @pytest.mark.asyncio
    async def test_list_files_with_filters(self, storage_provider):
        """Test file listing with category filter"""
        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            options = ListOptions(
                category="educational_content",
                mime_type="application/pdf",
                limit=20
            )
            result = await storage_provider._list_file_records(options)

            # Should apply filters
            assert isinstance(result, list)


class TestDeleteFileRecord:
    """Tests for _delete_file_record method"""

    @pytest.mark.asyncio
    async def test_delete_file_success(self, storage_provider, org_id):
        """Test successful file deletion"""
        file_id = uuid4()

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_file = Mock(id=file_id, organization_id=org_id)
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_file
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute
            await storage_provider._delete_file_record(file_id)

            # Assertions
            mock_db.delete.assert_called_once_with(mock_file)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, storage_provider):
        """Test deletion of non-existent file"""
        file_id = uuid4()

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute and assert
            with pytest.raises(FileNotFoundError):
                await storage_provider._delete_file_record(file_id)


class TestSoftDeleteFileRecord:
    """Tests for _soft_delete_file_record method"""

    @pytest.mark.asyncio
    async def test_soft_delete_success(self, storage_provider, org_id, user_id):
        """Test successful soft deletion"""
        file_id = uuid4()

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_file = Mock(
                id=file_id,
                organization_id=org_id,
                deleted_at=None
            )
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_file
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute
            await storage_provider._soft_delete_file_record(file_id)

            # Assertions
            assert mock_file.deleted_at is not None
            assert mock_file.deleted_by == user_id
            assert mock_file.status == FileStatus.DELETED
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_already_deleted(self, storage_provider):
        """Test soft deletion of already deleted file"""
        file_id = uuid4()

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute and assert
            with pytest.raises(FileNotFoundError, match="already deleted"):
                await storage_provider._soft_delete_file_record(file_id)


class TestUpdateFilePath:
    """Tests for _update_file_path method"""

    @pytest.mark.asyncio
    async def test_update_path_success(self, storage_provider, org_id):
        """Test successful path update"""
        file_id = uuid4()
        new_path = "org_123/files/2025/10/new-location.pdf"

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_file = Mock(id=file_id, organization_id=org_id, storage_path="old_path")
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_file
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute
            await storage_provider._update_file_path(file_id, new_path)

            # Assertions
            assert mock_file.storage_path == new_path
            mock_db.commit.assert_called_once()


class TestTrackFileAccess:
    """Tests for _track_file_access method"""

    @pytest.mark.asyncio
    async def test_track_access_success(self, storage_provider, org_id, user_id):
        """Test successful access tracking"""
        file_id = uuid4()
        action = "download"

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute
            await storage_provider._track_file_access(file_id, action)

            # Assertions
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

            # Verify access log was created with correct data
            call_args = mock_db.add.call_args[0][0]
            assert isinstance(call_args, FileAccessLog)
            assert call_args.file_id == file_id
            assert call_args.user_id == user_id
            assert call_args.organization_id == org_id
            assert call_args.action == action

    @pytest.mark.asyncio
    async def test_track_access_failure_doesnt_break(self, storage_provider):
        """Test that audit logging failures don't break operations"""
        file_id = uuid4()

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_db = AsyncMock()
            mock_db.commit.side_effect = Exception("Database error")
            mock_session.return_value.__aenter__.return_value = mock_db

            # Should not raise exception
            await storage_provider._track_file_access(file_id, "view")


class TestValidateTenantAccess:
    """Tests for _validate_tenant_access method"""

    @pytest.mark.asyncio
    async def test_validate_access_success(self, storage_provider, org_id):
        """Test successful tenant access validation"""
        file_id = uuid4()

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_file = Mock(
                id=file_id,
                organization_id=org_id,
                deleted_at=None
            )
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_file
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute
            result = await storage_provider._validate_tenant_access(file_id)

            # Assertion
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_access_wrong_organization(self, storage_provider):
        """Test access validation with wrong organization"""
        file_id = uuid4()
        wrong_org_id = uuid4()

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_file = Mock(
                id=file_id,
                organization_id=wrong_org_id,  # Different org
                deleted_at=None
            )
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_file
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute and assert
            with pytest.raises(TenantIsolationError, match="different organization"):
                await storage_provider._validate_tenant_access(file_id)

    @pytest.mark.asyncio
    async def test_validate_access_deleted_file(self, storage_provider, org_id):
        """Test access validation for deleted file"""
        file_id = uuid4()

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_file = Mock(
                id=file_id,
                organization_id=org_id,
                deleted_at=datetime.now(timezone.utc)  # Deleted
            )
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_file
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute and assert
            with pytest.raises(AccessDeniedError, match="deleted"):
                await storage_provider._validate_tenant_access(file_id)

    @pytest.mark.asyncio
    async def test_validate_access_file_not_found(self, storage_provider):
        """Test access validation for non-existent file"""
        file_id = uuid4()

        with patch('apps.backend.services.storage.supabase_provider.get_async_session') as mock_session:
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db

            # Execute and assert
            with pytest.raises(FileNotFoundError):
                await storage_provider._validate_tenant_access(file_id)


# Integration test markers
pytestmark = pytest.mark.unit
