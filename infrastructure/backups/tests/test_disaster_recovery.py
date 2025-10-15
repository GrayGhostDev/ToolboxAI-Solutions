"""
Unit Tests for Disaster Recovery Orchestrator

Tests DR scenarios, RTO/RPO tracking, and recovery procedures.
"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from disaster_recovery_orchestrator import (
    DROrchestrator,
    DRScenario,
    RecoveryStatus,
    RecoveryMetrics
)


@pytest.fixture
def temp_dr_dir():
    """Create temporary DR directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_dr_config(temp_dr_dir):
    """Create mock DR configuration."""
    return {
        "version": "1.0.0",
        "storage": {
            "local": {
                "path": str(temp_dr_dir)
            }
        },
        "rto_minutes": 30,
        "rpo_minutes": 60
    }


@pytest.fixture
def dr_orchestrator(mock_dr_config, temp_dr_dir):
    """Create DROrchestrator instance."""
    config_dir = temp_dr_dir / "config"
    config_dir.mkdir()
    config_file = config_dir / "backup_config.json"

    with open(config_file, 'w') as f:
        json.dump(mock_dr_config, f)

    with patch.object(DROrchestrator, '_load_config', return_value=mock_dr_config):
        orchestrator = DROrchestrator()
        orchestrator.config_path = config_file
        return orchestrator


class TestDROrchest ratorInitialization:
    """Test DROrchestrator initialization."""

    def test_singleton_pattern(self, dr_orchestrator):
        """Test singleton pattern implementation."""
        orchestrator1 = dr_orchestrator
        orchestrator2 = DROrchestrator()
        assert orchestrator1 is orchestrator2

    def test_initialization_loads_config(self, dr_orchestrator):
        """Test configuration is loaded."""
        assert dr_orchestrator.config is not None
        assert dr_orchestrator.rto_minutes == 30
        assert dr_orchestrator.rpo_minutes == 60

    def test_initialization_state(self, dr_orchestrator):
        """Test initial state."""
        assert dr_orchestrator.current_recovery is None
        assert dr_orchestrator.recovery_history == []


class TestBackupHealthVerification:
    """Test backup health check functionality."""

    @pytest.mark.asyncio
    async def test_verify_backup_health_no_backups(self, dr_orchestrator):
        """Test health check with no backups available."""
        with patch('disaster_recovery_orchestrator.restore_manager') as mock_restore:
            mock_restore.list_available_backups.return_value = []

            health = await dr_orchestrator.verify_backup_health()

            assert health["healthy"] is False
            assert "No backups available" in health["issues"]

    @pytest.mark.asyncio
    async def test_verify_backup_health_recent_backup(self, dr_orchestrator):
        """Test health check with recent backup."""
        recent_backup = {
            "backup_id": "backup_full_recent",
            "backup_type": "full",
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }

        with patch('disaster_recovery_orchestrator.restore_manager') as mock_restore:
            mock_restore.list_available_backups.return_value = [recent_backup]

            health = await dr_orchestrator.verify_backup_health()

            assert health["healthy"] is True
            assert health["last_full_backup"] == "backup_full_recent"
            assert health["last_backup_age_hours"] is not None
            assert health["last_backup_age_hours"] < 1  # Less than 1 hour old

    @pytest.mark.asyncio
    async def test_verify_backup_health_old_backup_exceeds_rpo(self, dr_orchestrator):
        """Test health check fails when backup exceeds RPO."""
        # Backup from 2 hours ago (exceeds 60 min RPO)
        old_time = datetime.now() - timedelta(hours=2)
        old_backup = {
            "backup_id": "backup_full_old",
            "backup_type": "full",
            "timestamp": old_time.isoformat(),
            "status": "completed"
        }

        with patch('disaster_recovery_orchestrator.restore_manager') as mock_restore:
            mock_restore.list_available_backups.return_value = [old_backup]

            health = await dr_orchestrator.verify_backup_health()

            assert health["healthy"] is False
            assert any("exceeds RPO" in issue for issue in health["issues"])

    @pytest.mark.asyncio
    async def test_verify_backup_health_counts_recent_backups(self, dr_orchestrator):
        """Test backup counting for recent periods."""
        now = datetime.now()
        backups = [
            {
                "backup_id": f"backup_{i}",
                "backup_type": "full",
                "timestamp": (now - timedelta(hours=i)).isoformat(),
                "status": "completed"
            }
            for i in range(48)  # 48 backups over 48 hours
        ]

        with patch('disaster_recovery_orchestrator.restore_manager') as mock_restore:
            mock_restore.list_available_backups.return_value = backups

            health = await dr_orchestrator.verify_backup_health()

            # Should have 24 backups in last 24 hours
            assert health["backup_count_24h"] == 24

            # Should have 48 backups in last 7 days
            assert health["backup_count_7d"] == 48


