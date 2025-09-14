"""
Reward Calculator - Learning Outcome Rewards and Progress Tracking
=================================================================

The RewardCalculator evaluates educational actions and student progress to generate
meaningful reward signals for the SPARC framework:
- Multi-dimensional reward assessment across learning domains
- Real-time progress tracking and achievement recognition
- Adaptive reward shaping based on individual learning curves
- Integration with educational standards and learning objectives
- Comprehensive analytics for learning outcome optimization

This component provides the feedback mechanism that drives the learning
optimization loop in the SPARC framework.
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import statistics
from pathlib import Path
import math

from .state_manager import EnvironmentState, StateType
from .action_executor import ActionResult

logger = logging.getLogger(__name__)

# Constants for reward calculation
DEFAULT_TIME_WINDOW_SECONDS = 300  # 5 minutes
DEFAULT_HISTORY_SIZE = 100  # Number of historical records to keep
CONTENT_DETAIL_DIVISOR = 1000  # For rough measure of elaboration
SECONDS_PER_MINUTE = 60
SUSTAINED_ENGAGEMENT_THRESHOLD = 300  # 5 minutes
DIFFICULT_TASK_THRESHOLD = 300  # 5 minutes on difficult tasks
MAX_SESSION_DURATION = 1800  # 30 minutes


class RewardDimension(Enum):
    """Dimensions of educational reward assessment"""

    LEARNING_PROGRESS = "learning_progress"
    ENGAGEMENT = "engagement"
    ACCURACY = "accuracy"
    CREATIVITY = "creativity"
    COLLABORATION = "collaboration"
    PERSISTENCE = "persistence"
    CRITICAL_THINKING = "critical_thinking"
    PROBLEM_SOLVING = "problem_solving"
    COMMUNICATION = "communication"
    METACOGNITION = "metacognition"


class RewardType(Enum):
    """Types of rewards in the educational context"""

    IMMEDIATE = "immediate"  # Instant feedback on actions
    PROGRESS = "progress"  # Recognition of learning advancement
    ACHIEVEMENT = "achievement"  # Milestone and goal completion
    BEHAVIORAL = "behavioral"  # Process and effort recognition
    SOCIAL = "social"  # Collaboration and peer interaction
    ADAPTIVE = "adaptive"  # Personalized challenge adjustment


@dataclass
class RewardComponent:
    """Individual component of a reward calculation"""

    dimension: RewardDimension
    raw_value: float  # 0-1 raw assessment value
    weight: float = 1.0  # Importance weight
    confidence: float = 1.0  # Confidence in assessment

    # Context information
    evidence: List[str] = field(default_factory=list)
    contributing_factors: Dict[str, float] = field(default_factory=dict)

    # Educational metadata
    learning_objective: Optional[str] = None
    skill_area: Optional[str] = None
    difficulty_level: Optional[float] = None

    @property
    def weighted_value(self) -> float:
        """Calculate weighted and confidence-adjusted value"""
        return self.raw_value * self.weight * self.confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result["dimension"] = self.dimension.value
        result["weighted_value"] = self.weighted_value
        return result


@dataclass
class RewardSignal:
    """Complete reward signal for an educational interaction"""

    # Core reward data
    total_reward: float
    components: List[RewardComponent] = field(default_factory=list)
    reward_type: RewardType = RewardType.IMMEDIATE

    # Contextual information
    student_id: Optional[str] = None
    subject_area: Optional[str] = None
    learning_session_id: Optional[str] = None

    # Temporal data
    timestamp: datetime = field(default_factory=datetime.now)
    time_window: Optional[Tuple[datetime, datetime]] = None

    # Quality metrics
    confidence: float = 1.0
    reliability: float = 1.0  # How reliable is this reward signal

    # Educational outcomes
    learning_gains: Dict[str, float] = field(default_factory=dict)
    skill_improvements: Dict[str, float] = field(default_factory=dict)
    behavioral_indicators: Dict[str, Any] = field(default_factory=dict)

    # Feedback and recommendations
    feedback_message: Optional[str] = None
    recommended_actions: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)

    # Metadata
    calculation_method: str = "standard"
    normalization_applied: bool = False

    @property
    def dimension_breakdown(self) -> Dict[str, float]:
        """Get reward breakdown by dimension"""
        breakdown = {}
        for component in self.components:
            dimension = component.dimension.value
            if dimension in breakdown:
                breakdown[dimension] += component.weighted_value
            else:
                breakdown[dimension] = component.weighted_value
        return breakdown

    @property
    def quality_score(self) -> float:
        """Overall quality of the reward signal"""
        return (self.confidence + self.reliability) / 2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result["reward_type"] = self.reward_type.value
        result["timestamp"] = self.timestamp.isoformat()
        result["components"] = [comp.to_dict() for comp in self.components]
        result["dimension_breakdown"] = self.dimension_breakdown
        result["quality_score"] = self.quality_score

        if self.time_window:
            result["time_window"] = [
                self.time_window[0].isoformat(),
                self.time_window[1].isoformat(),
            ]

        return result


class LearningCurveAnalyzer:
    """Analyzes learning curves and progress patterns"""

    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.learning_curves: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=window_size)
        )
        self.performance_baselines: Dict[str, float] = {}

    def add_performance_point(
        self, student_id: str, performance: float, timestamp: datetime
    ):
        """Add a performance data point"""
        self.learning_curves[student_id].append(
            {"performance": performance, "timestamp": timestamp}
        )

        # Update baseline if we have enough data
        if len(self.learning_curves[student_id]) >= 5:
            recent_performances = [
                p["performance"] for p in list(self.learning_curves[student_id])[-5:]
            ]
            self.performance_baselines[student_id] = statistics.mean(
                recent_performances
            )

    def calculate_learning_velocity(self, student_id: str) -> float:
        """Calculate the rate of learning (improvement over time)"""
        if (
            student_id not in self.learning_curves
            or len(self.learning_curves[student_id]) < 3
        ):
            return 0.0

        curve = list(self.learning_curves[student_id])

        # Use linear regression to find trend
        n = len(curve)
        sum_x = sum(range(n))
        sum_y = sum(point["performance"] for point in curve)
        sum_xy = sum(i * point["performance"] for i, point in enumerate(curve))
        sum_x2 = sum(i * i for i in range(n))

        # Calculate slope (learning velocity)
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def detect_learning_plateau(self, student_id: str, threshold: float = 0.01) -> bool:
        """Detect if student has hit a learning plateau"""
        velocity = self.calculate_learning_velocity(student_id)
        return abs(velocity) < threshold and len(self.learning_curves[student_id]) >= 10

    def calculate_consistency(self, student_id: str) -> float:
        """Calculate consistency of performance (lower variance = higher consistency)"""
        if (
            student_id not in self.learning_curves
            or len(self.learning_curves[student_id]) < 3
        ):
            return 0.5

        performances = [p["performance"] for p in self.learning_curves[student_id]]
        variance = statistics.variance(performances)

        # Convert variance to consistency score (0-1, higher is more consistent)
        # Use negative exponential to map variance to consistency
        consistency = math.exp(-variance * 5)  # Adjust multiplier as needed
        return min(1.0, max(0.0, consistency))


class EngagementAnalyzer:
    """Analyzes student engagement patterns"""

    def __init__(self):
        self.engagement_indicators = {
            "time_on_task": 0.3,
            "interaction_frequency": 0.2,
            "exploration_behavior": 0.2,
            "help_seeking": 0.1,
            "persistence": 0.2,
        }

    def calculate_engagement_score(
        self,
        state: EnvironmentState,
        action_result: ActionResult,
        time_window: int = DEFAULT_TIME_WINDOW_SECONDS,
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate engagement score based on various indicators"""

        indicators = {}

        # Time on task (from game state if available)
        if state.state_type == StateType.ROBLOX_GAME and state.game_state:
            active_time = state.game_state.get("active_time", 0)
            # Normalize to 0-1 scale (optimal engagement around 10-20 minutes)
            optimal_time = 900  # 15 minutes
            if active_time <= optimal_time:
                indicators["time_on_task"] = active_time / optimal_time
            else:
                # Diminishing returns after optimal time
                indicators["time_on_task"] = optimal_time / active_time
        else:
            indicators["time_on_task"] = 0.5  # Default moderate engagement

        # Interaction frequency
        if state.game_state:
            interactions = state.game_state.get("interaction_count", 0)
            time_minutes = (
                state.game_state.get("active_time", SECONDS_PER_MINUTE)
                / SECONDS_PER_MINUTE
            )
            interaction_rate = interactions / max(time_minutes, 1)
            # Optimal interaction rate is around 5-10 per minute
            optimal_rate = 7.5
            if interaction_rate <= optimal_rate:
                indicators["interaction_frequency"] = interaction_rate / optimal_rate
            else:
                indicators["interaction_frequency"] = optimal_rate / interaction_rate
        else:
            indicators["interaction_frequency"] = 0.5

        # Exploration behavior (variety of actions/areas)
        if state.active_tools:
            tool_variety = len(set(state.active_tools)) / max(
                len(state.active_tools), 1
            )
            indicators["exploration_behavior"] = tool_variety
        else:
            indicators["exploration_behavior"] = 0.4

        # Help seeking behavior (moderate help seeking is positive)
        help_requests = state.data.get("help_requests", 0)
        if help_requests == 0:
            indicators["help_seeking"] = (
                0.3  # No help seeking might indicate disengagement
            )
        elif help_requests <= 3:
            indicators["help_seeking"] = 0.5 + (
                help_requests * 0.15
            )  # Moderate help seeking
        else:
            indicators["help_seeking"] = 0.8 - (
                (help_requests - 3) * 0.1
            )  # Too much help seeking

        # Persistence (continuing after failures)
        failures = state.data.get("failed_attempts", 0)
        continued_attempts = state.data.get("continued_attempts", 0)
        if failures > 0:
            persistence_ratio = continued_attempts / failures
            indicators["persistence"] = min(1.0, persistence_ratio)
        else:
            indicators["persistence"] = 0.7  # No failures, moderate persistence score

        # Calculate weighted engagement score
        total_score = 0
        total_weight = 0

        for indicator, value in indicators.items():
            if indicator in self.engagement_indicators:
                weight = self.engagement_indicators[indicator]
                total_score += value * weight
                total_weight += weight

        engagement_score = total_score / total_weight if total_weight > 0 else 0.5

        return engagement_score, indicators


