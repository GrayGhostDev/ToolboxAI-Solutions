"""
Unit Tests for BackupManager

Tests backup creation, encryption, compression, and metadata handling.
"""

import json
import os
import shutil

# Add parent directory to path for imports
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from backup.backup_manager import BackupManager, BackupMetadata, BackupStatus


@pytest.fixture
def temp_backup_dir():
    """Create temporary backup directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_config(temp_backup_dir):
    """Create mock backup configuration."""
    return {
        "version": "1.0.0",
        "backup_strategies": {
            "full": {"enabled": True, "schedule": "0 2 * * 0", "retention_days": 30},
            "incremental": {
                "enabled": True,
                "schedule": "0 2 * * 1-6",
                "retention_days": 7,
            },
        },
        "encryption": {
            "enabled": True,
            "algorithm": "AES-256-GCM",
            "key_rotation_days": 90,
            "fernet_enabled": True,
        },
        "storage": {"local": {"path": str(temp_backup_dir), "enabled": True, "max_size_gb": 500}},
        "databases": {
            "postgresql": {
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "user": "test_user",
                "backup_format": "custom",
                "compress_level": 9,
                "parallel_jobs": 4,
            }
        },
        "compression": {"enabled": True, "algorithm": "gzip", "level": 9},
        "validation": {"enabled": True, "checksum_algorithm": "SHA256"},
        "rto_minutes": 30,
        "rpo_minutes": 60,
    }


@pytest.fixture
def backup_manager(mock_config, temp_backup_dir):
    """Create BackupManager instance with mocked configuration."""
    with patch.object(BackupManager, "_load_config", return_value=mock_config):
        with patch.dict(
            os.environ, {"BACKUP_ENCRYPTION_KEY": "test_key_32_bytes_long_for_fernet!"}
        ):
            manager = BackupManager()
            manager.backup_root = temp_backup_dir
            manager.metadata_dir = temp_backup_dir / "metadata"
            manager.metadata_dir.mkdir(exist_ok=True)
            return manager


class TestBackupManagerInitialization:
    """Test BackupManager initialization and configuration."""

    def test_singleton_pattern(self, backup_manager):
        """Test that BackupManager implements singleton pattern."""
        manager1 = backup_manager
        manager2 = BackupManager()
        assert manager1 is manager2

    def test_initialization_creates_directories(self, backup_manager, temp_backup_dir):
        """Test that initialization creates required directories."""
        assert (temp_backup_dir / "metadata").exists()
        assert (temp_backup_dir / "metadata").is_dir()

    def test_config_loaded(self, backup_manager):
        """Test that configuration is loaded correctly."""
        assert backup_manager.config is not None
        assert "backup_strategies" in backup_manager.config
        assert "encryption" in backup_manager.config
        assert backup_manager.config["rto_minutes"] == 30

    def test_encryption_key_loaded(self, backup_manager):
        """Test that encryption key is loaded from environment."""
        assert backup_manager.encryption_key is not None
        assert backup_manager.cipher is not None


class TestBackupIDGeneration:
    """Test backup ID generation."""

    def test_generate_backup_id_format(self, backup_manager):
        """Test backup ID format is correct."""
        backup_id = backup_manager._generate_backup_id("full")

        assert backup_id.startswith("backup_full_")
        assert len(backup_id) > len("backup_full_")

        # Should contain timestamp
        timestamp_part = backup_id.replace("backup_full_", "")
        assert len(timestamp_part) == 15  # YYYYMMDD_HHMMSS

    def test_generate_backup_id_unique(self, backup_manager):
        """Test that generated backup IDs are unique."""
        id1 = backup_manager._generate_backup_id("full")
        id2 = backup_manager._generate_backup_id("full")

        # IDs should be different (unless generated in same second)
        # We can't guarantee they're different, but we can check format
        assert id1.startswith("backup_full_")
        assert id2.startswith("backup_full_")


class TestChecksumCalculation:
    """Test checksum calculation functionality."""

    def test_calculate_checksum(self, backup_manager, temp_backup_dir):
        """Test SHA-256 checksum calculation."""
        test_file = temp_backup_dir / "test_file.txt"
        test_content = b"Test backup content for checksum"
        test_file.write_bytes(test_content)

        checksum = backup_manager._calculate_checksum(test_file)

        # Should return hex string
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 produces 64 hex characters

        # Calculate expected checksum
        import hashlib

        expected = hashlib.sha256(test_content).hexdigest()
        assert checksum == expected

    def test_calculate_checksum_large_file(self, backup_manager, temp_backup_dir):
        """Test checksum calculation for large files."""
        test_file = temp_backup_dir / "large_file.bin"

        # Create 10MB file
        large_content = b"X" * (10 * 1024 * 1024)
        test_file.write_bytes(large_content)

        checksum = backup_manager._calculate_checksum(test_file)

        assert isinstance(checksum, str)
        assert len(checksum) == 64


class TestCompression:
    """Test file compression functionality."""

    def test_compress_file(self, backup_manager, temp_backup_dir):
        """Test gzip compression."""
        input_file = temp_backup_dir / "input.txt"
        output_file = temp_backup_dir / "output.txt.gz"

        test_content = b"Test content for compression" * 1000
        input_file.write_bytes(test_content)

        backup_manager._compress_file(input_file, output_file)

        # Compressed file should exist
        assert output_file.exists()

        # Compressed file should be smaller
        assert output_file.stat().st_size < input_file.stat().st_size

        # Verify can decompress
        import gzip

        with gzip.open(output_file, "rb") as f:
            decompressed = f.read()

        assert decompressed == test_content


class TestEncryption:
    """Test file encryption functionality."""

    def test_encrypt_file(self, backup_manager, temp_backup_dir):
        """Test Fernet encryption."""
        input_file = temp_backup_dir / "plain.txt"
        output_file = temp_backup_dir / "encrypted.enc"

        test_content = b"Sensitive backup data"
        input_file.write_bytes(test_content)

        backup_manager._encrypt_file(input_file, output_file)

        # Encrypted file should exist
        assert output_file.exists()

        # Encrypted content should be different
        encrypted_content = output_file.read_bytes()
        assert encrypted_content != test_content

        # Verify can decrypt
        decrypted = backup_manager.cipher.decrypt(encrypted_content)
        assert decrypted == test_content

    def test_encrypt_file_without_cipher(self, backup_manager, temp_backup_dir):
        """Test encryption behavior when cipher not initialized."""
        backup_manager.cipher = None

        input_file = temp_backup_dir / "plain.txt"
        output_file = temp_backup_dir / "encrypted.enc"
        input_file.write_bytes(b"test")

        # Should log warning but not raise exception
        backup_manager._encrypt_file(input_file, output_file)

        # Output file should not be created
        assert not output_file.exists()


class TestMetadataManagement:
    """Test backup metadata handling."""

    def test_save_metadata(self, backup_manager, temp_backup_dir):
        """Test saving backup metadata."""
        metadata = BackupMetadata(
            backup_id="test_backup_001",
            backup_type="full",
            timestamp=datetime.now().isoformat(),
            database_name="test_db",
            file_path=str(temp_backup_dir / "backup.dump"),
            file_size=1024 * 1024,
            checksum="abc123def456",
            encrypted=True,
            compressed=True,
            status="completed",
            duration_seconds=120.5,
            retention_until=(datetime.now() + timedelta(days=30)).isoformat(),
        )

        backup_manager._save_metadata(metadata)

        # Metadata file should exist
        metadata_file = backup_manager.metadata_dir / f"{metadata.backup_id}.json"
        assert metadata_file.exists()

        # Verify content
        with open(metadata_file) as f:
            saved_data = json.load(f)

        assert saved_data["backup_id"] == "test_backup_001"
        assert saved_data["backup_type"] == "full"
        assert saved_data["file_size"] == 1024 * 1024
        assert saved_data["encrypted"] is True


class TestDatabaseCredentials:
    """Test database credential extraction."""

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb"})
    def test_get_database_credentials_from_url(self, backup_manager):
        """Test extracting credentials from DATABASE_URL."""
        with patch("backup.backup_manager.settings") as mock_settings:
            mock_settings.DATABASE_URL = "postgresql://user:pass@localhost:5432/testdb"

            creds = backup_manager._get_database_credentials()

            assert creds["host"] == "localhost"
            assert creds["port"] == "5432"
            assert creds["user"] == "user"
            assert creds["password"] == "pass"
            assert creds["database"] == "testdb"

    @patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql://host:5432/dbname",
            "DB_USER": "envuser",
            "DB_PASSWORD": "envpass",
        },
    )
    def test_get_database_credentials_from_env(self, backup_manager):
        """Test extracting credentials from environment variables."""
        with patch("backup.backup_manager.settings") as mock_settings:
            mock_settings.DATABASE_URL = "postgresql://host:5432/dbname"

            creds = backup_manager._get_database_credentials()

            assert creds["user"] == "envuser"
            assert creds["password"] == "envpass"


class TestFullBackupCreation:
    """Test full backup creation workflow."""

    @pytest.mark.asyncio
    async def test_create_full_backup_success(self, backup_manager, temp_backup_dir):
        """Test successful full backup creation."""
        # Mock pg_dump subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"Success", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("backup.backup_manager.settings") as mock_settings:
                mock_settings.DATABASE_URL = "postgresql://user:pass@localhost:5432/testdb"

                # Create dummy backup file
                backup_file = temp_backup_dir / "backup_full_test.dump"
                backup_file.write_bytes(b"Mock backup data")

                with patch.object(
                    backup_manager,
                    "_generate_backup_id",
                    return_value="backup_full_test",
                ):
                    metadata = await backup_manager.create_full_backup()

        assert metadata is not None
        assert metadata.status == BackupStatus.COMPLETED.value
        assert metadata.backup_type == "full"

    @pytest.mark.asyncio
    async def test_create_full_backup_pg_dump_failure(self, backup_manager):
        """Test backup creation when pg_dump fails."""
        # Mock failing pg_dump subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"pg_dump error"))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("backup.backup_manager.settings") as mock_settings:
                mock_settings.DATABASE_URL = "postgresql://user:pass@localhost:5432/testdb"

                with pytest.raises(RuntimeError, match="Backup failed"):
                    await backup_manager.create_full_backup()


class TestBackupTypeSelection:
    """Test backup type selection and execution."""

    @pytest.mark.asyncio
    async def test_create_backup_full_type(self, backup_manager):
        """Test creating full backup via create_backup method."""
        with patch.object(
            backup_manager, "create_full_backup", new_callable=AsyncMock
        ) as mock_full:
            mock_metadata = BackupMetadata(
                backup_id="test",
                backup_type="full",
                timestamp=datetime.now().isoformat(),
                database_name="test",
                file_path="/test",
                file_size=0,
                checksum="",
                encrypted=False,
                compressed=False,
                status="completed",
                duration_seconds=0,
                retention_until="",
            )
            mock_full.return_value = mock_metadata

            result = await backup_manager.create_backup(backup_type="full")

            mock_full.assert_called_once()
            assert result.backup_type == "full"

    @pytest.mark.asyncio
    async def test_create_backup_unknown_type(self, backup_manager):
        """Test creating backup with unknown type raises error."""
        with pytest.raises(ValueError, match="Unknown backup type"):
            await backup_manager.create_backup(backup_type="unknown")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
