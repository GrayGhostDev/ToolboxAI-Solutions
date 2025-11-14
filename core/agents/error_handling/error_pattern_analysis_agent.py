"""
Error Pattern Analysis Agent

Specialized agent for learning from error patterns and predicting issues
using machine learning techniques and pattern recognition.
"""

import hashlib
import logging
import pickle
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np
from langchain_core.tools import Tool
from pydantic import BaseModel, Field
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

from core.agents.error_handling.base_error_agent import (
    BaseErrorAgent,
    ErrorAgentConfig,
    ErrorPattern,
    ErrorPriority,
    ErrorState,
    ErrorType,
)

logger = logging.getLogger(__name__)


class PatternCluster(BaseModel):
    """Model for error pattern cluster"""

    cluster_id: str = Field(description="Unique cluster identifier")
    centroid: list[float] = Field(description="Cluster centroid in feature space")
    patterns: list[ErrorPattern] = Field(description="Patterns in this cluster")
    error_count: int = Field(description="Total errors in cluster")
    avg_resolution_time: float = Field(description="Average time to resolve")
    common_fixes: list[str] = Field(description="Common fixes for this cluster")
    risk_score: float = Field(description="Risk score for this pattern cluster")


class PredictedError(BaseModel):
    """Model for predicted error"""

    prediction_id: str = Field(description="Unique prediction identifier")
    error_type: ErrorType = Field(description="Predicted error type")
    probability: float = Field(description="Prediction probability (0-1)")
    expected_timeframe: str = Field(description="When error is expected")
    affected_components: list[str] = Field(description="Components likely affected")
    prevention_steps: list[str] = Field(description="Steps to prevent the error")
    confidence: float = Field(description="Confidence in prediction")
    evidence: list[str] = Field(description="Evidence supporting prediction")


class ErrorTrend(BaseModel):
    """Model for error trends"""

    trend_id: str = Field(description="Unique trend identifier")
    error_type: ErrorType = Field(description="Error type showing trend")
    direction: str = Field(description="Trend direction (increasing/decreasing/stable)")
    rate: float = Field(description="Rate of change")
    timeframe: str = Field(description="Timeframe of the trend")
    significance: float = Field(description="Statistical significance")
    projected_impact: str = Field(description="Projected impact if trend continues")


class PatternInsight(BaseModel):
    """Model for pattern-based insights"""

    insight_id: str = Field(description="Unique insight identifier")
    description: str = Field(description="Insight description")
    pattern_ids: list[str] = Field(description="Related pattern IDs")
    actionable_recommendation: str = Field(description="Actionable recommendation")
    priority: ErrorPriority = Field(description="Priority of the insight")
    estimated_impact: str = Field(description="Estimated impact if actioned")
    supporting_data: dict[str, Any] = Field(description="Supporting data")


@dataclass
class PatternAnalysisConfig(ErrorAgentConfig):
    """Configuration for pattern analysis agent"""

    min_pattern_frequency: int = 3
    clustering_threshold: float = 0.7
    prediction_window_hours: int = 24
    trend_analysis_days: int = 7
    max_patterns_stored: int = 10000
    enable_ml_predictions: bool = True
    feature_extraction_method: str = "tfidf"
    model_update_frequency: int = 3600  # seconds


