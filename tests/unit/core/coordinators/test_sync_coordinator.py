"""
Unit tests for Sync Coordinator - Distributed state synchronization system
Tests state management, event bus, conflict resolution, and real-time updates
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio
import json

from core.coordinators.sync_coordinator import (
    SyncCoordinator,
    Event,
    StateSnapshot,
    ConflictResolution,
    EventPriority,
    SyncState,
    create_sync_coordinator,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_config():
    """Sample configuration for sync coordinator"""
    return {
        "event_buffer_size": 1000,
        "state_history_size": 50,
        "sync_interval": 1,  # Fast for testing
        "enable_conflict_resolution": True,
        "default_conflict_strategy": "timestamp_wins",
    }


@pytest.fixture
def sync_coordinator(sample_config):
    """SyncCoordinator instance with test configuration"""
    coordinator = SyncCoordinator(config=sample_config)
    return coordinator


@pytest.fixture
def sample_event():
    """Sample event for testing"""
    return Event(
        event_id="event_123",
        event_type="test_event",
        source="test_component",
        target=None,
        data={"key": "value"},
        priority=EventPriority.NORMAL,
    )


@pytest.fixture
def sample_state_snapshot():
    """Sample state snapshot"""
    return StateSnapshot(
        component_id="test_component",
        state_data={"status": "active", "count": 42},
        version=1,
    )


# ============================================================================
# Test Class: SyncCoordinator Initialization
# ============================================================================


@pytest.mark.unit
class TestSyncCoordinatorInitialization:
    """Test SyncCoordinator initialization"""

    def test_initialization_with_config(self, sample_config):
        """Test initialization with custom configuration"""
        coordinator = SyncCoordinator(config=sample_config)

        assert coordinator.event_buffer_size == 1000
        assert coordinator.state_history_size == 50
        assert coordinator.sync_interval == 1
        assert coordinator.enable_conflict_resolution is True

    def test_initialization_with_defaults(self):
        """Test initialization with default configuration"""
        coordinator = SyncCoordinator()

        assert coordinator.event_buffer_size == 10000
        assert coordinator.state_history_size == 100
        assert coordinator.sync_interval == 5
        assert coordinator.enable_conflict_resolution is True

    def test_conflict_resolution_strategies_loaded(self, sync_coordinator):
        """Test conflict resolution strategies are registered"""
        assert "timestamp_wins" in sync_coordinator.conflict_resolution_strategies
        assert "version_wins" in sync_coordinator.conflict_resolution_strategies
        assert "merge_strategy" in sync_coordinator.conflict_resolution_strategies
        assert "user_decides" in sync_coordinator.conflict_resolution_strategies

    @pytest.mark.asyncio
    async def test_initialize_starts_background_tasks(self, sync_coordinator):
        """Test initialization starts background tasks"""
        with patch("asyncio.create_task") as mock_create_task:
            await sync_coordinator.initialize()

            assert sync_coordinator.is_initialized is True
            assert mock_create_task.call_count == 3  # 3 background tasks

    @pytest.mark.asyncio
    async def test_initialize_registers_event_handlers(self, sync_coordinator):
        """Test initialization registers built-in event handlers"""
        await sync_coordinator.initialize()

        assert "state_changed" in sync_coordinator.event_handlers
        assert "component_connected" in sync_coordinator.event_handlers
        assert "component_disconnected" in sync_coordinator.event_handlers
        assert "workflow_started" in sync_coordinator.event_handlers
        assert "content_generated" in sync_coordinator.event_handlers


# ============================================================================
# Test Class: Event System
# ============================================================================


@pytest.mark.unit
class TestEventSystem:
    """Test event bus and event handling"""

    @pytest.mark.asyncio
    async def test_publish_event(self, sync_coordinator):
        """Test publishing event to event bus"""
        event_id = await sync_coordinator.publish_event(
            event_type="test_event",
            source="test_source",
            data={"key": "value"},
            priority=EventPriority.NORMAL,
        )

        assert event_id is not None
        assert sync_coordinator.event_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_publish_event_with_target(self, sync_coordinator):
        """Test publishing event with specific target"""
        event_id = await sync_coordinator.publish_event(
            event_type="targeted_event",
            source="source_comp",
            data={"message": "hello"},
            target="target_comp",
            priority=EventPriority.HIGH,
        )

        assert event_id is not None

    @pytest.mark.asyncio
    async def test_publish_event_queue_full(self, sync_coordinator):
        """Test event publishing when queue is full"""
        sync_coordinator.event_queue = asyncio.Queue(maxsize=1)

        # Fill the queue
        await sync_coordinator.event_queue.put(
            Event("e1", "test", "src", None, {})
        )

        # Try to add another event
        with pytest.raises(RuntimeError) as exc_info:
            await sync_coordinator.publish_event("test", "src", {})

        assert "queue is full" in str(exc_info.value).lower()

    def test_register_event_handler(self, sync_coordinator):
        """Test registering event handler"""
        async def test_handler(event):
            pass

        sync_coordinator.register_event_handler("custom_event", test_handler)

        assert test_handler in sync_coordinator.event_handlers["custom_event"]

    def test_unregister_event_handler(self, sync_coordinator):
        """Test unregistering event handler"""
        async def test_handler(event):
            pass

        sync_coordinator.register_event_handler("custom_event", test_handler)
        sync_coordinator.unregister_event_handler("custom_event", test_handler)

        assert test_handler not in sync_coordinator.event_handlers["custom_event"]

    @pytest.mark.asyncio
    async def test_process_event_calls_handlers(self, sync_coordinator):
        """Test event processing calls registered handlers"""
        handler_called = False

        async def test_handler(event):
            nonlocal handler_called
            handler_called = True

        sync_coordinator.register_event_handler("test_event", test_handler)

        event = Event("e1", "test_event", "src", None, {"data": "test"})
        await sync_coordinator._process_event(event)

        assert handler_called is True

    @pytest.mark.asyncio
    async def test_process_event_handles_handler_exceptions(
        self, sync_coordinator
    ):
        """Test event processing handles handler exceptions gracefully"""
        async def failing_handler(event):
            raise Exception("Handler failed")

        sync_coordinator.register_event_handler("test_event", failing_handler)

        event = Event("e1", "test_event", "src", None, {})

        # Should not raise exception
        await sync_coordinator._process_event(event)

    @pytest.mark.asyncio
    async def test_event_retry_for_critical_priority(self, sync_coordinator):
        """Test critical events are retried on failure"""
        fail_count = 0

        async def intermittent_handler(event):
            nonlocal fail_count
            fail_count += 1
            if fail_count < 2:
                raise Exception("Temporary failure")

        sync_coordinator.register_event_handler("critical_event", intermittent_handler)

        event = Event(
            "e1",
            "critical_event",
            "src",
            None,
            {},
            priority=EventPriority.CRITICAL,
            retry_count=3,
        )

        # Process event (will fail and retry)
        await sync_coordinator._process_event(event)

        # Event should be added back to queue for retry
        assert event.retry_count == 2  # Decremented by 1


# ============================================================================
# Test Class: State Management
# ============================================================================


@pytest.mark.unit
class TestStateManagement:
    """Test state synchronization and management"""

    @pytest.mark.asyncio
    async def test_update_component_state(self, sync_coordinator):
        """Test updating component state"""
        snapshot = await sync_coordinator.update_component_state(
            "test_component", {"status": "active", "value": 100}
        )

        assert snapshot.component_id == "test_component"
        assert snapshot.version == 1
        assert snapshot.state_data["status"] == "active"
        assert sync_coordinator.component_sync_status["test_component"] == SyncState.SYNCED

    @pytest.mark.asyncio
    async def test_update_component_state_increments_version(
        self, sync_coordinator
    ):
        """Test state update increments version"""
        await sync_coordinator.update_component_state("comp", {"data": "v1"})
        snapshot2 = await sync_coordinator.update_component_state("comp", {"data": "v2"})

        assert snapshot2.version == 2

    @pytest.mark.asyncio
    async def test_update_component_state_adds_to_history(self, sync_coordinator):
        """Test state updates are added to history"""
        await sync_coordinator.update_component_state("comp", {"data": "v1"})
        await sync_coordinator.update_component_state("comp", {"data": "v2"})
        await sync_coordinator.update_component_state("comp", {"data": "v3"})

        history = sync_coordinator.state_history["comp"]
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_update_component_state_publishes_event(
        self, sync_coordinator
    ):
        """Test state update publishes state_changed event"""
        with patch.object(
            sync_coordinator, "publish_event", new_callable=AsyncMock
        ) as mock_publish:
            await sync_coordinator.update_component_state("comp", {"data": "test"})

            # Should publish state_changed event
            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            assert call_args[1]["event_type"] == "state_changed"

    @pytest.mark.asyncio
    async def test_get_component_state_current(self, sync_coordinator):
        """Test getting current component state"""
        await sync_coordinator.update_component_state("comp", {"data": "current"})

        snapshot = await sync_coordinator.get_component_state("comp")

        assert snapshot is not None
        assert snapshot.state_data["data"] == "current"

    @pytest.mark.asyncio
    async def test_get_component_state_specific_version(self, sync_coordinator):
        """Test getting specific version from history"""
        await sync_coordinator.update_component_state("comp", {"data": "v1"})
        await sync_coordinator.update_component_state("comp", {"data": "v2"})
        await sync_coordinator.update_component_state("comp", {"data": "v3"})

        snapshot = await sync_coordinator.get_component_state("comp", version=2)

        assert snapshot is not None
        assert snapshot.version == 2
        assert snapshot.state_data["data"] == "v2"

    @pytest.mark.asyncio
    async def test_get_component_state_not_found(self, sync_coordinator):
        """Test getting non-existent component state"""
        snapshot = await sync_coordinator.get_component_state("nonexistent")

        assert snapshot is None

    @pytest.mark.asyncio
    async def test_get_component_history(self, sync_coordinator):
        """Test retrieving component state history"""
        for i in range(5):
            await sync_coordinator.update_component_state("comp", {"version": i})

        history = await sync_coordinator.get_component_history("comp", limit=3)

        assert len(history) == 3
        assert history[-1].state_data["version"] == 4  # Most recent


# ============================================================================
# Test Class: Conflict Resolution
# ============================================================================


@pytest.mark.unit
class TestConflictResolution:
    """Test conflict detection and resolution"""

    @pytest.mark.asyncio
    async def test_detect_conflict_version(self, sync_coordinator):
        """Test version conflict detection"""
        current = StateSnapshot("comp", {"data": "old"}, 2)
        new = StateSnapshot("comp", {"data": "new"}, 1)  # Lower version

        conflict = await sync_coordinator._detect_conflict(current, new)

        assert conflict == "version_conflict"

    @pytest.mark.asyncio
    async def test_detect_conflict_concurrent_update(self, sync_coordinator):
        """Test concurrent update detection"""
        now = datetime.now()
        current = StateSnapshot("comp", {"data": "v1"}, 1)
        current.timestamp = now

        new = StateSnapshot("comp", {"data": "v2"}, 2)
        new.timestamp = now + timedelta(milliseconds=500)  # Within 1 second

        conflict = await sync_coordinator._detect_conflict(current, new)

        assert conflict == "concurrent_update"

    @pytest.mark.asyncio
    async def test_detect_conflict_data_incompatibility(self, sync_coordinator):
        """Test data conflict detection"""
        current = StateSnapshot("comp", {"key1": "value", "key2": 123}, 1)
        new = StateSnapshot("comp", {"key1": "new_value"}, 2)  # key2 deleted

        with patch.object(
            sync_coordinator, "_has_incompatible_changes", return_value=True
        ):
            conflict = await sync_coordinator._detect_conflict(current, new)

            assert conflict == "data_conflict"

    def test_compare_data_structures_key_deletion(self, sync_coordinator):
        """Test conflict detection for key deletion"""
        current = {"key1": "value", "key2": "value"}
        new = {"key1": "value"}  # key2 deleted

        has_conflict = sync_coordinator._compare_data_structures(current, new)

        assert has_conflict is True

    def test_compare_data_structures_type_change(self, sync_coordinator):
        """Test conflict detection for type changes"""
        current = {"key": "string_value"}
        new = {"key": 123}  # Type changed from str to int

        has_conflict = sync_coordinator._compare_data_structures(current, new)

        assert has_conflict is True

    def test_compare_data_structures_no_conflict(self, sync_coordinator):
        """Test no conflict for compatible changes"""
        current = {"key1": "value1", "key2": 100}
        new = {"key1": "new_value", "key2": 200, "key3": "added"}

        has_conflict = sync_coordinator._compare_data_structures(current, new)

        assert has_conflict is False

    @pytest.mark.asyncio
    async def test_resolve_by_timestamp(self, sync_coordinator):
        """Test timestamp-based conflict resolution"""
        older = StateSnapshot("comp", {"data": "older"}, 1)
        older.timestamp = datetime.now() - timedelta(minutes=5)

        newer = StateSnapshot("comp", {"data": "newer"}, 2)
        newer.timestamp = datetime.now()

        resolved = await sync_coordinator._resolve_by_timestamp(older, newer)

        assert resolved == newer

    @pytest.mark.asyncio
    async def test_resolve_by_version(self, sync_coordinator):
        """Test version-based conflict resolution"""
        lower_version = StateSnapshot("comp", {"data": "v1"}, 1)
        higher_version = StateSnapshot("comp", {"data": "v2"}, 5)

        resolved = await sync_coordinator._resolve_by_version(
            lower_version, higher_version
        )

        assert resolved == higher_version

    @pytest.mark.asyncio
    async def test_resolve_by_merge(self, sync_coordinator):
        """Test merge-based conflict resolution"""
        current = StateSnapshot("comp", {"key1": "value1", "key2": 100}, 1)
        new = StateSnapshot("comp", {"key1": "new_value", "key3": "added"}, 2)

        resolved = await sync_coordinator._resolve_by_merge(current, new)

        # Should merge both states
        assert resolved.state_data["key1"] == "new_value"  # Updated
        assert resolved.state_data["key2"] == 100  # Preserved
        assert resolved.state_data["key3"] == "added"  # Added
        assert resolved.version == 3  # Version incremented

    def test_merge_state_data_nested_dicts(self, sync_coordinator):
        """Test merging nested dictionaries"""
        current = {"nested": {"a": 1, "b": 2}, "top": "value"}
        new = {"nested": {"b": 3, "c": 4}, "new_key": "new"}

        merged = sync_coordinator._merge_state_data(current, new)

        assert merged["nested"]["a"] == 1  # Preserved
        assert merged["nested"]["b"] == 3  # Updated
        assert merged["nested"]["c"] == 4  # Added
        assert merged["top"] == "value"  # Preserved
        assert merged["new_key"] == "new"  # Added

    @pytest.mark.asyncio
    async def test_handle_conflict_records_resolution(self, sync_coordinator):
        """Test conflict handling records resolution"""
        sync_coordinator.config["default_conflict_strategy"] = "version_wins"

        current = StateSnapshot("comp", {"data": "old"}, 1)
        new = StateSnapshot("comp", {"data": "new"}, 2)

        with patch.object(
            sync_coordinator, "publish_event", new_callable=AsyncMock
        ):
            resolved = await sync_coordinator._handle_conflict(
                "version_conflict", current, new
            )

        # Check resolution was recorded
        assert len(sync_coordinator.active_conflicts) == 1
        conflict = list(sync_coordinator.active_conflicts.values())[0]
        assert conflict.conflict_type == "version_conflict"
        assert conflict.resolution_strategy == "version_wins"


# ============================================================================
# Test Class: Component Registration
# ============================================================================


@pytest.mark.unit
class TestComponentRegistration:
    """Test component registration and connection management"""

    @pytest.mark.asyncio
    async def test_register_component_success(self, sync_coordinator):
        """Test successful component registration"""
        with patch.object(
            sync_coordinator, "publish_event", new_callable=AsyncMock
        ):
            success = await sync_coordinator.register_component(
                "test_comp", initial_state={"status": "active"}
            )

        assert success is True
        assert sync_coordinator.component_sync_status["test_comp"] == SyncState.SYNCED
        assert "test_comp" in sync_coordinator.component_states

    @pytest.mark.asyncio
    async def test_register_component_publishes_event(self, sync_coordinator):
        """Test component registration publishes event"""
        with patch.object(
            sync_coordinator, "publish_event", new_callable=AsyncMock
        ) as mock_publish:
            await sync_coordinator.register_component("comp")

            mock_publish.assert_called_once()
            call_args = mock_publish.call_args[1]
            assert call_args["event_type"] == "component_connected"

    @pytest.mark.asyncio
    async def test_unregister_component_success(self, sync_coordinator):
        """Test successful component unregistration"""
        await sync_coordinator.register_component("comp")

        with patch.object(
            sync_coordinator, "publish_event", new_callable=AsyncMock
        ):
            success = await sync_coordinator.unregister_component("comp")

        assert success is True
        assert sync_coordinator.component_sync_status["comp"] == SyncState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_unregister_component_publishes_event(self, sync_coordinator):
        """Test component unregistration publishes event"""
        await sync_coordinator.register_component("comp")

        with patch.object(
            sync_coordinator, "publish_event", new_callable=AsyncMock
        ) as mock_publish:
            await sync_coordinator.unregister_component("comp")

            mock_publish.assert_called_once()
            call_args = mock_publish.call_args[1]
            assert call_args["event_type"] == "component_disconnected"


# ============================================================================
# Test Class: State Rollback
# ============================================================================


@pytest.mark.unit
class TestStateRollback:
    """Test state versioning and rollback"""

    @pytest.mark.asyncio
    async def test_rollback_component_state_success(self, sync_coordinator):
        """Test successful state rollback"""
        # Create version history
        await sync_coordinator.update_component_state("comp", {"data": "v1"})
        await sync_coordinator.update_component_state("comp", {"data": "v2"})
        await sync_coordinator.update_component_state("comp", {"data": "v3"})

        with patch.object(
            sync_coordinator, "publish_event", new_callable=AsyncMock
        ):
            success = await sync_coordinator.rollback_component_state("comp", 2)

        assert success is True

        # Check state was rolled back
        current_state = await sync_coordinator.get_component_state("comp")
        assert current_state.state_data["data"] == "v2"
        assert current_state.version == 4  # New version created

    @pytest.mark.asyncio
    async def test_rollback_component_state_version_not_found(
        self, sync_coordinator
    ):
        """Test rollback fails for non-existent version"""
        await sync_coordinator.update_component_state("comp", {"data": "v1"})

        success = await sync_coordinator.rollback_component_state("comp", 99)

        assert success is False

    @pytest.mark.asyncio
    async def test_rollback_publishes_event(self, sync_coordinator):
        """Test rollback publishes state_rollback event"""
        await sync_coordinator.update_component_state("comp", {"data": "v1"})
        await sync_coordinator.update_component_state("comp", {"data": "v2"})

        with patch.object(
            sync_coordinator, "publish_event", new_callable=AsyncMock
        ) as mock_publish:
            await sync_coordinator.rollback_component_state("comp", 1)

            # Find rollback event call
            rollback_calls = [
                call
                for call in mock_publish.call_args_list
                if call[1].get("event_type") == "state_rollback"
            ]
            assert len(rollback_calls) > 0


# ============================================================================
# Test Class: Synchronization Status
# ============================================================================


@pytest.mark.unit
class TestSynchronizationStatus:
    """Test sync status and monitoring"""

    @pytest.mark.asyncio
    async def test_get_sync_status(self, sync_coordinator):
        """Test getting synchronization status"""
        # Register some components
        await sync_coordinator.register_component("comp1", initial_state={"a": 1})
        await sync_coordinator.register_component("comp2", initial_state={"b": 2})

        status = await sync_coordinator.get_sync_status()

        assert "sync_health" in status
        assert status["total_components"] == 2
        assert "status_summary" in status
        assert status["status_summary"]["synced"] == 2

    @pytest.mark.asyncio
    async def test_get_sync_status_health_calculation(self, sync_coordinator):
        """Test sync health percentage calculation"""
        # 3 synced, 1 error
        await sync_coordinator.register_component("comp1")
        await sync_coordinator.register_component("comp2")
        await sync_coordinator.register_component("comp3")
        sync_coordinator.component_sync_status["comp4"] = SyncState.ERROR

        status = await sync_coordinator.get_sync_status()

        # 3 out of 4 = 75% health
        assert status["sync_health"] == 75.0

    @pytest.mark.asyncio
    async def test_get_component_history(self, sync_coordinator):
        """Test retrieving component state history"""
        for i in range(10):
            await sync_coordinator.update_component_state("comp", {"version": i})

        history = await sync_coordinator.get_component_history("comp", limit=5)

        assert len(history) == 5
        # Should return most recent 5
        assert history[-1].state_data["version"] == 9

    @pytest.mark.asyncio
    async def test_sync_component_success(self, sync_coordinator):
        """Test forcing component synchronization"""
        with patch.object(
            sync_coordinator,
            "_fetch_component_state",
            new_callable=AsyncMock,
            return_value={"synced": True},
        ):
            success = await sync_coordinator.sync_component("test_comp")

        assert success is True
        assert "test_comp" in sync_coordinator.component_states

    @pytest.mark.asyncio
    async def test_sync_component_no_state_available(self, sync_coordinator):
        """Test sync fails when component state unavailable"""
        with patch.object(
            sync_coordinator,
            "_fetch_component_state",
            new_callable=AsyncMock,
            return_value=None,
        ):
            success = await sync_coordinator.sync_component("test_comp")

        assert success is False


# ============================================================================
# Test Class: Metrics and Health
# ============================================================================


@pytest.mark.unit
class TestMetricsAndHealth:
    """Test metrics collection and health monitoring"""

    @pytest.mark.asyncio
    async def test_get_metrics(self, sync_coordinator):
        """Test getting comprehensive metrics"""
        # Add some test data
        await sync_coordinator.register_component("comp1")
        await sync_coordinator.update_component_state("comp1", {"data": "test"})

        metrics = await sync_coordinator.get_metrics()

        assert "sync_status" in metrics
        assert "event_processing" in metrics
        assert "state_management" in metrics
        assert "conflict_resolution" in metrics

    @pytest.mark.asyncio
    async def test_get_health_healthy(self, sync_coordinator):
        """Test health status when system is healthy"""
        # All components synced
        await sync_coordinator.register_component("comp1")
        await sync_coordinator.register_component("comp2")

        health = await sync_coordinator.get_health()

        assert health["status"] == "healthy"
        assert health["sync_health"] == 100.0

    @pytest.mark.asyncio
    async def test_get_health_degraded(self, sync_coordinator):
        """Test health status when system is degraded"""
        # Mixed sync states - 70-90% synced
        await sync_coordinator.register_component("comp1")
        await sync_coordinator.register_component("comp2")
        sync_coordinator.component_sync_status["comp3"] = SyncState.ERROR

        health = await sync_coordinator.get_health()

        assert health["status"] in ["healthy", "degraded"]
        assert health["sync_health"] < 100.0

    @pytest.mark.asyncio
    async def test_get_health_unhealthy(self, sync_coordinator):
        """Test health status when system is unhealthy"""
        # Most components in error state
        sync_coordinator.component_sync_status["comp1"] = SyncState.ERROR
        sync_coordinator.component_sync_status["comp2"] = SyncState.ERROR
        sync_coordinator.component_sync_status["comp3"] = SyncState.ERROR
        sync_coordinator.component_sync_status["comp4"] = SyncState.SYNCED

        health = await sync_coordinator.get_health()

        assert health["status"] == "unhealthy"
        assert health["sync_health"] == 25.0


# ============================================================================
# Test Class: Event Handlers
# ============================================================================


@pytest.mark.unit
class TestEventHandlers:
    """Test built-in event handlers"""

    @pytest.mark.asyncio
    async def test_handle_state_change_updates_sync_time(
        self, sync_coordinator
    ):
        """Test state_changed handler updates last sync time"""
        event = Event(
            "e1",
            "state_changed",
            "src",
            None,
            {"component_id": "test_comp"},
        )

        await sync_coordinator._handle_state_change(event)

        assert "test_comp" in sync_coordinator.last_sync_times

    @pytest.mark.asyncio
    async def test_handle_component_connect_updates_status(
        self, sync_coordinator
    ):
        """Test component_connected handler updates sync status"""
        event = Event(
            "e1",
            "component_connected",
            "src",
            None,
            {"component_id": "new_comp"},
        )

        await sync_coordinator._handle_component_connect(event)

        assert sync_coordinator.component_sync_status["new_comp"] == SyncState.SYNCED

    @pytest.mark.asyncio
    async def test_handle_component_disconnect_updates_status(
        self, sync_coordinator
    ):
        """Test component_disconnected handler updates sync status"""
        event = Event(
            "e1",
            "component_disconnected",
            "src",
            None,
            {"component_id": "disconnected_comp"},
        )

        await sync_coordinator._handle_component_disconnect(event)

        assert (
            sync_coordinator.component_sync_status["disconnected_comp"]
            == SyncState.DISCONNECTED
        )

    @pytest.mark.asyncio
    async def test_handle_workflow_event_publishes_sync(
        self, sync_coordinator
    ):
        """Test workflow event handler publishes sync event"""
        event = Event(
            "e1",
            "workflow_started",
            "workflow",
            None,
            {"workflow_id": "wf_123", "status": "running"},
        )

        with patch.object(
            sync_coordinator, "publish_event", new_callable=AsyncMock
        ) as mock_publish:
            await sync_coordinator._handle_workflow_event(event)

            mock_publish.assert_called_once()
            call_args = mock_publish.call_args[1]
            assert call_args["event_type"] == "workflow_sync"


# ============================================================================
# Test Class: StateSnapshot
# ============================================================================


@pytest.mark.unit
class TestStateSnapshot:
    """Test StateSnapshot dataclass"""

    def test_state_snapshot_checksum_calculation(self):
        """Test checksum is calculated automatically"""
        snapshot = StateSnapshot("comp", {"key": "value"}, 1)

        assert snapshot.checksum != ""
        assert len(snapshot.checksum) == 64  # SHA256 hex length

    def test_state_snapshot_checksum_consistency(self):
        """Test checksum is consistent for same data"""
        snapshot1 = StateSnapshot("comp", {"a": 1, "b": 2}, 1)
        snapshot2 = StateSnapshot("comp", {"a": 1, "b": 2}, 1)

        assert snapshot1.checksum == snapshot2.checksum

    def test_state_snapshot_checksum_different_data(self):
        """Test checksum differs for different data"""
        snapshot1 = StateSnapshot("comp", {"a": 1}, 1)
        snapshot2 = StateSnapshot("comp", {"a": 2}, 1)

        assert snapshot1.checksum != snapshot2.checksum


# ============================================================================
# Test Class: Event Properties
# ============================================================================


@pytest.mark.unit
class TestEventProperties:
    """Test Event dataclass properties"""

    def test_event_is_expired_false(self):
        """Test event is not expired within TTL"""
        event = Event(
            "e1",
            "test",
            "src",
            None,
            {},
            ttl_seconds=3600,  # 1 hour
        )

        assert event.is_expired is False

    def test_event_is_expired_true(self):
        """Test event is expired after TTL"""
        event = Event(
            "e1",
            "test",
            "src",
            None,
            {},
            ttl_seconds=1,  # 1 second
        )
        event.timestamp = datetime.now() - timedelta(seconds=2)

        assert event.is_expired is True


# ============================================================================
# Test Class: FastAPI Routes
# ============================================================================


@pytest.mark.unit
class TestFastAPIRoutes:
    """Test FastAPI endpoint setup"""

    def test_routes_registered(self, sync_coordinator):
        """Test all required routes are registered"""
        routes = [route.path for route in sync_coordinator.app.routes]

        assert "/register" in routes
        assert "/register/{component_id}" in routes
        assert "/state/{component_id}" in routes
        assert "/sync/{component_id}" in routes
        assert "/rollback/{component_id}" in routes
        assert "/events" in routes
        assert "/status" in routes
        assert "/metrics" in routes
        assert "/health" in routes


# ============================================================================
# Test Class: Shutdown
# ============================================================================


@pytest.mark.unit
class TestShutdown:
    """Test graceful shutdown"""

    @pytest.mark.asyncio
    async def test_shutdown_cancels_background_tasks(self, sync_coordinator):
        """Test shutdown cancels all background tasks"""
        sync_coordinator.event_processor_task = AsyncMock()
        sync_coordinator.sync_monitor_task = AsyncMock()
        sync_coordinator.cleanup_task = AsyncMock()
        sync_coordinator.is_initialized = True

        await sync_coordinator.shutdown()

        sync_coordinator.event_processor_task.cancel.assert_called_once()
        sync_coordinator.sync_monitor_task.cancel.assert_called_once()
        sync_coordinator.cleanup_task.cancel.assert_called_once()
        assert sync_coordinator.is_initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_closes_thread_pool(self, sync_coordinator):
        """Test shutdown closes thread pool"""
        sync_coordinator.thread_pool = MagicMock()
        sync_coordinator.is_initialized = True

        await sync_coordinator.shutdown()

        sync_coordinator.thread_pool.shutdown.assert_called_once_with(wait=True)


# ============================================================================
# Test Class: Convenience Functions
# ============================================================================


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    @pytest.mark.asyncio
    async def test_create_sync_coordinator(self):
        """Test create_sync_coordinator factory function"""
        with patch.object(SyncCoordinator, "initialize", new_callable=AsyncMock):
            coordinator = await create_sync_coordinator(
                config={"sync_interval": 10}
            )

            assert isinstance(coordinator, SyncCoordinator)
            assert coordinator.sync_interval == 10
            coordinator.initialize.assert_called_once()
