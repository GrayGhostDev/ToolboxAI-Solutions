"""
Context Tracker - User Context Management and Session Persistence
================================================================

The ContextTracker manages comprehensive user context across learning sessions:
- Multi-layered context management (immediate, session, historical)
- Intelligent context compression and summarization
- Learning pattern recognition and adaptation
- Cross-session persistence and recovery
- Real-time context updates and synchronization
- Educational profile development and maintenance

This component provides the memory and continuity that enables
personalized and adaptive educational experiences.
"""

import gzip
import json
import logging
import os
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ContextScope(Enum):
    """Scope of context information"""

    IMMEDIATE = "immediate"  # Current interaction/action
    SESSION = "session"  # Current learning session
    SHORT_TERM = "short_term"  # Recent sessions (days)
    LONG_TERM = "long_term"  # Historical patterns (weeks/months)
    PERSISTENT = "persistent"  # Permanent learner profile


class ContextType(Enum):
    """Types of context information"""

    LEARNING_STATE = "learning_state"
    BEHAVIORAL_PATTERNS = "behavioral_patterns"
    PERFORMANCE_HISTORY = "performance_history"
    PREFERENCES = "preferences"
    SOCIAL_INTERACTIONS = "social_interactions"
    EMOTIONAL_STATE = "emotional_state"
    METACOGNITIVE = "metacognitive"
    ENVIRONMENTAL = "environmental"


@dataclass
class ContextEntry:
    """Individual context entry with metadata"""

    # Core data
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context_type: ContextType = ContextType.LEARNING_STATE
    scope: ContextScope = ContextScope.IMMEDIATE

    # Content
    data: dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    keywords: list[str] = field(default_factory=list)

    # Temporal information
    timestamp: datetime = field(default_factory=datetime.now)
    validity_period: Optional[timedelta] = None
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0

    # Relevance and quality
    relevance_score: float = 1.0  # 0-1 how relevant this context is
    confidence: float = 1.0  # 0-1 confidence in the data
    importance: float = 0.5  # 0-1 importance for future decisions

    # Relationships
    related_entries: list[str] = field(default_factory=list)
    derived_from: Optional[str] = None

    # Educational metadata
    subject_area: Optional[str] = None
    learning_objective: Optional[str] = None
    skill_level: Optional[float] = None

    @property
    def is_expired(self) -> bool:
        """Check if context entry has expired"""
        if self.validity_period:
            return datetime.now() > (self.timestamp + self.validity_period)
        return False

    @property
    def age(self) -> timedelta:
        """Age of the context entry"""
        return datetime.now() - self.timestamp

    @property
    def recency_score(self) -> float:
        """Score based on recency (1.0 = very recent, 0.0 = very old)"""
        max_age_days = 30  # Consider 30 days as maximum relevance
        age_days = self.age.total_seconds() / (24 * 3600)
        return max(0.0, 1.0 - (age_days / max_age_days))

    def update_access(self):
        """Update access statistics"""
        self.last_accessed = datetime.now()
        self.access_count += 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result["context_type"] = self.context_type.value
        result["scope"] = self.scope.value
        result["timestamp"] = self.timestamp.isoformat()
        result["last_accessed"] = self.last_accessed.isoformat()
        result["validity_period"] = (
            self.validity_period.total_seconds() if self.validity_period else None
        )
        result["is_expired"] = self.is_expired
        result["age_seconds"] = self.age.total_seconds()
        result["recency_score"] = self.recency_score
        return result


@dataclass
class UserContext:
    """Complete user context aggregation"""

    # User identification
    user_id: str
    session_id: str

    # Context entries by scope
    immediate_context: list[ContextEntry] = field(default_factory=list)
    session_context: list[ContextEntry] = field(default_factory=list)
    short_term_context: list[ContextEntry] = field(default_factory=list)
    long_term_context: list[ContextEntry] = field(default_factory=list)
    persistent_context: list[ContextEntry] = field(default_factory=list)

    # Session information
    session_start: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    session_duration: float = 0.0

    # Learning profile
    learning_style: str = "unknown"
    preferred_difficulty: float = 0.5
    dominant_subjects: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    areas_for_improvement: list[str] = field(default_factory=list)

    # Behavioral patterns
    engagement_patterns: dict[str, Any] = field(default_factory=dict)
    performance_trends: dict[str, list[float]] = field(default_factory=dict)
    learning_velocity: float = 0.0

    # Social context
    peer_interactions: dict[str, Any] = field(default_factory=dict)
    collaboration_history: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    context_version: str = "1.0"
    last_updated: datetime = field(default_factory=datetime.now)
    compression_ratio: float = 1.0  # How much context has been compressed

    def get_all_entries(self) -> list[ContextEntry]:
        """Get all context entries across all scopes"""
        all_entries = []
        all_entries.extend(self.immediate_context)
        all_entries.extend(self.session_context)
        all_entries.extend(self.short_term_context)
        all_entries.extend(self.long_term_context)
        all_entries.extend(self.persistent_context)
        return all_entries

    def get_relevant_context(
        self,
        context_types: Optional[list[ContextType]] = None,
        min_relevance: float = 0.3,
    ) -> list[ContextEntry]:
        """Get relevant context entries based on filters"""

        all_entries = self.get_all_entries()
        relevant_entries = []

        for entry in all_entries:
            # Skip expired entries
            if entry.is_expired:
                continue

            # Filter by context type if specified
            if context_types and entry.context_type not in context_types:
                continue

            # Filter by relevance threshold
            if entry.relevance_score < min_relevance:
                continue

            relevant_entries.append(entry)

        # Sort by relevance and recency
        relevant_entries.sort(
            key=lambda e: (e.relevance_score * e.recency_score * e.importance),
            reverse=True,
        )

        return relevant_entries

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)

        # Convert datetime fields
        result["session_start"] = self.session_start.isoformat()
        result["last_activity"] = self.last_activity.isoformat()
        result["last_updated"] = self.last_updated.isoformat()

        # Convert context entries
        result["immediate_context"] = [entry.to_dict() for entry in self.immediate_context]
        result["session_context"] = [entry.to_dict() for entry in self.session_context]
        result["short_term_context"] = [entry.to_dict() for entry in self.short_term_context]
        result["long_term_context"] = [entry.to_dict() for entry in self.long_term_context]
        result["persistent_context"] = [entry.to_dict() for entry in self.persistent_context]

        return result


