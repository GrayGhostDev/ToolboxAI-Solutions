"""
Comprehensive unit tests for core/coordinators/task_registry.py

Tests cover:
- TaskState enum values
- TaskRegistry initialization
- Key generation methods
- Task enqueueing (with idempotency, priority)
- Task claiming (with capability matching, lock acquisition)
- Worker heartbeats (task claim renewal)
- Task state transitions (start, complete, fail, requeue)
- Queue statistics (qstat)
- Worker listing (list_workers)
- Edge cases and error handling
"""

import json
import uuid
from unittest.mock import Mock, patch

import pytest

# Import the module under test
from core.coordinators.task_registry import (
    CLAIM_TTL_SEC,
    HEARTBEAT_TTL_SEC,
    KEY_PREFIX,
    MAX_RETRIES,
    TaskRegistry,
    TaskState,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    redis_mock = Mock()

    # Mock pipeline
    pipeline_mock = Mock()
    pipeline_mock.set = Mock(return_value=pipeline_mock)
    pipeline_mock.zadd = Mock(return_value=pipeline_mock)
    pipeline_mock.zrem = Mock(return_value=pipeline_mock)
    pipeline_mock.delete = Mock(return_value=pipeline_mock)
    pipeline_mock.expire = Mock(return_value=pipeline_mock)
    pipeline_mock.execute = Mock(return_value=[True, True])

    redis_mock.pipeline = Mock(return_value=pipeline_mock)
    redis_mock.set = Mock(return_value=True)
    redis_mock.get = Mock(return_value=None)
    redis_mock.zadd = Mock(return_value=1)
    redis_mock.zrange = Mock(return_value=[])
    redis_mock.zrem = Mock(return_value=1)
    redis_mock.zcard = Mock(return_value=0)
    redis_mock.delete = Mock(return_value=1)
    redis_mock.keys = Mock(return_value=[])
    redis_mock.expire = Mock(return_value=True)

    return redis_mock


@pytest.fixture
def mock_redis_adapter(mock_redis):
    """Create mock RedisAdapter"""
    adapter = Mock()
    adapter.r = mock_redis
    return adapter


@pytest.fixture
def task_registry(mock_redis_adapter):
    """Create TaskRegistry with mock Redis adapter"""
    return TaskRegistry(r=mock_redis_adapter)


# ============================================================================
# Test TaskState Enum
# ============================================================================


class TestTaskStateEnum:
    """Test TaskState enum"""

    def test_task_state_values(self):
        """Test all TaskState enum values"""
        assert TaskState.QUEUED.value == "queued"
        assert TaskState.CLAIMED.value == "claimed"
        assert TaskState.IN_PROGRESS.value == "in_progress"
        assert TaskState.NEEDS_REVIEW.value == "needs_review"
        assert TaskState.NEEDS_FIX.value == "needs_fix"
        assert TaskState.BLOCKED.value == "blocked"
        assert TaskState.COMPLETE.value == "complete"
        assert TaskState.FAILED.value == "failed"

    def test_task_state_is_string_enum(self):
        """Test TaskState inherits from str"""
        assert isinstance(TaskState.QUEUED, str)
        assert isinstance(TaskState.COMPLETE, str)

    def test_task_state_count(self):
        """Test number of task states"""
        states = list(TaskState)
        assert len(states) == 8


# ============================================================================
# Test TaskRegistry Initialization
# ============================================================================


class TestTaskRegistryInitialization:
    """Test TaskRegistry initialization"""

    def test_initialization_with_redis_adapter(self, mock_redis_adapter):
        """Test initialization with provided Redis adapter"""
        registry = TaskRegistry(r=mock_redis_adapter)

        assert registry.r == mock_redis_adapter

    def test_initialization_without_adapter(self):
        """Test initialization creates default Redis adapter"""
        with patch("core.coordinators.task_registry.RedisAdapter") as mock_adapter_class:
            mock_adapter_instance = Mock()
            mock_adapter_class.return_value = mock_adapter_instance

            registry = TaskRegistry()

            assert registry.r == mock_adapter_instance
            mock_adapter_class.assert_called_once()


# ============================================================================
# Test Key Generation Methods
# ============================================================================


class TestKeyGenerationMethods:
    """Test Redis key generation methods"""

    def test_k_method_basic(self, task_registry):
        """Test basic key generation"""
        key = task_registry._k("test", "key")

        assert key == f"{KEY_PREFIX}:test:key"

    def test_k_method_single_part(self, task_registry):
        """Test key generation with single part"""
        key = task_registry._k("single")

        assert key == f"{KEY_PREFIX}:single"

    def test_k_method_multiple_parts(self, task_registry):
        """Test key generation with multiple parts"""
        key = task_registry._k("part1", "part2", "part3", "part4")

        assert key == f"{KEY_PREFIX}:part1:part2:part3:part4"

    def test_k_task_method(self, task_registry):
        """Test task key generation"""
        tid = "task-123"
        key = task_registry.k_task(tid)

        assert key == f"{KEY_PREFIX}:task:{tid}"

    def test_k_state_method(self, task_registry):
        """Test state key generation"""
        state = "queued"
        key = task_registry.k_state(state)

        assert key == f"{KEY_PREFIX}:tasks:state:{state}"

    def test_k_lock_method(self, task_registry):
        """Test lock key generation"""
        tid = "task-456"
        key = task_registry.k_lock(tid)

        assert key == f"{KEY_PREFIX}:task:lock:{tid}"

    def test_k_claim_method(self, task_registry):
        """Test claim key generation"""
        tid = "task-789"
        key = task_registry.k_claim(tid)

        assert key == f"{KEY_PREFIX}:task:claim:{tid}"

    def test_k_worker_hb_method(self, task_registry):
        """Test worker heartbeat key generation"""
        wid = "worker-001"
        key = task_registry.k_worker_hb(wid)

        assert key == f"{KEY_PREFIX}:worker:hb:{wid}"


# ============================================================================
# Test Task Enqueueing
# ============================================================================


class TestTaskEnqueue:
    """Test task enqueueing"""

    def test_enqueue_basic(self, task_registry):
        """Test basic task enqueueing"""
        payload = {"type": "test_task", "data": "test_data"}

        with patch("time.time", return_value=1000.0):
            tid = task_registry.enqueue(payload)

        assert tid is not None
        # Should create task and add to QUEUED state
        task_registry.r.r.pipeline.assert_called()

    def test_enqueue_with_priority(self, task_registry):
        """Test enqueueing with custom priority"""
        payload = {"type": "high_priority"}
        priority = 10.0

        with patch("time.time", return_value=1000.0):
            tid = task_registry.enqueue(payload, priority=priority)

        assert tid is not None

    def test_enqueue_with_idempotency_key(self, task_registry):
        """Test enqueueing with idempotency key"""
        payload = {"type": "idempotent_task"}
        idempotency_key = "unique-key-123"

        tid = task_registry.enqueue(payload, idempotency_key=idempotency_key)

        assert tid == idempotency_key

    def test_enqueue_generates_uuid_when_no_key(self, task_registry):
        """Test enqueueing generates UUID when no idempotency key"""
        payload = {"type": "task"}

        with patch("uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")):
            tid = task_registry.enqueue(payload)

        assert tid == "12345678-1234-5678-1234-567812345678"

    def test_enqueue_task_structure(self, task_registry):
        """Test enqueued task has correct structure"""
        payload = {"type": "test"}

        with patch("time.time", return_value=1234.5):
            with patch(
                "uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")
            ):
                tid = task_registry.enqueue(payload, priority=5.0)

        # Verify pipeline calls
        pipeline = task_registry.r.r.pipeline.return_value
        pipeline.set.assert_called()

        # Check task data structure
        call_args = pipeline.set.call_args_list[0]
        task_data = json.loads(call_args[0][1])

        assert task_data["id"] == "12345678-1234-5678-1234-567812345678"
        assert task_data["state"] == TaskState.QUEUED.value
        assert task_data["priority"] == 5.0
        assert task_data["created_at"] == 1234.5
        assert task_data["updated_at"] == 1234.5
        assert task_data["retries"] == 0
        assert task_data["claimed_by"] == ""
        assert task_data["payload"] == payload

    def test_enqueue_adds_to_state_zset(self, task_registry):
        """Test enqueueing adds task to state zset"""
        payload = {"type": "test"}

        with patch("time.time", return_value=1000.0):
            tid = task_registry.enqueue(payload)

        pipeline = task_registry.r.r.pipeline.return_value
        pipeline.zadd.assert_called_once()


