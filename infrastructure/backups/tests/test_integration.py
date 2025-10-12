"""
Integration Tests for Complete Backup System

Tests full backup/restore workflows, DR scenarios, and system integration.
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from backup.backup_manager import backup_manager, BackupMetadata
from restore.restore_manager import restore_manager
from disaster_recovery_orchestrator import dr_orchestrator
from validation.backup_validator import backup_validator


@pytest.fixture
def integrated_system_dir():
    """Create integrated test environment."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_integrated_config(integrated_system_dir):
    """Create integrated system configuration."""
    return {
        "version": "1.0.0",
        "backup_strategies": {
            "full": {
                "enabled": True,
                "retention_days": 30
            }
        },
        "encryption": {
            "enabled": False  # Disabled for integration tests
        },
        "storage": {
            "local": {
                "path": str(integrated_system_dir / "backups"),
                "enabled": True,
                "max_size_gb": 500
            }
        },
        "databases": {
            "postgresql": {
                "host": "localhost",
                "port": 5432,
                "backup_format": "custom",
                "compress_level": 9,
                "parallel_jobs": 2
            }
        },
        "compression": {
            "enabled": True,
            "level": 9
        },
        "validation": {
            "enabled": True
        },
        "rto_minutes": 30,
        "rpo_minutes": 60
    }


class TestFullBackupRestoreWorkflow:
    """Test complete backup and restore workflow."""

    @pytest.mark.asyncio
    async def test_backup_then_restore_workflow(self, mock_integrated_config, integrated_system_dir):
        """Test creating backup and then restoring it."""
        backups_dir = integrated_system_dir / "backups"
        backups_dir.mkdir()

        metadata_dir = backups_dir / "metadata"
        metadata_dir.mkdir()

        # Configure managers
        with patch.object(backup_manager, '_load_config', return_value=mock_integrated_config):
            with patch.object(restore_manager, '_load_config', return_value=mock_integrated_config):
                backup_manager.backup_root = backups_dir
                backup_manager.metadata_dir = metadata_dir
                backup_manager.cipher = None  # Encryption disabled

                restore_manager.backup_root = backups_dir
                restore_manager.metadata_dir = metadata_dir

                # Mock pg_dump
                mock_dump_process = AsyncMock()
                mock_dump_process.returncode = 0
                mock_dump_process.communicate = AsyncMock(return_value=(b"Backup success", b""))

                # Mock pg_restore
                mock_restore_process = AsyncMock()
                mock_restore_process.returncode = 0
                mock_restore_process.communicate = AsyncMock(return_value=(b"Restore success", b""))

                async def mock_subprocess(*args, **kwargs):
                    if 'pg_dump' in args[0]:
                        # Create mock backup file
                        file_arg = next((arg for arg in args if arg.startswith('--file=')), None)
                        if file_arg:
                            backup_file = Path(file_arg.replace('--file=', ''))
                            backup_file.write_bytes(b"Mock backup data content")
                        return mock_dump_process
                    elif 'pg_restore' in args[0]:
                        return mock_restore_process
                    return mock_dump_process

                with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
                    with patch('backup.backup_manager.settings') as mock_settings:
                        mock_settings.DATABASE_URL = 'postgresql://user:pass@localhost:5432/testdb'

                        with patch('restore.restore_manager.settings', mock_settings):
                            # Step 1: Create backup
                            backup_metadata = await backup_manager.create_backup(backup_type="full")

                            assert backup_metadata.status == "completed"
                            assert Path(backup_metadata.file_path).exists()

                            # Step 2: Restore backup
                            restore_result = await restore_manager.restore_backup(
                                backup_id=backup_metadata.backup_id,
                                validate=False  # Skip validation for speed
                            )

                            assert restore_result.success is True
                            assert restore_result.backup_id == backup_metadata.backup_id