class CreativityAssessment:
    """Assesses creativity and innovation in student work"""

    def __init__(self):
        self.creativity_dimensions = {
            "originality": 0.4,  # Uniqueness of solution/creation
            "fluency": 0.2,  # Number of ideas generated
            "flexibility": 0.2,  # Variety of approaches used
            "elaboration": 0.2,  # Detail and development of ideas
        }

    def assess_creativity(
        self, state: EnvironmentState, action_result: ActionResult
    ) -> Tuple[float, Dict[str, float]]:
        """Assess creativity based on student actions and outputs"""

        creativity_scores = {}

        # Originality assessment
        if state.state_type == StateType.ROBLOX_GAME:
            # Look for unique building patterns, novel tool usage
            unique_combinations = state.data.get("unique_combinations", 0)
            standard_patterns = state.data.get("standard_patterns", 1)
            originality = unique_combinations / max(
                unique_combinations + standard_patterns, 1
            )
            creativity_scores["originality"] = originality
        else:
            creativity_scores["originality"] = 0.5

        # Fluency - number of different approaches/ideas
        different_approaches = len(state.data.get("approaches_used", ["default"]))
        max_expected_approaches = 5
        fluency = min(1.0, different_approaches / max_expected_approaches)
        creativity_scores["fluency"] = fluency

        # Flexibility - variety in problem-solving strategies
        strategy_types = set(state.data.get("strategy_types", ["basic"]))
        flexibility = min(
            1.0, len(strategy_types) / 4
        )  # Up to 4 different strategy types
        creativity_scores["flexibility"] = flexibility

        # Elaboration - detail and refinement
        if state.state_type == StateType.ROBLOX_GAME:
            detail_level = (
                state.game_state.get("detail_score", 0.5) if state.game_state else 0.5
            )
            creativity_scores["elaboration"] = detail_level
        else:
            content_detail = (
                len(str(state.data)) / CONTENT_DETAIL_DIVISOR
            )  # Rough measure of elaboration
            creativity_scores["elaboration"] = min(1.0, content_detail)

        # Calculate weighted creativity score
        total_score = 0
        for dimension, score in creativity_scores.items():
            weight = self.creativity_dimensions.get(dimension, 0.25)
            total_score += score * weight

        return total_score, creativity_scores


