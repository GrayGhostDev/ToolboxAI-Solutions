"""Learning Analytics Agent for Student Progress Tracking and Educational Insights

This agent analyzes learning patterns, tracks student progress, measures engagement,
and provides actionable insights for improving educational outcomes.
"""

import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import numpy as np

from ..base_agent import AgentConfig, BaseAgent, TaskResult


class ProgressStatus(Enum):
    """Student progress status levels."""

    EXCEEDING = "exceeding"  # Above expected level
    ON_TRACK = "on_track"  # Meeting expectations
    APPROACHING = "approaching"  # Close to expectations
    STRUGGLING = "struggling"  # Below expectations
    AT_RISK = "at_risk"  # Needs immediate intervention


class EngagementLevel(Enum):
    """Student engagement levels."""

    HIGHLY_ENGAGED = "highly_engaged"
    ENGAGED = "engaged"
    MODERATELY_ENGAGED = "moderately_engaged"
    LOW_ENGAGEMENT = "low_engagement"
    DISENGAGED = "disengaged"


class LearningStyle(Enum):
    """Identified learning style preferences."""

    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MULTIMODAL = "multimodal"


class MetricType(Enum):
    """Types of learning metrics to track."""

    COMPLETION_RATE = "completion_rate"
    ACCURACY = "accuracy"
    TIME_ON_TASK = "time_on_task"
    ATTEMPT_COUNT = "attempt_count"
    HELP_REQUESTS = "help_requests"
    ENGAGEMENT_SCORE = "engagement_score"
    MASTERY_LEVEL = "mastery_level"
    GROWTH_RATE = "growth_rate"


@dataclass
class StudentActivity:
    """Individual student activity record."""

    student_id: str
    activity_type: str
    content_id: str
    timestamp: datetime
    duration_minutes: float
    score: Optional[float] = None
    completed: bool = False
    attempts: int = 1
    help_used: bool = False
    feedback_given: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StudentProgress:
    """Comprehensive student progress tracking."""

    student_id: str
    grade_level: str
    subject: str
    current_level: str
    progress_status: ProgressStatus
    engagement_level: EngagementLevel

    # Performance metrics
    overall_score: float
    completion_rate: float
    accuracy_rate: float
    average_time_on_task: float
    total_activities_completed: int

    # Learning patterns
    preferred_learning_style: LearningStyle
    peak_learning_time: Optional[str] = None
    strongest_topics: list[str] = field(default_factory=list)
    struggling_topics: list[str] = field(default_factory=list)

    # Growth metrics
    growth_rate: float = 0.0
    mastery_levels: dict[str, float] = field(default_factory=dict)
    skill_progression: list[dict[str, Any]] = field(default_factory=list)

    # Engagement metrics
    login_frequency: float = 0.0
    session_duration_avg: float = 0.0
    interaction_count: int = 0
    collaboration_score: float = 0.0

    # Risk indicators
    risk_factors: list[str] = field(default_factory=list)
    intervention_needed: bool = False
    last_active: Optional[datetime] = None

    # Historical data
    progress_history: list[dict[str, Any]] = field(default_factory=list)
    achievement_milestones: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class LearningPattern:
    """Identified learning pattern for a student or group."""

    pattern_type: str
    description: str
    confidence: float
    affected_students: list[str]
    characteristics: dict[str, Any]
    recommendations: list[str]
    evidence: list[dict[str, Any]]


@dataclass
class ClassroomAnalytics:
    """Aggregate classroom-level analytics."""

    classroom_id: str
    total_students: int
    average_progress: float
    engagement_distribution: dict[EngagementLevel, int]

    # Performance distribution
    performance_quartiles: dict[str, float]
    score_distribution: list[float]
    completion_distribution: list[float]

    # Topic analysis
    mastered_topics: list[str]
    challenging_topics: list[str]
    topic_performance: dict[str, float]

    # Trends
    weekly_progress: list[float]
    engagement_trend: str
    performance_trend: str

    # Risk analysis
    at_risk_students: list[str]
    high_performers: list[str]
    improving_students: list[str]

    # Recommendations
    class_recommendations: list[str]
    content_adjustments: list[str]
    teaching_strategies: list[str]


@dataclass
class PredictiveInsight:
    """Predictive analytics for future performance."""

    student_id: str
    prediction_type: str
    predicted_value: float
    confidence: float
    timeframe: str
    factors: list[str]
    recommended_interventions: list[str]
    expected_outcome: str