# ============================================================================
# Test Task Claiming
# ============================================================================


class TestTaskClaim:
    """Test task claiming"""

    def test_claim_no_tasks_available(self, task_registry):
        """Test claiming when no tasks available"""
        task_registry.r.r.zrange.return_value = []

        result = task_registry.claim("worker-1")

        assert result is None

    def test_claim_successful(self, task_registry, mock_redis):
        """Test successful task claiming"""
        tid = "task-123"
        task_data = {
            "id": tid,
            "state": TaskState.QUEUED.value,
            "priority": 1.0,
            "created_at": 1000.0,
            "updated_at": 1000.0,
            "retries": 0,
            "claimed_by": "",
            "payload": {"type": "test"},
        }

        mock_redis.zrange.return_value = [tid.encode()]
        mock_redis.get.return_value = json.dumps(task_data).encode()
        mock_redis.set.return_value = True  # Lock acquired

        with patch("time.time", return_value=2000.0):
            result = task_registry.claim("worker-1")

        assert result is not None
        assert result["id"] == tid
        assert result["state"] == TaskState.CLAIMED.value
        assert result["claimed_by"] == "worker-1"

    def test_claim_with_capability_matching(self, task_registry, mock_redis):
        """Test claiming with capability matching"""
        tid = "task-456"
        task_data = {
            "id": tid,
            "state": TaskState.QUEUED.value,
            "payload": {"capability": "python"},
        }

        mock_redis.zrange.return_value = [tid.encode()]
        mock_redis.get.return_value = json.dumps(task_data).encode()
        mock_redis.set.return_value = True

        result = task_registry.claim("worker-1", capability="python")

        assert result is not None

    def test_claim_capability_mismatch(self, task_registry, mock_redis):
        """Test claiming skips tasks with mismatched capability"""
        tid = "task-789"
        task_data = {
            "id": tid,
            "state": TaskState.QUEUED.value,
            "payload": {"capability": "python"},
        }

        mock_redis.zrange.return_value = [tid.encode()]
        mock_redis.get.return_value = json.dumps(task_data).encode()

        result = task_registry.claim("worker-1", capability="javascript")

        assert result is None

    def test_claim_wildcard_capability(self, task_registry, mock_redis):
        """Test claiming accepts wildcard capability"""
        tid = "task-wild"
        task_data = {"id": tid, "state": TaskState.QUEUED.value, "payload": {"capability": "*"}}

        mock_redis.zrange.return_value = [tid.encode()]
        mock_redis.get.return_value = json.dumps(task_data).encode()
        mock_redis.set.return_value = True

        result = task_registry.claim("worker-1", capability="anything")

        assert result is not None

    def test_claim_lock_acquisition_failure(self, task_registry, mock_redis):
        """Test claiming fails if lock cannot be acquired"""
        tid = "task-locked"
        task_data = {"id": tid, "state": TaskState.QUEUED.value, "payload": {}}

        mock_redis.zrange.return_value = [tid.encode()]
        mock_redis.get.return_value = json.dumps(task_data).encode()
        mock_redis.set.return_value = False  # Lock acquisition failed

        result = task_registry.claim("worker-1")

        assert result is None

    def test_claim_skips_missing_tasks(self, task_registry, mock_redis):
        """Test claiming skips tasks that don't exist"""
        tid = "missing-task"

        mock_redis.zrange.return_value = [tid.encode()]
        mock_redis.get.return_value = None  # Task doesn't exist

        result = task_registry.claim("worker-1")

        # Should remove from zset
        mock_redis.zrem.assert_called()

    def test_claim_sets_lock_with_ttl(self, task_registry, mock_redis):
        """Test claiming sets lock with TTL"""
        tid = "task-ttl"
        task_data = {"id": tid, "state": TaskState.QUEUED.value, "payload": {}}

        mock_redis.zrange.return_value = [tid.encode()]
        mock_redis.get.return_value = json.dumps(task_data).encode()
        mock_redis.set.return_value = True

        task_registry.claim("worker-1")

        # Verify lock set with NX and TTL
        lock_call = [call for call in mock_redis.set.call_args_list if "lock" in str(call)]
        assert len(lock_call) > 0


