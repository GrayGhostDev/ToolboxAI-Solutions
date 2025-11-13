"""
Unit tests for Error Handling API Router
Tests error reporting, swarm processing, workflow management, and recovery
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import status


@pytest.mark.unit
class TestErrorReporting:
    """Test suite for error reporting endpoints"""

    @pytest.fixture
    def sample_error_report(self):
        """Sample error report data"""
        return {
            "error_message": "Division by zero",
            "error_type": "RUNTIME",
            "stack_trace": "Traceback (most recent call last)...",
            "file_path": "/app/services/calculator.py",
            "line_number": 42,
            "priority": "HIGH",
            "affected_components": ["calculator_service"],
            "context": {"user_id": "user123", "request_id": "req456"},
        }

    @pytest.fixture
    def mock_swarm_coordinator(self):
        """Mock swarm coordinator"""
        coordinator = Mock()
        coordinator.orchestrate_error_handling = AsyncMock(
            return_value=Mock(
                errors_processed=5,
                agents_involved=["aggregation", "detection", "recovery"],
                model_dump=Mock(return_value={"status": "completed"}),
            )
        )
        coordinator.get_swarm_status = AsyncMock(
            return_value={"agents": ["aggregation", "detection"], "active": True}
        )
        coordinator.agents = {
            "pattern_analysis": Mock(
                analyze_error_patterns=AsyncMock(return_value={"patterns": []}),
                get_error_metrics=AsyncMock(return_value={"total_errors": 100}),
            ),
            "recovery": Mock(
                orchestrate_recovery=AsyncMock(
                    return_value=Mock(model_dump=Mock(return_value={"recovered": True}))
                )
            ),
            "aggregation": Mock(
                aggregate_errors=AsyncMock(),
                get_error_metrics=AsyncMock(return_value={"aggregated": 50}),
            ),
            "detection": Mock(get_error_metrics=AsyncMock(return_value={"detected": 75})),
        }
        return coordinator

    def test_report_error_success(self, test_client, sample_error_report, mock_swarm_coordinator):
        """Test successful single error reporting"""
        with patch(
            "apps.backend.api.routers.error_handling.swarm_coordinator", mock_swarm_coordinator
        ):
            with patch("apps.backend.api.routers.error_handling.process_single_error", AsyncMock()):
                response = test_client.post(
                    "/api/v1/error-handling/report-error", json=sample_error_report
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "error_id" in data
        assert data["error_id"].startswith("err_")
        assert data["message"] == "Error reported successfully"
        assert data["processing"] == "initiated"

    def test_report_error_invalid_type(self, test_client, sample_error_report):
        """Test error reporting with invalid error type"""
        sample_error_report["error_type"] = "INVALID_TYPE"

        response = test_client.post("/api/v1/error-handling/report-error", json=sample_error_report)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_report_error_invalid_priority(self, test_client, sample_error_report):
        """Test error reporting with invalid priority"""
        sample_error_report["priority"] = "INVALID_PRIORITY"

        response = test_client.post("/api/v1/error-handling/report-error", json=sample_error_report)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_report_error_minimal_data(self, test_client):
        """Test error reporting with minimal required data"""
        minimal_report = {"error_message": "Simple error", "error_type": "RUNTIME"}

        with patch("apps.backend.api.routers.error_handling.process_single_error", AsyncMock()):
            response = test_client.post("/api/v1/error-handling/report-error", json=minimal_report)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "error_id" in data


@pytest.mark.unit
class TestSwarmProcessing:
    """Test suite for swarm error processing"""

    @pytest.fixture
    def sample_swarm_request(self):
        """Sample swarm processing request"""
        return {
            "errors": [
                {
                    "error_message": "Database connection failed",
                    "error_type": "DATABASE",
                    "priority": "CRITICAL",
                    "affected_components": ["database_pool"],
                },
                {
                    "error_message": "API timeout",
                    "error_type": "TIMEOUT",
                    "priority": "HIGH",
                    "affected_components": ["api_gateway"],
                },
            ],
            "strategy": "parallel",
            "async_processing": True,
            "context": {"environment": "production"},
        }

    @pytest.fixture
    def mock_swarm_coordinator(self):
        """Mock swarm coordinator"""
        coordinator = Mock()
        coordinator.orchestrate_error_handling = AsyncMock(
            return_value=Mock(
                errors_processed=2,
                agents_involved=["aggregation", "detection", "recovery"],
                model_dump=Mock(
                    return_value={
                        "errors_processed": 2,
                        "fixes_applied": 2,
                        "recovery_success": True,
                    }
                ),
            )
        )
        return coordinator

    def test_process_errors_async(self, test_client, sample_swarm_request, mock_swarm_coordinator):
        """Test asynchronous error processing"""
        with patch(
            "apps.backend.api.routers.error_handling.swarm_coordinator", mock_swarm_coordinator
        ):
            with patch("apps.backend.api.routers.error_handling.run_swarm_workflow", AsyncMock()):
                response = test_client.post(
                    "/api/v1/error-handling/process-errors", json=sample_swarm_request
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "workflow_id" in data
        assert data["workflow_id"].startswith("workflow_")
        assert data["async"] is True
        assert "Processing 2 errors" in data["message"]

    def test_process_errors_sync(self, test_client, sample_swarm_request, mock_swarm_coordinator):
        """Test synchronous error processing"""
        sample_swarm_request["async_processing"] = False

        with patch(
            "apps.backend.api.routers.error_handling.swarm_coordinator", mock_swarm_coordinator
        ):
            response = test_client.post(
                "/api/v1/error-handling/process-errors", json=sample_swarm_request
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["async"] is False
        assert "result" in data
        assert data["result"]["errors_processed"] == 2

    def test_process_errors_empty_list(self, test_client):
        """Test processing empty error list"""
        empty_request = {"errors": [], "async_processing": True}

        with patch("apps.backend.api.routers.error_handling.run_swarm_workflow", AsyncMock()):
            response = test_client.post("/api/v1/error-handling/process-errors", json=empty_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Processing 0 errors" in data["message"]


@pytest.mark.unit
class TestWorkflowManagement:
    """Test suite for workflow status endpoints"""

    def test_get_workflow_status_success(self, test_client):
        """Test successful workflow status retrieval"""
        workflow_id = "workflow_20251010_120000"

        # Mock active workflow
        mock_workflow = {
            "status": "running",
            "errors_processed": 3,
            "agents_active": ["aggregation", "detection"],
            "progress": 75.5,
            "estimated_completion": "2025-10-10T12:05:00",
        }

        with patch.dict(
            "apps.backend.api.routers.error_handling.active_workflows", {workflow_id: mock_workflow}
        ):
            response = test_client.get(f"/api/v1/error-handling/workflow/{workflow_id}/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["workflow_id"] == workflow_id
        assert data["status"] == "running"
        assert data["errors_processed"] == 3
        assert data["agents_active"] == ["aggregation", "detection"]
        assert data["progress_percentage"] == 75.5

    def test_get_workflow_status_not_found(self, test_client):
        """Test workflow status for non-existent workflow"""
        workflow_id = "workflow_nonexistent"

        with patch.dict("apps.backend.api.routers.error_handling.active_workflows", {}):
            response = test_client.get(f"/api/v1/error-handling/workflow/{workflow_id}/status")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_get_workflow_status_completed(self, test_client):
        """Test status of completed workflow"""
        workflow_id = "workflow_completed"

        mock_workflow = {
            "status": "completed",
            "errors_processed": 10,
            "agents_active": [],
            "progress": 100.0,
            "estimated_completion": None,
        }

        with patch.dict(
            "apps.backend.api.routers.error_handling.active_workflows", {workflow_id: mock_workflow}
        ):
            response = test_client.get(f"/api/v1/error-handling/workflow/{workflow_id}/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress_percentage"] == 100.0


@pytest.mark.unit
class TestPatternAnalysis:
    """Test suite for pattern analysis endpoints"""

    @pytest.fixture
    def mock_swarm_coordinator(self):
        """Mock swarm coordinator with pattern analyzer"""
        coordinator = Mock()
        coordinator.agents = {
            "pattern_analysis": Mock(
                analyze_error_patterns=AsyncMock(
                    return_value={
                        "patterns": [
                            {"type": "recurring_timeout", "count": 15},
                            {"type": "database_deadlock", "count": 8},
                        ],
                        "recommendations": ["Increase timeout", "Review locking"],
                    }
                )
            )
        }
        return coordinator

    def test_analyze_error_patterns_default_timeframe(self, test_client, mock_swarm_coordinator):
        """Test error pattern analysis with default timeframe"""
        with patch(
            "apps.backend.api.routers.error_handling.swarm_coordinator", mock_swarm_coordinator
        ):
            response = test_client.get("/api/v1/error-handling/patterns/analyze")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "analysis" in data
        assert data["timeframe_days"] == 7  # Default

    def test_analyze_error_patterns_custom_timeframe(self, test_client, mock_swarm_coordinator):
        """Test error pattern analysis with custom timeframe"""
        with patch(
            "apps.backend.api.routers.error_handling.swarm_coordinator", mock_swarm_coordinator
        ):
            response = test_client.get(
                "/api/v1/error-handling/patterns/analyze", params={"timeframe_days": 30}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["timeframe_days"] == 30

    def test_predict_errors_default_timeframe(self, test_client, mock_swarm_coordinator):
        """Test error prediction with default timeframe"""
        with patch(
            "apps.backend.api.routers.error_handling.swarm_coordinator", mock_swarm_coordinator
        ):
            response = test_client.post("/api/v1/error-handling/predict-errors")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "predictions" in data
        assert data["timeframe_hours"] == 24  # Default
        assert "confidence" in data

    def test_predict_errors_custom_timeframe(self, test_client, mock_swarm_coordinator):
        """Test error prediction with custom timeframe"""
        with patch(
            "apps.backend.api.routers.error_handling.swarm_coordinator", mock_swarm_coordinator
        ):
            response = test_client.post(
                "/api/v1/error-handling/predict-errors", params={"timeframe_hours": 48}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["timeframe_hours"] == 48


@pytest.mark.unit
class TestSwarmStatus:
    """Test suite for swarm status endpoint"""

    @pytest.fixture
    def mock_swarm_coordinator(self):
        """Mock swarm coordinator"""
        coordinator = Mock()
        coordinator.get_swarm_status = AsyncMock(
            return_value={
                "agents": {
                    "aggregation": {"status": "active", "errors_processed": 100},
                    "detection": {"status": "active", "patterns_found": 25},
                    "recovery": {"status": "idle", "recoveries_performed": 15},
                },
                "health": "healthy",
                "uptime_hours": 72.5,
            }
        )
        return coordinator

    def test_get_swarm_status_success(self, test_client, mock_swarm_coordinator):
        """Test successful swarm status retrieval"""
        with patch(
            "apps.backend.api.routers.error_handling.swarm_coordinator", mock_swarm_coordinator
        ):
            with patch.dict(
                "apps.backend.api.routers.error_handling.active_workflows", {"wf1": {}, "wf2": {}}
            ):
                response = test_client.get("/api/v1/error-handling/swarm/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "swarm_status" in data
        assert data["active_workflows"] == 2
        assert "timestamp" in data
        assert data["swarm_status"]["health"] == "healthy"


@pytest.mark.unit
class TestRecovery:
    """Test suite for recovery endpoints"""

    @pytest.fixture
    def mock_swarm_coordinator(self):
        """Mock swarm coordinator with recovery agent"""
        coordinator = Mock()
        recovery_agent = Mock()
        recovery_agent.orchestrate_recovery = AsyncMock(
            return_value=Mock(
                model_dump=Mock(
                    return_value={
                        "recovery_success": True,
                        "steps_executed": ["restart_service", "clear_cache"],
                        "component_health": "healthy",
                    }
                )
            )
        )
        coordinator.agents = {"recovery": recovery_agent}
        return coordinator

    def test_trigger_recovery_async(self, test_client, mock_swarm_coordinator):
        """Test asynchronous recovery trigger"""
        with patch(
            "apps.backend.api.routers.error_handling.swarm_coordinator", mock_swarm_coordinator
        ):
            response = test_client.post(
                "/api/v1/error-handling/recovery/trigger",
                params={"component": "database_pool", "strategy": "restart"},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "Recovery initiated for database_pool" in data["message"]
        assert data["async"] is True

    def test_trigger_recovery_sync(self, test_client, mock_swarm_coordinator):
        """Test synchronous recovery trigger"""
        with patch(
            "apps.backend.api.routers.error_handling.swarm_coordinator", mock_swarm_coordinator
        ):
            # Mock background_tasks to force sync path
            response = test_client.post(
                "/api/v1/error-handling/recovery/trigger", params={"component": "api_gateway"}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"

    def test_trigger_recovery_no_strategy(self, test_client, mock_swarm_coordinator):
        """Test recovery trigger without explicit strategy"""
        with patch(
            "apps.backend.api.routers.error_handling.swarm_coordinator", mock_swarm_coordinator
        ):
            response = test_client.post(
                "/api/v1/error-handling/recovery/trigger", params={"component": "cache_service"}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"


@pytest.mark.unit
class TestMetrics:
    """Test suite for metrics endpoint"""

    @pytest.fixture
    def mock_swarm_coordinator(self):
        """Mock swarm coordinator with multiple agents"""
        coordinator = Mock()
        coordinator.agents = {
            "aggregation": Mock(
                get_error_metrics=AsyncMock(
                    return_value={"total_aggregated": 500, "avg_aggregation_time": 0.15}
                )
            ),
            "detection": Mock(
                get_error_metrics=AsyncMock(
                    return_value={"patterns_detected": 75, "accuracy": 0.92}
                )
            ),
            "recovery": Mock(
                get_error_metrics=AsyncMock(
                    return_value={"recoveries_attempted": 50, "success_rate": 0.88}
                )
            ),
            "pattern_analysis": Mock(
                get_error_metrics=AsyncMock(
                    return_value={"analyses_performed": 100, "insights_generated": 25}
                )
            ),
        }
        return coordinator

    def test_get_error_metrics_success(self, test_client, mock_swarm_coordinator):
        """Test successful metrics retrieval"""
        mock_workflows = {
            "wf1": {"errors_processed": 10},
            "wf2": {"errors_processed": 15},
            "wf3": {"errors_processed": 5},
        }

        with patch(
            "apps.backend.api.routers.error_handling.swarm_coordinator", mock_swarm_coordinator
        ):
            with patch.dict(
                "apps.backend.api.routers.error_handling.active_workflows", mock_workflows
            ):
                response = test_client.get("/api/v1/error-handling/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "metrics" in data
        assert "timestamp" in data

        metrics = data["metrics"]
        assert "aggregation" in metrics
        assert "detection" in metrics
        assert "recovery" in metrics
        assert "pattern_analysis" in metrics
        assert "workflows" in metrics

        # Verify workflow metrics
        assert metrics["workflows"]["active"] == 3
        assert metrics["workflows"]["total_processed"] == 30

    def test_get_error_metrics_empty_workflows(self, test_client, mock_swarm_coordinator):
        """Test metrics with no active workflows"""
        with patch(
            "apps.backend.api.routers.error_handling.swarm_coordinator", mock_swarm_coordinator
        ):
            with patch.dict("apps.backend.api.routers.error_handling.active_workflows", {}):
                response = test_client.get("/api/v1/error-handling/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["metrics"]["workflows"]["active"] == 0
        assert data["metrics"]["workflows"]["total_processed"] == 0


@pytest.mark.unit
class TestBackgroundTasks:
    """Test suite for background task processing"""

    @pytest.mark.asyncio
    async def test_process_single_error(self):
        """Test single error background processing"""
        from apps.backend.api.routers.error_handling import process_single_error

        error_state = {
            "error_id": "err_test_123",
            "error_type": "RUNTIME",
            "priority": "MEDIUM",
            "description": "Test error",
            "resolution_status": "pending",
        }

        mock_aggregator = Mock()
        mock_aggregator.aggregate_errors = AsyncMock()

        mock_coordinator = Mock()
        mock_coordinator.agents = {"aggregation": mock_aggregator}

        with patch("apps.backend.api.routers.error_handling.swarm_coordinator", mock_coordinator):
            await process_single_error(error_state)

        mock_aggregator.aggregate_errors.assert_called_once_with([error_state], source="api")

    @pytest.mark.asyncio
    async def test_run_swarm_workflow(self):
        """Test swarm workflow background execution"""
        from apps.backend.api.routers.error_handling import (
            active_workflows,
            run_swarm_workflow,
        )

        workflow_id = "test_workflow_123"
        error_states = [
            {"error_id": "err1", "description": "Error 1"},
            {"error_id": "err2", "description": "Error 2"},
        ]
        context = {"environment": "test"}

        mock_result = Mock()
        mock_result.errors_processed = 2
        mock_result.agents_involved = ["aggregation", "detection"]
        mock_result.model_dump = Mock(return_value={"status": "success"})

        mock_coordinator = Mock()
        mock_coordinator.orchestrate_error_handling = AsyncMock(return_value=mock_result)

        with patch("apps.backend.api.routers.error_handling.swarm_coordinator", mock_coordinator):
            with patch.dict(
                "apps.backend.api.routers.error_handling.active_workflows", {}, clear=True
            ):
                await run_swarm_workflow(workflow_id, error_states, context)

                # Verify workflow was tracked
                assert workflow_id in active_workflows
                assert active_workflows[workflow_id]["status"] == "completed"
                assert active_workflows[workflow_id]["errors_processed"] == 2

    @pytest.mark.asyncio
    async def test_run_swarm_workflow_failure(self):
        """Test swarm workflow failure handling"""
        from apps.backend.api.routers.error_handling import (
            active_workflows,
            run_swarm_workflow,
        )

        workflow_id = "test_workflow_fail"
        error_states = [{"error_id": "err1"}]
        context = {}

        mock_coordinator = Mock()
        mock_coordinator.orchestrate_error_handling = AsyncMock(
            side_effect=Exception("Processing failed")
        )

        with patch("apps.backend.api.routers.error_handling.swarm_coordinator", mock_coordinator):
            with patch.dict(
                "apps.backend.api.routers.error_handling.active_workflows", {}, clear=True
            ):
                await run_swarm_workflow(workflow_id, error_states, context)

                # Verify workflow failure was tracked
                assert workflow_id in active_workflows
                assert active_workflows[workflow_id]["status"] == "failed"
                assert "error" in active_workflows[workflow_id]