class LearningAnalyticsAgent(BaseAgent):
    """
    Agent for comprehensive learning analytics and student progress tracking.

    Capabilities:
    - Track individual student progress
    - Identify learning patterns
    - Measure engagement levels
    - Detect at-risk students
    - Generate predictive insights
    - Provide personalized recommendations
    - Analyze classroom-level trends
    """

    def __init__(self):
        """Initialize the Learning Analytics Agent."""
        config = AgentConfig(name="LearningAnalyticsAgent")
        super().__init__(config)

        # Analytics storage
        self.student_activities: list[StudentActivity] = []
        self.student_profiles: dict[str, StudentProgress] = {}
        self.learning_patterns: list[LearningPattern] = []
        self.classroom_analytics: dict[str, ClassroomAnalytics] = {}

        # Thresholds and benchmarks
        self.risk_thresholds = {
            "completion_rate": 0.6,
            "accuracy_rate": 0.5,
            "engagement_score": 0.4,
            "login_frequency": 2,  # days between logins
            "growth_rate": -0.1,  # negative growth
        }

        self.engagement_thresholds = {
            EngagementLevel.HIGHLY_ENGAGED: 0.85,
            EngagementLevel.ENGAGED: 0.70,
            EngagementLevel.MODERATELY_ENGAGED: 0.50,
            EngagementLevel.LOW_ENGAGEMENT: 0.30,
            EngagementLevel.DISENGAGED: 0.0,
        }

    async def process(self, task_data: dict[str, Any]) -> TaskResult:
        """
        Process learning analytics task.

        Args:
            task_data: Contains analytics request type and parameters

        Returns:
            TaskResult with analytics insights
        """
        analytics_type = task_data.get("type", "student_progress")

        try:
            if analytics_type == "student_progress":
                result = await self.analyze_student_progress(task_data)
            elif analytics_type == "learning_patterns":
                result = await self.identify_learning_patterns(task_data)
            elif analytics_type == "engagement_analysis":
                result = await self.analyze_engagement(task_data)
            elif analytics_type == "risk_assessment":
                result = await self.assess_at_risk_students(task_data)
            elif analytics_type == "predictive_insights":
                result = await self.generate_predictive_insights(task_data)
            elif analytics_type == "classroom_analytics":
                result = await self.analyze_classroom_performance(task_data)
            elif analytics_type == "personalized_recommendations":
                result = await self.generate_recommendations(task_data)
            elif analytics_type == "activity_tracking":
                result = await self.track_student_activity(task_data)
            else:
                result = await self.comprehensive_analysis(task_data)

            return TaskResult(
                success=True,
                data=result,
                metadata={
                    "analytics_type": analytics_type,
                    "timestamp": datetime.now().isoformat(),
                    "confidence": result.get("confidence", 0.85),
                },
            )

        except Exception as e:
            self.logger.error(f"Analytics processing failed: {str(e)}")
            return TaskResult(success=False, data={}, error=str(e))

    async def track_student_activity(self, data: dict[str, Any]) -> dict[str, Any]:
        """Track and record student learning activities."""
        activity = StudentActivity(
            student_id=data["student_id"],
            activity_type=data["activity_type"],
            content_id=data["content_id"],
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            duration_minutes=data.get("duration_minutes", 0),
            score=data.get("score"),
            completed=data.get("completed", False),
            attempts=data.get("attempts", 1),
            help_used=data.get("help_used", False),
            feedback_given=data.get("feedback"),
            metadata=data.get("metadata", {}),
        )

        self.student_activities.append(activity)

        # Update student profile
        await self._update_student_profile(activity)

        # Check for immediate insights
        insights = await self._generate_activity_insights(activity)

        return {
            "activity_recorded": True,
            "student_id": activity.student_id,
            "immediate_insights": insights,
            "current_progress": self._get_student_summary(activity.student_id),
        }

    async def analyze_student_progress(self, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze individual student progress and performance."""
        student_id = data["student_id"]
        timeframe = data.get("timeframe", "all")

        # Get student activities
        activities = self._get_student_activities(student_id, timeframe)

        if not activities:
            return {
                "student_id": student_id,
                "status": "no_data",
                "message": "No activity data available for this student",
            }

        # Calculate progress metrics
        progress = await self._calculate_progress_metrics(activities)

        # Identify learning patterns
        patterns = await self._identify_student_patterns(activities)

        # Determine progress status
        status = self._determine_progress_status(progress)

        # Generate growth analysis
        growth = await self._analyze_growth_rate(student_id, activities)

        # Create or update student profile
        profile = StudentProgress(
            student_id=student_id,
            grade_level=data.get("grade_level", "unknown"),
            subject=data.get("subject", "general"),
            current_level=self._determine_current_level(progress),
            progress_status=status,
            engagement_level=self._calculate_engagement_level(activities),
            overall_score=progress["overall_score"],
            completion_rate=progress["completion_rate"],
            accuracy_rate=progress["accuracy_rate"],
            average_time_on_task=progress["avg_time_on_task"],
            total_activities_completed=len([a for a in activities if a.completed]),
            preferred_learning_style=patterns["learning_style"],
            peak_learning_time=patterns["peak_time"],
            strongest_topics=patterns["strong_topics"],
            struggling_topics=patterns["weak_topics"],
            growth_rate=growth["rate"],
            mastery_levels=progress["mastery_levels"],
            risk_factors=self._identify_risk_factors(progress, activities),
            intervention_needed=status == ProgressStatus.AT_RISK,
            last_active=max(a.timestamp for a in activities) if activities else None,
        )

        self.student_profiles[student_id] = profile

        return {
            "student_id": student_id,
            "progress_summary": {
                "status": profile.progress_status.value,
                "overall_score": profile.overall_score,
                "completion_rate": profile.completion_rate,
                "engagement": profile.engagement_level.value,
            },
            "strengths": profile.strongest_topics,
            "areas_for_improvement": profile.struggling_topics,
            "growth_analysis": growth,
            "recommendations": await self._generate_student_recommendations(profile),
            "detailed_metrics": progress,
            "learning_patterns": patterns,
        }

    async def identify_learning_patterns(self, data: dict[str, Any]) -> dict[str, Any]:
        """Identify learning patterns across students or for individuals."""
        scope = data.get("scope", "individual")

        if scope == "individual":
            student_id = data["student_id"]
            activities = self._get_student_activities(student_id)
            patterns = await self._identify_student_patterns(activities)

            return {
                "student_id": student_id,
                "patterns": patterns,
                "learning_style": (
                    patterns["learning_style"].value if patterns["learning_style"] else None
                ),
                "behavioral_patterns": patterns["behaviors"],
                "performance_patterns": patterns["performance"],
                "recommendations": patterns["recommendations"],
            }

        else:  # classroom or cohort level
            # Cluster students by learning patterns
            clusters = await self._cluster_learning_patterns(data.get("student_ids", []))

            # Identify common patterns
            common_patterns = await self._identify_common_patterns(clusters)

            return {
                "scope": scope,
                "pattern_clusters": clusters,
                "common_patterns": common_patterns,
                "diversity_index": self._calculate_learning_diversity(clusters),
                "grouped_recommendations": await self._generate_group_recommendations(clusters),
            }

    async def analyze_engagement(self, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze student engagement levels and patterns."""
        student_ids = data.get("student_ids", [])
        if not student_ids and "student_id" in data:
            student_ids = [data["student_id"]]

        engagement_analysis = {}

        for student_id in student_ids:
            activities = self._get_student_activities(student_id)

            # Calculate engagement metrics
            metrics = {
                "login_frequency": self._calculate_login_frequency(activities),
                "session_duration": self._calculate_average_session_duration(activities),
                "interaction_rate": self._calculate_interaction_rate(activities),
                "completion_consistency": self._calculate_completion_consistency(activities),
                "help_seeking_behavior": self._analyze_help_seeking(activities),
                "time_distribution": self._analyze_time_distribution(activities),
            }

            # Determine engagement level
            engagement_score = self._calculate_engagement_score(metrics)
            engagement_level = self._determine_engagement_level(engagement_score)

            # Identify engagement patterns
            patterns = {
                "peak_engagement_times": self._identify_peak_times(activities),
                "engagement_triggers": self._identify_engagement_triggers(activities),
                "disengagement_indicators": self._identify_disengagement_signs(metrics),
                "engagement_trend": self._calculate_engagement_trend(activities),
            }

            engagement_analysis[student_id] = {
                "engagement_level": engagement_level.value,
                "engagement_score": engagement_score,
                "metrics": metrics,
                "patterns": patterns,
                "recommendations": self._generate_engagement_recommendations(
                    engagement_level, patterns
                ),
            }

        # Generate aggregate insights if multiple students
        if len(student_ids) > 1:
            engagement_analysis["aggregate"] = {
                "average_engagement": statistics.mean(
                    [
                        a["engagement_score"]
                        for a in engagement_analysis.values()
                        if isinstance(a, dict) and "engagement_score" in a
                    ]
                ),
                "distribution": Counter(
                    [
                        a["engagement_level"]
                        for a in engagement_analysis.values()
                        if isinstance(a, dict) and "engagement_level" in a
                    ]
                ),
                "trends": self._analyze_cohort_engagement_trends(engagement_analysis),
            }

        return engagement_analysis

    async def assess_at_risk_students(self, data: dict[str, Any]) -> dict[str, Any]:
        """Identify and assess students at risk of falling behind."""
        classroom_id = data.get("classroom_id")
        threshold_overrides = data.get("thresholds", {})

        # Merge custom thresholds
        thresholds = {**self.risk_thresholds, **threshold_overrides}

        at_risk_students = []
        borderline_students = []

        # Analyze all students in classroom
        for student_id, profile in self.student_profiles.items():
            if classroom_id and profile.metadata.get("classroom_id") != classroom_id:
                continue

            risk_score = 0
            risk_factors = []

            # Check each risk indicator
            if profile.completion_rate < thresholds["completion_rate"]:
                risk_score += 2
                risk_factors.append(f"Low completion rate: {profile.completion_rate:.1%}")

            if profile.accuracy_rate < thresholds["accuracy_rate"]:
                risk_score += 2
                risk_factors.append(f"Low accuracy: {profile.accuracy_rate:.1%}")

            if profile.engagement_level in [
                EngagementLevel.LOW_ENGAGEMENT,
                EngagementLevel.DISENGAGED,
            ]:
                risk_score += 3
                risk_factors.append(f"Low engagement: {profile.engagement_level.value}")

            if profile.growth_rate < thresholds["growth_rate"]:
                risk_score += 3
                risk_factors.append(f"Negative growth: {profile.growth_rate:.1%}")

            if profile.last_active:
                days_inactive = (datetime.now() - profile.last_active).days
                if days_inactive > thresholds["login_frequency"]:
                    risk_score += 1
                    risk_factors.append(f"Inactive for {days_inactive} days")

            # Categorize risk level
            if risk_score >= 5:
                at_risk_students.append(
                    {
                        "student_id": student_id,
                        "risk_score": risk_score,
                        "risk_level": "high",
                        "risk_factors": risk_factors,
                        "intervention_priority": "immediate",
                        "recommended_interventions": await self._generate_interventions(
                            profile, risk_factors
                        ),
                    }
                )
            elif risk_score >= 3:
                borderline_students.append(
                    {
                        "student_id": student_id,
                        "risk_score": risk_score,
                        "risk_level": "moderate",
                        "risk_factors": risk_factors,
                        "intervention_priority": "monitor",
                        "recommended_interventions": await self._generate_interventions(
                            profile, risk_factors
                        ),
                    }
                )

        return {
            "assessment_date": datetime.now().isoformat(),
            "total_assessed": len(self.student_profiles),
            "at_risk_count": len(at_risk_students),
            "borderline_count": len(borderline_students),
            "at_risk_students": at_risk_students,
            "borderline_students": borderline_students,
            "risk_distribution": self._calculate_risk_distribution(),
            "classroom_health": self._assess_classroom_health(
                at_risk_students, borderline_students
            ),
            "action_plan": await self._generate_action_plan(at_risk_students, borderline_students),
        }

    async def generate_predictive_insights(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate predictive insights about future student performance."""
        student_id = data["student_id"]
        prediction_horizon = data.get("horizon", "month")  # week, month, quarter

        # Get historical data
        activities = self._get_student_activities(student_id)
        profile = self.student_profiles.get(student_id)

        if not activities or not profile:
            return {
                "student_id": student_id,
                "status": "insufficient_data",
                "message": "Not enough historical data for predictions",
            }

        predictions = []

        # Predict completion rate
        completion_prediction = await self._predict_completion_rate(
            activities, profile, prediction_horizon
        )
        predictions.append(
            PredictiveInsight(
                student_id=student_id,
                prediction_type="completion_rate",
                predicted_value=completion_prediction["value"],
                confidence=completion_prediction["confidence"],
                timeframe=prediction_horizon,
                factors=completion_prediction["factors"],
                recommended_interventions=completion_prediction["interventions"],
                expected_outcome=completion_prediction["outcome"],
            )
        )

        # Predict performance level
        performance_prediction = await self._predict_performance_level(
            activities, profile, prediction_horizon
        )
        predictions.append(
            PredictiveInsight(
                student_id=student_id,
                prediction_type="performance_level",
                predicted_value=performance_prediction["value"],
                confidence=performance_prediction["confidence"],
                timeframe=prediction_horizon,
                factors=performance_prediction["factors"],
                recommended_interventions=performance_prediction["interventions"],
                expected_outcome=performance_prediction["outcome"],
            )
        )

        # Predict engagement changes
        engagement_prediction = await self._predict_engagement_changes(
            activities, profile, prediction_horizon
        )
        predictions.append(
            PredictiveInsight(
                student_id=student_id,
                prediction_type="engagement_level",
                predicted_value=engagement_prediction["value"],
                confidence=engagement_prediction["confidence"],
                timeframe=prediction_horizon,
                factors=engagement_prediction["factors"],
                recommended_interventions=engagement_prediction["interventions"],
                expected_outcome=engagement_prediction["outcome"],
            )
        )

        # Predict mastery timeline
        mastery_prediction = await self._predict_mastery_timeline(
            activities, profile, data.get("target_skills", [])
        )

        return {
            "student_id": student_id,
            "prediction_horizon": prediction_horizon,
            "predictions": [
                {
                    "type": p.prediction_type,
                    "predicted_value": p.predicted_value,
                    "confidence": p.confidence,
                    "factors": p.factors,
                    "interventions": p.recommended_interventions,
                    "expected_outcome": p.expected_outcome,
                }
                for p in predictions
            ],
            "mastery_timeline": mastery_prediction,
            "risk_assessment": self._assess_future_risk(predictions),
            "optimization_opportunities": await self._identify_optimization_opportunities(
                predictions, profile
            ),
            "recommended_adjustments": await self._generate_predictive_recommendations(
                predictions, profile
            ),
        }

    async def analyze_classroom_performance(self, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze aggregate classroom-level performance and trends."""
        classroom_id = data["classroom_id"]
        student_ids = data.get("student_ids", [])

        # Collect classroom data
        classroom_activities = []
        classroom_profiles = []

        for student_id in student_ids:
            activities = self._get_student_activities(student_id)
            if activities:
                classroom_activities.extend(activities)

            profile = self.student_profiles.get(student_id)
            if profile:
                classroom_profiles.append(profile)

        if not classroom_profiles:
            return {
                "classroom_id": classroom_id,
                "status": "no_data",
                "message": "No student data available for this classroom",
            }

        # Calculate aggregate metrics
        avg_progress = statistics.mean([p.overall_score for p in classroom_profiles])

        # Performance distribution
        scores = [p.overall_score for p in classroom_profiles]
        performance_quartiles = {
            "q1": np.percentile(scores, 25),
            "median": np.percentile(scores, 50),
            "q3": np.percentile(scores, 75),
            "min": min(scores),
            "max": max(scores),
        }

        # Engagement distribution
        engagement_dist = Counter([p.engagement_level for p in classroom_profiles])

        # Topic performance analysis
        topic_performance = await self._analyze_topic_performance(classroom_activities)

        # Identify patterns
        mastered_topics = [topic for topic, score in topic_performance.items() if score >= 0.8]
        challenging_topics = [topic for topic, score in topic_performance.items() if score < 0.6]

        # Trend analysis
        weekly_progress = await self._calculate_weekly_progress(classroom_activities)
        engagement_trend = self._determine_trend(
            [p.engagement_level.value for p in classroom_profiles]
        )
        performance_trend = self._determine_trend(weekly_progress)

        # Identify student groups
        at_risk = [
            p.student_id for p in classroom_profiles if p.progress_status == ProgressStatus.AT_RISK
        ]
        high_performers = [
            p.student_id
            for p in classroom_profiles
            if p.progress_status == ProgressStatus.EXCEEDING
        ]
        improving = await self._identify_improving_students(classroom_profiles)

        # Generate recommendations
        recommendations = await self._generate_classroom_recommendations(
            classroom_profiles, topic_performance
        )

        analytics = ClassroomAnalytics(
            classroom_id=classroom_id,
            total_students=len(student_ids),
            average_progress=avg_progress,
            engagement_distribution={k: v for k, v in engagement_dist.items()},
            performance_quartiles=performance_quartiles,
            score_distribution=scores,
            completion_distribution=[p.completion_rate for p in classroom_profiles],
            mastered_topics=mastered_topics,
            challenging_topics=challenging_topics,
            topic_performance=topic_performance,
            weekly_progress=weekly_progress,
            engagement_trend=engagement_trend,
            performance_trend=performance_trend,
            at_risk_students=at_risk,
            high_performers=high_performers,
            improving_students=improving,
            class_recommendations=recommendations["class_level"],
            content_adjustments=recommendations["content"],
            teaching_strategies=recommendations["strategies"],
        )

        self.classroom_analytics[classroom_id] = analytics

        return {
            "classroom_id": classroom_id,
            "summary": {
                "total_students": analytics.total_students,
                "average_progress": analytics.average_progress,
                "performance_trend": analytics.performance_trend,
                "engagement_trend": analytics.engagement_trend,
            },
            "performance_insights": {
                "distribution": performance_quartiles,
                "mastered_topics": mastered_topics,
                "challenging_topics": challenging_topics,
                "topic_scores": topic_performance,
            },
            "student_segments": {
                "high_performers": high_performers,
                "at_risk": at_risk,
                "improving": improving,
                "engagement_distribution": dict(engagement_dist),
            },
            "trends": {
                "weekly_progress": weekly_progress,
                "performance_trend": performance_trend,
                "engagement_trend": engagement_trend,
            },
            "recommendations": {
                "immediate_actions": recommendations["class_level"][:3],
                "content_adjustments": recommendations["content"],
                "teaching_strategies": recommendations["strategies"],
                "individualized_support": await self._generate_individualized_support(
                    at_risk, classroom_profiles
                ),
            },
        }

    async def generate_recommendations(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate personalized learning recommendations."""
        student_id = data["student_id"]
        profile = self.student_profiles.get(student_id)

        if not profile:
            return {
                "student_id": student_id,
                "status": "no_profile",
                "message": "Student profile not found",
            }

        recommendations = {
            "immediate_actions": [],
            "content_recommendations": [],
            "learning_strategies": [],
            "practice_areas": [],
            "enrichment_opportunities": [],
        }

        # Based on progress status
        if profile.progress_status == ProgressStatus.AT_RISK:
            recommendations["immediate_actions"].extend(
                [
                    "Schedule one-on-one support session",
                    "Reduce content difficulty temporarily",
                    "Increase scaffolding and guided practice",
                ]
            )
        elif profile.progress_status == ProgressStatus.STRUGGLING:
            recommendations["immediate_actions"].extend(
                [
                    "Review prerequisite concepts",
                    "Provide additional practice problems",
                    "Implement peer tutoring",
                ]
            )
        elif profile.progress_status == ProgressStatus.EXCEEDING:
            recommendations["immediate_actions"].extend(
                [
                    "Introduce advanced challenges",
                    "Consider acceleration options",
                    "Provide leadership opportunities",
                ]
            )

        # Based on learning style
        if profile.preferred_learning_style == LearningStyle.VISUAL:
            recommendations["learning_strategies"].extend(
                [
                    "Use more diagrams and infographics",
                    "Incorporate video tutorials",
                    "Create mind maps for complex topics",
                ]
            )
        elif profile.preferred_learning_style == LearningStyle.KINESTHETIC:
            recommendations["learning_strategies"].extend(
                [
                    "Add hands-on activities",
                    "Use manipulatives and simulations",
                    "Incorporate movement-based learning",
                ]
            )

        # Based on struggling topics
        for topic in profile.struggling_topics:
            recommendations["practice_areas"].append(
                {
                    "topic": topic,
                    "recommended_exercises": await self._get_topic_exercises(
                        topic, profile.grade_level
                    ),
                    "estimated_time": "15-20 minutes daily",
                    "support_resources": await self._get_support_resources(topic),
                }
            )

        # Based on engagement level
        if profile.engagement_level in [
            EngagementLevel.LOW_ENGAGEMENT,
            EngagementLevel.DISENGAGED,
        ]:
            recommendations["content_recommendations"].extend(
                [
                    "Gamify learning experiences",
                    "Add collaborative projects",
                    "Incorporate student interests",
                    "Shorten activity duration",
                    "Increase variety in content types",
                ]
            )

        # Enrichment for high performers
        if profile.progress_status == ProgressStatus.EXCEEDING:
            recommendations["enrichment_opportunities"].extend(
                [
                    "Advanced problem-solving challenges",
                    "Cross-curricular projects",
                    "Peer mentoring opportunities",
                    "Independent research topics",
                ]
            )

        return {
            "student_id": student_id,
            "personalized_recommendations": recommendations,
            "priority_order": self._prioritize_recommendations(recommendations, profile),
            "expected_impact": await self._estimate_recommendation_impact(recommendations, profile),
            "implementation_timeline": self._generate_implementation_timeline(recommendations),
            "success_metrics": self._define_success_metrics(recommendations, profile),
        }

    async def comprehensive_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        """Perform comprehensive analysis combining all analytics capabilities."""
        scope = data.get("scope", "student")

        if scope == "student":
            student_id = data["student_id"]

            # Run all analyses
            progress = await self.analyze_student_progress({"student_id": student_id})
            patterns = await self.identify_learning_patterns({"student_id": student_id})
            engagement = await self.analyze_engagement({"student_id": student_id})
            predictions = await self.generate_predictive_insights({"student_id": student_id})
            recommendations = await self.generate_recommendations({"student_id": student_id})

            return {
                "student_id": student_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "progress_analysis": progress,
                "learning_patterns": patterns,
                "engagement_analysis": engagement,
                "predictive_insights": predictions,
                "recommendations": recommendations,
                "executive_summary": await self._generate_executive_summary(
                    progress, patterns, engagement, predictions
                ),
            }

        else:  # classroom scope
            classroom_id = data["classroom_id"]
            student_ids = data.get("student_ids", [])

            # Run classroom analyses
            classroom = await self.analyze_classroom_performance(
                {"classroom_id": classroom_id, "student_ids": student_ids}
            )
            risk_assessment = await self.assess_at_risk_students({"classroom_id": classroom_id})

            # Individual summaries
            individual_insights = {}
            for student_id in student_ids:
                individual_insights[student_id] = {
                    "progress": self._get_student_summary(student_id),
                    "needs_attention": student_id in risk_assessment["at_risk_students"],
                }

            return {
                "classroom_id": classroom_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "classroom_performance": classroom,
                "risk_assessment": risk_assessment,
                "individual_insights": individual_insights,
                "action_priorities": await self._prioritize_classroom_actions(
                    classroom, risk_assessment
                ),
                "resource_allocation": await self._recommend_resource_allocation(
                    classroom, risk_assessment
                ),
            }

    # Helper methods

    def _get_student_activities(
        self, student_id: str, timeframe: str = "all"
    ) -> list[StudentActivity]:
        """Get student activities within specified timeframe."""
        activities = [a for a in self.student_activities if a.student_id == student_id]

        if timeframe != "all":
            cutoff = self._get_timeframe_cutoff(timeframe)
            activities = [a for a in activities if a.timestamp >= cutoff]

        return sorted(activities, key=lambda x: x.timestamp)

    def _get_timeframe_cutoff(self, timeframe: str) -> datetime:
        """Get cutoff date for timeframe."""
        now = datetime.now()
        if timeframe == "week":
            return now - timedelta(days=7)
        elif timeframe == "month":
            return now - timedelta(days=30)
        elif timeframe == "quarter":
            return now - timedelta(days=90)
        else:
            return datetime.min

    async def _calculate_progress_metrics(
        self, activities: list[StudentActivity]
    ) -> dict[str, Any]:
        """Calculate comprehensive progress metrics."""
        if not activities:
            return {}

        completed = [a for a in activities if a.completed]
        scored = [a for a in activities if a.score is not None]

        metrics = {
            "overall_score": statistics.mean([a.score for a in scored]) if scored else 0,
            "completion_rate": len(completed) / len(activities) if activities else 0,
            "accuracy_rate": (
                statistics.mean([a.score for a in scored if a.score is not None]) if scored else 0
            ),
            "avg_time_on_task": statistics.mean([a.duration_minutes for a in activities]),
            "total_time_spent": sum(a.duration_minutes for a in activities),
            "avg_attempts": statistics.mean([a.attempts for a in activities]),
            "help_usage_rate": len([a for a in activities if a.help_used]) / len(activities),
            "mastery_levels": self._calculate_mastery_levels(activities),
        }

        return metrics

    def _calculate_mastery_levels(self, activities: list[StudentActivity]) -> dict[str, float]:
        """Calculate mastery level for each topic."""
        topic_scores = defaultdict(list)

        for activity in activities:
            if activity.score is not None:
                topic = activity.metadata.get("topic", "general")
                topic_scores[topic].append(activity.score)

        mastery_levels = {}
        for topic, scores in topic_scores.items():
            if scores:
                # Weight recent scores more heavily
                weights = [0.5 + 0.5 * (i / len(scores)) for i in range(len(scores))]
                weighted_avg = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
                mastery_levels[topic] = weighted_avg

        return mastery_levels

    def _determine_progress_status(self, metrics: dict[str, Any]) -> ProgressStatus:
        """Determine student's progress status."""
        score = metrics.get("overall_score", 0)
        completion = metrics.get("completion_rate", 0)

        if score >= 0.85 and completion >= 0.9:
            return ProgressStatus.EXCEEDING
        elif score >= 0.70 and completion >= 0.75:
            return ProgressStatus.ON_TRACK
        elif score >= 0.60 and completion >= 0.60:
            return ProgressStatus.APPROACHING
        elif score >= 0.50 or completion >= 0.50:
            return ProgressStatus.STRUGGLING
        else:
            return ProgressStatus.AT_RISK

    def _calculate_engagement_level(self, activities: list[StudentActivity]) -> EngagementLevel:
        """Calculate student's engagement level."""
        if not activities:
            return EngagementLevel.DISENGAGED

        # Calculate engagement metrics
        completion_rate = len([a for a in activities if a.completed]) / len(activities)
        avg_duration = statistics.mean([a.duration_minutes for a in activities])
        recent_activity = (datetime.now() - max(a.timestamp for a in activities)).days

        # Engagement score (0-1)
        engagement_score = (
            completion_rate * 0.4
            + min(avg_duration / 30, 1) * 0.3  # Normalize to 30 min sessions
            + max(0, 1 - recent_activity / 7) * 0.3  # Penalize inactivity
        )

        return self._determine_engagement_level(engagement_score)

    def _determine_engagement_level(self, score: float) -> EngagementLevel:
        """Determine engagement level from score."""
        for level, threshold in sorted(
            self.engagement_thresholds.items(), key=lambda x: x[1], reverse=True
        ):
            if score >= threshold:
                return level
        return EngagementLevel.DISENGAGED

    async def _identify_student_patterns(self, activities: list[StudentActivity]) -> dict[str, Any]:
        """Identify learning patterns for a student."""
        patterns = {
            "learning_style": LearningStyle.MULTIMODAL,
            "peak_time": None,
            "strong_topics": [],
            "weak_topics": [],
            "behaviors": [],
            "performance": {},
            "recommendations": [],
        }

        if not activities:
            return patterns

        # Analyze activity types to determine learning style
        [a.activity_type for a in activities]
        type_performance = defaultdict(list)

        for activity in activities:
            if activity.score is not None:
                type_performance[activity.activity_type].append(activity.score)

        # Determine preferred learning style based on performance
        best_type = max(type_performance.items(), key=lambda x: statistics.mean(x[1]))
        if "visual" in best_type[0].lower():
            patterns["learning_style"] = LearningStyle.VISUAL
        elif "audio" in best_type[0].lower():
            patterns["learning_style"] = LearningStyle.AUDITORY
        elif "interactive" in best_type[0].lower() or "hands" in best_type[0].lower():
            patterns["learning_style"] = LearningStyle.KINESTHETIC
        elif "read" in best_type[0].lower() or "text" in best_type[0].lower():
            patterns["learning_style"] = LearningStyle.READING_WRITING

        # Identify peak learning times
        time_performance = defaultdict(list)
        for activity in activities:
            hour = activity.timestamp.hour
            if activity.score is not None:
                time_performance[hour].append(activity.score)

        if time_performance:
            best_hour = max(time_performance.items(), key=lambda x: statistics.mean(x[1]))
            patterns["peak_time"] = f"{best_hour[0]:02d}:00"

        # Identify strong and weak topics
        topic_performance = defaultdict(list)
        for activity in activities:
            if activity.score is not None:
                topic = activity.metadata.get("topic", "general")
                topic_performance[topic].append(activity.score)

        for topic, scores in topic_performance.items():
            avg_score = statistics.mean(scores)
            if avg_score >= 0.8:
                patterns["strong_topics"].append(topic)
            elif avg_score < 0.6:
                patterns["weak_topics"].append(topic)

        # Identify behavioral patterns
        if len([a for a in activities if a.help_used]) / len(activities) > 0.3:
            patterns["behaviors"].append("frequent_help_seeker")

        avg_attempts = statistics.mean([a.attempts for a in activities])
        if avg_attempts > 2:
            patterns["behaviors"].append("persistent_learner")
        elif avg_attempts < 1.5:
            patterns["behaviors"].append("quick_completer")

        # Generate pattern-based recommendations
        patterns["recommendations"] = await self._generate_pattern_recommendations(patterns)

        return patterns

    def _get_student_summary(self, student_id: str) -> dict[str, Any]:
        """Get quick summary of student progress."""
        profile = self.student_profiles.get(student_id)

        if not profile:
            return {"status": "no_profile"}

        return {
            "progress_status": profile.progress_status.value,
            "engagement_level": profile.engagement_level.value,
            "overall_score": profile.overall_score,
            "completion_rate": profile.completion_rate,
            "last_active": profile.last_active.isoformat() if profile.last_active else None,
            "needs_intervention": profile.intervention_needed,
        }

    async def _generate_pattern_recommendations(self, patterns: dict[str, Any]) -> list[str]:
        """Generate recommendations based on identified patterns."""
        recommendations = []

        # Learning style recommendations
        if patterns["learning_style"] == LearningStyle.VISUAL:
            recommendations.append("Incorporate more visual aids and diagrams")
        elif patterns["learning_style"] == LearningStyle.KINESTHETIC:
            recommendations.append("Add hands-on activities and simulations")

        # Peak time recommendations
        if patterns["peak_time"]:
            recommendations.append(f"Schedule important lessons around {patterns['peak_time']}")

        # Topic recommendations
        if patterns["weak_topics"]:
            recommendations.append(
                f"Focus on strengthening: {', '.join(patterns['weak_topics'][:3])}"
            )

        if patterns["strong_topics"]:
            recommendations.append(
                f"Build on strengths in: {', '.join(patterns['strong_topics'][:3])}"
            )

        return recommendations

    async def _process_task(self, state: "AgentState") -> Any:
        """
        Process the task for this educational agent.

        This implements the abstract method from BaseAgent.

        Args:
            state: Current agent state containing the task

        Returns:
            Task result
        """

        # Extract the task
        task = state.get("task", "")
        context = state.get("context", {})

        # For now, return a simple response
        # This will be replaced with actual LLM integration
        return {
            "agent": self.__class__.__name__,
            "task": task,
            "status": "completed",
            "result": f"{self.__class__.__name__} processed task: {task[:100] if task else 'No task'}...",
            "context": context,
        }
