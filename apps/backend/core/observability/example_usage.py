"""
Example Usage of Observability Integration

This module demonstrates how to integrate and use the observability system
with a FastAPI application.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

# Import observability components
from .correlation import (
    CorrelationMiddleware,
    correlation_manager,
    correlate_async_task,
    get_correlation_context,
    get_correlation_id
)
from .anomaly_detection import (
    anomaly_engine,
    alert_manager,
    AnomalyAlert,
    track_latency,
    track_errors
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create FastAPI app with observability
app = FastAPI(title="Observability Example", version="1.0.0")

# Add correlation middleware
app.add_middleware(CorrelationMiddleware)


# Example: Custom alert handler
async def slack_alert_handler(alert: AnomalyAlert):
    """Example alert handler that would send to Slack"""
    logger.warning(
        f"🚨 ALERT: {alert.title} | "
        f"Severity: {alert.severity.value} | "
        f"Metric: {alert.metric_name} | "
        f"Current: {alert.current_value:.2f} | "
        f"Expected: {alert.expected_value:.2f}"
    )
    # In real implementation, send to Slack webhook


async def email_alert_handler(alert: AnomalyAlert):
    """Example alert handler that would send email"""
    logger.info(f"📧 Email alert sent for: {alert.title}")
    # In real implementation, send email


# Register alert handlers
alert_manager.register_alert_handler(slack_alert_handler)
alert_manager.register_alert_handler(email_alert_handler)


# Example: Basic endpoint with tracking
@app.get("/")
@track_latency("homepage")
@track_errors("homepage")
async def homepage():
    """Homepage endpoint with automatic latency and error tracking"""
    context = get_correlation_context()

    return {
        "message": "Welcome to the Observability Example API",
        "correlation_id": context.correlation_id if context else None,
        "trace_id": context.trace_id if context else None,
        "timestamp": datetime.utcnow().isoformat()
    }


# Example: Endpoint that triggers background tasks
@app.post("/process-data")
@track_latency("process_data")
@track_errors("process_data")
async def process_data(data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Process data endpoint that triggers correlated background tasks"""
    context = get_correlation_context()

    # Record custom metrics
    anomaly_engine.record_metric("data_items_received", len(data.get("items", [])))

    # Start background processing with correlation
    background_tasks.add_task(background_data_processing, data)

    return {
        "status": "processing_started",
        "correlation_id": context.correlation_id if context else None,
        "items_count": len(data.get("items", []))
    }


@correlate_async_task("background_data_processing")
async def background_data_processing(data: Dict[str, Any]):
    """Background task with correlation tracking"""
    context = get_correlation_context()

    logger.info(
        f"Starting background processing",
        extra={
            "correlation_id": context.correlation_id if context else None,
            "items_count": len(data.get("items", []))
        }
    )

    # Simulate processing time
    processing_time = len(data.get("items", [])) * 0.1
    await asyncio.sleep(processing_time)

    # Record processing metrics
    anomaly_engine.record_metric("data_processing_duration_seconds", processing_time)
    anomaly_engine.record_metric("data_items_processed", len(data.get("items", [])))

    # Simulate child tasks
    for item in data.get("items", []):
        await process_individual_item(item)

    logger.info(
        f"Background processing completed",
        extra={"correlation_id": context.correlation_id if context else None}
    )


@correlate_async_task("item_processing")
async def process_individual_item(item: Dict[str, Any]):
    """Process individual item with correlation"""
    context = get_correlation_context()

    # Simulate item processing
    await asyncio.sleep(0.01)

    # Record item metrics
    anomaly_engine.record_metric("item_processing_latency_ms", 10)

    return f"Processed item: {item.get('id', 'unknown')}"


# Example: Endpoint that can trigger anomalies
@app.get("/load-test/{request_count}")
@track_latency("load_test")
@track_errors("load_test")
async def load_test(request_count: int):
    """Generate load to test anomaly detection"""
    if request_count > 1000:
        raise HTTPException(status_code=400, detail="Too many requests")

    # Simulate varying latencies
    base_latency = 50  # 50ms base
    for i in range(request_count):
        # Add some variance and occasional spikes
        if i % 10 == 0:
            latency = base_latency * 5  # Spike every 10th request
        else:
            latency = base_latency + (i % 3) * 10

        anomaly_engine.record_metric("simulated_request_latency_ms", latency)

        # Simulate errors occasionally
        if i % 20 == 0:
            anomaly_engine.record_metric("simulated_request_errors", 1)
        else:
            anomaly_engine.record_metric("simulated_request_success", 1)

    return {
        "status": "load_test_completed",
        "requests_generated": request_count,
        "correlation_id": get_correlation_id()
    }


# Example: Database operation with tracking
@app.get("/users/{user_id}")
@track_latency("get_user")
@track_errors("get_user")
async def get_user(user_id: int):
    """Simulate database operation with tracking"""
    # Simulate database query time
    query_time = 0.05 + (user_id % 10) * 0.01  # Vary by user_id
    await asyncio.sleep(query_time)

    # Record database metrics
    anomaly_engine.record_metric("database_query_latency_ms", query_time * 1000)

    # Simulate occasional database errors
    if user_id == 999:
        anomaly_engine.record_metric("database_errors", 1)
        raise HTTPException(status_code=404, detail="User not found")

    anomaly_engine.record_metric("database_success", 1)

    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "correlation_id": get_correlation_id()
    }


