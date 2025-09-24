"""
GPT-4.1 Migration Monitoring API Endpoints

FastAPI endpoints for the GPT-4.1 migration monitoring system.
Provides REST API access to all monitoring components.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.agents.monitoring.migration_integration import GPT4MigrationSystem
from core.agents.monitoring.gpt4_migration_monitor import MigrationPhase
from core.agents.monitoring.cost_tracker import CostCategory
from core.agents.monitoring.alert_manager import AlertSeverity, AlertCategory

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/gpt4-migration", tags=["GPT-4.1 Migration"])

# Global migration system instance
migration_system = GPT4MigrationSystem()


# Request/Response Models

class APIRequestTracking(BaseModel):
    """Model for tracking API requests"""
    model: str = Field(..., description="OpenAI model used")
    input_tokens: int = Field(..., ge=0, description="Number of input tokens")
    output_tokens: int = Field(..., ge=0, description="Number of output tokens")
    latency: float = Field(..., ge=0, description="Request latency in seconds")
    success: bool = Field(..., description="Whether the request was successful")
    category: str = Field(default="other", description="Request category")
    endpoint: str = Field(default="", description="API endpoint called")


class AlertAcknowledgment(BaseModel):
    """Model for alert acknowledgment"""
    alert_id: str = Field(..., description="Alert ID to acknowledge")
    user: str = Field(..., description="User acknowledging the alert")


class AlertResolution(BaseModel):
    """Model for alert resolution"""
    alert_id: str = Field(..., description="Alert ID to resolve")
    user: str = Field(..., description="User resolving the alert")


class BudgetUpdate(BaseModel):
    """Model for budget limit updates"""
    period: str = Field(..., description="Budget period (daily, weekly, monthly)")
    limit: float = Field(..., ge=0, description="Budget limit in dollars")
    alert_threshold: float = Field(default=0.8, ge=0, le=1, description="Alert threshold (0-1)")


class PhaseAdvancement(BaseModel):
    """Model for migration phase advancement"""
    new_phase: str = Field(..., description="New migration phase")


# Dependency for authentication (if needed)
async def get_current_user():
    """Get current authenticated user - placeholder for actual auth"""
    return {"user_id": "admin", "role": "admin"}  # Replace with actual auth


# Endpoints

@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_monitoring(
    phase: str = Query(default="preparation", description="Initial migration phase"),
    current_user = Depends(get_current_user)
):
    """Initialize the GPT-4.1 migration monitoring system"""

    try:
        # Convert string to enum
        migration_phase = MigrationPhase(phase.lower())

        result = await migration_system.initialize(migration_phase)

        if result["status"] == "success":
            logger.info(f"Migration monitoring initialized in {phase} phase by {current_user.get('user_id')}")
            return JSONResponse(content=result, status_code=200)
        else:
            logger.error(f"Failed to initialize migration monitoring: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "Initialization failed"))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid migration phase: {phase}")
    except Exception as e:
        logger.error(f"Unexpected error initializing monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track-request", response_model=Dict[str, Any])
async def track_api_request(
    request_data: APIRequestTracking,
    current_user = Depends(get_current_user)
):
    """Track a single OpenAI API request"""

    try:
        # Convert category string to enum
        try:
            category = CostCategory(request_data.category.lower())
        except ValueError:
            category = CostCategory.OTHER

        result = await migration_system.track_api_request(
            model=request_data.model,
            input_tokens=request_data.input_tokens,
            output_tokens=request_data.output_tokens,
            latency=request_data.latency,
            success=request_data.success,
            category=category,
            endpoint=request_data.endpoint
        )

        return result

    except Exception as e:
        logger.error(f"Failed to track API request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=Dict[str, Any])
async def get_migration_status():
    """Get comprehensive migration status"""

    try:
        status = await migration_system.get_migration_status()
        return status

    except Exception as e:
        logger.error(f"Failed to get migration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/{layout_name}", response_model=Dict[str, Any])
async def get_dashboard_data(
    layout_name: str = "default",
    force_refresh: bool = Query(default=False, description="Force refresh cached data")
):
    """Get dashboard data for specified layout"""

    try:
        dashboard_data = await migration_system.dashboard.get_dashboard_data(
            layout_name,
            force_refresh=force_refresh
        )
        return dashboard_data

    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/layouts", response_model=List[Dict[str, str]])
async def get_available_layouts():
    """Get list of available dashboard layouts"""

    try:
        layouts = migration_system.dashboard.get_available_layouts()
        return layouts

    except Exception as e:
        logger.error(f"Failed to get dashboard layouts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring-cycle", response_model=Dict[str, Any])
async def run_monitoring_cycle(
    current_user = Depends(get_current_user)
):
    """Run a complete monitoring cycle"""

    try:
        result = await migration_system.run_monitoring_cycle()
        return result

    except Exception as e:
        logger.error(f"Failed to run monitoring cycle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/advance-phase", response_model=Dict[str, Any])
async def advance_migration_phase(
    phase_data: PhaseAdvancement,
    current_user = Depends(get_current_user)
):
    """Advance to the next migration phase"""

    try:
        new_phase = MigrationPhase(phase_data.new_phase.lower())
        result = await migration_system.advance_migration_phase(new_phase)

        logger.info(f"Migration phase advanced to {new_phase.value} by {current_user.get('user_id')}")
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid migration phase: {phase_data.new_phase}")
    except Exception as e:
        logger.error(f"Failed to advance migration phase: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=Dict[str, Any])
async def get_active_alerts(
    severity: Optional[str] = Query(default=None, description="Filter by severity"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum number of alerts")
):
    """Get active alerts with optional filtering"""

    try:
        # Parse filters
        severity_filter = None
        if severity:
            try:
                severity_filter = [AlertSeverity(severity.lower())]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

        category_filter = None
        if category:
            try:
                category_filter = [AlertCategory(category.lower())]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

        # Get alerts
        alerts = migration_system.alert_manager.get_active_alerts(
            severity_filter=severity_filter,
            category_filter=category_filter
        )

        # Limit results
        alerts = alerts[:limit]

        # Convert to serializable format
        alert_data = [
            {
                "id": alert.id,
                "timestamp": alert.timestamp.isoformat(),
                "severity": alert.severity.value,
                "category": alert.category.value,
                "title": alert.title,
                "message": alert.message,
                "source": alert.source,
                "acknowledged": alert.acknowledged,
                "resolved": alert.resolved,
                "escalation_level": alert.escalation_level,
                "metadata": alert.metadata
            }
            for alert in alerts
        ]

        return {
            "alerts": alert_data,
            "total_count": len(alert_data),
            "filtered": bool(severity or category),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/acknowledge", response_model=Dict[str, Any])
async def acknowledge_alert(
    ack_data: AlertAcknowledgment,
    current_user = Depends(get_current_user)
):
    """Acknowledge an alert"""

    try:
        success = await migration_system.acknowledge_alert(ack_data.alert_id, ack_data.user)

        if success:
            logger.info(f"Alert {ack_data.alert_id} acknowledged by {ack_data.user}")
            return {
                "status": "success",
                "alert_id": ack_data.alert_id,
                "acknowledged_by": ack_data.user,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Alert not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/resolve", response_model=Dict[str, Any])
async def resolve_alert(
    resolve_data: AlertResolution,
    current_user = Depends(get_current_user)
):
    """Resolve an alert"""

    try:
        success = await migration_system.resolve_alert(resolve_data.alert_id, resolve_data.user)

        if success:
            logger.info(f"Alert {resolve_data.alert_id} resolved by {resolve_data.user}")
            return {
                "status": "success",
                "alert_id": resolve_data.alert_id,
                "resolved_by": resolve_data.user,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Alert not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/statistics", response_model=Dict[str, Any])
async def get_alert_statistics(
    days_back: int = Query(default=7, ge=1, le=90, description="Number of days to analyze")
):
    """Get alert statistics for the specified period"""

    try:
        stats = migration_system.alert_manager.get_alert_statistics(days_back)
        return stats

    except Exception as e:
        logger.error(f"Failed to get alert statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost/analysis", response_model=Dict[str, Any])
async def get_cost_analysis(
    days_back: int = Query(default=7, ge=1, le=90, description="Number of days to analyze")
):
    """Get cost analysis for the specified period"""

    try:
        from datetime import timedelta

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        analysis = migration_system.cost_tracker.get_cost_analysis(start_date, end_date)

        return {
            "period_start": analysis.period_start.isoformat(),
            "period_end": analysis.period_end.isoformat(),
            "total_cost": analysis.total_cost,
            "breakdown_by_model": analysis.breakdown_by_model,
            "breakdown_by_category": analysis.breakdown_by_category,
            "avg_cost_per_request": analysis.avg_cost_per_request,
            "tokens_per_dollar": analysis.tokens_per_dollar,
            "efficiency_score": analysis.efficiency_score,
            "cost_trends": analysis.cost_trends
        }

    except Exception as e:
        logger.error(f"Failed to get cost analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost/projection", response_model=Dict[str, Any])
async def get_cost_projection():
    """Get monthly cost projection"""

    try:
        projection = migration_system.cost_tracker.project_monthly_cost()
        return projection

    except Exception as e:
        logger.error(f"Failed to get cost projection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cost/budget", response_model=Dict[str, Any])
async def update_budget_limit(
    budget_data: BudgetUpdate,
    current_user = Depends(get_current_user)
):
    """Update budget limit for a specific period"""

    try:
        migration_system.cost_tracker.set_budget_limit(
            budget_data.period,
            budget_data.limit,
            budget_data.alert_threshold
        )

        logger.info(f"Budget limit updated for {budget_data.period}: ${budget_data.limit} by {current_user.get('user_id')}")

        return {
            "status": "success",
            "period": budget_data.period,
            "limit": budget_data.limit,
            "alert_threshold": budget_data.alert_threshold,
            "updated_by": current_user.get("user_id"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to update budget limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/real-time/{model}", response_model=Dict[str, Any])
async def get_real_time_performance(
    model: str
):
    """Get real-time performance metrics for a specific model"""

    try:
        metrics = migration_system.performance_analyzer.get_real_time_metrics(model)
        return metrics

    except Exception as e:
        logger.error(f"Failed to get real-time performance for {model}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/summary/{model}", response_model=Dict[str, Any])
async def get_performance_summary(
    model: str,
    days_back: int = Query(default=7, ge=1, le=90, description="Number of days to analyze")
):
    """Get performance summary for a specific model"""

    try:
        summary = migration_system.performance_analyzer.generate_performance_summary(model, days_back)

        return {
            "period_start": summary.period_start.isoformat(),
            "period_end": summary.period_end.isoformat(),
            "model": summary.model,
            "metrics": summary.metrics,
            "trends": summary.trends,
            "anomalies": [
                {
                    "timestamp": anomaly.timestamp.isoformat(),
                    "metric_type": anomaly.metric_type.value,
                    "severity": anomaly.severity,
                    "current_value": anomaly.current_value,
                    "expected_value": anomaly.expected_value,
                    "deviation_percentage": anomaly.deviation_percentage,
                    "description": anomaly.description,
                    "recommendations": anomaly.recommendations
                }
                for anomaly in summary.anomalies
            ],
            "overall_score": summary.overall_score,
            "recommendations": summary.recommendations
        }

    except Exception as e:
        logger.error(f"Failed to get performance summary for {model}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", response_model=Dict[str, Any])
async def get_optimization_recommendations():
    """Get optimization recommendations from all monitoring systems"""

    try:
        recommendations = migration_system.get_optimization_recommendations()
        return recommendations

    except Exception as e:
        logger.error(f"Failed to get optimization recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", response_model=Dict[str, Any])
async def export_monitoring_data(
    current_user = Depends(get_current_user)
):
    """Export all monitoring data for analysis"""

    try:
        export_data = await migration_system.export_monitoring_data()

        logger.info(f"Monitoring data exported by {current_user.get('user_id')}")
        return export_data

    except Exception as e:
        logger.error(f"Failed to export monitoring data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/control/stop", response_model=Dict[str, Any])
async def stop_monitoring(
    current_user = Depends(get_current_user)
):
    """Stop the monitoring system"""

    try:
        migration_system.stop_monitoring()

        logger.info(f"Monitoring stopped by {current_user.get('user_id')}")

        return {
            "status": "stopped",
            "stopped_by": current_user.get("user_id"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/control/restart", response_model=Dict[str, Any])
async def restart_monitoring(
    current_user = Depends(get_current_user)
):
    """Restart the monitoring system"""

    try:
        migration_system.restart_monitoring()

        logger.info(f"Monitoring restarted by {current_user.get('user_id')}")

        return {
            "status": "restarted",
            "restarted_by": current_user.get("user_id"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to restart monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, Any])
async def get_monitoring_health():
    """Get monitoring system health status"""

    try:
        return {
            "status": "healthy" if migration_system.monitoring_active else "inactive",
            "initialized": migration_system.initialized,
            "monitoring_active": migration_system.monitoring_active,
            "components": {
                "migration_monitor": True,
                "cost_tracker": True,
                "performance_analyzer": True,
                "alert_manager": True,
                "dashboard": True
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get monitoring health: {e}")
        raise HTTPException(status_code=500, detail=str(e))