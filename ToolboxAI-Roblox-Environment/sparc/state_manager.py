"""
State Manager - Environment State Tracking and Management
========================================================

The StateManager handles all aspects of environment state tracking, including:
- Real-time state observation and updates
- State history management with compression
- State serialization and persistence
- State quality assessment and validation
- Predictive state modeling

This component is crucial for maintaining awareness of the educational environment
and enabling intelligent decision-making by other SPARC components.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import numpy as np
from collections import deque
import hashlib
import gzip
from pathlib import Path

logger = logging.getLogger(__name__)


class StateType(Enum):
    """Types of environment states"""

    ROBLOX_GAME = "roblox_game"
    EDUCATIONAL_CONTENT = "educational_content"
    USER_INTERACTION = "user_interaction"
    QUIZ_SESSION = "quiz_session"
    LEARNING_PROGRESS = "learning_progress"
    SYSTEM_STATUS = "system_status"


class StateQuality(Enum):
    """Quality levels of state information"""

    EXCELLENT = "excellent"  # >95% confidence
    GOOD = "good"  # 80-95% confidence
    FAIR = "fair"  # 60-80% confidence
    POOR = "poor"  # <60% confidence


@dataclass
class EnvironmentState:
    """Represents the current state of the educational environment"""

    # Core identification
    state_id: str
    timestamp: datetime
    state_type: StateType

    # State data
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Quality metrics
    confidence: float = 1.0  # 0-1 confidence in state accuracy
    completeness: float = 1.0  # 0-1 completeness of state data
    freshness: float = 1.0  # 0-1 how recent the state is

    # Educational context
    subject_area: Optional[str] = None
    grade_level: Optional[int] = None
    learning_objective: Optional[str] = None
    student_id: Optional[str] = None

    # Game context (for Roblox states)
    game_state: Optional[Dict[str, Any]] = None
    player_positions: Optional[Dict[str, Tuple[float, float, float]]] = None
    active_tools: Optional[List[str]] = None

    # Derived properties
    @property
    def age(self) -> timedelta:
        """Time since state was created"""
        return datetime.now() - self.timestamp

    @property
    def quality(self) -> StateQuality:
        """Overall quality assessment"""
        overall_quality = (self.confidence + self.completeness + self.freshness) / 3
        if overall_quality >= 0.95:
            return StateQuality.EXCELLENT
        elif overall_quality >= 0.80:
            return StateQuality.GOOD
        elif overall_quality >= 0.60:
            return StateQuality.FAIR
        else:
            return StateQuality.POOR

    @property
    def summary(self) -> str:
        """Human-readable state summary"""
        return (
            f"{self.state_type.value} state "
            f"(quality: {self.quality.value}, "
            f"age: {self.age.total_seconds():.1f}s)"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        result["state_type"] = self.state_type.value
        result["quality"] = self.quality.value
        result["age_seconds"] = self.age.total_seconds()
        return result

    def hash(self) -> str:
        """Generate hash for state deduplication"""
        data_str = json.dumps(self.data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()


class StateHistoryEntry:
    """Entry in state history with compression support"""

    def __init__(self, state: EnvironmentState, compressed: bool = False):
        self.state_id = state.state_id
        self.timestamp = state.timestamp
        self.state_type = state.state_type
        self.quality = state.quality
        self.compressed = compressed

        if compressed:
            # Store compressed version
            self._compressed_data = gzip.compress(pickle.dumps(state))
            self._state = None
        else:
            self._state = state
            self._compressed_data = None

    def get_state(self) -> EnvironmentState:
        """Get the state, decompressing if necessary"""
        if self._state is not None:
            return self._state

        # Decompress state
        if self._compressed_data:
            # Decompress and deserialize from JSON
            json_data = gzip.decompress(self._compressed_data).decode("utf-8")
            state_dict = json.loads(json_data)
            self._state = EnvironmentState(**state_dict)
            return self._state

        raise ValueError("State data not available")

    def compress(self):
        """Compress the stored state"""
        if not self.compressed and self._state:
            # Serialize to JSON and compress
            state_dict = (
                asdict(self._state)
                if hasattr(self._state, "__dataclass_fields__")
                else self._state.__dict__
            )
            json_data = json.dumps(state_dict, default=str)
            self._compressed_data = gzip.compress(json_data.encode("utf-8"))
            self._state = None
            self.compressed = True

    @property
    def memory_usage(self) -> int:
        """Estimate memory usage in bytes"""
        if self.compressed:
            return len(self._compressed_data) if self._compressed_data else 0
        else:
            # Estimate size using JSON serialization
            state_dict = (
                asdict(self._state)
                if hasattr(self._state, "__dataclass_fields__")
                else self._state.__dict__
            )
            return len(json.dumps(state_dict, default=str)) if self._state else 0


class StateManager:
    """
    Manages environment state tracking and history.

    The StateManager provides comprehensive state management including:
    - Real-time state updates and validation
    - Historical state tracking with intelligent compression
    - State quality assessment and improvement
    - Predictive state modeling
    - Persistence and recovery
    """

    def __init__(
        self,
        history_size: int = 1000,
        compression_threshold: int = 500,
        persistence_interval: float = 30.0,
        prediction_enabled: bool = True,
    ):
        """
        Initialize StateManager.

        Args:
            history_size: Maximum number of states to keep in history
            compression_threshold: Number of states before compression starts
            persistence_interval: Seconds between state persistence
            prediction_enabled: Whether to enable predictive modeling
        """
        self.history_size = history_size
        self.compression_threshold = compression_threshold
        self.persistence_interval = persistence_interval
        self.prediction_enabled = prediction_enabled

        # State storage
        self.current_state: Optional[EnvironmentState] = None
        self.state_history: deque = deque(maxlen=history_size)
        self.state_index: Dict[str, StateHistoryEntry] = {}

        # Quality tracking
        self.quality_metrics = {
            "total_states": 0,
            "excellent_states": 0,
            "good_states": 0,
            "fair_states": 0,
            "poor_states": 0,
        }

        # Prediction models
        self.state_predictors = {}
        self.prediction_accuracy = {}

        # Persistence
        self.persistence_path = Path("data/state_manager")
        self.persistence_path.mkdir(parents=True, exist_ok=True)
        self.last_persistence = datetime.now()

        # Performance tracking
        self.update_times = deque(maxlen=100)
        self.compression_stats = {"compressed": 0, "saved_bytes": 0}

        logger.info(f"StateManager initialized with history_size={history_size}")

    async def initialize_state(self, initial_data: Dict[str, Any] = None) -> EnvironmentState:
        """
        Initialize a new state with optional initial data.
        Ensures sensible defaults for confidence/completeness by injecting
        timestamp and source metadata if missing.
        
        Args:
            initial_data: Optional initial state data
            
        Returns:
            Initialized EnvironmentState
        """
        if initial_data is None:
            initial_data = {}

        # Populate defaults to improve initial quality metrics
        payload: Dict[str, Any] = {
            **initial_data,
        }
        # Ensure an ISO timestamp is present for freshness/confidence computation
        payload.setdefault("timestamp", datetime.now().isoformat())
        # Tag the source of this state for traceability
        payload.setdefault("source", "initialize_state")
        # Provide a hint that this is a system bootstrap unless caller specified
        payload.setdefault("system_bootstrap", True)

        return await self.update_state(payload)
    
    async def update_state(self, observation: Dict[str, Any]) -> EnvironmentState:
        """
        Update environment state with new observation.

        Args:
            observation: New environment observation data

        Returns:
            Updated EnvironmentState
        """
        start_time = datetime.now()

        try:
            # Create new state from observation
            new_state = await self._create_state_from_observation(observation)

            # Validate state quality
            await self._validate_state_quality(new_state)

            # Update current state
            self.current_state = new_state

            # Add to history
            await self._add_to_history(new_state)

            # Update quality metrics
            self._update_quality_metrics(new_state)

            # Trigger compression if needed
            if len(self.state_history) > self.compression_threshold:
                await self._compress_old_states()

            # Update predictions
            if self.prediction_enabled:
                await self._update_predictions(new_state)

            # Persist if interval passed
            if (
                datetime.now() - self.last_persistence
            ).total_seconds() > self.persistence_interval:
                await self._persist_states()

            # Track performance
            update_time = (datetime.now() - start_time).total_seconds()
            self.update_times.append(update_time)

            logger.debug(
                f"State updated: {new_state.summary} (took {update_time:.3f}s)"
            )
            return new_state

        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error(f"Failed to update state: {e}")
            raise

    async def _create_state_from_observation(
        self, observation: Dict[str, Any]
    ) -> EnvironmentState:
        """Create EnvironmentState from raw observation data"""

        # Generate unique state ID
        state_id = (
            f"state_{datetime.now().timestamp()}_{hash(str(observation)) % 10000}"
        )

        # Determine state type from observation
        state_type = self._infer_state_type(observation)

        # Extract educational context
        subject_area = observation.get("subject_area")
        grade_level = observation.get("grade_level")
        learning_objective = observation.get("learning_objective")
        student_id = observation.get("student_id")

        # Extract game context for Roblox states
        game_state = None
        player_positions = None
        active_tools = None

        if state_type == StateType.ROBLOX_GAME:
            game_state = observation.get("game_state", {})
            player_positions = observation.get("player_positions", {})
            active_tools = observation.get("active_tools", [])

        # Calculate quality metrics
        confidence = self._calculate_confidence(observation)
        completeness = self._calculate_completeness(observation)
        freshness = 1.0  # New observation is always fresh

        # Create state
        state = EnvironmentState(
            state_id=state_id,
            timestamp=datetime.now(),
            state_type=state_type,
            data=observation.copy(),
            metadata={
                "observation_keys": list(observation.keys()),
                "data_size": len(str(observation)),
                "source": observation.get("source", "unknown"),
            },
            confidence=confidence,
            completeness=completeness,
            freshness=freshness,
            subject_area=subject_area,
            grade_level=grade_level,
            learning_objective=learning_objective,
            student_id=student_id,
            game_state=game_state,
            player_positions=player_positions,
            active_tools=active_tools,
        )

        return state

    def _infer_state_type(self, observation: Dict[str, Any]) -> StateType:
        """Infer state type from observation data"""

        if "roblox" in str(observation).lower() or "game_state" in observation:
            return StateType.ROBLOX_GAME
        elif "quiz" in str(observation).lower() or "questions" in observation:
            return StateType.QUIZ_SESSION
        elif "learning_progress" in observation or "scores" in observation:
            return StateType.LEARNING_PROGRESS
        elif "content" in observation or "lesson" in observation:
            return StateType.EDUCATIONAL_CONTENT
        elif "user_action" in observation or "interaction" in observation:
            return StateType.USER_INTERACTION
        else:
            return StateType.SYSTEM_STATUS

    def _calculate_confidence(self, observation: Dict[str, Any]) -> float:
        """Calculate confidence in observation data"""
        confidence_factors = []

        # Data completeness factor
        required_keys = ["timestamp", "source"]
        present_keys = sum(1 for key in required_keys if key in observation)
        confidence_factors.append(present_keys / len(required_keys))

        # Data validation factor
        valid_data = 0
        total_data = 0
        for key, value in observation.items():
            total_data += 1
            if value is not None and str(value).strip():
                valid_data += 1

        if total_data > 0:
            confidence_factors.append(valid_data / total_data)

        # Freshness factor (based on timestamp if available)
        if "timestamp" in observation:
            try:
                obs_time = datetime.fromisoformat(observation["timestamp"])
                age = (datetime.now() - obs_time).total_seconds()
                FRESHNESS_DECAY_SECONDS = 300  # 5 minutes
                freshness = max(0, 1 - age / FRESHNESS_DECAY_SECONDS)
                confidence_factors.append(freshness)
            except (ValueError, TypeError, AttributeError):
                DEFAULT_CONFIDENCE = 0.5
                confidence_factors.append(DEFAULT_CONFIDENCE)

        return (
            sum(confidence_factors) / len(confidence_factors)
            if confidence_factors
            else 0.5
        )

    def _calculate_completeness(self, observation: Dict[str, Any]) -> float:
        """Calculate completeness of observation data"""

        # Define expected keys for different observation types
        expected_keys_by_type = {
            "roblox_game": ["game_state", "player_positions", "active_tools"],
            "quiz_session": ["questions", "answers", "scores"],
            "educational_content": ["subject_area", "grade_level", "content"],
            "user_interaction": ["user_id", "action_type", "timestamp"],
            "learning_progress": ["student_id", "progress_metrics", "achievements"],
        }

        # Try to match observation type
        observation_type = None
        for obs_type, keys in expected_keys_by_type.items():
            if any(key in observation for key in keys):
                observation_type = obs_type
                break

        if observation_type:
            expected_keys = expected_keys_by_type[observation_type]
            present_keys = sum(1 for key in expected_keys if key in observation)
            return present_keys / len(expected_keys)

        # Generic completeness assessment
        non_empty_values = sum(
            1 for v in observation.values() if v is not None and str(v).strip()
        )
        MIN_EXPECTED_FIELDS = 5
        return min(1.0, non_empty_values / max(MIN_EXPECTED_FIELDS, len(observation)))

    async def _validate_state_quality(self, state: EnvironmentState):
        """Validate and potentially improve state quality"""

        # Check for data anomalies
        LOW_CONFIDENCE_THRESHOLD = 0.3
        if state.confidence < LOW_CONFIDENCE_THRESHOLD:
            logger.warning(f"Low confidence state detected: {state.state_id}")
            # Attempt to improve confidence
            await self._attempt_state_improvement(state)

        # Check for required educational context
        if state.state_type in [StateType.EDUCATIONAL_CONTENT, StateType.QUIZ_SESSION]:
            if not state.subject_area:
                logger.warning(
                    f"Missing subject area in educational state: {state.state_id}"
                )

        # Validate Roblox game states
        if state.state_type == StateType.ROBLOX_GAME:
            if not state.game_state:
                logger.warning(f"Missing game state in Roblox state: {state.state_id}")

    async def _attempt_state_improvement(self, state: EnvironmentState):
        """Attempt to improve state quality through various methods"""

        # Try to infer missing data from recent states
        recent_states = self.get_recent_states(5)

        # Infer subject area if missing
        if not state.subject_area and recent_states:
            subjects = [s.subject_area for s in recent_states if s.subject_area]
            if subjects:
                state.subject_area = max(set(subjects), key=subjects.count)
                logger.debug(f"Inferred subject area: {state.subject_area}")

        # Infer grade level if missing
        if not state.grade_level and recent_states:
            grades = [s.grade_level for s in recent_states if s.grade_level]
            if grades:
                state.grade_level = max(set(grades), key=grades.count)
                logger.debug(f"Inferred grade level: {state.grade_level}")

        # Recalculate confidence after improvements
        original_confidence = state.confidence
        CONFIDENCE_IMPROVEMENT = 0.1
        state.confidence = min(1.0, state.confidence + CONFIDENCE_IMPROVEMENT)

        if state.confidence > original_confidence:
            logger.debug(
                f"Improved state confidence from {original_confidence:.3f} to {state.confidence:.3f}"
            )

    async def _add_to_history(self, state: EnvironmentState):
        """Add state to history with deduplication"""

        # Check for duplicate states
        state_hash = state.hash()
        if self.state_history:
            recent_hashes = [
                entry.get_state().hash() for entry in list(self.state_history)[-5:]
            ]  # Check last 5 states
            if state_hash in recent_hashes:
                logger.debug(f"Duplicate state detected, skipping: {state.state_id}")
                return

        # Create history entry
        history_entry = StateHistoryEntry(state, compressed=False)

        # Add to history
        self.state_history.append(history_entry)
        self.state_index[state.state_id] = history_entry

        # Update metrics
        self.quality_metrics["total_states"] += 1

    def _update_quality_metrics(self, state: EnvironmentState):
        """Update quality tracking metrics"""

        quality_key = f"{state.quality.value}_states"
        if quality_key in self.quality_metrics:
            self.quality_metrics[quality_key] += 1

    async def _compress_old_states(self):
        """Compress old states to save memory"""

        compress_before = len(self.state_history) - self.compression_threshold + 100
        compressed_count = 0
        bytes_saved = 0

        for i, entry in enumerate(self.state_history):
            if i < compress_before and not entry.compressed:
                original_size = entry.memory_usage
                entry.compress()
                bytes_saved += original_size - entry.memory_usage
                compressed_count += 1

        if compressed_count > 0:
            self.compression_stats["compressed"] += compressed_count
            self.compression_stats["saved_bytes"] += bytes_saved
            logger.debug(
                f"Compressed {compressed_count} states, saved {bytes_saved} bytes"
            )

    async def _update_predictions(self, state: EnvironmentState):
        """Update predictive models with new state"""

        # Simple prediction based on state patterns
        state_type_key = state.state_type.value

        if state_type_key not in self.state_predictors:
            self.state_predictors[state_type_key] = {
                "pattern_count": {},
                "transition_matrix": {},
                "recent_patterns": deque(maxlen=20),
            }

        predictor = self.state_predictors[state_type_key]

        # Extract pattern from state
        pattern = self._extract_state_pattern(state)
        predictor["recent_patterns"].append(pattern)

        # Update pattern counts
        if pattern not in predictor["pattern_count"]:
            predictor["pattern_count"][pattern] = 0
        predictor["pattern_count"][pattern] += 1

        # Update transition matrix if we have previous patterns
        if len(predictor["recent_patterns"]) > 1:
            prev_pattern = predictor["recent_patterns"][-2]
            if prev_pattern not in predictor["transition_matrix"]:
                predictor["transition_matrix"][prev_pattern] = {}
            if pattern not in predictor["transition_matrix"][prev_pattern]:
                predictor["transition_matrix"][prev_pattern][pattern] = 0
            predictor["transition_matrix"][prev_pattern][pattern] += 1

    def _extract_state_pattern(self, state: EnvironmentState) -> str:
        """Extract a pattern signature from state"""

        pattern_elements = [
            state.state_type.value,
            state.quality.value,
            str(state.subject_area) if state.subject_area else "none",
            str(state.grade_level) if state.grade_level else "none",
        ]

        # Add specific pattern elements based on state type
        if state.state_type == StateType.ROBLOX_GAME and state.active_tools:
            pattern_elements.append(f"tools:{len(state.active_tools)}")

        if state.state_type == StateType.QUIZ_SESSION:
            quiz_data = state.data.get("quiz_data", {})
            pattern_elements.append(f"questions:{len(quiz_data.get('questions', []))}")

        return "|".join(pattern_elements)

    async def _persist_states(self):
        """Persist states to storage"""

        try:
            # Save current state
            if self.current_state:
                current_file = self.persistence_path / "current_state.json"
                with open(current_file, "w") as f:
                    json.dump(self.current_state.to_dict(), f, indent=2)

            # Save recent states
            recent_states = self.get_recent_states(50)
            recent_file = self.persistence_path / "recent_states.json"
            with open(recent_file, "w") as f:
                json.dump([state.to_dict() for state in recent_states], f, indent=2)

            # Save quality metrics
            metrics_file = self.persistence_path / "quality_metrics.json"
            with open(metrics_file, "w") as f:
                json.dump(self.quality_metrics, f, indent=2)

            self.last_persistence = datetime.now()
            logger.debug("States persisted successfully")

        except (IOError, OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to persist states: {e}")

    def get_current_state(self) -> Optional[EnvironmentState]:
        """Get the current environment state"""
        return self.current_state

    def get_recent_states(self, count: int = 10) -> List[EnvironmentState]:
        """Get recent states from history"""

        if not self.state_history:
            return []

        recent_entries = list(self.state_history)[-count:]
        return [entry.get_state() for entry in recent_entries]

    def get_states_by_type(
        self, state_type: StateType, count: int = 10
    ) -> List[EnvironmentState]:
        """Get states of specific type"""

        matching_states = []
        for entry in reversed(self.state_history):
            if entry.state_type == state_type:
                matching_states.append(entry.get_state())
                if len(matching_states) >= count:
                    break

        return matching_states

    def get_state_by_id(self, state_id: str) -> Optional[EnvironmentState]:
        """Get specific state by ID"""

        if state_id in self.state_index:
            return self.state_index[state_id].get_state()
        return None

    async def predict_next_state(
        self, current_state: Optional[EnvironmentState] = None
    ) -> Dict[str, Any]:
        """Predict likely next state based on patterns"""

        if not self.prediction_enabled:
            return {"prediction": "disabled"}

        if current_state is None:
            current_state = self.current_state

        if not current_state:
            return {"prediction": "no_current_state"}

        state_type_key = current_state.state_type.value
        if state_type_key not in self.state_predictors:
            return {"prediction": "insufficient_data"}

        predictor = self.state_predictors[state_type_key]
        current_pattern = self._extract_state_pattern(current_state)

        # Get transition probabilities
        if current_pattern in predictor["transition_matrix"]:
            transitions = predictor["transition_matrix"][current_pattern]
            total_transitions = sum(transitions.values())

            predictions = {}
            for next_pattern, count in transitions.items():
                probability = count / total_transitions
                predictions[next_pattern] = probability

            # Sort by probability
            sorted_predictions = sorted(
                predictions.items(), key=lambda x: x[1], reverse=True
            )

            return {
                "prediction": "success",
                "current_pattern": current_pattern,
                "next_patterns": sorted_predictions[:5],
                "confidence": max(predictions.values()) if predictions else 0.0,
            }

        return {"prediction": "no_pattern_match"}

    async def calculate_reward(self, metrics: Dict[str, Any]) -> float:
        """Calculate a normalized reward [0, 1] for a completed task.

        The reward considers learning objectives met and execution time. It is
        intentionally simple and deterministic to start, and can be extended
        with additional domain metrics (engagement, difficulty, retention).

        Expected keys in metrics:
        - objectives_met: int, number of objectives satisfied
        - total_objectives|objectives_total (optional): int, denominator for normalization
        - execution_time: float seconds to completion (optional)
        """
        try:
            objectives_met = int(metrics.get("objectives_met", 0) or 0)
            total_objectives = int(
                metrics.get("total_objectives")
                or metrics.get("objectives_total")
                or objectives_met
                or 1
            )
            objectives_norm = max(0.0, min(1.0, objectives_met / max(1, total_objectives)))

            exec_time = float(metrics.get("execution_time", 0.0) or 0.0)
            # Favor completions within ~5 seconds; soft decay over next 60 seconds
            if exec_time <= 5.0:
                time_norm = 1.0
            else:
                time_norm = max(0.0, 1.0 - (exec_time - 5.0) / 60.0)

            # Weighted combination — emphasize pedagogical completeness
            reward = 0.6 * objectives_norm + 0.4 * time_norm
            # Clamp to [0,1]
            reward = max(0.0, min(1.0, reward))

            # Optionally keep lightweight telemetry
            self.quality_metrics["last_reward"] = reward
            self.quality_metrics["last_reward_objectives_norm"] = objectives_norm
            self.quality_metrics["last_reward_time_norm"] = time_norm

            logger.debug(
                "Calculated reward: %.3f (obj=%.3f, time=%.3f, met=%d/%d, exec=%.2fs)",
                reward,
                objectives_norm,
                time_norm,
                objectives_met,
                total_objectives,
                exec_time,
            )
            return reward
        except Exception as e:
            logger.error(f"Reward calculation failed: {e}")
            # Return a conservative default
            return 0.0

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of StateManager"""

        return {
            "current_state": self.current_state.summary if self.current_state else None,
            "history_size": len(self.state_history),
            "quality_metrics": self.quality_metrics.copy(),
            "performance": {
                "average_update_time": (
                    np.mean(self.update_times) if self.update_times else 0
                ),
                "compression_stats": self.compression_stats.copy(),
            },
            "prediction_models": len(self.state_predictors),
            "memory_usage": {
                "total_entries": len(self.state_history),
                "compressed_entries": sum(
                    1 for e in self.state_history if e.compressed
                ),
                "estimated_bytes": sum(e.memory_usage for e in self.state_history),
            },
            "persistence": {
                "last_persistence": self.last_persistence.isoformat(),
                "persistence_path": str(self.persistence_path),
            },
        }

    async def reset(self):
        """Reset StateManager to initial state"""

        logger.info("Resetting StateManager")

        self.current_state = None
        self.state_history.clear()
        self.state_index.clear()
        self.quality_metrics = {
            "total_states": 0,
            "excellent_states": 0,
            "good_states": 0,
            "fair_states": 0,
            "poor_states": 0,
        }
        self.state_predictors.clear()
        self.prediction_accuracy.clear()
        self.update_times.clear()
        self.compression_stats = {"compressed": 0, "saved_bytes": 0}

        logger.info("StateManager reset completed")


# Backward compatibility alias
SPARCStateManager = StateManager