# Example: Chain of correlated operations
@app.post("/complex-workflow")
@track_latency("complex_workflow")
@track_errors("complex_workflow")
async def complex_workflow(workflow_data: Dict[str, Any]):
    """Example of a complex workflow with multiple correlated steps"""
    context = get_correlation_context()

    logger.info(
        "Starting complex workflow",
        extra={"correlation_id": context.correlation_id if context else None}
    )

    # Step 1: Validate data
    await validate_workflow_data(workflow_data)

    # Step 2: Process in parallel
    tasks = []
    for step in workflow_data.get("steps", []):
        task = asyncio.create_task(process_workflow_step(step))
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    # Step 3: Finalize
    final_result = await finalize_workflow(results)

    return {
        "status": "workflow_completed",
        "result": final_result,
        "correlation_id": context.correlation_id if context else None
    }


@correlate_async_task("validate_workflow_data")
async def validate_workflow_data(data: Dict[str, Any]):
    """Validate workflow data"""
    await asyncio.sleep(0.02)  # Simulate validation time

    anomaly_engine.record_metric("workflow_validation_time_ms", 20)

    if not data.get("steps"):
        raise ValueError("No steps provided")

    logger.info("Workflow data validated")


@correlate_async_task("process_workflow_step")
async def process_workflow_step(step: Dict[str, Any]) -> Dict[str, Any]:
    """Process individual workflow step"""
    step_type = step.get("type", "unknown")
    processing_time = step.get("duration", 0.1)

    await asyncio.sleep(processing_time)

    # Record step metrics
    anomaly_engine.record_metric(f"workflow_step_{step_type}_duration_ms", processing_time * 1000)

    return {
        "step_id": step.get("id"),
        "result": f"Processed {step_type} step",
        "duration": processing_time
    }


@correlate_async_task("finalize_workflow")
async def finalize_workflow(step_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Finalize workflow"""
    await asyncio.sleep(0.05)  # Simulate finalization

    total_duration = sum(result.get("duration", 0) for result in step_results)

    anomaly_engine.record_metric("workflow_total_duration_seconds", total_duration)
    anomaly_engine.record_metric("workflow_steps_completed", len(step_results))

    logger.info(f"Workflow finalized with {len(step_results)} steps")

    return {
        "steps_completed": len(step_results),
        "total_duration": total_duration,
        "status": "success"
    }


# Observability endpoints
@app.get("/observability/metrics")
async def get_metrics():
    """Get current metrics summary"""
    summary = anomaly_engine.get_all_metrics_summary()
    correlation_metrics = correlation_manager.get_metrics()

    return {
        "metrics": summary,
        "correlation": correlation_metrics,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/observability/alerts")
async def get_alerts(limit: int = 20):
    """Get recent alerts"""
    alerts = alert_manager.get_recent_alerts(limit)

    return {
        "alerts": [alert.to_dict() for alert in alerts],
        "count": len(alerts),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/observability/correlation/{correlation_id}")
async def get_correlation_chain(correlation_id: str):
    """Get correlation chain for a specific correlation ID"""
    chain = correlation_manager.get_correlation_chain(correlation_id)

    return {
        "correlation_id": correlation_id,
        "chain": [
            {
                "correlation_id": ctx.correlation_id,
                "trace_id": ctx.trace_id,
                "request_type": ctx.request_type,
                "created_at": ctx.created_at.isoformat(),
                "metadata": ctx.metadata
            }
            for ctx in chain
        ],
        "chain_length": len(chain)
    }


@app.post("/observability/test-anomaly")
async def create_test_anomaly():
    """Create test data to trigger anomaly detection"""
    # Record normal values
    for i in range(10):
        anomaly_engine.record_metric("test_metric", 100 + i * 2)

    # Record anomalous value
    anomaly_engine.record_metric("test_metric", 500)  # 5x normal

    return {
        "status": "test_anomaly_created",
        "message": "Recorded normal values (100-118) then anomalous value (500)",
        "correlation_id": get_correlation_id()
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "observability": {
            "correlation_tracking": "active",
            "anomaly_detection": "active",
            "alerting": "active"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Observability Example API")
    print("📊 Endpoints available:")
    print("  GET  /                          - Homepage")
    print("  POST /process-data              - Process data with background tasks")
    print("  GET  /load-test/{count}         - Generate load for testing")
    print("  GET  /users/{user_id}           - Get user (simulated DB operation)")
    print("  POST /complex-workflow          - Complex multi-step workflow")
    print("  GET  /observability/metrics     - Current metrics")
    print("  GET  /observability/alerts      - Recent alerts")
    print("  POST /observability/test-anomaly - Create test anomaly")
    print("  GET  /health                    - Health check")
    print("")
    print("🔍 Try these examples:")
    print("  curl http://localhost:8010/")
    print("  curl -X POST http://localhost:8010/process-data -H 'Content-Type: application/json' -d '{\"items\": [1,2,3]}'")
    print("  curl http://localhost:8010/load-test/50")
    print("  curl http://localhost:8010/observability/metrics")

    uvicorn.run(
        "example_usage:app",
        host="127.0.0.1",
        port=8010,  # Different port to avoid conflicts
        reload=True,
        log_level="info"
    )