class CollaborationAssessment:
    """Assesses collaborative learning behaviors"""

    def __init__(self):
        self.collaboration_factors = {
            "participation": 0.3,  # Active participation in group activities
            "communication": 0.3,  # Quality of communication with peers
            "cooperation": 0.2,  # Working together effectively
            "support": 0.2,  # Helping and supporting others
        }

    def assess_collaboration(
        self, state: EnvironmentState, action_result: ActionResult
    ) -> Tuple[float, Dict[str, float]]:
        """Assess collaborative learning behaviors"""

        collab_scores = {}

        # Check if this is a multi-player scenario
        is_collaborative = (
            state.player_positions and len(state.player_positions) > 1
        ) or state.data.get("group_activity", False)

        if not is_collaborative:
            # No collaboration opportunity
            return 0.0, {factor: 0.0 for factor in self.collaboration_factors}

        # Participation - active involvement in group activities
        player_actions = state.data.get("player_actions", {})
        if state.student_id and state.student_id in player_actions:
            student_actions = player_actions[state.student_id]
            total_actions = sum(player_actions.values())
            participation = student_actions / max(total_actions, 1)
            # Normalize around fair participation (1/n where n is number of players)
            expected_participation = 1 / max(len(player_actions), 1)
            collab_scores["participation"] = min(
                1.0, participation / expected_participation
            )
        else:
            collab_scores["participation"] = 0.5

        # Communication - messages sent, quality of interaction
        messages_sent = state.data.get("messages_sent", 0)
        messages_received = state.data.get("messages_received", 0)
        total_messages = messages_sent + messages_received

        if total_messages > 0:
            # Good communication involves both sending and receiving
            send_ratio = messages_sent / total_messages
            # Optimal ratio is around 0.4-0.6 (balanced communication)
            if 0.4 <= send_ratio <= 0.6:
                communication_score = 1.0
            else:
                communication_score = 1.0 - abs(send_ratio - 0.5) * 2
            collab_scores["communication"] = communication_score
        else:
            collab_scores["communication"] = 0.0

        # Cooperation - working together on shared goals
        shared_goals_achieved = state.data.get("shared_goals_achieved", 0)
        total_shared_goals = state.data.get("total_shared_goals", 1)
        collab_scores["cooperation"] = shared_goals_achieved / total_shared_goals

        # Support - helping other students
        help_provided = state.data.get("help_provided_to_others", 0)
        help_requests_received = state.data.get("help_requests_from_others", 1)
        support_ratio = help_provided / help_requests_received
        collab_scores["support"] = min(1.0, support_ratio)

        # Calculate weighted collaboration score
        total_score = 0
        for factor, score in collab_scores.items():
            weight = self.collaboration_factors.get(factor, 0.25)
            total_score += score * weight

        return total_score, collab_scores


