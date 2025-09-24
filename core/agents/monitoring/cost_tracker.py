"""
Cost Tracker for GPT-4.1 Migration

Specialized component for tracking API costs, budget management,
and cost optimization during the migration process.
"""

import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CostCategory(Enum):
    """Categories for cost tracking"""
    CONTENT_GENERATION = "content_generation"
    EDUCATIONAL_SUPPORT = "educational_support"
    TESTING_VALIDATION = "testing_validation"
    ANALYSIS = "analysis"
    MONITORING = "monitoring"
    OTHER = "other"


@dataclass
class CostEntry:
    """Individual cost entry"""
    timestamp: datetime
    model: str
    tokens_used: int
    cost: float
    category: CostCategory
    request_id: str
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetLimit:
    """Budget limit configuration"""
    period: str  # daily, weekly, monthly
    limit: float
    current_usage: float = 0.0
    alert_threshold: float = 0.8  # Alert at 80% of limit


@dataclass
class CostAnalysis:
    """Cost analysis results"""
    total_cost: float
    period_start: datetime
    period_end: datetime
    breakdown_by_model: Dict[str, float]
    breakdown_by_category: Dict[str, float]
    avg_cost_per_request: float
    tokens_per_dollar: float
    efficiency_score: float
    cost_trends: Dict[str, float]