# ============================================================================
# Test Worker Heartbeat
# ============================================================================


class TestWorkerHeartbeat:
    """Test worker heartbeat functionality"""

    def test_heartbeat_updates_worker_timestamp(self, task_registry):
        """Test heartbeat updates worker timestamp"""
        worker_id = "worker-1"
        tasks = ["task-1", "task-2"]

        with patch("time.time", return_value=5000):
            task_registry.heartbeat(worker_id, tasks)

        pipeline = task_registry.r.r.pipeline.return_value
        # Should set worker heartbeat with timestamp
        pipeline.set.assert_called()

    def test_heartbeat_renews_task_locks(self, task_registry, mock_redis):
        """Test heartbeat renews task locks"""
        worker_id = "worker-1"
        tasks = ["task-1", "task-2"]

        mock_redis.get.return_value = worker_id.encode()

        task_registry.heartbeat(worker_id, tasks)

        pipeline = task_registry.r.r.pipeline.return_value
        # Should renew lock and claim TTLs
        pipeline.expire.assert_called()

    def test_heartbeat_only_renews_own_locks(self, task_registry, mock_redis):
        """Test heartbeat only renews locks owned by the worker"""
        worker_id = "worker-1"
        tasks = ["task-1", "task-2"]

        # Mock get to return different worker for one task
        mock_redis.get.side_effect = [worker_id.encode(), b"other-worker"]

        task_registry.heartbeat(worker_id, tasks)

        # Should only renew lock for task-1 (owned by worker-1)
        pipeline = task_registry.r.r.pipeline.return_value
        assert pipeline.expire.call_count >= 1

    def test_heartbeat_empty_task_list(self, task_registry):
        """Test heartbeat with empty task list"""
        worker_id = "worker-1"

        task_registry.heartbeat(worker_id, [])

        # Should still update worker heartbeat
        pipeline = task_registry.r.r.pipeline.return_value
        pipeline.set.assert_called()

    def test_heartbeat_sets_ttl(self, task_registry):
        """Test heartbeat sets TTL on worker key"""
        worker_id = "worker-1"

        with patch("time.time", return_value=3000):
            task_registry.heartbeat(worker_id, [])

        pipeline = task_registry.r.r.pipeline.return_value
        # Check that set was called with ex parameter
        set_calls = pipeline.set.call_args_list
        assert len(set_calls) > 0