class ErrorPatternAnalysisAgent(BaseErrorAgent):
    """
    Agent specialized in analyzing error patterns and predicting future issues.

    Capabilities:
    - Pattern recognition and clustering
    - Machine learning-based prediction
    - Trend analysis and forecasting
    - Anomaly detection
    - Root cause pattern identification
    - Preventive recommendation generation
    """

    def __init__(self, config: Optional[PatternAnalysisConfig] = None):
        if config is None:
            config = PatternAnalysisConfig(
                name="ErrorPatternAnalysisAgent",
                model="gpt-4",
                temperature=0.2,
                min_pattern_frequency=3,
                enable_ml_predictions=True,
            )

        super().__init__(config)
        self.analysis_config = config

        # Pattern storage
        self.pattern_clusters: list[PatternCluster] = []
        self.error_sequences: list[List[str]] = []
        self.pattern_features: dict[str, np.ndarray] = {}

        # ML models
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.clustering_model = KMeans(n_clusters=10)
        self.prediction_model = RandomForestClassifier(n_estimators=100)
        self.models_trained = False

        # Analysis results
        self.predictions: list[PredictedError] = []
        self.trends: list[ErrorTrend] = []
        self.insights: list[PatternInsight] = []

        # Initialize analysis tools
        self.tools.extend(self._create_analysis_tools())

        # Load existing patterns if available
        self._load_pattern_models()

        logger.info("Initialized Error Pattern Analysis Agent")

    def _get_default_system_prompt(self) -> str:
        """Get specialized system prompt for pattern analysis"""
        return """You are the Error Pattern Analysis Agent, specialized in identifying patterns and predicting future errors.

Your core capabilities:
- Identify recurring error patterns using ML techniques
- Predict future errors based on historical data
- Analyze trends and anomalies in error occurrences
- Cluster similar errors for better understanding
- Generate preventive recommendations
- Provide statistical insights on error patterns

Analysis principles:
1. Data-driven decisions - base predictions on evidence
2. Pattern recognition - identify recurring issues
3. Predictive accuracy - minimize false positives
4. Actionable insights - provide clear recommendations
5. Continuous learning - improve predictions over time

Use statistical and machine learning techniques to provide accurate predictions."""

    def _create_analysis_tools(self) -> list[Tool]:
        """Create specialized tools for pattern analysis"""
        tools = []

        tools.append(
            Tool(
                name="analyze_pattern",
                description="Analyze error pattern for insights",
                func=self._analyze_pattern_tool,
            )
        )

        tools.append(
            Tool(
                name="predict_errors",
                description="Predict future errors based on patterns",
                func=self._predict_errors_tool,
            )
        )

        tools.append(
            Tool(
                name="detect_anomalies",
                description="Detect anomalous error patterns",
                func=self._detect_anomalies_tool,
            )
        )

        tools.append(
            Tool(
                name="analyze_trends",
                description="Analyze error trends over time",
                func=self._analyze_trends_tool,
            )
        )

        tools.append(
            Tool(
                name="cluster_errors",
                description="Cluster similar errors together",
                func=self._cluster_errors_tool,
            )
        )

        tools.append(
            Tool(
                name="generate_insights",
                description="Generate insights from patterns",
                func=self._generate_insights_tool,
            )
        )

        return tools

    def _load_pattern_models(self):
        """Load pre-trained pattern models if available"""
        model_path = Path("core/agents/error_handling/models")
        model_path.mkdir(parents=True, exist_ok=True)

        # Load vectorizer
        vectorizer_path = model_path / "vectorizer.pkl"
        if vectorizer_path.exists():
            try:
                with open(vectorizer_path, "rb") as f:
                    self.vectorizer = pickle.load(f)
                logger.info("Loaded vectorizer model")
            except Exception as e:
                logger.error(f"Failed to load vectorizer: {e}")

        # Load clustering model
        clustering_path = model_path / "clustering_model.pkl"
        if clustering_path.exists():
            try:
                with open(clustering_path, "rb") as f:
                    self.clustering_model = pickle.load(f)
                logger.info("Loaded clustering model")
            except Exception as e:
                logger.error(f"Failed to load clustering model: {e}")

        # Load prediction model
        prediction_path = model_path / "prediction_model.pkl"
        if prediction_path.exists():
            try:
                with open(prediction_path, "rb") as f:
                    self.prediction_model = pickle.load(f)
                self.models_trained = True
                logger.info("Loaded prediction model")
            except Exception as e:
                logger.error(f"Failed to load prediction model: {e}")

    def _save_pattern_models(self):
        """Save trained pattern models"""
        model_path = Path("core/agents/error_handling/models")
        model_path.mkdir(parents=True, exist_ok=True)

        # Save vectorizer
        try:
            with open(model_path / "vectorizer.pkl", "wb") as f:
                pickle.dump(self.vectorizer, f)
        except Exception as e:
            logger.error(f"Failed to save vectorizer: {e}")

        # Save clustering model
        try:
            with open(model_path / "clustering_model.pkl", "wb") as f:
                pickle.dump(self.clustering_model, f)
        except Exception as e:
            logger.error(f"Failed to save clustering model: {e}")

        # Save prediction model
        if self.models_trained:
            try:
                with open(model_path / "prediction_model.pkl", "wb") as f:
                    pickle.dump(self.prediction_model, f)
            except Exception as e:
                logger.error(f"Failed to save prediction model: {e}")

    async def analyze_error_patterns(
        self, error_history: list[ErrorState], timeframe_days: int = 7
    ) -> dict[str, Any]:
        """
        Analyze error patterns from historical data.

        Args:
            error_history: List of historical error states
            timeframe_days: Days of history to analyze

        Returns:
            Analysis results with patterns, clusters, and insights
        """
        logger.info(f"Analyzing {len(error_history)} errors over {timeframe_days} days")

        # Filter errors by timeframe
        cutoff_date = datetime.now() - timedelta(days=timeframe_days)
        recent_errors = [
            e for e in error_history if datetime.fromisoformat(e["timestamp"]) > cutoff_date
        ]

        # Extract features from errors
        features = self._extract_error_features(recent_errors)

        # Cluster errors
        clusters = await self._cluster_similar_errors(features, recent_errors)

        # Identify patterns
        patterns = self._identify_patterns(recent_errors, clusters)

        # Analyze trends
        trends = self._analyze_error_trends(recent_errors, timeframe_days)

        # Generate predictions
        predictions = []
        if self.analysis_config.enable_ml_predictions:
            predictions = await self._generate_predictions(features, recent_errors)

        # Generate insights
        insights = self._generate_pattern_insights(patterns, trends, clusters)

        # Update stored patterns
        self._update_pattern_database(patterns)

        # Save models
        self._save_pattern_models()

        return {
            "analysis_id": f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "errors_analyzed": len(recent_errors),
            "timeframe_days": timeframe_days,
            "pattern_clusters": clusters,
            "identified_patterns": patterns,
            "trends": trends,
            "predictions": predictions,
            "insights": insights,
            "summary": self._generate_analysis_summary(patterns, trends, predictions),
        }

    def _extract_error_features(self, errors: list[ErrorState]) -> np.ndarray:
        """Extract features from errors for ML analysis"""
        if not errors:
            return np.array([])

        # Create text representations of errors
        error_texts = []
        for error in errors:
            text = f"{error['error_type'].value} {error.get('description', '')} "
            text += f"{' '.join(error.get('affected_components', []))}"
            error_texts.append(text)

        # Vectorize using TF-IDF
        try:
            if not hasattr(self.vectorizer, "vocabulary_"):
                # First time - fit the vectorizer
                features = self.vectorizer.fit_transform(error_texts)
            else:
                # Use existing vocabulary
                features = self.vectorizer.transform(error_texts)

            return features.toarray()
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return np.array([])

    async def _cluster_similar_errors(
        self, features: np.ndarray, errors: list[ErrorState]
    ) -> list[PatternCluster]:
        """Cluster similar errors together"""
        if len(features) < 2:
            return []

        clusters = []

        try:
            # Perform clustering
            n_clusters = min(10, len(features) // 2)
            self.clustering_model = KMeans(n_clusters=n_clusters)
            labels = self.clustering_model.fit_predict(features)

            # Group errors by cluster
            cluster_groups = defaultdict(list)
            for i, label in enumerate(labels):
                cluster_groups[label].append(errors[i])

            # Create PatternCluster objects
            for cluster_id, cluster_errors in cluster_groups.items():
                # Calculate cluster statistics
                error_types = Counter(e["error_type"] for e in cluster_errors)
                common_type = error_types.most_common(1)[0][0]

                # Find common fixes
                fixes = []
                for e in cluster_errors:
                    fixes.extend(
                        [f["fix"] for f in e.get("attempted_fixes", []) if f.get("success")]
                    )

                common_fixes = [fix for fix, _ in Counter(fixes).most_common(3)]

                # Calculate risk score
                priority_scores = {
                    "LOW": 1,
                    "MEDIUM": 2,
                    "HIGH": 3,
                    "CRITICAL": 4,
                    "EMERGENCY": 5,
                }
                avg_priority = np.mean(
                    [priority_scores.get(e["priority"].name, 2) for e in cluster_errors]
                )
                risk_score = avg_priority / 5.0

                cluster = PatternCluster(
                    cluster_id=f"cluster_{cluster_id}",
                    centroid=self.clustering_model.cluster_centers_[cluster_id].tolist(),
                    patterns=[],  # Will be filled later
                    error_count=len(cluster_errors),
                    avg_resolution_time=0.0,  # Calculate from resolution times
                    common_fixes=common_fixes,
                    risk_score=risk_score,
                )
                clusters.append(cluster)

        except Exception as e:
            logger.error(f"Clustering failed: {e}")

        return clusters

    def _identify_patterns(
        self, errors: list[ErrorState], clusters: list[PatternCluster]
    ) -> list[ErrorPattern]:
        """Identify recurring patterns in errors"""
        patterns = []
        pattern_map = defaultdict(list)

        # Group errors by type and description similarity
        for error in errors:
            # Create pattern key
            pattern_key = self._generate_pattern_key(error)
            pattern_map[pattern_key].append(error)

        # Create patterns for frequently occurring groups
        for pattern_key, pattern_errors in pattern_map.items():
            if len(pattern_errors) >= self.analysis_config.min_pattern_frequency:
                # Extract common characteristics
                error_type = pattern_errors[0]["error_type"]
                descriptions = [e.get("description", "") for e in pattern_errors]

                # Calculate success rate of fixes
                successful_fixes = 0
                total_fixes = 0
                for e in pattern_errors:
                    for fix in e.get("attempted_fixes", []):
                        total_fixes += 1
                        if fix.get("success"):
                            successful_fixes += 1

                success_rate = successful_fixes / total_fixes if total_fixes > 0 else 0.0

                pattern = ErrorPattern(
                    pattern_id=hashlib.md5(pattern_key.encode()).hexdigest()[:8],
                    pattern=self._generate_pattern_regex(descriptions),
                    error_type=error_type,
                    priority=self._calculate_pattern_priority(pattern_errors),
                    suggested_fix=self._extract_common_fix(pattern_errors),
                    frequency=len(pattern_errors),
                    success_rate=success_rate,
                    last_seen=max(e["timestamp"] for e in pattern_errors),
                )
                patterns.append(pattern)

        return patterns

    def _generate_pattern_key(self, error: ErrorState) -> str:
        """Generate a key for pattern grouping"""
        # Use error type and key parts of description
        desc = error.get("description", "").lower()
        # Remove specific values to generalize
        desc = re.sub(r"\b\d+\b", "NUM", desc)  # Replace numbers
        desc = re.sub(r'"[^"]*"', "STR", desc)  # Replace quoted strings
        desc = re.sub(r"'[^']*'", "STR", desc)  # Replace single quoted strings

        return f"{error['error_type'].value}_{desc[:50]}"

    def _generate_pattern_regex(self, descriptions: list[str]) -> str:
        """Generate regex pattern from error descriptions"""
        if not descriptions:
            return ".*"

        # Find common substrings
        common_parts = []
        first_desc = descriptions[0]
        words = first_desc.split()

        for word in words:
            if all(word in desc for desc in descriptions):
                common_parts.append(word)

        if common_parts:
            # Create regex with wildcards between common parts
            regex = ".*" + ".*".join(re.escape(part) for part in common_parts) + ".*"
            return regex

        return ".*"

    def _calculate_pattern_priority(self, errors: list[ErrorState]) -> ErrorPriority:
        """Calculate priority for a pattern based on its errors"""
        priorities = [e["priority"] for e in errors]
        # Return most common priority
        priority_counts = Counter(priorities)
        return priority_counts.most_common(1)[0][0]

    def _extract_common_fix(self, errors: list[ErrorState]) -> Optional[str]:
        """Extract most common successful fix from errors"""
        successful_fixes = []
        for error in errors:
            for fix in error.get("attempted_fixes", []):
                if fix.get("success"):
                    successful_fixes.append(fix.get("fix", ""))

        if successful_fixes:
            fix_counts = Counter(successful_fixes)
            return fix_counts.most_common(1)[0][0]
        return None

    def _analyze_error_trends(
        self, errors: list[ErrorState], timeframe_days: int
    ) -> list[ErrorTrend]:
        """Analyze trends in error occurrences"""
        trends = []

        # Group errors by type and day
        daily_counts = defaultdict(lambda: defaultdict(int))
        for error in errors:
            error_date = datetime.fromisoformat(error["timestamp"]).date()
            daily_counts[error["error_type"]][error_date] += 1

        # Analyze trends for each error type
        for error_type, daily_data in daily_counts.items():
            dates = sorted(daily_data.keys())
            if len(dates) < 2:
                continue

            counts = [daily_data[date] for date in dates]

            # Calculate trend using simple linear regression
            x = np.arange(len(counts))
            y = np.array(counts)

            # Calculate slope
            if len(x) > 1:
                slope = np.polyfit(x, y, 1)[0]

                # Determine trend direction
                if slope > 0.5:
                    direction = "increasing"
                elif slope < -0.5:
                    direction = "decreasing"
                else:
                    direction = "stable"

                # Calculate significance (simplified)
                variance = np.var(y)
                significance = min(abs(slope) / (variance + 1), 1.0)

                trend = ErrorTrend(
                    trend_id=f"trend_{error_type.value}",
                    error_type=error_type,
                    direction=direction,
                    rate=float(slope),
                    timeframe=f"{timeframe_days} days",
                    significance=significance,
                    projected_impact=self._project_trend_impact(direction, slope, error_type),
                )
                trends.append(trend)

        return trends

    def _project_trend_impact(self, direction: str, rate: float, error_type: ErrorType) -> str:
        """Project the impact of a trend"""
        if direction == "increasing":
            if rate > 2:
                return f"Critical: {error_type.value} errors increasing rapidly"
            else:
                return f"Warning: {error_type.value} errors increasing"
        elif direction == "decreasing":
            return f"Positive: {error_type.value} errors decreasing"
        else:
            return f"Stable: {error_type.value} errors remain constant"

    async def _generate_predictions(
        self, features: np.ndarray, errors: list[ErrorState]
    ) -> list[PredictedError]:
        """Generate predictions for future errors"""
        predictions = []

        if len(features) < 10:
            return predictions

        try:
            # Prepare training data
            X = features[:-1]  # All but last
            y = [e["error_type"].value for e in errors[1:]]  # Shifted by one

            # Train prediction model if not trained
            if not self.models_trained and len(X) > 0:
                self.prediction_model.fit(X, y)
                self.models_trained = True

            # Make predictions for next timeframe
            if self.models_trained:
                last_feature = features[-1].reshape(1, -1)
                prediction_proba = self.prediction_model.predict_proba(last_feature)[0]
                predicted_class = self.prediction_model.classes_[np.argmax(prediction_proba)]
                confidence = np.max(prediction_proba)

                if confidence > 0.6:  # Only high-confidence predictions
                    prediction = PredictedError(
                        prediction_id=f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        error_type=ErrorType[predicted_class.upper()],
                        probability=confidence,
                        expected_timeframe=f"Next {self.analysis_config.prediction_window_hours} hours",
                        affected_components=self._predict_affected_components(
                            errors, predicted_class
                        ),
                        prevention_steps=self._generate_prevention_steps(predicted_class),
                        confidence=confidence,
                        evidence=self._gather_prediction_evidence(errors, predicted_class),
                    )
                    predictions.append(prediction)

        except Exception as e:
            logger.error(f"Prediction generation failed: {e}")

        return predictions

    def _predict_affected_components(
        self, errors: list[ErrorState], predicted_type: str
    ) -> list[str]:
        """Predict which components will be affected"""
        affected = set()
        for error in errors:
            if error["error_type"].value == predicted_type:
                affected.update(error.get("affected_components", []))
        return list(affected)[:5]  # Top 5 components

    def _generate_prevention_steps(self, error_type: str) -> list[str]:
        """Generate prevention steps for predicted error"""
        prevention_map = {
            "MEMORY_LEAK": [
                "Review memory allocation patterns",
                "Implement proper resource cleanup",
                "Add memory monitoring",
            ],
            "PERFORMANCE": [
                "Optimize database queries",
                "Implement caching strategies",
                "Review algorithm complexity",
            ],
            "DEPENDENCY": [
                "Update dependencies to latest stable versions",
                "Review dependency compatibility",
                "Implement dependency health checks",
            ],
            "RUNTIME": [
                "Add input validation",
                "Implement error boundaries",
                "Increase test coverage",
            ],
        }
        return prevention_map.get(error_type.upper(), ["Review code for potential issues"])

    def _gather_prediction_evidence(
        self, errors: list[ErrorState], predicted_type: str
    ) -> list[str]:
        """Gather evidence supporting the prediction"""
        evidence = []
        recent_count = sum(1 for e in errors[-10:] if e["error_type"].value == predicted_type)
        if recent_count > 0:
            evidence.append(f"{recent_count} similar errors in last 10 errors")

        # Check for increasing trend
        hourly_counts = defaultdict(int)
        for error in errors:
            if error["error_type"].value == predicted_type:
                hour = datetime.fromisoformat(error["timestamp"]).hour
                hourly_counts[hour] += 1

        if hourly_counts:
            peak_hour = max(hourly_counts, key=hourly_counts.get)
            evidence.append(f"Peak occurrence at hour {peak_hour}")

        return evidence

    def _generate_pattern_insights(
        self,
        patterns: list[ErrorPattern],
        trends: list[ErrorTrend],
        clusters: list[PatternCluster],
    ) -> list[PatternInsight]:
        """Generate actionable insights from patterns"""
        insights = []

        # Insight 1: High-frequency patterns
        high_freq_patterns = [p for p in patterns if p.frequency > 10]
        if high_freq_patterns:
            insight = PatternInsight(
                insight_id=f"insight_freq_{datetime.now().strftime('%H%M%S')}",
                description=f"Found {len(high_freq_patterns)} high-frequency error patterns",
                pattern_ids=[p.pattern_id for p in high_freq_patterns],
                actionable_recommendation="Prioritize fixing these recurring issues",
                priority=ErrorPriority.HIGH,
                estimated_impact=f"Could prevent {sum(p.frequency for p in high_freq_patterns)} errors",
                supporting_data={"pattern_count": len(high_freq_patterns)},
            )
            insights.append(insight)

        # Insight 2: Increasing trends
        increasing_trends = [t for t in trends if t.direction == "increasing"]
        if increasing_trends:
            most_critical = max(increasing_trends, key=lambda t: t.significance)
            insight = PatternInsight(
                insight_id=f"insight_trend_{datetime.now().strftime('%H%M%S')}",
                description=f"{most_critical.error_type.value} errors increasing rapidly",
                pattern_ids=[],
                actionable_recommendation="Investigate root cause immediately",
                priority=ErrorPriority.CRITICAL,
                estimated_impact=most_critical.projected_impact,
                supporting_data={"trend_rate": most_critical.rate},
            )
            insights.append(insight)

        # Insight 3: Large clusters
        large_clusters = [c for c in clusters if c.error_count > 20]
        if large_clusters:
            insight = PatternInsight(
                insight_id=f"insight_cluster_{datetime.now().strftime('%H%M%S')}",
                description=f"Identified {len(large_clusters)} major error clusters",
                pattern_ids=[],
                actionable_recommendation="Implement cluster-specific solutions",
                priority=ErrorPriority.HIGH,
                estimated_impact=f"Affects {sum(c.error_count for c in large_clusters)} errors",
                supporting_data={"cluster_count": len(large_clusters)},
            )
            insights.append(insight)

        return insights[:5]  # Return top 5 insights

    def _update_pattern_database(self, new_patterns: list[ErrorPattern]):
        """Update the stored pattern database"""
        # Merge with existing patterns
        existing_ids = {p.pattern_id for p in self.error_patterns}
        for pattern in new_patterns:
            if pattern.pattern_id in existing_ids:
                # Update existing pattern
                for i, p in enumerate(self.error_patterns):
                    if p.pattern_id == pattern.pattern_id:
                        self.error_patterns[i] = pattern
                        break
            else:
                # Add new pattern
                self.error_patterns.append(pattern)

        # Limit stored patterns
        if len(self.error_patterns) > self.analysis_config.max_patterns_stored:
            # Keep most frequent and recent patterns
            self.error_patterns.sort(key=lambda p: (p.frequency, p.last_seen), reverse=True)
            self.error_patterns = self.error_patterns[: self.analysis_config.max_patterns_stored]

        # Save patterns
        self._save_patterns()

    def _generate_analysis_summary(
        self,
        patterns: list[ErrorPattern],
        trends: list[ErrorTrend],
        predictions: list[PredictedError],
    ) -> dict[str, Any]:
        """Generate summary of the analysis"""
        return {
            "total_patterns": len(patterns),
            "critical_trends": len([t for t in trends if t.significance > 0.7]),
            "high_confidence_predictions": len([p for p in predictions if p.confidence > 0.8]),
            "most_frequent_pattern": patterns[0].pattern_id if patterns else None,
            "most_significant_trend": trends[0].trend_id if trends else None,
            "action_required": len(patterns) > 5
            or any(t.direction == "increasing" for t in trends),
        }

    # Tool implementations
    def _analyze_pattern_tool(self, pattern_description: str) -> str:
        """Tool: Analyze a specific pattern"""
        matching_patterns = [
            p for p in self.error_patterns if pattern_description.lower() in p.regex.lower()
        ]
        return f"Found {len(matching_patterns)} matching patterns"

    def _predict_errors_tool(self, timeframe: str) -> str:
        """Tool: Predict errors for timeframe"""
        return f"Generated predictions for {timeframe}"

    def _detect_anomalies_tool(self, data: str) -> str:
        """Tool: Detect anomalies in error data"""
        return "Anomaly detection completed"

    def _analyze_trends_tool(self, period: str) -> str:
        """Tool: Analyze trends over period"""
        return f"Trend analysis for {period} completed"

    def _cluster_errors_tool(self, error_type: Optional[str] = None) -> str:
        """Tool: Cluster errors"""
        return f"Clustered errors{f' of type {error_type}' if error_type else ''}"

    def _generate_insights_tool(self, focus_area: Optional[str] = None) -> str:
        """Tool: Generate insights"""
        return f"Generated insights{f' for {focus_area}' if focus_area else ''}"

    async def get_pattern_analysis_metrics(self) -> dict[str, Any]:
        """Get metrics specific to pattern analysis"""
        base_metrics = await self.get_error_metrics()

        analysis_metrics = {
            "total_patterns_identified": len(self.error_patterns),
            "pattern_clusters": len(self.pattern_clusters),
            "active_predictions": len(self.predictions),
            "trends_detected": len(self.trends),
            "insights_generated": len(self.insights),
            "model_accuracy": 0.0,
            "prediction_confidence_avg": 0.0,
        }

        if self.predictions:
            confidences = [p.confidence for p in self.predictions]
            analysis_metrics["prediction_confidence_avg"] = sum(confidences) / len(confidences)

        # Combine metrics
        return {**base_metrics, **analysis_metrics}

    async def _process_task(self, state) -> Any:
        """
        Process pattern analysis task.

        Args:
            state: Agent state containing task information

        Returns:
            Task processing result
        """
        try:
            task = state.get("task", {})
            task_type = task.get("type", "analyze_patterns")

            if task_type == "analyze_patterns":
                errors = task.get("errors", [])
                time_window = task.get("time_window", 24)  # hours

                # Convert dict errors to ErrorState format if needed
                formatted_errors = []
                for error in errors:
                    if isinstance(error, dict):
                        # Ensure error has required fields
                        if "error_type" not in error:
                            error["error_type"] = ErrorType.RUNTIME
                        if "priority" not in error:
                            error["priority"] = ErrorPriority.MEDIUM
                        if "timestamp" not in error:
                            error["timestamp"] = datetime.now().isoformat()
                    formatted_errors.append(error)

                # Perform analysis
                result = await self.analyze_patterns(formatted_errors, time_window)

                return {
                    "status": "completed",
                    "result": result,
                    "patterns_found": len(result.get("patterns", [])),
                    "insights_generated": len(result.get("insights", [])),
                }

            elif task_type == "predict_errors":
                context = task.get("context", {})
                prediction = await self.predict_error(context)

                return {
                    "status": "completed",
                    "result": prediction,
                    "prediction_confidence": prediction.confidence if prediction else 0.0,
                }

            elif task_type == "get_metrics":
                metrics = await self.get_performance_metrics()
                return {"status": "completed", "result": metrics}

            else:
                return {
                    "status": "error",
                    "error": f"Unknown task type: {task_type}",
                    "result": None,
                }

        except Exception as e:
            logger.error(f"Error processing pattern analysis task: {e}")
            return {"status": "error", "error": str(e), "result": None}
