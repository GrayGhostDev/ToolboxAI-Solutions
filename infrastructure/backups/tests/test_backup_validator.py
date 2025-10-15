"""
Unit Tests for Backup Validator

Tests validation levels, prerequisites checks, and validation workflows.
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil
import hashlib

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validation.backup_validator import (
    BackupValidator,
    ValidationLevel,
    ValidationResult
)


@pytest.fixture
def temp_validation_dir():
    """Create temporary validation directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_validator_config(temp_validation_dir):
    """Create mock validator configuration."""
    return {
        "version": "1.0.0",
        "storage": {
            "local": {
                "path": str(temp_validation_dir),
                "max_size_gb": 500
            }
        }
    }


@pytest.fixture
def backup_validator(mock_validator_config, temp_validation_dir):
    """Create BackupValidator instance."""
    with patch.object(BackupValidator, '_load_config', return_value=mock_validator_config):
        validator = BackupValidator()
        validator.backup_root = temp_validation_dir
        validator.metadata_dir = temp_validation_dir / "metadata"
        validator.metadata_dir.mkdir(exist_ok=True)
        validator.validation_log_dir = temp_validation_dir / "validation_logs"
        validator.validation_log_dir.mkdir(exist_ok=True)
        return validator


class TestBackupValidatorInitialization:
    """Test BackupValidator initialization."""

    def test_singleton_pattern(self, backup_validator):
        """Test singleton pattern implementation."""
        validator1 = backup_validator
        validator2 = BackupValidator()
        assert validator1 is validator2

    def test_initialization_creates_directories(self, backup_validator, temp_validation_dir):
        """Test initialization creates required directories."""
        assert (temp_validation_dir / "metadata").exists()
        assert (temp_validation_dir / "validation_logs").exists()


class TestValidationResultSaving:
    """Test validation result persistence."""

    def test_save_validation_result(self, backup_validator):
        """Test saving validation results to file."""
        result = ValidationResult(
            backup_id="test_backup",
            validation_level=ValidationLevel.STANDARD.value,
            timestamp=datetime.now().isoformat(),
            success=True,
            duration_seconds=5.5,
            checks_passed=["checksum", "metadata"],
            checks_failed=[],
            warnings=[]
        )

        backup_validator._save_validation_result(result)

        # Verify file created
        log_file = backup_validator.validation_log_dir / "validation_test_backup.json"
        assert log_file.exists()

        # Verify content
        with open(log_file, 'r') as f:
            saved_data = json.load(f)

        assert saved_data["backup_id"] == "test_backup"
        assert saved_data["success"] is True
        assert saved_data["duration_seconds"] == 5.5