class LearningPatternRecognizer:
    """Recognizes patterns in learning behavior and performance"""

    def __init__(self):
        self.pattern_types = {
            "performance_cycles": self._detect_performance_cycles,
            "engagement_patterns": self._detect_engagement_patterns,
            "difficulty_preferences": self._detect_difficulty_preferences,
            "learning_velocity": self._calculate_learning_velocity,
            "subject_preferences": self._detect_subject_preferences,
            "time_patterns": self._detect_time_patterns,
            "collaboration_tendencies": self._detect_collaboration_tendencies,
        }

    def analyze_patterns(self, context: UserContext) -> dict[str, Any]:
        """Analyze learning patterns from user context"""

        patterns = {}

        for pattern_name, detector in self.pattern_types.items():
            try:
                pattern_result = detector(context)
                patterns[pattern_name] = pattern_result
            except Exception as e:
                logger.warning(f"Pattern detection failed for {pattern_name}: {e}")
                patterns[pattern_name] = None

        return patterns

    def _detect_performance_cycles(self, context: UserContext) -> dict[str, Any]:
        """Detect cyclical patterns in performance"""

        performance_entries = [
            entry
            for entry in context.get_all_entries()
            if entry.context_type == ContextType.PERFORMANCE_HISTORY and "score" in entry.data
        ]

        if len(performance_entries) < 10:
            return {"status": "insufficient_data", "confidence": 0.0}

        # Sort by timestamp
        performance_entries.sort(key=lambda e: e.timestamp)
        scores = [entry.data["score"] for entry in performance_entries]

        # Simple cycle detection using autocorrelation
        def autocorrelation(data, lag):
            if len(data) <= lag:
                return 0

            n = len(data) - lag
            if n <= 0:
                return 0

            mean_data = np.mean(data)
            numerator = sum((data[i] - mean_data) * (data[i + lag] - mean_data) for i in range(n))
            denominator = sum((x - mean_data) ** 2 for x in data)

            return numerator / denominator if denominator != 0 else 0

        # Check for cycles of different lengths
        max_cycle_length = min(len(scores) // 3, 20)
        best_correlation = 0
        best_cycle_length = 0

        for lag in range(2, max_cycle_length):
            correlation = autocorrelation(scores, lag)
            if abs(correlation) > abs(best_correlation):
                best_correlation = correlation
                best_cycle_length = lag

        cycle_strength = abs(best_correlation)

        return {
            "status": "detected" if cycle_strength > 0.3 else "weak",
            "cycle_length": best_cycle_length,
            "strength": cycle_strength,
            "confidence": min(1.0, cycle_strength * 2),
            "trend": "improving" if best_correlation > 0 else "declining",
        }

    def _detect_engagement_patterns(self, context: UserContext) -> dict[str, Any]:
        """Detect patterns in student engagement"""

        engagement_entries = [
            entry
            for entry in context.get_all_entries()
            if entry.context_type == ContextType.BEHAVIORAL_PATTERNS
            and "engagement_level" in entry.data
        ]

        if len(engagement_entries) < 5:
            return {"status": "insufficient_data", "confidence": 0.0}

        engagement_entries.sort(key=lambda e: e.timestamp)
        engagement_levels = [entry.data["engagement_level"] for entry in engagement_entries]

        # Calculate engagement statistics
        avg_engagement = np.mean(engagement_levels)
        engagement_std = np.std(engagement_levels)

        # Detect time-of-day patterns if timestamps are available
        hours = []
        for entry in engagement_entries[-20:]:  # Last 20 entries
            hours.append(entry.timestamp.hour)

        if hours:
            # Find peak engagement hours
            hour_engagement = {}
            for i, hour in enumerate(hours):
                if hour not in hour_engagement:
                    hour_engagement[hour] = []
                if i < len(engagement_levels):
                    hour_engagement[hour].append(engagement_levels[-(len(hours) - i)])

            hour_averages = {hour: np.mean(levels) for hour, levels in hour_engagement.items()}
            peak_hour = max(hour_averages.items(), key=lambda x: x[1])[0] if hour_averages else None
        else:
            peak_hour = None

        # Detect engagement trend
        if len(engagement_levels) > 5:
            recent_avg = np.mean(engagement_levels[-5:])
            earlier_avg = np.mean(engagement_levels[:5])
            trend = recent_avg - earlier_avg
        else:
            trend = 0

        return {
            "status": "detected",
            "average_engagement": avg_engagement,
            "engagement_consistency": 1.0 - min(1.0, engagement_std),
            "peak_hour": peak_hour,
            "trend": ("increasing" if trend > 0.1 else "decreasing" if trend < -0.1 else "stable"),
            "trend_magnitude": abs(trend),
            "confidence": min(1.0, len(engagement_entries) / 20.0),
        }

    def _detect_difficulty_preferences(self, context: UserContext) -> dict[str, Any]:
        """Detect preferred difficulty levels"""

        difficulty_entries = [
            entry
            for entry in context.get_all_entries()
            if "difficulty" in entry.data and "performance" in entry.data
        ]

        if len(difficulty_entries) < 5:
            return {"status": "insufficient_data", "confidence": 0.0}

        # Group by difficulty levels
        difficulty_performance = {}
        for entry in difficulty_entries:
            difficulty = round(entry.data["difficulty"], 1)  # Round to 0.1
            performance = entry.data["performance"]

            if difficulty not in difficulty_performance:
                difficulty_performance[difficulty] = []
            difficulty_performance[difficulty].append(performance)

        # Calculate average performance at each difficulty
        difficulty_averages = {
            diff: np.mean(perfs) for diff, perfs in difficulty_performance.items()
        }

        # Find optimal difficulty (best performance)
        if difficulty_averages:
            optimal_difficulty = max(difficulty_averages.items(), key=lambda x: x[1])[0]
            optimal_performance = difficulty_averages[optimal_difficulty]
        else:
            optimal_difficulty = 0.5
            optimal_performance = 0.5

        return {
            "status": "detected",
            "optimal_difficulty": optimal_difficulty,
            "optimal_performance": optimal_performance,
            "difficulty_range": (
                min(difficulty_averages.keys()),
                max(difficulty_averages.keys()),
            ),
            "difficulty_performance_map": difficulty_averages,
            "confidence": min(1.0, len(difficulty_entries) / 15.0),
        }

    def _calculate_learning_velocity(self, context: UserContext) -> dict[str, Any]:
        """Calculate learning velocity (rate of improvement)"""

        performance_entries = [
            entry
            for entry in context.get_all_entries()
            if entry.context_type == ContextType.PERFORMANCE_HISTORY and "score" in entry.data
        ]

        if len(performance_entries) < 5:
            return {"status": "insufficient_data", "velocity": 0.0, "confidence": 0.0}

        # Sort by timestamp
        performance_entries.sort(key=lambda e: e.timestamp)

        # Calculate velocity using linear regression
        n = len(performance_entries)
        scores = [entry.data["score"] for entry in performance_entries]

        # Use index as x (time proxy)
        x_values = list(range(n))
        y_values = scores

        # Linear regression: y = mx + b
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            velocity = 0.0
        else:
            velocity = (n * sum_xy - sum_x * sum_y) / denominator

        # Calculate R-squared for confidence
        y_mean = np.mean(y_values)
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)

        if ss_tot == 0:
            r_squared = 1.0 if velocity == 0 else 0.0
        else:
            y_pred = [velocity * x + (sum_y - velocity * sum_x) / n for x in x_values]
            ss_res = sum((y - y_pred) ** 2 for y, y_pred in zip(y_values, y_pred))
            r_squared = 1 - (ss_res / ss_tot)

        return {
            "status": "calculated",
            "velocity": velocity,
            "r_squared": r_squared,
            "confidence": min(1.0, r_squared * (n / 10.0)),  # More data = higher confidence
            "trend": (
                "improving" if velocity > 0.01 else "declining" if velocity < -0.01 else "stable"
            ),
            "data_points": n,
        }

    def _detect_subject_preferences(self, context: UserContext) -> dict[str, Any]:
        """Detect subject area preferences and performance"""

        subject_entries = [
            entry
            for entry in context.get_all_entries()
            if entry.subject_area and "performance" in entry.data
        ]

        if len(subject_entries) < 5:
            return {"status": "insufficient_data", "confidence": 0.0}

        # Group by subject area
        subject_performance = {}
        subject_engagement = {}

        for entry in subject_entries:
            subject = entry.subject_area
            performance = entry.data.get("performance", 0.5)
            engagement = entry.data.get("engagement", 0.5)

            if subject not in subject_performance:
                subject_performance[subject] = []
                subject_engagement[subject] = []

            subject_performance[subject].append(performance)
            subject_engagement[subject].append(engagement)

        # Calculate averages
        subject_avg_performance = {
            subj: np.mean(perfs) for subj, perfs in subject_performance.items()
        }
        subject_avg_engagement = {subj: np.mean(engs) for subj, engs in subject_engagement.items()}

        # Find preferred subjects (high engagement and performance)
        subject_scores = {}
        for subject in subject_avg_performance:
            perf = subject_avg_performance[subject]
            eng = subject_avg_engagement.get(subject, 0.5)
            subject_scores[subject] = (perf + eng) / 2

        # Sort by preference score
        preferred_subjects = sorted(subject_scores.items(), key=lambda x: x[1], reverse=True)

        return {
            "status": "detected",
            "subject_performance": subject_avg_performance,
            "subject_engagement": subject_avg_engagement,
            "preferred_subjects": [subj for subj, _ in preferred_subjects[:3]],
            "subject_rankings": preferred_subjects,
            "confidence": min(1.0, len(subject_entries) / 20.0),
        }

    def _detect_time_patterns(self, context: UserContext) -> dict[str, Any]:
        """Detect time-based learning patterns"""

        timed_entries = [
            entry
            for entry in context.get_all_entries()
            if "performance" in entry.data or "engagement" in entry.data
        ]

        if len(timed_entries) < 10:
            return {"status": "insufficient_data", "confidence": 0.0}

        # Analyze by hour of day
        hourly_performance = {}
        hourly_engagement = {}

        for entry in timed_entries:
            hour = entry.timestamp.hour

            if hour not in hourly_performance:
                hourly_performance[hour] = []
                hourly_engagement[hour] = []

            if "performance" in entry.data:
                hourly_performance[hour].append(entry.data["performance"])
            if "engagement" in entry.data:
                hourly_engagement[hour].append(entry.data["engagement"])

        # Calculate averages for hours with enough data
        hour_avg_performance = {}
        hour_avg_engagement = {}

        for hour in hourly_performance:
            if len(hourly_performance[hour]) >= 2:
                hour_avg_performance[hour] = np.mean(hourly_performance[hour])
            if len(hourly_engagement[hour]) >= 2:
                hour_avg_engagement[hour] = np.mean(hourly_engagement[hour])

        # Find peak hours
        best_performance_hour = (
            max(hour_avg_performance.items(), key=lambda x: x[1])[0]
            if hour_avg_performance
            else None
        )
        best_engagement_hour = (
            max(hour_avg_engagement.items(), key=lambda x: x[1])[0] if hour_avg_engagement else None
        )

        return {
            "status": "detected",
            "hourly_performance": hour_avg_performance,
            "hourly_engagement": hour_avg_engagement,
            "best_performance_hour": best_performance_hour,
            "best_engagement_hour": best_engagement_hour,
            "active_hours": list(hour_avg_performance.keys()),
            "confidence": min(1.0, len(timed_entries) / 30.0),
        }

    def _detect_collaboration_tendencies(self, context: UserContext) -> dict[str, Any]:
        """Detect collaboration patterns and preferences"""

        collab_entries = [
            entry
            for entry in context.get_all_entries()
            if entry.context_type == ContextType.SOCIAL_INTERACTIONS
            or "collaboration" in entry.data
        ]

        if len(collab_entries) < 3:
            return {"status": "insufficient_data", "confidence": 0.0}

        # Analyze collaboration patterns
        solo_performance = []
        group_performance = []

        for entry in collab_entries:
            if "collaboration_type" in entry.data:
                performance = entry.data.get("performance", 0.5)
                if entry.data["collaboration_type"] == "solo":
                    solo_performance.append(performance)
                elif entry.data["collaboration_type"] == "group":
                    group_performance.append(performance)

        # Calculate preferences
        prefers_collaboration = False
        collaboration_benefit = 0.0

        if solo_performance and group_performance:
            solo_avg = np.mean(solo_performance)
            group_avg = np.mean(group_performance)
            collaboration_benefit = group_avg - solo_avg
            prefers_collaboration = collaboration_benefit > 0.05  # 5% threshold

        # Analyze peer interaction frequency
        peer_interactions = sum(1 for entry in collab_entries if "peer_interaction" in entry.data)

        return {
            "status": "detected",
            "prefers_collaboration": prefers_collaboration,
            "collaboration_benefit": collaboration_benefit,
            "solo_avg_performance": (np.mean(solo_performance) if solo_performance else None),
            "group_avg_performance": (np.mean(group_performance) if group_performance else None),
            "peer_interaction_frequency": peer_interactions,
            "social_learning_tendency": (
                "high" if peer_interactions > 5 else "medium" if peer_interactions > 2 else "low"
            ),
            "confidence": min(1.0, len(collab_entries) / 10.0),
        }


class ContextCompressor:
    """Compresses and summarizes context information"""

    def __init__(self, compression_threshold: int = 50):
        self.compression_threshold = compression_threshold

    def compress_context_scope(
        self, entries: list[ContextEntry]
    ) -> tuple[list[ContextEntry], float]:
        """Compress a list of context entries"""

        if len(entries) <= self.compression_threshold:
            return entries, 1.0  # No compression needed

        # Sort by importance and recency
        sorted_entries = sorted(
            entries,
            key=lambda e: e.importance * e.recency_score * e.relevance_score,
            reverse=True,
        )

        # Keep most important entries
        keep_count = self.compression_threshold // 2
        important_entries = sorted_entries[:keep_count]

        # Compress the rest into summaries
        remaining_entries = sorted_entries[keep_count:]
        summarized_entries = self._create_summaries(remaining_entries)

        compressed_entries = important_entries + summarized_entries
        compression_ratio = len(compressed_entries) / len(entries)

        return compressed_entries, compression_ratio

    def _create_summaries(self, entries: list[ContextEntry]) -> list[ContextEntry]:
        """Create summary entries from detailed entries"""

        # Group by context type and time period
        grouped_entries = {}

        for entry in entries:
            # Create time bucket (day)
            time_bucket = entry.timestamp.date()
            key = (entry.context_type, time_bucket)

            if key not in grouped_entries:
                grouped_entries[key] = []
            grouped_entries[key].append(entry)

        summary_entries = []

        for (context_type, date), group_entries in grouped_entries.items():
            if len(group_entries) < 2:
                # Keep individual entry if only one
                summary_entries.extend(group_entries)
                continue

            # Create summary entry
            summary_data = self._summarize_entries(group_entries)

            summary_entry = ContextEntry(
                context_type=context_type,
                scope=ContextScope.SESSION,  # Summaries are session-level
                data=summary_data,
                summary=f"Summary of {len(group_entries)} {context_type.value} entries from {date}",
                timestamp=max(entry.timestamp for entry in group_entries),
                relevance_score=np.mean([entry.relevance_score for entry in group_entries]),
                confidence=np.mean([entry.confidence for entry in group_entries])
                * 0.8,  # Slightly lower confidence
                importance=max(entry.importance for entry in group_entries),
                related_entries=[entry.entry_id for entry in group_entries],
            )

            summary_entries.append(summary_entry)

        return summary_entries

    def _summarize_entries(self, entries: list[ContextEntry]) -> dict[str, Any]:
        """Summarize a group of similar entries"""

        summary = {
            "entry_count": len(entries),
            "time_span": (
                min(e.timestamp for e in entries).isoformat(),
                max(e.timestamp for e in entries).isoformat(),
            ),
            "compressed": True,
        }

        # Aggregate numeric values
        numeric_fields = ["performance", "engagement", "score", "difficulty"]

        for field in numeric_fields:
            values = []
            for entry in entries:
                if field in entry.data and isinstance(entry.data[field], (int, float)):
                    values.append(entry.data[field])

            if values:
                summary[f"{field}_avg"] = np.mean(values)
                summary[f"{field}_min"] = min(values)
                summary[f"{field}_max"] = max(values)
                summary[f"{field}_count"] = len(values)

        # Aggregate categorical values
        categorical_fields = ["subject_area", "learning_objective", "action_type"]

        for field in categorical_fields:
            values = []
            for entry in entries:
                if field in entry.data and entry.data[field]:
                    values.append(entry.data[field])

            if values:
                # Count occurrences
                value_counts = {}
                for value in values:
                    value_counts[value] = value_counts.get(value, 0) + 1

                summary[f"{field}_distribution"] = value_counts
                summary[f"{field}_most_common"] = max(value_counts.items(), key=lambda x: x[1])[0]

        # Extract common keywords
        all_keywords = []
        for entry in entries:
            all_keywords.extend(entry.keywords)

        if all_keywords:
            keyword_counts = {}
            for keyword in all_keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

            # Top keywords
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            summary["top_keywords"] = [kw for kw, _ in top_keywords]

        return summary


