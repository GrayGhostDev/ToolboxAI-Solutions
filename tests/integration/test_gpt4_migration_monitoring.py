"""
Integration tests for the GPT-4.1 Migration Monitoring System

Tests the complete GPT-4.1 migration monitoring pipeline including:
- Migration monitoring agent
- Cost tracking
- Performance analysis
- Alert management
- Dashboard integration
- API endpoints
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Test imports
from core.agents.monitoring.gpt4_migration_monitor import (
    GPT4MigrationMonitor,
    MigrationPhase,
    MigrationMetrics,
    AlertLevel
)
from core.agents.monitoring.cost_tracker import (
    CostTracker,
    CostCategory,
    CostEntry
)
from core.agents.monitoring.performance_analyzer import (
    PerformanceAnalyzer,
    PerformanceMetric,
    PerformanceDataPoint
)
from core.agents.monitoring.alert_manager import (
    AlertManager,
    AlertSeverity,
    AlertCategory,
    Alert
)
from core.agents.monitoring.migration_dashboard import MigrationDashboard
from core.agents.monitoring.migration_integration import GPT4MigrationSystem

from core.agents.base_agent import AgentConfig


class TestGPT4MigrationMonitor:
    """Test the main migration monitoring agent"""

    @pytest.fixture
    def migration_monitor(self):
        """Create a migration monitor instance for testing"""
        config = AgentConfig(
            name="TestMigrationMonitor",
            model="gpt-4o-mini",
            temperature=0.1
        )
        return GPT4MigrationMonitor(config)

    @pytest.mark.asyncio
    async def test_initialization(self, migration_monitor):
        """Test migration monitor initialization"""
        assert migration_monitor.name == "GPT4MigrationMonitor"
        assert migration_monitor.current_phase == MigrationPhase.PREPARATION
        assert migration_monitor.MIGRATION_DEADLINE.year == 2025
        assert migration_monitor.MIGRATION_DEADLINE.month == 7
        assert migration_monitor.MIGRATION_DEADLINE.day == 14

    @pytest.mark.asyncio
    async def test_collect_metrics(self, migration_monitor):
        """Test metrics collection"""
        metrics = await migration_monitor._collect_current_metrics()

        assert isinstance(metrics, MigrationMetrics)
        assert metrics.total_requests >= 0
        assert metrics.error_rate >= 0
        assert metrics.total_cost >= 0

    @pytest.mark.asyncio
    async def test_deadline_progress(self, migration_monitor):
        """Test deadline progress calculation"""
        progress = await migration_monitor._check_deadline_progress()

        assert "days_remaining" in progress
        assert "progress_percentage" in progress
        assert "urgency_level" in progress
        assert progress["migration_deadline"] is not None

    @pytest.mark.asyncio
    async def test_migration_report(self, migration_monitor):
        """Test migration report generation"""
        report = await migration_monitor._generate_migration_report()

        assert "report_id" in report
        assert "migration_phase" in report
        assert "deadline_info" in report
        assert "current_metrics" in report

    @pytest.mark.asyncio
    async def test_phase_advancement(self, migration_monitor):
        """Test migration phase advancement"""
        # Start in preparation phase
        assert migration_monitor.current_phase == MigrationPhase.PREPARATION

        # Advance to testing phase
        report = await migration_monitor.advance_phase(MigrationPhase.TESTING)

        assert migration_monitor.current_phase == MigrationPhase.TESTING
        assert "phase_transition" in report
        assert report["phase_transition"]["to"] == "testing"


class TestCostTracker:
    """Test the cost tracking system"""

    @pytest.fixture
    def cost_tracker(self):
        """Create a cost tracker instance for testing"""
        return CostTracker()

    def test_initialization(self, cost_tracker):
        """Test cost tracker initialization"""
        assert len(cost_tracker.cost_entries) == 0
        assert "daily" in cost_tracker.budget_limits
        assert "monthly" in cost_tracker.budget_limits
        assert cost_tracker.MODEL_PRICING["gpt-4o-mini"]["input"] < cost_tracker.MODEL_PRICING["gpt-4"]["input"]

    def test_track_request_cost(self, cost_tracker):
        """Test API request cost tracking"""
        cost = cost_tracker.track_request_cost(
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
            category=CostCategory.CONTENT_GENERATION,
            success=True
        )

        assert cost > 0
        assert len(cost_tracker.cost_entries) == 1

        entry = cost_tracker.cost_entries[0]
        assert entry.model == "gpt-4o-mini"
        assert entry.tokens_used == 150
        assert entry.success == True
        assert entry.category == CostCategory.CONTENT_GENERATION

    def test_cost_analysis(self, cost_tracker):
        """Test cost analysis functionality"""
        # Add some test data
        for i in range(10):
            cost_tracker.track_request_cost(
                model="gpt-4o-mini",
                input_tokens=100 + i * 10,
                output_tokens=50 + i * 5,
                category=CostCategory.CONTENT_GENERATION,
                success=i % 10 != 0  # 10% failure rate
            )

        analysis = cost_tracker.get_cost_analysis()

        assert analysis.total_cost > 0
        assert analysis.avg_cost_per_request > 0
        assert analysis.tokens_per_dollar > 0
        assert "gpt-4o-mini" in analysis.breakdown_by_model
        assert "content_generation" in analysis.breakdown_by_category

    def test_budget_alerts(self, cost_tracker):
        """Test budget alert generation"""
        # Set a low budget for testing
        cost_tracker.set_budget_limit("daily", 0.01)

        # Add costs that exceed the budget
        for i in range(5):
            cost_tracker.track_request_cost(
                model="gpt-4",
                input_tokens=1000,
                output_tokens=500,
                category=CostCategory.CONTENT_GENERATION,
                success=True
            )

        alerts = cost_tracker._check_budget_alerts()
        assert len(alerts) > 0
        assert any(alert["level"] == "critical" for alert in alerts)

    def test_optimization_recommendations(self, cost_tracker):
        """Test cost optimization recommendations"""
        # Add expensive model usage
        for i in range(5):
            cost_tracker.track_request_cost(
                model="gpt-4",
                input_tokens=1000,
                output_tokens=500,
                category=CostCategory.CONTENT_GENERATION,
                success=True
            )

        recommendations = cost_tracker.get_optimization_recommendations()
        assert len(recommendations) > 0
        assert any("gpt-4o-mini" in rec.get("description", "").lower() for rec in recommendations)


class TestPerformanceAnalyzer:
    """Test the performance analysis system"""

    @pytest.fixture
    def performance_analyzer(self):
        """Create a performance analyzer instance for testing"""
        return PerformanceAnalyzer()

    def test_initialization(self, performance_analyzer):
        """Test performance analyzer initialization"""
        assert len(performance_analyzer.data_points) == 0
        assert PerformanceMetric.LATENCY in performance_analyzer.anomaly_thresholds
        assert "gpt-4o" in performance_analyzer.performance_targets

    def test_record_performance_data(self, performance_analyzer):
        """Test recording performance data"""
        performance_analyzer.record_performance_data(
            PerformanceMetric.LATENCY,
            2.5,
            "gpt-4o",
            "/v1/chat/completions"
        )

        assert len(performance_analyzer.data_points) == 1
        data_point = performance_analyzer.data_points[0]
        assert data_point.metric_type == PerformanceMetric.LATENCY
        assert data_point.value == 2.5
        assert data_point.model == "gpt-4o"

    def test_establish_baseline(self, performance_analyzer):
        """Test baseline establishment"""
        # Add some data points
        for i in range(10):
            performance_analyzer.record_performance_data(
                PerformanceMetric.LATENCY,
                2.0 + i * 0.1,
                "gpt-4o"
            )

        baseline = performance_analyzer.establish_baseline("gpt-4o")

        assert PerformanceMetric.LATENCY in baseline
        assert baseline[PerformanceMetric.LATENCY] > 0

    def test_anomaly_detection(self, performance_analyzer):
        """Test performance anomaly detection"""
        # Establish baseline
        for i in range(20):
            performance_analyzer.record_performance_data(
                PerformanceMetric.LATENCY,
                2.0 + (i % 5) * 0.1,
                "gpt-4o"
            )

        performance_analyzer.establish_baseline("gpt-4o")

        # Add anomalous data point
        performance_analyzer.record_performance_data(
            PerformanceMetric.LATENCY,
            10.0,  # Very high latency
            "gpt-4o"
        )

        anomalies = performance_analyzer.detect_anomalies("gpt-4o")

        # Should detect the high latency anomaly
        latency_anomalies = [a for a in anomalies if a.metric_type == PerformanceMetric.LATENCY]
        assert len(latency_anomalies) > 0

    def test_performance_trends(self, performance_analyzer):
        """Test performance trend analysis"""
        # Add trending data
        for i in range(20):
            performance_analyzer.record_performance_data(
                PerformanceMetric.LATENCY,
                1.0 + i * 0.1,  # Increasing latency trend
                "gpt-4o"
            )

        trends = performance_analyzer.analyze_performance_trends("gpt-4o")

        assert PerformanceMetric.LATENCY in trends
        # Should show increasing trend
        assert trends[PerformanceMetric.LATENCY]["trend_percentage"] > 0

    def test_performance_summary(self, performance_analyzer):
        """Test performance summary generation"""
        # Add various performance data
        metrics = [
            (PerformanceMetric.LATENCY, 2.0),
            (PerformanceMetric.SUCCESS_RATE, 0.95),
            (PerformanceMetric.ERROR_RATE, 0.05)
        ]

        for metric, value in metrics:
            for i in range(10):
                performance_analyzer.record_performance_data(metric, value, "gpt-4o")

        summary = performance_analyzer.generate_performance_summary("gpt-4o")

        assert summary.model == "gpt-4o"
        assert summary.overall_score >= 0
        assert summary.overall_score <= 100
        assert len(summary.metrics) > 0


class TestAlertManager:
    """Test the alert management system"""

    @pytest.fixture
    def alert_manager(self):
        """Create an alert manager instance for testing"""
        return AlertManager()

    def test_initialization(self, alert_manager):
        """Test alert manager initialization"""
        assert len(alert_manager.active_alerts) == 0
        assert len(alert_manager.alert_rules) > 0
        assert "cost_budget_exceeded" in alert_manager.alert_rules

    @pytest.mark.asyncio
    async def test_trigger_alert(self, alert_manager):
        """Test alert triggering"""
        alert = await alert_manager.trigger_alert(
            "error_rate_high",
            "Error rate is elevated",
            0.08,  # 8% error rate
            {"model": "gpt-4"}
        )

        assert alert is not None
        assert alert.severity == AlertSeverity.WARNING
        assert alert.category == AlertCategory.ERROR_RATE
        assert len(alert_manager.active_alerts) == 1

    @pytest.mark.asyncio
    async def test_alert_acknowledgment(self, alert_manager):
        """Test alert acknowledgment"""
        # Trigger an alert
        alert = await alert_manager.trigger_alert(
            "error_rate_critical",
            "Critical error rate",
            0.15,
            {}
        )

        # Acknowledge the alert
        success = await alert_manager.acknowledge_alert(alert.id, "test_user")

        assert success == True
        assert alert.acknowledged == True
        assert alert.acknowledged_by == "test_user"

    @pytest.mark.asyncio
    async def test_alert_resolution(self, alert_manager):
        """Test alert resolution"""
        # Trigger an alert
        alert = await alert_manager.trigger_alert(
            "latency_high",
            "High latency detected",
            7.0,
            {}
        )

        # Resolve the alert
        success = await alert_manager.resolve_alert(alert.id, "test_user")

        assert success == True
        assert alert.resolved == True
        assert alert.resolved_by == "test_user"
        assert alert.id not in alert_manager.active_alerts

    def test_alert_statistics(self, alert_manager):
        """Test alert statistics generation"""
        stats = alert_manager.get_alert_statistics(days_back=1)

        assert "total_alerts" in stats
        assert "resolution_rate" in stats
        assert "severity_breakdown" in stats
        assert "category_breakdown" in stats

    def test_alert_filtering(self, alert_manager):
        """Test alert filtering functionality"""
        # Get alerts with severity filter
        critical_alerts = alert_manager.get_active_alerts(
            severity_filter=[AlertSeverity.CRITICAL]
        )

        # All returned alerts should be critical
        for alert in critical_alerts:
            assert alert.severity == AlertSeverity.CRITICAL


class TestMigrationDashboard:
    """Test the migration dashboard system"""

    @pytest.fixture
    def dashboard(self):
        """Create a dashboard instance for testing"""
        migration_monitor = GPT4MigrationMonitor()
        cost_tracker = CostTracker()
        performance_analyzer = PerformanceAnalyzer()
        alert_manager = AlertManager()

        return MigrationDashboard(
            migration_monitor,
            cost_tracker,
            performance_analyzer,
            alert_manager
        )

    def test_initialization(self, dashboard):
        """Test dashboard initialization"""
        assert dashboard.current_layout == "default"
        assert len(dashboard.layouts) > 0
        assert "executive" in dashboard.layouts
        assert "technical" in dashboard.layouts
        assert "cost" in dashboard.layouts

    @pytest.mark.asyncio
    async def test_dashboard_data_generation(self, dashboard):
        """Test dashboard data generation"""
        dashboard_data = await dashboard.get_dashboard_data("executive")

        assert "layout" in dashboard_data
        assert "widgets" in dashboard_data
        assert "metadata" in dashboard_data
        assert dashboard_data["layout"]["name"] == "executive"

    def test_available_layouts(self, dashboard):
        """Test getting available layouts"""
        layouts = dashboard.get_available_layouts()

        assert len(layouts) > 0
        for layout in layouts:
            assert "name" in layout
            assert "description" in layout
            assert "widget_count" in layout

    @pytest.mark.asyncio
    async def test_real_time_updates(self, dashboard):
        """Test real-time widget updates"""
        widget_ids = ["migration_progress", "cost_summary"]
        updates = await dashboard.get_real_time_update(widget_ids)

        assert "timestamp" in updates
        assert "updates" in updates

        for widget_id in widget_ids:
            assert widget_id in updates["updates"]


class TestGPT4MigrationSystem:
    """Test the complete migration system integration"""

    @pytest.fixture
    def migration_system(self):
        """Create a complete migration system for testing"""
        return GPT4MigrationSystem()

    @pytest.mark.asyncio
    async def test_system_initialization(self, migration_system):
        """Test complete system initialization"""
        result = await migration_system.initialize(MigrationPhase.PREPARATION)

        assert result["status"] == "success"
        assert migration_system.initialized == True
        assert migration_system.monitoring_active == True

    @pytest.mark.asyncio
    async def test_api_request_tracking(self, migration_system):
        """Test API request tracking through the system"""
        await migration_system.initialize()

        result = await migration_system.track_api_request(
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            latency=2.0,
            success=True,
            category=CostCategory.CONTENT_GENERATION
        )

        assert result["status"] == "tracked"
        assert result["cost"] > 0
        assert result["tokens"] == 150

    @pytest.mark.asyncio
    async def test_monitoring_cycle(self, migration_system):
        """Test complete monitoring cycle"""
        await migration_system.initialize()

        # Add some tracking data
        for i in range(5):
            await migration_system.track_api_request(
                model="gpt-4o",
                input_tokens=100,
                output_tokens=50,
                latency=2.0 + i * 0.5,
                success=i % 4 != 0  # 25% failure rate
            )

        result = await migration_system.run_monitoring_cycle()

        assert result["status"] in ["completed", "success"]

    @pytest.mark.asyncio
    async def test_migration_status(self, migration_system):
        """Test getting comprehensive migration status"""
        await migration_system.initialize()

        status = await migration_system.get_migration_status()

        assert "migration_report" in status
        assert "cost_analysis" in status
        assert "performance_summaries" in status
        assert "alert_statistics" in status
        assert "dashboard_data" in status

    def test_optimization_recommendations(self, migration_system):
        """Test getting optimization recommendations"""
        recommendations = migration_system.get_optimization_recommendations()

        assert "cost_optimization" in recommendations
        assert isinstance(recommendations["cost_optimization"], list)

    @pytest.mark.asyncio
    async def test_export_functionality(self, migration_system):
        """Test data export functionality"""
        await migration_system.initialize()

        export_data = await migration_system.export_monitoring_data()

        assert "cost_data" in export_data
        assert "performance_data" in export_data
        assert "dashboard_data" in export_data
        assert "export_timestamp" in export_data


@pytest.mark.integration
class TestAPIIntegration:
    """Test API endpoint integration with the monitoring system"""

    @pytest.mark.asyncio
    async def test_dashboard_endpoint(self):
        """Test dashboard API endpoint"""
        # This would require setting up the FastAPI test client
        # and testing the actual API endpoints
        pass

    @pytest.mark.asyncio
    async def test_cost_tracking_endpoint(self):
        """Test cost tracking API endpoint"""
        pass

    @pytest.mark.asyncio
    async def test_alert_management_endpoints(self):
        """Test alert management API endpoints"""
        pass


# Performance benchmarks
@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Benchmark tests for monitoring system performance"""

    def test_cost_tracking_performance(self, benchmark):
        """Benchmark cost tracking performance"""
        cost_tracker = CostTracker()

        def track_requests():
            for i in range(1000):
                cost_tracker.track_request_cost(
                    model="gpt-4o-mini",
                    input_tokens=100,
                    output_tokens=50,
                    category=CostCategory.CONTENT_GENERATION,
                    success=True
                )

        result = benchmark(track_requests)
        assert len(cost_tracker.cost_entries) == 1000

    def test_performance_data_recording(self, benchmark):
        """Benchmark performance data recording"""
        analyzer = PerformanceAnalyzer()

        def record_data():
            for i in range(1000):
                analyzer.record_performance_data(
                    PerformanceMetric.LATENCY,
                    2.0 + i * 0.001,
                    "gpt-4o"
                )

        result = benchmark(record_data)
        assert len(analyzer.data_points) == 1000


# Utility functions for testing
def create_test_metrics() -> MigrationMetrics:
    """Create test migration metrics"""
    return MigrationMetrics(
        total_requests=1000,
        successful_requests=950,
        failed_requests=50,
        total_tokens=500000,
        total_cost=15.0,
        avg_latency=2.5,
        error_rate=5.0,
        cost_per_request=0.015,
        tokens_per_request=500,
        daily_cost=15.0,
        weekly_cost=105.0,
        monthly_projected_cost=450.0
    )


def create_test_cost_entries(count: int = 10) -> list:
    """Create test cost entries"""
    entries = []
    for i in range(count):
        entry = CostEntry(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
            model="gpt-4o",
            tokens_used=100 + i * 10,
            cost=0.01 + i * 0.001,
            category=CostCategory.CONTENT_GENERATION,
            request_id=f"req_{i}",
            success=i % 10 != 0  # 10% failure rate
        )
        entries.append(entry)
    return entries


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])