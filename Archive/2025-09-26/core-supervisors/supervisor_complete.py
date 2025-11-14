"""
Complete Supervisor Agent Implementation with Full Workflow Graph

This module provides a complete implementation of the supervisor agent with proper
LangGraph workflow, agent initialization, and task delegation.

Author: ToolboxAI Team
Created: 2025-09-17
Version: 2.0.0
"""

import asyncio
import json
import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph

from .base_agent import (
    AgentConfig,
    AgentPriority,
    AgentState,
    BaseAgent,
    TaskResult,
)

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks the supervisor can handle"""
    CONTENT_GENERATION = "content_generation"
    QUIZ_CREATION = "quiz_creation"
    TERRAIN_BUILDING = "terrain_building"
    SCRIPT_DEVELOPMENT = "script_development"
    REVIEW_OPTIMIZATION = "review_optimization"
    COMPLEX_WORKFLOW = "complex_workflow"
    TESTING_VALIDATION = "testing_validation"
    DATABASE_OPERATION = "database_operation"
    EDUCATIONAL_ASSESSMENT = "educational_assessment"


class DelegationStrategy(Enum):
    """Strategy for task delegation"""
    SINGLE = "single"  # Single agent
    PARALLEL = "parallel"  # Multiple agents in parallel
    SEQUENTIAL = "sequential"  # Multiple agents in sequence
    HIERARCHICAL = "hierarchical"  # Nested delegation
    ADAPTIVE = "adaptive"  # Dynamic based on load


class SupervisorDecision(Enum):
    """Supervisor routing decisions"""
    DELEGATE_CONTENT = "delegate_content"
    DELEGATE_QUIZ = "delegate_quiz"
    DELEGATE_TERRAIN = "delegate_terrain"
    DELEGATE_SCRIPT = "delegate_script"
    DELEGATE_REVIEW = "delegate_review"
    DELEGATE_TESTING = "delegate_testing"
    DELEGATE_DATABASE = "delegate_database"
    PARALLEL_EXECUTION = "parallel_execution"
    SEQUENTIAL_EXECUTION = "sequential_execution"
    DIRECT_RESPONSE = "direct_response"
    ESCALATE = "escalate"
    RETRY = "retry"


@dataclass
class DelegationTask:
    """Represents a task to be delegated to an agent"""
    task_id: str
    agent_type: str
    task_description: str
    context: dict[str, Any]
    priority: AgentPriority = AgentPriority.MEDIUM
    dependencies: list[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300  # seconds
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[TaskResult] = None
    error: Optional[str] = None


@dataclass
class WorkflowState:
    """Enhanced state for workflow execution"""
    messages: list[BaseMessage]
    task: str
    context: dict[str, Any]
    metadata: dict[str, Any]
    delegations: list[DelegationTask]
    results: list[dict[str, Any]]
    errors: list[str]
    current_phase: str
    decision: Optional[SupervisorDecision]
    final_result: Optional[Any]
    workflow_id: str
    created_at: datetime
    updated_at: datetime


class CompleteSupervisorAgent(BaseAgent):
    """
    Complete implementation of Supervisor Agent with full orchestration capabilities.

    This agent manages and coordinates all specialized agents to handle complex
    educational content generation tasks for Roblox environments.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Complete Supervisor Agent"""
        # Set LangSmith environment variables if present
        import os
        if os.getenv("LANGCHAIN_WORKSPACE_ID"):
            os.environ["LANGSMITH_WORKSPACE_ID"] = os.getenv("LANGCHAIN_WORKSPACE_ID")
        if os.getenv("LANGSMITH_API_KEY") and not os.getenv("LANGCHAIN_API_KEY"):
            os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

        if config is None:
            config = AgentConfig(
                name="CompleteSupervisorAgent",
                model="gpt-3.5-turbo",
                temperature=0.3,
                max_tokens=4096,
                system_prompt=self._get_enhanced_supervisor_prompt(),
                verbose=True
            )
        super().__init__(config)

        # Initialize managed agents dictionary
        self.managed_agents: dict[str, BaseAgent] = {}

        # Load balancing - Initialize BEFORE calling _initialize_all_agents()
        self.agent_load: dict[str, int] = {}

        # Performance tracking
        self.agent_performance: dict[str, dict[str, Any]] = {}
        self.task_history: list[DelegationTask] = []

        # Initialize all agents at startup
        self._initialize_all_agents()

        # Workflow components
        self.workflow_graph: Optional[CompiledGraph] = None
        self.active_workflows: dict[str, WorkflowState] = {}

        # Build the workflow graph
        self._build_complete_workflow_graph()

        logger.info(f"Initialized Complete Supervisor with {len(self.managed_agents)} agents")

    def _get_enhanced_supervisor_prompt(self) -> str:
        """Get enhanced system prompt for the supervisor"""
        return """You are the Master Supervisor Agent orchestrating a team of specialized AI agents for creating educational Roblox environments.

Your team of specialized agents:

1. **ContentAgent** - Educational content generation
   - Curriculum alignment (Common Core, NGSS, state standards)
   - Age-appropriate content creation
   - Learning objective mapping
   - Educational narrative development

2. **QuizAgent** - Assessment and quiz creation
   - Multiple choice, true/false, fill-in-blank questions
   - Adaptive difficulty adjustment
   - Immediate feedback generation
   - Progress tracking integration

3. **TerrainAgent** - 3D environment and terrain generation
   - Terrain generation (mountains, valleys, plains)
   - Biome creation (forest, desert, ocean)
   - Educational landmark placement
   - Performance-optimized terrain

4. **ScriptAgent** - Lua script development
   - Roblox Lua script generation
   - Performance optimization
   - Security validation
   - Remote event handling

5. **ReviewAgent** - Code review and optimization
   - Code quality assessment
   - Performance optimization
   - Security vulnerability detection
   - Best practices enforcement

6. **TestingAgent** - Automated testing and validation
   - Unit and integration testing
   - Performance testing
   - Security testing
   - Compatibility testing

7. **DatabaseAgent** - Data persistence and management
   - User progress tracking
   - Content storage
   - Analytics data management
   - Backup and recovery

Your responsibilities:
- Analyze incoming tasks to understand requirements
- Determine optimal agent allocation and strategy
- Coordinate multi-agent workflows
- Monitor execution and handle failures
- Aggregate and synthesize results
- Ensure quality and completeness

Decision-making criteria:
- Task complexity and requirements
- Agent availability and load
- Dependencies between subtasks
- Priority and deadlines
- Resource constraints

Always provide structured, actionable decisions with clear rationale."""

    def _initialize_all_agents(self):
        """Initialize all managed agents at startup"""
        try:
            # Import all agent classes
            from .content_agent import ContentAgent

            # Import database agents
            from .database.supervisor_agent import DatabaseSupervisorAgent
            from .educational.adaptive_learning_agent import AdaptiveLearningAgent
            from .educational.assessment_design_agent import AssessmentDesignAgent

            # Import educational agents
            from .educational.curriculum_alignment_agent import CurriculumAlignmentAgent
            from .educational.educational_validation_agent import (
                EducationalValidationAgent,
            )
            from .educational.learning_analytics_agent import LearningAnalyticsAgent
            from .quiz_agent import QuizAgent
            from .review_agent import ReviewAgent
            from .script_agent import ScriptAgent
            from .terrain_agent import TerrainAgent
            from .testing_agent import TestingAgent

            # Create agent instances with proper configuration
            # Note: Some educational agents don't accept config parameters
            agents_with_config = [
                ("content", ContentAgent, {"temperature": 0.7}),
                ("quiz", QuizAgent, {"temperature": 0.5}),
                ("terrain", TerrainAgent, {"temperature": 0.6}),
                ("script", ScriptAgent, {"temperature": 0.3}),
                ("review", ReviewAgent, {"temperature": 0.2}),
                ("testing", TestingAgent, {"temperature": 0.3}),
                ("curriculum", CurriculumAlignmentAgent, {"temperature": 0.4}),
                ("database", DatabaseSupervisorAgent, {"temperature": 0.3}),
            ]

            # Educational agents that create their own config
            agents_without_config = [
                ("assessment", AssessmentDesignAgent),
                ("adaptive", AdaptiveLearningAgent),
                ("analytics", LearningAnalyticsAgent),
                ("validation", EducationalValidationAgent),
            ]

            # Initialize agents that accept config
            for agent_key, agent_class, config_overrides in agents_with_config:
                try:
                    # Create agent configuration
                    agent_config = AgentConfig(
                        name=f"{agent_class.__name__}_{agent_key}",
                        model=self.config.model,
                        **config_overrides
                    )

                    # Initialize agent
                    agent_instance = agent_class(agent_config)
                    self.managed_agents[agent_key] = agent_instance
                    self.agent_load[agent_key] = 0
                    self.agent_performance[agent_key] = {
                        "total_tasks": 0,
                        "successful_tasks": 0,
                        "failed_tasks": 0,
                        "average_time": 0.0,
                        "last_used": None
                    }

                    logger.info(f"Initialized {agent_key} agent successfully")

                except Exception as e:
                    logger.error(f"Failed to initialize {agent_key} agent: {e}")
                    # Continue initializing other agents even if one fails

            # Initialize agents that don't accept config
            for agent_key, agent_class in agents_without_config:
                try:
                    # Initialize agent without config (they create their own)
                    agent_instance = agent_class()
                    self.managed_agents[agent_key] = agent_instance
                    self.agent_load[agent_key] = 0
                    self.agent_performance[agent_key] = {
                        "total_tasks": 0,
                        "successful_tasks": 0,
                        "average_time": 0.0,
                        "last_used": None
                    }

                    logger.info(f"Initialized {agent_key} agent successfully")

                except Exception as e:
                    logger.error(f"Failed to initialize {agent_key} agent: {e}")
                    # Continue initializing other agents even if one fails

        except Exception as e:
            logger.error(f"Error during agent initialization: {e}")
            traceback.print_exc()

    def _build_complete_workflow_graph(self):
        """Build the complete workflow graph with all nodes and edges"""
        try:
            # Create state graph
            workflow = StateGraph(dict[str, Any])

            # Add all workflow nodes
            workflow.add_node("analyze", self._analyze_task_node)
            workflow.add_node("plan", self._plan_execution_node)
            workflow.add_node("validate", self._validate_plan_node)
            workflow.add_node("delegate", self._delegate_tasks_node)
            workflow.add_node("monitor", self._monitor_execution_node)
            workflow.add_node("aggregate", self._aggregate_results_node)
            workflow.add_node("quality_check", self._quality_check_node)
            workflow.add_node("finalize", self._finalize_results_node)
            workflow.add_node("error_handler", self._handle_errors_node)
            workflow.add_node("retry", self._retry_failed_tasks_node)

            # Set entry point
            workflow.set_entry_point("analyze")

            # Add edges
            workflow.add_edge("analyze", "plan")
            workflow.add_edge("plan", "validate")

            # Conditional edges from validation
            workflow.add_conditional_edges(
                "validate",
                self._validation_router,
                {
                    "proceed": "delegate",
                    "replan": "plan",
                    "error": "error_handler"
                }
            )

            workflow.add_edge("delegate", "monitor")

            # Conditional edges from monitoring
            workflow.add_conditional_edges(
                "monitor",
                self._monitor_router,
                {
                    "complete": "aggregate",
                    "continue": "monitor",
                    "retry": "retry",
                    "error": "error_handler"
                }
            )

            workflow.add_edge("retry", "delegate")
            workflow.add_edge("aggregate", "quality_check")

            # Conditional edges from quality check
            workflow.add_conditional_edges(
                "quality_check",
                self._quality_router,
                {
                    "pass": "finalize",
                    "fail": "retry",
                    "error": "error_handler"
                }
            )

            workflow.add_edge("finalize", END)
            workflow.add_edge("error_handler", END)

            # Compile the workflow
            self.workflow_graph = workflow.compile()

            logger.info("Successfully built complete workflow graph")

        except Exception as e:
            logger.error(f"Failed to build workflow graph: {e}")
            traceback.print_exc()

    async def _analyze_task_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Analyze the incoming task and extract requirements"""
        try:
            task = state.get("task", "")
            context = state.get("context", {})

            # Create analysis prompt
            analysis_prompt = f"""Analyze this task for educational Roblox content generation:

Task: {task}
Context: {json.dumps(context, indent=2)}

Provide a detailed analysis including:

1. **Task Type Classification**:
   - Primary type: (content_generation, quiz_creation, terrain_building, script_development, etc.)
   - Secondary types if applicable

2. **Educational Requirements**:
   - Subject area
   - Grade level
   - Learning objectives
   - Curriculum standards

3. **Technical Requirements**:
   - Roblox-specific features needed
   - Performance constraints
   - Security considerations

4. **Resource Requirements**:
   - Which agents are needed
   - Estimated complexity (simple/moderate/complex)
   - Dependencies between subtasks

5. **Success Criteria**:
   - What defines successful completion
   - Quality metrics
   - Validation requirements

Provide your analysis in JSON format."""

            # Get analysis from LLM
            response = await self.llm.ainvoke(analysis_prompt)

            # Parse analysis
            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback to text analysis
                analysis = {
                    "raw_analysis": response.content,
                    "task_type": self._infer_task_type(task),
                    "complexity": "moderate",
                    "agents_needed": self._infer_required_agents(task)
                }

            # Update state
            state["analysis"] = analysis
            state["phase"] = "analyzed"
            state["timestamp"] = datetime.now().isoformat()

            logger.info(f"Task analysis complete: {analysis.get('task_type', 'unknown')}")

            return state

        except Exception as e:
            logger.error(f"Error in task analysis: {e}")
            state["error"] = str(e)
            state["phase"] = "error"
            return state

    async def _plan_execution_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Create execution plan based on analysis"""
        try:
            analysis = state.get("analysis", {})
            task = state.get("task", "")
            context = state.get("context", {})

            # Get available agents for the prompt
            available_agents = list(self.managed_agents.keys())

            # Create planning prompt with available agents
            planning_prompt = f"""Create a detailed execution plan for this task:

Task: {task}
Analysis: {json.dumps(analysis, indent=2)}

IMPORTANT: You MUST use ONLY these exact agent names:
{json.dumps(available_agents, indent=2)}

Available agents and their capabilities:
- content: Educational content generation, curriculum alignment
- quiz: Quiz and assessment creation
- terrain: 3D environment and terrain generation
- script: Lua script development for Roblox
- review: Code review and optimization
- testing: Testing and validation
- curriculum: Curriculum alignment verification
- database: Data persistence and management

Create a structured execution plan with:

1. **Delegation Strategy**:
   - single: One agent handles everything
   - parallel: Multiple agents work simultaneously
   - sequential: Agents work in order
   - hierarchical: Nested delegations

2. **Task Breakdown**:
   For each subtask provide:
   - agent: Which agent should handle it (MUST be from the list above)
   - description: What needs to be done
   - dependencies: Other subtasks that must complete first
   - priority: high/medium/low
   - estimated_time: In seconds
   - context: Specific parameters for that agent

3. **Execution Order**:
   - Define the sequence or parallelization
   - Identify critical path
   - Set checkpoints for monitoring

Provide the plan in JSON format with a 'delegations' array."""

            # Get execution plan from LLM
            response = await self.llm.ainvoke(planning_prompt)

            # Parse plan
            try:
                plan = json.loads(response.content)
            except json.JSONDecodeError:
                # Create default plan
                plan = self._create_default_plan(analysis, task, context)

            # Create DelegationTask objects
            delegations = []
            for idx, task_spec in enumerate(plan.get("delegations", [])):
                delegation = DelegationTask(
                    task_id=f"{state.get('workflow_id', 'wf')}_{idx:03d}",
                    agent_type=task_spec.get("agent", "content"),
                    task_description=task_spec.get("description", task),
                    context={
                        **context,
                        **task_spec.get("context", {}),
                        "original_task": task,
                        "task_index": idx
                    },
                    priority=self._parse_priority(task_spec.get("priority", "medium")),
                    dependencies=task_spec.get("dependencies", []),
                    timeout=task_spec.get("estimated_time", 300)
                )
                delegations.append(delegation)

            # Update state
            state["plan"] = plan
            state["delegations"] = delegations
            state["strategy"] = plan.get("strategy", DelegationStrategy.SEQUENTIAL.value)
            state["phase"] = "planned"

            logger.info(f"Execution plan created with {len(delegations)} delegations")

            return state

        except Exception as e:
            logger.error(f"Error in execution planning: {e}")
            state["error"] = str(e)
            state["phase"] = "error"
            return state

    async def _validate_plan_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Validate the execution plan before proceeding"""
        try:
            state.get("plan", {})
            delegations = state.get("delegations", [])

            validation_issues = []

            # Check if we have delegations
            if not delegations:
                validation_issues.append("No delegations created")

            # Check agent availability
            for delegation in delegations:
                if delegation.agent_type not in self.managed_agents:
                    validation_issues.append(f"Agent {delegation.agent_type} not available")

            # Check circular dependencies
            if self._has_circular_dependencies(delegations):
                validation_issues.append("Circular dependencies detected")

            # Check resource constraints
            if len(delegations) > 20:
                validation_issues.append("Too many delegations (>20)")

            # Update state
            if validation_issues:
                state["validation_issues"] = validation_issues
                state["phase"] = "validation_failed"
                logger.warning(f"Plan validation failed: {validation_issues}")
            else:
                state["phase"] = "validated"
                logger.info("Plan validation successful")

            return state

        except Exception as e:
            logger.error(f"Error in plan validation: {e}")
            state["error"] = str(e)
            state["phase"] = "error"
            return state

    async def _delegate_tasks_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Delegate tasks to appropriate agents"""
        try:
            delegations = state.get("delegations", [])
            strategy = state.get("strategy", DelegationStrategy.SEQUENTIAL.value)

            results = []

            if strategy == DelegationStrategy.PARALLEL.value:
                # Execute all tasks in parallel
                results = await self._execute_parallel_delegations(delegations)

            elif strategy == DelegationStrategy.SEQUENTIAL.value:
                # Execute tasks in sequence
                results = await self._execute_sequential_delegations(delegations)

            elif strategy == DelegationStrategy.HIERARCHICAL.value:
                # Execute with nested delegation
                results = await self._execute_hierarchical_delegations(delegations)

            else:
                # Default to sequential
                results = await self._execute_sequential_delegations(delegations)

            # Update state
            state["delegation_results"] = results
            state["phase"] = "delegated"

            # Count successes and failures
            successful = sum(1 for r in results if r.get("success", False))
            failed = len(results) - successful

            logger.info(f"Delegation complete: {successful} successful, {failed} failed")

            return state

        except Exception as e:
            logger.error(f"Error in task delegation: {e}")
            state["error"] = str(e)
            state["phase"] = "error"
            return state

    async def _execute_parallel_delegations(self, delegations: list[DelegationTask]) -> list[dict[str, Any]]:
        """Execute delegations in parallel"""
        tasks = []
        for delegation in delegations:
            if not delegation.dependencies:  # Only tasks without dependencies
                task = self._execute_single_delegation(delegation)
                tasks.append(task)

        # Wait for all parallel tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "task_id": delegations[idx].task_id,
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)

        # Handle dependent tasks
        for delegation in delegations:
            if delegation.dependencies:
                # Check if dependencies are complete
                dep_results = [r for r in processed_results if r["task_id"] in delegation.dependencies]
                if all(r.get("success", False) for r in dep_results):
                    result = await self._execute_single_delegation(delegation)
                    processed_results.append(result)
                else:
                    processed_results.append({
                        "task_id": delegation.task_id,
                        "success": False,
                        "error": "Dependencies failed"
                    })

        return processed_results

    async def _execute_sequential_delegations(self, delegations: list[DelegationTask]) -> list[dict[str, Any]]:
        """Execute delegations in sequence"""
        results = []
        completed_tasks = set()

        # Sort by dependencies
        sorted_delegations = self._topological_sort(delegations)

        for delegation in sorted_delegations:
            # Check dependencies
            if all(dep in completed_tasks for dep in delegation.dependencies):
                result = await self._execute_single_delegation(delegation)
                results.append(result)
                if result.get("success", False):
                    completed_tasks.add(delegation.task_id)
            else:
                results.append({
                    "task_id": delegation.task_id,
                    "success": False,
                    "error": "Dependencies not met"
                })

        return results

    async def _execute_hierarchical_delegations(self, delegations: list[DelegationTask]) -> list[dict[str, Any]]:
        """Execute delegations with hierarchical structure"""
        # Group by priority levels
        priority_groups = {}
        for delegation in delegations:
            priority = delegation.priority.value
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(delegation)

        results = []

        # Execute by priority
        for priority in sorted(priority_groups.keys(), reverse=True):
            group_delegations = priority_groups[priority]
            group_results = await self._execute_parallel_delegations(group_delegations)
            results.extend(group_results)

        return results

    async def _execute_single_delegation(self, delegation: DelegationTask) -> dict[str, Any]:
        """Execute a single delegation to an agent"""
        try:
            # Get the agent
            agent = self.managed_agents.get(delegation.agent_type)
            if not agent:
                return {
                    "task_id": delegation.task_id,
                    "agent": delegation.agent_type,
                    "success": False,
                    "error": f"Agent {delegation.agent_type} not found"
                }

            # Update agent load
            self.agent_load[delegation.agent_type] += 1
            delegation.started_at = datetime.now()

            # Execute the task
            try:
                # Set timeout
                result = await asyncio.wait_for(
                    agent.execute(delegation.task_description, delegation.context),
                    timeout=delegation.timeout
                )

                delegation.completed_at = datetime.now()
                delegation.result = result

                # Update performance metrics
                self._update_agent_performance(delegation.agent_type, result, delegation)

                return {
                    "task_id": delegation.task_id,
                    "agent": delegation.agent_type,
                    "success": result.success,
                    "output": result.output,
                    "metadata": result.metadata,
                    "execution_time": (delegation.completed_at - delegation.started_at).total_seconds()
                }

            except asyncio.TimeoutError:
                return {
                    "task_id": delegation.task_id,
                    "agent": delegation.agent_type,
                    "success": False,
                    "error": f"Task timeout after {delegation.timeout} seconds"
                }

            finally:
                # Update agent load
                self.agent_load[delegation.agent_type] -= 1

        except Exception as e:
            logger.error(f"Error executing delegation {delegation.task_id}: {e}")
            return {
                "task_id": delegation.task_id,
                "agent": delegation.agent_type,
                "success": False,
                "error": str(e)
            }

    async def _monitor_execution_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Monitor ongoing task execution"""
        try:
            results = state.get("delegation_results", [])

            # Check completion status
            total_tasks = len(results)
            completed = sum(1 for r in results if "output" in r or "error" in r)
            successful = sum(1 for r in results if r.get("success", False))
            failed = sum(1 for r in results if not r.get("success", True) and "error" in r)

            state["execution_stats"] = {
                "total": total_tasks,
                "completed": completed,
                "successful": successful,
                "failed": failed,
                "in_progress": total_tasks - completed
            }

            # Determine next action
            if completed == total_tasks:
                if failed > 0 and failed < total_tasks:
                    state["phase"] = "partial_complete"
                elif failed == total_tasks:
                    state["phase"] = "all_failed"
                else:
                    state["phase"] = "complete"
            else:
                state["phase"] = "monitoring"

            logger.info(f"Monitoring: {completed}/{total_tasks} tasks complete")

            return state

        except Exception as e:
            logger.error(f"Error in execution monitoring: {e}")
            state["error"] = str(e)
            state["phase"] = "error"
            return state

    async def _aggregate_results_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Aggregate results from all delegations"""
        try:
            results = state.get("delegation_results", [])
            task = state.get("task", "")

            # Helper function to safely serialize objects
            def safe_json_dumps(obj):
                """Safely serialize objects to JSON, handling non-serializable types"""
                try:
                    # Try standard serialization first
                    return json.dumps(obj)
                except (TypeError, ValueError):
                    # Handle special types
                    if hasattr(obj, '__dict__'):
                        # Convert object to dict
                        return json.dumps({k: str(v) for k, v in obj.__dict__.items()})
                    elif isinstance(obj, dict):
                        # Recursively handle dict values
                        safe_dict = {}
                        for k, v in obj.items():
                            try:
                                json.dumps(v)
                                safe_dict[k] = v
                            except:
                                safe_dict[k] = str(v)
                        return json.dumps(safe_dict)
                    else:
                        return str(obj)

            # Create aggregation prompt
            results_summary = "\n\n".join([
                f"Agent: {r.get('agent', 'unknown')}\n"
                f"Task ID: {r.get('task_id', 'unknown')}\n"
                f"Success: {r.get('success', False)}\n"
                f"Output: {safe_json_dumps(r.get('output', {})) if r.get('output') else r.get('error', 'No output')}"
                for r in results
            ])

            aggregation_prompt = f"""Aggregate and synthesize these results into a cohesive response:

Original Task: {task}

Agent Results:
{results_summary}

Create a unified output that:
1. Combines all successful results coherently
2. Highlights key achievements
3. Notes any failures or limitations
4. Provides a complete solution to the original task
5. Includes all generated content (code, configurations, educational materials)

Format the response as a comprehensive JSON structure."""

            # Get aggregated response
            response = await self.llm.ainvoke(aggregation_prompt)

            # Parse aggregated result
            try:
                aggregated = json.loads(response.content)
            except json.JSONDecodeError:
                aggregated = {
                    "summary": response.content,
                    "components": [r.get("output", {}) for r in results if r.get("success", False)],
                    "failures": [r.get("error", "Unknown error") for r in results if not r.get("success", True)]
                }

            # Update state
            state["aggregated_result"] = aggregated
            state["phase"] = "aggregated"

            logger.info("Results aggregation complete")

            return state

        except Exception as e:
            logger.error(f"Error in results aggregation: {e}")
            state["error"] = str(e)
            state["phase"] = "error"
            return state

    async def _quality_check_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Perform quality checks on aggregated results"""
        try:
            aggregated = state.get("aggregated_result", {})
            analysis = state.get("analysis", {})

            # Create quality check prompt
            quality_prompt = f"""Perform quality assessment on these results:

Original Requirements:
{json.dumps(analysis, indent=2)}

Aggregated Results:
{json.dumps(aggregated, indent=2)}

Assess:
1. **Completeness**: Are all requirements met?
2. **Correctness**: Is the solution technically correct?
3. **Quality**: Does it meet quality standards?
4. **Educational Value**: Is it appropriate for the target audience?
5. **Integration**: Do all components work together?

Provide assessment as JSON with:
- overall_score: 0-100
- passed: true/false
- issues: [] list of issues found
- recommendations: [] list of improvements"""

            # Get quality assessment
            response = await self.llm.ainvoke(quality_prompt)

            # Parse assessment
            try:
                assessment = json.loads(response.content)
            except json.JSONDecodeError:
                assessment = {
                    "overall_score": 75,
                    "passed": True,
                    "issues": [],
                    "recommendations": ["Review generated content for accuracy"]
                }

            # Update state
            state["quality_assessment"] = assessment
            state["quality_passed"] = assessment.get("passed", True)
            state["phase"] = "quality_checked"

            logger.info(f"Quality check: Score {assessment.get('overall_score', 'N/A')}, "
                       f"Passed: {assessment.get('passed', 'Unknown')}")

            return state

        except Exception as e:
            logger.error(f"Error in quality check: {e}")
            state["error"] = str(e)
            state["phase"] = "error"
            return state

    async def _finalize_results_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Finalize and format the results"""
        try:
            aggregated = state.get("aggregated_result", {})
            assessment = state.get("quality_assessment", {})
            stats = state.get("execution_stats", {})

            # Create final result structure
            final_result = {
                "success": state.get("quality_passed", True),
                "task": state.get("task", ""),
                "result": aggregated,
                "quality_assessment": assessment,
                "execution_stats": stats,
                "metadata": {
                    "workflow_id": state.get("workflow_id", ""),
                    "created_at": state.get("created_at", ""),
                    "completed_at": datetime.now().isoformat(),
                    "total_execution_time": (
                        datetime.now() - datetime.fromisoformat(state.get("created_at", datetime.now().isoformat()))
                    ).total_seconds()
                }
            }

            # Update state
            state["final_result"] = final_result
            state["phase"] = "completed"

            # Store in history
            self.task_history.extend(state.get("delegations", []))

            logger.info(f"Workflow completed successfully: {state.get('workflow_id', 'unknown')}")

            return state

        except Exception as e:
            logger.error(f"Error in finalizing results: {e}")
            state["error"] = str(e)
            state["phase"] = "error"
            return state

    async def _handle_errors_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Handle errors in the workflow"""
        try:
            error = state.get("error", "Unknown error")
            phase = state.get("phase", "unknown")

            logger.error(f"Handling error in phase {phase}: {error}")

            # Create error response
            error_result = {
                "success": False,
                "error": error,
                "phase": phase,
                "partial_results": state.get("delegation_results", []),
                "recovery_attempted": False
            }

            # Attempt recovery for certain errors
            if "timeout" in str(error).lower():
                # Try with extended timeout
                error_result["recovery_attempted"] = True
                error_result["recovery_action"] = "retry_with_extended_timeout"
            elif "not found" in str(error).lower():
                # Try alternative agent
                error_result["recovery_attempted"] = True
                error_result["recovery_action"] = "use_alternative_agent"

            state["final_result"] = error_result
            state["phase"] = "error_handled"

            return state

        except Exception as e:
            logger.error(f"Error in error handler: {e}")
            state["final_result"] = {"success": False, "error": str(e)}
            return state

    async def _retry_failed_tasks_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Retry failed tasks with adjusted parameters"""
        try:
            results = state.get("delegation_results", [])
            failed_tasks = [r for r in results if not r.get("success", False)]

            if not failed_tasks:
                return state

            logger.info(f"Retrying {len(failed_tasks)} failed tasks")

            # Get original delegations
            delegations = state.get("delegations", [])
            retry_delegations = []

            for failed in failed_tasks:
                task_id = failed.get("task_id")
                original = next((d for d in delegations if d.task_id == task_id), None)

                if original and original.retry_count < original.max_retries:
                    # Create retry delegation with adjustments
                    retry_delegation = DelegationTask(
                        task_id=f"{task_id}_retry_{original.retry_count + 1}",
                        agent_type=original.agent_type,
                        task_description=original.task_description,
                        context={
                            **original.context,
                            "retry_attempt": original.retry_count + 1,
                            "previous_error": failed.get("error", "")
                        },
                        priority=original.priority,
                        dependencies=original.dependencies,
                        retry_count=original.retry_count + 1,
                        max_retries=original.max_retries,
                        timeout=original.timeout * 1.5,  # Extend timeout
                        created_at=original.created_at
                    )
                    retry_delegations.append(retry_delegation)

            if retry_delegations:
                # Execute retries
                retry_results = await self._execute_sequential_delegations(retry_delegations)

                # Merge with original results
                for retry_result in retry_results:
                    # Find and replace original failed result
                    original_id = retry_result["task_id"].rsplit("_retry_", 1)[0]
                    for i, result in enumerate(results):
                        if result.get("task_id") == original_id:
                            results[i] = retry_result
                            break

                state["delegation_results"] = results
                state["retries_performed"] = len(retry_delegations)

            state["phase"] = "retried"

            return state

        except Exception as e:
            logger.error(f"Error in retry logic: {e}")
            state["error"] = str(e)
            return state

    def _validation_router(self, state: dict[str, Any]) -> Literal["proceed", "replan", "error"]:
        """Route based on validation results"""
        if state.get("phase") == "error":
            return "error"
        elif state.get("phase") == "validation_failed":
            return "replan"
        else:
            return "proceed"

    def _monitor_router(self, state: dict[str, Any]) -> Literal["complete", "continue", "retry", "error"]:
        """Route based on monitoring results"""
        phase = state.get("phase", "")
        stats = state.get("execution_stats", {})

        if phase == "error":
            return "error"
        elif phase == "complete":
            return "complete"
        elif phase == "all_failed":
            return "retry"
        elif stats.get("in_progress", 0) > 0:
            return "continue"
        else:
            return "complete"

    def _quality_router(self, state: dict[str, Any]) -> Literal["pass", "fail", "error"]:
        """Route based on quality check results"""
        if state.get("phase") == "error":
            return "error"
        elif state.get("quality_passed", False):
            return "pass"
        else:
            return "fail"

    async def _process_task(self, state: AgentState) -> Any:
        """Process task through the complete workflow"""
        try:
            # Create workflow state
            workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.metrics['tasks_processed']}"

            workflow_state = {
                "task": state["task"],
                "context": state["context"],
                "workflow_id": workflow_id,
                "created_at": datetime.now().isoformat(),
                "messages": [],
                "metadata": state["metadata"],
                "phase": "initialized"
            }

            # Store active workflow
            self.active_workflows[workflow_id] = workflow_state

            # Execute workflow graph
            final_state = await self.workflow_graph.ainvoke(workflow_state)

            # Extract final result
            result = final_state.get("final_result", {})

            # Clean up active workflow
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

            return result

        except Exception as e:
            logger.error(f"Error in workflow execution: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "phase": "workflow_error"
            }

    def _infer_task_type(self, task: str) -> str:
        """Infer task type from task description"""
        task_lower = task.lower()

        if any(word in task_lower for word in ["quiz", "assessment", "test", "questions"]):
            return TaskType.QUIZ_CREATION.value
        elif any(word in task_lower for word in ["terrain", "environment", "world", "landscape"]):
            return TaskType.TERRAIN_BUILDING.value
        elif any(word in task_lower for word in ["script", "code", "lua", "program"]):
            return TaskType.SCRIPT_DEVELOPMENT.value
        elif any(word in task_lower for word in ["review", "optimize", "improve", "check"]):
            return TaskType.REVIEW_OPTIMIZATION.value
        elif any(word in task_lower for word in ["content", "lesson", "curriculum", "educational"]):
            return TaskType.CONTENT_GENERATION.value
        else:
            return TaskType.COMPLEX_WORKFLOW.value

    def _infer_required_agents(self, task: str) -> list[str]:
        """Infer required agents from task description"""
        required = []
        task_lower = task.lower()

        if any(word in task_lower for word in ["content", "lesson", "curriculum"]):
            required.append("content")
        if any(word in task_lower for word in ["quiz", "assessment", "test"]):
            required.append("quiz")
        if any(word in task_lower for word in ["terrain", "environment", "world"]):
            required.append("terrain")
        if any(word in task_lower for word in ["script", "code", "lua"]):
            required.append("script")
        if any(word in task_lower for word in ["review", "optimize", "check"]):
            required.append("review")
        if any(word in task_lower for word in ["test", "validate", "verify"]):
            required.append("testing")

        # Default to content agent if none identified
        if not required:
            required.append("content")

        return required

    def _create_default_plan(self, analysis: dict[str, Any], task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Create a default execution plan"""
        agents_needed = analysis.get("agents_needed", ["content"])

        delegations = []
        for idx, agent in enumerate(agents_needed):
            delegations.append({
                "agent": agent,
                "description": f"Handle {agent} aspects of: {task}",
                "context": context,
                "priority": "medium",
                "dependencies": [],
                "estimated_time": 300
            })

        return {
            "strategy": DelegationStrategy.SEQUENTIAL.value if len(agents_needed) > 1 else DelegationStrategy.SINGLE.value,
            "delegations": delegations
        }

    def _parse_priority(self, priority_str: str) -> AgentPriority:
        """Parse priority string to AgentPriority enum"""
        priority_map = {
            "critical": AgentPriority.CRITICAL,
            "high": AgentPriority.HIGH,
            "medium": AgentPriority.MEDIUM,
            "low": AgentPriority.LOW
        }
        return priority_map.get(priority_str.lower(), AgentPriority.MEDIUM)

    def _has_circular_dependencies(self, delegations: list[DelegationTask]) -> bool:
        """Check for circular dependencies in delegations"""
        # Build dependency graph
        graph = {d.task_id: d.dependencies for d in delegations}

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for task_id in graph:
            if task_id not in visited:
                if has_cycle(task_id):
                    return True

        return False

    def _topological_sort(self, delegations: list[DelegationTask]) -> list[DelegationTask]:
        """Sort delegations based on dependencies"""
        # Build dependency graph
        graph = {d.task_id: d for d in delegations}
        in_degree = {d.task_id: 0 for d in delegations}

        for d in delegations:
            for dep in d.dependencies:
                if dep in in_degree:
                    in_degree[d.task_id] += 1

        # Find nodes with no dependencies
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        sorted_tasks = []

        while queue:
            task_id = queue.pop(0)
            sorted_tasks.append(graph[task_id])

            # Update in-degrees
            for d in delegations:
                if task_id in d.dependencies:
                    in_degree[d.task_id] -= 1
                    if in_degree[d.task_id] == 0:
                        queue.append(d.task_id)

        # Add any remaining tasks (might have circular dependencies)
        for d in delegations:
            if d not in sorted_tasks:
                sorted_tasks.append(d)

        return sorted_tasks

    def _update_agent_performance(self, agent_type: str, result: TaskResult, delegation: DelegationTask):
        """Update agent performance metrics"""
        if agent_type not in self.agent_performance:
            self.agent_performance[agent_type] = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "average_time": 0.0,
                "last_used": None
            }

        metrics = self.agent_performance[agent_type]
        metrics["total_tasks"] += 1

        if result.success:
            metrics["successful_tasks"] += 1
        else:
            metrics["failed_tasks"] += 1

        # Update average time
        execution_time = (delegation.completed_at - delegation.started_at).total_seconds()
        current_avg = metrics["average_time"]
        metrics["average_time"] = (
            (current_avg * (metrics["total_tasks"] - 1) + execution_time) / metrics["total_tasks"]
        )

        metrics["last_used"] = datetime.now().isoformat()

    async def get_agent_status_report(self) -> dict[str, Any]:
        """Get comprehensive status report for all agents"""
        report = {
            "supervisor_status": self.get_status(),
            "managed_agents": {},
            "performance_metrics": self.agent_performance,
            "active_workflows": len(self.active_workflows),
            "task_history_count": len(self.task_history),
            "agent_load": self.agent_load
        }

        for name, agent in self.managed_agents.items():
            report["managed_agents"][name] = agent.get_status()

        return report

    async def shutdown(self):
        """Shutdown the supervisor and all managed agents"""
        logger.info("Shutting down Complete Supervisor Agent")

        # Cancel active workflows
        for workflow_id in list(self.active_workflows.keys()):
            logger.info(f"Cancelling workflow: {workflow_id}")
            del self.active_workflows[workflow_id]

        # Reset all agents
        for name, agent in self.managed_agents.items():
            try:
                agent.reset()
                logger.info(f"Reset agent: {name}")
            except Exception as e:
                logger.error(f"Error resetting agent {name}: {e}")

        # Clear history
        self.task_history.clear()

        logger.info("Complete Supervisor Agent shutdown complete")