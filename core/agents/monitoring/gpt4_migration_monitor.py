"""
GPT-4.1 Migration Monitor Agent

Comprehensive monitoring agent for tracking GPT-4.1 API migration progress,
performance metrics, costs, and alerting for the July 14, 2025 deadline.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from core.agents.base_agent import BaseAgent, AgentConfig, AgentState, TaskResult
from apps.backend.core.metrics.metrics import (
    GPT41_REQUESTS, GPT41_TOKENS, GPT41_COST, GPT41_LATENCY,
    track_gpt41_request
)

logger = logging.getLogger(__name__)


class MigrationPhase(Enum):
    """Migration phases for tracking progress"""
    PREPARATION = "preparation"
    TESTING = "testing"
    GRADUAL_ROLLOUT = "gradual_rollout"
    FULL_MIGRATION = "full_migration"
    COMPLETED = "completed"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class MigrationMetrics:
    """Container for migration metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_latency: float = 0.0
    error_rate: float = 0.0
    cost_per_request: float = 0.0
    tokens_per_request: float = 0.0
    daily_cost: float = 0.0
    weekly_cost: float = 0.0
    monthly_projected_cost: float = 0.0


@dataclass
class ModelPerformance:
    """Performance metrics for specific models"""
    model_name: str
    requests: int = 0
    success_rate: float = 0.0
    avg_latency: float = 0.0
    cost_efficiency: float = 0.0  # Cost per successful token
    quality_score: float = 0.0    # Based on output quality metrics


@dataclass
class MigrationAlert:
    """Alert for migration issues"""
    level: AlertLevel
    message: str
    timestamp: datetime
    metric_name: str
    current_value: float
    threshold: float
    recommendations: List[str] = field(default_factory=list)