class TestPrerequisitesValidation:
    """Test backup prerequisites validation."""

    @pytest.mark.asyncio
    async def test_validate_prerequisites_success(self, backup_validator, temp_validation_dir):
        """Test successful prerequisites validation."""
        # Mock sufficient disk space
        with patch('shutil.disk_usage') as mock_disk:
            mock_disk.return_value = Mock(free=500 * 1024**3)  # 500 GB free

            # Mock pg_dump available
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"pg_dump version", b""))

            with patch('asyncio.create_subprocess_exec', return_value=mock_process):
                with patch('validation.backup_validator.settings') as mock_settings:
                    mock_settings.DATABASE_URL = 'postgresql://user:pass@localhost:5432/testdb'

                    results = await backup_validator.validate_prerequisites()

        assert results["all_passed"] is True
        assert results["checks"]["disk_space"]["passed"] is True
        assert results["checks"]["pg_dump"]["passed"] is True

    @pytest.mark.asyncio
    async def test_validate_prerequisites_low_disk_space(self, backup_validator):
        """Test prerequisites validation with low disk space."""
        # Mock insufficient disk space (10 GB free, 500 GB max)
        with patch('shutil.disk_usage') as mock_disk:
            mock_disk.return_value = Mock(free=10 * 1024**3)

            results = await backup_validator.validate_prerequisites()

        assert results["all_passed"] is False
        assert results["checks"]["disk_space"]["passed"] is False
        assert "Low disk space" in results["checks"]["disk_space"]["message"]

    @pytest.mark.asyncio
    async def test_validate_prerequisites_pg_dump_missing(self, backup_validator):
        """Test prerequisites validation when pg_dump not found."""
        with patch('shutil.disk_usage') as mock_disk:
            mock_disk.return_value = Mock(free=500 * 1024**3)

            with patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError):
                results = await backup_validator.validate_prerequisites()

        assert results["all_passed"] is False
        assert results["checks"]["pg_dump"]["passed"] is False

    @pytest.mark.asyncio
    async def test_validate_prerequisites_database_unreachable(self, backup_validator):
        """Test prerequisites validation when database is unreachable."""
        with patch('shutil.disk_usage') as mock_disk:
            mock_disk.return_value = Mock(free=500 * 1024**3)

            # Mock pg_dump available
            mock_pg_dump = AsyncMock()
            mock_pg_dump.returncode = 0
            mock_pg_dump.communicate = AsyncMock(return_value=(b"", b""))

            # Mock pg_isready failing
            mock_pg_isready = AsyncMock()
            mock_pg_isready.returncode = 1
            mock_pg_isready.communicate = AsyncMock(return_value=(b"", b"could not connect"))

            async def mock_subprocess(*args, **kwargs):
                if 'pg_dump' in args[0]:
                    return mock_pg_dump
                elif 'pg_isready' in args[0]:
                    return mock_pg_isready
                return mock_pg_dump

            with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
                with patch('validation.backup_validator.settings') as mock_settings:
                    mock_settings.DATABASE_URL = 'postgresql://user:pass@localhost:5432/testdb'

                    results = await backup_validator.validate_prerequisites()

        assert results["checks"]["database_connectivity"]["passed"] is False


class TestBasicValidation:
    """Test BASIC validation level."""

    @pytest.mark.asyncio
    async def test_validate_backup_basic_success(self, backup_validator, temp_validation_dir):
        """Test successful basic validation (checksum only)."""
        # Create backup file with known content
        backup_file = temp_validation_dir / "backup_test.dump"
        test_content = b"Test backup data"
        backup_file.write_bytes(test_content)

        # Calculate checksum
        checksum = hashlib.sha256(test_content).hexdigest()

        # Create metadata
        metadata = {
            "backup_id": "backup_test",
            "backup_type": "full",
            "file_path": str(backup_file),
            "checksum": checksum,
            "status": "completed"
        }

        metadata_file = backup_validator.metadata_dir / "backup_test.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        # Mock restore_manager validation
        with patch('validation.backup_validator.restore_manager') as mock_restore:
            mock_restore._validate_backup.return_value = True

            result = await backup_validator.validate_backup(
                backup_id="backup_test",
                validation_level=ValidationLevel.BASIC.value
            )

        assert result.success is True
        assert "metadata_exists" in result.checks_passed
        assert "file_exists" in result.checks_passed
        assert "checksum_valid" in result.checks_passed

    @pytest.mark.asyncio
    async def test_validate_backup_basic_checksum_fail(self, backup_validator, temp_validation_dir):
        """Test basic validation failure with bad checksum."""
        backup_file = temp_validation_dir / "backup_test.dump"
        backup_file.write_bytes(b"Test backup data")

        metadata = {
            "backup_id": "backup_test",
            "file_path": str(backup_file),
            "checksum": "wrong_checksum",
            "status": "completed"
        }

        metadata_file = backup_validator.metadata_dir / "backup_test.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        with patch('validation.backup_validator.restore_manager') as mock_restore:
            mock_restore._validate_backup.return_value = False

            result = await backup_validator.validate_backup(
                backup_id="backup_test",
                validation_level=ValidationLevel.BASIC.value
            )

        assert result.success is False
        assert "checksum_valid" in result.checks_failed


