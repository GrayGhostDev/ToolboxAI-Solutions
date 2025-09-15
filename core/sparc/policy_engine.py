"""
Policy Engine - Educational Policy Decisions and Learning
========================================================

The PolicyEngine handles intelligent decision-making for educational AI agents:
- Multi-objective policy optimization for educational goals
- Adaptive learning algorithms that improve over time
- Context-aware policy decisions based on student needs
- Integration with educational standards and learning objectives
- Real-time policy adaptation based on student performance

This component implements sophisticated educational AI policies that balance
learning effectiveness, student engagement, and curriculum requirements.
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import secrets  # Use secrets for secure randomness (SonarQube: S2245)
from collections import defaultdict, deque
import json  # Use JSON instead of pickle for security (SonarQube: S5301)
from pathlib import Path

from .state_manager import EnvironmentState, StateType, StateQuality

logger = logging.getLogger(__name__)


class PolicyType(Enum):
    """Types of educational policies"""

    EXPLORATION = "exploration"  # Encourage exploration and discovery
    EXPLOITATION = "exploitation"  # Focus on mastering known concepts
    SCAFFOLDING = "scaffolding"  # Provide learning support
    CHALLENGE = "challenge"  # Increase difficulty appropriately
    COLLABORATION = "collaboration"  # Promote group learning
    ASSESSMENT = "assessment"  # Evaluate learning progress
    ADAPTATION = "adaptation"  # Adapt to individual needs


class LearningObjective(Enum):
    """Primary learning objectives"""

    KNOWLEDGE_ACQUISITION = "knowledge_acquisition"
    SKILL_DEVELOPMENT = "skill_development"
    PROBLEM_SOLVING = "problem_solving"
    CREATIVE_EXPRESSION = "creative_expression"
    CRITICAL_THINKING = "critical_thinking"
    COLLABORATION = "collaboration"
    COMMUNICATION = "communication"


class PolicyDefaults:
    """Provide sensible defaults for all policy attributes"""
    
    DEFAULT_LEARNING_RATE = 0.01
    DEFAULT_EXPLORATION_RATE = 0.1
    DEFAULT_EPSILON = 0.2
    DEFAULT_GAMMA = 0.95
    DEFAULT_POLICY_TYPE = PolicyType.EXPLORATION
    DEFAULT_LEARNING_OBJECTIVE = LearningObjective.KNOWLEDGE_ACQUISITION
    DEFAULT_CONFIDENCE = 0.7
    DEFAULT_IMPACT_SCORE = 0.5
    DEFAULT_PRIORITY = 1
    DEFAULT_AGE_RANGE = (8, 18)
    DEFAULT_DIFFICULTY = 0.5
    DEFAULT_ENGAGEMENT = 0.6
    
    @classmethod
    def get_default_policy(cls) -> 'EducationalPolicy':
        """Return fully initialized default policy"""
        return EducationalPolicy(
            policy_id="default_policy",
            name="Default Educational Policy",
            description="Safe default policy for general educational use",
            learning_objectives=[cls.DEFAULT_LEARNING_OBJECTIVE],
            target_age_range=cls.DEFAULT_AGE_RANGE,
            subject_areas=["general"],
            exploration_weight=0.4,
            exploitation_weight=0.3,
            scaffolding_weight=0.2,
            challenge_weight=0.1
        )
    
    @classmethod
    def get_default_state(cls) -> EnvironmentState:
        """Return a safe default environment state"""
        return EnvironmentState(
            state_type=StateType.LEARNING,
            quality=StateQuality.MEDIUM,
            timestamp=datetime.now(),
            data={
                "difficulty": cls.DEFAULT_DIFFICULTY,
                "engagement": cls.DEFAULT_ENGAGEMENT,
                "progress": 0.0,
                "session_time": 0,
                "attempts": 0
            },
            metadata={
                "initialized": True,
                "is_default": True
            }
        )
    
    @classmethod
    def get_default_decision(cls) -> 'PolicyDecision':
        """Return a safe default policy decision"""
        return PolicyDecision(
            decision_id=f"default_{datetime.now().timestamp()}",
            policy_type=cls.DEFAULT_POLICY_TYPE,
            action="continue_learning",
            parameters={
                "difficulty": cls.DEFAULT_DIFFICULTY,
                "support_level": "medium",
                "feedback_type": "encouraging"
            },
            confidence=cls.DEFAULT_CONFIDENCE,
            reasoning="Using default policy due to missing input",
            expected_outcome="Standard learning progression",
            learning_objectives=[cls.DEFAULT_LEARNING_OBJECTIVE],
            timestamp=datetime.now(),
            metadata={"is_default": True}
        )


@dataclass
class PolicyDecision:
    """Represents a policy decision with action and rationale"""

    # Core decision
    policy_type: PolicyType
    action_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Priority and timing
    priority: float = 0.5  # 0-1 priority level
    urgency: float = 0.5  # 0-1 urgency level
    estimated_duration: float = 30.0  # seconds

    # Educational context
    learning_objective: Optional[LearningObjective] = None
    target_skills: List[str] = field(default_factory=list)
    difficulty_level: float = 0.5  # 0-1 difficulty

    # Decision rationale
    rationale: str = ""
    confidence: float = 0.5  # 0-1 confidence in decision
    expected_outcomes: List[str] = field(default_factory=list)

    # Follow-up actions
    next_actions: List[str] = field(default_factory=list)
    conditions_for_next: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    decision_id: str = field(default_factory=lambda: f"decision_{datetime.now().timestamp()}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result["policy_type"] = self.policy_type.value
        result["learning_objective"] = self.learning_objective.value if self.learning_objective else None
        result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class EducationalPolicy:
    """Represents an educational policy with learning parameters"""

    # Policy identification
    policy_id: str
    name: str
    description: str

    # Educational parameters
    learning_objectives: List[LearningObjective]
    target_age_range: Tuple[int, int]  # (min_age, max_age)
    subject_areas: List[str]

    # Policy weights (0-1 for each aspect)
    exploration_weight: float = 0.3
    exploitation_weight: float = 0.4
    scaffolding_weight: float = 0.2
    challenge_weight: float = 0.1

    # Adaptation parameters
    adaptation_rate: float = 0.1  # How quickly to adapt
    success_threshold: float = 0.7  # Success rate to maintain
    difficulty_adjustment_rate: float = 0.05

    # Constraints
    max_difficulty_increase: float = 0.2
    min_engagement_threshold: float = 0.6
    required_mastery_level: float = 0.8

    # Performance tracking
    success_count: int = 0
    total_applications: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def success_rate(self) -> float:
        """Current success rate of the policy"""
        if self.total_applications == 0:
            return 0.0
        return self.success_count / self.total_applications

    def update_performance(self, success: bool):
        """Update performance metrics"""
        self.total_applications += 1
        if success:
            self.success_count += 1
        self.last_updated = datetime.now()


class PolicyEngine:
    """
    Advanced educational policy engine with learning capabilities.

    The PolicyEngine implements sophisticated algorithms for making educational
    decisions that adapt to student needs, learning progress, and contextual factors.
    It balances multiple objectives while maintaining educational effectiveness.
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        exploration_rate: float = 0.1,
        decay_factor: float = 0.95,
        update_frequency: int = 10,
    ):
        """
        Initialize PolicyEngine.

        Args:
            learning_rate: Rate of policy learning and adaptation
            exploration_rate: Rate of exploration vs exploitation
            decay_factor: Decay factor for older experiences
            update_frequency: How often to update policies
        """
        self.learning_rate = learning_rate
        self.exploration_rate = exploration_rate
        self.decay_factor = decay_factor
        self.update_frequency = update_frequency

        # Policy storage
        self.policies: Dict[str, EducationalPolicy] = {}
        self.policy_history: deque = deque(maxlen=1000)
        self.decision_history: deque = deque(maxlen=500)

        # Learning algorithms
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.state_action_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.reward_history: deque = deque(maxlen=100)

        # Student models
        self.student_models: Dict[str, Dict[str, Any]] = {}
        self.learning_curves: Dict[str, List[float]] = defaultdict(list)

        # Educational objectives tracking
        self.objective_progress: Dict[LearningObjective, float] = {obj: 0.0 for obj in LearningObjective}

        # Performance metrics
        self.policy_performance: Dict[str, Dict[str, float]] = {}
        self.adaptation_log: List[Dict[str, Any]] = []
        self.decision_count = 0

        # Persistence
        self.persistence_path = Path("data/policy_engine")
        self.persistence_path.mkdir(parents=True, exist_ok=True)

        # Initialize default policies
        self._initialize_default_policies()

        logger.info(f"PolicyEngine initialized with learning_rate={learning_rate}")

    def _initialize_default_policies(self):
        """Initialize default educational policies"""

        # Beginner-friendly exploration policy
        exploration_policy = EducationalPolicy(
            policy_id="exploration_beginner",
            name="Beginner Exploration",
            description="Encourages exploration and discovery for new learners",
            learning_objectives=[LearningObjective.KNOWLEDGE_ACQUISITION, LearningObjective.CREATIVE_EXPRESSION],
            target_age_range=(6, 12),
            subject_areas=["general", "science", "math"],
            exploration_weight=0.6,
            exploitation_weight=0.2,
            scaffolding_weight=0.2,
            challenge_weight=0.0,
        )

        # Advanced challenge policy
        challenge_policy = EducationalPolicy(
            policy_id="challenge_advanced",
            name="Advanced Challenge",
            description="Provides appropriate challenges for advanced learners",
            learning_objectives=[LearningObjective.PROBLEM_SOLVING, LearningObjective.CRITICAL_THINKING],
            target_age_range=(12, 18),
            subject_areas=["math", "science", "engineering"],
            exploration_weight=0.2,
            exploitation_weight=0.3,
            scaffolding_weight=0.1,
            challenge_weight=0.4,
        )

        # Collaborative learning policy
        collaboration_policy = EducationalPolicy(
            policy_id="collaboration_group",
            name="Collaborative Learning",
            description="Promotes group learning and communication",
            learning_objectives=[LearningObjective.COLLABORATION, LearningObjective.COMMUNICATION],
            target_age_range=(8, 18),
            subject_areas=["general"],
            exploration_weight=0.3,
            exploitation_weight=0.2,
            scaffolding_weight=0.3,
            challenge_weight=0.2,
        )

        self.policies = {
            "exploration_beginner": exploration_policy,
            "challenge_advanced": challenge_policy,
            "collaboration_group": collaboration_policy,
        }

        logger.debug(f"Initialized {len(self.policies)} default policies")
    
    def _get_default_state(self) -> EnvironmentState:
        """Get default state when none is provided"""
        return PolicyDefaults.get_default_state()

    async def decide(self, policy_input: Optional[Dict[str, Any]] = None) -> PolicyDecision:
        """
        Make a policy decision based on current state and context.

        Args:
            policy_input: Dictionary containing state, context, and history

        Returns:
            PolicyDecision with recommended action
        """
        start_time = datetime.now()
        self.decision_count += 1

        try:
            # Handle null input
            if policy_input is None:
                policy_input = {}
            
            # Extract input components with defaults
            current_state = policy_input.get("state")
            user_context = policy_input.get("context", {})
            state_history = policy_input.get("history", [])

            # Use default state if none provided
            if not current_state:
                current_state = self._get_default_state()
                logger.warning("No state provided, using default state")

            # Analyze student needs and context
            student_analysis = await self._analyze_student_needs(current_state, user_context)

            # Select appropriate policy
            selected_policy = await self._select_policy(student_analysis, current_state)

            # Generate decision using selected policy
            decision = await self._generate_decision(selected_policy, current_state, student_analysis, state_history)

            # Add decision to history
            self.decision_history.append(decision)

            # Update Q-learning table
            await self._update_q_learning(current_state, decision)

            decision_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Policy decision made in {decision_time:.3f}s: {decision.action_type}")

            return decision

        except Exception as e:
            logger.error(f"Failed to make policy decision: {e}")
            # Return safe default decision
            return await self._generate_safe_default_decision(policy_input)

    async def _analyze_student_needs(self, state: EnvironmentState, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze student needs based on state and context"""
        
        # Ensure context is not None
        if context is None:
            context = {}

        # Safe attribute access with defaults
        analysis = {
            "student_id": getattr(state, 'student_id', None) or "unknown_student",
            "current_subject": getattr(state, 'subject_area', None) or "general",
            "current_grade": getattr(state, 'grade_level', None) or 7,
            "engagement_level": 0.5,
            "difficulty_preference": 0.5,
            "learning_style": "unknown",
            "strengths": [],
            "weaknesses": [],
            "recent_performance": [],
        }

        # Extract engagement indicators from state
        if state.state_type == StateType.ROBLOX_GAME:
            game_data = state.game_state or {}
            active_time = game_data.get("active_time", 0)
            interactions = game_data.get("interaction_count", 0)

            # Simple engagement heuristic
            if active_time > 300:  # More than 5 minutes
                analysis["engagement_level"] = min(1.0, active_time / 1800)  # Cap at 30 min
            if interactions > 10:
                analysis["engagement_level"] = min(1.0, analysis["engagement_level"] + 0.2)

        # Analyze quiz performance if available
        if state.state_type == StateType.QUIZ_SESSION:
            quiz_data = state.data.get("quiz_data", {})
            if "scores" in quiz_data:
                recent_scores = quiz_data["scores"][-5:]  # Last 5 scores
                analysis["recent_performance"] = recent_scores
                avg_score = np.mean(recent_scores) if recent_scores else 0.5

                # Adjust difficulty preference based on performance
                if avg_score > 0.8:
                    analysis["difficulty_preference"] = min(1.0, avg_score + 0.1)
                elif avg_score < 0.6:
                    analysis["difficulty_preference"] = max(0.3, avg_score - 0.1)

        # Get student model if available
        if state.student_id and state.student_id in self.student_models:
            student_model = self.student_models[state.student_id]
            analysis.update(
                {
                    "learning_style": student_model.get("learning_style", "unknown"),
                    "strengths": student_model.get("strengths", []),
                    "weaknesses": student_model.get("weaknesses", []),
                    "preferred_difficulty": student_model.get("preferred_difficulty", 0.5),
                }
            )

        # Analyze learning curve trends
        if state.student_id in self.learning_curves:
            curve = self.learning_curves[state.student_id]
            if len(curve) >= 3:
                recent_trend = np.mean(curve[-3:]) - np.mean(curve[-6:-3]) if len(curve) >= 6 else 0
                analysis["learning_trend"] = recent_trend

                # Adjust engagement based on trend
                if recent_trend > 0.1:  # Improving
                    analysis["engagement_level"] = min(1.0, analysis["engagement_level"] + 0.1)
                elif recent_trend < -0.1:  # Declining
                    analysis["engagement_level"] = max(0.2, analysis["engagement_level"] - 0.1)

        return analysis

    async def _select_policy(self, student_analysis: Dict[str, Any], state: EnvironmentState) -> EducationalPolicy:
        """Select the most appropriate policy for the current situation"""
        
        # Null safety check
        if not self.policies:
            logger.warning("No policies available, using default")
            return self._create_default_policy()

        best_policy = None
        best_score = -1

        for policy_id, policy in self.policies.items():
            score = await self._score_policy(policy, student_analysis, state)

            if score > best_score:
                best_score = score
                best_policy = policy

        # Add some exploration - occasionally try non-optimal policies
        # Use SystemRandom for better randomness (SonarQube: S2245)
        secure_random = secrets.SystemRandom()
        if secure_random.random() < self.exploration_rate and len(self.policies) > 1:
            alternative_policies = [p for p in self.policies.values() if p != best_policy]
            if alternative_policies:  # Null safety check
                best_policy = secure_random.choice(alternative_policies)
                logger.debug(f"Exploration: selected alternative policy {best_policy.policy_id}")

        return best_policy or self._create_default_policy()  # Safe fallback

    async def _score_policy(
        self, policy: EducationalPolicy, student_analysis: Dict[str, Any], state: EnvironmentState
    ) -> float:
        """Score how well a policy matches the current situation"""

        score = 0.0

        # Age appropriateness
        student_grade = int(student_analysis.get("current_grade", 8))
        student_age = student_grade + 5  # Rough age estimation

        if policy.target_age_range[0] <= student_age <= policy.target_age_range[1]:
            score += 0.3
        else:
            # Penalty for age mismatch
            age_diff = min(abs(student_age - policy.target_age_range[0]), abs(student_age - policy.target_age_range[1]))
            score -= age_diff * 0.05

        # Subject area match
        current_subject = student_analysis.get("current_subject", "").lower()
        if current_subject in [area.lower() for area in policy.subject_areas]:
            score += 0.2
        elif "general" in policy.subject_areas:
            score += 0.1

        # Performance-based scoring
        engagement = student_analysis.get("engagement_level", 0.5)
        difficulty_pref = student_analysis.get("difficulty_preference", 0.5)

        # Match policy weights to student needs
        if engagement < 0.4:  # Low engagement - need exploration/scaffolding
            score += policy.exploration_weight * 0.3 + policy.scaffolding_weight * 0.2
        elif engagement > 0.7:  # High engagement - can handle challenges
            score += policy.challenge_weight * 0.3 + policy.exploitation_weight * 0.2

        # Difficulty matching
        if difficulty_pref > 0.7 and policy.challenge_weight > 0.3:
            score += 0.2
        elif difficulty_pref < 0.4 and policy.scaffolding_weight > 0.3:
            score += 0.2

        # Historical performance of policy
        policy_success = getattr(policy, 'success_rate', 0.7)  # Default to 0.7 if not set
        score += policy_success * 0.3

        # Learning objectives alignment
        state_objectives = self._infer_learning_objectives(state)
        objective_overlap = len(set(policy.learning_objectives) & set(state_objectives))
        score += objective_overlap * 0.1

        return max(0, score)

    def _infer_learning_objectives(self, state: EnvironmentState) -> List[LearningObjective]:
        """Infer likely learning objectives from current state"""
        
        # Null safety check
        if not state:
            return [LearningObjective.KNOWLEDGE_ACQUISITION]  # Default objective

        objectives = []

        if hasattr(state, 'state_type') and state.state_type == StateType.QUIZ_SESSION:
            objectives.extend([LearningObjective.KNOWLEDGE_ACQUISITION, LearningObjective.PROBLEM_SOLVING])
        elif hasattr(state, 'state_type') and state.state_type == StateType.ROBLOX_GAME:
            objectives.extend([LearningObjective.CREATIVE_EXPRESSION, LearningObjective.SKILL_DEVELOPMENT])

            # Check for collaborative elements with null safety
            if hasattr(state, 'player_positions') and state.player_positions and len(state.player_positions) > 1:
                objectives.append(LearningObjective.COLLABORATION)

        elif hasattr(state, 'state_type') and state.state_type == StateType.EDUCATIONAL_CONTENT:
            objectives.append(LearningObjective.KNOWLEDGE_ACQUISITION)

        # Subject-specific objectives with null safety
        if hasattr(state, 'subject_area') and state.subject_area:
            subject = state.subject_area.lower()
            if subject in ["math", "mathematics"]:
                objectives.append(LearningObjective.PROBLEM_SOLVING)
            elif subject in ["science", "physics", "chemistry"]:
                objectives.extend([LearningObjective.CRITICAL_THINKING, LearningObjective.PROBLEM_SOLVING])
            elif subject in ["art", "creative", "design"]:
                objectives.append(LearningObjective.CREATIVE_EXPRESSION)

        return objectives if objectives else [LearningObjective.KNOWLEDGE_ACQUISITION]  # Ensure non-empty

    def _create_default_policy(self) -> EducationalPolicy:
        """Create a default educational policy for fallback scenarios"""
        return EducationalPolicy(
            policy_id="default_policy",
            name="Balanced Learning Policy",
            description="Default balanced policy for general education",
            learning_objectives=[
                LearningObjective.KNOWLEDGE_ACQUISITION,
                LearningObjective.SKILL_DEVELOPMENT,
                LearningObjective.PROBLEM_SOLVING
            ],
            target_age_range=(7, 18),  # Wide age range
            subject_areas=["general", "math", "science", "language"],
            exploration_weight=0.3,
            exploitation_weight=0.4,
            scaffolding_weight=0.2,
            challenge_weight=0.1,
            adaptation_rate=0.1,
            success_threshold=0.7,
            difficulty_adjustment_rate=0.05,
            max_difficulty_increase=0.2,
            min_engagement_threshold=0.6,
            success_rate=0.7  # Default success rate
        )

    async def _generate_decision(
        self,
        policy: EducationalPolicy,
        state: EnvironmentState,
        student_analysis: Dict[str, Any],
        history: List[EnvironmentState],
    ) -> PolicyDecision:
        """Generate a specific decision based on policy and context"""

        # Determine action type based on policy and current state
        action_type = await self._select_action_type(policy, state, student_analysis)

        # Generate parameters for the action
        parameters = await self._generate_action_parameters(action_type, policy, state, student_analysis)

        # Calculate priority and urgency
        priority = await self._calculate_priority(action_type, state, student_analysis)
        urgency = await self._calculate_urgency(action_type, state, student_analysis)

        # Estimate duration
        duration = await self._estimate_action_duration(action_type, parameters)

        # Generate rationale
        rationale = await self._generate_rationale(action_type, policy, student_analysis, state)

        # Predict expected outcomes
        outcomes = await self._predict_outcomes(action_type, parameters, student_analysis)

        # Plan next actions
        next_actions = await self._plan_next_actions(action_type, policy, student_analysis)

        # Infer primary learning objective
        primary_objective = self._select_primary_objective(policy, state)

        # Determine target skills
        target_skills = self._identify_target_skills(state, student_analysis)

        # Calculate difficulty level
        difficulty = self._calculate_difficulty_level(policy, student_analysis, state)

        # Calculate confidence in decision
        confidence = await self._calculate_decision_confidence(policy, action_type, student_analysis)

        decision = PolicyDecision(
            policy_type=self._map_action_to_policy_type(action_type),
            action_type=action_type,
            parameters=parameters,
            priority=priority,
            urgency=urgency,
            estimated_duration=duration,
            learning_objective=primary_objective,
            target_skills=target_skills,
            difficulty_level=difficulty,
            rationale=rationale,
            confidence=confidence,
            expected_outcomes=outcomes,
            next_actions=next_actions,
        )

        return decision

    async def _select_action_type(
        self, policy: EducationalPolicy, state: EnvironmentState, analysis: Dict[str, Any]
    ) -> str:
        """Select the most appropriate action type"""

        # Weight different action types based on policy
        action_weights = {
            "provide_hint": policy.scaffolding_weight,
            "increase_difficulty": policy.challenge_weight,
            "encourage_exploration": policy.exploration_weight,
            "reinforce_learning": policy.exploitation_weight,
            "create_quiz": policy.exploitation_weight * 0.7,
            "generate_content": policy.exploration_weight * 0.8,
            "facilitate_collaboration": policy.scaffolding_weight * 0.6,
            "provide_feedback": policy.exploitation_weight * 0.9,
            "adapt_difficulty": (policy.challenge_weight + policy.scaffolding_weight) * 0.5,
        }

        # Adjust weights based on current situation with null safety
        engagement = analysis.get("engagement_level", 0.5) if analysis else 0.5
        performance = analysis.get("recent_performance", []) if analysis else []

        if engagement < 0.4:
            action_weights["encourage_exploration"] *= 1.5
            action_weights["provide_hint"] *= 1.3
        elif engagement > 0.7:
            action_weights["increase_difficulty"] *= 1.4
            action_weights["create_quiz"] *= 1.2

        if performance:
            try:
                perf_mean = np.mean(performance)
                if perf_mean > 0.8:
                    action_weights["increase_difficulty"] *= 1.3
                elif perf_mean < 0.6:
                    action_weights["provide_hint"] *= 1.4
                    action_weights["adapt_difficulty"] *= 1.2
            except (ValueError, TypeError):
                # Handle invalid performance data
                pass

        # State-specific adjustments with null safety
        if state and hasattr(state, 'state_type'):
            if state.state_type == StateType.QUIZ_SESSION:
                action_weights["provide_feedback"] *= 1.5
                action_weights["adapt_difficulty"] *= 1.3
            elif state.state_type == StateType.ROBLOX_GAME:
                action_weights["encourage_exploration"] *= 1.3
                action_weights["generate_content"] *= 1.2

        # Select action with weighted random choice
        actions, weights = zip(*action_weights.items())
        weights_array = np.array(weights)
        weights_array = weights_array / weights_array.sum()  # Normalize

        selected_action = np.random.choice(actions, p=weights_array)
        return selected_action

    async def _generate_action_parameters(
        self, action_type: str, policy: EducationalPolicy, state: EnvironmentState, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate specific parameters for the selected action"""

        parameters = {}

        if action_type == "provide_hint":
            parameters.update(
                {
                    "hint_level": min(3, max(1, 3 - int(analysis.get("engagement_level", 0.5) * 3))),
                    "context_specific": True,
                    "encourage_thinking": True,
                }
            )

        elif action_type == "increase_difficulty":
            current_difficulty = analysis.get("difficulty_preference", 0.5)
            increase = min(policy.max_difficulty_increase, policy.difficulty_adjustment_rate * 2)
            parameters.update(
                {
                    "new_difficulty": min(1.0, current_difficulty + increase),
                    "gradual_increase": True,
                    "provide_support": True,
                }
            )

        elif action_type == "encourage_exploration":
            parameters.update(
                {
                    "exploration_areas": self._suggest_exploration_areas(state, analysis),
                    "time_limit": 600,  # 10 minutes
                    "guidance_level": "minimal" if analysis.get("engagement_level", 0) > 0.6 else "moderate",
                }
            )

        elif action_type == "create_quiz":
            parameters.update(
                {
                    "num_questions": min(10, max(3, int(analysis.get("engagement_level", 0.5) * 8) + 3)),
                    "difficulty": analysis.get("difficulty_preference", 0.5),
                    "subject_area": state.subject_area or "general",
                    "question_types": ["multiple_choice", "true_false", "short_answer"],
                }
            )

        elif action_type == "generate_content":
            parameters.update(
                {
                    "content_type": self._determine_content_type(state, analysis),
                    "subject_area": state.subject_area or "general",
                    "grade_level": state.grade_level or 5,
                    "interactive_elements": True,
                    "estimated_time": 300,  # 5 minutes
                }
            )

        elif action_type == "adapt_difficulty":
            current_perf = np.mean(analysis.get("recent_performance", [0.5]))
            target_success_rate = policy.success_threshold

            if current_perf > target_success_rate + 0.1:
                adjustment = policy.difficulty_adjustment_rate
            elif current_perf < target_success_rate - 0.1:
                adjustment = -policy.difficulty_adjustment_rate
            else:
                adjustment = 0

            parameters.update(
                {
                    "difficulty_adjustment": adjustment,
                    "current_performance": current_perf,
                    "target_success_rate": target_success_rate,
                }
            )

        elif action_type == "provide_feedback":
            parameters.update(
                {
                    "feedback_type": "constructive",
                    "include_encouragement": True,
                    "specific_areas": analysis.get("weaknesses", []),
                    "celebrate_strengths": analysis.get("strengths", []),
                }
            )

        # Add common parameters
        parameters.update(
            {"student_id": state.student_id, "timestamp": datetime.now().isoformat(), "policy_id": policy.policy_id}
        )

        return parameters

    def _suggest_exploration_areas(self, state: EnvironmentState, analysis: Dict[str, Any]) -> List[str]:
        """Suggest areas for student exploration"""

        areas = []

        # Subject-specific areas
        subject = state.subject_area
        if subject:
            subject_areas = {
                "math": ["geometry", "algebra", "statistics", "problem_solving"],
                "science": ["experiments", "observations", "hypothesis_testing", "research"],
                "history": ["primary_sources", "timelines", "cultural_connections"],
                "art": ["different_mediums", "styles", "techniques", "expression"],
            }
            areas.extend(subject_areas.get(subject.lower(), ["creative_activities"]))

        # Roblox-specific areas
        if state.state_type == StateType.ROBLOX_GAME:
            areas.extend(["building_mechanics", "scripting_basics", "collaborative_projects", "game_design_principles"])

        # Based on weaknesses
        weaknesses = analysis.get("weaknesses", [])
        for weakness in weaknesses:
            areas.append(f"practice_{weakness}")

        return areas[:5]  # Limit to 5 areas

    def _determine_content_type(self, state: EnvironmentState, analysis: Dict[str, Any]) -> str:
        """Determine appropriate content type to generate"""

        engagement = analysis.get("engagement_level", 0.5)
        learning_style = analysis.get("learning_style", "unknown")

        if state.state_type == StateType.ROBLOX_GAME:
            if engagement > 0.7:
                return "interactive_challenge"
            else:
                return "guided_tutorial"

        elif learning_style == "visual":
            return "visual_demonstration"
        elif learning_style == "kinesthetic":
            return "hands_on_activity"
        elif learning_style == "auditory":
            return "narrated_lesson"
        else:
            return "mixed_media_lesson"

    async def _calculate_priority(self, action_type: str, state: EnvironmentState, analysis: Dict[str, Any]) -> float:
        """Calculate action priority (0-1)"""

        base_priorities = {
            "provide_hint": 0.7,
            "increase_difficulty": 0.6,
            "encourage_exploration": 0.5,
            "create_quiz": 0.6,
            "generate_content": 0.5,
            "adapt_difficulty": 0.8,
            "provide_feedback": 0.7,
            "facilitate_collaboration": 0.4,
        }

        priority = base_priorities.get(action_type, 0.5)

        # Adjust based on student needs
        engagement = analysis.get("engagement_level", 0.5)
        recent_perf = analysis.get("recent_performance", [])

        if engagement < 0.3:  # Very low engagement - high priority intervention
            if action_type in ["encourage_exploration", "provide_hint"]:
                priority += 0.2

        if recent_perf and np.mean(recent_perf) < 0.4:  # Poor performance
            if action_type in ["provide_hint", "adapt_difficulty"]:
                priority += 0.2

        # State quality affects priority
        if state.quality.value in ["poor", "fair"]:
            priority *= 0.8  # Lower priority if state data is questionable

        return min(1.0, priority)

    async def _calculate_urgency(self, action_type: str, state: EnvironmentState, analysis: Dict[str, Any]) -> float:
        """Calculate action urgency (0-1)"""

        urgency = 0.5  # Default urgency

        # Time-sensitive actions
        if state.state_type == StateType.QUIZ_SESSION:
            quiz_data = state.data.get("quiz_data", {})
            if quiz_data.get("time_remaining", float("inf")) < 300:  # Less than 5 minutes
                urgency = 0.9

        # Low engagement is urgent
        engagement = analysis.get("engagement_level", 0.5)
        if engagement < 0.3:
            urgency = max(urgency, 0.8)

        # Poor recent performance needs urgent attention
        recent_perf = analysis.get("recent_performance", [])
        if recent_perf and np.mean(recent_perf) < 0.3:
            urgency = max(urgency, 0.7)

        # Declining learning trend is moderately urgent
        trend = analysis.get("learning_trend", 0)
        if trend < -0.2:
            urgency = max(urgency, 0.6)

        return min(1.0, urgency)

    async def _estimate_action_duration(self, action_type: str, parameters: Dict[str, Any]) -> float:
        """Estimate action duration in seconds"""

        base_durations = {
            "provide_hint": 10,
            "increase_difficulty": 5,
            "encourage_exploration": 300,
            "create_quiz": 180,
            "generate_content": 120,
            "adapt_difficulty": 15,
            "provide_feedback": 30,
            "facilitate_collaboration": 600,
        }

        duration = base_durations.get(action_type, 60)

        # Adjust based on parameters
        if action_type == "create_quiz":
            num_questions = parameters.get("num_questions", 5)
            duration = num_questions * 20  # 20 seconds per question

        elif action_type == "generate_content":
            content_type = parameters.get("content_type", "basic")
            if content_type == "interactive_challenge":
                duration = 300
            elif content_type == "visual_demonstration":
                duration = 180

        return float(duration)

    async def _generate_rationale(
        self, action_type: str, policy: EducationalPolicy, analysis: Dict[str, Any], state: EnvironmentState
    ) -> str:
        """Generate human-readable rationale for the decision"""

        engagement = analysis.get("engagement_level", 0.5)
        performance = analysis.get("recent_performance", [])
        avg_performance = np.mean(performance) if performance else 0.5

        rationales = {
            "provide_hint": f"Student shows {engagement:.1%} engagement with {avg_performance:.1%} performance. Hint will provide scaffolding support.",
            "increase_difficulty": f"High performance ({avg_performance:.1%}) indicates readiness for increased challenge level.",
            "encourage_exploration": f"Low engagement ({engagement:.1%}) suggests need for exploratory learning to rekindle interest.",
            "create_quiz": f"Assessment needed to gauge understanding in {state.subject_area or 'current topic'}.",
            "generate_content": f"New content will provide {policy.name} approach suitable for current learning context.",
            "adapt_difficulty": f"Performance trend indicates need for difficulty adjustment to maintain optimal challenge.",
            "provide_feedback": f"Constructive feedback will help address learning gaps and celebrate progress.",
            "facilitate_collaboration": f"Collaborative learning aligns with policy objectives and student social learning needs.",
        }

        return rationales.get(
            action_type, f"Action selected based on {policy.name} policy for optimal learning outcomes."
        )

    async def _predict_outcomes(
        self, action_type: str, parameters: Dict[str, Any], analysis: Dict[str, Any]
    ) -> List[str]:
        """Predict likely outcomes of the action"""

        outcomes = []

        if action_type == "provide_hint":
            outcomes.extend(
                [
                    "Increased problem-solving success",
                    "Maintained student confidence",
                    "Continued engagement with material",
                ]
            )

        elif action_type == "increase_difficulty":
            outcomes.extend(
                [
                    "Enhanced critical thinking skills",
                    "Possible temporary performance dip",
                    "Long-term skill development",
                ]
            )

        elif action_type == "encourage_exploration":
            outcomes.extend(
                [
                    "Increased engagement and curiosity",
                    "Discovery of new interests",
                    "Improved creative problem-solving",
                ]
            )

        elif action_type == "create_quiz":
            outcomes.extend(
                [
                    "Assessment of current understanding",
                    "Identification of knowledge gaps",
                    "Reinforcement of key concepts",
                ]
            )

        # Add confidence-based outcomes
        if analysis.get("engagement_level", 0.5) > 0.7:
            outcomes.append("High likelihood of positive response")
        elif analysis.get("engagement_level", 0.5) < 0.4:
            outcomes.append("May require additional motivation")

        return outcomes

    async def _plan_next_actions(
        self, current_action: str, policy: EducationalPolicy, analysis: Dict[str, Any]
    ) -> List[str]:
        """Plan logical next actions based on current action"""

        next_actions = []

        action_sequences = {
            "provide_hint": ["assess_understanding", "provide_feedback"],
            "increase_difficulty": ["monitor_performance", "provide_support_if_needed"],
            "encourage_exploration": ["track_discoveries", "reinforce_learning"],
            "create_quiz": ["analyze_results", "adapt_teaching_approach"],
            "generate_content": ["monitor_engagement", "assess_comprehension"],
            "adapt_difficulty": ["monitor_new_performance", "fine_tune_if_needed"],
            "provide_feedback": ["encourage_reflection", "plan_next_steps"],
        }

        next_actions = action_sequences.get(current_action, ["monitor_progress"])

        # Add policy-specific next actions
        if policy.challenge_weight > 0.5:
            next_actions.append("prepare_advanced_challenges")
        if policy.collaboration_weight > 0.5:
            next_actions.append("facilitate_peer_interaction")

        return next_actions

    def _select_primary_objective(
        self, policy: EducationalPolicy, state: EnvironmentState
    ) -> Optional[LearningObjective]:
        """Select primary learning objective for this decision"""

        # Get objectives from policy and state
        policy_objectives = policy.learning_objectives
        state_objectives = self._infer_learning_objectives(state)

        # Find overlap
        common_objectives = set(policy_objectives) & set(state_objectives)

        if common_objectives:
            # Prioritize based on current needs
            if LearningObjective.PROBLEM_SOLVING in common_objectives:
                return LearningObjective.PROBLEM_SOLVING
            else:
                return list(common_objectives)[0]

        # Fallback to policy primary objective
        if policy_objectives:
            return policy_objectives[0]

        return LearningObjective.KNOWLEDGE_ACQUISITION  # Default

    def _identify_target_skills(self, state: EnvironmentState, analysis: Dict[str, Any]) -> List[str]:
        """Identify skills to target with this action"""

        skills = []

        # Subject-specific skills
        subject = state.subject_area
        if subject:
            subject_skills = {
                "math": ["numerical_reasoning", "logical_thinking", "pattern_recognition"],
                "science": ["observation", "hypothesis_formation", "data_analysis"],
                "language": ["reading_comprehension", "written_expression", "vocabulary"],
                "history": ["chronological_thinking", "source_analysis", "contextual_understanding"],
            }
            skills.extend(subject_skills.get(subject.lower(), ["general_reasoning"]))

        # Address weaknesses
        weaknesses = analysis.get("weaknesses", [])
        skills.extend(weaknesses[:2])  # Focus on top 2 weaknesses

        # State-type specific skills
        if state.state_type == StateType.ROBLOX_GAME:
            skills.extend(["spatial_reasoning", "creative_problem_solving", "digital_literacy"])

        return skills[:5]  # Limit to 5 skills

    def _calculate_difficulty_level(
        self, policy: EducationalPolicy, analysis: Dict[str, Any], state: EnvironmentState
    ) -> float:
        """Calculate appropriate difficulty level for the action"""

        base_difficulty = analysis.get("difficulty_preference", 0.5)
        performance = analysis.get("recent_performance", [])

        if performance:
            avg_performance = np.mean(performance)
            # Adjust difficulty based on performance
            if avg_performance > 0.8:
                base_difficulty = min(1.0, base_difficulty + 0.1)
            elif avg_performance < 0.6:
                base_difficulty = max(0.2, base_difficulty - 0.1)

        # Policy adjustments
        if policy.challenge_weight > 0.5:
            base_difficulty += 0.1
        if policy.scaffolding_weight > 0.5:
            base_difficulty -= 0.1

        return max(0.1, min(1.0, base_difficulty))

    async def _calculate_decision_confidence(
        self, policy: EducationalPolicy, action_type: str, analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence in the policy decision"""

        confidence_factors = []

        # Policy success rate
        confidence_factors.append(policy.success_rate)

        # Data quality
        engagement_conf = 1.0 if "engagement_level" in analysis else 0.5
        performance_conf = 1.0 if "recent_performance" in analysis else 0.5
        confidence_factors.extend([engagement_conf, performance_conf])

        # Historical success of this action type
        if action_type in self.policy_performance:
            action_success = self.policy_performance[action_type].get("success_rate", 0.5)
            confidence_factors.append(action_success)

        # Student model completeness
        if analysis.get("learning_style") != "unknown":
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.4)

        return np.mean(confidence_factors)

    def _map_action_to_policy_type(self, action_type: str) -> PolicyType:
        """Map action type to policy type enum"""

        mapping = {
            "provide_hint": PolicyType.SCAFFOLDING,
            "increase_difficulty": PolicyType.CHALLENGE,
            "encourage_exploration": PolicyType.EXPLORATION,
            "reinforce_learning": PolicyType.EXPLOITATION,
            "create_quiz": PolicyType.ASSESSMENT,
            "generate_content": PolicyType.EXPLORATION,
            "facilitate_collaboration": PolicyType.COLLABORATION,
            "provide_feedback": PolicyType.ASSESSMENT,
            "adapt_difficulty": PolicyType.ADAPTATION,
        }

        return mapping.get(action_type, PolicyType.ADAPTATION)

    async def _generate_safe_default_decision(self, policy_input: Dict[str, Any]) -> PolicyDecision:
        """Generate a safe default decision when normal processing fails"""

        return PolicyDecision(
            policy_type=PolicyType.SCAFFOLDING,
            action_type="provide_support",
            parameters={"support_type": "general", "safety_fallback": True},
            priority=0.7,
            urgency=0.5,
            rationale="Safe default action due to decision processing error",
            confidence=0.3,
            expected_outcomes=["Maintain learning continuity", "Provide basic support"],
        )

    async def _update_q_learning(self, state: EnvironmentState, decision: PolicyDecision):
        """Update Q-learning table with state-action pair"""

        # Create state signature
        state_sig = f"{state.state_type.value}_{state.quality.value}_{state.subject_area or 'none'}"
        action_sig = decision.action_type

        # Initialize if not exists
        if state_sig not in self.q_table:
            self.q_table[state_sig] = defaultdict(float)

        # Update action count
        self.state_action_counts[state_sig][action_sig] += 1

        # The reward will be updated later when we get feedback
        logger.debug(f"Updated Q-table entry: {state_sig} -> {action_sig}")

    async def update_policy(
        self, state: EnvironmentState, action: Any, reward: float, next_state: Optional[EnvironmentState] = None
    ):
        """Update policy based on action results and rewards"""

        try:
            # Update Q-learning
            state_sig = f"{state.state_type.value}_{state.quality.value}_{state.subject_area or 'none'}"
            action_sig = getattr(action, "action_type", str(action))

            if next_state:
                next_state_sig = (
                    f"{next_state.state_type.value}_{next_state.quality.value}_{next_state.subject_area or 'none'}"
                )
                max_next_q = max(self.q_table[next_state_sig].values()) if self.q_table[next_state_sig] else 0
            else:
                max_next_q = 0

            # Q-learning update
            current_q = self.q_table[state_sig][action_sig]
            updated_q = current_q + self.learning_rate * (reward + self.decay_factor * max_next_q - current_q)
            self.q_table[state_sig][action_sig] = updated_q

            # Update policy performance tracking
            if action_sig not in self.policy_performance:
                self.policy_performance[action_sig] = {
                    "total_applications": 0,
                    "success_count": 0,
                    "success_rate": 0.0,
                    "average_reward": 0.0,
                    "reward_history": deque(maxlen=50),
                }

            perf = self.policy_performance[action_sig]
            perf["total_applications"] += 1
            perf["reward_history"].append(reward)
            perf["average_reward"] = np.mean(perf["reward_history"])

            if reward > 0.5:  # Consider reward > 0.5 as success
                perf["success_count"] += 1

            perf["success_rate"] = perf["success_count"] / perf["total_applications"]

            # Update reward history
            self.reward_history.append(reward)

            # Update student model if student_id available
            if state.student_id:
                await self._update_student_model(state.student_id, state, action, reward)

            # Adapt policies if needed
            if self.decision_count % self.update_frequency == 0:
                await self._adapt_policies()

            logger.debug(f"Policy updated: action={action_sig}, reward={reward:.3f}, q_value={updated_q:.3f}")

        except Exception as e:
            logger.error(f"Failed to update policy: {e}")

    async def _update_student_model(self, student_id: str, state: EnvironmentState, action: Any, reward: float):
        """Update individual student model"""

        if student_id not in self.student_models:
            self.student_models[student_id] = {
                "learning_style": "unknown",
                "strengths": [],
                "weaknesses": [],
                "preferred_difficulty": 0.5,
                "engagement_history": deque(maxlen=20),
                "performance_history": deque(maxlen=20),
                "last_updated": datetime.now(),
            }

        model = self.student_models[student_id]

        # Update learning curve
        self.learning_curves[student_id].append(reward)

        # Update performance history
        model["performance_history"].append(reward)

        # Estimate engagement from reward
        estimated_engagement = min(1.0, max(0.0, reward * 1.5))  # Scale reward to engagement
        model["engagement_history"].append(estimated_engagement)

        # Update preferred difficulty based on performance
        if len(model["performance_history"]) >= 5:
            recent_perf = list(model["performance_history"])[-5:]
            avg_perf = np.mean(recent_perf)

            if avg_perf > 0.8:
                model["preferred_difficulty"] = min(1.0, model["preferred_difficulty"] + 0.05)
            elif avg_perf < 0.6:
                model["preferred_difficulty"] = max(0.2, model["preferred_difficulty"] - 0.05)

        # Infer learning style from action preferences
        action_type = getattr(action, "action_type", str(action))
        if reward > 0.7:  # Good response to this action type
            if action_type in ["generate_content", "encourage_exploration"]:
                if model["learning_style"] == "unknown":
                    model["learning_style"] = "visual"
            elif action_type in ["create_quiz", "provide_feedback"]:
                if model["learning_style"] == "unknown":
                    model["learning_style"] = "analytical"

        model["last_updated"] = datetime.now()

    async def _adapt_policies(self):
        """Adapt policies based on performance data"""

        adaptations = []

        for policy_id, policy in self.policies.items():
            # Check if policy needs adaptation
            if policy.success_rate < 0.6 and policy.total_applications > 10:
                # Policy is underperforming
                old_weights = (
                    policy.exploration_weight,
                    policy.exploitation_weight,
                    policy.scaffolding_weight,
                    policy.challenge_weight,
                )

                # Adjust weights based on what's working
                best_actions = sorted(
                    self.policy_performance.items(), key=lambda x: x[1]["success_rate"], reverse=True
                )[:3]

                for action_type, perf in best_actions:
                    if self._map_action_to_policy_type(action_type) == PolicyType.EXPLORATION:
                        policy.exploration_weight = min(1.0, policy.exploration_weight + 0.1)
                    elif self._map_action_to_policy_type(action_type) == PolicyType.CHALLENGE:
                        policy.challenge_weight = min(1.0, policy.challenge_weight + 0.1)
                    elif self._map_action_to_policy_type(action_type) == PolicyType.SCAFFOLDING:
                        policy.scaffolding_weight = min(1.0, policy.scaffolding_weight + 0.1)

                # Normalize weights
                total_weight = (
                    policy.exploration_weight
                    + policy.exploitation_weight
                    + policy.scaffolding_weight
                    + policy.challenge_weight
                )
                if total_weight > 1:
                    policy.exploration_weight /= total_weight
                    policy.exploitation_weight /= total_weight
                    policy.scaffolding_weight /= total_weight
                    policy.challenge_weight /= total_weight

                new_weights = (
                    policy.exploration_weight,
                    policy.exploitation_weight,
                    policy.scaffolding_weight,
                    policy.challenge_weight,
                )

                adaptations.append(
                    {
                        "policy_id": policy_id,
                        "old_weights": old_weights,
                        "new_weights": new_weights,
                        "reason": f"Low success rate: {policy.success_rate:.3f}",
                    }
                )

        if adaptations:
            self.adaptation_log.extend(adaptations)
            logger.info(f"Adapted {len(adaptations)} policies based on performance")

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of PolicyEngine"""

        return {
            "decision_count": self.decision_count,
            "policies": {
                "total_policies": len(self.policies),
                "policy_performance": {
                    pid: {"success_rate": p.success_rate, "applications": p.total_applications}
                    for pid, p in self.policies.items()
                },
            },
            "learning": {
                "q_table_size": len(self.q_table),
                "state_action_pairs": sum(len(actions) for actions in self.q_table.values()),
                "average_reward": np.mean(self.reward_history) if self.reward_history else 0,
                "exploration_rate": self.exploration_rate,
            },
            "student_models": {
                "total_students": len(self.student_models),
                "avg_learning_curve_length": (
                    np.mean([len(curve) for curve in self.learning_curves.values()]) if self.learning_curves else 0
                ),
            },
            "adaptations": len(self.adaptation_log),
            "performance_tracking": {
                "tracked_actions": len(self.policy_performance),
                "best_performing_action": (
                    max(self.policy_performance.items(), key=lambda x: x[1]["success_rate"])[0]
                    if self.policy_performance
                    else None
                ),
            },
        }

    async def reset(self):
        """Reset PolicyEngine to initial state"""

        logger.info("Resetting PolicyEngine")

        # Reset learning data
        self.q_table.clear()
        self.state_action_counts.clear()
        self.reward_history.clear()

        # Reset student models
        self.student_models.clear()
        self.learning_curves.clear()

        # Reset performance tracking
        self.policy_performance.clear()
        self.adaptation_log.clear()
        self.decision_count = 0

        # Reset decision history
        self.decision_history.clear()
        self.policy_history.clear()

        # Reinitialize policies
        self._initialize_default_policies()

        logger.info("PolicyEngine reset completed")
