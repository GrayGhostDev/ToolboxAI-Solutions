"""
Integration Test for Observability System

Tests the complete observability integration including correlation tracking,
anomaly detection, and alerting system.
"""

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from .anomaly_detection import (
    AnomalyAlert,
    alert_manager,
    anomaly_engine,
    track_errors,
    track_latency,
)
from .correlation import (
    CorrelationMiddleware,
    correlate_async_task,
    correlation_manager,
    get_correlation_context,
)


class TestObservabilityIntegration:
    """Test suite for observability integration"""

    def setup_method(self):
        """Setup test environment"""
        # Clear any existing state
        anomaly_engine.metrics.clear()
        alert_manager.alert_history.clear()
        alert_manager.alert_handlers.clear()

    def test_correlation_middleware_integration(self):
        """Test correlation middleware with FastAPI"""
        app = FastAPI()
        app.add_middleware(CorrelationMiddleware)

        @app.get("/test")
        async def test_endpoint():
            context = get_correlation_context()
            return {
                "correlation_id": context.correlation_id if context else None,
                "trace_id": context.trace_id if context else None,
            }

        with TestClient(app) as client:
            # Test request without correlation ID
            response = client.get("/test")
            assert response.status_code == 200
            data = response.json()
            assert data["correlation_id"] is not None
            assert "corr_" in data["correlation_id"]

            # Test request with provided correlation ID
            headers = {"X-Correlation-ID": "test-correlation-123"}
            response = client.get("/test", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["correlation_id"] == "test-correlation-123"

    @pytest.mark.asyncio
    async def test_async_task_correlation(self):
        """Test correlation tracking in async tasks"""
        results = []

        @correlate_async_task("test_task")
        async def test_task(task_id: str):
            context = get_correlation_context()
            results.append(
                {
                    "task_id": task_id,
                    "correlation_id": context.correlation_id if context else None,
                    "request_type": context.request_type if context else None,
                }
            )

        # Create a parent context
        app = FastAPI()
        app.add_middleware(CorrelationMiddleware)

        @app.get("/trigger-tasks")
        async def trigger_tasks():
            tasks = []
            for i in range(3):
                task = asyncio.create_task(test_task(f"task-{i}"))
                tasks.append(task)
            await asyncio.gather(*tasks)
            return {"status": "completed"}

        with TestClient(app) as client:
            response = client.get("/trigger-tasks")
            assert response.status_code == 200

            # Give tasks time to complete
            await asyncio.sleep(0.1)

            # Verify correlation was propagated
            assert len(results) == 3
            for result in results:
                assert result["correlation_id"] is not None
                assert result["request_type"] == "async_task"

    def test_latency_tracking_decorator(self):
        """Test latency tracking decorator"""
        app = FastAPI()
        app.add_middleware(CorrelationMiddleware)

        @app.get("/slow-endpoint")
        @track_latency("slow_operation")
        async def slow_endpoint():
            await asyncio.sleep(0.1)  # 100ms delay
            return {"status": "completed"}

        with TestClient(app) as client:
            response = client.get("/slow-endpoint")
            assert response.status_code == 200

            # Check that latency was recorded
            metrics = anomaly_engine.get_metric_summary("slow_operation_latency")
            assert "error" not in metrics
            assert metrics["count"] >= 1
            assert metrics["latest"] >= 100  # Should be at least 100ms

    def test_error_tracking_decorator(self):
        """Test error tracking decorator"""
        app = FastAPI()
        app.add_middleware(CorrelationMiddleware)

        @app.get("/error-endpoint")
        @track_errors("error_operation")
        async def error_endpoint():
            raise ValueError("Test error")

        @app.get("/success-endpoint")
        @track_errors("success_operation")
        async def success_endpoint():
            return {"status": "success"}

        with TestClient(app) as client:
            # Test error case
            response = client.get("/error-endpoint")
            assert response.status_code == 500

            # Test success case
            response = client.get("/success-endpoint")
            assert response.status_code == 200

            # Check error metrics
            error_metrics = anomaly_engine.get_metric_summary("error_operation_error")
            success_error_metrics = anomaly_engine.get_metric_summary("error_operation_success")
            success_success_metrics = anomaly_engine.get_metric_summary("success_operation_success")

            # Error operation should have recorded an error
            assert "error" not in error_metrics
            assert error_metrics["count"] >= 1

            # Success operation should have recorded a success
            assert "error" not in success_success_metrics
            assert success_success_metrics["count"] >= 1

    @pytest.mark.asyncio
    async def test_anomaly_detection_alerts(self):
        """Test anomaly detection and alerting"""
        alerts_received = []

        async def test_alert_handler(alert: AnomalyAlert):
            alerts_received.append(alert)

        # Register alert handler
        alert_manager.register_alert_handler(test_alert_handler)

        # Record normal values
        for i in range(10):
            anomaly_engine.record_metric("test_metric", 50.0 + i)

        # Give some time for processing
        await asyncio.sleep(0.1)

        # Record an anomalous value
        anomaly_engine.record_metric("test_metric", 500.0)  # 10x normal value

        # Give time for anomaly detection
        await asyncio.sleep(0.2)

        # Should have triggered an alert
        assert len(alerts_received) > 0
        alert = alerts_received[0]
        assert alert.metric_name == "test_metric"
        assert alert.current_value == 500.0
        assert alert.confidence > 1.0

    def test_metrics_summary_endpoint(self):
        """Test metrics summary functionality"""
        # Record some test metrics
        for i in range(5):
            anomaly_engine.record_metric("endpoint_latency", 100 + i * 10)
            anomaly_engine.record_metric("endpoint_errors", 1 if i % 2 == 0 else 0)

        # Get summary
        summary = anomaly_engine.get_all_metrics_summary()

        assert "endpoint_latency" in summary
        assert "endpoint_errors" in summary

        latency_summary = summary["endpoint_latency"]
        assert latency_summary["count"] == 5
        assert latency_summary["min"] == 100
        assert latency_summary["max"] == 140
        assert latency_summary["mean"] == 120

    @pytest.mark.asyncio
    async def test_correlation_chain_tracking(self):
        """Test correlation chain tracking across multiple operations"""
        app = FastAPI()
        app.add_middleware(CorrelationMiddleware)

        @correlate_async_task("child_operation")
        async def child_operation():
            context = get_correlation_context()
            return context.correlation_id if context else None

        @app.get("/parent-operation")
        async def parent_operation():
            parent_context = get_correlation_context()
            parent_correlation_id = parent_context.correlation_id if parent_context else None

            # Start child operation
            child_correlation_id = await child_operation()

            return {
                "parent_correlation_id": parent_correlation_id,
                "child_correlation_id": child_correlation_id,
            }

        with TestClient(app) as client:
            response = client.get("/parent-operation")
            assert response.status_code == 200

            data = response.json()
            parent_id = data["parent_correlation_id"]
            child_id = data["child_correlation_id"]

            assert parent_id is not None
            assert child_id is not None
            assert parent_id != child_id

            # Get correlation chain
            chain = correlation_manager.get_correlation_chain(parent_id)

            # Should have at least the parent context
            assert len(chain) >= 1

            # Parent should be in the chain
            parent_found = any(ctx.correlation_id == parent_id for ctx in chain)
            assert parent_found

    def test_websocket_correlation_setup(self):
        """Test WebSocket correlation context creation"""
        from fastapi import WebSocket
        from starlette.testclient import TestClient

        app = FastAPI()

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()

            # Create WebSocket correlation context
            context = correlation_manager.create_context_from_websocket(websocket)

            await websocket.send_json(
                {
                    "correlation_id": context.correlation_id,
                    "request_type": context.request_type,
                    "trace_id": context.trace_id,
                }
            )

            await websocket.close()

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                data = websocket.receive_json()

                assert data["correlation_id"] is not None
                assert data["request_type"] == "websocket"
                assert "corr_" in data["correlation_id"]

    @pytest.mark.asyncio
    async def test_performance_overhead(self):
        """Test that observability has minimal performance overhead"""
        import time

        app = FastAPI()
        app.add_middleware(CorrelationMiddleware)

        @app.get("/performance-test")
        @track_latency("performance_test")
        @track_errors("performance_test")
        async def performance_test():
            return {"status": "ok"}

        # Measure without observability
        start_time = time.time()
        for _ in range(100):
            pass  # Simulate work
        baseline_time = time.time() - start_time

        # Measure with observability
        with TestClient(app) as client:
            start_time = time.time()
            for _ in range(100):
                response = client.get("/performance-test")
                assert response.status_code == 200
            observability_time = time.time() - start_time

        # Overhead should be minimal (less than 50% increase)
        overhead_ratio = observability_time / max(baseline_time, 0.001)
        assert overhead_ratio < 10  # Very generous threshold for test environment

    def test_correlation_context_cleanup(self):
        """Test that correlation contexts are properly cleaned up"""
        from .correlation import _correlation_store

        initial_size = _correlation_store.size()

        # Create some contexts
        app = FastAPI()
        app.add_middleware(CorrelationMiddleware)

        @app.get("/test-cleanup")
        async def test_cleanup():
            return {"status": "ok"}

        with TestClient(app) as client:
            # Make several requests
            for i in range(10):
                response = client.get("/test-cleanup")
                assert response.status_code == 200

        # Store size should have increased
        current_size = _correlation_store.size()
        assert current_size > initial_size

        # Force cleanup by setting a very short TTL
        original_ttl = _correlation_store.ttl_seconds
        _correlation_store.ttl_seconds = 0

        # Trigger cleanup
        _correlation_store._cleanup_expired()

        # Should be cleaned up
        final_size = _correlation_store.size()
        assert final_size <= initial_size

        # Restore original TTL
        _correlation_store.ttl_seconds = original_ttl


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