class TestStandardValidation:
    """Test STANDARD validation level."""

    @pytest.mark.asyncio
    async def test_validate_backup_standard_success(self, backup_validator, temp_validation_dir):
        """Test successful standard validation (checksum + metadata)."""
        backup_file = temp_validation_dir / "backup_test.dump"
        test_content = b"Test backup data"
        backup_file.write_bytes(test_content)

        checksum = hashlib.sha256(test_content).hexdigest()

        # Complete metadata with all required fields
        metadata = {
            "backup_id": "backup_test",
            "backup_type": "full",
            "timestamp": datetime.now().isoformat(),
            "file_path": str(backup_file),
            "file_size": len(test_content),
            "checksum": checksum,
            "status": "completed"
        }

        metadata_file = backup_validator.metadata_dir / "backup_test.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        with patch('validation.backup_validator.restore_manager') as mock_restore:
            mock_restore._validate_backup.return_value = True

            result = await backup_validator.validate_backup(
                backup_id="backup_test",
                validation_level=ValidationLevel.STANDARD.value
            )

        assert result.success is True
        assert "checksum_valid" in result.checks_passed
        assert "metadata_complete" in result.checks_passed

    @pytest.mark.asyncio
    async def test_validate_backup_standard_warns_missing_fields(self, backup_validator, temp_validation_dir):
        """Test standard validation warns about missing metadata fields."""
        backup_file = temp_validation_dir / "backup_test.dump"
        backup_file.write_bytes(b"Test")

        # Incomplete metadata (missing timestamp)
        metadata = {
            "backup_id": "backup_test",
            "file_path": str(backup_file),
            "checksum": hashlib.sha256(b"Test").hexdigest(),
            "status": "completed"
        }

        metadata_file = backup_validator.metadata_dir / "backup_test.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        with patch('validation.backup_validator.restore_manager') as mock_restore:
            mock_restore._validate_backup.return_value = True

            result = await backup_validator.validate_backup(
                backup_id="backup_test",
                validation_level=ValidationLevel.STANDARD.value
            )

        assert result.success is True
        assert len(result.warnings) > 0
        assert any("Missing metadata field" in w for w in result.warnings)


class TestComprehensiveValidation:
    """Test COMPREHENSIVE validation level."""

    @pytest.mark.asyncio
    async def test_validate_backup_comprehensive_includes_test_restore(self, backup_validator, temp_validation_dir):
        """Test comprehensive validation includes test restore."""
        backup_file = temp_validation_dir / "backup_test.dump"
        backup_file.write_bytes(b"Test")

        metadata = {
            "backup_id": "backup_test",
            "backup_type": "full",
            "timestamp": datetime.now().isoformat(),
            "file_path": str(backup_file),
            "file_size": 4,
            "checksum": hashlib.sha256(b"Test").hexdigest(),
            "status": "completed"
        }

        metadata_file = backup_validator.metadata_dir / "backup_test.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        with patch('validation.backup_validator.restore_manager') as mock_restore:
            mock_restore._validate_backup.return_value = True

            result = await backup_validator.validate_backup(
                backup_id="backup_test",
                validation_level=ValidationLevel.COMPREHENSIVE.value
            )

        assert result.success is True
        assert "test_restore" in result.checks_passed
        # Note: Currently warns that test restore not implemented
        assert any("not yet implemented" in w for w in result.warnings)


class TestValidationErrors:
    """Test validation error handling."""

    @pytest.mark.asyncio
    async def test_validate_backup_metadata_not_found(self, backup_validator):
        """Test validation fails when metadata doesn't exist."""
        result = await backup_validator.validate_backup(
            backup_id="nonexistent_backup",
            validation_level=ValidationLevel.BASIC.value
        )

        assert result.success is False
        assert "metadata_exists" in result.checks_failed
        assert "Backup metadata not found" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_backup_file_not_found(self, backup_validator):
        """Test validation fails when backup file doesn't exist."""
        metadata = {
            "backup_id": "backup_test",
            "file_path": "/nonexistent/backup.dump",
            "checksum": "abc123",
            "status": "completed"
        }

        metadata_file = backup_validator.metadata_dir / "backup_test.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        result = await backup_validator.validate_backup(
            backup_id="backup_test",
            validation_level=ValidationLevel.BASIC.value
        )

        assert result.success is False
        assert "file_exists" in result.checks_failed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