class GPT4MigrationMonitor(BaseAgent):
    """
    Specialized agent for monitoring GPT-4.1 migration progress.

    Key responsibilities:
    1. Track API usage and performance metrics
    2. Monitor costs and budget adherence
    3. Generate alerts for issues or thresholds
    4. Provide migration progress reports
    5. Recommend optimizations
    """

    # Migration deadline
    MIGRATION_DEADLINE = datetime(2025, 7, 14, 23, 59, 59, tzinfo=timezone.utc)

    # Default thresholds
    DEFAULT_THRESHOLDS = {
        "error_rate_warning": 5.0,      # 5% error rate
        "error_rate_critical": 10.0,    # 10% error rate
        "latency_warning": 5.0,         # 5 seconds
        "latency_critical": 10.0,       # 10 seconds
        "daily_cost_warning": 100.0,    # $100/day
        "daily_cost_critical": 200.0,   # $200/day
        "monthly_budget": 3000.0,       # $3000/month
        "token_efficiency_min": 0.8     # 80% token efficiency
    }

    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="GPT4MigrationMonitor",
                model="gpt-4o-mini",  # Use efficient model for monitoring
                temperature=0.1,      # Low temperature for consistent analysis
                system_prompt=self._get_system_prompt()
            )

        super().__init__(config)

        # Migration tracking
        self.current_phase = MigrationPhase.PREPARATION
        self.migration_start_date = datetime.now(timezone.utc)
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()

        # Metrics storage
        self.metrics_history: List[Tuple[datetime, MigrationMetrics]] = []
        self.model_performance: Dict[str, ModelPerformance] = {}
        self.active_alerts: List[MigrationAlert] = []

        # Cost tracking
        self.daily_costs: Dict[str, float] = {}  # date -> cost
        self.monthly_budget_used = 0.0

        # Performance baselines
        self.baseline_metrics: Optional[MigrationMetrics] = None

        logger.info("GPT-4.1 Migration Monitor initialized")
        logger.info(f"Migration deadline: {self.MIGRATION_DEADLINE}")

    def _get_system_prompt(self) -> str:
        """Get specialized system prompt for migration monitoring"""
        return """You are the GPT-4.1 Migration Monitor, a specialized AI agent responsible for
tracking and optimizing the migration from GPT-3.5/GPT-4 to GPT-4.1 by July 14, 2025.

Your primary responsibilities:
1. Monitor API usage patterns, costs, and performance metrics
2. Detect anomalies, performance degradation, or cost overruns
3. Generate actionable alerts and recommendations
4. Track migration progress toward the deadline
5. Provide detailed analysis and optimization suggestions

Focus on:
- Cost efficiency and budget management
- Performance optimization (latency, success rates)
- Quality maintenance during migration
- Risk mitigation and early warning
- Deadline adherence tracking

Always provide specific, actionable recommendations based on data analysis.
"""

    async def _process_task(self, state: AgentState) -> Any:
        """Process migration monitoring tasks"""
        task = state["task"].lower()
        context = state.get("context", {})

        try:
            if "collect" in task and "metrics" in task:
                return await self._collect_current_metrics()
            elif "analyze" in task and "performance" in task:
                return await self._analyze_performance_trends()
            elif "check" in task and ("alert" in task or "threshold" in task):
                return await self._check_thresholds_and_alert()
            elif "generate" in task and "report" in task:
                return await self._generate_migration_report()
            elif "optimize" in task or "recommend" in task:
                return await self._generate_optimization_recommendations()
            elif "cost" in task and "projection" in task:
                return await self._project_costs()
            elif "deadline" in task and "progress" in task:
                return await self._check_deadline_progress()
            elif "baseline" in task:
                return await self._establish_baseline()
            elif "model" in task and "comparison" in task:
                return await self._compare_model_performance()
            else:
                # Default comprehensive monitoring
                return await self._comprehensive_monitoring_cycle()

        except Exception as e:
            logger.error(f"Migration monitoring task failed: {e}")
            raise

    async def _collect_current_metrics(self) -> MigrationMetrics:
        """Collect current migration metrics from various sources"""
        try:
            # Get metrics from Prometheus
            current_metrics = MigrationMetrics()

            # This would integrate with actual Prometheus metrics
            # For now, we'll simulate metric collection
            current_time = datetime.now(timezone.utc)

            # In a real implementation, these would query Prometheus:
            # current_metrics.total_requests = GPT41_REQUESTS._value.sum()
            # current_metrics.total_tokens = GPT41_TOKENS._value.sum()
            # current_metrics.total_cost = GPT41_COST._value.sum()

            # Simulate metrics for demonstration
            current_metrics.total_requests = 1000
            current_metrics.successful_requests = 950
            current_metrics.failed_requests = 50
            current_metrics.total_tokens = 500000
            current_metrics.total_cost = 15.0
            current_metrics.avg_latency = 2.5

            # Calculate derived metrics
            if current_metrics.total_requests > 0:
                current_metrics.error_rate = (
                    current_metrics.failed_requests / current_metrics.total_requests * 100
                )
                current_metrics.cost_per_request = (
                    current_metrics.total_cost / current_metrics.total_requests
                )
                current_metrics.tokens_per_request = (
                    current_metrics.total_tokens / current_metrics.total_requests
                )

            # Calculate daily/weekly/monthly costs
            today = current_time.date().isoformat()
            current_metrics.daily_cost = self.daily_costs.get(today, 0.0)

            # Weekly cost (last 7 days)
            week_ago = current_time - timedelta(days=7)
            current_metrics.weekly_cost = sum(
                cost for date, cost in self.daily_costs.items()
                if datetime.fromisoformat(date).date() >= week_ago.date()
            )

            # Monthly projection
            days_in_month = 30
            if current_metrics.daily_cost > 0:
                current_metrics.monthly_projected_cost = current_metrics.daily_cost * days_in_month

            # Store metrics history
            self.metrics_history.append((current_time, current_metrics))

            # Keep only last 30 days of history
            cutoff_date = current_time - timedelta(days=30)
            self.metrics_history = [
                (ts, metrics) for ts, metrics in self.metrics_history
                if ts >= cutoff_date
            ]

            logger.info(f"Collected metrics: {current_metrics}")
            return current_metrics

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            raise

    async def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        if len(self.metrics_history) < 2:
            return {"status": "insufficient_data", "message": "Need more data points for trend analysis"}

        # Get recent metrics for comparison
        recent_metrics = [metrics for _, metrics in self.metrics_history[-7:]]  # Last week
        older_metrics = [metrics for _, metrics in self.metrics_history[-14:-7]]  # Previous week

        trends = {}

        if recent_metrics and older_metrics:
            # Calculate average metrics for each period
            recent_avg = self._calculate_average_metrics(recent_metrics)
            older_avg = self._calculate_average_metrics(older_metrics)

            # Calculate trend percentages
            trends = {
                "error_rate_trend": self._calculate_trend_percentage(
                    older_avg.error_rate, recent_avg.error_rate
                ),
                "latency_trend": self._calculate_trend_percentage(
                    older_avg.avg_latency, recent_avg.avg_latency
                ),
                "cost_trend": self._calculate_trend_percentage(
                    older_avg.daily_cost, recent_avg.daily_cost
                ),
                "efficiency_trend": self._calculate_trend_percentage(
                    older_avg.cost_per_request, recent_avg.cost_per_request
                )
            }

            # Generate trend analysis
            analysis = await self._generate_trend_analysis(trends, recent_avg, older_avg)

            return {
                "trends": trends,
                "recent_metrics": recent_avg,
                "previous_metrics": older_avg,
                "analysis": analysis,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        return {"status": "insufficient_data"}

    def _calculate_average_metrics(self, metrics_list: List[MigrationMetrics]) -> MigrationMetrics:
        """Calculate average metrics from a list"""
        if not metrics_list:
            return MigrationMetrics()

        count = len(metrics_list)
        avg_metrics = MigrationMetrics()

        for metrics in metrics_list:
            avg_metrics.total_requests += metrics.total_requests
            avg_metrics.successful_requests += metrics.successful_requests
            avg_metrics.failed_requests += metrics.failed_requests
            avg_metrics.total_tokens += metrics.total_tokens
            avg_metrics.total_cost += metrics.total_cost
            avg_metrics.avg_latency += metrics.avg_latency
            avg_metrics.error_rate += metrics.error_rate
            avg_metrics.cost_per_request += metrics.cost_per_request
            avg_metrics.daily_cost += metrics.daily_cost

        # Calculate averages
        avg_metrics.total_requests //= count
        avg_metrics.successful_requests //= count
        avg_metrics.failed_requests //= count
        avg_metrics.total_tokens //= count
        avg_metrics.total_cost /= count
        avg_metrics.avg_latency /= count
        avg_metrics.error_rate /= count
        avg_metrics.cost_per_request /= count
        avg_metrics.daily_cost /= count

        return avg_metrics

    def _calculate_trend_percentage(self, old_value: float, new_value: float) -> float:
        """Calculate percentage change between two values"""
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        return ((new_value - old_value) / old_value) * 100

    async def _generate_trend_analysis(
        self,
        trends: Dict[str, float],
        recent: MigrationMetrics,
        previous: MigrationMetrics
    ) -> str:
        """Generate AI-powered trend analysis"""
        analysis_prompt = f"""Analyze the following GPT-4.1 migration performance trends:

Recent Week Metrics:
- Error Rate: {recent.error_rate:.2f}%
- Average Latency: {recent.avg_latency:.2f}s
- Daily Cost: ${recent.daily_cost:.2f}
- Cost per Request: ${recent.cost_per_request:.4f}

Previous Week Metrics:
- Error Rate: {previous.error_rate:.2f}%
- Average Latency: {previous.avg_latency:.2f}s
- Daily Cost: ${previous.daily_cost:.2f}
- Cost per Request: ${previous.cost_per_request:.4f}

Trends:
- Error Rate Change: {trends.get('error_rate_trend', 0):.1f}%
- Latency Change: {trends.get('latency_trend', 0):.1f}%
- Cost Change: {trends.get('cost_trend', 0):.1f}%
- Efficiency Change: {trends.get('efficiency_trend', 0):.1f}%

Provide a concise analysis focusing on:
1. Performance improvement or degradation
2. Cost optimization opportunities
3. Potential risks or concerns
4. Specific recommendations for next steps
"""

        response = await self.llm.ainvoke(analysis_prompt)
        return response.content

    async def _check_thresholds_and_alert(self) -> List[MigrationAlert]:
        """Check current metrics against thresholds and generate alerts"""
        current_metrics = await self._collect_current_metrics()
        new_alerts = []

        # Check error rate thresholds
        if current_metrics.error_rate >= self.thresholds["error_rate_critical"]:
            alert = MigrationAlert(
                level=AlertLevel.CRITICAL,
                message=f"Critical error rate: {current_metrics.error_rate:.2f}%",
                timestamp=datetime.now(timezone.utc),
                metric_name="error_rate",
                current_value=current_metrics.error_rate,
                threshold=self.thresholds["error_rate_critical"],
                recommendations=[
                    "Investigate failed requests immediately",
                    "Consider rolling back recent changes",
                    "Check API key and authentication",
                    "Review error logs for patterns"
                ]
            )
            new_alerts.append(alert)
        elif current_metrics.error_rate >= self.thresholds["error_rate_warning"]:
            alert = MigrationAlert(
                level=AlertLevel.WARNING,
                message=f"Elevated error rate: {current_metrics.error_rate:.2f}%",
                timestamp=datetime.now(timezone.utc),
                metric_name="error_rate",
                current_value=current_metrics.error_rate,
                threshold=self.thresholds["error_rate_warning"],
                recommendations=[
                    "Monitor error patterns closely",
                    "Review recent API changes",
                    "Check rate limiting settings"
                ]
            )
            new_alerts.append(alert)

        # Check latency thresholds
        if current_metrics.avg_latency >= self.thresholds["latency_critical"]:
            alert = MigrationAlert(
                level=AlertLevel.CRITICAL,
                message=f"Critical latency: {current_metrics.avg_latency:.2f}s",
                timestamp=datetime.now(timezone.utc),
                metric_name="latency",
                current_value=current_metrics.avg_latency,
                threshold=self.thresholds["latency_critical"],
                recommendations=[
                    "Check API endpoint health",
                    "Review request complexity",
                    "Consider request optimization",
                    "Check network connectivity"
                ]
            )
            new_alerts.append(alert)
        elif current_metrics.avg_latency >= self.thresholds["latency_warning"]:
            alert = MigrationAlert(
                level=AlertLevel.WARNING,
                message=f"High latency: {current_metrics.avg_latency:.2f}s",
                timestamp=datetime.now(timezone.utc),
                metric_name="latency",
                current_value=current_metrics.avg_latency,
                threshold=self.thresholds["latency_warning"],
                recommendations=[
                    "Monitor latency trends",
                    "Optimize request parameters",
                    "Review prompt complexity"
                ]
            )
            new_alerts.append(alert)

        # Check cost thresholds
        if current_metrics.daily_cost >= self.thresholds["daily_cost_critical"]:
            alert = MigrationAlert(
                level=AlertLevel.CRITICAL,
                message=f"Critical daily cost: ${current_metrics.daily_cost:.2f}",
                timestamp=datetime.now(timezone.utc),
                metric_name="daily_cost",
                current_value=current_metrics.daily_cost,
                threshold=self.thresholds["daily_cost_critical"],
                recommendations=[
                    "Implement immediate cost controls",
                    "Review high-cost operations",
                    "Consider model downgrade for non-critical tasks",
                    "Implement request throttling"
                ]
            )
            new_alerts.append(alert)
        elif current_metrics.daily_cost >= self.thresholds["daily_cost_warning"]:
            alert = MigrationAlert(
                level=AlertLevel.WARNING,
                message=f"High daily cost: ${current_metrics.daily_cost:.2f}",
                timestamp=datetime.now(timezone.utc),
                metric_name="daily_cost",
                current_value=current_metrics.daily_cost,
                threshold=self.thresholds["daily_cost_warning"],
                recommendations=[
                    "Monitor cost trends closely",
                    "Optimize token usage",
                    "Review request efficiency"
                ]
            )
            new_alerts.append(alert)

        # Check monthly budget
        if current_metrics.monthly_projected_cost >= self.thresholds["monthly_budget"]:
            alert = MigrationAlert(
                level=AlertLevel.EMERGENCY,
                message=f"Monthly budget exceeded: ${current_metrics.monthly_projected_cost:.2f}",
                timestamp=datetime.now(timezone.utc),
                metric_name="monthly_budget",
                current_value=current_metrics.monthly_projected_cost,
                threshold=self.thresholds["monthly_budget"],
                recommendations=[
                    "Implement emergency cost controls",
                    "Temporarily pause non-essential operations",
                    "Review budget allocation",
                    "Escalate to management"
                ]
            )
            new_alerts.append(alert)

        # Add new alerts to active alerts
        self.active_alerts.extend(new_alerts)

        # Clean up old alerts (older than 24 hours)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        self.active_alerts = [
            alert for alert in self.active_alerts
            if alert.timestamp >= cutoff_time
        ]

        if new_alerts:
            logger.warning(f"Generated {len(new_alerts)} new alerts")
            for alert in new_alerts:
                logger.warning(f"{alert.level.value.upper()}: {alert.message}")

        return new_alerts

    async def _generate_migration_report(self) -> Dict[str, Any]:
        """Generate comprehensive migration progress report"""
        current_metrics = await self._collect_current_metrics()
        trends = await self._analyze_performance_trends()
        alerts = await self._check_thresholds_and_alert()
        deadline_progress = await self._check_deadline_progress()

        # Generate AI analysis of overall status
        report_prompt = f"""Generate a comprehensive GPT-4.1 migration progress report based on:

Current Metrics:
- Total Requests: {current_metrics.total_requests:,}
- Success Rate: {(current_metrics.successful_requests / max(1, current_metrics.total_requests) * 100):.1f}%
- Error Rate: {current_metrics.error_rate:.2f}%
- Average Latency: {current_metrics.avg_latency:.2f}s
- Daily Cost: ${current_metrics.daily_cost:.2f}
- Monthly Projection: ${current_metrics.monthly_projected_cost:.2f}

Migration Progress:
- Current Phase: {self.current_phase.value}
- Days to Deadline: {deadline_progress.get('days_remaining', 'unknown')}
- Progress Percentage: {deadline_progress.get('progress_percentage', 0):.1f}%

Active Alerts: {len(alerts)} alerts
Recent Trends: {len(trends.get('trends', {})) > 0}

Provide a structured report with:
1. Executive Summary
2. Key Performance Indicators
3. Cost Analysis
4. Risk Assessment
5. Recommendations for next phase
6. Timeline adjustments if needed
"""

        ai_analysis = await self.llm.ainvoke(report_prompt)

        report = {
            "report_id": f"migration_report_{int(time.time())}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "migration_phase": self.current_phase.value,
            "deadline_info": deadline_progress,
            "current_metrics": current_metrics.__dict__,
            "performance_trends": trends,
            "active_alerts": [
                {
                    "level": alert.level.value,
                    "message": alert.message,
                    "metric": alert.metric_name,
                    "value": alert.current_value,
                    "threshold": alert.threshold,
                    "recommendations": alert.recommendations
                }
                for alert in alerts
            ],
            "ai_analysis": ai_analysis.content,
            "model_performance": {
                name: perf.__dict__ for name, perf in self.model_performance.items()
            }
        }

        logger.info(f"Generated migration report: {report['report_id']}")
        return report

    async def _generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate AI-powered optimization recommendations"""
        current_metrics = await self._collect_current_metrics()

        optimization_prompt = f"""Based on the current GPT-4.1 migration metrics, provide specific optimization recommendations:

Current Performance:
- Error Rate: {current_metrics.error_rate:.2f}%
- Average Latency: {current_metrics.avg_latency:.2f}s
- Cost per Request: ${current_metrics.cost_per_request:.4f}
- Tokens per Request: {current_metrics.tokens_per_request:.0f}
- Daily Cost: ${current_metrics.daily_cost:.2f}

Focus on:
1. Cost reduction strategies
2. Performance optimization
3. Error rate improvement
4. Token efficiency
5. Migration timeline optimization

Provide 5-10 specific, actionable recommendations with:
- Priority level (High/Medium/Low)
- Expected impact
- Implementation complexity
- Timeline for implementation
"""

        response = await self.llm.ainvoke(optimization_prompt)

        # Parse AI response into structured recommendations
        # In a real implementation, you might use structured output or parsing
        recommendations = [
            {
                "id": f"rec_{int(time.time())}_{i}",
                "priority": "High",
                "category": "Cost Optimization",
                "description": "Implement request caching for repeated queries",
                "expected_impact": "15-25% cost reduction",
                "complexity": "Medium",
                "timeline": "1-2 weeks",
                "ai_reasoning": response.content
            }
            # Additional recommendations would be parsed from AI response
        ]

        return recommendations

    async def _project_costs(self) -> Dict[str, Any]:
        """Project costs for migration timeline"""
        current_metrics = await self._collect_current_metrics()

        # Calculate projections based on current usage
        daily_cost = current_metrics.daily_cost
        weekly_cost = daily_cost * 7
        monthly_cost = daily_cost * 30

        # Project to migration deadline
        deadline_progress = await self._check_deadline_progress()
        days_remaining = deadline_progress.get("days_remaining", 365)
        cost_to_deadline = daily_cost * days_remaining

        projections = {
            "current_daily_cost": daily_cost,
            "projected_weekly_cost": weekly_cost,
            "projected_monthly_cost": monthly_cost,
            "projected_cost_to_deadline": cost_to_deadline,
            "budget_utilization": {
                "monthly_budget": self.thresholds["monthly_budget"],
                "current_utilization": (monthly_cost / self.thresholds["monthly_budget"]) * 100,
                "remaining_budget": self.thresholds["monthly_budget"] - monthly_cost
            },
            "cost_trends": {
                "tokens_per_dollar": current_metrics.total_tokens / max(0.01, current_metrics.total_cost),
                "requests_per_dollar": current_metrics.total_requests / max(0.01, current_metrics.total_cost),
                "efficiency_score": self._calculate_cost_efficiency_score(current_metrics)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return projections

    def _calculate_cost_efficiency_score(self, metrics: MigrationMetrics) -> float:
        """Calculate cost efficiency score (0-100)"""
        # Base score on multiple factors
        score = 100.0

        # Penalize high error rate (wasted cost)
        if metrics.error_rate > 0:
            score -= min(50, metrics.error_rate * 5)  # -5 points per 1% error rate

        # Penalize high latency (inefficiency)
        if metrics.avg_latency > 2.0:  # Target under 2s
            score -= min(30, (metrics.avg_latency - 2.0) * 10)

        # Reward high token efficiency
        if metrics.tokens_per_request > 0:
            # Assume target of 500 tokens per request
            target_tokens = 500
            if metrics.tokens_per_request <= target_tokens:
                score += min(20, (target_tokens - metrics.tokens_per_request) / target_tokens * 20)

        return max(0, min(100, score))

    async def _check_deadline_progress(self) -> Dict[str, Any]:
        """Check progress toward migration deadline"""
        now = datetime.now(timezone.utc)
        time_remaining = self.MIGRATION_DEADLINE - now

        # Calculate progress based on current phase
        phase_progress = {
            MigrationPhase.PREPARATION: 20,
            MigrationPhase.TESTING: 40,
            MigrationPhase.GRADUAL_ROLLOUT: 70,
            MigrationPhase.FULL_MIGRATION: 90,
            MigrationPhase.COMPLETED: 100
        }

        current_progress = phase_progress.get(self.current_phase, 0)

        progress_info = {
            "migration_deadline": self.MIGRATION_DEADLINE.isoformat(),
            "current_time": now.isoformat(),
            "days_remaining": time_remaining.days,
            "hours_remaining": time_remaining.total_seconds() / 3600,
            "current_phase": self.current_phase.value,
            "progress_percentage": current_progress,
            "on_track": time_remaining.days > 0 and current_progress >= 50,
            "urgency_level": self._calculate_urgency_level(time_remaining.days, current_progress)
        }

        return progress_info

    def _calculate_urgency_level(self, days_remaining: int, progress_percentage: float) -> str:
        """Calculate urgency level based on time and progress"""
        if days_remaining <= 30 and progress_percentage < 80:
            return "critical"
        elif days_remaining <= 60 and progress_percentage < 60:
            return "high"
        elif days_remaining <= 90 and progress_percentage < 40:
            return "medium"
        else:
            return "low"

    async def _establish_baseline(self) -> Dict[str, Any]:
        """Establish performance baseline for comparison"""
        current_metrics = await self._collect_current_metrics()
        self.baseline_metrics = current_metrics

        baseline_info = {
            "baseline_established": datetime.now(timezone.utc).isoformat(),
            "baseline_metrics": current_metrics.__dict__,
            "comparison_targets": {
                "error_rate_target": "< 2%",
                "latency_target": "< 3s",
                "cost_efficiency_target": "> 80%",
                "success_rate_target": "> 98%"
            }
        }

        logger.info("Established migration baseline metrics")
        return baseline_info

    async def _compare_model_performance(self) -> Dict[str, Any]:
        """Compare performance across different models"""
        # This would integrate with actual model performance tracking
        # For now, we'll simulate model comparison

        models = ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4o-mini"]
        comparison = {}

        for model in models:
            # In real implementation, query actual performance data
            perf = ModelPerformance(
                model_name=model,
                requests=1000,
                success_rate=95.0 + (hash(model) % 5),  # Simulate variations
                avg_latency=2.0 + (hash(model) % 10) / 10,
                cost_efficiency=0.8 + (hash(model) % 20) / 100,
                quality_score=85.0 + (hash(model) % 15)
            )

            self.model_performance[model] = perf
            comparison[model] = perf.__dict__

        # Generate AI-powered comparison analysis
        comparison_prompt = f"""Analyze the performance comparison of different GPT models for the migration:

Model Performance Data:
{json.dumps(comparison, indent=2)}

Provide analysis on:
1. Which model offers the best cost-performance ratio
2. Quality vs cost trade-offs
3. Recommended model selection for different use cases
4. Migration strategy based on performance data
"""

        analysis = await self.llm.ainvoke(comparison_prompt)

        return {
            "model_comparison": comparison,
            "ai_analysis": analysis.content,
            "recommendation": "gpt-4o-mini",  # Based on analysis
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def _comprehensive_monitoring_cycle(self) -> Dict[str, Any]:
        """Run a complete monitoring cycle"""
        logger.info("Starting comprehensive monitoring cycle")

        results = {}

        try:
            # Collect current metrics
            results["metrics"] = await self._collect_current_metrics()

            # Check for alerts
            results["alerts"] = await self._check_thresholds_and_alert()

            # Analyze trends
            results["trends"] = await self._analyze_performance_trends()

            # Check deadline progress
            results["deadline_progress"] = await self._check_deadline_progress()

            # Generate recommendations if needed
            if results["alerts"] or results["deadline_progress"].get("urgency_level") in ["high", "critical"]:
                results["recommendations"] = await self._generate_optimization_recommendations()

            # Project costs
            results["cost_projections"] = await self._project_costs()

            results["monitoring_cycle_completed"] = datetime.now(timezone.utc).isoformat()
            results["status"] = "success"

        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}")
            results["status"] = "error"
            results["error"] = str(e)

        return results

    # Public API methods

    async def start_monitoring(self, phase: MigrationPhase = MigrationPhase.PREPARATION) -> TaskResult:
        """Start migration monitoring for a specific phase"""
        self.current_phase = phase
        logger.info(f"Started migration monitoring in {phase.value} phase")

        # Establish baseline if in preparation phase
        if phase == MigrationPhase.PREPARATION:
            await self._establish_baseline()

        result = await self.execute(
            "Start comprehensive migration monitoring",
            {"phase": phase.value}
        )

        return result

    async def update_thresholds(self, new_thresholds: Dict[str, float]) -> None:
        """Update alert thresholds"""
        self.thresholds.update(new_thresholds)
        logger.info(f"Updated thresholds: {new_thresholds}")

    async def advance_phase(self, new_phase: MigrationPhase) -> Dict[str, Any]:
        """Advance to next migration phase"""
        old_phase = self.current_phase
        self.current_phase = new_phase

        logger.info(f"Advanced migration phase: {old_phase.value} -> {new_phase.value}")

        # Generate phase transition report
        transition_report = await self._generate_migration_report()
        transition_report["phase_transition"] = {
            "from": old_phase.value,
            "to": new_phase.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return transition_report

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current data for dashboard display"""
        current_metrics = await self._collect_current_metrics()
        deadline_progress = await self._check_deadline_progress()
        active_alerts = [
            {
                "level": alert.level.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat()
            }
            for alert in self.active_alerts[-10:]  # Last 10 alerts
        ]

        return {
            "current_metrics": current_metrics.__dict__,
            "deadline_progress": deadline_progress,
            "active_alerts": active_alerts,
            "migration_phase": self.current_phase.value,
            "model_performance": {
                name: perf.__dict__ for name, perf in self.model_performance.items()
            },
            "cost_efficiency_score": self._calculate_cost_efficiency_score(current_metrics),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }