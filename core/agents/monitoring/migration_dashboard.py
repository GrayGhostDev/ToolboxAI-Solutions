"""
Migration Dashboard for GPT-4.1 Monitoring

Provides a comprehensive dashboard interface for monitoring the GPT-4.1 migration
progress, including real-time metrics, visualizations, and management controls.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from .gpt4_migration_monitor import GPT4MigrationMonitor, MigrationPhase
from .cost_tracker import CostTracker, CostCategory
from .performance_analyzer import PerformanceAnalyzer, PerformanceMetric
from .alert_manager import AlertManager, AlertSeverity, AlertCategory

logger = logging.getLogger(__name__)


@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    id: str
    title: str
    type: str  # chart, metric, table, alert
    size: str  # small, medium, large
    position: Tuple[int, int]  # row, column
    config: Dict[str, Any] = field(default_factory=dict)
    data_source: str = ""
    refresh_interval: int = 30  # seconds


@dataclass
class DashboardLayout:
    """Dashboard layout configuration"""
    name: str
    description: str
    widgets: List[DashboardWidget]
    auto_refresh: bool = True
    refresh_interval: int = 30


class MigrationDashboard:
    """
    Comprehensive dashboard for GPT-4.1 migration monitoring.

    Features:
    - Real-time metrics display
    - Interactive charts and visualizations
    - Alert management interface
    - Cost tracking and projections
    - Performance monitoring
    - Migration progress tracking
    - Customizable layouts
    """

    def __init__(
        self,
        migration_monitor: GPT4MigrationMonitor,
        cost_tracker: CostTracker,
        performance_analyzer: PerformanceAnalyzer,
        alert_manager: AlertManager
    ):
        self.migration_monitor = migration_monitor
        self.cost_tracker = cost_tracker
        self.performance_analyzer = performance_analyzer
        self.alert_manager = alert_manager

        # Dashboard state
        self.current_layout = "default"
        self.layouts: Dict[str, DashboardLayout] = {}
        self.user_preferences: Dict[str, Any] = {}

        # Real-time data cache
        self.data_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, datetime] = {}

        # Initialize default layouts
        self._initialize_default_layouts()

        logger.info("MigrationDashboard initialized")

    def _initialize_default_layouts(self) -> None:
        """Initialize default dashboard layouts"""

        # Executive Summary Layout
        executive_layout = DashboardLayout(
            name="executive",
            description="High-level executive summary for leadership",
            widgets=[
                DashboardWidget(
                    id="migration_progress",
                    title="Migration Progress",
                    type="progress_circle",
                    size="large",
                    position=(0, 0),
                    config={"show_deadline": True, "color_scheme": "blue"},
                    data_source="migration_progress"
                ),
                DashboardWidget(
                    id="cost_summary",
                    title="Cost Summary",
                    type="metric_card",
                    size="medium",
                    position=(0, 1),
                    config={"format": "currency", "trend": True},
                    data_source="cost_summary"
                ),
                DashboardWidget(
                    id="performance_score",
                    title="Overall Performance",
                    type="gauge",
                    size="medium",
                    position=(0, 2),
                    config={"min": 0, "max": 100, "thresholds": [50, 75, 90]},
                    data_source="performance_score"
                ),
                DashboardWidget(
                    id="active_alerts",
                    title="Critical Alerts",
                    type="alert_list",
                    size="large",
                    position=(1, 0),
                    config={"severity_filter": ["critical", "emergency"], "max_items": 5},
                    data_source="active_alerts"
                ),
                DashboardWidget(
                    id="cost_projection",
                    title="Monthly Cost Projection",
                    type="line_chart",
                    size="large",
                    position=(1, 1),
                    config={"time_range": "30d", "show_budget_line": True},
                    data_source="cost_trends"
                )
            ]
        )

        # Technical Operations Layout
        technical_layout = DashboardLayout(
            name="technical",
            description="Detailed technical metrics for operations team",
            widgets=[
                DashboardWidget(
                    id="api_latency",
                    title="API Latency",
                    type="time_series",
                    size="large",
                    position=(0, 0),
                    config={"time_range": "24h", "metrics": ["p50", "p95", "p99"]},
                    data_source="latency_metrics"
                ),
                DashboardWidget(
                    id="error_rates",
                    title="Error Rates by Model",
                    type="bar_chart",
                    size="medium",
                    position=(0, 1),
                    config={"group_by": "model", "time_range": "24h"},
                    data_source="error_rates"
                ),
                DashboardWidget(
                    id="throughput",
                    title="Request Throughput",
                    type="area_chart",
                    size="medium",
                    position=(0, 2),
                    config={"time_range": "24h", "aggregate": "requests_per_minute"},
                    data_source="throughput_metrics"
                ),
                DashboardWidget(
                    id="model_performance",
                    title="Model Performance Comparison",
                    type="comparison_table",
                    size="large",
                    position=(1, 0),
                    config={"metrics": ["latency", "success_rate", "cost_efficiency"]},
                    data_source="model_comparison"
                ),
                DashboardWidget(
                    id="token_usage",
                    title="Token Usage Patterns",
                    type="stacked_area",
                    size="large",
                    position=(1, 1),
                    config={"time_range": "7d", "group_by": "model"},
                    data_source="token_usage"
                ),
                DashboardWidget(
                    id="system_health",
                    title="System Health",
                    type="status_grid",
                    size="medium",
                    position=(2, 0),
                    config={"show_last_check": True},
                    data_source="system_health"
                )
            ]
        )

        # Cost Management Layout
        cost_layout = DashboardLayout(
            name="cost",
            description="Comprehensive cost tracking and optimization",
            widgets=[
                DashboardWidget(
                    id="daily_costs",
                    title="Daily Cost Breakdown",
                    type="column_chart",
                    size="large",
                    position=(0, 0),
                    config={"time_range": "30d", "stack_by": "category"},
                    data_source="daily_costs"
                ),
                DashboardWidget(
                    id="budget_utilization",
                    title="Budget Utilization",
                    type="progress_bar",
                    size="medium",
                    position=(0, 1),
                    config={"show_percentage": True, "show_remaining": True},
                    data_source="budget_status"
                ),
                DashboardWidget(
                    id="cost_per_model",
                    title="Cost by Model",
                    type="pie_chart",
                    size="medium",
                    position=(0, 2),
                    config={"time_range": "7d"},
                    data_source="cost_by_model"
                ),
                DashboardWidget(
                    id="efficiency_metrics",
                    title="Cost Efficiency Metrics",
                    type="metric_grid",
                    size="large",
                    position=(1, 0),
                    config={"metrics": ["cost_per_request", "tokens_per_dollar", "efficiency_score"]},
                    data_source="efficiency_metrics"
                ),
                DashboardWidget(
                    id="optimization_recommendations",
                    title="Cost Optimization Opportunities",
                    type="recommendation_list",
                    size="large",
                    position=(1, 1),
                    config={"priority_filter": ["high", "critical"], "max_items": 10},
                    data_source="cost_recommendations"
                )
            ]
        )

        # Store layouts
        self.layouts = {
            "executive": executive_layout,
            "technical": technical_layout,
            "cost": cost_layout,
            "default": executive_layout  # Default to executive view
        }

    async def get_dashboard_data(
        self,
        layout_name: str = "default",
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard data for specified layout"""

        if layout_name not in self.layouts:
            layout_name = "default"

        layout = self.layouts[layout_name]

        # Collect data for all widgets in the layout
        dashboard_data = {
            "layout": {
                "name": layout.name,
                "description": layout.description,
                "auto_refresh": layout.auto_refresh,
                "refresh_interval": layout.refresh_interval
            },
            "widgets": {},
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "layout_name": layout_name,
                "data_freshness": {}
            }
        }

        # Collect data for each widget
        for widget in layout.widgets:
            try:
                widget_data = await self._get_widget_data(widget, force_refresh)
                dashboard_data["widgets"][widget.id] = widget_data
                dashboard_data["metadata"]["data_freshness"][widget.id] = widget_data.get("last_updated")
            except Exception as e:
                logger.error(f"Failed to get data for widget {widget.id}: {e}")
                dashboard_data["widgets"][widget.id] = {"error": str(e)}

        return dashboard_data

    async def _get_widget_data(self, widget: DashboardWidget, force_refresh: bool = False) -> Dict[str, Any]:
        """Get data for a specific widget"""

        # Check cache first (unless force refresh)
        cache_key = f"{widget.id}_{widget.data_source}"
        if not force_refresh and self._is_cache_valid(cache_key, widget.refresh_interval):
            return self.data_cache[cache_key]

        # Generate fresh data based on data source
        data = await self._generate_widget_data(widget)

        # Cache the data
        self.data_cache[cache_key] = data
        self.cache_timestamps[cache_key] = datetime.now(timezone.utc)

        return data

    def _is_cache_valid(self, cache_key: str, max_age_seconds: int) -> bool:
        """Check if cached data is still valid"""

        if cache_key not in self.data_cache or cache_key not in self.cache_timestamps:
            return False

        age = (datetime.now(timezone.utc) - self.cache_timestamps[cache_key]).total_seconds()
        return age < max_age_seconds

    async def _generate_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Generate data for widget based on its data source"""

        data_source = widget.data_source
        config = widget.config

        try:
            if data_source == "migration_progress":
                return await self._get_migration_progress_data(config)
            elif data_source == "cost_summary":
                return await self._get_cost_summary_data(config)
            elif data_source == "performance_score":
                return await self._get_performance_score_data(config)
            elif data_source == "active_alerts":
                return await self._get_active_alerts_data(config)
            elif data_source == "cost_trends":
                return await self._get_cost_trends_data(config)
            elif data_source == "latency_metrics":
                return await self._get_latency_metrics_data(config)
            elif data_source == "error_rates":
                return await self._get_error_rates_data(config)
            elif data_source == "throughput_metrics":
                return await self._get_throughput_metrics_data(config)
            elif data_source == "model_comparison":
                return await self._get_model_comparison_data(config)
            elif data_source == "token_usage":
                return await self._get_token_usage_data(config)
            elif data_source == "system_health":
                return await self._get_system_health_data(config)
            elif data_source == "daily_costs":
                return await self._get_daily_costs_data(config)
            elif data_source == "budget_status":
                return await self._get_budget_status_data(config)
            elif data_source == "cost_by_model":
                return await self._get_cost_by_model_data(config)
            elif data_source == "efficiency_metrics":
                return await self._get_efficiency_metrics_data(config)
            elif data_source == "cost_recommendations":
                return await self._get_cost_recommendations_data(config)
            else:
                return {"error": f"Unknown data source: {data_source}"}

        except Exception as e:
            logger.error(f"Failed to generate data for {data_source}: {e}")
            return {"error": str(e)}

    async def _get_migration_progress_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get migration progress data"""

        deadline_progress = await self.migration_monitor._check_deadline_progress()

        return {
            "widget_type": "progress_circle",
            "data": {
                "progress_percentage": deadline_progress["progress_percentage"],
                "days_remaining": deadline_progress["days_remaining"],
                "current_phase": deadline_progress["current_phase"],
                "urgency_level": deadline_progress["urgency_level"],
                "on_track": deadline_progress["on_track"],
                "deadline": deadline_progress["migration_deadline"]
            },
            "config": config,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _get_cost_summary_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get cost summary data"""

        # Get current month projection
        projection = self.cost_tracker.project_monthly_cost()

        # Get recent cost analysis
        analysis = self.cost_tracker.get_cost_analysis(
            start_date=datetime.now(timezone.utc) - timedelta(days=7)
        )

        return {
            "widget_type": "metric_card",
            "data": {
                "current_monthly_cost": projection["current_month_cost"],
                "projected_monthly_total": projection["projected_monthly_total"],
                "daily_average": projection["daily_average"],
                "budget_utilization": projection["budget_utilization_percentage"],
                "weekly_total": analysis.total_cost,
                "trend_percentage": analysis.cost_trends.get("cost_change_percentage", 0)
            },
            "config": config,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _get_performance_score_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get overall performance score data"""

        # Get performance data for primary model (gpt-4o)
        real_time_metrics = self.performance_analyzer.get_real_time_metrics("gpt-4o")

        return {
            "widget_type": "gauge",
            "data": {
                "score": real_time_metrics["performance_score"],
                "status": real_time_metrics["status"],
                "anomaly_count": len(real_time_metrics["anomalies"]),
                "metrics": real_time_metrics["metrics"]
            },
            "config": config,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _get_active_alerts_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get active alerts data"""

        # Filter alerts based on config
        severity_filter = config.get("severity_filter", [])
        max_items = config.get("max_items", 10)

        # Convert string severity to enum
        severity_enums = []
        for severity in severity_filter:
            try:
                severity_enums.append(AlertSeverity(severity))
            except ValueError:
                continue

        active_alerts = self.alert_manager.get_active_alerts(
            severity_filter=severity_enums if severity_enums else None
        )

        return {
            "widget_type": "alert_list",
            "data": {
                "alerts": [
                    {
                        "id": alert.id,
                        "title": alert.title,
                        "message": alert.message,
                        "severity": alert.severity.value,
                        "category": alert.category.value,
                        "timestamp": alert.timestamp.isoformat(),
                        "acknowledged": alert.acknowledged,
                        "escalation_level": alert.escalation_level
                    }
                    for alert in active_alerts[:max_items]
                ],
                "total_count": len(active_alerts),
                "severity_breakdown": {
                    severity.value: len([a for a in active_alerts if a.severity == severity])
                    for severity in AlertSeverity
                }
            },
            "config": config,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _get_cost_trends_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get cost trends data for charting"""

        time_range = config.get("time_range", "30d")
        days_back = int(time_range.rstrip("d"))

        # Get daily costs for the period
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        # Generate time series data
        daily_data = []
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.date().isoformat()
            daily_cost = self.cost_tracker.daily_costs.get(date_str, 0.0)

            daily_data.append({
                "date": date_str,
                "cost": daily_cost,
                "timestamp": current_date.isoformat()
            })

            current_date += timedelta(days=1)

        # Calculate projection line
        projection = self.cost_tracker.project_monthly_cost()
        budget_line = projection["monthly_budget"] / 30  # Daily budget

        return {
            "widget_type": "line_chart",
            "data": {
                "series": [
                    {
                        "name": "Daily Cost",
                        "data": daily_data
                    }
                ],
                "budget_line": budget_line if config.get("show_budget_line") else None,
                "time_range": time_range
            },
            "config": config,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _get_model_comparison_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get model performance comparison data"""

        models = ["gpt-4", "gpt-4o", "gpt-4o-mini"]
        comparison_data = []

        for model in models:
            try:
                summary = self.performance_analyzer.generate_performance_summary(model)
                comparison_data.append({
                    "model": model,
                    "performance_score": summary.overall_score,
                    "metrics": summary.metrics,
                    "anomaly_count": len(summary.anomalies)
                })
            except Exception as e:
                logger.warning(f"Failed to get comparison data for {model}: {e}")

        return {
            "widget_type": "comparison_table",
            "data": {
                "models": comparison_data,
                "metrics": config.get("metrics", ["latency", "success_rate", "cost_efficiency"])
            },
            "config": config,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    # Placeholder methods for other data sources
    async def _get_latency_metrics_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"widget_type": "time_series", "data": {"placeholder": True}, "config": config, "last_updated": datetime.now(timezone.utc).isoformat()}

    async def _get_error_rates_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"widget_type": "bar_chart", "data": {"placeholder": True}, "config": config, "last_updated": datetime.now(timezone.utc).isoformat()}

    async def _get_throughput_metrics_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"widget_type": "area_chart", "data": {"placeholder": True}, "config": config, "last_updated": datetime.now(timezone.utc).isoformat()}

    async def _get_token_usage_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"widget_type": "stacked_area", "data": {"placeholder": True}, "config": config, "last_updated": datetime.now(timezone.utc).isoformat()}

    async def _get_system_health_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"widget_type": "status_grid", "data": {"placeholder": True}, "config": config, "last_updated": datetime.now(timezone.utc).isoformat()}

    async def _get_daily_costs_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"widget_type": "column_chart", "data": {"placeholder": True}, "config": config, "last_updated": datetime.now(timezone.utc).isoformat()}

    async def _get_budget_status_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        projection = self.cost_tracker.project_monthly_cost()
        return {
            "widget_type": "progress_bar",
            "data": {
                "utilization_percentage": projection["budget_utilization_percentage"],
                "current_amount": projection["current_month_cost"],
                "budget_amount": projection["monthly_budget"],
                "remaining_amount": projection["monthly_budget"] - projection["current_month_cost"],
                "is_over_budget": projection["is_over_budget"]
            },
            "config": config,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _get_cost_by_model_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        time_range = config.get("time_range", "7d")
        days_back = int(time_range.rstrip("d"))

        analysis = self.cost_tracker.get_cost_analysis(
            start_date=datetime.now(timezone.utc) - timedelta(days=days_back)
        )

        return {
            "widget_type": "pie_chart",
            "data": {
                "breakdown": analysis.breakdown_by_model,
                "total": analysis.total_cost
            },
            "config": config,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _get_efficiency_metrics_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        analysis = self.cost_tracker.get_cost_analysis()
        return {
            "widget_type": "metric_grid",
            "data": {
                "cost_per_request": analysis.avg_cost_per_request,
                "tokens_per_dollar": analysis.tokens_per_dollar,
                "efficiency_score": analysis.efficiency_score
            },
            "config": config,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _get_cost_recommendations_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        recommendations = self.cost_tracker.get_optimization_recommendations()

        # Filter by priority if specified
        priority_filter = config.get("priority_filter", [])
        if priority_filter:
            recommendations = [
                rec for rec in recommendations
                if rec.get("priority", "").lower() in [p.lower() for p in priority_filter]
            ]

        max_items = config.get("max_items", 10)

        return {
            "widget_type": "recommendation_list",
            "data": {
                "recommendations": recommendations[:max_items]
            },
            "config": config,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    # Dashboard management methods

    def get_available_layouts(self) -> List[Dict[str, str]]:
        """Get list of available dashboard layouts"""
        return [
            {
                "name": name,
                "description": layout.description,
                "widget_count": len(layout.widgets)
            }
            for name, layout in self.layouts.items()
        ]

    def set_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> None:
        """Set user-specific dashboard preferences"""
        self.user_preferences[user_id] = preferences
        logger.info(f"Updated preferences for user {user_id}")

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user-specific dashboard preferences"""
        return self.user_preferences.get(user_id, {})

    async def export_dashboard_data(self, layout_name: str = "default") -> str:
        """Export dashboard data as JSON"""
        dashboard_data = await self.get_dashboard_data(layout_name, force_refresh=True)
        return json.dumps(dashboard_data, indent=2, default=str)

    def clear_cache(self) -> None:
        """Clear all cached dashboard data"""
        self.data_cache.clear()
        self.cache_timestamps.clear()
        logger.info("Dashboard cache cleared")

    async def get_real_time_update(self, widget_ids: List[str]) -> Dict[str, Any]:
        """Get real-time updates for specific widgets"""

        updates = {}

        for widget_id in widget_ids:
            # Find the widget in current layouts
            widget = None
            for layout in self.layouts.values():
                for w in layout.widgets:
                    if w.id == widget_id:
                        widget = w
                        break
                if widget:
                    break

            if widget:
                try:
                    updates[widget_id] = await self._get_widget_data(widget, force_refresh=True)
                except Exception as e:
                    updates[widget_id] = {"error": str(e)}

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "updates": updates
        }