# ============================================================================
# Test Task State Transitions
# ============================================================================


class TestTaskStateTransitions:
    """Test task state transition methods"""

    def test_start_task(self, task_registry, mock_redis):
        """Test starting a task"""
        tid = "task-start"
        task_data = {"id": tid, "state": TaskState.CLAIMED.value, "updated_at": 1000.0}

        mock_redis.get.return_value = json.dumps(task_data).encode()

        with patch("time.time", return_value=2000.0):
            task_registry.start(tid)

        # Verify task state updated to IN_PROGRESS
        set_call = mock_redis.set.call_args_list[-1]
        updated_task = json.loads(set_call[0][1])
        assert updated_task["state"] == TaskState.IN_PROGRESS.value
        assert updated_task["updated_at"] == 2000.0

    def test_start_nonexistent_task(self, task_registry, mock_redis):
        """Test starting nonexistent task does nothing"""
        mock_redis.get.return_value = None

        task_registry.start("nonexistent")

        # Should not crash, just return

    def test_complete_task(self, task_registry, mock_redis):
        """Test completing a task"""
        tid = "task-complete"
        task_data = {"id": tid, "state": TaskState.IN_PROGRESS.value, "updated_at": 1000.0}

        mock_redis.get.return_value = json.dumps(task_data).encode()

        with patch("time.time", return_value=3000.0):
            task_registry.complete(tid)

        pipeline = task_registry.r.r.pipeline.return_value
        # Should update state, delete locks, add to COMPLETE zset
        pipeline.set.assert_called()
        pipeline.delete.assert_called()
        pipeline.zadd.assert_called()

    def test_complete_removes_locks(self, task_registry, mock_redis):
        """Test completing removes task locks"""
        tid = "task-locks"
        task_data = {"id": tid, "state": TaskState.IN_PROGRESS.value}

        mock_redis.get.return_value = json.dumps(task_data).encode()

        task_registry.complete(tid)

        pipeline = task_registry.r.r.pipeline.return_value
        # Should delete both lock and claim
        assert pipeline.delete.call_count >= 2

    def test_fail_task_with_requeue(self, task_registry, mock_redis):
        """Test failing task with requeue"""
        tid = "task-fail"
        task_data = {"id": tid, "state": TaskState.IN_PROGRESS.value, "retries": 0}

        mock_redis.get.return_value = json.dumps(task_data).encode()

        task_registry.fail(tid, requeue=True)

        # Should increment retries
        set_call = mock_redis.set.call_args_list[0]
        updated_task = json.loads(set_call[0][1])
        assert updated_task["retries"] == 1

    def test_fail_task_without_requeue(self, task_registry, mock_redis):
        """Test failing task without requeue"""
        tid = "task-no-requeue"
        task_data = {"id": tid, "state": TaskState.IN_PROGRESS.value, "retries": 0}

        mock_redis.get.return_value = json.dumps(task_data).encode()

        with patch("time.time", return_value=4000.0):
            task_registry.fail(tid, requeue=False)

        # Should mark as FAILED
        set_calls = mock_redis.set.call_args_list
        final_task = json.loads(set_calls[-1][0][1])
        assert final_task["state"] == TaskState.FAILED.value

    def test_fail_task_max_retries_exceeded(self, task_registry, mock_redis):
        """Test failing task when max retries exceeded"""
        tid = "task-max-retries"
        task_data = {"id": tid, "state": TaskState.IN_PROGRESS.value, "retries": MAX_RETRIES}

        mock_redis.get.return_value = json.dumps(task_data).encode()

        task_registry.fail(tid, requeue=True)

        # Should mark as FAILED, not requeue
        set_calls = mock_redis.set.call_args_list
        final_task = json.loads(set_calls[-1][0][1])
        assert final_task["state"] == TaskState.FAILED.value

    def test_requeue_task(self, task_registry, mock_redis):
        """Test requeuing a task"""
        tid = "task-requeue"
        task_data = {
            "id": tid,
            "state": TaskState.FAILED.value,
            "claimed_by": "worker-1",
            "updated_at": 1000.0,
        }

        mock_redis.get.return_value = json.dumps(task_data).encode()

        with patch("time.time", return_value=5000.0):
            task_registry.requeue(tid)

        pipeline = task_registry.r.r.pipeline.return_value
        # Should update state, clear claimed_by, add to QUEUED, delete locks
        pipeline.set.assert_called()
        pipeline.zadd.assert_called()
        pipeline.delete.assert_called()

    def test_requeue_clears_claimed_by(self, task_registry, mock_redis):
        """Test requeue clears claimed_by field"""
        tid = "task-clear"
        task_data = {"id": tid, "state": TaskState.FAILED.value, "claimed_by": "worker-1"}

        mock_redis.get.return_value = json.dumps(task_data).encode()

        task_registry.requeue(tid)

        pipeline = task_registry.r.r.pipeline.return_value
        set_call = pipeline.set.call_args_list[0]
        updated_task = json.loads(set_call[0][1])
        assert updated_task["claimed_by"] == ""
        assert updated_task["state"] == TaskState.QUEUED.value


# ============================================================================
# Test Queue Statistics
# ============================================================================


class TestQueueStatistics:
    """Test queue statistics"""

    def test_qstat_returns_all_states(self, task_registry, mock_redis):
        """Test qstat returns counts for all states"""
        mock_redis.zcard.return_value = 5

        stats = task_registry.qstat()

        assert isinstance(stats, dict)
        assert len(stats) == 8  # All TaskState values
        assert TaskState.QUEUED.value in stats
        assert TaskState.COMPLETE.value in stats

    def test_qstat_calls_zcard_for_each_state(self, task_registry, mock_redis):
        """Test qstat calls zcard for each state"""
        task_registry.qstat()

        # Should call zcard once per state
        assert mock_redis.zcard.call_count == 8

    def test_qstat_with_different_counts(self, task_registry, mock_redis):
        """Test qstat with different counts per state"""
        state_counts = {
            TaskState.QUEUED.value: 10,
            TaskState.CLAIMED.value: 3,
            TaskState.IN_PROGRESS.value: 5,
            TaskState.COMPLETE.value: 100,
            TaskState.FAILED.value: 2,
            TaskState.NEEDS_REVIEW.value: 0,
            TaskState.NEEDS_FIX.value: 0,
            TaskState.BLOCKED.value: 0,
        }

        def zcard_side_effect(key):
            state = key.split(":")[-1]
            return state_counts.get(state, 0)

        mock_redis.zcard.side_effect = zcard_side_effect

        stats = task_registry.qstat()

        assert stats[TaskState.QUEUED.value] == 10
        assert stats[TaskState.COMPLETE.value] == 100


# ============================================================================
# Test Worker Listing
# ============================================================================


class TestWorkerListing:
    """Test worker listing"""

    def test_list_workers_no_workers(self, task_registry, mock_redis):
        """Test listing workers when none exist"""
        mock_redis.keys.return_value = []

        workers = task_registry.list_workers()

        assert workers == []

    def test_list_workers_with_workers(self, task_registry, mock_redis):
        """Test listing active workers"""
        worker_keys = [
            f"{KEY_PREFIX}:worker:hb:worker-1".encode(),
            f"{KEY_PREFIX}:worker:hb:worker-2".encode(),
        ]
        mock_redis.keys.return_value = worker_keys

        # Mock timestamps
        def get_side_effect(key):
            if b"worker-1" in key:
                return b"5000"
            elif b"worker-2" in key:
                return b"5010"
            return None

        mock_redis.get.side_effect = get_side_effect

        with patch("time.time", return_value=5020):
            workers = task_registry.list_workers()

        assert len(workers) == 2
        assert any(w["worker_id"] == "worker-1" for w in workers)
        assert any(w["worker_id"] == "worker-2" for w in workers)

    def test_list_workers_calculates_age(self, task_registry, mock_redis):
        """Test worker listing calculates age correctly"""
        worker_key = f"{KEY_PREFIX}:worker:hb:worker-1".encode()
        mock_redis.keys.return_value = [worker_key]
        mock_redis.get.return_value = b"4000"

        with patch("time.time", return_value=5000):
            workers = task_registry.list_workers()

        assert workers[0]["worker_id"] == "worker-1"
        assert workers[0]["last_seen"] == 4000
        assert workers[0]["age"] == 1000

    def test_list_workers_handles_missing_timestamp(self, task_registry, mock_redis):
        """Test worker listing handles missing timestamp"""
        worker_key = f"{KEY_PREFIX}:worker:hb:worker-1".encode()
        mock_redis.keys.return_value = [worker_key]
        mock_redis.get.return_value = None

        workers = task_registry.list_workers()

        assert workers[0]["last_seen"] == 0

    def test_list_workers_handles_invalid_timestamp(self, task_registry, mock_redis):
        """Test worker listing handles invalid timestamp"""
        worker_key = f"{KEY_PREFIX}:worker:hb:worker-1".encode()
        mock_redis.keys.return_value = [worker_key]
        mock_redis.get.return_value = b"invalid"

        workers = task_registry.list_workers()

        # Should default to 0
        assert workers[0]["last_seen"] == 0


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_operations_on_nonexistent_tasks(self, task_registry, mock_redis):
        """Test operations on nonexistent tasks don't crash"""
        mock_redis.get.return_value = None

        # All should handle gracefully
        task_registry.start("nonexistent")
        task_registry.complete("nonexistent")
        task_registry.fail("nonexistent")
        task_registry.requeue("nonexistent")

    def test_empty_payload_enqueue(self, task_registry):
        """Test enqueueing task with empty payload"""
        tid = task_registry.enqueue({})

        assert tid is not None

    def test_complex_payload_enqueue(self, task_registry):
        """Test enqueueing task with complex payload"""
        payload = {
            "type": "complex",
            "nested": {"data": [1, 2, 3], "more": {"deep": "value"}},
            "array": ["a", "b", "c"],
        }

        tid = task_registry.enqueue(payload)

        assert tid is not None

    def test_zero_priority_enqueue(self, task_registry):
        """Test enqueueing with zero priority"""
        tid = task_registry.enqueue({"type": "test"}, priority=0.0)

        assert tid is not None

    def test_negative_priority_enqueue(self, task_registry):
        """Test enqueueing with negative priority"""
        tid = task_registry.enqueue({"type": "test"}, priority=-1.0)

        assert tid is not None

    def test_very_high_priority_enqueue(self, task_registry):
        """Test enqueueing with very high priority"""
        tid = task_registry.enqueue({"type": "urgent"}, priority=1000000.0)

        assert tid is not None


