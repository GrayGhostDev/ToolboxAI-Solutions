"""
Error Handling Swarm Coordinator

Central orchestrator for the error handling agent swarm using LangGraph workflows
for intelligent agent coordination and task distribution.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, TypedDict, Annotated, Sequence
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from pydantic import BaseModel, Field

# Import MemorySaver with correct path
from langgraph.checkpoint.memory import MemorySaver

# Import all specialized agents
from core.agents.error_handling.base_error_agent import ErrorState, ErrorType, ErrorPriority
from core.agents.error_handling.error_correction_agent import ErrorCorrectionAgent
from core.agents.error_handling.debugging_agent import AdvancedDebuggingAgent
# Note: These imports are now integrated into the unified orchestration system
# from core.agents.error_handling.testing_orchestrator_agent import TestingOrchestratorAgent
# from core.agents.error_handling.auto_recovery_orchestrator_agent import AutoRecoveryOrchestratorAgent

from core.agents.error_handling.error_pattern_analysis_agent import ErrorPatternAnalysisAgent
from core.agents.error_handling.error_aggregation_intelligence_agent import ErrorAggregationIntelligenceAgent

# Use the new orchestration system for testing and recovery
try:
    from ...orchestration.error_handling import ErrorHandlingOrchestrationModule
except ImportError:
    ErrorHandlingOrchestrationModule = None

logger = logging.getLogger(__name__)


class SwarmState(TypedDict):
    """Shared state for the error handling swarm"""
    current_errors: List[ErrorState]
    processed_errors: List[ErrorState]
    active_agents: List[str]
    priority_queue: List[Dict[str, Any]]
    recovery_attempts: Dict[str, Any]
    system_health: Dict[str, Any]
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    messages: Sequence[BaseMessage]
    next_action: str
    workflow_status: str


class SwarmAction(Enum):
    """Actions the swarm can take"""
    AGGREGATE = "aggregate"
    ANALYZE_PATTERN = "analyze_pattern"
    DEBUG = "debug"
    CORRECT = "correct"
    TEST = "test"
    RECOVER = "recover"
    MONITOR = "monitor"
    COMPLETE = "complete"


class WorkflowResult(BaseModel):
    """Result of a workflow execution"""
    workflow_id: str = Field(description="Unique workflow identifier")
    status: str = Field(description="Workflow status")
    errors_processed: int = Field(description="Number of errors processed")
    agents_involved: List[str] = Field(description="Agents that participated")
    actions_taken: List[str] = Field(description="Actions executed")
    success_rate: float = Field(description="Success rate of actions")
    duration_seconds: float = Field(description="Total execution time")
    recommendations: List[str] = Field(description="Recommendations for future")


@dataclass
class SwarmConfig:
    """Configuration for swarm coordinator"""
    name: str = "ErrorHandlingSwarmCoordinator"
    max_parallel_agents: int = 5
    workflow_timeout: int = 600  # seconds
    enable_learning: bool = True
    consensus_threshold: float = 0.7
    auto_scale_agents: bool = True


class ErrorHandlingSwarmCoordinator:
    """
    Central coordinator for the error handling agent swarm.

    Orchestrates multiple specialized agents using LangGraph workflows
    for comprehensive error handling, debugging, testing, and recovery.
    """

    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()

        # Initialize all specialized agents
        self.agents = {
            "aggregation": ErrorAggregationIntelligenceAgent(),
            "pattern_analysis": ErrorPatternAnalysisAgent(),
            "debugging": AdvancedDebuggingAgent(),
            "correction": ErrorCorrectionAgent(),
            "testing": TestingOrchestratorAgent(),
            "recovery": AutoRecoveryOrchestratorAgent()
        }

        # Workflow state
        self.workflow_graph = self._build_workflow_graph()
        self.memory = MemorySaver()
        self.active_workflows: Dict[str, WorkflowResult] = {}

        logger.info("Initialized Error Handling Swarm Coordinator")

    def _build_workflow_graph(self) -> StateGraph:
        """Build the LangGraph workflow for error handling"""
        workflow = StateGraph(SwarmState)

        # Add nodes for each major step
        workflow.add_node("aggregate", self._aggregate_errors)
        workflow.add_node("analyze_patterns", self._analyze_patterns)
        workflow.add_node("route_errors", self._route_errors)
        workflow.add_node("debug_errors", self._debug_errors)
        workflow.add_node("correct_errors", self._correct_errors)
        workflow.add_node("test_fixes", self._test_fixes)
        workflow.add_node("recover_system", self._recover_system)
        workflow.add_node("monitor_health", self._monitor_health)
        workflow.add_node("complete", self._complete_workflow)

        # Define edges (workflow transitions)
        workflow.add_edge("aggregate", "analyze_patterns")
        workflow.add_edge("analyze_patterns", "route_errors")

        # Conditional routing based on error priority
        workflow.add_conditional_edges(
            "route_errors",
            self._determine_next_action,
            {
                SwarmAction.DEBUG.value: "debug_errors",
                SwarmAction.CORRECT.value: "correct_errors",
                SwarmAction.RECOVER.value: "recover_system",
                SwarmAction.MONITOR.value: "monitor_health",
                SwarmAction.COMPLETE.value: "complete"
            }
        )

        # After specific actions, decide next step
        workflow.add_conditional_edges(
            "debug_errors",
            self._post_debug_routing,
            {
                SwarmAction.CORRECT.value: "correct_errors",
                SwarmAction.RECOVER.value: "recover_system",
                SwarmAction.COMPLETE.value: "complete"
            }
        )

        workflow.add_conditional_edges(
            "correct_errors",
            self._post_correction_routing,
            {
                SwarmAction.TEST.value: "test_fixes",
                SwarmAction.RECOVER.value: "recover_system",
                SwarmAction.COMPLETE.value: "complete"
            }
        )

        workflow.add_edge("test_fixes", "monitor_health")
        workflow.add_edge("recover_system", "monitor_health")
        workflow.add_edge("monitor_health", "complete")

        # Set entry point
        workflow.set_entry_point("aggregate")

        return workflow

    async def orchestrate_error_handling(
        self,
        errors: List[ErrorState],
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Main orchestration method for handling errors.

        Args:
            errors: List of errors to process
            context: Optional context for processing

        Returns:
            WorkflowResult with processing outcome
        """
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()

        logger.info(f"Starting error handling workflow: {workflow_id}")

        # Initialize state
        initial_state: SwarmState = {
            "current_errors": errors,
            "processed_errors": [],
            "active_agents": [],
            "priority_queue": [],
            "recovery_attempts": {},
            "system_health": {},
            "context": context or {},
            "metadata": {"workflow_id": workflow_id},
            "messages": [HumanMessage(content=f"Processing {len(errors)} errors")],
            "next_action": SwarmAction.AGGREGATE.value,
            "workflow_status": "initiated"
        }

        # Execute workflow
        try:
            app = self.workflow_graph.compile(checkpointer=self.memory)

            # Run the workflow
            config = {"configurable": {"thread_id": workflow_id}}
            final_state = await app.ainvoke(initial_state, config)

            # Calculate metrics
            duration = (datetime.now() - start_time).total_seconds()
            success_rate = self._calculate_success_rate(final_state)

            # Create result
            result = WorkflowResult(
                workflow_id=workflow_id,
                status="completed",
                errors_processed=len(final_state["processed_errors"]),
                agents_involved=final_state["active_agents"],
                actions_taken=self._extract_actions(final_state),
                success_rate=success_rate,
                duration_seconds=duration,
                recommendations=self._generate_recommendations(final_state)
            )

            self.active_workflows[workflow_id] = result
            return result

        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            return WorkflowResult(
                workflow_id=workflow_id,
                status="failed",
                errors_processed=0,
                agents_involved=[],
                actions_taken=[],
                success_rate=0.0,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                recommendations=["Investigate workflow failure"]
            )

    async def _aggregate_errors(self, state: SwarmState) -> SwarmState:
        """Aggregate errors using the aggregation agent"""
        logger.info("Aggregating errors")

        aggregator = self.agents["aggregation"]
        aggregation_result = await aggregator.aggregate_errors(
            state["current_errors"],
            source="swarm_coordinator"
        )

        state["priority_queue"] = self._build_priority_queue(aggregation_result)
        state["active_agents"].append("aggregation")
        state["workflow_status"] = "aggregated"

        return state

    async def _analyze_patterns(self, state: SwarmState) -> SwarmState:
        """Analyze error patterns"""
        logger.info("Analyzing error patterns")

        analyzer = self.agents["pattern_analysis"]
        analysis_result = await analyzer.analyze_error_patterns(
            state["current_errors"],
            timeframe_days=7
        )

        state["context"]["pattern_analysis"] = analysis_result
        state["active_agents"].append("pattern_analysis")
        state["workflow_status"] = "patterns_analyzed"

        # Add predictions to context
        if analysis_result.get("predictions"):
            state["context"]["predictions"] = analysis_result["predictions"]

        return state

    def _route_errors(self, state: SwarmState) -> SwarmState:
        """Route errors to appropriate agents"""
        logger.info("Routing errors to specialized agents")

        # Group errors by type for efficient routing
        error_groups = {}
        for error in state["current_errors"]:
            error_type = error["error_type"]
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(error)

        state["context"]["error_groups"] = error_groups
        state["workflow_status"] = "routed"

        return state

    def _determine_next_action(self, state: SwarmState) -> str:
        """Determine next action based on error priority"""
        if not state["current_errors"]:
            return SwarmAction.COMPLETE.value

        # Check highest priority error
        priorities = [e["priority"] for e in state["current_errors"]]

        if ErrorPriority.EMERGENCY in priorities or ErrorPriority.CRITICAL in priorities:
            return SwarmAction.RECOVER.value
        elif ErrorPriority.HIGH in priorities:
            return SwarmAction.DEBUG.value
        else:
            return SwarmAction.CORRECT.value

    async def _debug_errors(self, state: SwarmState) -> SwarmState:
        """Debug errors using debugging agent"""
        logger.info("Debugging high-priority errors")

        debugger = self.agents["debugging"]

        # Debug critical errors
        for error in state["current_errors"][:5]:  # Limit to 5 for performance
            if error["priority"] in [ErrorPriority.CRITICAL, ErrorPriority.HIGH]:
                debug_info = await debugger.debug_error(error)
                error["debug_info"] = debug_info.model_dump()

        state["active_agents"].append("debugging")
        state["workflow_status"] = "debugged"

        return state

    async def _correct_errors(self, state: SwarmState) -> SwarmState:
        """Correct errors using correction agent"""
        logger.info("Applying error corrections")

        corrector = self.agents["correction"]

        corrections_applied = []
        for error in state["current_errors"][:10]:  # Limit corrections
            fix = await corrector.correct_error(error)
            if fix.validation_passed:
                corrections_applied.append({
                    "error_id": error["error_id"],
                    "fix": fix.model_dump()
                })
                state["processed_errors"].append(error)

        state["context"]["corrections"] = corrections_applied
        state["active_agents"].append("correction")
        state["workflow_status"] = "corrected"

        return state

    async def _test_fixes(self, state: SwarmState) -> SwarmState:
        """Test applied fixes"""
        logger.info("Testing applied fixes")

        tester = self.agents["testing"]

        # Run tests for corrected components
        affected_components = set()
        for error in state["processed_errors"]:
            affected_components.update(error.get("affected_components", []))

        if affected_components:
            test_report = await tester.orchestrate_testing(
                target=list(affected_components)[0] if affected_components else None,
                test_type="unit"
            )
            state["context"]["test_report"] = test_report.model_dump()

        state["active_agents"].append("testing")
        state["workflow_status"] = "tested"

        return state

    async def _recover_system(self, state: SwarmState) -> SwarmState:
        """Recover system using recovery orchestrator"""
        logger.info("Orchestrating system recovery")

        orchestrator = self.agents["recovery"]

        # Apply recovery for critical errors
        for error in state["current_errors"]:
            if error["priority"] in [ErrorPriority.EMERGENCY, ErrorPriority.CRITICAL]:
                recovery = await orchestrator.orchestrate_recovery(error)
                state["recovery_attempts"][error["error_id"]] = recovery.model_dump()

        state["active_agents"].append("recovery")
        state["workflow_status"] = "recovered"

        return state

    async def _monitor_health(self, state: SwarmState) -> SwarmState:
        """Monitor system health after interventions"""
        logger.info("Monitoring system health")

        # Collect health metrics from all agents
        health_metrics = {}
        for agent_name, agent in self.agents.items():
            if hasattr(agent, 'get_error_metrics'):
                metrics = await agent.get_error_metrics()
                health_metrics[agent_name] = metrics

        state["system_health"] = health_metrics
        state["workflow_status"] = "monitored"

        return state

    def _complete_workflow(self, state: SwarmState) -> SwarmState:
        """Complete the workflow"""
        logger.info("Completing workflow")

        state["workflow_status"] = "completed"
        state["messages"].append(
            AIMessage(content=f"Processed {len(state['processed_errors'])} errors successfully")
        )

        return state

    def _post_debug_routing(self, state: SwarmState) -> str:
        """Routing after debugging"""
        if state.get("context", {}).get("debug_info"):
            return SwarmAction.CORRECT.value
        return SwarmAction.COMPLETE.value

    def _post_correction_routing(self, state: SwarmState) -> str:
        """Routing after correction"""
        if state.get("context", {}).get("corrections"):
            return SwarmAction.TEST.value
        return SwarmAction.COMPLETE.value

    def _build_priority_queue(self, aggregation_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build priority queue from aggregation results"""
        queue = []
        for group_id in aggregation_result.get("aggregated_groups", []):
            queue.append({
                "group_id": group_id,
                "priority": aggregation_result.get("queue_assignments", {}).get(group_id)
            })
        return sorted(queue, key=lambda x: x.get("priority", 0), reverse=True)

    def _calculate_success_rate(self, state: SwarmState) -> float:
        """Calculate success rate of the workflow"""
        if not state["current_errors"]:
            return 1.0

        processed = len(state["processed_errors"])
        total = len(state["current_errors"])

        return processed / total if total > 0 else 0.0

    def _extract_actions(self, state: SwarmState) -> List[str]:
        """Extract actions taken during workflow"""
        actions = []

        if "aggregation" in state["active_agents"]:
            actions.append("Aggregated errors")
        if "pattern_analysis" in state["active_agents"]:
            actions.append("Analyzed patterns")
        if "debugging" in state["active_agents"]:
            actions.append("Debugged critical errors")
        if "correction" in state["active_agents"]:
            actions.append("Applied corrections")
        if "testing" in state["active_agents"]:
            actions.append("Tested fixes")
        if "recovery" in state["active_agents"]:
            actions.append("Executed recovery")

        return actions

    def _generate_recommendations(self, state: SwarmState) -> List[str]:
        """Generate recommendations based on workflow results"""
        recommendations = []

        # Based on pattern analysis
        if state.get("context", {}).get("pattern_analysis", {}).get("insights"):
            recommendations.append("Review pattern insights for preventive measures")

        # Based on test results
        if state.get("context", {}).get("test_report", {}).get("failed", 0) > 0:
            recommendations.append("Fix failing tests before deployment")

        # Based on recovery attempts
        if state.get("recovery_attempts"):
            recommendations.append("Monitor recovered services closely")

        # Based on predictions
        if state.get("context", {}).get("predictions"):
            recommendations.append("Implement preventive measures for predicted errors")

        return recommendations

    async def get_swarm_status(self) -> Dict[str, Any]:
        """Get current status of the swarm"""
        status = {
            "active_workflows": len(self.active_workflows),
            "available_agents": list(self.agents.keys()),
            "agent_status": {}
        }

        for agent_name, agent in self.agents.items():
            status["agent_status"][agent_name] = "active"

        return status