class ContextTracker:
    """
    Advanced context tracking system for educational personalization.

    The ContextTracker maintains comprehensive user context across multiple
    time scales and provides intelligent context management including
    compression, pattern recognition, and adaptive personalization.
    """

    def __init__(
        self,
        window_size: int = 50,
        session_timeout: float = 1800.0,  # 30 minutes
        compression_enabled: bool = True,
        retention_days: int = 30,
    ):
        """
        Initialize ContextTracker.

        Args:
            window_size: Size of context windows
            session_timeout: Session timeout in seconds
            compression_enabled: Whether to compress old context
            retention_days: Days to retain context data
        """
        self.window_size = window_size
        self.session_timeout = session_timeout
        self.compression_enabled = compression_enabled
        self.retention_days = retention_days

        # Context storage
        self.user_contexts: dict[str, UserContext] = {}
        self.active_sessions: dict[str, str] = {}  # user_id -> session_id

        # Pattern recognition and compression
        self.pattern_recognizer = LearningPatternRecognizer()
        self.compressor = ContextCompressor(compression_threshold=window_size)

        # Context statistics
        self.context_stats = {
            "total_updates": 0,
            "compression_events": 0,
            "pattern_detections": 0,
            "session_count": 0,
        }

        # Persistence - use environment-aware path for Docker compatibility
        data_dir = os.environ.get("DATA_DIR", "/tmp" if os.path.exists("/tmp") else "data")
        self.persistence_path = Path(data_dir) / "context_tracker"
        try:
            self.persistence_path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fallback to temp directory if permission denied
            self.persistence_path = Path("/tmp/context_tracker")
            self.persistence_path.mkdir(parents=True, exist_ok=True)

        # Cleanup scheduler
        self.last_cleanup = datetime.now()
        self.cleanup_interval = timedelta(hours=1)

        logger.info(f"ContextTracker initialized with window_size={window_size}")

    async def update_context(self, update_data: dict[str, Any]):
        """
        Update user context with new information.

        Args:
            update_data: Dictionary containing context update information
        """
        try:
            # Extract update components
            user_id = update_data.get("state", {}).get("student_id")
            if not user_id:
                logger.warning("No user ID found in context update")
                return

            # Get or create user context
            user_context = await self._get_or_create_user_context(user_id)

            # Create context entries from update data
            context_entries = await self._create_context_entries(update_data)

            # Add entries to appropriate scopes
            for entry in context_entries:
                await self._add_context_entry(user_context, entry)

            # Update learning patterns
            await self._update_learning_patterns(user_context)

            # Trigger compression if needed
            if self.compression_enabled:
                await self._check_and_compress_context(user_context)

            # Update context metadata
            user_context.last_activity = datetime.now()
            user_context.last_updated = datetime.now()
            user_context.session_duration = (
                user_context.last_activity - user_context.session_start
            ).total_seconds()

            # Update statistics
            self.context_stats["total_updates"] += 1

            # Periodic cleanup
            await self._periodic_cleanup()

            logger.debug(f"Context updated for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to update context: {e}")

    async def get_current_context(self, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get current context for a user or all users"""

        if user_id:
            if user_id not in self.user_contexts:
                return {}

            context = self.user_contexts[user_id]
            return {
                "user_id": user_id,
                "session_id": context.session_id,
                "learning_profile": {
                    "learning_style": context.learning_style,
                    "preferred_difficulty": context.preferred_difficulty,
                    "strengths": context.strengths,
                    "areas_for_improvement": context.areas_for_improvement,
                },
                "current_session": {
                    "duration": context.session_duration,
                    "last_activity": context.last_activity.isoformat(),
                    "engagement_patterns": context.engagement_patterns,
                },
                "relevant_context": [
                    entry.to_dict() for entry in context.get_relevant_context()[:10]
                ],
            }
        else:
            # Return summary for all users
            return {
                "active_users": len(self.user_contexts),
                "active_sessions": len(self.active_sessions),
                "total_context_entries": sum(
                    len(ctx.get_all_entries()) for ctx in self.user_contexts.values()
                ),
            }

    async def get_context_summary(self) -> dict[str, Any]:
        """Get summary of context tracking system"""

        return {
            "system_status": {
                "active_users": len(self.user_contexts),
                "active_sessions": len(self.active_sessions),
                "compression_enabled": self.compression_enabled,
                "retention_days": self.retention_days,
            },
            "statistics": self.context_stats.copy(),
            "recent_activity": {
                "last_update": max(
                    [ctx.last_updated for ctx in self.user_contexts.values()],
                    default=datetime.now(),
                ).isoformat(),
                "last_cleanup": self.last_cleanup.isoformat(),
            },
        }

    async def get_learning_patterns(self, user_id: str) -> Optional[dict[str, Any]]:
        """Get detected learning patterns for a user"""

        if user_id not in self.user_contexts:
            return None

        context = self.user_contexts[user_id]
        patterns = self.pattern_recognizer.analyze_patterns(context)

        return {
            "user_id": user_id,
            "patterns": patterns,
            "pattern_count": sum(
                1 for p in patterns.values() if p and p.get("status") == "detected"
            ),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    async def _get_or_create_user_context(self, user_id: str) -> UserContext:
        """Get existing or create new user context"""

        if user_id in self.user_contexts:
            context = self.user_contexts[user_id]

            # Check if session has expired
            if (datetime.now() - context.last_activity).total_seconds() > self.session_timeout:
                # Start new session
                context.session_id = str(uuid.uuid4())
                context.session_start = datetime.now()
                context.session_duration = 0.0
                self.context_stats["session_count"] += 1

            return context

        # Create new user context
        session_id = str(uuid.uuid4())
        context = UserContext(user_id=user_id, session_id=session_id)

        self.user_contexts[user_id] = context
        self.active_sessions[user_id] = session_id
        self.context_stats["session_count"] += 1

        # Try to load persistent context
        await self._load_persistent_context(context)

        logger.info(f"Created new context for user {user_id}")
        return context

    async def _create_context_entries(self, update_data: dict[str, Any]) -> list[ContextEntry]:
        """Create context entries from update data"""

        entries = []

        # Extract state information
        state = update_data.get("state")
        if state:
            state_entry = ContextEntry(
                context_type=ContextType.LEARNING_STATE,
                scope=ContextScope.IMMEDIATE,
                data={
                    "state_type": (
                        state.state_type.value if hasattr(state, "state_type") else "unknown"
                    ),
                    "subject_area": state.subject_area,
                    "grade_level": state.grade_level,
                    "learning_objective": state.learning_objective,
                    "confidence": state.confidence,
                    "quality": (state.quality.value if hasattr(state, "quality") else "unknown"),
                },
                summary=f"Learning state in {state.subject_area or 'unknown subject'}",
                keywords=[state.subject_area] if state.subject_area else [],
                subject_area=state.subject_area,
                learning_objective=state.learning_objective,
                validity_period=timedelta(minutes=30),
            )
            entries.append(state_entry)

        # Extract action information
        action = update_data.get("action")
        if action:
            action_entry = ContextEntry(
                context_type=ContextType.BEHAVIORAL_PATTERNS,
                scope=ContextScope.IMMEDIATE,
                data={
                    "action_type": getattr(action, "type", "unknown"),
                    "parameters": getattr(action, "parameters", {}),
                    "priority": getattr(action, "priority", 0.5),
                    "difficulty": getattr(action, "difficulty_level", 0.5),
                },
                summary=f"Action: {getattr(action, 'type', 'unknown')}",
                keywords=[getattr(action, "type", "unknown")],
                validity_period=timedelta(hours=1),
            )
            entries.append(action_entry)

        # Extract result information
        result = update_data.get("result")
        if result:
            performance_score = 1.0 if result.success else 0.0

            performance_entry = ContextEntry(
                context_type=ContextType.PERFORMANCE_HISTORY,
                scope=ContextScope.SESSION,
                data={
                    "success": result.success,
                    "performance": performance_score,
                    "execution_time": result.execution_time,
                    "error_message": result.error_message,
                },
                summary=f"Performance: {'Success' if result.success else 'Failed'}",
                keywords=["performance", "success" if result.success else "failure"],
                relevance_score=0.9,  # Performance is highly relevant
                importance=0.8,
                validity_period=timedelta(days=7),
            )
            entries.append(performance_entry)

        # Extract reward information
        rewards = update_data.get("rewards")
        if rewards:
            reward_entry = ContextEntry(
                context_type=ContextType.PERFORMANCE_HISTORY,
                scope=ContextScope.SESSION,
                data={
                    "total_reward": rewards.total_reward,
                    "dimension_breakdown": rewards.dimension_breakdown,
                    "learning_gains": rewards.learning_gains,
                    "confidence": rewards.confidence,
                },
                summary=f"Reward: {rewards.total_reward:.2f}",
                keywords=["reward", "learning_gains"],
                relevance_score=0.8,
                importance=0.7,
                validity_period=timedelta(days=14),
            )
            entries.append(reward_entry)

        # Extract environmental context
        cycle_info = update_data.get("cycle")
        if cycle_info:
            env_entry = ContextEntry(
                context_type=ContextType.ENVIRONMENTAL,
                scope=ContextScope.SESSION,
                data={
                    "cycle_count": cycle_info,
                    "timestamp": datetime.now().isoformat(),
                },
                summary=f"Learning cycle {cycle_info}",
                keywords=["cycle", "session"],
                validity_period=timedelta(hours=4),
            )
            entries.append(env_entry)

        return entries

    async def _add_context_entry(self, user_context: UserContext, entry: ContextEntry):
        """Add a context entry to the appropriate scope"""

        # Set user-specific information
        entry.related_entries = []  # Will be populated by pattern analysis

        # Add to appropriate scope
        if entry.scope == ContextScope.IMMEDIATE:
            user_context.immediate_context.append(entry)
            # Keep only recent immediate context
            if len(user_context.immediate_context) > self.window_size // 4:
                user_context.immediate_context = user_context.immediate_context[
                    -(self.window_size // 4) :
                ]

        elif entry.scope == ContextScope.SESSION:
            user_context.session_context.append(entry)

        elif entry.scope == ContextScope.SHORT_TERM:
            user_context.short_term_context.append(entry)

        elif entry.scope == ContextScope.LONG_TERM:
            user_context.long_term_context.append(entry)

        elif entry.scope == ContextScope.PERSISTENT:
            user_context.persistent_context.append(entry)

        # Update derived information
        await self._update_derived_context(user_context, entry)

    async def _update_derived_context(self, user_context: UserContext, new_entry: ContextEntry):
        """Update derived context information from new entry"""

        # Update learning style inference
        if new_entry.context_type == ContextType.BEHAVIORAL_PATTERNS:
            action_type = new_entry.data.get("action_type", "")
            if "visual" in action_type or "generate_content" in action_type:
                if user_context.learning_style == "unknown":
                    user_context.learning_style = "visual"
            elif "quiz" in action_type or "assessment" in action_type:
                if user_context.learning_style == "unknown":
                    user_context.learning_style = "analytical"

        # Update preferred difficulty
        if "difficulty" in new_entry.data and "performance" in new_entry.data:
            new_entry.data["difficulty"]
            performance = new_entry.data["performance"]

            # Simple adaptive adjustment
            if performance > 0.8:
                user_context.preferred_difficulty = min(
                    1.0, user_context.preferred_difficulty + 0.02
                )
            elif performance < 0.6:
                user_context.preferred_difficulty = max(
                    0.2, user_context.preferred_difficulty - 0.02
                )

        # Update subject tracking
        if new_entry.subject_area and new_entry.subject_area not in user_context.dominant_subjects:
            user_context.dominant_subjects.append(new_entry.subject_area)
            if len(user_context.dominant_subjects) > 5:
                user_context.dominant_subjects = user_context.dominant_subjects[-5:]

        # Update engagement patterns
        if new_entry.context_type == ContextType.BEHAVIORAL_PATTERNS:
            engagement_indicators = [
                "time_on_task",
                "interaction_frequency",
                "exploration_behavior",
            ]
            for indicator in engagement_indicators:
                if indicator in new_entry.data:
                    if indicator not in user_context.engagement_patterns:
                        user_context.engagement_patterns[indicator] = deque(maxlen=20)
                    user_context.engagement_patterns[indicator].append(new_entry.data[indicator])

        # Update performance trends
        if new_entry.context_type == ContextType.PERFORMANCE_HISTORY:
            subject = new_entry.subject_area or "general"
            if subject not in user_context.performance_trends:
                user_context.performance_trends[subject] = []

            performance = new_entry.data.get("performance", new_entry.data.get("total_reward", 0.5))
            user_context.performance_trends[subject].append(performance)

            # Keep only recent trends
            if len(user_context.performance_trends[subject]) > 20:
                user_context.performance_trends[subject] = user_context.performance_trends[subject][
                    -20:
                ]

    async def _update_learning_patterns(self, user_context: UserContext):
        """Update learning patterns for the user"""

        try:
            patterns = self.pattern_recognizer.analyze_patterns(user_context)

            # Update user context based on detected patterns
            for pattern_name, pattern_data in patterns.items():
                if not pattern_data or pattern_data.get("status") != "detected":
                    continue

                if pattern_name == "learning_velocity":
                    user_context.learning_velocity = pattern_data.get("velocity", 0.0)

                elif pattern_name == "difficulty_preferences":
                    optimal_diff = pattern_data.get("optimal_difficulty")
                    if optimal_diff is not None:
                        # Gradual adjustment toward optimal
                        adjustment = (optimal_diff - user_context.preferred_difficulty) * 0.1
                        user_context.preferred_difficulty += adjustment

                elif pattern_name == "subject_preferences":
                    preferred_subjects = pattern_data.get("preferred_subjects", [])
                    if preferred_subjects:
                        user_context.dominant_subjects = preferred_subjects[:3]

            self.context_stats["pattern_detections"] += 1

        except Exception as e:
            logger.error(f"Failed to update learning patterns: {e}")

    async def _check_and_compress_context(self, user_context: UserContext):
        """Check if context compression is needed and perform it"""

        total_entries = len(user_context.get_all_entries())

        if total_entries <= self.window_size * 2:
            return  # No compression needed

        # Compress different scopes
        scopes_to_compress = [
            ("session_context", user_context.session_context),
            ("short_term_context", user_context.short_term_context),
            ("long_term_context", user_context.long_term_context),
        ]

        total_compression_ratio = 1.0

        for scope_name, scope_entries in scopes_to_compress:
            if len(scope_entries) > self.window_size:
                compressed_entries, compression_ratio = self.compressor.compress_context_scope(
                    scope_entries
                )

                # Update the scope with compressed entries
                if scope_name == "session_context":
                    user_context.session_context = compressed_entries
                elif scope_name == "short_term_context":
                    user_context.short_term_context = compressed_entries
                elif scope_name == "long_term_context":
                    user_context.long_term_context = compressed_entries

                total_compression_ratio *= compression_ratio

        user_context.compression_ratio = total_compression_ratio
        self.context_stats["compression_events"] += 1

        logger.debug(
            f"Context compressed for user {user_context.user_id}, ratio: {total_compression_ratio:.2f}"
        )

    async def _periodic_cleanup(self):
        """Perform periodic cleanup of expired context"""

        if datetime.now() - self.last_cleanup < self.cleanup_interval:
            return

        cleanup_before = datetime.now() - timedelta(days=self.retention_days)

        for user_id, context in list(self.user_contexts.items()):
            # Remove expired entries
            for scope_entries in [
                context.immediate_context,
                context.session_context,
                context.short_term_context,
                context.long_term_context,
            ]:
                # Remove entries older than retention period
                scope_entries[:] = [
                    entry
                    for entry in scope_entries
                    if entry.timestamp > cleanup_before and not entry.is_expired
                ]

            # Remove inactive user contexts
            if (datetime.now() - context.last_activity).total_seconds() > self.session_timeout * 3:
                # Move to long-term storage before removing
                await self._save_persistent_context(context)
                del self.user_contexts[user_id]
                if user_id in self.active_sessions:
                    del self.active_sessions[user_id]

        self.last_cleanup = datetime.now()
        logger.debug("Periodic cleanup completed")

    async def _load_persistent_context(self, context: UserContext):
        """Load persistent context for a user"""

        try:
            persistent_file = self.persistence_path / f"{context.user_id}_persistent.json.gz"

            if persistent_file.exists():
                with gzip.open(persistent_file, "rt", encoding="utf-8") as f:
                    persistent_data = json.load(f)

                # Restore persistent context entries
                context.persistent_context = persistent_data.get("persistent_context", [])
                context.learning_style = persistent_data.get("learning_style", "unknown")
                context.preferred_difficulty = persistent_data.get("preferred_difficulty", 0.5)
                context.dominant_subjects = persistent_data.get("dominant_subjects", [])
                context.strengths = persistent_data.get("strengths", [])
                context.areas_for_improvement = persistent_data.get("areas_for_improvement", [])

                logger.debug(f"Loaded persistent context for user {context.user_id}")

        except Exception as e:
            logger.error(f"Failed to load persistent context for {context.user_id}: {e}")

    async def _save_persistent_context(self, context: UserContext):
        """Save persistent context for a user"""

        try:
            persistent_data = {
                "user_id": context.user_id,
                "persistent_context": context.persistent_context,
                "learning_style": context.learning_style,
                "preferred_difficulty": context.preferred_difficulty,
                "dominant_subjects": context.dominant_subjects,
                "strengths": context.strengths,
                "areas_for_improvement": context.areas_for_improvement,
                "last_saved": datetime.now().isoformat(),
            }

            persistent_file = self.persistence_path / f"{context.user_id}_persistent.json.gz"

            with gzip.open(persistent_file, "wt", encoding="utf-8") as f:
                json.dump(persistent_data, f, indent=2, default=str)

            logger.debug(f"Saved persistent context for user {context.user_id}")

        except Exception as e:
            logger.error(f"Failed to save persistent context for {context.user_id}: {e}")

    async def get_status(self) -> dict[str, Any]:
        """Get comprehensive status of ContextTracker"""

        context_distribution = {}
        for user_id, context in self.user_contexts.items():
            entry_count = len(context.get_all_entries())
            context_distribution[user_id] = {
                "total_entries": entry_count,
                "immediate": len(context.immediate_context),
                "session": len(context.session_context),
                "short_term": len(context.short_term_context),
                "long_term": len(context.long_term_context),
                "persistent": len(context.persistent_context),
                "compression_ratio": context.compression_ratio,
                "session_duration": context.session_duration,
            }

        return {
            "system_status": {
                "active_users": len(self.user_contexts),
                "active_sessions": len(self.active_sessions),
                "total_context_entries": sum(
                    len(ctx.get_all_entries()) for ctx in self.user_contexts.values()
                ),
            },
            "configuration": {
                "window_size": self.window_size,
                "session_timeout": self.session_timeout,
                "compression_enabled": self.compression_enabled,
                "retention_days": self.retention_days,
            },
            "statistics": self.context_stats.copy(),
            "context_distribution": context_distribution,
            "cleanup_info": {
                "last_cleanup": self.last_cleanup.isoformat(),
                "cleanup_interval_hours": self.cleanup_interval.total_seconds() / 3600,
            },
        }

    async def reset(self):
        """Reset ContextTracker to initial state"""

        logger.info("Resetting ContextTracker")

        # Save persistent context for all users before reset
        for context in self.user_contexts.values():
            await self._save_persistent_context(context)

        # Clear all runtime context
        self.user_contexts.clear()
        self.active_sessions.clear()

        # Reset statistics
        self.context_stats = {
            "total_updates": 0,
            "compression_events": 0,
            "pattern_detections": 0,
            "session_count": 0,
        }

        # Reset cleanup timer
        self.last_cleanup = datetime.now()

        logger.info("ContextTracker reset completed")