class TestBackupValidationIntegration:
    """Test backup validation integration."""

    @pytest.mark.asyncio
    async def test_backup_with_validation(self, mock_integrated_config, integrated_system_dir):
        """Test backup creation followed by validation."""
        backups_dir = integrated_system_dir / "backups"
        backups_dir.mkdir()

        metadata_dir = backups_dir / "metadata"
        metadata_dir.mkdir()

        validation_log_dir = integrated_system_dir / "validation_logs"
        validation_log_dir.mkdir()

        # Configure managers
        with patch.object(backup_manager, '_load_config', return_value=mock_integrated_config):
            with patch.object(backup_validator, '_load_config', return_value=mock_integrated_config):
                backup_manager.backup_root = backups_dir
                backup_manager.metadata_dir = metadata_dir
                backup_manager.cipher = None

                backup_validator.backup_root = backups_dir
                backup_validator.metadata_dir = metadata_dir
                backup_validator.validation_log_dir = validation_log_dir

                # Mock pg_dump
                mock_process = AsyncMock()
                mock_process.returncode = 0
                mock_process.communicate = AsyncMock(return_value=(b"Success", b""))

                async def mock_subprocess(*args, **kwargs):
                    # Create backup file
                    file_arg = next((arg for arg in args if arg.startswith('--file=')), None)
                    if file_arg:
                        backup_file = Path(file_arg.replace('--file=', ''))
                        backup_file.write_bytes(b"Mock backup data for validation")
                    return mock_process

                with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
                    with patch('backup.backup_manager.settings') as mock_settings:
                        mock_settings.DATABASE_URL = 'postgresql://user:pass@localhost:5432/testdb'

                        # Create backup
                        backup_metadata = await backup_manager.create_backup(backup_type="full")

                        # Validate backup
                        with patch('validation.backup_validator.restore_manager') as mock_restore:
                            mock_restore._validate_backup.return_value = True

                            validation_result = await backup_validator.validate_backup(
                                backup_id=backup_metadata.backup_id,
                                validation_level="standard"
                            )

                            assert validation_result.success is True
                            assert len(validation_result.checks_passed) > 0


class TestDisasterRecoveryScenario:
    """Test complete disaster recovery scenarios."""

    @pytest.mark.asyncio
    async def test_database_failure_recovery(self, mock_integrated_config, integrated_system_dir):
        """Test complete database failure recovery scenario."""
        backups_dir = integrated_system_dir / "backups"
        backups_dir.mkdir()

        metadata_dir = backups_dir / "metadata"
        metadata_dir.mkdir()

        # Create mock recent backup
        backup_id = "backup_full_recent"
        backup_file = backups_dir / f"{backup_id}.dump"
        backup_file.write_bytes(b"Recent backup data")

        metadata = {
            "backup_id": backup_id,
            "backup_type": "full",
            "timestamp": datetime.now().isoformat(),
            "database_name": "test_db",
            "file_path": str(backup_file),
            "file_size": backup_file.stat().st_size,
            "checksum": "abc123",
            "encrypted": False,
            "compressed": False,
            "status": "completed",
            "duration_seconds": 60.0,
            "retention_until": (datetime.now() + timedelta(days=30)).isoformat()
        }

        metadata_file = metadata_dir / f"{backup_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        # Configure DR orchestrator
        with patch.object(dr_orchestrator, '_load_config', return_value=mock_integrated_config):
            dr_orchestrator.backup_root = backups_dir
            dr_orchestrator.metadata_dir = metadata_dir

            # Mock restore manager
            with patch('disaster_recovery_orchestrator.restore_manager') as mock_restore:
                mock_restore.list_available_backups.return_value = [metadata]

                # Execute DR scenario (dry run)
                recovery_metrics = await dr_orchestrator.execute_recovery(
                    scenario="database_failure",
                    dry_run=True
                )

                assert recovery_metrics.status == "completed"
                assert recovery_metrics.actual_rto_minutes is not None
                assert recovery_metrics.actual_rpo_minutes is not None

                # Check RTO/RPO targets
                assert recovery_metrics.rto_target_minutes == 30
                assert recovery_metrics.rpo_target_minutes == 60


class TestBackupRetentionWorkflow:
    """Test backup retention and cleanup."""

    @pytest.mark.asyncio
    async def test_backup_retention_enforcement(self, mock_integrated_config, integrated_system_dir):
        """Test that old backups are identified for cleanup."""
        backups_dir = integrated_system_dir / "backups"
        backups_dir.mkdir()

        metadata_dir = backups_dir / "metadata"
        metadata_dir.mkdir()

        # Create old and new backups
        now = datetime.now()

        # Recent backup (within retention)
        recent_backup = {
            "backup_id": "backup_recent",
            "timestamp": now.isoformat(),
            "retention_until": (now + timedelta(days=30)).isoformat(),
            "status": "completed"
        }

        # Old backup (outside retention)
        old_backup = {
            "backup_id": "backup_old",
            "timestamp": (now - timedelta(days=40)).isoformat(),
            "retention_until": (now - timedelta(days=10)).isoformat(),
            "status": "completed"
        }

        # Save metadata
        for backup in [recent_backup, old_backup]:
            metadata_file = metadata_dir / f"{backup['backup_id']}.json"
            with open(metadata_file, 'w') as f:
                json.dump(backup, f)

        # List backups
        with patch.object(restore_manager, '_load_config', return_value=mock_integrated_config):
            restore_manager.backup_root = backups_dir
            restore_manager.metadata_dir = metadata_dir

            backups = restore_manager.list_available_backups()

            # Both should be listed (cleanup is separate process)
            assert len(backups) == 2

            # Identify expired backups
            expired = []
            for backup in backups:
                retention_until = datetime.fromisoformat(backup["retention_until"])
                if retention_until < now:
                    expired.append(backup["backup_id"])

            assert "backup_old" in expired
            assert "backup_recent" not in expired


