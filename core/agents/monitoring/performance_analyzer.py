"""
Performance Analyzer for GPT-4.1 Migration

Analyzes API performance metrics, detects anomalies, and provides
optimization recommendations for the migration process.
"""

import logging
import statistics
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class PerformanceMetric(Enum):
    """Types of performance metrics"""
    LATENCY = "latency"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    TOKEN_EFFICIENCY = "token_efficiency"
    COST_EFFICIENCY = "cost_efficiency"


@dataclass
class PerformanceDataPoint:
    """Individual performance measurement"""
    timestamp: datetime
    metric_type: PerformanceMetric
    value: float
    model: str
    endpoint: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAnomaly:
    """Detected performance anomaly"""
    timestamp: datetime
    metric_type: PerformanceMetric
    severity: str  # low, medium, high, critical
    current_value: float
    expected_value: float
    deviation_percentage: float
    description: str
    recommendations: List[str] = field(default_factory=list)


@dataclass
class PerformanceSummary:
    """Summary of performance analysis"""
    period_start: datetime
    period_end: datetime
    model: str
    metrics: Dict[str, float]
    trends: Dict[str, float]
    anomalies: List[PerformanceAnomaly]
    overall_score: float
    recommendations: List[str]


class PerformanceAnalyzer:
    """
    Advanced performance analysis for GPT-4.1 migration monitoring.

    Features:
    - Real-time performance metric tracking
    - Anomaly detection using statistical methods
    - Performance trend analysis
    - Model comparison and optimization
    - Automated performance scoring
    """

    def __init__(self):
        self.data_points: List[PerformanceDataPoint] = []
        self.baselines: Dict[str, Dict[PerformanceMetric, float]] = {}  # model -> metric -> baseline
        self.anomaly_thresholds = {
            PerformanceMetric.LATENCY: {"warning": 2.0, "critical": 3.0},  # Standard deviations
            PerformanceMetric.SUCCESS_RATE: {"warning": 0.95, "critical": 0.90},  # Absolute values
            PerformanceMetric.ERROR_RATE: {"warning": 0.05, "critical": 0.10},  # Absolute values
            PerformanceMetric.THROUGHPUT: {"warning": 2.0, "critical": 3.0},  # Standard deviations
            PerformanceMetric.TOKEN_EFFICIENCY: {"warning": 0.8, "critical": 0.7},  # Absolute values
            PerformanceMetric.COST_EFFICIENCY: {"warning": 0.8, "critical": 0.7}  # Absolute values
        }

        # Performance targets for each model
        self.performance_targets = {
            "gpt-4": {
                PerformanceMetric.LATENCY: 3.0,  # seconds
                PerformanceMetric.SUCCESS_RATE: 0.98,
                PerformanceMetric.ERROR_RATE: 0.02,
                PerformanceMetric.TOKEN_EFFICIENCY: 0.85,
                PerformanceMetric.COST_EFFICIENCY: 0.70
            },
            "gpt-4o": {
                PerformanceMetric.LATENCY: 2.0,
                PerformanceMetric.SUCCESS_RATE: 0.99,
                PerformanceMetric.ERROR_RATE: 0.01,
                PerformanceMetric.TOKEN_EFFICIENCY: 0.90,
                PerformanceMetric.COST_EFFICIENCY: 0.85
            },
            "gpt-4o-mini": {
                PerformanceMetric.LATENCY: 1.5,
                PerformanceMetric.SUCCESS_RATE: 0.98,
                PerformanceMetric.ERROR_RATE: 0.02,
                PerformanceMetric.TOKEN_EFFICIENCY: 0.85,
                PerformanceMetric.COST_EFFICIENCY: 0.95
            }
        }

        logger.info("PerformanceAnalyzer initialized")

    def record_performance_data(
        self,
        metric_type: PerformanceMetric,
        value: float,
        model: str,
        endpoint: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a performance data point"""

        data_point = PerformanceDataPoint(
            timestamp=datetime.now(timezone.utc),
            metric_type=metric_type,
            value=value,
            model=model,
            endpoint=endpoint,
            metadata=metadata or {}
        )

        self.data_points.append(data_point)

        # Keep only last 30 days of data
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        self.data_points = [
            dp for dp in self.data_points
            if dp.timestamp >= cutoff_date
        ]

        logger.debug(f"Recorded {metric_type.value} for {model}: {value}")

    def establish_baseline(self, model: str, days_back: int = 7) -> Dict[PerformanceMetric, float]:
        """Establish performance baseline for a model"""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)

        # Get data points for the baseline period
        baseline_data = [
            dp for dp in self.data_points
            if dp.model == model and start_time <= dp.timestamp <= end_time
        ]

        if not baseline_data:
            logger.warning(f"No data available for baseline establishment for {model}")
            return {}

        # Calculate baseline for each metric
        baseline_metrics = {}

        for metric_type in PerformanceMetric:
            metric_values = [
                dp.value for dp in baseline_data
                if dp.metric_type == metric_type
            ]

            if metric_values:
                if metric_type in [PerformanceMetric.LATENCY, PerformanceMetric.THROUGHPUT]:
                    # For latency and throughput, use median as baseline
                    baseline_metrics[metric_type] = statistics.median(metric_values)
                else:
                    # For rates and efficiencies, use mean
                    baseline_metrics[metric_type] = statistics.mean(metric_values)

        # Store baseline
        self.baselines[model] = baseline_metrics

        logger.info(f"Established baseline for {model}: {baseline_metrics}")
        return baseline_metrics

    def detect_anomalies(
        self,
        model: str,
        hours_back: int = 1
    ) -> List[PerformanceAnomaly]:
        """Detect performance anomalies for a model"""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours_back)

        # Get recent data points
        recent_data = [
            dp for dp in self.data_points
            if dp.model == model and start_time <= dp.timestamp <= end_time
        ]

        anomalies = []

        if model not in self.baselines:
            logger.warning(f"No baseline established for {model}, cannot detect anomalies")
            return anomalies

        baseline = self.baselines[model]

        for metric_type in PerformanceMetric:
            # Get recent values for this metric
            recent_values = [
                dp.value for dp in recent_data
                if dp.metric_type == metric_type
            ]

            if not recent_values or metric_type not in baseline:
                continue

            # Calculate current value (mean of recent values)
            current_value = statistics.mean(recent_values)
            baseline_value = baseline[metric_type]

            # Detect anomaly based on metric type
            anomaly = self._detect_metric_anomaly(
                metric_type, current_value, baseline_value, model
            )

            if anomaly:
                anomalies.append(anomaly)

        return anomalies

    def _detect_metric_anomaly(
        self,
        metric_type: PerformanceMetric,
        current_value: float,
        baseline_value: float,
        model: str
    ) -> Optional[PerformanceAnomaly]:
        """Detect anomaly for a specific metric"""

        thresholds = self.anomaly_thresholds[metric_type]

        if metric_type in [PerformanceMetric.LATENCY, PerformanceMetric.THROUGHPUT]:
            # For latency and throughput, check standard deviation-based anomalies
            # For now, use simple percentage-based detection
            deviation = abs(current_value - baseline_value) / baseline_value

            if deviation > 0.5:  # 50% deviation
                severity = "critical" if deviation > 1.0 else "high"

                return PerformanceAnomaly(
                    timestamp=datetime.now(timezone.utc),
                    metric_type=metric_type,
                    severity=severity,
                    current_value=current_value,
                    expected_value=baseline_value,
                    deviation_percentage=deviation * 100,
                    description=f"{metric_type.value} anomaly detected for {model}",
                    recommendations=self._get_anomaly_recommendations(metric_type, current_value, baseline_value)
                )

        elif metric_type in [PerformanceMetric.SUCCESS_RATE, PerformanceMetric.TOKEN_EFFICIENCY,
                           PerformanceMetric.COST_EFFICIENCY]:
            # For rates and efficiencies, check if below threshold
            if current_value < thresholds["critical"]:
                severity = "critical"
            elif current_value < thresholds["warning"]:
                severity = "high"
            else:
                return None

            deviation = abs(current_value - baseline_value) / baseline_value

            return PerformanceAnomaly(
                timestamp=datetime.now(timezone.utc),
                metric_type=metric_type,
                severity=severity,
                current_value=current_value,
                expected_value=baseline_value,
                deviation_percentage=deviation * 100,
                description=f"{metric_type.value} below threshold for {model}",
                recommendations=self._get_anomaly_recommendations(metric_type, current_value, baseline_value)
            )

        elif metric_type == PerformanceMetric.ERROR_RATE:
            # For error rate, check if above threshold
            if current_value > thresholds["critical"]:
                severity = "critical"
            elif current_value > thresholds["warning"]:
                severity = "high"
            else:
                return None

            deviation = abs(current_value - baseline_value) / max(0.001, baseline_value)

            return PerformanceAnomaly(
                timestamp=datetime.now(timezone.utc),
                metric_type=metric_type,
                severity=severity,
                current_value=current_value,
                expected_value=baseline_value,
                deviation_percentage=deviation * 100,
                description=f"{metric_type.value} above threshold for {model}",
                recommendations=self._get_anomaly_recommendations(metric_type, current_value, baseline_value)
            )

        return None

    def _get_anomaly_recommendations(
        self,
        metric_type: PerformanceMetric,
        current_value: float,
        baseline_value: float
    ) -> List[str]:
        """Get recommendations for addressing an anomaly"""

        recommendations = []

        if metric_type == PerformanceMetric.LATENCY:
            if current_value > baseline_value:
                recommendations.extend([
                    "Check API endpoint health and status",
                    "Review request complexity and prompt length",
                    "Consider request optimization or batching",
                    "Monitor network connectivity and routing",
                    "Check for rate limiting or throttling"
                ])

        elif metric_type == PerformanceMetric.SUCCESS_RATE:
            recommendations.extend([
                "Review recent API key and authentication status",
                "Check for rate limiting or quota issues",
                "Analyze error patterns in failed requests",
                "Verify request format and parameters",
                "Consider implementing retry logic with backoff"
            ])

        elif metric_type == PerformanceMetric.ERROR_RATE:
            recommendations.extend([
                "Investigate error patterns and types",
                "Check API key validity and permissions",
                "Review request format and validation",
                "Monitor rate limits and quota usage",
                "Implement better error handling and retry logic"
            ])

        elif metric_type == PerformanceMetric.TOKEN_EFFICIENCY:
            recommendations.extend([
                "Optimize prompt length and structure",
                "Use more efficient prompting techniques",
                "Implement response caching for common queries",
                "Review output length requirements",
                "Consider using more efficient models for simple tasks"
            ])

        elif metric_type == PerformanceMetric.COST_EFFICIENCY:
            recommendations.extend([
                "Review model selection for different use cases",
                "Implement request caching and deduplication",
                "Optimize token usage and prompt efficiency",
                "Consider downgrading model for non-critical tasks",
                "Implement cost controls and budgeting"
            ])

        return recommendations

    def analyze_performance_trends(
        self,
        model: str,
        days_back: int = 7
    ) -> Dict[PerformanceMetric, Dict[str, float]]:
        """Analyze performance trends over time"""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)

        # Get data points for the analysis period
        trend_data = [
            dp for dp in self.data_points
            if dp.model == model and start_time <= dp.timestamp <= end_time
        ]

        trends = {}

        for metric_type in PerformanceMetric:
            metric_data = [
                (dp.timestamp, dp.value) for dp in trend_data
                if dp.metric_type == metric_type
            ]

            if len(metric_data) < 2:
                continue

            # Sort by timestamp
            metric_data.sort(key=lambda x: x[0])

            # Split into first and second half for trend calculation
            mid_point = len(metric_data) // 2
            first_half = metric_data[:mid_point]
            second_half = metric_data[mid_point:]

            if first_half and second_half:
                first_avg = statistics.mean([value for _, value in first_half])
                second_avg = statistics.mean([value for _, value in second_half])

                # Calculate trend percentage
                if first_avg > 0:
                    trend_percentage = ((second_avg - first_avg) / first_avg) * 100
                else:
                    trend_percentage = 0.0

                # Calculate other statistics
                all_values = [value for _, value in metric_data]

                trends[metric_type] = {
                    "trend_percentage": trend_percentage,
                    "current_average": second_avg,
                    "previous_average": first_avg,
                    "overall_average": statistics.mean(all_values),
                    "min_value": min(all_values),
                    "max_value": max(all_values),
                    "std_deviation": statistics.stdev(all_values) if len(all_values) > 1 else 0.0
                }

        return trends

    def generate_performance_summary(
        self,
        model: str,
        days_back: int = 7
    ) -> PerformanceSummary:
        """Generate comprehensive performance summary"""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)

        # Collect current metrics
        current_metrics = self._calculate_current_metrics(model, hours_back=24)

        # Analyze trends
        trends = self.analyze_performance_trends(model, days_back)

        # Detect anomalies
        anomalies = self.detect_anomalies(model, hours_back=24)

        # Calculate overall performance score
        overall_score = self._calculate_performance_score(model, current_metrics)

        # Generate recommendations
        recommendations = self._generate_performance_recommendations(
            model, current_metrics, trends, anomalies
        )

        return PerformanceSummary(
            period_start=start_time,
            period_end=end_time,
            model=model,
            metrics=current_metrics,
            trends={
                metric.value: trend_data.get("trend_percentage", 0.0)
                for metric, trend_data in trends.items()
            },
            anomalies=anomalies,
            overall_score=overall_score,
            recommendations=recommendations
        )

    def _calculate_current_metrics(
        self,
        model: str,
        hours_back: int = 24
    ) -> Dict[str, float]:
        """Calculate current metric values"""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours_back)

        recent_data = [
            dp for dp in self.data_points
            if dp.model == model and start_time <= dp.timestamp <= end_time
        ]

        metrics = {}

        for metric_type in PerformanceMetric:
            values = [
                dp.value for dp in recent_data
                if dp.metric_type == metric_type
            ]

            if values:
                if metric_type == PerformanceMetric.LATENCY:
                    # Use median for latency
                    metrics[metric_type.value] = statistics.median(values)
                else:
                    # Use mean for other metrics
                    metrics[metric_type.value] = statistics.mean(values)

        return metrics

    def _calculate_performance_score(
        self,
        model: str,
        current_metrics: Dict[str, float]
    ) -> float:
        """Calculate overall performance score (0-100)"""

        if model not in self.performance_targets:
            return 50.0  # Default score if no targets defined

        targets = self.performance_targets[model]
        score = 100.0
        scored_metrics = 0

        for metric_type, target_value in targets.items():
            metric_key = metric_type.value

            if metric_key not in current_metrics:
                continue

            current_value = current_metrics[metric_key]
            scored_metrics += 1

            if metric_type == PerformanceMetric.LATENCY:
                # Lower is better for latency
                if current_value <= target_value:
                    metric_score = 20.0  # Full points
                else:
                    # Deduct points based on how much over target
                    excess_ratio = (current_value - target_value) / target_value
                    metric_score = max(0, 20.0 - (excess_ratio * 20.0))

            elif metric_type == PerformanceMetric.ERROR_RATE:
                # Lower is better for error rate
                if current_value <= target_value:
                    metric_score = 20.0
                else:
                    # Deduct points based on excess error rate
                    excess_ratio = (current_value - target_value) / target_value
                    metric_score = max(0, 20.0 - (excess_ratio * 20.0))

            else:
                # Higher is better for success rate, efficiency metrics
                if current_value >= target_value:
                    metric_score = 20.0
                else:
                    # Deduct points based on shortfall
                    shortfall_ratio = (target_value - current_value) / target_value
                    metric_score = max(0, 20.0 - (shortfall_ratio * 20.0))

            score = min(score, score * (metric_score / 20.0))

        # If no metrics were scored, return default
        if scored_metrics == 0:
            return 50.0

        return max(0, min(100, score))

    def _generate_performance_recommendations(
        self,
        model: str,
        current_metrics: Dict[str, float],
        trends: Dict[PerformanceMetric, Dict[str, float]],
        anomalies: List[PerformanceAnomaly]
    ) -> List[str]:
        """Generate performance optimization recommendations"""

        recommendations = []

        # Recommendations based on anomalies
        for anomaly in anomalies:
            recommendations.extend(anomaly.recommendations)

        # Recommendations based on trends
        for metric_type, trend_data in trends.items():
            trend_percentage = trend_data.get("trend_percentage", 0.0)

            if metric_type == PerformanceMetric.LATENCY and trend_percentage > 20:
                recommendations.append("Latency increasing - investigate API performance and optimize requests")
            elif metric_type == PerformanceMetric.ERROR_RATE and trend_percentage > 50:
                recommendations.append("Error rate rising - review error patterns and improve error handling")
            elif metric_type == PerformanceMetric.COST_EFFICIENCY and trend_percentage < -20:
                recommendations.append("Cost efficiency declining - review model usage and implement cost controls")

        # Recommendations based on current metric values
        if model in self.performance_targets:
            targets = self.performance_targets[model]

            for metric_type, target_value in targets.items():
                metric_key = metric_type.value
                if metric_key in current_metrics:
                    current_value = current_metrics[metric_key]

                    if metric_type == PerformanceMetric.LATENCY and current_value > target_value * 1.2:
                        recommendations.append(f"Latency ({current_value:.2f}s) above target - optimize request complexity")
                    elif metric_type == PerformanceMetric.SUCCESS_RATE and current_value < target_value * 0.95:
                        recommendations.append(f"Success rate ({current_value:.1%}) below target - improve error handling")

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        return unique_recommendations[:10]  # Limit to top 10 recommendations

    def compare_model_performance(
        self,
        models: List[str],
        days_back: int = 7
    ) -> Dict[str, PerformanceSummary]:
        """Compare performance across multiple models"""

        comparison = {}

        for model in models:
            try:
                summary = self.generate_performance_summary(model, days_back)
                comparison[model] = summary
            except Exception as e:
                logger.error(f"Failed to generate summary for {model}: {e}")

        return comparison

    def export_performance_data(
        self,
        model: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Export performance data for external analysis"""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)

        # Filter data points
        filtered_data = [
            dp for dp in self.data_points
            if start_time <= dp.timestamp <= end_time
        ]

        if model:
            filtered_data = [dp for dp in filtered_data if dp.model == model]

        export_data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "period_start": start_time.isoformat(),
            "period_end": end_time.isoformat(),
            "model_filter": model,
            "total_data_points": len(filtered_data),
            "data_points": [
                {
                    "timestamp": dp.timestamp.isoformat(),
                    "metric_type": dp.metric_type.value,
                    "value": dp.value,
                    "model": dp.model,
                    "endpoint": dp.endpoint,
                    "metadata": dp.metadata
                }
                for dp in filtered_data
            ],
            "baselines": {
                model_name: {
                    metric.value: baseline_value
                    for metric, baseline_value in baseline_metrics.items()
                }
                for model_name, baseline_metrics in self.baselines.items()
            }
        }

        return export_data

    def get_real_time_metrics(self, model: str) -> Dict[str, Any]:
        """Get real-time performance metrics for dashboard"""

        # Get metrics from last hour
        current_metrics = self._calculate_current_metrics(model, hours_back=1)

        # Get recent anomalies
        recent_anomalies = self.detect_anomalies(model, hours_back=1)

        # Calculate performance score
        performance_score = self._calculate_performance_score(model, current_metrics)

        return {
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": current_metrics,
            "performance_score": performance_score,
            "anomalies": [
                {
                    "type": anomaly.metric_type.value,
                    "severity": anomaly.severity,
                    "description": anomaly.description,
                    "current_value": anomaly.current_value,
                    "expected_value": anomaly.expected_value
                }
                for anomaly in recent_anomalies
            ],
            "status": self._get_performance_status(performance_score, recent_anomalies)
        }

    def _get_performance_status(
        self,
        performance_score: float,
        anomalies: List[PerformanceAnomaly]
    ) -> str:
        """Get overall performance status"""

        critical_anomalies = [a for a in anomalies if a.severity == "critical"]
        high_anomalies = [a for a in anomalies if a.severity == "high"]

        if critical_anomalies or performance_score < 50:
            return "critical"
        elif high_anomalies or performance_score < 70:
            return "warning"
        elif performance_score < 85:
            return "fair"
        else:
            return "excellent"