class CostTracker:
    """
    Advanced cost tracking and budget management for GPT-4.1 migration.

    Features:
    - Real-time cost tracking by model and category
    - Budget limit monitoring and alerts
    - Cost optimization recommendations
    - Historical cost analysis and projections
    - Token efficiency tracking
    """

    # Model pricing (as of 2025 - update with actual rates)
    MODEL_PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},      # per 1K tokens
        "gpt-4o": {"input": 0.005, "output": 0.015},   # per 1K tokens
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # per 1K tokens
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},   # per 1K tokens
    }

    def __init__(self):
        self.cost_entries: List[CostEntry] = []
        self.budget_limits: Dict[str, BudgetLimit] = {
            "daily": BudgetLimit("daily", 100.0),
            "weekly": BudgetLimit("weekly", 500.0),
            "monthly": BudgetLimit("monthly", 2000.0)
        }

        # Cost optimization settings
        self.optimization_enabled = True
        self.auto_fallback_enabled = True
        self.cost_alert_recipients = []

        # Historical data
        self.daily_costs: Dict[str, float] = {}  # date -> total cost
        self.model_usage_history: Dict[str, List[Tuple[datetime, float]]] = {}

        logger.info("CostTracker initialized")

    def track_request_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        category: CostCategory = CostCategory.OTHER,
        request_id: str = "",
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """Track cost for a single API request"""

        # Calculate cost based on model pricing
        cost = self._calculate_request_cost(model, input_tokens, output_tokens)

        # Create cost entry
        entry = CostEntry(
            timestamp=datetime.now(timezone.utc),
            model=model,
            tokens_used=input_tokens + output_tokens,
            cost=cost,
            category=category,
            request_id=request_id or f"req_{int(datetime.now().timestamp())}",
            success=success,
            metadata=metadata or {}
        )

        # Store entry
        self.cost_entries.append(entry)

        # Update daily costs
        today = entry.timestamp.date().isoformat()
        self.daily_costs[today] = self.daily_costs.get(today, 0.0) + cost

        # Update model usage history
        if model not in self.model_usage_history:
            self.model_usage_history[model] = []
        self.model_usage_history[model].append((entry.timestamp, cost))

        # Update budget usage
        self._update_budget_usage(cost)

        # Check for budget alerts
        self._check_budget_alerts()

        logger.debug(f"Tracked cost: ${cost:.4f} for {model} ({input_tokens + output_tokens} tokens)")

        return cost

    def _calculate_request_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a request based on token usage"""

        if model not in self.MODEL_PRICING:
            logger.warning(f"Unknown model pricing for {model}, using gpt-4 rates")
            model = "gpt-4"

        pricing = self.MODEL_PRICING[model]

        # Calculate cost per 1K tokens
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]

        return input_cost + output_cost

    def _update_budget_usage(self, cost: float) -> None:
        """Update budget usage for all periods"""
        now = datetime.now(timezone.utc)

        for period, budget in self.budget_limits.items():
            # Calculate period start based on current time
            if period == "daily":
                period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "weekly":
                days_since_monday = now.weekday()
                period_start = (now - timedelta(days=days_since_monday)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            elif period == "monthly":
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                continue

            # Calculate total usage for this period
            period_entries = [
                entry for entry in self.cost_entries
                if entry.timestamp >= period_start and entry.success
            ]

            budget.current_usage = sum(entry.cost for entry in period_entries)

    def _check_budget_alerts(self) -> List[Dict[str, Any]]:
        """Check for budget threshold violations"""
        alerts = []

        for period, budget in self.budget_limits.items():
            usage_percentage = budget.current_usage / budget.limit

            if usage_percentage >= 1.0:
                alerts.append({
                    "level": "critical",
                    "message": f"{period.title()} budget exceeded: ${budget.current_usage:.2f} / ${budget.limit:.2f}",
                    "period": period,
                    "usage": budget.current_usage,
                    "limit": budget.limit,
                    "percentage": usage_percentage * 100
                })
            elif usage_percentage >= budget.alert_threshold:
                alerts.append({
                    "level": "warning",
                    "message": f"{period.title()} budget at {usage_percentage*100:.1f}%: ${budget.current_usage:.2f} / ${budget.limit:.2f}",
                    "period": period,
                    "usage": budget.current_usage,
                    "limit": budget.limit,
                    "percentage": usage_percentage * 100
                })

        if alerts:
            logger.warning(f"Budget alerts: {len(alerts)} violations detected")
            for alert in alerts:
                logger.warning(alert["message"])

        return alerts

    def get_cost_analysis(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> CostAnalysis:
        """Get comprehensive cost analysis for a period"""

        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now(timezone.utc)

        # Filter entries for the period
        period_entries = [
            entry for entry in self.cost_entries
            if start_date <= entry.timestamp <= end_date and entry.success
        ]

        if not period_entries:
            return CostAnalysis(
                total_cost=0.0,
                period_start=start_date,
                period_end=end_date,
                breakdown_by_model={},
                breakdown_by_category={},
                avg_cost_per_request=0.0,
                tokens_per_dollar=0.0,
                efficiency_score=0.0,
                cost_trends={}
            )

        # Calculate totals
        total_cost = sum(entry.cost for entry in period_entries)
        total_tokens = sum(entry.tokens_used for entry in period_entries)
        total_requests = len(period_entries)

        # Breakdown by model
        breakdown_by_model = {}
        for entry in period_entries:
            breakdown_by_model[entry.model] = breakdown_by_model.get(entry.model, 0.0) + entry.cost

        # Breakdown by category
        breakdown_by_category = {}
        for entry in period_entries:
            cat_name = entry.category.value
            breakdown_by_category[cat_name] = breakdown_by_category.get(cat_name, 0.0) + entry.cost

        # Calculate metrics
        avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0.0
        tokens_per_dollar = total_tokens / total_cost if total_cost > 0 else 0.0

        # Calculate efficiency score
        efficiency_score = self._calculate_efficiency_score(period_entries)

        # Calculate cost trends
        cost_trends = self._calculate_cost_trends(period_entries)

        return CostAnalysis(
            total_cost=total_cost,
            period_start=start_date,
            period_end=end_date,
            breakdown_by_model=breakdown_by_model,
            breakdown_by_category=breakdown_by_category,
            avg_cost_per_request=avg_cost_per_request,
            tokens_per_dollar=tokens_per_dollar,
            efficiency_score=efficiency_score,
            cost_trends=cost_trends
        )

    def _calculate_efficiency_score(self, entries: List[CostEntry]) -> float:
        """Calculate cost efficiency score (0-100)"""
        if not entries:
            return 0.0

        # Base efficiency on multiple factors
        score = 100.0

        # Factor 1: Model efficiency (prefer more efficient models)
        model_costs = {}
        for entry in entries:
            model_costs[entry.model] = model_costs.get(entry.model, 0.0) + entry.cost

        # Penalize usage of expensive models when cheaper alternatives exist
        if "gpt-4" in model_costs and "gpt-4o-mini" in model_costs:
            expensive_ratio = model_costs["gpt-4"] / sum(model_costs.values())
            score -= expensive_ratio * 30  # Up to 30 point penalty

        # Factor 2: Success rate (failed requests waste money)
        failed_entries = sum(1 for entry in entries if not entry.success)
        failure_rate = failed_entries / len(entries)
        score -= failure_rate * 40  # Up to 40 point penalty

        # Factor 3: Token efficiency
        avg_tokens = sum(entry.tokens_used for entry in entries) / len(entries)
        if avg_tokens > 1000:  # Penalize very long responses
            score -= min(20, (avg_tokens - 1000) / 100)  # Up to 20 point penalty

        return max(0.0, min(100.0, score))

    def _calculate_cost_trends(self, entries: List[CostEntry]) -> Dict[str, float]:
        """Calculate cost trends over the period"""
        if len(entries) < 2:
            return {}

        # Sort entries by timestamp
        sorted_entries = sorted(entries, key=lambda x: x.timestamp)

        # Split into first and second half
        mid_point = len(sorted_entries) // 2
        first_half = sorted_entries[:mid_point]
        second_half = sorted_entries[mid_point:]

        # Calculate average daily cost for each half
        first_half_cost = sum(entry.cost for entry in first_half)
        second_half_cost = sum(entry.cost for entry in second_half)

        first_half_days = (first_half[-1].timestamp - first_half[0].timestamp).days + 1
        second_half_days = (second_half[-1].timestamp - second_half[0].timestamp).days + 1

        first_avg_daily = first_half_cost / max(1, first_half_days)
        second_avg_daily = second_half_cost / max(1, second_half_days)

        # Calculate trend percentage
        if first_avg_daily > 0:
            cost_trend = ((second_avg_daily - first_avg_daily) / first_avg_daily) * 100
        else:
            cost_trend = 0.0

        return {
            "cost_change_percentage": cost_trend,
            "first_period_avg_daily": first_avg_daily,
            "second_period_avg_daily": second_avg_daily
        }

    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get cost optimization recommendations"""
        recommendations = []

        # Analyze recent cost data
        recent_analysis = self.get_cost_analysis(
            start_date=datetime.now(timezone.utc) - timedelta(days=7)
        )

        # Recommendation 1: Model optimization
        if "gpt-4" in recent_analysis.breakdown_by_model:
            gpt4_cost = recent_analysis.breakdown_by_model["gpt-4"]
            if gpt4_cost > recent_analysis.total_cost * 0.3:  # >30% of total cost
                recommendations.append({
                    "priority": "high",
                    "category": "model_optimization",
                    "title": "Consider GPT-4o-mini for non-critical tasks",
                    "description": f"GPT-4 accounts for ${gpt4_cost:.2f} ({gpt4_cost/recent_analysis.total_cost*100:.1f}%) of recent costs",
                    "potential_savings": gpt4_cost * 0.8,  # 80% savings with mini
                    "implementation": "Review GPT-4 usage and downgrade non-critical operations to GPT-4o-mini"
                })

        # Recommendation 2: Request efficiency
        if recent_analysis.avg_cost_per_request > 0.05:  # $0.05 per request
            recommendations.append({
                "priority": "medium",
                "category": "request_optimization",
                "title": "Optimize request size and prompts",
                "description": f"Average cost per request is ${recent_analysis.avg_cost_per_request:.4f}",
                "potential_savings": recent_analysis.total_cost * 0.2,  # 20% savings
                "implementation": "Reduce prompt length, use more efficient prompting techniques"
            })

        # Recommendation 3: Caching
        if recent_analysis.efficiency_score < 70:
            recommendations.append({
                "priority": "high",
                "category": "caching",
                "title": "Implement response caching",
                "description": f"Efficiency score is {recent_analysis.efficiency_score:.1f}/100",
                "potential_savings": recent_analysis.total_cost * 0.3,  # 30% savings
                "implementation": "Cache common requests and responses to reduce API calls"
            })

        # Recommendation 4: Budget management
        budget_alerts = self._check_budget_alerts()
        if any(alert["level"] == "critical" for alert in budget_alerts):
            recommendations.append({
                "priority": "critical",
                "category": "budget_control",
                "title": "Implement immediate cost controls",
                "description": "Budget limits exceeded",
                "potential_savings": "Prevent budget overrun",
                "implementation": "Temporarily throttle requests, review high-cost operations"
            })

        return recommendations

    def project_monthly_cost(self) -> Dict[str, Any]:
        """Project monthly cost based on current usage patterns"""

        # Get current month data
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        current_month_analysis = self.get_cost_analysis(
            start_date=month_start,
            end_date=now
        )

        # Calculate days elapsed and remaining
        days_elapsed = (now - month_start).days + 1
        days_in_month = 31  # Conservative estimate
        days_remaining = days_in_month - days_elapsed

        # Project based on current daily average
        if days_elapsed > 0:
            daily_average = current_month_analysis.total_cost / days_elapsed
            projected_total = daily_average * days_in_month
            projected_remaining = daily_average * days_remaining
        else:
            daily_average = 0.0
            projected_total = 0.0
            projected_remaining = 0.0

        monthly_limit = self.budget_limits["monthly"].limit

        return {
            "current_month_cost": current_month_analysis.total_cost,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "daily_average": daily_average,
            "projected_monthly_total": projected_total,
            "projected_remaining_cost": projected_remaining,
            "monthly_budget": monthly_limit,
            "budget_utilization_percentage": (projected_total / monthly_limit) * 100,
            "is_over_budget": projected_total > monthly_limit,
            "excess_amount": max(0, projected_total - monthly_limit)
        }

    def export_cost_data(self, format: str = "json") -> str:
        """Export cost data for external analysis"""

        data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_entries": len(self.cost_entries),
            "budget_limits": {
                period: {
                    "limit": budget.limit,
                    "current_usage": budget.current_usage,
                    "alert_threshold": budget.alert_threshold
                }
                for period, budget in self.budget_limits.items()
            },
            "recent_analysis": self.get_cost_analysis().__dict__,
            "cost_entries": [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "model": entry.model,
                    "tokens_used": entry.tokens_used,
                    "cost": entry.cost,
                    "category": entry.category.value,
                    "request_id": entry.request_id,
                    "success": entry.success,
                    "metadata": entry.metadata
                }
                for entry in self.cost_entries[-1000:]  # Last 1000 entries
            ]
        }

        if format.lower() == "json":
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def set_budget_limit(self, period: str, limit: float, alert_threshold: float = 0.8) -> None:
        """Set or update budget limit for a period"""

        if period not in self.budget_limits:
            self.budget_limits[period] = BudgetLimit(period, limit, 0.0, alert_threshold)
        else:
            self.budget_limits[period].limit = limit
            self.budget_limits[period].alert_threshold = alert_threshold

        logger.info(f"Set {period} budget limit to ${limit:.2f} (alert at {alert_threshold*100:.1f}%)")

    def reset_period_usage(self, period: str) -> None:
        """Reset usage for a specific period (for testing or manual reset)"""
        if period in self.budget_limits:
            self.budget_limits[period].current_usage = 0.0
            logger.info(f"Reset {period} usage to $0.00")

    def get_model_efficiency_ranking(self) -> List[Dict[str, Any]]:
        """Get models ranked by cost efficiency"""

        model_stats = {}

        for entry in self.cost_entries:
            if entry.success:  # Only count successful requests
                if entry.model not in model_stats:
                    model_stats[entry.model] = {
                        "total_cost": 0.0,
                        "total_tokens": 0,
                        "request_count": 0
                    }

                model_stats[entry.model]["total_cost"] += entry.cost
                model_stats[entry.model]["total_tokens"] += entry.tokens_used
                model_stats[entry.model]["request_count"] += 1

        # Calculate efficiency metrics
        efficiency_ranking = []

        for model, stats in model_stats.items():
            if stats["total_cost"] > 0:
                tokens_per_dollar = stats["total_tokens"] / stats["total_cost"]
                cost_per_request = stats["total_cost"] / stats["request_count"]

                efficiency_ranking.append({
                    "model": model,
                    "tokens_per_dollar": tokens_per_dollar,
                    "cost_per_request": cost_per_request,
                    "total_requests": stats["request_count"],
                    "total_cost": stats["total_cost"],
                    "efficiency_score": tokens_per_dollar / cost_per_request  # Higher is better
                })

        # Sort by efficiency score (highest first)
        efficiency_ranking.sort(key=lambda x: x["efficiency_score"], reverse=True)

        return efficiency_ranking