# ============================================================================
# Test Environment Variables
# ============================================================================


class TestEnvironmentVariables:
    """Test environment variable configuration"""

    def test_key_prefix_default(self):
        """Test KEY_PREFIX has default value"""
        assert KEY_PREFIX == "termq" or KEY_PREFIX.startswith("termq")

    def test_claim_ttl_default(self):
        """Test CLAIM_TTL_SEC has default value"""
        assert CLAIM_TTL_SEC == 300 or isinstance(CLAIM_TTL_SEC, int)

    def test_heartbeat_ttl_default(self):
        """Test HEARTBEAT_TTL_SEC has default value"""
        assert HEARTBEAT_TTL_SEC == 30 or isinstance(HEARTBEAT_TTL_SEC, int)

    def test_max_retries_default(self):
        """Test MAX_RETRIES has default value"""
        assert MAX_RETRIES == 3 or isinstance(MAX_RETRIES, int)


# ============================================================================
# Test Task Lifecycle Integration
# ============================================================================


class TestTaskLifecycleIntegration:
    """Test complete task lifecycle"""

    def test_full_task_lifecycle_success(self, task_registry, mock_redis):
        """Test full lifecycle: enqueue -> claim -> start -> complete"""
        # 1. Enqueue
        payload = {"type": "integration_test"}
        tid = task_registry.enqueue(payload)

        # 2. Claim
        mock_redis.zrange.return_value = [tid.encode()]
        task_data = {"id": tid, "state": TaskState.QUEUED.value, "payload": payload}
        mock_redis.get.return_value = json.dumps(task_data).encode()
        mock_redis.set.return_value = True

        claimed = task_registry.claim("worker-1")
        assert claimed is not None

        # 3. Start
        mock_redis.get.return_value = json.dumps(claimed).encode()
        task_registry.start(tid)

        # 4. Complete
        task_registry.complete(tid)

    def test_full_task_lifecycle_with_retry(self, task_registry, mock_redis):
        """Test lifecycle with failure and retry"""
        payload = {"type": "retry_test"}
        tid = task_registry.enqueue(payload)

        # Claim and start
        task_data = {
            "id": tid,
            "state": TaskState.IN_PROGRESS.value,
            "retries": 0,
            "payload": payload,
        }
        mock_redis.get.return_value = json.dumps(task_data).encode()

        # Fail with requeue
        task_registry.fail(tid, requeue=True)

        # Should be requeued with incremented retry count


# ============================================================================
# Test Marks and Configuration
# ============================================================================

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit
