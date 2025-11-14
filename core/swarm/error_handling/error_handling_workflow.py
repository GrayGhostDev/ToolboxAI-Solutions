"""
LangGraph Workflow for Error Handling Swarm

Implements the complete error handling workflow using LangGraph
with parallel processing, consensus mechanisms, and adaptive routing.
"""

import asyncio
import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Any, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from core.agents.error_handling.swarm_coordinator import (
    ErrorHandlingSwarmCoordinator,
)

logger = logging.getLogger(__name__)


class ErrorHandlingWorkflowState(TypedDict):
    """Extended state for the error handling workflow"""

    # Core state
    errors: list[dict[str, Any]]
    agents: list[str]
    decisions: list[dict[str, Any]]
    consensus: dict[str, Any]

    # Workflow control
    phase: str
    parallel_tasks: list[dict[str, Any]]
    completed_tasks: list[str]

    # Results
    fixes_applied: list[dict[str, Any]]
    tests_passed: bool
    recovery_success: bool

    # Monitoring
    metrics: dict[str, Any]
    alerts: list[dict[str, Any]]

    # Messages
    messages: Sequence[BaseMessage]


class ErrorHandlingWorkflow:
    """
    Complete LangGraph workflow for error handling with parallel processing.
    """

    def __init__(self):
        self.coordinator = ErrorHandlingSwarmCoordinator()
        self.workflow = self._build_workflow()
        self.memory = MemorySaver()

        logger.info("Initialized Error Handling Workflow")

    def _build_workflow(self) -> StateGraph:
        """Build the complete workflow graph"""
        workflow = StateGraph(ErrorHandlingWorkflowState)

        # Phase 1: Collection and Analysis (Parallel)
        workflow.add_node("collect_errors", self._collect_errors)
        workflow.add_node("initial_analysis", self._initial_analysis)

        # Phase 2: Agent Assignment (Consensus)
        workflow.add_node("assign_agents", self._assign_agents_with_consensus)

        # Phase 3: Parallel Processing
        workflow.add_node("parallel_debug", self._parallel_debug)
        workflow.add_node("parallel_correct", self._parallel_correct)
        workflow.add_node("parallel_test", self._parallel_test)

        # Phase 4: Recovery and Monitoring
        workflow.add_node("orchestrate_recovery", self._orchestrate_recovery)
        workflow.add_node("monitor_results", self._monitor_results)

        # Phase 5: Learning and Completion
        workflow.add_node("learn_from_results", self._learn_from_results)
        workflow.add_node("generate_report", self._generate_report)

        # Define workflow transitions
        workflow.set_entry_point("collect_errors")
        workflow.add_edge("collect_errors", "initial_analysis")
        workflow.add_edge("initial_analysis", "assign_agents")

        # Conditional routing based on consensus
        workflow.add_conditional_edges(
            "assign_agents",
            self._route_based_on_consensus,
            {
                "debug": "parallel_debug",
                "correct": "parallel_correct",
                "recover": "orchestrate_recovery",
                "monitor": "monitor_results",
            },
        )

        # Parallel branches merge
        workflow.add_edge("parallel_debug", "parallel_correct")
        workflow.add_edge("parallel_correct", "parallel_test")
        workflow.add_edge("parallel_test", "orchestrate_recovery")
        workflow.add_edge("orchestrate_recovery", "monitor_results")
        workflow.add_edge("monitor_results", "learn_from_results")
        workflow.add_edge("learn_from_results", "generate_report")
        workflow.add_edge("generate_report", END)

        return workflow

    async def _collect_errors(
        self, state: ErrorHandlingWorkflowState
    ) -> ErrorHandlingWorkflowState:
        """Collect errors from multiple sources"""
        logger.info("Collecting errors from all sources")

        # In production, would collect from:
        # - Log aggregators
        # - Monitoring systems
        # - User reports
        # - Automated scanners

        state["phase"] = "collection"
        state["messages"].append(
            SystemMessage(content=f"Collected {len(state['errors'])} errors for processing")
        )

        return state

    async def _initial_analysis(
        self, state: ErrorHandlingWorkflowState
    ) -> ErrorHandlingWorkflowState:
        """Perform initial analysis on collected errors"""
        logger.info("Performing initial error analysis")

        # Use pattern analysis agent
        analyzer = self.coordinator.agents["pattern_analysis"]

        # Convert to ErrorState format
        error_states = [self._dict_to_error_state(e) for e in state["errors"]]

        # Analyze patterns
        analysis = await analyzer.analyze_error_patterns(error_states)

        state["phase"] = "analysis"
        state["metrics"]["pattern_analysis"] = analysis

        # Generate alerts for critical patterns
        if analysis.get("insights"):
            for insight in analysis["insights"][:3]:
                state["alerts"].append(
                    {
                        "type": "pattern_detected",
                        "severity": "high",
                        "description": insight.description,
                    }
                )

        return state

    async def _assign_agents_with_consensus(
        self, state: ErrorHandlingWorkflowState
    ) -> ErrorHandlingWorkflowState:
        """Assign agents using consensus mechanism"""
        logger.info("Assigning agents with consensus")

        # Get recommendations from multiple agents
        recommendations = {}

        for error in state["errors"][:5]:  # Process top priority errors
            agent_votes = {}

            # Each agent votes on whether they should handle this error
            for agent_name, agent in self.coordinator.agents.items():
                confidence = self._calculate_agent_confidence(agent_name, error)
                agent_votes[agent_name] = confidence

            # Select agent with highest confidence
            best_agent = max(agent_votes, key=agent_votes.get)

            if agent_votes[best_agent] >= 0.7:  # Consensus threshold
                recommendations[error["error_id"]] = best_agent
                state["agents"].append(best_agent)

        state["consensus"] = {
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat(),
        }

        state["phase"] = "assigned"

        return state

    def _calculate_agent_confidence(self, agent_name: str, error: dict[str, Any]) -> float:
        """Calculate agent's confidence in handling an error"""
        error_type = error.get("error_type", "unknown")

        confidence_map = {
            "correction": {
                "syntax_error": 0.9,
                "type_error": 0.8,
                "runtime_error": 0.7,
            },
            "debugging": {"runtime_error": 0.9, "memory_leak": 0.8, "deadlock": 0.9},
            "recovery": {"network_error": 0.9, "api_error": 0.8, "database_error": 0.7},
            "testing": {"logic_error": 0.8, "integration_error": 0.9},
        }

        return confidence_map.get(agent_name, {}).get(error_type, 0.5)

    async def _parallel_debug(
        self, state: ErrorHandlingWorkflowState
    ) -> ErrorHandlingWorkflowState:
        """Debug errors in parallel"""
        logger.info("Running parallel debugging")

        debugger = self.coordinator.agents["debugging"]

        # Create debugging tasks
        debug_tasks = []
        for error in state["errors"][:3]:  # Limit parallel tasks
            if state["consensus"]["recommendations"].get(error["error_id"]) == "debugging":
                error_state = self._dict_to_error_state(error)
                debug_tasks.append(debugger.debug_error(error_state))

        # Execute in parallel
        if debug_tasks:
            debug_results = await asyncio.gather(*debug_tasks, return_exceptions=True)

            for result in debug_results:
                if not isinstance(result, Exception):
                    state["decisions"].append({"type": "debug_info", "data": result.model_dump()})

        state["completed_tasks"].append("debugging")
        return state

    async def _parallel_correct(
        self, state: ErrorHandlingWorkflowState
    ) -> ErrorHandlingWorkflowState:
        """Apply corrections in parallel"""
        logger.info("Applying parallel corrections")

        corrector = self.coordinator.agents["correction"]

        # Create correction tasks
        correction_tasks = []
        for error in state["errors"][:5]:
            if state["consensus"]["recommendations"].get(error["error_id"]) == "correction":
                error_state = self._dict_to_error_state(error)
                correction_tasks.append(corrector.correct_error(error_state))

        # Execute in parallel
        if correction_tasks:
            correction_results = await asyncio.gather(*correction_tasks, return_exceptions=True)

            for result in correction_results:
                if not isinstance(result, Exception) and result.validation_passed:
                    state["fixes_applied"].append(
                        {
                            "fix_id": f"fix_{len(state['fixes_applied'])}",
                            "data": result.model_dump(),
                        }
                    )

        state["completed_tasks"].append("correction")
        return state

    async def _parallel_test(self, state: ErrorHandlingWorkflowState) -> ErrorHandlingWorkflowState:
        """Run tests in parallel"""
        logger.info("Running parallel tests")

        tester = self.coordinator.agents["testing"]

        # Test all affected components
        affected_components = set()
        for fix in state["fixes_applied"]:
            if "file_path" in fix["data"]:
                affected_components.add(fix["data"]["file_path"])

        if affected_components:
            test_report = await tester.orchestrate_testing(
                target=list(affected_components)[0] if len(affected_components) == 1 else None,
                test_type="unit",
            )

            state["tests_passed"] = test_report.passed == test_report.total_tests
            state["metrics"]["test_report"] = test_report.model_dump()

        state["completed_tasks"].append("testing")
        return state

    async def _orchestrate_recovery(
        self, state: ErrorHandlingWorkflowState
    ) -> ErrorHandlingWorkflowState:
        """Orchestrate system recovery"""
        logger.info("Orchestrating recovery")

        orchestrator = self.coordinator.agents["recovery"]

        # Apply recovery for critical errors
        recovery_needed = False
        for error in state["errors"]:
            if error.get("priority") in ["CRITICAL", "EMERGENCY"]:
                recovery_needed = True
                error_state = self._dict_to_error_state(error)
                recovery = await orchestrator.orchestrate_recovery(error_state)

                if recovery.success:
                    state["recovery_success"] = True
                    state["decisions"].append({"type": "recovery", "data": recovery.model_dump()})

        if not recovery_needed:
            state["recovery_success"] = True

        state["completed_tasks"].append("recovery")
        return state

    async def _monitor_results(
        self, state: ErrorHandlingWorkflowState
    ) -> ErrorHandlingWorkflowState:
        """Monitor results and system health"""
        logger.info("Monitoring results")

        # Collect metrics from all agents
        for agent_name, agent in self.coordinator.agents.items():
            if hasattr(agent, "get_error_metrics"):
                metrics = await agent.get_error_metrics()
                state["metrics"][f"{agent_name}_metrics"] = metrics

        # Check system health
        health_score = self._calculate_health_score(state)
        state["metrics"]["health_score"] = health_score

        if health_score < 0.5:
            state["alerts"].append(
                {
                    "type": "low_health",
                    "severity": "critical",
                    "description": f"System health score: {health_score:.2f}",
                }
            )

        state["completed_tasks"].append("monitoring")
        return state

    async def _learn_from_results(
        self, state: ErrorHandlingWorkflowState
    ) -> ErrorHandlingWorkflowState:
        """Learn from the results for future improvements"""
        logger.info("Learning from results")

        # Update pattern database
        self.coordinator.agents["pattern_analysis"]

        # Learn from successful fixes
        for fix in state["fixes_applied"]:
            # Update patterns with successful fixes
            pass  # Implementation would update ML models

        # Update agent performance metrics
        for agent_name in state["agents"]:
            # Track agent performance
            pass  # Implementation would update agent scores

        state["phase"] = "learned"
        return state

    def _generate_report(self, state: ErrorHandlingWorkflowState) -> ErrorHandlingWorkflowState:
        """Generate final report"""
        logger.info("Generating final report")

        report = {
            "workflow_id": f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "errors_processed": len(state["errors"]),
            "fixes_applied": len(state["fixes_applied"]),
            "tests_passed": state["tests_passed"],
            "recovery_success": state["recovery_success"],
            "health_score": state["metrics"].get("health_score", 0),
            "alerts_generated": len(state["alerts"]),
            "agents_used": list(set(state["agents"])),
            "recommendations": self._generate_recommendations(state),
        }

        state["metrics"]["final_report"] = report
        state["phase"] = "completed"

        state["messages"].append(
            AIMessage(
                content=f"Workflow completed. Processed {report['errors_processed']} errors, "
                f"applied {report['fixes_applied']} fixes."
            )
        )

        return state

    def _route_based_on_consensus(self, state: ErrorHandlingWorkflowState) -> str:
        """Route based on consensus decision"""
        if not state["consensus"]["recommendations"]:
            return "monitor"

        # Get most common recommendation
        agent_counts = {}
        for agent in state["consensus"]["recommendations"].values():
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

        most_common = max(agent_counts, key=agent_counts.get)

        routing_map = {
            "debugging": "debug",
            "correction": "correct",
            "recovery": "recover",
        }

        return routing_map.get(most_common, "monitor")

    def _dict_to_error_state(self, error_dict: dict[str, Any]) -> Any:
        """Convert dictionary to ErrorState (simplified)"""
        # In production, would properly convert to ErrorState
        return error_dict

    def _calculate_health_score(self, state: ErrorHandlingWorkflowState) -> float:
        """Calculate overall system health score"""
        score = 1.0

        # Deduct for unprocessed errors
        unprocessed = len(state["errors"]) - len(state["fixes_applied"])
        score -= (unprocessed / len(state["errors"])) * 0.3 if state["errors"] else 0

        # Deduct for failed tests
        if not state["tests_passed"]:
            score -= 0.2

        # Deduct for recovery failures
        if not state["recovery_success"]:
            score -= 0.3

        # Deduct for alerts
        score -= len(state["alerts"]) * 0.05

        return max(0, min(1, score))

    def _generate_recommendations(self, state: ErrorHandlingWorkflowState) -> list[str]:
        """Generate recommendations based on workflow results"""
        recommendations = []

        if not state["tests_passed"]:
            recommendations.append("Fix failing tests before deployment")

        if state["metrics"].get("pattern_analysis", {}).get("predictions"):
            recommendations.append("Review predicted errors and implement preventive measures")

        if len(state["alerts"]) > 5:
            recommendations.append("Investigate high alert volume")

        health_score = state["metrics"].get("health_score", 1)
        if health_score < 0.7:
            recommendations.append("System health is low - consider manual intervention")

        return recommendations

    async def execute(
        self, errors: list[dict[str, Any]], context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Execute the complete workflow"""
        initial_state: ErrorHandlingWorkflowState = {
            "errors": errors,
            "agents": [],
            "decisions": [],
            "consensus": {},
            "phase": "initiated",
            "parallel_tasks": [],
            "completed_tasks": [],
            "fixes_applied": [],
            "tests_passed": False,
            "recovery_success": False,
            "metrics": {},
            "alerts": [],
            "messages": [HumanMessage(content=f"Processing {len(errors)} errors")],
        }

        app = self.workflow.compile(checkpointer=self.memory)
        config = {
            "configurable": {"thread_id": f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}
        }

        final_state = await app.ainvoke(initial_state, config)

        return final_state["metrics"].get("final_report", {})