class RewardCalculator:
    """
    Advanced reward calculator for educational interactions.

    The RewardCalculator provides sophisticated reward signal generation
    that considers multiple dimensions of learning, individual progress
    patterns, and educational objectives to drive optimal learning outcomes.
    """

    def __init__(
        self,
        dimensions: Optional[List[str]] = None,
        normalization: bool = True,
        history_size: int = DEFAULT_HISTORY_SIZE,
    ):
        """
        Initialize RewardCalculator.

        Args:
            dimensions: List of reward dimensions to consider
            normalization: Whether to normalize rewards
            history_size: Size of reward history to maintain
        """
        self.dimensions = dimensions or [dim.value for dim in RewardDimension]
        self.normalization_enabled = normalization
        self.history_size = history_size

        # Reward calculation components
        self.learning_curve_analyzer = LearningCurveAnalyzer()
        self.engagement_analyzer = EngagementAnalyzer()
        self.creativity_assessment = CreativityAssessment()
        self.collaboration_assessment = CollaborationAssessment()

        # Reward history and statistics
        self.reward_history: deque = deque(maxlen=history_size)
        self.dimension_statistics: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"mean": 0.0, "std": 0.1, "min": 0.0, "max": 1.0}
        )

        # Student-specific reward patterns
        self.student_reward_profiles: Dict[str, Dict[str, Any]] = {}

        # Educational objective weights
        self.objective_weights = {
            "knowledge_acquisition": {
                RewardDimension.ACCURACY: 0.4,
                RewardDimension.LEARNING_PROGRESS: 0.6,
            },
            "skill_development": {
                RewardDimension.LEARNING_PROGRESS: 0.3,
                RewardDimension.PERSISTENCE: 0.3,
                RewardDimension.PROBLEM_SOLVING: 0.4,
            },
            "creative_expression": {
                RewardDimension.CREATIVITY: 0.6,
                RewardDimension.ENGAGEMENT: 0.4,
            },
            "collaboration": {
                RewardDimension.COLLABORATION: 0.7,
                RewardDimension.COMMUNICATION: 0.3,
            },
        }

        # Adaptive weights based on learning stage
        self.stage_weights = {
            "novice": {
                RewardDimension.ENGAGEMENT: 1.2,
                RewardDimension.PERSISTENCE: 1.1,
                RewardDimension.ACCURACY: 0.8,
            },
            "developing": {
                RewardDimension.LEARNING_PROGRESS: 1.2,
                RewardDimension.PROBLEM_SOLVING: 1.1,
                RewardDimension.ACCURACY: 1.0,
            },
            "proficient": {
                RewardDimension.CREATIVITY: 1.2,
                RewardDimension.CRITICAL_THINKING: 1.2,
                RewardDimension.COLLABORATION: 1.1,
            },
        }

        # Performance tracking
        self.calculation_stats = {
            "total_calculations": 0,
            "average_calculation_time": 0.0,
            "reward_distribution": defaultdict(int),
        }

        # Persistence
        self.persistence_path = Path("data/reward_calculator")
        self.persistence_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"RewardCalculator initialized with {len(self.dimensions)} dimensions"
        )

    async def calculate_rewards(self, reward_input: Dict[str, Any]) -> RewardSignal:
        """
        Calculate comprehensive reward signal for an educational interaction.

        Args:
            reward_input: Dictionary containing state, action, result, and context

        Returns:
            RewardSignal with multi-dimensional reward assessment
        """
        start_time = datetime.now()

        try:
            # Extract input components
            state = reward_input.get("state")
            action = reward_input.get("action")
            result = reward_input.get("result")
            context = reward_input.get("context", {})

            if not state:
                raise ValueError("State is required for reward calculation")

            # Initialize reward components
            reward_components = []

            # Calculate rewards for each dimension
            if RewardDimension.LEARNING_PROGRESS.value in self.dimensions:
                progress_component = await self._calculate_learning_progress_reward(
                    state, action, result, context
                )
                reward_components.append(progress_component)

            if RewardDimension.ENGAGEMENT.value in self.dimensions:
                engagement_component = await self._calculate_engagement_reward(
                    state, action, result, context
                )
                reward_components.append(engagement_component)

            if RewardDimension.ACCURACY.value in self.dimensions:
                accuracy_component = await self._calculate_accuracy_reward(
                    state, action, result, context
                )
                reward_components.append(accuracy_component)

            if RewardDimension.CREATIVITY.value in self.dimensions:
                creativity_component = await self._calculate_creativity_reward(
                    state, action, result, context
                )
                reward_components.append(creativity_component)

            if RewardDimension.COLLABORATION.value in self.dimensions:
                collaboration_component = await self._calculate_collaboration_reward(
                    state, action, result, context
                )
                reward_components.append(collaboration_component)

            if RewardDimension.PERSISTENCE.value in self.dimensions:
                persistence_component = await self._calculate_persistence_reward(
                    state, action, result, context
                )
                reward_components.append(persistence_component)

            if RewardDimension.CRITICAL_THINKING.value in self.dimensions:
                thinking_component = await self._calculate_critical_thinking_reward(
                    state, action, result, context
                )
                reward_components.append(thinking_component)

            if RewardDimension.PROBLEM_SOLVING.value in self.dimensions:
                problem_solving_component = (
                    await self._calculate_problem_solving_reward(
                        state, action, result, context
                    )
                )
                reward_components.append(problem_solving_component)

            # Apply adaptive weighting based on learning stage and objectives
            weighted_components = await self._apply_adaptive_weighting(
                reward_components, state, context
            )

            # Calculate total reward
            total_reward = sum(comp.weighted_value for comp in weighted_components)

            # Normalize if enabled
            if self.normalization_enabled:
                total_reward = await self._normalize_reward(
                    total_reward, state.student_id
                )

            # Determine reward type
            reward_type = self._determine_reward_type(action, result, context)

            # Calculate confidence and reliability
            confidence = self._calculate_reward_confidence(weighted_components, state)
            reliability = self._calculate_reward_reliability(
                weighted_components, context
            )

            # Generate educational feedback
            feedback_message, recommendations, improvements = (
                await self._generate_educational_feedback(
                    weighted_components, state, total_reward
                )
            )

            # Calculate learning gains and skill improvements
            learning_gains = await self._calculate_learning_gains(
                weighted_components, state
            )
            skill_improvements = await self._calculate_skill_improvements(
                weighted_components, state
            )

            # Create reward signal
            reward_signal = RewardSignal(
                total_reward=total_reward,
                components=weighted_components,
                reward_type=reward_type,
                student_id=state.student_id,
                subject_area=state.subject_area,
                confidence=confidence,
                reliability=reliability,
                learning_gains=learning_gains,
                skill_improvements=skill_improvements,
                feedback_message=feedback_message,
                recommended_actions=recommendations,
                areas_for_improvement=improvements,
                calculation_method="multi_dimensional_adaptive",
            )

            # Update reward history and statistics
            await self._update_reward_statistics(reward_signal)

            # Update student reward profile
            if state.student_id:
                await self._update_student_reward_profile(
                    state.student_id, reward_signal
                )

            # Track performance
            calculation_time = (datetime.now() - start_time).total_seconds()
            self.calculation_stats["total_calculations"] += 1
            self.calculation_stats["average_calculation_time"] = (
                self.calculation_stats["average_calculation_time"]
                * (self.calculation_stats["total_calculations"] - 1)
                + calculation_time
            ) / self.calculation_stats["total_calculations"]

            logger.debug(
                f"Reward calculated: {total_reward:.3f} (took {calculation_time:.3f}s)"
            )
            return reward_signal

        except Exception as e:
            logger.error(f"Failed to calculate rewards: {e}")
            # Return minimal reward signal
            return RewardSignal(
                total_reward=0.0,
                components=[],
                student_id=state.student_id if state else None,
                confidence=0.0,
                reliability=0.0,
                feedback_message="Reward calculation failed",
                calculation_method="error_fallback",
            )

    async def _calculate_learning_progress_reward(
        self,
        state: EnvironmentState,
        action: Any,
        result: ActionResult,
        context: Dict[str, Any],
    ) -> RewardComponent:
        """Calculate reward based on learning progress"""

        evidence = []
        contributing_factors = {}

        # Base progress assessment
        base_progress = 0.5

        # Quiz performance progress
        if state.state_type == StateType.QUIZ_SESSION:
            quiz_data = state.data.get("quiz_data", {})
            if "scores" in quiz_data and quiz_data["scores"]:
                recent_scores = quiz_data["scores"][-3:]  # Last 3 scores
                if len(recent_scores) > 1:
                    progress_trend = recent_scores[-1] - recent_scores[0]
                    base_progress = 0.5 + (progress_trend * 0.5)  # Scale trend to 0-1
                    evidence.append(f"Quiz score trend: {progress_trend:+.2f}")
                    contributing_factors["quiz_improvement"] = progress_trend

        # Learning velocity from analyzer
        if state.student_id:
            self.learning_curve_analyzer.add_performance_point(
                state.student_id, base_progress, datetime.now()
            )
            velocity = self.learning_curve_analyzer.calculate_learning_velocity(
                state.student_id
            )
            velocity_contribution = min(0.3, max(-0.3, velocity))  # Cap contribution
            base_progress += velocity_contribution
            evidence.append(f"Learning velocity: {velocity:.3f}")
            contributing_factors["learning_velocity"] = velocity

        # Action success contribution
        if result and hasattr(result, "success"):
            if result.success:
                base_progress += 0.1
                evidence.append("Action completed successfully")
                contributing_factors["action_success"] = 0.1
            else:
                base_progress -= 0.05
                evidence.append("Action failed")
                contributing_factors["action_failure"] = -0.05

        # Time-based progress (consistent engagement over time)
        session_duration = context.get("session_duration", 0)
        if session_duration > SUSTAINED_ENGAGEMENT_THRESHOLD:
            duration_bonus = min(0.2, session_duration / MAX_SESSION_DURATION)
            base_progress += duration_bonus
            evidence.append(
                f"Sustained engagement: {session_duration/SECONDS_PER_MINUTE:.1f} minutes"
            )
            contributing_factors["sustained_engagement"] = duration_bonus

        # Clamp to valid range
        base_progress = max(0.0, min(1.0, base_progress))

        # Confidence based on evidence quality
        confidence = min(1.0, len(evidence) / 3.0)  # More evidence = higher confidence

        return RewardComponent(
            dimension=RewardDimension.LEARNING_PROGRESS,
            raw_value=base_progress,
            weight=1.0,
            confidence=confidence,
            evidence=evidence,
            contributing_factors=contributing_factors,
            learning_objective=context.get("learning_objective"),
            skill_area=state.subject_area,
        )

    async def _calculate_engagement_reward(
        self,
        state: EnvironmentState,
        action: Any,
        result: ActionResult,
        context: Dict[str, Any],
    ) -> RewardComponent:
        """Calculate reward based on student engagement"""

        engagement_score, indicators = (
            self.engagement_analyzer.calculate_engagement_score(state, result)
        )

        evidence = []
        for indicator, value in indicators.items():
            evidence.append(f"{indicator}: {value:.2f}")

        # Engagement confidence based on data availability
        data_quality_indicators = [
            "active_time" in (state.game_state or {}),
            "interaction_count" in (state.game_state or {}),
            bool(state.active_tools),
            "help_requests" in state.data,
            "failed_attempts" in state.data,
        ]
        confidence = sum(data_quality_indicators) / len(data_quality_indicators)

        return RewardComponent(
            dimension=RewardDimension.ENGAGEMENT,
            raw_value=engagement_score,
            weight=1.0,
            confidence=confidence,
            evidence=evidence,
            contributing_factors=indicators,
            learning_objective=context.get("learning_objective"),
            skill_area=state.subject_area,
        )

    async def _calculate_accuracy_reward(
        self,
        state: EnvironmentState,
        action: Any,
        result: ActionResult,
        context: Dict[str, Any],
    ) -> RewardComponent:
        """Calculate reward based on accuracy of responses/actions"""

        accuracy_score = 0.5  # Default neutral accuracy
        evidence = []
        contributing_factors = {}

        # Quiz accuracy
        if state.state_type == StateType.QUIZ_SESSION:
            quiz_data = state.data.get("quiz_data", {})
            if "current_score" in quiz_data:
                accuracy_score = quiz_data["current_score"]
                evidence.append(f"Quiz accuracy: {accuracy_score:.1%}")
                contributing_factors["quiz_accuracy"] = accuracy_score
            elif "scores" in quiz_data and quiz_data["scores"]:
                recent_score = quiz_data["scores"][-1]
                accuracy_score = recent_score
                evidence.append(f"Recent quiz score: {accuracy_score:.1%}")
                contributing_factors["recent_score"] = recent_score

        # Roblox task accuracy
        elif state.state_type == StateType.ROBLOX_GAME:
            if state.game_state:
                tasks_completed = state.game_state.get("tasks_completed", 0)
                tasks_attempted = state.game_state.get("tasks_attempted", 1)
                task_accuracy = tasks_completed / tasks_attempted
                accuracy_score = task_accuracy
                evidence.append(f"Task completion rate: {task_accuracy:.1%}")
                contributing_factors["task_accuracy"] = task_accuracy

        # Action result accuracy
        if result and hasattr(result, "success") and hasattr(result, "result_data"):
            if result.success:
                action_accuracy = result.result_data.get("accuracy", 0.8)
                accuracy_score = (
                    accuracy_score + action_accuracy
                ) / 2  # Average with existing
                evidence.append(f"Action accuracy: {action_accuracy:.1%}")
                contributing_factors["action_accuracy"] = action_accuracy

        # Penalty for excessive errors
        error_count = state.data.get("error_count", 0)
        if error_count > 0:
            error_penalty = min(0.3, error_count * 0.05)  # Up to 30% penalty
            accuracy_score -= error_penalty
            evidence.append(f"Error penalty: -{error_penalty:.1%}")
            contributing_factors["error_penalty"] = -error_penalty

        # Clamp to valid range
        accuracy_score = max(0.0, min(1.0, accuracy_score))

        # Confidence based on data availability
        confidence = 0.8 if evidence else 0.3

        return RewardComponent(
            dimension=RewardDimension.ACCURACY,
            raw_value=accuracy_score,
            weight=1.0,
            confidence=confidence,
            evidence=evidence,
            contributing_factors=contributing_factors,
            learning_objective=context.get("learning_objective"),
            skill_area=state.subject_area,
        )

    async def _calculate_creativity_reward(
        self,
        state: EnvironmentState,
        action: Any,
        result: ActionResult,
        context: Dict[str, Any],
    ) -> RewardComponent:
        """Calculate reward based on creativity and innovation"""

        creativity_score, creativity_breakdown = (
            self.creativity_assessment.assess_creativity(state, result)
        )

        evidence = []
        for dimension, score in creativity_breakdown.items():
            evidence.append(f"{dimension}: {score:.2f}")

        # Higher confidence for creative activities
        is_creative_context = (
            state.state_type == StateType.ROBLOX_GAME
            or "creative" in str(context.get("learning_objective", "")).lower()
            or state.subject_area in ["art", "design", "creative_writing"]
        )
        confidence = 0.8 if is_creative_context else 0.5

        return RewardComponent(
            dimension=RewardDimension.CREATIVITY,
            raw_value=creativity_score,
            weight=1.0,
            confidence=confidence,
            evidence=evidence,
            contributing_factors=creativity_breakdown,
            learning_objective=context.get("learning_objective"),
            skill_area=state.subject_area,
        )

    async def _calculate_collaboration_reward(
        self,
        state: EnvironmentState,
        action: Any,
        result: ActionResult,
        context: Dict[str, Any],
    ) -> RewardComponent:
        """Calculate reward based on collaborative behaviors"""

        collaboration_score, collab_breakdown = (
            self.collaboration_assessment.assess_collaboration(state, result)
        )

        evidence = []
        for factor, score in collab_breakdown.items():
            evidence.append(f"{factor}: {score:.2f}")

        # Confidence based on multi-player context
        is_collaborative = (
            state.player_positions and len(state.player_positions) > 1
        ) or state.data.get("group_activity", False)
        confidence = 0.9 if is_collaborative else 0.1

        return RewardComponent(
            dimension=RewardDimension.COLLABORATION,
            raw_value=collaboration_score,
            weight=1.0,
            confidence=confidence,
            evidence=evidence,
            contributing_factors=collab_breakdown,
            learning_objective=context.get("learning_objective"),
            skill_area=state.subject_area,
        )

    async def _calculate_persistence_reward(
        self,
        state: EnvironmentState,
        action: Any,
        result: ActionResult,
        context: Dict[str, Any],
    ) -> RewardComponent:
        """Calculate reward based on persistence and effort"""

        persistence_score = 0.5  # Default
        evidence = []
        contributing_factors = {}

        # Attempts after failures
        failed_attempts = state.data.get("failed_attempts", 0)
        continued_attempts = state.data.get("continued_attempts", 0)

        if failed_attempts > 0:
            persistence_ratio = continued_attempts / failed_attempts
            persistence_score = min(1.0, persistence_ratio)
            evidence.append(f"Continued after {failed_attempts} failures")
            contributing_factors["failure_recovery"] = persistence_ratio

        # Time spent on challenging tasks
        time_on_difficult_tasks = state.data.get("difficult_task_time", 0)
        if time_on_difficult_tasks > DIFFICULT_TASK_THRESHOLD:
            time_persistence = min(1.0, time_on_difficult_tasks / MAX_SESSION_DURATION)
            persistence_score = (persistence_score + time_persistence) / 2
            evidence.append(
                f"Spent {time_on_difficult_tasks/SECONDS_PER_MINUTE:.1f} min on difficult tasks"
            )
            contributing_factors["time_persistence"] = time_persistence

        # Help-seeking behavior (appropriate help-seeking shows persistence)
        help_requests = state.data.get("help_requests", 0)
        if 1 <= help_requests <= 3:  # Moderate help-seeking is positive
            help_persistence = 0.3
            persistence_score += help_persistence
            evidence.append(f"Appropriate help-seeking: {help_requests} requests")
            contributing_factors["help_seeking"] = help_persistence

        # Multiple strategy attempts
        strategies_tried = len(state.data.get("strategies_attempted", []))
        if strategies_tried > 1:
            strategy_persistence = min(0.3, strategies_tried * 0.1)
            persistence_score += strategy_persistence
            evidence.append(f"Tried {strategies_tried} different strategies")
            contributing_factors["strategy_diversity"] = strategy_persistence

        # Clamp to valid range
        persistence_score = max(0.0, min(1.0, persistence_score))

        # Confidence based on evidence
        confidence = min(1.0, len(evidence) / 2.0)

        return RewardComponent(
            dimension=RewardDimension.PERSISTENCE,
            raw_value=persistence_score,
            weight=1.0,
            confidence=confidence,
            evidence=evidence,
            contributing_factors=contributing_factors,
            learning_objective=context.get("learning_objective"),
            skill_area=state.subject_area,
        )

    async def _calculate_critical_thinking_reward(
        self,
        state: EnvironmentState,
        action: Any,
        result: ActionResult,
        context: Dict[str, Any],
    ) -> RewardComponent:
        """Calculate reward based on critical thinking skills"""

        thinking_score = 0.5  # Default
        evidence = []
        contributing_factors = {}

        # Analysis depth indicators
        analysis_indicators = state.data.get("analysis_depth", 0)
        if analysis_indicators > 0:
            thinking_score = min(1.0, analysis_indicators / 5.0)  # Up to 5 indicators
            evidence.append(f"Analysis depth: {analysis_indicators}")
            contributing_factors["analysis_depth"] = analysis_indicators / 5.0

        # Question asking (indicates critical thinking)
        questions_asked = state.data.get("questions_asked", 0)
        if questions_asked > 0:
            question_thinking = min(0.3, questions_asked * 0.1)
            thinking_score += question_thinking
            evidence.append(f"Asked {questions_asked} thoughtful questions")
            contributing_factors["questioning"] = question_thinking

        # Evidence evaluation
        evidence_evaluation = state.data.get("evaluated_sources", 0)
        if evidence_evaluation > 0:
            eval_thinking = min(0.4, evidence_evaluation * 0.2)
            thinking_score += eval_thinking
            evidence.append(f"Evaluated {evidence_evaluation} sources")
            contributing_factors["evidence_evaluation"] = eval_thinking

        # Logical reasoning patterns
        if state.state_type == StateType.QUIZ_SESSION:
            reasoning_quality = state.data.get("reasoning_quality", 0.5)
            thinking_score = (thinking_score + reasoning_quality) / 2
            evidence.append(f"Reasoning quality: {reasoning_quality:.2f}")
            contributing_factors["reasoning_quality"] = reasoning_quality

        # Clamp to valid range
        thinking_score = max(0.0, min(1.0, thinking_score))

        # Confidence based on subject area (higher for subjects that emphasize critical thinking)
        subject_emphasis = {
            "science": 0.9,
            "history": 0.8,
            "literature": 0.8,
            "philosophy": 0.9,
            "math": 0.7,
        }
        confidence = subject_emphasis.get(state.subject_area or "", 0.6)

        return RewardComponent(
            dimension=RewardDimension.CRITICAL_THINKING,
            raw_value=thinking_score,
            weight=1.0,
            confidence=confidence,
            evidence=evidence,
            contributing_factors=contributing_factors,
            learning_objective=context.get("learning_objective"),
            skill_area=state.subject_area,
        )

    async def _calculate_problem_solving_reward(
        self,
        state: EnvironmentState,
        action: Any,
        result: ActionResult,
        context: Dict[str, Any],
    ) -> RewardComponent:
        """Calculate reward based on problem-solving skills"""

        problem_solving_score = 0.5  # Default
        evidence = []
        contributing_factors = {}

        # Problem identification
        problems_identified = state.data.get("problems_identified", 0)
        if problems_identified > 0:
            identification_score = min(0.3, problems_identified * 0.1)
            problem_solving_score += identification_score
            evidence.append(f"Identified {problems_identified} problems")
            contributing_factors["problem_identification"] = identification_score

        # Solution generation
        solutions_generated = state.data.get("solutions_generated", 0)
        if solutions_generated > 0:
            solution_score = min(0.4, solutions_generated * 0.1)
            problem_solving_score += solution_score
            evidence.append(f"Generated {solutions_generated} solutions")
            contributing_factors["solution_generation"] = solution_score

        # Solution effectiveness
        if result and hasattr(result, "success") and result.success:
            solution_effectiveness = result.result_data.get("effectiveness", 0.7)
            problem_solving_score = (problem_solving_score + solution_effectiveness) / 2
            evidence.append(f"Solution effectiveness: {solution_effectiveness:.2f}")
            contributing_factors["solution_effectiveness"] = solution_effectiveness

        # Systematic approach
        systematic_steps = state.data.get("systematic_steps", 0)
        if systematic_steps > 2:  # More than basic steps
            systematic_score = min(0.3, systematic_steps * 0.05)
            problem_solving_score += systematic_score
            evidence.append(f"Used {systematic_steps} systematic steps")
            contributing_factors["systematic_approach"] = systematic_score

        # Transfer of learning (applying solutions to new problems)
        transfer_instances = state.data.get("learning_transfer", 0)
        if transfer_instances > 0:
            transfer_score = min(0.2, transfer_instances * 0.1)
            problem_solving_score += transfer_score
            evidence.append(f"Applied learning to {transfer_instances} new situations")
            contributing_factors["learning_transfer"] = transfer_score

        # Clamp to valid range
        problem_solving_score = max(0.0, min(1.0, problem_solving_score))

        # Confidence based on problem-solving context
        is_problem_solving_context = (
            "problem" in str(context.get("learning_objective", "")).lower()
            or state.state_type == StateType.QUIZ_SESSION
            or state.subject_area in ["math", "science", "engineering"]
        )
        confidence = 0.8 if is_problem_solving_context else 0.5

        return RewardComponent(
            dimension=RewardDimension.PROBLEM_SOLVING,
            raw_value=problem_solving_score,
            weight=1.0,
            confidence=confidence,
            evidence=evidence,
            contributing_factors=contributing_factors,
            learning_objective=context.get("learning_objective"),
            skill_area=state.subject_area,
        )

    async def _apply_adaptive_weighting(
        self,
        components: List[RewardComponent],
        state: EnvironmentState,
        context: Dict[str, Any],
    ) -> List[RewardComponent]:
        """Apply adaptive weighting based on learning objectives and student stage"""

        weighted_components = []

        for component in components:
            # Start with base weight
            new_weight = component.weight

            # Apply objective-based weighting
            learning_objective = context.get("learning_objective", "").lower()
            for objective, weights in self.objective_weights.items():
                if objective in learning_objective:
                    dimension_weight = weights.get(component.dimension, 1.0)
                    new_weight *= dimension_weight
                    break

            # Apply stage-based weighting
            student_stage = self._determine_learning_stage(state, context)
            if student_stage in self.stage_weights:
                stage_weight = self.stage_weights[student_stage].get(
                    component.dimension, 1.0
                )
                new_weight *= stage_weight

            # Create new component with adjusted weight
            weighted_component = RewardComponent(
                dimension=component.dimension,
                raw_value=component.raw_value,
                weight=new_weight,
                confidence=component.confidence,
                evidence=component.evidence,
                contributing_factors=component.contributing_factors,
                learning_objective=component.learning_objective,
                skill_area=component.skill_area,
                difficulty_level=component.difficulty_level,
            )

            weighted_components.append(weighted_component)

        return weighted_components

    def _determine_learning_stage(
        self, state: EnvironmentState, context: Dict[str, Any]
    ) -> str:
        """Determine the student's current learning stage"""

        # Use multiple indicators to determine stage
        indicators = []

        # Grade level indicator
        if state.grade_level:
            grade_level = int(state.grade_level)
            if grade_level <= 5:
                indicators.append("novice")
            elif grade_level <= 8:
                indicators.append("developing")
            else:
                indicators.append("proficient")

        # Performance indicator
        if state.student_id:
            recent_performance = self.learning_curve_analyzer.learning_curves.get(
                state.student_id
            )
            if recent_performance:
                avg_performance = np.mean(
                    [p["performance"] for p in recent_performance]
                )
                if avg_performance < 0.4:
                    indicators.append("novice")
                elif avg_performance < 0.7:
                    indicators.append("developing")
                else:
                    indicators.append("proficient")

        # Subject experience indicator
        subject_experience = context.get("subject_experience", "novice")
        indicators.append(subject_experience)

        # Return most common indicator
        if indicators:
            return max(set(indicators), key=indicators.count)
        else:
            return "developing"  # Default

    async def _normalize_reward(
        self, raw_reward: float, student_id: Optional[str]
    ) -> float:
        """Normalize reward based on historical distribution"""

        if not self.reward_history:
            return raw_reward  # No history to normalize against

        # Calculate statistics from reward history
        recent_rewards = [r.total_reward for r in self.reward_history]
        mean_reward = np.mean(recent_rewards)
        std_reward = np.std(recent_rewards)

        if std_reward == 0:
            return 0.5  # No variation, return neutral reward

        # Z-score normalization, then map to 0-1 range
        z_score = (raw_reward - mean_reward) / std_reward

        # Use sigmoid function to map to 0-1 range
        normalized = 1 / (1 + np.exp(-z_score))

        return float(normalized)

    def _determine_reward_type(
        self, action: Any, result: ActionResult, context: Dict[str, Any]
    ) -> RewardType:
        """Determine the type of reward based on context"""

        # Check for achievement milestones
        if context.get("milestone_reached") or context.get("goal_completed"):
            return RewardType.ACHIEVEMENT

        # Check for progress-based rewards
        if context.get("progress_made") or context.get("skill_improvement"):
            return RewardType.PROGRESS

        # Check for collaborative activities
        if context.get("collaborative_activity") or context.get("peer_interaction"):
            return RewardType.SOCIAL

        # Check for behavioral rewards
        if context.get("effort_recognition") or context.get("persistence_shown"):
            return RewardType.BEHAVIORAL

        # Check for adaptive rewards
        if context.get("difficulty_adjusted") or context.get("personalized_content"):
            return RewardType.ADAPTIVE

        # Default to immediate reward
        return RewardType.IMMEDIATE

    def _calculate_reward_confidence(
        self, components: List[RewardComponent], state: EnvironmentState
    ) -> float:
        """Calculate overall confidence in the reward signal"""

        if not components:
            return 0.0

        # Weight confidence by component weights
        total_weighted_confidence = sum(
            comp.confidence * comp.weight for comp in components
        )
        total_weight = sum(comp.weight for comp in components)

        if total_weight == 0:
            return 0.0

        base_confidence = total_weighted_confidence / total_weight

        # Adjust confidence based on state quality
        state_quality_factor = {
            "excellent": 1.0,
            "good": 0.9,
            "fair": 0.7,
            "poor": 0.5,
        }.get(state.quality.value, 0.5)

        return base_confidence * state_quality_factor

    def _calculate_reward_reliability(
        self, components: List[RewardComponent], context: Dict[str, Any]
    ) -> float:
        """Calculate reliability of the reward signal"""

        reliability_factors = []

        # Data completeness factor
        data_completeness = context.get("data_completeness", 0.5)
        reliability_factors.append(data_completeness)

        # Number of evidence points
        total_evidence = sum(len(comp.evidence) for comp in components)
        evidence_factor = min(
            1.0, total_evidence / (len(components) * 2)
        )  # 2 evidence per component
        reliability_factors.append(evidence_factor)

        # Consistency across dimensions
        if len(components) > 1:
            values = [comp.weighted_value for comp in components]
            consistency = 1.0 - np.std(values)  # Lower std = higher consistency
            reliability_factors.append(max(0.0, consistency))
        else:
            reliability_factors.append(0.7)  # Moderate reliability for single dimension

        return np.mean(reliability_factors)

    async def _generate_educational_feedback(
        self,
        components: List[RewardComponent],
        state: EnvironmentState,
        total_reward: float,
    ) -> Tuple[str, List[str], List[str]]:
        """Generate educational feedback and recommendations"""

        # Determine overall performance level
        if total_reward >= 0.8:
            performance_level = "excellent"
        elif total_reward >= 0.6:
            performance_level = "good"
        elif total_reward >= 0.4:
            performance_level = "fair"
        else:
            performance_level = "needs_improvement"

        # Generate feedback message
        feedback_templates = {
            "excellent": "Outstanding work! You're demonstrating strong skills and making great progress.",
            "good": "Good job! You're on the right track and showing solid understanding.",
            "fair": "You're making progress. Keep working and focus on the areas that need more attention.",
            "needs_improvement": "Don't give up! Learning takes time. Let's focus on building your skills step by step.",
        }

        base_feedback = feedback_templates[performance_level]

        # Add specific dimension feedback
        strong_dimensions = [comp for comp in components if comp.weighted_value >= 0.7]
        weak_dimensions = [comp for comp in components if comp.weighted_value < 0.4]

        if strong_dimensions:
            strengths = [
                comp.dimension.value.replace("_", " ").title()
                for comp in strong_dimensions[:2]
            ]
            base_feedback += f" Your {' and '.join(strengths)} are particularly strong."

        # Generate recommendations
        recommendations = []
        if weak_dimensions:
            for comp in weak_dimensions[:3]:  # Top 3 areas for improvement
                dimension_name = comp.dimension.value.replace("_", " ")
                recommendations.append(f"Focus on improving {dimension_name}")

        # Add context-specific recommendations
        if state.state_type == StateType.QUIZ_SESSION and total_reward < 0.6:
            recommendations.append("Review the material and try practice questions")
        elif state.state_type == StateType.ROBLOX_GAME and total_reward < 0.6:
            recommendations.append("Explore different tools and approaches")

        if not recommendations:
            if total_reward >= 0.7:
                recommendations.append(
                    "Continue challenging yourself with harder problems"
                )
            else:
                recommendations.append(
                    "Keep practicing and don't hesitate to ask for help"
                )

        # Identify areas for improvement
        improvements = []
        for comp in weak_dimensions:
            dimension_name = comp.dimension.value.replace("_", " ")
            improvements.append(dimension_name)

        return base_feedback, recommendations[:3], improvements[:3]

    async def _calculate_learning_gains(
        self, components: List[RewardComponent], state: EnvironmentState
    ) -> Dict[str, float]:
        """Calculate specific learning gains by area"""

        gains = {}

        for component in components:
            if component.learning_objective:
                objective = component.learning_objective.replace("_", " ").title()
                gains[objective] = component.weighted_value

            if component.skill_area:
                skill = component.skill_area.replace("_", " ").title()
                if skill in gains:
                    gains[skill] = (gains[skill] + component.weighted_value) / 2
                else:
                    gains[skill] = component.weighted_value

        # Add overall learning gain
        if components:
            overall_gain = np.mean([comp.weighted_value for comp in components])
            gains["Overall Learning"] = overall_gain

        return gains

    async def _calculate_skill_improvements(
        self, components: List[RewardComponent], state: EnvironmentState
    ) -> Dict[str, float]:
        """Calculate skill improvements in different areas"""

        improvements = {}

        # Map dimensions to skills
        dimension_to_skill = {
            RewardDimension.PROBLEM_SOLVING: "Problem Solving",
            RewardDimension.CRITICAL_THINKING: "Critical Thinking",
            RewardDimension.CREATIVITY: "Creativity",
            RewardDimension.COLLABORATION: "Teamwork",
            RewardDimension.COMMUNICATION: "Communication",
            RewardDimension.PERSISTENCE: "Perseverance",
        }

        for component in components:
            if component.dimension in dimension_to_skill:
                skill = dimension_to_skill[component.dimension]
                improvements[skill] = component.weighted_value

        # Subject-specific improvements
        if state.subject_area:
            subject_components = [
                comp for comp in components if comp.skill_area == state.subject_area
            ]
            if subject_components:
                subject_improvement = np.mean(
                    [comp.weighted_value for comp in subject_components]
                )
                improvements[f"{state.subject_area.title()} Skills"] = (
                    subject_improvement
                )

        return improvements

    async def _update_reward_statistics(self, reward_signal: RewardSignal):
        """Update reward statistics and history"""

        # Add to history
        self.reward_history.append(reward_signal)

        # Update dimension statistics
        for component in reward_signal.components:
            dimension = component.dimension.value
            value = component.weighted_value

            stats = self.dimension_statistics[dimension]

            # Update running statistics
            n = len(self.reward_history)
            if n == 1:
                stats["mean"] = value
                stats["std"] = 0.1
                stats["min"] = value
                stats["max"] = value
            else:
                # Update mean
                old_mean = stats["mean"]
                stats["mean"] = old_mean + (value - old_mean) / n

                # Update min/max
                stats["min"] = min(stats["min"], value)
                stats["max"] = max(stats["max"], value)

                # Approximate std update (simplified)
                if n > 2:
                    stats["std"] = (
                        stats["std"] * 0.95 + abs(value - stats["mean"]) * 0.05
                    )

        # Update reward distribution
        reward_bucket = int(reward_signal.total_reward * 10)  # 0-10 buckets
        self.calculation_stats["reward_distribution"][reward_bucket] += 1

    async def _update_student_reward_profile(
        self, student_id: str, reward_signal: RewardSignal
    ):
        """Update individual student reward profile"""

        if student_id not in self.student_reward_profiles:
            self.student_reward_profiles[student_id] = {
                "reward_history": deque(maxlen=50),
                "dimension_preferences": {},
                "average_reward": 0.0,
                "reward_trend": 0.0,
                "last_updated": datetime.now(),
            }

        profile = self.student_reward_profiles[student_id]
        profile["reward_history"].append(reward_signal.total_reward)

        # Update average reward
        profile["average_reward"] = np.mean(profile["reward_history"])

        # Update reward trend
        if len(profile["reward_history"]) >= 5:
            recent = list(profile["reward_history"])[-5:]
            earlier = (
                list(profile["reward_history"])[-10:-5]
                if len(profile["reward_history"]) >= 10
                else recent
            )
            profile["reward_trend"] = np.mean(recent) - np.mean(earlier)

        # Update dimension preferences
        for component in reward_signal.components:
            dimension = component.dimension.value
            if dimension not in profile["dimension_preferences"]:
                profile["dimension_preferences"][dimension] = deque(maxlen=20)
            profile["dimension_preferences"][dimension].append(component.weighted_value)

        profile["last_updated"] = datetime.now()

    async def get_student_profile(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get student reward profile"""

        if student_id not in self.student_reward_profiles:
            return None

        profile = self.student_reward_profiles[student_id].copy()

        # Convert deques to lists for JSON serialization
        profile["reward_history"] = list(profile["reward_history"])

        dimension_prefs = {}
        for dimension, values in profile["dimension_preferences"].items():
            dimension_prefs[dimension] = {
                "average": np.mean(values),
                "trend": (
                    np.mean(list(values)[-3:]) - np.mean(list(values)[:3])
                    if len(values) >= 6
                    else 0
                ),
                "consistency": 1.0 - np.std(values) if len(values) > 1 else 0.5,
            }
        profile["dimension_preferences"] = dimension_prefs

        profile["last_updated"] = profile["last_updated"].isoformat()

        return profile

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of RewardCalculator"""

        return {
            "dimensions": self.dimensions,
            "normalization_enabled": self.normalization_enabled,
            "reward_history_size": len(self.reward_history),
            "student_profiles": len(self.student_reward_profiles),
            "calculation_stats": self.calculation_stats.copy(),
            "dimension_statistics": dict(self.dimension_statistics),
            "analyzers": {
                "learning_curves_tracked": len(
                    self.learning_curve_analyzer.learning_curves
                ),
                "engagement_analyzer_active": True,
                "creativity_assessment_active": True,
                "collaboration_assessment_active": True,
            },
            "recent_performance": {
                "average_reward": (
                    np.mean([r.total_reward for r in self.reward_history])
                    if self.reward_history
                    else 0
                ),
                "reward_range": (
                    (
                        min(r.total_reward for r in self.reward_history),
                        max(r.total_reward for r in self.reward_history),
                    )
                    if self.reward_history
                    else (0, 0)
                ),
            },
        }

    async def reset(self):
        """Reset RewardCalculator to initial state"""

        logger.info("Resetting RewardCalculator")

        # Clear history and statistics
        self.reward_history.clear()
        self.dimension_statistics.clear()
        self.student_reward_profiles.clear()

        # Reset analyzers
        self.learning_curve_analyzer = LearningCurveAnalyzer()

        # Reset calculation stats
        self.calculation_stats = {
            "total_calculations": 0,
            "average_calculation_time": 0.0,
            "reward_distribution": defaultdict(int),
        }

        logger.info("RewardCalculator reset completed")