class TestMonitoringIntegration:
    """Test monitoring metrics integration."""

    def test_metrics_recording_during_backup(self, mock_integrated_config):
        """Test that metrics are recorded during backup operations."""
        from monitoring.prometheus_metrics import metrics_collector

        if not metrics_collector._initialized:
            pytest.skip("Prometheus metrics not available")

        # Record backup metrics
        start_time = metrics_collector.record_backup_start("full")

        # Simulate backup
        import time
        time.sleep(0.1)

        metrics_collector.record_backup_success(
            backup_type="full",
            start_time=start_time,
            size_bytes=1024 * 1024 * 100  # 100 MB
        )

        # No errors should occur
        # Actual metric values can't be easily verified without Prometheus

    def test_metrics_recording_failure(self):
        """Test failure metrics recording."""
        from monitoring.prometheus_metrics import metrics_collector

        if not metrics_collector._initialized:
            pytest.skip("Prometheus metrics not available")

        start_time = metrics_collector.record_backup_start("full")

        metrics_collector.record_backup_failure(
            backup_type="full",
            start_time=start_time,
            error_type="database_connection_failed"
        )

        # No errors should occur


class TestEndToEndBackupSystem:
    """Test complete end-to-end backup system."""

    @pytest.mark.asyncio
    async def test_complete_backup_lifecycle(self, mock_integrated_config, integrated_system_dir):
        """Test complete backup lifecycle: create -> validate -> restore -> DR test."""
        backups_dir = integrated_system_dir / "backups"
        backups_dir.mkdir()

        metadata_dir = backups_dir / "metadata"
        metadata_dir.mkdir()

        validation_log_dir = integrated_system_dir / "validation_logs"
        validation_log_dir.mkdir()

        # Configure all components
        with patch.object(backup_manager, '_load_config', return_value=mock_integrated_config):
            with patch.object(restore_manager, '_load_config', return_value=mock_integrated_config):
                with patch.object(backup_validator, '_load_config', return_value=mock_integrated_config):
                    with patch.object(dr_orchestrator, '_load_config', return_value=mock_integrated_config):

                        # Set directories
                        for manager in [backup_manager, restore_manager, dr_orchestrator]:
                            manager.backup_root = backups_dir
                            manager.metadata_dir = metadata_dir

                        backup_manager.cipher = None
                        backup_validator.backup_root = backups_dir
                        backup_validator.metadata_dir = metadata_dir
                        backup_validator.validation_log_dir = validation_log_dir

                        # Mock subprocess calls
                        mock_process = AsyncMock()
                        mock_process.returncode = 0
                        mock_process.communicate = AsyncMock(return_value=(b"Success", b""))

                        async def mock_subprocess(*args, **kwargs):
                            if 'pg_dump' in args[0]:
                                file_arg = next((arg for arg in args if arg.startswith('--file=')), None)
                                if file_arg:
                                    backup_file = Path(file_arg.replace('--file=', ''))
                                    backup_file.write_bytes(b"End-to-end test backup data")
                            return mock_process

                        with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
                            with patch('backup.backup_manager.settings') as mock_settings:
                                mock_settings.DATABASE_URL = 'postgresql://user:pass@localhost:5432/testdb'

                                with patch('restore.restore_manager.settings', mock_settings):

                                    # 1. Create backup
                                    backup_metadata = await backup_manager.create_backup("full")
                                    assert backup_metadata.status == "completed"

                                    # 2. Validate backup
                                    with patch('validation.backup_validator.restore_manager') as mock_val_restore:
                                        mock_val_restore._validate_backup.return_value = True

                                        validation_result = await backup_validator.validate_backup(
                                            backup_id=backup_metadata.backup_id,
                                            validation_level="standard"
                                        )
                                        assert validation_result.success is True

                                    # 3. Test restore
                                    restore_result = await restore_manager.restore_backup(
                                        backup_id=backup_metadata.backup_id,
                                        validate=False
                                    )
                                    assert restore_result.success is True

                                    # 4. Run DR test
                                    with patch('disaster_recovery_orchestrator.restore_manager') as mock_dr_restore:
                                        mock_dr_restore.list_available_backups.return_value = [
                                            {
                                                "backup_id": backup_metadata.backup_id,
                                                "backup_type": "full",
                                                "timestamp": backup_metadata.timestamp,
                                                "status": "completed"
                                            }
                                        ]

                                        dr_results = await dr_orchestrator.test_dr_procedures()
                                        assert dr_results["overall_success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