class TestRecoveryExecution:
    """Test disaster recovery execution."""

    @pytest.mark.asyncio
    async def test_execute_recovery_dry_run(self, dr_orchestrator):
        """Test recovery in dry-run mode."""
        recent_backup = {
            "backup_id": "backup_full_test",
            "backup_type": "full",
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }

        with patch('disaster_recovery_orchestrator.restore_manager') as mock_restore:
            mock_restore.list_available_backups.return_value = [recent_backup]

            # Mock health check
            with patch.object(dr_orchestrator, 'verify_backup_health', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = {"healthy": True, "issues": []}

                metrics = await dr_orchestrator.execute_recovery(
                    scenario=DRScenario.DATABASE_FAILURE.value,
                    dry_run=True
                )

        assert metrics.status == RecoveryStatus.COMPLETED.value
        assert metrics.scenario == DRScenario.DATABASE_FAILURE.value
        assert len(metrics.steps_completed) > 0
        assert "backup_health_verification" in metrics.steps_completed

    @pytest.mark.asyncio
    async def test_execute_recovery_unhealthy_backups(self, dr_orchestrator):
        """Test recovery fails with unhealthy backups."""
        with patch.object(dr_orchestrator, 'verify_backup_health', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = {
                "healthy": False,
                "issues": ["No backups available"]
            }

            with pytest.raises(RuntimeError, match="Backup health check failed"):
                await dr_orchestrator.execute_recovery(
                    scenario=DRScenario.DATABASE_FAILURE.value,
                    dry_run=False
                )

    @pytest.mark.asyncio
    async def test_execute_recovery_no_backups_available(self, dr_orchestrator):
        """Test recovery fails when no backups exist."""
        with patch.object(dr_orchestrator, 'verify_backup_health', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = {"healthy": True, "issues": []}

            with patch('disaster_recovery_orchestrator.restore_manager') as mock_restore:
                mock_restore.list_available_backups.return_value = []

                with pytest.raises(RuntimeError, match="No backups available"):
                    await dr_orchestrator.execute_recovery(
                        scenario=DRScenario.DATABASE_FAILURE.value,
                        dry_run=False
                    )

    @pytest.mark.asyncio
    async def test_execute_recovery_with_target_point_in_time(self, dr_orchestrator):
        """Test recovery to specific point in time."""
        target_time = datetime.now() - timedelta(hours=1)

        # Create backups before and after target time
        backups = [
            {
                "backup_id": "backup_after",
                "timestamp": (target_time + timedelta(minutes=30)).isoformat(),
                "status": "completed"
            },
            {
                "backup_id": "backup_before",
                "timestamp": (target_time - timedelta(minutes=30)).isoformat(),
                "status": "completed"
            },
            {
                "backup_id": "backup_way_before",
                "timestamp": (target_time - timedelta(hours=2)).isoformat(),
                "status": "completed"
            }
        ]

        with patch('disaster_recovery_orchestrator.restore_manager') as mock_restore:
            mock_restore.list_available_backups.return_value = backups

            with patch.object(dr_orchestrator, 'verify_backup_health', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = {"healthy": True, "issues": []}

                metrics = await dr_orchestrator.execute_recovery(
                    scenario=DRScenario.DATA_CORRUPTION.value,
                    target_point_in_time=target_time,
                    dry_run=True
                )

        # Should select backup_before (closest before target time)
        assert metrics.status == RecoveryStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_execute_recovery_tracks_rto_rpo(self, dr_orchestrator):
        """Test that RTO and RPO are tracked correctly."""
        backup_time = datetime.now() - timedelta(minutes=45)

        backup = {
            "backup_id": "backup_test",
            "backup_type": "full",
            "timestamp": backup_time.isoformat(),
            "status": "completed"
        }

        with patch('disaster_recovery_orchestrator.restore_manager') as mock_restore:
            mock_restore.list_available_backups.return_value = [backup]

            with patch.object(dr_orchestrator, 'verify_backup_health', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = {"healthy": True, "issues": []}

                metrics = await dr_orchestrator.execute_recovery(
                    scenario=DRScenario.DATABASE_FAILURE.value,
                    dry_run=True
                )

        # RPO should be ~45 minutes
        assert metrics.actual_rpo_minutes is not None
        assert 40 <= metrics.actual_rpo_minutes <= 50

        # RTO should be measured
        assert metrics.actual_rto_minutes is not None
        assert metrics.actual_rto_minutes > 0

    @pytest.mark.asyncio
    async def test_execute_recovery_saves_to_history(self, dr_orchestrator):
        """Test that recovery is saved to history."""
        initial_history_len = len(dr_orchestrator.recovery_history)

        backup = {
            "backup_id": "backup_test",
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }

        with patch('disaster_recovery_orchestrator.restore_manager') as mock_restore:
            mock_restore.list_available_backups.return_value = [backup]

            with patch.object(dr_orchestrator, 'verify_backup_health', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = {"healthy": True, "issues": []}

                await dr_orchestrator.execute_recovery(
                    scenario=DRScenario.HARDWARE_FAILURE.value,
                    dry_run=True
                )

        assert len(dr_orchestrator.recovery_history) == initial_history_len + 1
        assert dr_orchestrator.recovery_history[-1].scenario == DRScenario.HARDWARE_FAILURE.value


class TestDRTesting:
    """Test DR procedure testing."""

    @pytest.mark.asyncio
    async def test_test_dr_procedures_success(self, dr_orchestrator):
        """Test successful DR procedure testing."""
        backup = {
            "backup_id": "backup_test",
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }

        with patch('disaster_recovery_orchestrator.restore_manager') as mock_restore:
            mock_restore.list_available_backups.return_value = [backup]

            with patch.object(dr_orchestrator, 'verify_backup_health', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = {"healthy": True, "issues": []}

                results = await dr_orchestrator.test_dr_procedures()

        assert results["overall_success"] is True
        assert len(results["scenarios_tested"]) > 0

        # Check database failure scenario was tested
        db_failure_test = next(
            (s for s in results["scenarios_tested"]
             if s["scenario"] == DRScenario.DATABASE_FAILURE.value),
            None
        )
        assert db_failure_test is not None
        assert db_failure_test["success"] is True

    @pytest.mark.asyncio
    async def test_test_dr_procedures_failure(self, dr_orchestrator):
        """Test DR procedure testing with failures."""
        with patch.object(dr_orchestrator, 'verify_backup_health', new_callable=AsyncMock) as mock_health:
            mock_health.side_effect = Exception("Health check failed")

            results = await dr_orchestrator.test_dr_procedures()

        assert results["overall_success"] is False
        assert len(results["scenarios_tested"]) > 0

        # Should have error recorded
        failed_test = results["scenarios_tested"][0]
        assert failed_test["success"] is False
        assert "error" in failed_test


class TestRecoveryMetrics:
    """Test recovery metrics tracking."""

    def test_recovery_metrics_initialization(self):
        """Test RecoveryMetrics dataclass initialization."""
        metrics = RecoveryMetrics(
            scenario="test_scenario",
            start_time=datetime.now().isoformat()
        )

        assert metrics.scenario == "test_scenario"
        assert metrics.status == RecoveryStatus.NOT_STARTED.value
        assert metrics.steps_completed == []
        assert metrics.steps_failed == []
        assert metrics.error_messages == []

    def test_recovery_metrics_step_tracking(self):
        """Test tracking completed steps."""
        metrics = RecoveryMetrics(
            scenario="test",
            start_time=datetime.now().isoformat()
        )

        metrics.steps_completed.append("step1")
        metrics.steps_completed.append("step2")

        assert len(metrics.steps_completed) == 2
        assert "step1" in metrics.steps_completed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
