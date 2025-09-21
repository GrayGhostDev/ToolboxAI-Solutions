"""
GPT-4.1 Migration Integration Example

This module demonstrates how to integrate and use the comprehensive
GPT-4.1 migration monitoring system in your application.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .gpt4_migration_monitor import GPT4MigrationMonitor, MigrationPhase
from .cost_tracker import CostTracker, CostCategory
from .performance_analyzer import PerformanceAnalyzer, PerformanceMetric
from .alert_manager import AlertManager, AlertSeverity, AlertCategory
from .migration_dashboard import MigrationDashboard

from core.agents.base_agent import AgentConfig

logger = logging.getLogger(__name__)


class GPT4MigrationSystem:
    """
    Complete GPT-4.1 migration monitoring system integration.

    This class provides a unified interface to all monitoring components
    and demonstrates how to integrate them into your application.
    """

    def __init__(self):
        # Initialize all monitoring components
        self.migration_monitor = GPT4MigrationMonitor()
        self.cost_tracker = CostTracker()
        self.performance_analyzer = PerformanceAnalyzer()
        self.alert_manager = AlertManager()
        self.dashboard = MigrationDashboard(
            self.migration_monitor,
            self.cost_tracker,
            self.performance_analyzer,
            self.alert_manager
        )

        # System state
        self.initialized = False
        self.monitoring_active = False

        logger.info("GPT4MigrationSystem initialized")

    async def initialize(self, migration_phase: MigrationPhase = MigrationPhase.PREPARATION) -> Dict[str, Any]:
        """Initialize the migration monitoring system"""

        try:
            # Start migration monitoring
            result = await self.migration_monitor.start_monitoring(migration_phase)

            # Establish performance baselines for key models
            models = ["gpt-4", "gpt-4o", "gpt-4o-mini"]
            for model in models:
                baseline = self.performance_analyzer.establish_baseline(model)
                logger.info(f"Established baseline for {model}: {baseline}")

            # Configure cost tracking budgets
            self.cost_tracker.set_budget_limit("daily", 100.0)    # $100/day
            self.cost_tracker.set_budget_limit("weekly", 600.0)   # $600/week
            self.cost_tracker.set_budget_limit("monthly", 2500.0) # $2500/month

            # Test alert system
            await self._test_alert_system()

            self.initialized = True
            self.monitoring_active = True

            logger.info("GPT4MigrationSystem initialized successfully")

            return {
                "status": "success",
                "migration_phase": migration_phase.value,
                "baselines_established": len(models),
                "budgets_configured": True,
                "alerts_tested": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to initialize migration system: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def _test_alert_system(self) -> None:
        """Test the alert system with a low-priority alert"""

        await self.alert_manager.trigger_alert(
            rule_id="system_test",
            message="Migration monitoring system initialized successfully",
            value=1.0,
            metadata={"test": True}
        )

    async def track_api_request(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency: float,
        success: bool,
        category: CostCategory = CostCategory.OTHER,
        endpoint: str = ""
    ) -> Dict[str, Any]:
        """
        Track a single API request across all monitoring systems.

        This is the main method you'll call after each OpenAI API request.
        """

        if not self.monitoring_active:
            logger.warning("Monitoring not active, skipping request tracking")
            return {"status": "skipped", "reason": "monitoring_inactive"}

        try:
            # Track cost
            cost = self.cost_tracker.track_request_cost(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                category=category,
                success=success,
                metadata={"endpoint": endpoint}
            )

            # Track performance metrics
            self.performance_analyzer.record_performance_data(
                PerformanceMetric.LATENCY,
                latency,
                model,
                endpoint
            )

            success_rate = 1.0 if success else 0.0
            self.performance_analyzer.record_performance_data(
                PerformanceMetric.SUCCESS_RATE,
                success_rate,
                model,
                endpoint
            )

            error_rate = 0.0 if success else 1.0
            self.performance_analyzer.record_performance_data(
                PerformanceMetric.ERROR_RATE,
                error_rate,
                model,
                endpoint
            )

            # Calculate token efficiency (tokens per second)
            if latency > 0:
                token_efficiency = (input_tokens + output_tokens) / latency
                self.performance_analyzer.record_performance_data(
                    PerformanceMetric.TOKEN_EFFICIENCY,
                    token_efficiency,
                    model,
                    endpoint
                )

            # Calculate cost efficiency (tokens per dollar)
            if cost > 0:
                cost_efficiency = (input_tokens + output_tokens) / cost
                self.performance_analyzer.record_performance_data(
                    PerformanceMetric.COST_EFFICIENCY,
                    cost_efficiency,
                    model,
                    endpoint
                )

            # Check for immediate issues and trigger alerts if needed
            await self._check_immediate_alerts(model, latency, success, cost)

            return {
                "status": "tracked",
                "cost": cost,
                "model": model,
                "tokens": input_tokens + output_tokens,
                "latency": latency,
                "success": success,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to track API request: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def _check_immediate_alerts(self, model: str, latency: float, success: bool, cost: float) -> None:
        """Check for immediate alert conditions after API request"""

        # Check for high latency
        if latency > 10.0:  # 10 seconds
            await self.alert_manager.trigger_alert(
                "latency_critical",
                f"Critical latency detected for {model}",
                latency,
                {"model": model, "cost": cost}
            )
        elif latency > 5.0:  # 5 seconds
            await self.alert_manager.trigger_alert(
                "latency_high",
                f"High latency detected for {model}",
                latency,
                {"model": model, "cost": cost}
            )

        # Check for API errors
        if not success:
            await self.alert_manager.trigger_alert(
                "api_error",
                f"API request failed for {model}",
                1.0,
                {"model": model, "latency": latency, "cost": cost}
            )

    async def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run a complete monitoring cycle - call this periodically (e.g., every 5 minutes)"""

        if not self.monitoring_active:
            return {"status": "inactive"}

        try:
            # Run comprehensive monitoring
            monitoring_result = await self.migration_monitor._comprehensive_monitoring_cycle()

            # Check for performance anomalies
            models = ["gpt-4", "gpt-4o", "gpt-4o-mini"]
            anomalies_detected = 0

            for model in models:
                anomalies = self.performance_analyzer.detect_anomalies(model)
                for anomaly in anomalies:
                    await self.alert_manager.trigger_alert(
                        f"performance_anomaly_{anomaly.metric_type.value}",
                        f"Performance anomaly detected: {anomaly.description}",
                        anomaly.current_value,
                        {
                            "model": model,
                            "expected_value": anomaly.expected_value,
                            "deviation": anomaly.deviation_percentage
                        }
                    )
                    anomalies_detected += 1

            # Check budget alerts
            budget_alerts = self.cost_tracker._check_budget_alerts()
            for alert in budget_alerts:
                await self.alert_manager.trigger_alert(
                    "budget_alert",
                    alert["message"],
                    alert["percentage"],
                    alert
                )

            return {
                "status": "completed",
                "monitoring_result": monitoring_result,
                "anomalies_detected": anomalies_detected,
                "budget_alerts": len(budget_alerts),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def get_migration_status(self) -> Dict[str, Any]:
        """Get comprehensive migration status"""

        try:
            # Get migration report
            migration_report = await self.migration_monitor._generate_migration_report()

            # Get cost analysis
            cost_analysis = self.cost_tracker.get_cost_analysis()

            # Get performance summaries
            performance_summaries = {}
            for model in ["gpt-4", "gpt-4o", "gpt-4o-mini"]:
                try:
                    summary = self.performance_analyzer.generate_performance_summary(model)
                    performance_summaries[model] = {
                        "overall_score": summary.overall_score,
                        "metrics": summary.metrics,
                        "anomaly_count": len(summary.anomalies),
                        "recommendations": summary.recommendations[:3]  # Top 3
                    }
                except Exception as e:
                    logger.warning(f"Failed to get performance summary for {model}: {e}")

            # Get alert statistics
            alert_stats = self.alert_manager.get_alert_statistics()

            # Get dashboard data
            dashboard_data = await self.dashboard.get_dashboard_data("executive")

            return {
                "migration_report": migration_report,
                "cost_analysis": {
                    "total_cost": cost_analysis.total_cost,
                    "avg_cost_per_request": cost_analysis.avg_cost_per_request,
                    "efficiency_score": cost_analysis.efficiency_score,
                    "breakdown_by_model": cost_analysis.breakdown_by_model
                },
                "performance_summaries": performance_summaries,
                "alert_statistics": alert_stats,
                "dashboard_data": dashboard_data,
                "system_status": {
                    "initialized": self.initialized,
                    "monitoring_active": self.monitoring_active,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def advance_migration_phase(self, new_phase: MigrationPhase) -> Dict[str, Any]:
        """Advance to the next migration phase"""

        try:
            result = await self.migration_monitor.advance_phase(new_phase)
            logger.info(f"Advanced to migration phase: {new_phase.value}")
            return result

        except Exception as e:
            logger.error(f"Failed to advance migration phase: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Acknowledge an alert"""
        return await self.alert_manager.acknowledge_alert(alert_id, user)

    async def resolve_alert(self, alert_id: str, user: str) -> bool:
        """Resolve an alert"""
        return await self.alert_manager.resolve_alert(alert_id, user)

    def get_optimization_recommendations(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get optimization recommendations from all systems"""

        return {
            "cost_optimization": self.cost_tracker.get_optimization_recommendations(),
            "migration_recommendations": [],  # Would come from migration monitor
            "performance_recommendations": []  # Would come from performance analyzer
        }

    async def export_monitoring_data(self) -> Dict[str, str]:
        """Export all monitoring data for analysis"""

        try:
            cost_data = self.cost_tracker.export_cost_data()
            performance_data = self.performance_analyzer.export_performance_data()
            dashboard_data = await self.dashboard.export_dashboard_data()

            return {
                "cost_data": cost_data,
                "performance_data": performance_data,
                "dashboard_data": dashboard_data,
                "export_timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to export monitoring data: {e}")
            return {
                "error": str(e),
                "export_timestamp": datetime.now(timezone.utc).isoformat()
            }

    def stop_monitoring(self) -> None:
        """Stop the monitoring system"""
        self.monitoring_active = False
        logger.info("Migration monitoring stopped")

    def restart_monitoring(self) -> None:
        """Restart the monitoring system"""
        if self.initialized:
            self.monitoring_active = True
            logger.info("Migration monitoring restarted")
        else:
            logger.warning("Cannot restart monitoring - system not initialized")


# Example usage and integration patterns

async def example_usage():
    """Example of how to use the GPT-4.1 migration monitoring system"""

    # Initialize the system
    migration_system = GPT4MigrationSystem()

    # Initialize in preparation phase
    init_result = await migration_system.initialize(MigrationPhase.PREPARATION)
    print(f"Initialization result: {init_result}")

    # Simulate tracking some API requests
    models = ["gpt-4", "gpt-4o", "gpt-4o-mini"]

    for i in range(10):
        model = models[i % len(models)]

        # Simulate API request tracking
        track_result = await migration_system.track_api_request(
            model=model,
            input_tokens=500 + (i * 10),
            output_tokens=200 + (i * 5),
            latency=2.0 + (i * 0.1),
            success=True,
            category=CostCategory.CONTENT_GENERATION,
            endpoint="/v1/chat/completions"
        )

        print(f"Tracked request {i+1}: {track_result}")

    # Run a monitoring cycle
    cycle_result = await migration_system.run_monitoring_cycle()
    print(f"Monitoring cycle result: {cycle_result}")

    # Get migration status
    status = await migration_system.get_migration_status()
    print(f"Migration status keys: {list(status.keys())}")

    # Get dashboard data
    dashboard_data = await migration_system.dashboard.get_dashboard_data("executive")
    print(f"Dashboard widgets: {list(dashboard_data['widgets'].keys())}")

    # Advance to testing phase
    advance_result = await migration_system.advance_migration_phase(MigrationPhase.TESTING)
    print(f"Phase advancement result: {advance_result['phase_transition']}")

    # Get optimization recommendations
    recommendations = migration_system.get_optimization_recommendations()
    print(f"Optimization recommendations: {len(recommendations['cost_optimization'])} cost optimizations")


# Integration with existing OpenAI service
class OpenAIServiceWithMonitoring:
    """
    Example of how to integrate migration monitoring with your existing OpenAI service.
    """

    def __init__(self, migration_system: GPT4MigrationSystem):
        self.migration_system = migration_system
        # Your existing OpenAI client initialization here

    async def chat_completion(
        self,
        model: str,
        messages: list,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Chat completion with integrated monitoring.
        """

        import time
        start_time = time.time()

        try:
            # Make your actual OpenAI API call here
            # response = await self.openai_client.chat.completions.create(...)

            # Simulate response for example
            response = {
                "choices": [{"message": {"content": "Example response"}}],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150
                }
            }

            # Calculate latency
            latency = time.time() - start_time

            # Track the request
            await self.migration_system.track_api_request(
                model=model,
                input_tokens=response["usage"]["prompt_tokens"],
                output_tokens=response["usage"]["completion_tokens"],
                latency=latency,
                success=True,
                category=CostCategory.EDUCATIONAL_SUPPORT,
                endpoint="/v1/chat/completions"
            )

            return response

        except Exception as e:
            # Track failed request
            latency = time.time() - start_time
            await self.migration_system.track_api_request(
                model=model,
                input_tokens=0,
                output_tokens=0,
                latency=latency,
                success=False,
                category=CostCategory.EDUCATIONAL_SUPPORT,
                endpoint="/v1/chat/completions"
            )

            raise e


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())