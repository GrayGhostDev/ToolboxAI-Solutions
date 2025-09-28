"""
GitHub Agent Orchestrator using LangGraph for workflow management.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langgraph.graph import END, StateGraph

from .deployment_prep_agent import DeploymentPrepAgent
from .git_lfs_migration_agent import GitLFSMigrationAgent
from .large_file_detection_agent import LargeFileDetectionAgent
from .repo_health_monitor_agent import RepoHealthMonitorAgent

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of operations the orchestrator can handle."""
    PRE_COMMIT = "pre_commit"
    PRE_PUSH = "pre_push"
    HEALTH_CHECK = "health_check"
    OPTIMIZATION = "optimization"
    DEPLOYMENT = "deployment"
    FULL_SCAN = "full_scan"


class GitHubAgentState(TypedDict):
    """State schema for GitHub agent workflow."""
    operation_type: Literal["pre_commit", "pre_push", "health_check", "optimization", "deployment", "full_scan"]
    files_to_process: List[str]
    large_files_detected: List[Dict[str, Any]]
    lfs_migrations: List[Dict[str, Any]]
    optimizations_applied: List[Dict[str, Any]]
    health_status: Dict[str, Any]
    deployment_readiness: Dict[str, Any]
    errors: List[str]
    recommendations: List[str]
    current_agent: str
    timestamp: str
    auto_fix: bool


