"""
Supervisor Agent - Orchestrates and manages other agents

Uses LangGraph for hierarchical task delegation and supervision.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph

from .base_agent import AgentConfig, AgentPriority, AgentState, BaseAgent, TaskResult

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks the supervisor can handle"""

    CONTENT_GENERATION = "content_generation"
    QUIZ_CREATION = "quiz_creation"
    TERRAIN_BUILDING = "terrain_building"
    SCRIPT_DEVELOPMENT = "script_development"
    REVIEW_OPTIMIZATION = "review_optimization"
    COMPLEX_WORKFLOW = "complex_workflow"
    PLUGIN_REQUEST = "plugin_request"
    DASHBOARD_REQUEST = "dashboard_request"
    CI_CD_PIPELINE = "ci_cd_pipeline"


class SupervisorDecision(Enum):
    """Supervisor routing decisions"""

    DELEGATE_CONTENT = "delegate_content"
    DELEGATE_QUIZ = "delegate_quiz"
    DELEGATE_TERRAIN = "delegate_terrain"
    DELEGATE_SCRIPT = "delegate_script"
    DELEGATE_REVIEW = "delegate_review"
    PARALLEL_EXECUTION = "parallel_execution"
    SEQUENTIAL_EXECUTION = "sequential_execution"
    DIRECT_RESPONSE = "direct_response"
    ESCALATE = "escalate"


class SupervisorAgent(BaseAgent):
    """
    Supervisor agent that orchestrates other specialized agents.

    Responsibilities:
    - Task analysis and routing
    - Agent coordination
    - Workflow management
    - Result aggregation
    - Error recovery
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="SupervisorAgent",
                model="gpt-3.5-turbo",
                temperature=0.3,  # Lower temperature for more consistent decisions
                system_prompt=self._get_supervisor_prompt(),
            )
        super().__init__(config)

        # Agent registry
        self.managed_agents: dict[str, BaseAgent] = {}

        # Workflow graph
        self.workflow = self._build_workflow_graph()

        # Task queue
        self.task_queue: list[dict[str, Any]] = []

        # Performance tracking
        self.agent_performance: dict[str, dict[str, Any]] = {}

    def _get_supervisor_prompt(self) -> str:
        """Get specialized prompt for supervisor agent"""
        return """You are the Supervisor Agent responsible for orchestrating a team of specialized agents to create educational Roblox environments.

Your team includes:
1. Content Agent - Educational content and curriculum alignment
2. Quiz Agent - Interactive quiz and assessment creation
3. Terrain Agent - 3D environment and terrain generation
4. Script Agent - Lua script development for Roblox
5. Review Agent - Code review and optimization
6. Testing Agent - Automated testing and quality assurance

Your responsibilities:
- Analyze incoming tasks and determine the best agent(s) to handle them
- Coordinate multi-agent workflows for complex tasks
- Monitor agent performance and handle errors
- Aggregate and synthesize results from multiple agents
- Ensure educational quality and technical correctness
- Trigger testing validation after agent completions

When routing tasks:
- Consider agent specializations and current workload
- Identify dependencies between subtasks
- Determine if parallel or sequential execution is needed
- Always include testing validation for code-related outputs
- Escalate issues that require human intervention

Always provide clear task decomposition and routing rationale."""

    def _build_workflow_graph(self) -> StateGraph:
        """Build the LangGraph workflow for task orchestration"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("analyze", self._analyze_task)
        workflow.add_node("route", self._route_task)
        workflow.add_node("delegate", self._delegate_task)
        workflow.add_node("aggregate", self._aggregate_results)
        workflow.add_node("review", self._review_results)

        # Add edges
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "route")

        # Conditional routing
        workflow.add_conditional_edges(
            "route",
            self._routing_decision,
            {"delegate": "delegate", "direct": END, "escalate": END},
        )

        workflow.add_edge("delegate", "aggregate")
        workflow.add_edge("aggregate", "review")
        workflow.add_edge("review", END)

        return workflow.compile()

    async def _analyze_task(self, state: AgentState) -> AgentState:
        """Analyze the incoming task and extract requirements"""
        task = state["task"]

        analysis_prompt = f"""Analyze this task and extract key requirements:

Task: {task}

Identify:
1. Task type(s) - What kind of work is needed?
2. Required agents - Which specialists should handle this?
3. Dependencies - What needs to be done in sequence?
4. Complexity - Simple, moderate, or complex?
5. Priority - How urgent is this task?
6. Success criteria - What defines completion?

Provide a structured analysis."""

        response = await self.llm.ainvoke(analysis_prompt)

        state["metadata"]["task_analysis"] = response.content
        state["messages"].append(AIMessage(content=f"Task analysis: {response.content}"))

        return state

    async def _route_task(self, state: AgentState) -> AgentState:
        """Determine routing strategy for the task"""
        analysis = state["metadata"].get("task_analysis", "")

        routing_prompt = f"""Based on this task analysis, determine the routing strategy:

Analysis: {analysis}

Decide:
1. Which agent(s) should handle this task?
2. Should they work in parallel or sequence?
3. What subtasks should be created?
4. What is the execution order?

Routing options:
- Single agent delegation
- Parallel multi-agent execution
- Sequential multi-agent workflow
- Direct response (no delegation needed)
- Escalate (requires human intervention)

Provide your routing decision with rationale."""

        response = await self.llm.ainvoke(routing_prompt)

        state["metadata"]["routing_decision"] = response.content
        state["messages"].append(AIMessage(content=f"Routing: {response.content}"))

        return state

    def _routing_decision(self, state: AgentState) -> Literal["delegate", "direct", "escalate"]:
        """Make routing decision based on analysis"""
        routing = state["metadata"].get("routing_decision", "")
        task_source = state["metadata"].get("source", "")

        # Check for plugin-specific routing
        if task_source == "roblox_plugin":
            return self._handle_plugin_routing(state)
        elif task_source == "dashboard":
            return self._handle_dashboard_routing(state)
        elif task_source == "ci_cd":
            return self._handle_cicd_routing(state)

        # Default routing logic
        if "escalate" in routing.lower():
            return "escalate"
        elif "direct" in routing.lower() or "no delegation" in routing.lower():
            return "direct"
        else:
            return "delegate"

    async def _delegate_task(self, state: AgentState) -> AgentState:
        """Delegate task to appropriate agent(s)"""
        routing = state["metadata"].get("routing_decision", "")
        metadata = state["metadata"]

        # Parse routing decision to identify agents and strategy
        delegations = self._parse_routing_decision(routing, metadata)

        if not delegations:
            state["error"] = "Failed to parse routing decision"
            return state

        # Sort delegations by priority if present
        delegations = sorted(
            delegations,
            key=lambda x: self._get_priority_value(x.get("priority", "medium")),
        )

        # Execute delegations based on source
        if metadata.get("source") == "roblox_plugin":
            results = await self._execute_plugin_delegations(delegations, state)
        elif metadata.get("source") == "dashboard":
            results = await self._execute_dashboard_delegations(delegations, state)
        elif metadata.get("source") == "ci_cd":
            results = await self._execute_cicd_delegations(delegations, state)
        else:
            results = await self._execute_standard_delegations(delegations, state)

        state["metadata"]["delegation_results"] = results

        return state

    async def _aggregate_results(self, state: AgentState) -> AgentState:
        """Aggregate results from multiple agents"""
        results = state["metadata"].get("delegation_results", [])

        if not results:
            state["result"] = "No results to aggregate"
            return state

        # Create aggregation prompt
        results_summary = "\n".join(
            [
                f"Agent: {r['agent']}\nTask: {r['task']}\nResult: {r['result'].output if r['result'].success else r['result'].error}"
                for r in results
            ]
        )

        aggregation_prompt = f"""Aggregate these results into a cohesive response:

{results_summary}

Create a unified output that:
1. Combines all successful results
2. Highlights any issues or failures
3. Provides a coherent narrative
4. Includes all generated code/content
5. Suggests next steps if needed"""

        response = await self.llm.ainvoke(aggregation_prompt)

        state["result"] = response.content
        state["messages"].append(AIMessage(content=f"Aggregated result: {response.content}"))

        return state

    async def _review_results(self, state: AgentState) -> AgentState:
        """Review and validate the aggregated results"""
        result = state.get("result", "")

        review_prompt = f"""Review this result for quality and completeness:

{result}

Check for:
1. Educational appropriateness
2. Technical accuracy
3. Completeness
4. Roblox compatibility
5. Best practices adherence

Provide a quality score (1-10) and any necessary corrections."""

        response = await self.llm.ainvoke(review_prompt)

        state["metadata"]["quality_review"] = response.content
        state["status"] = "completed"

        return state

    def _parse_routing_decision(
        self, routing: str, metadata: dict[str, Any] = None
    ) -> list[dict[str, str]]:
        """Parse routing decision into actionable delegations"""
        delegations = []

        # Check for plugin-specific requests
        if metadata and metadata.get("source") == "roblox_plugin":
            event_type = metadata.get("event_type", "")

            if event_type == "generate_lesson":
                delegations.extend(
                    [
                        {
                            "agent": "content",
                            "task": "Generate lesson content",
                            "priority": "high",
                        },
                        {
                            "agent": "terrain",
                            "task": "Create 3D environment",
                            "priority": "high",
                        },
                        {
                            "agent": "quiz",
                            "task": "Create assessment",
                            "priority": "medium",
                        },
                        {
                            "agent": "script",
                            "task": "Generate interaction scripts",
                            "priority": "medium",
                        },
                        {
                            "agent": "review",
                            "task": "Validate educational quality",
                            "priority": "low",
                        },
                    ]
                )
            elif event_type == "create_quiz":
                delegations.extend(
                    [
                        {
                            "agent": "quiz",
                            "task": "Create quiz questions",
                            "priority": "high",
                        },
                        {
                            "agent": "script",
                            "task": "Generate quiz UI",
                            "priority": "high",
                        },
                        {
                            "agent": "review",
                            "task": "Validate quiz accuracy",
                            "priority": "medium",
                        },
                    ]
                )
            elif event_type == "build_terrain":
                delegations.extend(
                    [
                        {
                            "agent": "terrain",
                            "task": "Generate terrain",
                            "priority": "high",
                        },
                        {
                            "agent": "script",
                            "task": "Add terrain interactions",
                            "priority": "medium",
                        },
                    ]
                )
            elif event_type == "content_generation":
                delegations.extend(
                    [
                        {
                            "agent": "content",
                            "task": "Generate educational materials",
                            "priority": "high",
                        },
                        {
                            "agent": "review",
                            "task": "Review content quality",
                            "priority": "medium",
                        },
                    ]
                )

        # Check for dashboard requests
        elif metadata and metadata.get("source") == "dashboard":
            request_type = metadata.get("request_type", "")

            if request_type == "lesson_creation":
                delegations.extend(
                    [
                        {
                            "agent": "content",
                            "task": "Create lesson plan",
                            "priority": "high",
                        },
                        {
                            "agent": "quiz",
                            "task": "Generate assessments",
                            "priority": "medium",
                        },
                        {
                            "agent": "terrain",
                            "task": "Design environment",
                            "priority": "medium",
                        },
                    ]
                )
            elif request_type == "analytics":
                delegations.append(
                    {
                        "agent": "analytics",
                        "task": "Generate analytics report",
                        "priority": "high",
                    }
                )

        # Check for CI/CD pipeline requests
        elif metadata and metadata.get("source") == "ci_cd":
            pipeline_stage = metadata.get("stage", "")

            if pipeline_stage == "generate":
                delegations.extend(
                    [
                        {
                            "agent": "content",
                            "task": "Generate CI/CD content",
                            "priority": "high",
                        },
                        {
                            "agent": "script",
                            "task": "Generate scripts",
                            "priority": "high",
                        },
                        {
                            "agent": "terrain",
                            "task": "Generate terrains",
                            "priority": "medium",
                        },
                    ]
                )
            elif pipeline_stage == "test":
                delegations.append(
                    {
                        "agent": "testing",
                        "task": "Run automated tests",
                        "priority": "high",
                    }
                )
            elif pipeline_stage == "deploy":
                delegations.append(
                    {
                        "agent": "deployment",
                        "task": "Deploy to staging",
                        "priority": "high",
                    }
                )

        # Fallback to default parsing if no specific source
        if not delegations:
            if "content" in routing.lower():
                delegations.append({"agent": "content", "task": "Generate educational content"})
            if "quiz" in routing.lower():
                delegations.append({"agent": "quiz", "task": "Create interactive quiz"})
            if "terrain" in routing.lower():
                delegations.append({"agent": "terrain", "task": "Generate terrain"})
            if "script" in routing.lower():
                delegations.append({"agent": "script", "task": "Develop Lua scripts"})
            if "review" in routing.lower():
                delegations.append({"agent": "review", "task": "Review and optimize"})
            if "test" in routing.lower() or "testing" in routing.lower():
                delegations.append({"agent": "testing", "task": "Run tests and validate quality"})

        return delegations

    def _get_or_create_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Get existing agent or create new one"""
        if agent_type not in self.managed_agents:
            # Use a whitelist approach for security
            agent_map = self._get_agent_class_map()

            if agent_type not in agent_map:
                logger.warning(f"Unknown agent type: {agent_type}")
                return None

            try:
                agent_class = agent_map[agent_type]
                self.managed_agents[agent_type] = agent_class()
            except (ImportError, AttributeError, TypeError) as e:
                logger.error(f"Failed to create {agent_type} agent: {e}")
                return None

        return self.managed_agents.get(agent_type)

    def _get_agent_class_map(self) -> dict[str, type]:
        """Get mapping of agent types to classes (whitelist approach)"""
        # Import all agents at once for better security
        from .content_agent import ContentAgent
        from .quiz_agent import QuizAgent
        from .review_agent import ReviewAgent
        from .script_agent import ScriptAgent
        from .terrain_agent import TerrainAgent
        from .testing_agent import TestingAgent

        return {
            "content": ContentAgent,
            "quiz": QuizAgent,
            "terrain": TerrainAgent,
            "script": ScriptAgent,
            "review": ReviewAgent,
            "testing": TestingAgent,
        }

    def _track_agent_performance(self, agent_type: str, result: TaskResult):
        """Track performance metrics for each agent"""
        if agent_type not in self.agent_performance:
            self.agent_performance[agent_type] = {
                "tasks": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0.0,
                "average_time": 0.0,
            }

        perf = self.agent_performance[agent_type]
        perf["tasks"] += 1

        if result.success:
            perf["successes"] += 1
        else:
            perf["failures"] += 1

        perf["total_time"] += result.execution_time
        perf["average_time"] = perf["total_time"] / perf["tasks"]

    async def _process_task(self, state: AgentState) -> Any:
        """Process task through the workflow"""
        try:
            # Execute workflow
            final_state = await self.workflow.ainvoke(state)

            # Handle different return types
            if isinstance(final_state, dict):
                return final_state.get("result", "Task processing completed")
            elif asyncio.iscoroutine(final_state):
                # If it's still a coroutine, await it
                result = await final_state
                if isinstance(result, dict):
                    return result.get("result", "Task processing completed")
                return result
            else:
                return final_state
        except Exception as e:
            logger.error(f"Supervisor workflow error: {e}")
            return {"error": str(e), "status": "failed"}

    async def delegate_complex_task(self, task: str, requirements: dict[str, Any]) -> TaskResult:
        """
        Delegate a complex task that requires multiple agents.

        Args:
            task: Task description
            requirements: Specific requirements and constraints

        Returns:
            Aggregated result from all involved agents
        """
        logger.info(f"Delegating complex task: {task}")

        # Create enriched context
        context = {
            "requirements": requirements,
            "priority": requirements.get("priority", AgentPriority.MEDIUM.value),
            "deadline": requirements.get("deadline"),
            "educational_level": requirements.get("grade_level"),
            "subject": requirements.get("subject"),
        }

        # Execute through supervisor workflow
        result = await self.execute(task, context)

        return result

    def get_agent_status_report(self) -> dict[str, Any]:
        """Get status report for all managed agents"""
        report = {
            "supervisor_status": self.get_status(),
            "managed_agents": {},
            "performance_metrics": self.agent_performance,
            "task_queue_size": len(self.task_queue),
        }

        for name, agent in self.managed_agents.items():
            report["managed_agents"][name] = agent.get_status()

        return report

    async def optimize_agent_allocation(self):
        """Optimize agent allocation based on performance metrics"""
        optimization_prompt = f"""Analyze agent performance and suggest optimizations:

Performance data: {self.agent_performance}

Suggest:
1. Which agents need scaling up/down?
2. Which task types should be re-routed?
3. Any agents that need retraining or updates?
4. Workflow optimizations?"""

        response = await self.llm.ainvoke(optimization_prompt)

        return {
            "optimization_suggestions": response.content,
            "current_performance": self.agent_performance,
            "timestamp": datetime.now().isoformat(),
        }

    def add_managed_agent(self, agent_type: str, agent: BaseAgent):
        """Add a new agent to supervision"""
        self.managed_agents[agent_type] = agent
        logger.info(f"Added {agent_type} to supervision")

    def _handle_plugin_routing(self, state: AgentState) -> str:
        """Handle routing for plugin-specific requests"""
        event_type = state["metadata"].get("event_type", "")

        # Plugin requests typically need delegation
        if event_type in [
            "generate_lesson",
            "create_quiz",
            "build_terrain",
            "content_generation",
        ]:
            return "delegate"
        elif event_type == "get_status":
            return "direct"  # Can be handled directly
        else:
            return "delegate"  # Default to delegation

    def _handle_dashboard_routing(self, state: AgentState) -> str:
        """Handle routing for dashboard requests"""
        request_type = state["metadata"].get("request_type", "")

        if request_type in ["lesson_creation", "quiz_generation"]:
            return "delegate"
        elif request_type in ["analytics", "status"]:
            return "direct"
        else:
            return "delegate"

    def _handle_cicd_routing(self, state: AgentState) -> str:
        """Handle routing for CI/CD pipeline requests"""
        state["metadata"].get("stage", "")

        # All CI/CD stages require delegation
        return "delegate"

    def _get_priority_value(self, priority: str) -> int:
        """Convert priority string to numeric value for sorting"""
        priority_map = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
            "background": 4,
        }
        return priority_map.get(priority.lower(), 2)

    async def _execute_plugin_delegations(
        self, delegations: list[dict], state: AgentState
    ) -> list[dict]:
        """Execute delegations for plugin requests with specific handling"""
        results = []

        # Plugin requests may need parallel execution for performance
        parallel_agents = ["content", "terrain", "quiz"]
        parallel_tasks = []
        sequential_tasks = []

        for delegation in delegations:
            if delegation["agent"] in parallel_agents:
                parallel_tasks.append(delegation)
            else:
                sequential_tasks.append(delegation)

        # Execute parallel tasks
        if parallel_tasks:
            import asyncio

            parallel_results = await asyncio.gather(
                *[self._execute_single_delegation(d, state) for d in parallel_tasks],
                return_exceptions=True,
            )
            for i, result in enumerate(parallel_results):
                if isinstance(result, Exception):
                    logger.error(f"Parallel task failed: {result}")
                    results.append({"agent": parallel_tasks[i]["agent"], "error": str(result)})
                else:
                    results.append(result)

        # Execute sequential tasks
        for delegation in sequential_tasks:
            result = await self._execute_single_delegation(delegation, state)
            results.append(result)

        return results

    async def _execute_dashboard_delegations(
        self, delegations: list[dict], state: AgentState
    ) -> list[dict]:
        """Execute delegations for dashboard requests"""
        results = []

        for delegation in delegations:
            result = await self._execute_single_delegation(delegation, state)
            results.append(result)

            # Update dashboard in real-time
            if state.get("dashboard_callback"):
                await state["dashboard_callback"](result)

        return results

    async def _execute_cicd_delegations(
        self, delegations: list[dict], state: AgentState
    ) -> list[dict]:
        """Execute delegations for CI/CD pipeline requests"""
        results = []

        # CI/CD tasks are typically sequential with validation
        for delegation in delegations:
            result = await self._execute_single_delegation(delegation, state)
            results.append(result)

            # Stop on failure for CI/CD
            if result.get("result") and not result["result"].success:
                logger.error(f"CI/CD task failed: {delegation['task']}")
                break

        return results

    async def _execute_standard_delegations(
        self, delegations: list[dict], state: AgentState
    ) -> list[dict]:
        """Execute standard delegations"""
        results = []

        for delegation in delegations:
            result = await self._execute_single_delegation(delegation, state)
            results.append(result)

        return results

    async def _execute_single_delegation(self, delegation: dict, state: AgentState) -> dict:
        """Execute a single delegation task"""
        agent_type = delegation["agent"]
        subtask = delegation["task"]

        # Get or create agent
        agent = self._get_or_create_agent(agent_type)

        if agent:
            # Execute subtask
            result = await agent.execute(subtask, state["context"])

            # Track performance
            self._track_agent_performance(agent_type, result)

            return {
                "agent": agent_type,
                "task": subtask,
                "result": result,
                "priority": delegation.get("priority", "medium"),
            }
        else:
            logger.warning(f"Agent {agent_type} not available")
            return {
                "agent": agent_type,
                "task": subtask,
                "error": "Agent not available",
            }

    async def handle_plugin_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a request from the Roblox plugin"""
        logger.info(f"Handling plugin request: {request.get('event_type')}")

        # Create state for the request
        state = AgentState(
            task=request.get("task", "Plugin request"),
            messages=[HumanMessage(content=str(request))],
            context=request.get("context", {}),
            metadata={
                "source": "roblox_plugin",
                "event_type": request.get("event_type"),
                "request_id": request.get("request_id"),
                **request.get("metadata", {}),
            },
            status="processing",
        )

        # Process through workflow
        final_state = await self.workflow.ainvoke(state)

        # Format response for plugin
        return {
            "request_id": request.get("request_id"),
            "status": "success" if not final_state.get("error") else "error",
            "result": final_state.get("result"),
            "error": final_state.get("error"),
            "metadata": final_state.get("metadata", {}),
        }

    async def handle_dashboard_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a request from the dashboard"""
        logger.info(f"Handling dashboard request: {request.get('request_type')}")

        # Create state for the request
        state = AgentState(
            task=request.get("task", "Dashboard request"),
            messages=[HumanMessage(content=str(request))],
            context=request.get("context", {}),
            metadata={
                "source": "dashboard",
                "request_type": request.get("request_type"),
                "user_id": request.get("user_id"),
                **request.get("metadata", {}),
            },
            status="processing",
        )

        # Add dashboard callback if provided
        if request.get("callback"):
            state["dashboard_callback"] = request["callback"]

        # Process through workflow
        final_state = await self.workflow.ainvoke(state)

        # Format response for dashboard
        return {
            "request_type": request.get("request_type"),
            "status": "success" if not final_state.get("error") else "error",
            "data": final_state.get("result"),
            "error": final_state.get("error"),
            "metadata": final_state.get("metadata", {}),
        }

    async def handle_cicd_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a request from CI/CD pipeline"""
        logger.info(f"Handling CI/CD request: {request.get('stage')}")

        # Create state for the request
        state = AgentState(
            task=request.get("task", "CI/CD pipeline task"),
            messages=[HumanMessage(content=str(request))],
            context=request.get("context", {}),
            metadata={
                "source": "ci_cd",
                "stage": request.get("stage"),
                "build_id": request.get("build_id"),
                "commit": request.get("commit"),
                **request.get("metadata", {}),
            },
            status="processing",
        )

        # Process through workflow
        final_state = await self.workflow.ainvoke(state)

        # Format response for CI/CD
        return {
            "stage": request.get("stage"),
            "build_id": request.get("build_id"),
            "status": "success" if not final_state.get("error") else "failed",
            "artifacts": final_state.get("result"),
            "error": final_state.get("error"),
            "metadata": final_state.get("metadata", {}),
        }

    async def emergency_stop(self):
        """Emergency stop all agent operations"""
        logger.warning("Emergency stop initiated")

        # Stop all managed agents
        for agent in self.managed_agents.values():
            agent.reset()

        # Clear task queue
        self.task_queue.clear()

        # Reset supervisor
        self.reset()

        return {"status": "All agents stopped", "timestamp": datetime.now().isoformat()}

    async def execute_advanced_workflow(
        self,
        task: str,
        context: dict[str, Any],
        workflow_template: str = "educational_content_generation",
        priority: str = "normal",
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Execute workflow using the Advanced Supervisor Agent.

        This method provides access to the advanced LangGraph workflow orchestration
        with database integration, SPARC framework, and enhanced monitoring.

        Args:
            task: Task description
            context: Task context and requirements
            workflow_template: Template to use for execution
            priority: Workflow priority (critical, high, normal, low, background)
            user_id: Optional user ID for tracking

        Returns:
            Workflow execution results with comprehensive metrics
        """
        try:
            # Import and create advanced supervisor
            from .supervisor_advanced import AdvancedSupervisorAgent, WorkflowPriority

            # Map priority string to enum
            priority_map = {
                "critical": WorkflowPriority.CRITICAL,
                "high": WorkflowPriority.HIGH,
                "normal": WorkflowPriority.NORMAL,
                "low": WorkflowPriority.LOW,
                "background": WorkflowPriority.BACKGROUND,
            }

            priority_enum = priority_map.get(priority.lower(), WorkflowPriority.NORMAL)

            # Create advanced supervisor instance
            advanced_supervisor = AdvancedSupervisorAgent()

            try:
                # Execute advanced workflow
                execution = await advanced_supervisor.execute_workflow(
                    task=task,
                    context=context,
                    workflow_template=workflow_template,
                    priority=priority_enum,
                    user_id=user_id,
                )

                # Format response for compatibility
                return {
                    "status": "success" if execution.status.value == "completed" else "error",
                    "execution_id": execution.execution_id,
                    "workflow_name": execution.workflow_name,
                    "result": execution.result,
                    "error": execution.error,
                    "metrics": execution.metrics,
                    "duration": (
                        (execution.completed_at - execution.started_at).total_seconds()
                        if execution.completed_at
                        else None
                    ),
                    "agents_used": execution.total_agents,
                    "success_rate": (
                        execution.completed_agents / execution.total_agents
                        if execution.total_agents > 0
                        else 0
                    ),
                }

            finally:
                # Graceful shutdown of advanced supervisor
                await advanced_supervisor.shutdown()

        except ImportError:
            logger.warning("Advanced supervisor not available, falling back to basic workflow")
            # Fallback to existing workflow
            return await self._execute_basic_workflow(task, context)
        except Exception as e:
            logger.error(f"Advanced workflow execution failed: {e}")
            return {
                "status": "error",
                "error": f"Advanced workflow failed: {e}",
                "fallback_available": True,
            }

    async def _execute_basic_workflow(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute basic workflow using existing supervisor logic.

        This is a fallback method that uses the original supervisor implementation.
        """
        try:
            # Create AgentState for compatibility
            from langchain_core.messages import HumanMessage

            from .base_agent import AgentState

            state = AgentState(
                task=task,
                messages=[HumanMessage(content=task)],
                context=context,
                metadata={"workflow_type": "basic"},
                status="pending",
            )

            # Execute through existing workflow
            result = await self._process_task(state)

            return {
                "status": "success",
                "result": result,
                "workflow_type": "basic",
                "message": "Executed using basic workflow",
            }

        except Exception as e:
            logger.error(f"Basic workflow execution failed: {e}")
            return {"status": "error", "error": f"Basic workflow failed: {e}"}

    async def get_workflow_templates(self) -> dict[str, Any]:
        """
        Get available workflow templates.

        Returns:
            Dictionary of available workflow templates with descriptions
        """
        return {
            "educational_content_generation": {
                "name": "Educational Content Generation",
                "description": "Complete educational content creation workflow",
                "agents": ["content", "quiz", "terrain", "script", "review"],
                "estimated_duration": "15-30 minutes",
                "complexity": "high",
            },
            "lesson_creation": {
                "name": "Lesson Creation",
                "description": "Create a complete lesson with assessments",
                "agents": ["content", "quiz", "review"],
                "estimated_duration": "10-15 minutes",
                "complexity": "medium",
            },
            "roblox_environment": {
                "name": "Roblox Environment Creation",
                "description": "Build interactive Roblox learning environment",
                "agents": ["terrain", "script", "testing"],
                "estimated_duration": "20-45 minutes",
                "complexity": "high",
            },
            "assessment_generation": {
                "name": "Assessment Generation",
                "description": "Generate comprehensive assessments",
                "agents": ["quiz", "review"],
                "estimated_duration": "5-10 minutes",
                "complexity": "low",
            },
        }

    async def get_system_health(self) -> dict[str, Any]:
        """
        Get comprehensive system health information.

        Returns:
            System health report including agent status and performance metrics
        """
        try:
            from .supervisor_advanced import AdvancedSupervisorAgent

            # Create temporary advanced supervisor for health check
            advanced_supervisor = AdvancedSupervisorAgent()

            try:
                health_report = await advanced_supervisor.get_agent_health_report()
                performance_report = await advanced_supervisor.get_performance_report()

                return {
                    "status": "healthy",
                    "advanced_features_available": True,
                    "agent_health": health_report,
                    "performance": performance_report,
                    "managed_agents": list(self.managed_agents.keys()),
                    "basic_supervisor": self.get_agent_status_report(),
                }

            finally:
                await advanced_supervisor.shutdown()

        except ImportError:
            # Fallback to basic health check
            return {
                "status": "healthy",
                "advanced_features_available": False,
                "basic_supervisor": self.get_agent_status_report(),
                "message": "Advanced features not available, using basic supervisor",
            }
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {
                "status": "degraded",
                "error": f"Health check failed: {e}",
                "basic_supervisor": self.get_agent_status_report(),
            }

    def validate_response(self, response: dict[str, Any]) -> bool:
        """
        Validate response from core.agents.

        Args:
            response: Response dictionary from agent(s)

        Returns:
            True if response is valid, False otherwise
        """
        if not response:
            return False

        # Check for error status
        if response.get("status") == "error":
            return False

        # Check for error field
        if response.get("error"):
            return False

        # For success status, ensure there's actual content
        if response.get("status") == "success":
            # Check for at least one valid content field
            valid_fields = [
                "content",
                "quiz",
                "terrain",
                "scripts",
                "lesson",
                "questions",
                "result",
            ]
            has_content = any(response.get(field) for field in valid_fields)
            return has_content

        # Default to true for other cases
        return True


# Compatibility layer for supervisor_complete and supervisor_advanced
# These are kept for backward compatibility but will be deprecated

# Alias for supervisor_complete.py compatibility
CompleteSupervisorAgent = SupervisorAgent


# Import for supervisor_advanced.py compatibility
# (Advanced features have been integrated into main SupervisorAgent)
class SupervisorAdvanced(SupervisorAgent):
    """
    Deprecated: Use SupervisorAgent instead.
    This class exists only for backward compatibility.
    """

    def __init__(self, *args, **kwargs):
        import warnings

        warnings.warn(
            "SupervisorAdvanced is deprecated. Use SupervisorAgent instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
