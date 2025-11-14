"""
Adaptive Learning Engine

Intelligent system for personalizing educational content based on individual learner
patterns, performance metrics, and engagement data. Uses advanced algorithms to
dynamically adjust difficulty, pacing, and content presentation.

Author: ToolboxAI Team
Created: 2025-09-19
Version: 2.0.0
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.agents.base_agent import AgentConfig, BaseAgent
from database.content_pipeline_models import ContentFeedback, EnhancedContentGeneration

logger = logging.getLogger(__name__)


class LearningStyle(Enum):
    """Primary learning style categories"""

    VISUAL = "visual"  # Learns through images, diagrams, videos
    AUDITORY = "auditory"  # Learns through listening and discussion
    KINESTHETIC = "kinesthetic"  # Learns through hands-on activities
    READING_WRITING = "reading_writing"  # Learns through text


class DifficultyLevel(Enum):
    """Content difficulty levels"""

    BEGINNER = 1
    ELEMENTARY = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5


class AdaptationType(Enum):
    """Types of content adaptations"""

    DIFFICULTY = "difficulty"
    PACE = "pace"
    STYLE = "style"
    SCAFFOLDING = "scaffolding"
    FEEDBACK = "feedback"
    ASSESSMENT = "assessment"


@dataclass
class LearnerMetrics:
    """Comprehensive metrics for a learner"""

    user_id: str

    # Performance metrics
    accuracy_rate: float = 0.0
    completion_rate: float = 0.0
    time_on_task: float = 0.0
    error_rate: float = 0.0
    help_requests: int = 0

    # Engagement metrics
    interaction_frequency: float = 0.0
    session_duration: float = 0.0
    return_rate: float = 0.0
    focus_score: float = 0.0

    # Progress metrics
    mastery_level: float = 0.0
    learning_velocity: float = 0.0
    knowledge_retention: float = 0.0
    skill_progression: dict[str, float] = field(default_factory=dict)

    # Pattern analysis
    peak_performance_time: Optional[int] = None  # Hour of day
    preferred_session_length: float = 30.0  # Minutes
    optimal_difficulty: float = 0.5  # 0-1 scale

    # Historical data
    performance_history: deque = field(default_factory=lambda: deque(maxlen=100))
    engagement_history: deque = field(default_factory=lambda: deque(maxlen=100))

    # Timestamps
    last_updated: datetime = field(default_factory=datetime.now)
    metrics_window: timedelta = field(default=timedelta(days=30))


@dataclass
class AdaptationRecommendation:
    """Recommendation for content adaptation"""

    adaptation_type: AdaptationType
    current_value: Any
    recommended_value: Any
    confidence: float
    rationale: str
    impact_prediction: float  # Predicted improvement
    priority: int  # 1-5, 1 being highest


@dataclass
class PersonalizationStrategy:
    """Complete personalization strategy for a learner"""

    user_id: str
    learning_style: LearningStyle
    current_difficulty: DifficultyLevel
    recommended_difficulty: DifficultyLevel

    # Pacing adjustments
    content_pace: float  # Multiplier for content delivery speed
    assessment_frequency: int  # Assessments per module
    break_frequency: int  # Minutes between breaks

    # Content preferences
    media_preferences: dict[str, float]  # media_type -> preference_score
    interaction_types: list[str]  # Preferred interaction methods
    feedback_style: str  # immediate, delayed, summary

    # Scaffolding
    hint_level: int  # 0-3, 0 being no hints
    example_frequency: float  # Examples per concept
    practice_problems: int  # Number of practice problems

    # Gamification
    achievement_sensitivity: float  # Response to achievements
    competition_preference: float  # Solo vs competitive
    narrative_engagement: float  # Story-driven content preference

    # Recommendations
    recommendations: list[AdaptationRecommendation] = field(default_factory=list)

    # Metadata
    strategy_version: str = "2.0"
    created_at: datetime = field(default_factory=datetime.now)
    confidence_score: float = 0.0


class AdaptiveLearningEngine(BaseAgent):
    """
    Advanced adaptive learning engine that personalizes educational content
    based on individual learner characteristics and performance patterns.

    Key Features:
    - Real-time performance analysis
    - Learning style detection
    - Dynamic difficulty adjustment
    - Personalized pacing
    - Predictive modeling for intervention
    - Multi-dimensional optimization
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """Initialize the adaptive learning engine"""

        config = AgentConfig(
            name="AdaptiveLearningEngine",
            model="gpt-4-turbo-preview",
            temperature=0.3,  # Lower temperature for consistent adaptations
            max_retries=3,
            timeout=300,
            verbose=True,
            system_prompt=self._get_engine_system_prompt(),
        )

        super().__init__(config)

        self.db_session = db_session

        # Learning models
        self.style_classifier = self._initialize_style_classifier()
        self.difficulty_optimizer = self._initialize_difficulty_optimizer()
        self.engagement_predictor = self._initialize_engagement_predictor()

        # Performance thresholds
        self.thresholds = {
            "mastery": 0.85,
            "struggling": 0.60,
            "frustration": 0.40,
            "boredom": 0.95,
            "optimal_challenge": (0.70, 0.85),
        }

        # Adaptation parameters
        self.adaptation_params = {
            "difficulty_step": 0.1,  # Adjustment step size
            "pace_adjustment": 0.15,  # Pacing change rate
            "style_weight": 0.3,  # Weight for style matching
            "history_weight": 0.7,  # Weight for historical performance
            "min_data_points": 5,  # Minimum data for adaptation
            "adaptation_cooldown": 300,  # Seconds between major adaptations
        }

        # Cache for learner profiles
        self.profile_cache: dict[str, LearnerMetrics] = {}
        self.strategy_cache: dict[str, PersonalizationStrategy] = {}

        logger.info("Adaptive Learning Engine initialized")

    def _get_engine_system_prompt(self) -> str:
        """Get the system prompt for the adaptive engine"""
        return """You are an Advanced Adaptive Learning Engine specializing in personalized education.

Your responsibilities include:

1. **Performance Analysis**:
   - Track learning progress and identify patterns
   - Detect struggling points and mastery areas
   - Predict future performance trends
   - Identify optimal learning conditions

2. **Learning Style Recognition**:
   - Classify learner preferences (visual, auditory, kinesthetic, reading/writing)
   - Adapt content presentation to match style
   - Balance style preferences with content requirements
   - Track style effectiveness over time

3. **Difficulty Optimization**:
   - Maintain optimal challenge level (Zone of Proximal Development)
   - Prevent frustration and boredom
   - Gradually increase complexity as mastery improves
   - Provide appropriate scaffolding

4. **Pacing Personalization**:
   - Adjust content delivery speed
   - Optimize session length and breaks
   - Adapt to attention patterns
   - Respond to engagement signals

5. **Intervention Strategies**:
   - Predict when learner needs help
   - Provide timely support and hints
   - Suggest alternative learning paths
   - Recommend remediation when needed

Always prioritize learner success and engagement. Use data-driven decisions while maintaining pedagogical best practices.
"""

    def _initialize_style_classifier(self) -> Any:
        """Initialize the learning style classifier"""
        # Simplified - in production would use trained model
        return {
            "visual_indicators": ["diagram", "chart", "image", "video", "animation"],
            "auditory_indicators": ["audio", "discussion", "podcast", "narration"],
            "kinesthetic_indicators": [
                "interactive",
                "hands-on",
                "simulation",
                "practice",
            ],
            "reading_indicators": ["text", "article", "notes", "documentation"],
        }

    def _initialize_difficulty_optimizer(self) -> Any:
        """Initialize the difficulty optimization system"""
        return {
            "performance_bands": {
                DifficultyLevel.BEGINNER: (0.85, 1.00),
                DifficultyLevel.ELEMENTARY: (0.75, 0.90),
                DifficultyLevel.INTERMEDIATE: (0.65, 0.80),
                DifficultyLevel.ADVANCED: (0.55, 0.70),
                DifficultyLevel.EXPERT: (0.45, 0.60),
            }
        }

    def _initialize_engagement_predictor(self) -> Any:
        """Initialize the engagement prediction model"""
        # Simplified - would use ML model in production
        return {
            "engagement_factors": {
                "interaction_rate": 0.3,
                "completion_rate": 0.25,
                "return_rate": 0.2,
                "session_duration": 0.15,
                "voluntary_practice": 0.1,
            }
        }

    async def analyze_learner(self, user_id: str) -> LearnerMetrics:
        """
        Analyze comprehensive learner metrics

        Args:
            user_id: User identifier

        Returns:
            Comprehensive learner metrics
        """
        # Check cache
        if user_id in self.profile_cache:
            cached = self.profile_cache[user_id]
            if (datetime.now() - cached.last_updated).seconds < 300:
                return cached

        metrics = LearnerMetrics(user_id=user_id)

        if self.db_session:
            # Load historical data
            performance_data = await self._load_performance_history(user_id)
            engagement_data = await self._load_engagement_history(user_id)

            # Calculate performance metrics
            metrics.accuracy_rate = self._calculate_accuracy(performance_data)
            metrics.completion_rate = self._calculate_completion_rate(performance_data)
            metrics.error_rate = self._calculate_error_rate(performance_data)

            # Calculate engagement metrics
            metrics.interaction_frequency = self._calculate_interaction_frequency(engagement_data)
            metrics.session_duration = self._calculate_average_session_duration(engagement_data)
            metrics.return_rate = self._calculate_return_rate(engagement_data)

            # Calculate progress metrics
            metrics.mastery_level = self._calculate_mastery_level(performance_data)
            metrics.learning_velocity = self._calculate_learning_velocity(performance_data)
            metrics.knowledge_retention = self._calculate_retention(performance_data)

            # Identify patterns
            metrics.peak_performance_time = self._identify_peak_time(performance_data)
            metrics.preferred_session_length = self._identify_preferred_session_length(
                engagement_data
            )
            metrics.optimal_difficulty = self._identify_optimal_difficulty(performance_data)

        # Cache the metrics
        self.profile_cache[user_id] = metrics

        return metrics

    async def detect_learning_style(self, user_id: str) -> LearningStyle:
        """
        Detect the primary learning style of a user

        Args:
            user_id: User identifier

        Returns:
            Primary learning style
        """
        if self.db_session:
            # Analyze interaction patterns
            interactions = await self._load_interaction_history(user_id)

            style_scores = {
                LearningStyle.VISUAL: 0,
                LearningStyle.AUDITORY: 0,
                LearningStyle.KINESTHETIC: 0,
                LearningStyle.READING_WRITING: 0,
            }

            # Score based on content preferences and performance
            for interaction in interactions:
                content_type = interaction.get("content_type", "")
                performance = interaction.get("performance", 0.5)

                if any(
                    indicator in content_type.lower()
                    for indicator in self.style_classifier["visual_indicators"]
                ):
                    style_scores[LearningStyle.VISUAL] += performance

                if any(
                    indicator in content_type.lower()
                    for indicator in self.style_classifier["auditory_indicators"]
                ):
                    style_scores[LearningStyle.AUDITORY] += performance

                if any(
                    indicator in content_type.lower()
                    for indicator in self.style_classifier["kinesthetic_indicators"]
                ):
                    style_scores[LearningStyle.KINESTHETIC] += performance

                if any(
                    indicator in content_type.lower()
                    for indicator in self.style_classifier["reading_indicators"]
                ):
                    style_scores[LearningStyle.READING_WRITING] += performance

            # Return highest scoring style
            if style_scores:
                return max(style_scores, key=style_scores.get)

        return LearningStyle.VISUAL  # Default

    async def optimize_difficulty(
        self,
        user_id: str,
        current_performance: float,
        current_difficulty: DifficultyLevel,
    ) -> tuple[DifficultyLevel, float]:
        """
        Optimize difficulty level based on performance

        Args:
            user_id: User identifier
            current_performance: Current performance score (0-1)
            current_difficulty: Current difficulty level

        Returns:
            Recommended difficulty level and confidence score
        """
        # Get performance bands
        bands = self.difficulty_optimizer["performance_bands"]

        # Check if current difficulty is appropriate
        min_perf, max_perf = bands[current_difficulty]

        confidence = 0.8

        if current_performance < min_perf:
            # Too difficult - decrease
            if current_difficulty.value > 1:
                new_difficulty = DifficultyLevel(current_difficulty.value - 1)
                confidence = min(0.9, (min_perf - current_performance) * 2)
            else:
                new_difficulty = current_difficulty
                confidence = 0.5

        elif current_performance > max_perf:
            # Too easy - increase
            if current_difficulty.value < 5:
                new_difficulty = DifficultyLevel(current_difficulty.value + 1)
                confidence = min(0.9, (current_performance - max_perf) * 2)
            else:
                new_difficulty = current_difficulty
                confidence = 0.5

        else:
            # Appropriate difficulty
            new_difficulty = current_difficulty
            confidence = 0.95

        return new_difficulty, confidence

    async def generate_personalization_strategy(
        self, user_id: str, content_type: str = "lesson"
    ) -> PersonalizationStrategy:
        """
        Generate comprehensive personalization strategy

        Args:
            user_id: User identifier
            content_type: Type of content being personalized

        Returns:
            Complete personalization strategy
        """
        # Check cache
        if user_id in self.strategy_cache:
            cached = self.strategy_cache[user_id]
            if (datetime.now() - cached.created_at).seconds < 600:
                return cached

        # Analyze learner
        metrics = await self.analyze_learner(user_id)
        learning_style = await self.detect_learning_style(user_id)

        # Determine difficulty
        current_difficulty = self._estimate_current_difficulty(metrics)
        recommended_difficulty, confidence = await self.optimize_difficulty(
            user_id, metrics.accuracy_rate, current_difficulty
        )

        # Create strategy
        strategy = PersonalizationStrategy(
            user_id=user_id,
            learning_style=learning_style,
            current_difficulty=current_difficulty,
            recommended_difficulty=recommended_difficulty,
            confidence_score=confidence,
        )

        # Set pacing parameters
        strategy.content_pace = self._calculate_pace_multiplier(metrics)
        strategy.assessment_frequency = self._calculate_assessment_frequency(metrics)
        strategy.break_frequency = self._calculate_break_frequency(metrics)

        # Set content preferences
        strategy.media_preferences = self._determine_media_preferences(learning_style)
        strategy.interaction_types = self._determine_interaction_types(learning_style, metrics)
        strategy.feedback_style = self._determine_feedback_style(metrics)

        # Set scaffolding
        strategy.hint_level = self._determine_hint_level(metrics)
        strategy.example_frequency = self._determine_example_frequency(metrics)
        strategy.practice_problems = self._determine_practice_count(metrics)

        # Set gamification
        strategy.achievement_sensitivity = (
            metrics.engagement_history[-1] if metrics.engagement_history else 0.5
        )
        strategy.competition_preference = self._estimate_competition_preference(metrics)
        strategy.narrative_engagement = self._estimate_narrative_preference(metrics)

        # Generate recommendations
        strategy.recommendations = await self._generate_recommendations(metrics, strategy)

        # Cache strategy
        self.strategy_cache[user_id] = strategy

        return strategy

    async def adapt_content(
        self, content: dict[str, Any], strategy: PersonalizationStrategy
    ) -> dict[str, Any]:
        """
        Adapt content based on personalization strategy

        Args:
            content: Original content
            strategy: Personalization strategy

        Returns:
            Adapted content
        """
        adapted_content = content.copy()

        # Apply difficulty adaptation
        adapted_content = self._adapt_difficulty(adapted_content, strategy.recommended_difficulty)

        # Apply style adaptation
        adapted_content = self._adapt_to_learning_style(adapted_content, strategy.learning_style)

        # Apply pacing adaptation
        adapted_content = self._adapt_pacing(adapted_content, strategy)

        # Apply scaffolding
        adapted_content = self._add_scaffolding(adapted_content, strategy)

        # Apply gamification
        adapted_content = self._add_gamification(adapted_content, strategy)

        # Add metadata
        adapted_content["personalization_metadata"] = {
            "strategy_version": strategy.strategy_version,
            "learning_style": strategy.learning_style.value,
            "difficulty_level": strategy.recommended_difficulty.value,
            "adaptations_applied": len(strategy.recommendations),
            "confidence_score": strategy.confidence_score,
            "adapted_at": datetime.now().isoformat(),
        }

        return adapted_content

    async def predict_performance(
        self, user_id: str, content_difficulty: DifficultyLevel
    ) -> dict[str, float]:
        """
        Predict learner performance on content

        Args:
            user_id: User identifier
            content_difficulty: Difficulty of content

        Returns:
            Performance predictions
        """
        metrics = await self.analyze_learner(user_id)

        # Simple prediction model (would use ML in production)
        difficulty_gap = content_difficulty.value - metrics.optimal_difficulty * 5

        base_performance = metrics.accuracy_rate
        difficulty_impact = -0.1 * abs(difficulty_gap)

        predicted_accuracy = max(0.2, min(1.0, base_performance + difficulty_impact))
        predicted_completion = max(0.3, min(1.0, metrics.completion_rate + difficulty_impact * 0.5))
        predicted_engagement = max(0.2, min(1.0, metrics.focus_score - abs(difficulty_gap) * 0.15))

        return {
            "predicted_accuracy": predicted_accuracy,
            "predicted_completion": predicted_completion,
            "predicted_engagement": predicted_engagement,
            "confidence": 0.75,  # Simplified confidence
            "risk_of_frustration": 1.0 if difficulty_gap > 2 else 0.0,
            "risk_of_boredom": 1.0 if difficulty_gap < -2 else 0.0,
        }

    async def recommend_intervention(
        self, user_id: str, current_performance: dict[str, float]
    ) -> Optional[dict[str, Any]]:
        """
        Recommend intervention if needed

        Args:
            user_id: User identifier
            current_performance: Current performance metrics

        Returns:
            Intervention recommendation if needed
        """
        accuracy = current_performance.get("accuracy", 1.0)
        engagement = current_performance.get("engagement", 1.0)

        if accuracy < self.thresholds["frustration"]:
            return {
                "type": "immediate",
                "reason": "frustration_detected",
                "actions": [
                    "Reduce difficulty",
                    "Provide additional hints",
                    "Offer tutorial review",
                    "Switch to guided practice",
                ],
                "urgency": "high",
            }

        elif accuracy > self.thresholds["boredom"]:
            return {
                "type": "adjustment",
                "reason": "insufficient_challenge",
                "actions": [
                    "Increase difficulty",
                    "Skip to advanced topics",
                    "Provide challenge problems",
                    "Reduce scaffolding",
                ],
                "urgency": "medium",
            }

        elif accuracy < self.thresholds["struggling"]:
            return {
                "type": "support",
                "reason": "struggling_detected",
                "actions": [
                    "Add more examples",
                    "Slow down pacing",
                    "Increase hint availability",
                    "Suggest peer collaboration",
                ],
                "urgency": "medium",
            }

        elif engagement < 0.4:
            return {
                "type": "engagement",
                "reason": "low_engagement",
                "actions": [
                    "Switch content format",
                    "Add interactive elements",
                    "Introduce gamification",
                    "Suggest break",
                ],
                "urgency": "low",
            }

        return None  # No intervention needed

    # Helper methods

    async def _load_performance_history(self, user_id: str) -> list[dict]:
        """Load performance history from database"""
        if not self.db_session:
            return []

        # Query recent content generations and feedback
        query = (
            select(ContentFeedback)
            .where(ContentFeedback.user_id == user_id)
            .order_by(ContentFeedback.created_at.desc())
            .limit(100)
        )

        result = await self.db_session.execute(query)
        feedback_records = result.scalars().all()

        return [
            {
                "timestamp": record.created_at,
                "accuracy": record.rating / 5.0 if record.rating else 0.5,
                "completion": record.completion_rate or 0.0,
                "duration": record.session_duration or 0.0,
            }
            for record in feedback_records
        ]

    async def _load_engagement_history(self, user_id: str) -> list[dict]:
        """Load engagement history from database"""
        # Simplified - would query actual engagement metrics
        return await self._load_performance_history(user_id)

    async def _load_interaction_history(self, user_id: str) -> list[dict]:
        """Load interaction history"""
        if not self.db_session:
            return []

        # Query content generation history
        query = (
            select(EnhancedContentGeneration)
            .where(EnhancedContentGeneration.user_id == user_id)
            .order_by(EnhancedContentGeneration.created_at.desc())
            .limit(50)
        )

        result = await self.db_session.execute(query)
        generations = result.scalars().all()

        return [
            {
                "content_type": gen.content_type,
                "quality_score": gen.quality_score or 0.5,
                "personalization_applied": gen.personalization_applied,
                "completion_time": gen.generation_time_seconds,
            }
            for gen in generations
        ]

    def _calculate_accuracy(self, performance_data: list[dict]) -> float:
        """Calculate average accuracy"""
        if not performance_data:
            return 0.5

        accuracies = [p.get("accuracy", 0.5) for p in performance_data]
        return sum(accuracies) / len(accuracies)

    def _calculate_completion_rate(self, performance_data: list[dict]) -> float:
        """Calculate completion rate"""
        if not performance_data:
            return 0.5

        completions = [p.get("completion", 0.0) for p in performance_data]
        return sum(completions) / len(completions)

    def _calculate_error_rate(self, performance_data: list[dict]) -> float:
        """Calculate error rate"""
        return 1.0 - self._calculate_accuracy(performance_data)

    def _calculate_interaction_frequency(self, engagement_data: list[dict]) -> float:
        """Calculate interaction frequency"""
        if len(engagement_data) < 2:
            return 0.5

        # Calculate average time between interactions
        timestamps = [e.get("timestamp") for e in engagement_data if e.get("timestamp")]
        if len(timestamps) < 2:
            return 0.5

        time_diffs = []
        for i in range(1, len(timestamps)):
            diff = (timestamps[i - 1] - timestamps[i]).total_seconds() / 3600  # Hours
            time_diffs.append(diff)

        avg_hours_between = sum(time_diffs) / len(time_diffs) if time_diffs else 24

        # Convert to frequency score (0-1, where 1 is very frequent)
        return max(0, min(1, 1 - (avg_hours_between / 168)))  # Normalize by week

    def _calculate_average_session_duration(self, engagement_data: list[dict]) -> float:
        """Calculate average session duration in minutes"""
        if not engagement_data:
            return 30.0

        durations = [e.get("duration", 30.0) for e in engagement_data if e.get("duration")]
        return sum(durations) / len(durations) if durations else 30.0

    def _calculate_return_rate(self, engagement_data: list[dict]) -> float:
        """Calculate return rate"""
        # Simplified - based on interaction frequency
        return self._calculate_interaction_frequency(engagement_data)

    def _calculate_mastery_level(self, performance_data: list[dict]) -> float:
        """Calculate overall mastery level"""
        accuracy = self._calculate_accuracy(performance_data)
        completion = self._calculate_completion_rate(performance_data)

        # Weighted average
        return accuracy * 0.7 + completion * 0.3

    def _calculate_learning_velocity(self, performance_data: list[dict]) -> float:
        """Calculate rate of improvement"""
        if len(performance_data) < 10:
            return 0.5

        # Compare recent vs older performance
        recent = performance_data[:5]
        older = performance_data[-5:]

        recent_accuracy = sum(p.get("accuracy", 0.5) for p in recent) / len(recent)
        older_accuracy = sum(p.get("accuracy", 0.5) for p in older) / len(older)

        # Calculate improvement rate
        improvement = recent_accuracy - older_accuracy

        # Normalize to 0-1 scale
        return max(0, min(1, 0.5 + improvement))

    def _calculate_retention(self, performance_data: list[dict]) -> float:
        """Calculate knowledge retention"""
        # Simplified - based on consistency of performance
        if not performance_data:
            return 0.5

        accuracies = [p.get("accuracy", 0.5) for p in performance_data]

        if len(accuracies) < 2:
            return accuracies[0] if accuracies else 0.5

        # Calculate variance (lower variance = better retention)
        mean_accuracy = sum(accuracies) / len(accuracies)
        variance = sum((a - mean_accuracy) ** 2 for a in accuracies) / len(accuracies)

        # Convert to retention score (lower variance = higher retention)
        return max(0, min(1, 1 - variance * 2))

    def _identify_peak_time(self, performance_data: list[dict]) -> Optional[int]:
        """Identify peak performance time of day"""
        if not performance_data:
            return None

        hour_performance = {}

        for p in performance_data:
            timestamp = p.get("timestamp")
            if timestamp:
                hour = timestamp.hour
                accuracy = p.get("accuracy", 0.5)

                if hour not in hour_performance:
                    hour_performance[hour] = []
                hour_performance[hour].append(accuracy)

        if not hour_performance:
            return None

        # Calculate average performance by hour
        hour_averages = {hour: sum(accs) / len(accs) for hour, accs in hour_performance.items()}

        # Return hour with best performance
        return max(hour_averages, key=hour_averages.get) if hour_averages else None

    def _identify_preferred_session_length(self, engagement_data: list[dict]) -> float:
        """Identify preferred session length in minutes"""
        durations = [e.get("duration", 30.0) for e in engagement_data if e.get("duration")]

        if not durations:
            return 30.0

        # Return median duration
        sorted_durations = sorted(durations)
        n = len(sorted_durations)

        if n % 2 == 0:
            return (sorted_durations[n // 2 - 1] + sorted_durations[n // 2]) / 2
        else:
            return sorted_durations[n // 2]

    def _identify_optimal_difficulty(self, performance_data: list[dict]) -> float:
        """Identify optimal difficulty level (0-1 scale)"""
        accuracy = self._calculate_accuracy(performance_data)

        # Optimal difficulty maintains 70-85% accuracy
        if accuracy < 0.7:
            return max(0.2, accuracy - 0.15)
        elif accuracy > 0.85:
            return min(0.9, accuracy + 0.1)
        else:
            return accuracy

    def _estimate_current_difficulty(self, metrics: LearnerMetrics) -> DifficultyLevel:
        """Estimate current difficulty level from metrics"""
        # Map optimal difficulty (0-1) to difficulty levels (1-5)
        difficulty_value = int(metrics.optimal_difficulty * 5)
        difficulty_value = max(1, min(5, difficulty_value))

        return DifficultyLevel(difficulty_value)

    def _calculate_pace_multiplier(self, metrics: LearnerMetrics) -> float:
        """Calculate content pace multiplier"""
        # Base pace on learning velocity and mastery
        base_pace = 1.0

        if metrics.learning_velocity > 0.7:
            base_pace *= 1.2  # Faster pace for quick learners
        elif metrics.learning_velocity < 0.3:
            base_pace *= 0.8  # Slower pace for struggling learners

        if metrics.mastery_level > 0.8:
            base_pace *= 1.1  # Speed up for high mastery
        elif metrics.mastery_level < 0.5:
            base_pace *= 0.9  # Slow down for low mastery

        return max(0.5, min(2.0, base_pace))

    def _calculate_assessment_frequency(self, metrics: LearnerMetrics) -> int:
        """Calculate assessments per module"""
        # More assessments for struggling learners
        if metrics.mastery_level < 0.5:
            return 3
        elif metrics.mastery_level < 0.7:
            return 2
        else:
            return 1

    def _calculate_break_frequency(self, metrics: LearnerMetrics) -> int:
        """Calculate minutes between breaks"""
        # Based on preferred session length and focus
        base_break = int(metrics.preferred_session_length)

        if metrics.focus_score < 0.5:
            base_break = int(base_break * 0.7)  # More frequent breaks

        return max(15, min(60, base_break))

    def _determine_media_preferences(self, learning_style: LearningStyle) -> dict[str, float]:
        """Determine media preferences based on learning style"""
        preferences = {
            "video": 0.5,
            "audio": 0.5,
            "text": 0.5,
            "interactive": 0.5,
            "diagram": 0.5,
        }

        if learning_style == LearningStyle.VISUAL:
            preferences["video"] = 0.9
            preferences["diagram"] = 0.9
            preferences["text"] = 0.3
        elif learning_style == LearningStyle.AUDITORY:
            preferences["audio"] = 0.9
            preferences["video"] = 0.7
            preferences["text"] = 0.3
        elif learning_style == LearningStyle.KINESTHETIC:
            preferences["interactive"] = 0.9
            preferences["video"] = 0.6
            preferences["text"] = 0.3
        elif learning_style == LearningStyle.READING_WRITING:
            preferences["text"] = 0.9
            preferences["diagram"] = 0.6
            preferences["video"] = 0.4

        return preferences

    def _determine_interaction_types(
        self, learning_style: LearningStyle, metrics: LearnerMetrics
    ) -> list[str]:
        """Determine preferred interaction types"""
        base_types = ["click", "drag", "type"]

        if learning_style == LearningStyle.KINESTHETIC:
            base_types.extend(["build", "manipulate", "simulate"])

        if metrics.engagement_history and metrics.engagement_history[-1] > 0.7:
            base_types.extend(["challenge", "compete"])

        return base_types

    def _determine_feedback_style(self, metrics: LearnerMetrics) -> str:
        """Determine feedback style preference"""
        if metrics.mastery_level < 0.5:
            return "immediate"  # Immediate feedback for struggling learners
        elif metrics.learning_velocity > 0.7:
            return "summary"  # Summary feedback for fast learners
        else:
            return "delayed"  # Delayed feedback for average pace

    def _determine_hint_level(self, metrics: LearnerMetrics) -> int:
        """Determine hint level (0-3)"""
        if metrics.mastery_level < 0.4:
            return 3  # Maximum hints
        elif metrics.mastery_level < 0.6:
            return 2  # Moderate hints
        elif metrics.mastery_level < 0.8:
            return 1  # Minimal hints
        else:
            return 0  # No hints

    def _determine_example_frequency(self, metrics: LearnerMetrics) -> float:
        """Determine examples per concept"""
        base_examples = 2.0

        if metrics.mastery_level < 0.5:
            base_examples *= 1.5  # More examples for struggling

        if metrics.learning_velocity < 0.3:
            base_examples *= 1.3  # More examples for slow learners

        return min(5.0, base_examples)

    def _determine_practice_count(self, metrics: LearnerMetrics) -> int:
        """Determine number of practice problems"""
        if metrics.mastery_level < 0.5:
            return 10  # Many practice problems
        elif metrics.mastery_level < 0.7:
            return 7  # Moderate practice
        elif metrics.mastery_level < 0.9:
            return 5  # Some practice
        else:
            return 3  # Minimal practice

    def _estimate_competition_preference(self, metrics: LearnerMetrics) -> float:
        """Estimate preference for competitive elements"""
        # Based on engagement patterns
        if metrics.engagement_history:
            avg_engagement = sum(metrics.engagement_history) / len(metrics.engagement_history)
            return min(1.0, avg_engagement * 1.2)
        return 0.5

    def _estimate_narrative_preference(self, metrics: LearnerMetrics) -> float:
        """Estimate preference for story-driven content"""
        # Higher for younger or less engaged learners
        engagement_factor = 1.0 - (metrics.focus_score if metrics.focus_score else 0.5)
        return min(1.0, 0.3 + engagement_factor * 0.7)

    async def _generate_recommendations(
        self, metrics: LearnerMetrics, strategy: PersonalizationStrategy
    ) -> list[AdaptationRecommendation]:
        """Generate specific adaptation recommendations"""
        recommendations = []

        # Difficulty recommendation
        if strategy.current_difficulty != strategy.recommended_difficulty:
            recommendations.append(
                AdaptationRecommendation(
                    adaptation_type=AdaptationType.DIFFICULTY,
                    current_value=strategy.current_difficulty.value,
                    recommended_value=strategy.recommended_difficulty.value,
                    confidence=strategy.confidence_score,
                    rationale="Performance indicates difficulty adjustment needed",
                    impact_prediction=0.15,
                    priority=1,
                )
            )

        # Pace recommendation
        if abs(strategy.content_pace - 1.0) > 0.1:
            recommendations.append(
                AdaptationRecommendation(
                    adaptation_type=AdaptationType.PACE,
                    current_value=1.0,
                    recommended_value=strategy.content_pace,
                    confidence=0.8,
                    rationale="Learning velocity suggests pace adjustment",
                    impact_prediction=0.1,
                    priority=2,
                )
            )

        # Scaffolding recommendation
        if strategy.hint_level > 1:
            recommendations.append(
                AdaptationRecommendation(
                    adaptation_type=AdaptationType.SCAFFOLDING,
                    current_value=0,
                    recommended_value=strategy.hint_level,
                    confidence=0.85,
                    rationale="Additional support needed for mastery",
                    impact_prediction=0.2,
                    priority=1,
                )
            )

        return recommendations

    def _adapt_difficulty(
        self, content: dict[str, Any], difficulty: DifficultyLevel
    ) -> dict[str, Any]:
        """Adapt content difficulty"""
        content["difficulty_level"] = difficulty.value

        # Adjust complexity markers
        if difficulty == DifficultyLevel.BEGINNER:
            content["complexity_reduction"] = {
                "simplify_language": True,
                "reduce_concepts": True,
                "increase_guidance": True,
            }
        elif difficulty == DifficultyLevel.EXPERT:
            content["complexity_enhancement"] = {
                "add_advanced_concepts": True,
                "reduce_guidance": True,
                "include_edge_cases": True,
            }

        return content

    def _adapt_to_learning_style(
        self, content: dict[str, Any], learning_style: LearningStyle
    ) -> dict[str, Any]:
        """Adapt content to learning style"""
        content["learning_style_adaptations"] = {
            "primary_style": learning_style.value,
            "content_emphasis": {},
        }

        if learning_style == LearningStyle.VISUAL:
            content["learning_style_adaptations"]["content_emphasis"] = {
                "visuals": "high",
                "diagrams": "high",
                "text": "low",
                "audio": "medium",
            }
        elif learning_style == LearningStyle.KINESTHETIC:
            content["learning_style_adaptations"]["content_emphasis"] = {
                "interactive": "high",
                "simulations": "high",
                "passive_content": "low",
            }

        return content

    def _adapt_pacing(
        self, content: dict[str, Any], strategy: PersonalizationStrategy
    ) -> dict[str, Any]:
        """Adapt content pacing"""
        content["pacing"] = {
            "speed_multiplier": strategy.content_pace,
            "assessment_frequency": strategy.assessment_frequency,
            "break_frequency_minutes": strategy.break_frequency,
        }

        return content

    def _add_scaffolding(
        self, content: dict[str, Any], strategy: PersonalizationStrategy
    ) -> dict[str, Any]:
        """Add scaffolding to content"""
        content["scaffolding"] = {
            "hint_level": strategy.hint_level,
            "example_count": int(strategy.example_frequency),
            "practice_problems": strategy.practice_problems,
            "feedback_timing": strategy.feedback_style,
        }

        return content

    def _add_gamification(
        self, content: dict[str, Any], strategy: PersonalizationStrategy
    ) -> dict[str, Any]:
        """Add gamification elements"""
        content["gamification"] = {
            "achievements_enabled": strategy.achievement_sensitivity > 0.5,
            "competition_mode": "enabled" if strategy.competition_preference > 0.6 else "disabled",
            "narrative_wrapper": strategy.narrative_engagement > 0.5,
            "reward_frequency": "high" if strategy.achievement_sensitivity > 0.7 else "normal",
        }

        return content

    async def _process_task(self, state: dict[str, Any]) -> Any:
        """Process an adaptive learning task"""
        user_id = state.get("user_id", "")
        task_type = state.get("task_type", "analyze")

        if task_type == "analyze":
            metrics = await self.analyze_learner(user_id)
            return {"metrics": metrics.__dict__, "analysis_complete": True}

        elif task_type == "personalize":
            strategy = await self.generate_personalization_strategy(
                user_id, state.get("content_type", "lesson")
            )
            return {"strategy": strategy.__dict__, "personalization_complete": True}

        elif task_type == "adapt":
            content = state.get("content", {})
            strategy = await self.generate_personalization_strategy(user_id)
            adapted = await self.adapt_content(content, strategy)
            return {
                "adapted_content": adapted,
                "adaptations_applied": len(strategy.recommendations),
            }

        elif task_type == "predict":
            difficulty = DifficultyLevel(state.get("difficulty", 3))
            prediction = await self.predict_performance(user_id, difficulty)
            return prediction

        elif task_type == "intervene":
            performance = state.get("performance", {})
            intervention = await self.recommend_intervention(user_id, performance)
            return {
                "intervention": intervention,
                "intervention_needed": intervention is not None,
            }

        return {"status": "unknown_task_type"}