class GitHubAgentOrchestrator:
    """Orchestrates GitHub agents using LangGraph."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the orchestrator.

        Args:
            config_path: Path to configuration file
        """
        self.agents = {
            'detection': LargeFileDetectionAgent(config_path),
            'lfs_migration': GitLFSMigrationAgent(config_path),
            'health_monitor': RepoHealthMonitorAgent(config_path),
            'deployment_prep': DeploymentPrepAgent(config_path) if DeploymentPrepAgent else None
        }

        self.workflow = StateGraph(GitHubAgentState)
        self._setup_workflow()
        self.app = self.workflow.compile()

    def _setup_workflow(self):
        """Set up the workflow graph."""
        # Add nodes
        self.workflow.add_node("coordinator", self.coordinator_node)
        self.workflow.add_node("detection_agent", self.detection_node)
        self.workflow.add_node("lfs_migration_agent", self.lfs_migration_node)
        self.workflow.add_node("health_monitor_agent", self.health_monitor_node)

        if self.agents.get('deployment_prep'):
            self.workflow.add_node("deployment_prep_agent", self.deployment_prep_node)

        # Set entry point
        self.workflow.set_entry_point("coordinator")

        # Add conditional edges from coordinator
        self.workflow.add_conditional_edges(
            "coordinator",
            self.route_coordinator,
            {
                "detection": "detection_agent",
                "lfs_migration": "lfs_migration_agent",
                "health_check": "health_monitor_agent",
                "deployment_prep": "deployment_prep_agent",
                "complete": END
            }
        )

        # Agent nodes return to coordinator
        for agent in ["detection_agent", "lfs_migration_agent", "health_monitor_agent"]:
            self.workflow.add_edge(agent, "coordinator")

        if self.agents.get('deployment_prep'):
            self.workflow.add_edge("deployment_prep_agent", "coordinator")

    async def coordinator_node(self, state: GitHubAgentState) -> GitHubAgentState:
        """Coordinator node that manages the workflow.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info(f"Coordinator: Processing {state['operation_type']} operation")
        state["current_agent"] = "coordinator"

        # Initialize timestamp if not set
        if not state.get("timestamp"):
            state["timestamp"] = datetime.now().isoformat()

        return state

    async def detection_node(self, state: GitHubAgentState) -> GitHubAgentState:
        """Large file detection node.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Running large file detection agent")
        state["current_agent"] = "detection"

        try:
            result = await self.agents['detection'].analyze()

            if result["success"]:
                state["large_files_detected"] = result.get("large_files", [])

                # Add recommendations
                if result.get("recommendations"):
                    state["recommendations"].extend(result["recommendations"])

                # Check for blockers
                blockers = [f for f in result["large_files"] if f["severity"] == "blocker"]
                if blockers:
                    state["errors"].append(
                        f"Found {len(blockers)} file(s) exceeding GitHub's 100MB limit"
                    )
            else:
                state["errors"].append(f"Detection failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"Error in detection node: {e}")
            state["errors"].append(f"Detection error: {str(e)}")

        return state

    async def lfs_migration_node(self, state: GitHubAgentState) -> GitHubAgentState:
        """Git LFS migration node.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Running Git LFS migration agent")
        state["current_agent"] = "lfs_migration"

        if not state.get("large_files_detected"):
            return state

        if not state.get("auto_fix", False):
            state["recommendations"].append(
                "Large files detected. Run with --auto-fix to migrate to Git LFS"
            )
            return state

        try:
            # Setup LFS if needed
            lfs_status = await self.agents['lfs_migration'].analyze()
            if not lfs_status["lfs_initialized"]:
                setup_result = await self.agents['lfs_migration'].setup_lfs()
                if not setup_result["success"]:
                    state["errors"].append("Failed to setup Git LFS")
                    return state

            # Migrate large files
            migrations = []
            for file_info in state["large_files_detected"][:10]:  # Limit to 10 files
                if file_info["severity"] in ["critical", "blocker"]:
                    migration_result = await self.agents['lfs_migration'].migrate_file_to_lfs(
                        file_info["path"]
                    )
                    migrations.append({
                        "file": file_info["path"],
                        "success": migration_result["success"],
                        "actions": migration_result.get("actions", [])
                    })

            state["lfs_migrations"] = migrations

        except Exception as e:
            logger.error(f"Error in LFS migration node: {e}")
            state["errors"].append(f"LFS migration error: {str(e)}")

        return state

    async def health_monitor_node(self, state: GitHubAgentState) -> GitHubAgentState:
        """Repository health monitoring node.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Running repository health monitor agent")
        state["current_agent"] = "health_monitor"

        try:
            health_result = await self.agents['health_monitor'].analyze()

            state["health_status"] = {
                "overall_status": health_result.get("overall_status", "unknown"),
                "metrics": health_result.get("metrics", {}),
                "issues": health_result.get("issues", [])
            }

            # Add health recommendations
            if health_result.get("recommendations"):
                state["recommendations"].extend(health_result["recommendations"])

            # Add critical issues to errors
            if health_result.get("overall_status") == "critical":
                state["errors"].append("Repository health is critical")

        except Exception as e:
            logger.error(f"Error in health monitor node: {e}")
            state["errors"].append(f"Health check error: {str(e)}")

        return state

    async def deployment_prep_node(self, state: GitHubAgentState) -> GitHubAgentState:
        """Deployment preparation node.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Running deployment preparation agent")
        state["current_agent"] = "deployment_prep"

        if self.agents.get('deployment_prep'):
            try:
                result = await self.agents['deployment_prep'].analyze()
                state["deployment_readiness"] = result

                if not result.get("ready", False):
                    state["errors"].append("Repository not ready for deployment")
                    if result.get("issues"):
                        for issue in result["issues"]:
                            state["recommendations"].append(f"Fix: {issue}")

            except Exception as e:
                logger.error(f"Error in deployment prep node: {e}")
                state["errors"].append(f"Deployment prep error: {str(e)}")

        return state

    def route_coordinator(self, state: GitHubAgentState) -> str:
        """Route to appropriate agent based on operation and state.

        Args:
            state: Current workflow state

        Returns:
            Next node to execute
        """
        operation = state.get("operation_type")

        # Pre-commit and pre-push checks
        if operation in ["pre_commit", "pre_push"]:
            if not state.get("large_files_detected"):
                return "detection"
            elif state.get("large_files_detected") and state.get("auto_fix") and not state.get("lfs_migrations"):
                return "lfs_migration"
            else:
                return "complete"

        # Health check
        elif operation == "health_check":
            if not state.get("health_status"):
                return "health_check"
            else:
                return "complete"

        # Deployment preparation
        elif operation == "deployment":
            if not state.get("health_status"):
                return "health_check"
            elif not state.get("deployment_readiness") and self.agents.get('deployment_prep'):
                return "deployment_prep"
            else:
                return "complete"

        # Full scan
        elif operation == "full_scan":
            if not state.get("large_files_detected"):
                return "detection"
            elif not state.get("health_status"):
                return "health_check"
            else:
                return "complete"

        return "complete"

    async def run(
        self,
        operation: OperationType,
        auto_fix: bool = False,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run the orchestrator workflow.

        Args:
            operation: Type of operation to perform
            auto_fix: Whether to automatically fix issues
            files: Specific files to process

        Returns:
            Workflow results
        """
        initial_state: GitHubAgentState = {
            "operation_type": operation.value,
            "files_to_process": files or [],
            "large_files_detected": [],
            "lfs_migrations": [],
            "optimizations_applied": [],
            "health_status": {},
            "deployment_readiness": {},
            "errors": [],
            "recommendations": [],
            "current_agent": "coordinator",
            "timestamp": datetime.now().isoformat(),
            "auto_fix": auto_fix
        }

        try:
            # Run the workflow
            final_state = await self.app.ainvoke(initial_state)

            # Generate summary
            summary = self._generate_summary(final_state)

            return {
                "success": len(final_state["errors"]) == 0,
                "operation": operation.value,
                "summary": summary,
                "state": final_state
            }

        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            return {
                "success": False,
                "operation": operation.value,
                "error": str(e),
                "state": initial_state
            }

    def _generate_summary(self, state: GitHubAgentState) -> Dict[str, Any]:
        """Generate a summary of the workflow execution.

        Args:
            state: Final workflow state

        Returns:
            Summary dictionary
        """
        summary = {
            "timestamp": state["timestamp"],
            "operation": state["operation_type"],
            "success": len(state["errors"]) == 0,
            "large_files_found": len(state["large_files_detected"]),
            "files_migrated": len(state["lfs_migrations"]),
            "errors": state["errors"],
            "recommendations": state["recommendations"]
        }

        if state.get("health_status"):
            summary["health_status"] = state["health_status"].get("overall_status", "unknown")

        if state.get("deployment_readiness"):
            summary["deployment_ready"] = state["deployment_readiness"].get("ready", False)

        return summary