import asyncio
from datetime import datetime
import pytest

from core.sparc.state_manager import StateManager, StateType


@pytest.mark.asyncio
async def test_initialize_state_defaults_populates_metadata_and_history():
    manager = StateManager(history_size=10)

    state = await manager.initialize_state()

    assert state is not None
    assert manager.get_current_state() is not None
    # Default type should fall back to system status
    assert state.state_type == StateType.SYSTEM_STATUS

    # Defaults injected by initialize_state
    assert "timestamp" in state.data
    assert state.metadata.get("source") == "initialize_state"
    assert state.data.get("system_bootstrap") is True

    # History should have at least one entry
    assert len(manager.get_recent_states(5)) >= 1


@pytest.mark.asyncio
async def test_initialize_state_with_custom_data_sets_educational_context():
    manager = StateManager(history_size=10)

    state = await manager.initialize_state({
        "subject_area": "Science",
        "grade_level": 7,
        "content": "Intro to Solar System"
    })

    assert state.subject_area == "Science"
    assert state.grade_level == 7
    # Presence of 'content' should infer EDUCATIONAL_CONTENT
    assert state.state_type == StateType.EDUCATIONAL_CONTENT


@pytest.mark.asyncio
async def test_calculate_reward_balances_objectives_and_time():
    manager = StateManager()

    # Fast and complete -> high reward
    r_fast_complete = await manager.calculate_reward({
        "objectives_met": 5,
        "total_objectives": 5,
        "execution_time": 3.0,
    })

    # Slow and partial -> lower reward
    r_slow_partial = await manager.calculate_reward({
        "objectives_met": 2,
        "total_objectives": 5,
        "execution_time": 120.0,
    })

    assert 0.0 <= r_slow_partial <= 1.0
    assert 0.0 <= r_fast_complete <= 1.0
    assert r_fast_complete > r_slow_partial

    # Quality metrics should record last reward
    assert "last_reward" in manager.quality_metrics

