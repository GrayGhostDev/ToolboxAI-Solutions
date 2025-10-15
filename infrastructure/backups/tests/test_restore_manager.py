"""
Unit Tests for RestoreManager

Tests backup restoration, decryption, decompression, and validation.
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import tempfile
import shutil
import gzip

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from restore.restore_manager import (
    RestoreManager,
    RestoreResult
)


@pytest.fixture
def temp_restore_dir():
    """Create temporary restore directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_config(temp_restore_dir):
    """Create mock restore configuration."""
    return {
        "version": "1.0.0",
        "encryption": {
            "enabled": True,
            "algorithm": "AES-256-GCM"
        },
        "storage": {
            "local": {
                "path": str(temp_restore_dir),
                "enabled": True
            }
        },
        "databases": {
            "postgresql": {
                "host": "localhost",
                "port": 5432,
                "parallel_jobs": 4
            }
        }
    }


@pytest.fixture
def sample_backup_metadata(temp_restore_dir):
    """Create sample backup metadata for testing."""
    backup_file = temp_restore_dir / "backup_test.dump"
    backup_file.write_bytes(b"Mock backup data")

    return {
        "backup_id": "backup_test_20250110_120000",
        "backup_type": "full",
        "timestamp": "2025-01-10T12:00:00",
        "database_name": "test_db",
        "file_path": str(backup_file),
        "file_size": backup_file.stat().st_size,
        "checksum": "abc123def456",
        "encrypted": False,
        "compressed": False,
        "status": "completed",
        "duration_seconds": 120.5,
        "retention_until": "2025-02-10T12:00:00"
    }


@pytest.fixture
def restore_manager(mock_config, temp_restore_dir):
    """Create RestoreManager instance with mocked configuration."""
    with patch.object(RestoreManager, '_load_config', return_value=mock_config):
        with patch.dict(os.environ, {'BACKUP_ENCRYPTION_KEY': 'test_key_32_bytes_long_for_fernet!'}):
            manager = RestoreManager()
            manager.backup_root = temp_restore_dir
            manager.metadata_dir = temp_restore_dir / "metadata"
            manager.metadata_dir.mkdir(exist_ok=True)
            manager.temp_dir = temp_restore_dir / "temp_restore"
            manager.temp_dir.mkdir(exist_ok=True)
            return manager


class TestRestoreManagerInitialization:
    """Test RestoreManager initialization and configuration."""

    def test_singleton_pattern(self, restore_manager):
        """Test that RestoreManager implements singleton pattern."""
        manager1 = restore_manager
        manager2 = RestoreManager()
        assert manager1 is manager2

    def test_initialization_creates_directories(self, restore_manager, temp_restore_dir):
        """Test that initialization creates required directories."""
        assert (temp_restore_dir / "metadata").exists()
        assert (temp_restore_dir / "temp_restore").exists()

    def test_config_loaded(self, restore_manager):
        """Test that configuration is loaded correctly."""
        assert restore_manager.config is not None
        assert "encryption" in restore_manager.config
        assert "storage" in restore_manager.config

    def test_encryption_key_loaded(self, restore_manager):
        """Test that encryption key is loaded from environment."""
        assert restore_manager.encryption_key is not None
        assert restore_manager.cipher is not None


class TestMetadataLoading:
    """Test backup metadata loading."""

    def test_load_metadata_success(self, restore_manager, sample_backup_metadata):
        """Test successfully loading backup metadata."""
        backup_id = sample_backup_metadata["backup_id"]
        metadata_file = restore_manager.metadata_dir / f"{backup_id}.json"

        with open(metadata_file, 'w') as f:
            json.dump(sample_backup_metadata, f)

        metadata = restore_manager._load_metadata(backup_id)

        assert metadata["backup_id"] == backup_id
        assert metadata["backup_type"] == "full"
        assert metadata["database_name"] == "test_db"

    def test_load_metadata_not_found(self, restore_manager):
        """Test loading metadata for non-existent backup."""
        with pytest.raises(FileNotFoundError):
            restore_manager._load_metadata("nonexistent_backup")


class TestListAvailableBackups:
    """Test listing available backups."""

    def test_list_available_backups_empty(self, restore_manager):
        """Test listing when no backups available."""
        backups = restore_manager.list_available_backups()
        assert backups == []

    def test_list_available_backups_with_data(self, restore_manager, sample_backup_metadata):
        """Test listing multiple backups."""
        # Create multiple backup metadata files
        for i in range(3):
            backup_id = f"backup_test_{i}"
            metadata = sample_backup_metadata.copy()
            metadata["backup_id"] = backup_id
            metadata["timestamp"] = f"2025-01-{10+i:02d}T12:00:00"

            metadata_file = restore_manager.metadata_dir / f"{backup_id}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)

        backups = restore_manager.list_available_backups()

        assert len(backups) == 3
        # Should be sorted by timestamp (newest first)
        assert backups[0]["backup_id"] == "backup_test_2"
        assert backups[1]["backup_id"] == "backup_test_1"
        assert backups[2]["backup_id"] == "backup_test_0"

    def test_list_available_backups_filters_incomplete(self, restore_manager, sample_backup_metadata):
        """Test that failed backups are not listed."""
        # Create completed backup
        metadata1 = sample_backup_metadata.copy()
        metadata1["backup_id"] = "backup_completed"
        metadata1["status"] = "completed"

        metadata_file1 = restore_manager.metadata_dir / "backup_completed.json"
        with open(metadata_file1, 'w') as f:
            json.dump(metadata1, f)

        # Create failed backup
        metadata2 = sample_backup_metadata.copy()
        metadata2["backup_id"] = "backup_failed"
        metadata2["status"] = "failed"

        metadata_file2 = restore_manager.metadata_dir / "backup_failed.json"
        with open(metadata_file2, 'w') as f:
            json.dump(metadata2, f)

        backups = restore_manager.list_available_backups()

        assert len(backups) == 1
        assert backups[0]["backup_id"] == "backup_completed"


class TestBackupValidation:
    """Test backup integrity validation."""

    def test_validate_backup_success(self, restore_manager, sample_backup_metadata, temp_restore_dir):
        """Test successful backup validation."""
        # Create backup file with known content
        backup_file = temp_restore_dir / "backup_test.dump"
        test_content = b"Test backup content"
        backup_file.write_bytes(test_content)

        # Calculate correct checksum
        import hashlib
        correct_checksum = hashlib.sha256(test_content).hexdigest()

        metadata = sample_backup_metadata.copy()
        metadata["file_path"] = str(backup_file)
        metadata["checksum"] = correct_checksum

        result = restore_manager._validate_backup(metadata)

        assert result is True

    def test_validate_backup_checksum_mismatch(self, restore_manager, sample_backup_metadata, temp_restore_dir):
        """Test validation failure with checksum mismatch."""
        backup_file = temp_restore_dir / "backup_test.dump"
        backup_file.write_bytes(b"Test backup content")

        metadata = sample_backup_metadata.copy()
        metadata["file_path"] = str(backup_file)
        metadata["checksum"] = "wrong_checksum"

        result = restore_manager._validate_backup(metadata)

        assert result is False

    def test_validate_backup_file_not_found(self, restore_manager, sample_backup_metadata):
        """Test validation failure when backup file doesn't exist."""
        metadata = sample_backup_metadata.copy()
        metadata["file_path"] = "/nonexistent/backup.dump"

        result = restore_manager._validate_backup(metadata)

        assert result is False


class TestDecryption:
    """Test file decryption functionality."""

    def test_decrypt_file_success(self, restore_manager, temp_restore_dir):
        """Test successful file decryption."""
        input_file = temp_restore_dir / "encrypted.enc"
        output_file = temp_restore_dir / "decrypted.txt"

        test_content = b"Encrypted backup data"
        encrypted_data = restore_manager.cipher.encrypt(test_content)
        input_file.write_bytes(encrypted_data)

        restore_manager._decrypt_file(input_file, output_file)

        assert output_file.exists()
        decrypted_content = output_file.read_bytes()
        assert decrypted_content == test_content

    def test_decrypt_file_without_cipher(self, restore_manager, temp_restore_dir):
        """Test decryption fails when cipher not initialized."""
        restore_manager.cipher = None

        input_file = temp_restore_dir / "encrypted.enc"
        output_file = temp_restore_dir / "decrypted.txt"
        input_file.write_bytes(b"fake encrypted data")

        with pytest.raises(RuntimeError, match="Encryption key not available"):
            restore_manager._decrypt_file(input_file, output_file)

    def test_decrypt_file_invalid_data(self, restore_manager, temp_restore_dir):
        """Test decryption fails with invalid encrypted data."""
        input_file = temp_restore_dir / "encrypted.enc"
        output_file = temp_restore_dir / "decrypted.txt"
        input_file.write_bytes(b"invalid encrypted data")

        with pytest.raises(RuntimeError, match="Invalid encryption key"):
            restore_manager._decrypt_file(input_file, output_file)


class TestDecompression:
    """Test file decompression functionality."""

    def test_decompress_file_success(self, restore_manager, temp_restore_dir):
        """Test successful file decompression."""
        input_file = temp_restore_dir / "compressed.gz"
        output_file = temp_restore_dir / "decompressed.txt"

        test_content = b"Compressed backup data"

        # Create compressed file
        with gzip.open(input_file, 'wb') as f:
            f.write(test_content)

        restore_manager._decompress_file(input_file, output_file)

        assert output_file.exists()
        decompressed_content = output_file.read_bytes()
        assert decompressed_content == test_content


class TestPrepareBackupFile:
    """Test backup file preparation (decryption + decompression)."""

    def test_prepare_backup_file_plain(self, restore_manager, sample_backup_metadata, temp_restore_dir):
        """Test preparing plain (unencrypted, uncompressed) backup file."""
        metadata = sample_backup_metadata.copy()
        metadata["encrypted"] = False
        metadata["compressed"] = False

        prepared_file = restore_manager._prepare_backup_file(metadata)

        # Should return original file path
        assert prepared_file == Path(metadata["file_path"])

    def test_prepare_backup_file_encrypted(self, restore_manager, sample_backup_metadata, temp_restore_dir):
        """Test preparing encrypted backup file."""
        # Create encrypted backup
        backup_file = temp_restore_dir / "backup_encrypted.enc"
        test_content = b"Backup data"
        encrypted_data = restore_manager.cipher.encrypt(test_content)
        backup_file.write_bytes(encrypted_data)

        metadata = sample_backup_metadata.copy()
        metadata["file_path"] = str(backup_file)
        metadata["encrypted"] = True
        metadata["compressed"] = False

        prepared_file = restore_manager._prepare_backup_file(metadata)

        # Should create decrypted file
        assert prepared_file.exists()
        assert prepared_file != backup_file

        # Verify content
        content = prepared_file.read_bytes()
        assert content == test_content

    def test_prepare_backup_file_compressed(self, restore_manager, sample_backup_metadata, temp_restore_dir):
        """Test preparing compressed backup file."""
        # Create compressed backup
        backup_file = temp_restore_dir / "backup_compressed.gz"
        test_content = b"Backup data"

        with gzip.open(backup_file, 'wb') as f:
            f.write(test_content)

        metadata = sample_backup_metadata.copy()
        metadata["file_path"] = str(backup_file)
        metadata["encrypted"] = False
        metadata["compressed"] = True

        prepared_file = restore_manager._prepare_backup_file(metadata)

        # Should create decompressed file
        assert prepared_file.exists()
        assert prepared_file != backup_file

        # Verify content
        content = prepared_file.read_bytes()
        assert content == test_content


class TestDatabaseCredentials:
    """Test database credential extraction."""

    @patch.dict(os.environ, {
        'DATABASE_URL': 'postgresql://restore_user:restore_pass@localhost:5433/restore_db'
    })
    def test_get_database_credentials(self, restore_manager):
        """Test extracting database credentials."""
        with patch('restore.restore_manager.settings') as mock_settings:
            mock_settings.DATABASE_URL = 'postgresql://restore_user:restore_pass@localhost:5433/restore_db'

            creds = restore_manager._get_database_credentials()

            assert creds["host"] == "localhost"
            assert creds["port"] == "5433"
            assert creds["user"] == "restore_user"
            assert creds["password"] == "restore_pass"
            assert creds["database"] == "restore_db"

    def test_get_database_credentials_with_target(self, restore_manager):
        """Test credentials with custom target database."""
        with patch('restore.restore_manager.settings') as mock_settings:
            mock_settings.DATABASE_URL = 'postgresql://user:pass@localhost:5432/original_db'

            creds = restore_manager._get_database_credentials(target_database="custom_db")

            assert creds["database"] == "custom_db"


class TestRestoreBackup:
    """Test backup restoration workflow."""

    @pytest.mark.asyncio
    async def test_restore_backup_success(self, restore_manager, sample_backup_metadata, temp_restore_dir):
        """Test successful backup restoration."""
        # Save metadata
        backup_id = sample_backup_metadata["backup_id"]
        metadata_file = restore_manager.metadata_dir / f"{backup_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(sample_backup_metadata, f)

        # Mock pg_restore subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"Restore success", b""))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('restore.restore_manager.settings') as mock_settings:
                mock_settings.DATABASE_URL = 'postgresql://user:pass@localhost:5432/testdb'

                with patch.object(restore_manager, '_validate_backup', return_value=True):
                    result = await restore_manager.restore_backup(backup_id=backup_id)

        assert result.success is True
        assert result.backup_id == backup_id
        assert result.target_database == "testdb"

    @pytest.mark.asyncio
    async def test_restore_backup_validation_failure(self, restore_manager, sample_backup_metadata):
        """Test restore failure due to validation."""
        backup_id = sample_backup_metadata["backup_id"]
        metadata_file = restore_manager.metadata_dir / f"{backup_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(sample_backup_metadata, f)

        with patch.object(restore_manager, '_validate_backup', return_value=False):
            result = await restore_manager.restore_backup(backup_id=backup_id, validate=True)

        assert result.success is False
        assert "validation failed" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_restore_backup_pg_restore_failure(self, restore_manager, sample_backup_metadata):
        """Test restore failure during pg_restore."""
        backup_id = sample_backup_metadata["backup_id"]
        metadata_file = restore_manager.metadata_dir / f"{backup_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(sample_backup_metadata, f)

        # Mock failing pg_restore
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"pg_restore error"))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch('restore.restore_manager.settings') as mock_settings:
                mock_settings.DATABASE_URL = 'postgresql://user:pass@localhost:5432/testdb'

                with patch.object(restore_manager, '_validate_backup', return_value=True):
                    result = await restore_manager.restore_backup(backup_id=backup_id)

        assert result.success is False
        assert "Restore failed" in result.error_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
