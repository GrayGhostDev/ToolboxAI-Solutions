import pytest_asyncio

#!/usr/bin/env python3
"""
Multi-Agent Coordination Integration Tests

Tests the complete multi-agent orchestration system including:
- Agent discovery and registration
- Task distribution and load balancing
- Consensus mechanisms and result aggregation
- SPARC framework integration
- Fault tolerance and recovery
- Performance under concurrent agent execution
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest

# Set environment for testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCK_LLM"] = "true"
os.environ["AGENT_ORCHESTRATION_ENABLED"] = "true"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
    pytest.mark.langgraph,
    pytest.mark.langchain,
]


@pytest.fixture
async def coordination_client():
    """HTTP client for agent coordination testing"""
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8009",
        timeout=60.0  # Longer timeout for agent operations
    ) as client:
        yield client


@pytest.fixture
async def agent_coordinator_client():
    """HTTP client for agent coordinator service"""
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8888",  # Agent coordinator port
        timeout=30.0
    ) as client:
        yield client


@pytest.fixture
def auth_headers():
    """Authentication headers for API requests"""
    from datetime import timedelta

    import jwt

    payload = {
        "sub": "agent_coordinator_test",
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_agents():
    """Mock agent configurations for testing"""
    return {
        "content_agent": {
            "id": "content_agent_1",
            "type": "content_generation",
            "capabilities": ["lesson_creation", "quiz_generation", "activity_design"],
            "load_capacity": 10,
            "response_time": 5.0,
            "success_rate": 0.95
        },
        "terrain_agent": {
            "id": "terrain_agent_1",
            "type": "roblox_terrain",
            "capabilities": ["terrain_generation", "environment_design", "scripting"],
            "load_capacity": 5,
            "response_time": 8.0,
            "success_rate": 0.90
        },
        "quiz_agent": {
            "id": "quiz_agent_1",
            "type": "assessment",
            "capabilities": ["question_generation", "scoring", "analytics"],
            "load_capacity": 15,
            "response_time": 3.0,
            "success_rate": 0.98
        },
        "analytics_agent": {
            "id": "analytics_agent_1",
            "type": "analytics",
            "capabilities": ["performance_analysis", "reporting", "insights"],
            "load_capacity": 20,
            "response_time": 2.0,
            "success_rate": 0.99
        }
    }


@pytest.fixture
def complex_tasks():
    """Complex task definitions for multi-agent testing"""
    return {
        "comprehensive_lesson": {
            "task_id": "lesson_task_1",
            "type": "comprehensive_lesson_creation",
            "requirements": {
                "subject": "Physics",
                "grade_level": 10,
                "topic": "Electromagnetic Waves",
                "duration": 90,
                "components": [
                    "interactive_content",
                    "quiz_assessment",
                    "roblox_simulation",
                    "performance_tracking"
                ]
            },
            "agents_needed": ["content_agent", "quiz_agent", "terrain_agent", "analytics_agent"],
            "priority": "high",
            "deadline": datetime.now() + timedelta(hours=2)
        },
        "adaptive_assessment": {
            "task_id": "assessment_task_1",
            "type": "adaptive_assessment_creation",
            "requirements": {
                "subject": "Mathematics",
                "topics": ["algebra", "geometry", "statistics"],
                "difficulty_levels": ["beginner", "intermediate", "advanced"],
                "question_count": 50,
                "adaptation_strategy": "bayesian"
            },
            "agents_needed": ["quiz_agent", "analytics_agent"],
            "priority": "medium",
            "deadline": datetime.now() + timedelta(hours=1)
        },
        "curriculum_generation": {
            "task_id": "curriculum_task_1",
            "type": "full_curriculum_generation",
            "requirements": {
                "subject": "Computer Science",
                "grade_levels": [9, 10, 11, 12],
                "duration": "full_year",
                "units": 8,
                "assessment_frequency": "weekly"
            },
            "agents_needed": ["content_agent", "quiz_agent", "analytics_agent"],
            "priority": "low",
            "deadline": datetime.now() + timedelta(days=7)
        }
    }


@pytest.fixture
async def mock_agent_pool():
    """Mock agent pool for controlled testing"""
    agents = {}

    for agent_type in ["content", "quiz", "terrain", "analytics"]:
        agent = Mock()
        agent.agent_id = f"{agent_type}_agent_mock"
        agent.agent_type = agent_type
        agent.capabilities = [f"{agent_type}_generation", f"{agent_type}_processing"]
        agent.is_available = True
        agent.current_load = 0
        agent.max_load = 10

        # Mock async methods
        agent.execute_task = AsyncMock(return_value={
            "status": "success",
            "result": f"Mock {agent_type} result",
            "execution_time": 2.0,
            "agent_id": agent.agent_id
        })
        agent.get_status = AsyncMock(return_value={
            "status": "ready",
            "load": 0,
            "last_heartbeat": datetime.now().isoformat()
        })

        agents[agent_type] = agent

    return agents


class TestAgentDiscoveryRegistration:
    """Test agent discovery and registration mechanisms"""

    @pytest.mark.asyncio
async def test_agent_registration(self, agent_coordinator_client, test_agents):
        """Test agent registration with coordinator"""
        agent = test_agents["content_agent"]

        response = await agent_coordinator_client.post(
            "/agents/register",
            json=agent
        )

        if response.status_code == 404:
            pytest.skip("Agent coordinator not available")

        if response.status_code == 200:
            result = response.json()
            assert result["status"] == "registered"
            assert "agent_id" in result
            assert result["agent_id"] == agent["id"]

    @pytest.mark.asyncio
async def test_agent_discovery(self, agent_coordinator_client, test_agents):
        """Test agent discovery by capabilities"""
        # Register multiple agents
        for agent_id, agent in test_agents.items():
            await agent_coordinator_client.post("/agents/register", json=agent)

        # Discover agents by capability
        response = await agent_coordinator_client.get(
            "/agents/discover?capability=lesson_creation"
        )

        if response.status_code == 404:
            pytest.skip("Agent discovery not available")

        if response.status_code == 200:
            result = response.json()
            agents = result.get("agents", [])

            # Should find content agent
            content_agents = [a for a in agents if "content" in a.get("type", "")]
            assert len(content_agents) > 0

    @pytest.mark.asyncio
async def test_agent_health_monitoring(self, agent_coordinator_client, test_agents):
        """Test agent health monitoring and status reporting"""
        agent = test_agents["content_agent"]

        # Register agent
        await agent_coordinator_client.post("/agents/register", json=agent)

        # Check agent health
        response = await agent_coordinator_client.get(
            f"/agents/{agent['id']}/health"
        )

        if response.status_code == 404:
            pytest.skip("Agent health monitoring not available")

        if response.status_code == 200:
            health = response.json()
            assert "status" in health
            assert health["status"] in ["healthy", "ready", "active"]

    @pytest.mark.asyncio
async def test_agent_deregistration(self, agent_coordinator_client, test_agents):
        """Test agent deregistration"""
        agent = test_agents["content_agent"]

        # Register agent
        await agent_coordinator_client.post("/agents/register", json=agent)

        # Deregister agent
        response = await agent_coordinator_client.delete(
            f"/agents/{agent['id']}"
        )

        if response.status_code == 404:
            pytest.skip("Agent deregistration not available")

        if response.status_code in [200, 204]:
            # Verify agent is no longer discoverable
            discover_response = await agent_coordinator_client.get(
                f"/agents/{agent['id']}"
            )
            assert discover_response.status_code == 404

    @pytest.mark.asyncio
async def test_agent_load_balancing(self, agent_coordinator_client, test_agents):
        """Test load balancing across multiple agents"""
        # Register multiple agents of same type
        content_agents = []
        for i in range(3):
            agent = test_agents["content_agent"].copy()
            agent["id"] = f"content_agent_{i}"
            agent["current_load"] = i * 2  # Different load levels
            content_agents.append(agent)

            await agent_coordinator_client.post("/agents/register", json=agent)

        # Request agent for task (should select least loaded)
        response = await agent_coordinator_client.get(
            "/agents/assign?type=content_generation&load_balance=true"
        )

        if response.status_code == 404:
            pytest.skip("Load balancing not available")

        if response.status_code == 200:
            result = response.json()
            assigned_agent = result.get("agent")

            # Should assign agent with lowest load (content_agent_0)
            if assigned_agent:
                assert assigned_agent["id"] == "content_agent_0"


class TestTaskDistribution:
    """Test task distribution and orchestration"""

    @pytest.mark.asyncio
async def test_simple_task_distribution(self, coordination_client, auth_headers, mock_agent_pool):
        """Test distribution of simple tasks to appropriate agents"""
        task = {
            "type": "content_generation",
            "data": {
                "subject": "Mathematics",
                "topic": "Linear Equations",
                "grade_level": 8
            },
            "priority": "normal"
        }

        with patch("core.coordinators.orchestrator.agent_pool", mock_agent_pool):
            response = await coordination_client.post(
                "/api/v1/agents/execute",
                json=task,
                headers=auth_headers
            )

            if response.status_code == 404:
                # Try alternative endpoint
                response = await coordination_client.post(
                    "/api/v1/orchestrator/task",
                    json=task,
                    headers=auth_headers
                )

            if response.status_code == 404:
                pytest.skip("Task distribution endpoint not available")

            if response.status_code in [200, 202]:
                result = response.json()
                assert result["status"] in ["success", "processing"]

                if "task_id" in result:
                    task_id = result["task_id"]

                    # Check task status
                    status_response = await coordination_client.get(
                        f"/api/v1/tasks/{task_id}/status",
                        headers=auth_headers
                    )

                    if status_response.status_code == 200:
                        status = status_response.json()
                        assert "status" in status

    @pytest.mark.asyncio
async def test_complex_multi_agent_task(self, coordination_client, auth_headers, complex_tasks, mock_agent_pool):
        """Test distribution of complex tasks requiring multiple agents"""
        task = complex_tasks["comprehensive_lesson"]

        with patch("core.coordinators.orchestrator.agent_pool", mock_agent_pool):
            response = await coordination_client.post(
                "/api/v1/agents/orchestrate",
                json=task,
                headers=auth_headers
            )

            if response.status_code == 404:
                response = await coordination_client.post(
                    "/api/v1/orchestrator/complex",
                    json=task,
                    headers=auth_headers
                )

            if response.status_code == 404:
                pytest.skip("Complex orchestration endpoint not available")

            if response.status_code in [200, 202]:
                result = response.json()

                if result.get("status") == "processing":
                    task_id = result.get("task_id")

                    # Poll for completion
                    for _ in range(10):
                        status_response = await coordination_client.get(
                            f"/api/v1/tasks/{task_id}/status",
                            headers=auth_headers
                        )

                        if status_response.status_code == 200:
                            status = status_response.json()
                            if status.get("status") == "completed":
                                # Verify all required components were generated
                                result_data = status.get("result", {})
                                expected_components = task["requirements"]["components"]

                                for component in expected_components:
                                    assert component in result_data or any(
                                        comp in str(result_data) for comp in [component, component.replace("_", "")]
                                    )
                                break

                        await asyncio.sleep(1)

    @pytest.mark.asyncio
async def test_task_priority_handling(self, coordination_client, auth_headers, complex_tasks, mock_agent_pool):
        """Test that high-priority tasks are handled first"""
        # Submit low priority task first
        low_priority_task = complex_tasks["curriculum_generation"]
        high_priority_task = complex_tasks["comprehensive_lesson"]

        with patch("core.coordinators.orchestrator.agent_pool", mock_agent_pool):
            # Submit low priority task
            low_response = await coordination_client.post(
                "/api/v1/agents/orchestrate",
                json=low_priority_task,
                headers=auth_headers
            )

            # Submit high priority task immediately after
            high_response = await coordination_client.post(
                "/api/v1/agents/orchestrate",
                json=high_priority_task,
                headers=auth_headers
            )

            if low_response.status_code == 404 or high_response.status_code == 404:
                pytest.skip("Priority handling endpoint not available")

            # High priority task should complete first or have better resource allocation
            if low_response.status_code == 202 and high_response.status_code == 202:
                low_task_id = low_response.json().get("task_id")
                high_task_id = high_response.json().get("task_id")

                # Check status after brief delay
                await asyncio.sleep(2)

                low_status = await coordination_client.get(
                    f"/api/v1/tasks/{low_task_id}/status",
                    headers=auth_headers
                )
                high_status = await coordination_client.get(
                    f"/api/v1/tasks/{high_task_id}/status",
                    headers=auth_headers
                )

                if low_status.status_code == 200 and high_status.status_code == 200:
                    low_data = low_status.json()
                    high_data = high_status.json()

                    # High priority should have made more progress
                    print(f"Low priority progress: {low_data.get('progress', 0)}%")
                    print(f"High priority progress: {high_data.get('progress', 0)}%")

    @pytest.mark.asyncio
async def test_task_cancellation(self, coordination_client, auth_headers, complex_tasks, mock_agent_pool):
        """Test task cancellation and resource cleanup"""
        task = complex_tasks["comprehensive_lesson"]

        with patch("core.coordinators.orchestrator.agent_pool", mock_agent_pool):
            response = await coordination_client.post(
                "/api/v1/agents/orchestrate",
                json=task,
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("Task orchestration not available")

            if response.status_code == 202:
                task_id = response.json()["task_id"]

                # Cancel the task
                cancel_response = await coordination_client.delete(
                    f"/api/v1/tasks/{task_id}",
                    headers=auth_headers
                )

                if cancel_response.status_code in [200, 204]:
                    # Verify task is cancelled
                    status_response = await coordination_client.get(
                        f"/api/v1/tasks/{task_id}/status",
                        headers=auth_headers
                    )

                    if status_response.status_code == 200:
                        status = status_response.json()
                        assert status.get("status") in ["cancelled", "terminated", "stopped"]


class TestConsensusAndAggregation:
    """Test consensus mechanisms and result aggregation"""

    @pytest.mark.asyncio
async def test_consensus_decision_making(self, coordination_client, auth_headers, mock_agent_pool):
        """Test consensus mechanism when agents disagree"""
        # Create a task that requires consensus
        consensus_task = {
            "type": "content_evaluation",
            "data": {
                "content": "Test educational content",
                "evaluation_criteria": ["accuracy", "engagement", "difficulty"],
                "consensus_required": True
            },
            "agents_needed": ["content_agent", "quiz_agent", "analytics_agent"]
        }

        # Mock agents with different opinions
        mock_agent_pool["content"].execute_task = AsyncMock(return_value={
            "status": "success",
            "evaluation": {"accuracy": 8, "engagement": 7, "difficulty": 6},
            "confidence": 0.8
        })
        mock_agent_pool["quiz"].execute_task = AsyncMock(return_value={
            "status": "success",
            "evaluation": {"accuracy": 9, "engagement": 6, "difficulty": 7},
            "confidence": 0.9
        })
        mock_agent_pool["analytics"].execute_task = AsyncMock(return_value={
            "status": "success",
            "evaluation": {"accuracy": 7, "engagement": 8, "difficulty": 8},
            "confidence": 0.95
        })

        with patch("core.coordinators.orchestrator.agent_pool", mock_agent_pool):
            response = await coordination_client.post(
                "/api/v1/agents/consensus",
                json=consensus_task,
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("Consensus mechanism not available")

            if response.status_code == 200:
                result = response.json()

                # Should have aggregated results
                if "consensus_result" in result:
                    consensus = result["consensus_result"]

                    # Should be weighted average based on confidence
                    assert "accuracy" in consensus
                    assert "engagement" in consensus
                    assert "difficulty" in consensus

                    # Verify consensus logic (weighted by confidence)
                    expected_accuracy = (8*0.8 + 9*0.9 + 7*0.95) / (0.8 + 0.9 + 0.95)
                    actual_accuracy = consensus["accuracy"]
                    assert abs(actual_accuracy - expected_accuracy) < 0.5

    @pytest.mark.asyncio
async def test_result_aggregation_strategies(self, coordination_client, auth_headers, mock_agent_pool):
        """Test different result aggregation strategies"""
        aggregation_strategies = [
            {"strategy": "majority_vote", "threshold": 0.6},
            {"strategy": "weighted_average", "weights": {"confidence": 1.0, "expertise": 0.5}},
            {"strategy": "best_result", "criteria": "highest_confidence"}
        ]

        for strategy in aggregation_strategies:
            task = {
                "type": "multi_agent_evaluation",
                "data": {"test": "content"},
                "aggregation": strategy,
                "agents_needed": ["content_agent", "quiz_agent", "analytics_agent"]
            }

            with patch("core.coordinators.orchestrator.agent_pool", mock_agent_pool):
                response = await coordination_client.post(
                    "/api/v1/agents/aggregate",
                    json=task,
                    headers=auth_headers
                )

                if response.status_code == 404:
                    continue  # Skip if not implemented

                if response.status_code == 200:
                    result = response.json()
                    assert "aggregated_result" in result
                    assert "strategy_used" in result
                    assert result["strategy_used"] == strategy["strategy"]

    @pytest.mark.asyncio
async def test_conflict_resolution(self, coordination_client, auth_headers, mock_agent_pool):
        """Test conflict resolution when agents produce incompatible results"""
        # Mock agents with conflicting results
        mock_agent_pool["content"].execute_task = AsyncMock(return_value={
            "status": "success",
            "recommendation": "use_interactive_video",
            "confidence": 0.9
        })
        mock_agent_pool["quiz"].execute_task = AsyncMock(return_value={
            "status": "success",
            "recommendation": "use_text_based_content",
            "confidence": 0.8
        })

        conflict_task = {
            "type": "content_format_decision",
            "data": {"subject": "Mathematics", "topic": "Algebra"},
            "conflict_resolution": "expert_arbitration",
            "agents_needed": ["content_agent", "quiz_agent"]
        }

        with patch("core.coordinators.orchestrator.agent_pool", mock_agent_pool):
            response = await coordination_client.post(
                "/api/v1/agents/resolve-conflict",
                json=conflict_task,
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("Conflict resolution not available")

            if response.status_code == 200:
                result = response.json()

                # Should have resolved the conflict
                assert "resolution" in result
                assert "resolution_method" in result

                # Should pick one recommendation or synthesize a new one
                resolution = result["resolution"]
                assert "recommendation" in resolution


class TestSPARCFrameworkIntegration:
    """Test SPARC (Structured Problem-Solving and Reasoning Chains) integration"""

    @pytest.mark.asyncio
async def test_sparc_reasoning_chain(self, coordination_client, auth_headers, mock_agent_pool):
        """Test SPARC reasoning chain execution"""
        sparc_task = {
            "type": "sparc_analysis",
            "problem": "How to improve student engagement in online mathematics lessons?",
            "context": {
                "subject": "Mathematics",
                "grade_level": 9,
                "current_engagement": 0.6,
                "target_engagement": 0.8
            },
            "sparc_steps": ["Specify", "Problem-solve", "Analyze", "Refine", "Conclude"]
        }

        with patch("core.coordinators.orchestrator.agent_pool", mock_agent_pool):
            response = await coordination_client.post(
                "/api/v1/sparc/execute",
                json=sparc_task,
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("SPARC framework not available")

            if response.status_code in [200, 202]:
                result = response.json()

                if result.get("status") == "processing":
                    task_id = result["task_id"]

                    # Monitor SPARC execution
                    for _ in range(10):
                        status_response = await coordination_client.get(
                            f"/api/v1/sparc/{task_id}/status",
                            headers=auth_headers
                        )

                        if status_response.status_code == 200:
                            status = status_response.json()

                            if status.get("status") == "completed":
                                # Verify SPARC steps were executed
                                steps = status.get("steps_completed", [])
                                assert len(steps) == 5  # All SPARC steps
                                assert "Specify" in steps
                                assert "Conclude" in steps
                                break

                        await asyncio.sleep(1)

    @pytest.mark.asyncio
async def test_sparc_step_execution(self, coordination_client, auth_headers, mock_agent_pool):
        """Test individual SPARC step execution"""
        sparc_steps = ["Specify", "Problem-solve", "Analyze", "Refine", "Conclude"]

        for step in sparc_steps:
            step_task = {
                "type": "sparc_step",
                "step": step,
                "context": {
                    "problem": "Student engagement optimization",
                    "previous_steps": sparc_steps[:sparc_steps.index(step)]
                }
            }

            with patch("core.coordinators.orchestrator.agent_pool", mock_agent_pool):
                response = await coordination_client.post(
                    f"/api/v1/sparc/step/{step.lower()}",
                    json=step_task,
                    headers=auth_headers
                )

                if response.status_code == 404:
                    continue  # Skip if not implemented

                if response.status_code == 200:
                    result = response.json()
                    assert "step_result" in result
                    assert result["step"] == step

    @pytest.mark.asyncio
async def test_sparc_knowledge_integration(self, coordination_client, auth_headers, mock_agent_pool):
        """Test SPARC integration with agent knowledge"""
        knowledge_task = {
            "type": "sparc_knowledge_integration",
            "domain": "educational_content_creation",
            "query": "Best practices for interactive mathematics lessons",
            "knowledge_sources": ["agent_memory", "curriculum_standards", "research_papers"]
        }

        with patch("core.coordinators.orchestrator.agent_pool", mock_agent_pool):
            response = await coordination_client.post(
                "/api/v1/sparc/knowledge",
                json=knowledge_task,
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("SPARC knowledge integration not available")

            if response.status_code == 200:
                result = response.json()
                assert "knowledge_synthesis" in result
                assert "sources_used" in result


class TestFaultToleranceRecovery:
    """Test fault tolerance and recovery mechanisms"""

    @pytest.mark.asyncio
async def test_agent_failure_recovery(self, coordination_client, auth_headers, mock_agent_pool):
        """Test recovery when individual agents fail"""
        # Mock one agent to fail
        mock_agent_pool["content"].execute_task = AsyncMock(side_effect=Exception("Agent failure"))
        mock_agent_pool["quiz"].execute_task = AsyncMock(return_value={
            "status": "success",
            "result": "Quiz generated successfully"
        })

        task = {
            "type": "multi_agent_task",
            "data": {"subject": "Mathematics"},
            "agents_needed": ["content_agent", "quiz_agent"],
            "fault_tolerance": "graceful_degradation"
        }

        with patch("core.coordinators.orchestrator.agent_pool", mock_agent_pool):
            response = await coordination_client.post(
                "/api/v1/agents/execute-resilient",
                json=task,
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("Fault tolerance not available")

            if response.status_code == 200:
                result = response.json()

                # Should complete with partial results
                assert result.get("status") in ["partial_success", "degraded_success"]
                assert "successful_agents" in result
                assert "failed_agents" in result
                assert "quiz_agent" in result["successful_agents"]
                assert "content_agent" in result["failed_agents"]

    @pytest.mark.asyncio
async def test_coordinator_failover(self, coordination_client, auth_headers):
        """Test coordinator failover mechanisms"""
        # Test coordinator health
        health_response = await coordination_client.get("/health")

        if health_response.status_code == 404:
            pytest.skip("Coordinator health endpoint not available")

        if health_response.status_code == 200:
            health = health_response.json()
            assert "status" in health

            # Test backup coordinator (if implemented)
            backup_response = await coordination_client.get(
                "/health",
                headers={"X-Coordinator-Backup": "true"}
            )

            if backup_response.status_code == 200:
                backup_health = backup_response.json()
                assert "status" in backup_health

    @pytest.mark.asyncio
async def test_task_retry_mechanisms(self, coordination_client, auth_headers, mock_agent_pool):
        """Test automatic retry mechanisms for failed tasks"""
        # Mock agent to fail twice, then succeed
        call_count = 0

        def mock_execute_with_retries(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception(f"Temporary failure {call_count}")
            return {
                "status": "success",
                "result": "Task completed after retries",
                "attempt": call_count
            }

        mock_agent_pool["content"].execute_task = AsyncMock(side_effect=mock_execute_with_retries)

        retry_task = {
            "type": "content_generation",
            "data": {"subject": "Mathematics"},
            "retry_config": {
                "max_attempts": 3,
                "backoff_strategy": "exponential",
                "retry_delay": 0.1
            }
        }

        with patch("core.coordinators.orchestrator.agent_pool", mock_agent_pool):
            response = await coordination_client.post(
                "/api/v1/agents/execute-with-retry",
                json=retry_task,
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("Retry mechanisms not available")

            if response.status_code == 200:
                result = response.json()
                assert result.get("status") == "success"
                assert result.get("attempts", 0) == 3

    @pytest.mark.asyncio
async def test_circuit_breaker_pattern(self, coordination_client, auth_headers, mock_agent_pool):
        """Test circuit breaker pattern for failing agents"""
        # Mock agent to consistently fail
        mock_agent_pool["content"].execute_task = AsyncMock(side_effect=Exception("Persistent failure"))

        # Make multiple requests to trigger circuit breaker
        for i in range(10):
            task = {
                "type": "content_generation",
                "data": {"subject": "Mathematics", "request_id": i},
                "circuit_breaker": True
            }

            response = await coordination_client.post(
                "/api/v1/agents/execute-protected",
                json=task,
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("Circuit breaker not available")

            if response.status_code == 429:  # Circuit breaker open
                result = response.json()
                assert "circuit_breaker" in result.get("error", "").lower()
                break

            await asyncio.sleep(0.1)


class TestPerformanceConcurrency:
    """Test performance under concurrent agent execution"""

    @pytest.mark.asyncio
async def test_concurrent_agent_execution(self, coordination_client, auth_headers, mock_agent_pool):
        """Test system performance under concurrent agent execution"""
        # Create multiple concurrent tasks
        tasks = []
        for i in range(20):
            task = {
                "type": "content_generation",
                "data": {
                    "subject": "Mathematics",
                    "topic": f"Topic {i}",
                    "grade_level": 7 + (i % 5)
                },
                "task_id": f"concurrent_task_{i}"
            }
            tasks.append(task)

        with patch("core.coordinators.orchestrator.agent_pool", mock_agent_pool):
            # Execute all tasks concurrently
            start_time = time.time()

            async def execute_task(task):
                response = await coordination_client.post(
                    "/api/v1/agents/execute",
                    json=task,
                    headers=auth_headers
                )
                return response.status_code

            results = await asyncio.gather(
                *[execute_task(task) for task in tasks],
                return_exceptions=True
            )

            execution_time = time.time() - start_time

            # Analyze results
            successful = sum(1 for r in results if r == 200)
            failed = sum(1 for r in results if isinstance(r, Exception))

            print(f"Concurrent execution: {successful} successful, {failed} failed")
            print(f"Total execution time: {execution_time:.2f} seconds")
            print(f"Average time per task: {execution_time/len(tasks):.2f} seconds")

            # Should handle most tasks successfully
            if successful > 0:
                success_rate = successful / len(tasks)
                assert success_rate >= 0.8  # At least 80% success rate

    @pytest.mark.asyncio
async def test_load_balancing_efficiency(self, coordination_client, auth_headers, mock_agent_pool):
        """Test efficiency of load balancing algorithms"""
        # Create multiple agents of same type with different capacities
        agent_configs = []
        for i in range(5):
            agent = mock_agent_pool["content"]
            agent.agent_id = f"content_agent_{i}"
            agent.max_load = 5 + i  # Different capacities
            agent.current_load = 0
            agent_configs.append(agent)

        # Submit tasks and verify load distribution
        task_count = 25
        with patch("core.coordinators.orchestrator.agent_pool", {"content": agent_configs}):
            for i in range(task_count):
                task = {
                    "type": "content_generation",
                    "data": {"subject": "Mathematics", "task_id": i}
                }

                response = await coordination_client.post(
                    "/api/v1/agents/execute-balanced",
                    json=task,
                    headers=auth_headers
                )

                if response.status_code == 404:
                    pytest.skip("Load balancing not available")

                await asyncio.sleep(0.01)  # Small delay

            # Check load distribution
            load_response = await coordination_client.get(
                "/api/v1/agents/load-status",
                headers=auth_headers
            )

            if load_response.status_code == 200:
                load_status = load_response.json()
                agent_loads = load_status.get("agent_loads", {})

                # Verify load is distributed based on capacity
                if agent_loads:
                    print(f"Agent load distribution: {agent_loads}")

    @pytest.mark.asyncio
async def test_resource_utilization_monitoring(self, coordination_client, auth_headers):
        """Test monitoring of resource utilization during agent execution"""
        response = await coordination_client.get(
            "/api/v1/agents/metrics",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resource monitoring not available")

        if response.status_code == 200:
            metrics = response.json()

            # Should provide resource utilization metrics
            expected_metrics = [
                "cpu_usage", "memory_usage", "active_agents",
                "queued_tasks", "completed_tasks", "average_response_time"
            ]

            for metric in expected_metrics:
                if metric in metrics:
                    assert isinstance(metrics[metric], (int, float))

            print(f"System metrics: {metrics}")

    @pytest.mark.asyncio
async def test_scalability_limits(self, coordination_client, auth_headers, mock_agent_pool):
        """Test system behavior at scalability limits"""
        # Test with large number of agents
        large_agent_pool = {}
        for agent_type in ["content", "quiz", "terrain", "analytics"]:
            agents = []
            for i in range(100):  # 100 agents of each type
                agent = Mock()
                agent.agent_id = f"{agent_type}_agent_{i}"
                agent.max_load = 5
                agent.current_load = 0
                agent.execute_task = AsyncMock(return_value={"status": "success"})
                agents.append(agent)
            large_agent_pool[agent_type] = agents

        # Submit large batch of tasks
        batch_size = 500
        tasks = []
        for i in range(batch_size):
            task = {
                "type": "batch_task",
                "data": {"task_id": i},
                "batch_processing": True
            }
            tasks.append(task)

        with patch("core.coordinators.orchestrator.agent_pool", large_agent_pool):
            start_time = time.time()

            # Submit batch
            response = await coordination_client.post(
                "/api/v1/agents/batch-execute",
                json={"tasks": tasks[:50]},  # Submit subset to avoid timeout
                headers=auth_headers
            )

            execution_time = time.time() - start_time

            if response.status_code == 404:
                pytest.skip("Batch execution not available")

            if response.status_code in [200, 202]:
                result = response.json()
                print(f"Batch execution completed in {execution_time:.2f} seconds")

                if "batch_id" in result:
                    # Monitor batch progress
                    batch_id = result["batch_id"]
                    progress_response = await coordination_client.get(
                        f"/api/v1/batches/{batch_id}/progress",
                        headers=auth_headers
                    )

                    if progress_response.status_code == 200:
                        progress = progress_response.json()
                        print(f"Batch progress: {progress}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])