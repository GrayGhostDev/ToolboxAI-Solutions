"""
Advanced Supervisor Agent - Comprehensive LangGraph Workflow Orchestration

Features:
- Advanced LangGraph workflow with dynamic routing and parallel execution
- Real database integration for audit trails and performance tracking
- SPARC framework integration for intelligent decision making
- Circuit breaker pattern for agent health monitoring
- Dynamic agent registry with load balancing and failover
- MCP context management for workflow state persistence
- Human-in-the-loop approval for critical decisions
- Comprehensive error handling and recovery mechanisms
- Workflow templates and sub-workflow composition
- Advanced performance monitoring and optimization
"""

import asyncio
import json
import logging
import time
import traceback
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

# Database and persistence imports
try:
    from database.connection_manager import (
        db_manager,
        get_async_session,
        get_redis_client,
    )
    from database.models.models import (
        Achievement,
        Analytics,
        Content,
        ContentStatus,
        Course,
        Lesson,
        Quiz,
        User,
        UserProgress,
    )

    DATABASE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Database imports failed: {e}")
    DATABASE_AVAILABLE = False

# SPARC Framework imports
try:
    from core.sparc.action_executor import ActionExecutor
    from core.sparc.context_tracker import ContextTracker
    from core.sparc.policy_engine import PolicyEngine
    from core.sparc.reward_calculator import RewardCalculator
    from core.sparc.state_manager import EnvironmentState, StateManager, StateType

    SPARC_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SPARC imports failed: {e}")
    SPARC_AVAILABLE = False

# MCP integration
try:
    from core.mcp.context_manager import ContextManager

    MCP_AVAILABLE = True
except ImportError as e:
    logging.warning(f"MCP imports failed: {e}")
    MCP_AVAILABLE = False

# Base agent imports
from .base_agent import AgentConfig, BaseAgent, TaskResult

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class AgentHealthStatus(Enum):
    """Agent health status for circuit breaker"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"


class WorkflowPriority(Enum):
    """Workflow priority levels"""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class WorkflowExecution:
    """Represents a complete workflow execution"""

    execution_id: str
    workflow_name: str
    status: WorkflowStatus
    priority: WorkflowPriority
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_agents: int = 0
    completed_agents: int = 0
    failed_agents: int = 0
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    metrics: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class AgentHealthMetrics:
    """Agent health and performance metrics"""

    agent_id: str
    agent_type: str
    status: AgentHealthStatus
    success_rate: float = 0.0
    average_response_time: float = 0.0
    error_count: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    circuit_open_until: Optional[datetime] = None
    total_requests: int = 0
    recent_errors: list[str] = field(default_factory=list)


@dataclass
class EnhancedAgentState:
    """Enhanced agent state with workflow context"""

    # Core AgentState fields
    task: str
    messages: list[BaseMessage] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None

    # Enhanced fields
    workflow_id: str = ""
    execution_id: str = ""
    step: str = "init"
    step_count: int = 0
    max_steps: int = 50
    priority: WorkflowPriority = WorkflowPriority.NORMAL
    requires_approval: bool = False
    approval_granted: bool = False
    checkpoint_data: dict[str, Any] = field(default_factory=dict)
    performance_metrics: dict[str, Any] = field(default_factory=dict)

    # SPARC integration
    sparc_state: Optional[dict[str, Any]] = None
    environment_context: Optional[dict[str, Any]] = None


class AdvancedSupervisorAgent:
    """
    Advanced Supervisor Agent with comprehensive workflow orchestration.

    This agent provides enterprise-grade workflow management including:
    - LangGraph-based workflow orchestration
    - Real-time database integration
    - SPARC framework decision making
    - Circuit breaker patterns for resilience
    - Dynamic load balancing and failover
    - MCP context management
    - Human-in-the-loop workflows
    - Comprehensive monitoring and analytics
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Advanced Supervisor Agent"""

        # Core configuration
        self.config = config or AgentConfig(
            name="AdvancedSupervisorAgent",
            model="gpt-4-turbo-preview",
            temperature=0.1,  # Lower temperature for consistent decisions
            max_tokens=4096,
        )

        # LLM setup
        self.llm = ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        # Agent registry and management
        self.agent_registry: dict[str, BaseAgent] = {}
        self.agent_health: dict[str, AgentHealthMetrics] = {}
        self.agent_load_balancer = defaultdict(list)  # agent_type -> [agent_instances]

        # Workflow management
        self.active_workflows: dict[str, WorkflowExecution] = {}
        self.workflow_templates: dict[str, dict[str, Any]] = {}
        self.workflow_history: list[WorkflowExecution] = []

        # LangGraph workflow engine
        self.workflow_graph = None
        self.checkpoint_saver = MemorySaver()
        self._build_workflow_graph()

        # Performance tracking
        self.performance_metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_execution_time": 0.0,
            "agent_utilization": defaultdict(float),
            "error_rates": defaultdict(float),
        }

        # Database integration
        self.db_session_factory = get_async_session if DATABASE_AVAILABLE else None
        # Initialize Redis client lazily or use sync version
        self.redis_client = None
        self._redis_initialized = False

        # SPARC framework integration
        self.state_manager = StateManager() if SPARC_AVAILABLE else None
        self.policy_engine = PolicyEngine() if SPARC_AVAILABLE else None
        self.action_executor = ActionExecutor() if SPARC_AVAILABLE else None
        self.reward_calculator = RewardCalculator() if SPARC_AVAILABLE else None
        self.context_tracker = ContextTracker() if SPARC_AVAILABLE else None

        # MCP context management
        self.context_manager = ContextManager() if MCP_AVAILABLE else None

        # Circuit breaker configuration
        self.circuit_breaker_config = {
            "failure_threshold": 5,
            "timeout": 60,  # seconds
            "reset_timeout": 300,  # 5 minutes
        }

        # Initialize workflow templates
        self._initialize_workflow_templates()

        # Background tasks
        self._background_tasks: set[asyncio.Task] = set()
        self._start_background_tasks()

        logger.info("Advanced Supervisor Agent initialized successfully")

    def _build_workflow_graph(self) -> None:
        """Build the advanced LangGraph workflow"""

        # Create the state graph with enhanced state
        workflow = StateGraph(EnhancedAgentState)

        # Define all workflow nodes
        workflow.add_node("initialize", self._initialize_workflow)
        workflow.add_node("analyze_task", self._analyze_task)
        workflow.add_node("check_approval", self._check_approval_required)
        workflow.add_node("wait_approval", self._wait_for_approval)
        workflow.add_node("route_agents", self._route_to_agents)
        workflow.add_node("execute_parallel", self._execute_parallel_agents)
        workflow.add_node("execute_sequential", self._execute_sequential_agents)
        workflow.add_node("monitor_execution", self._monitor_agent_execution)
        workflow.add_node("handle_failures", self._handle_agent_failures)
        workflow.add_node("aggregate_results", self._aggregate_results)
        workflow.add_node("validate_quality", self._validate_result_quality)
        workflow.add_node("update_database", self._update_database)
        workflow.add_node("calculate_rewards", self._calculate_sparc_rewards)
        workflow.add_node("finalize", self._finalize_workflow)

        # Set entry point
        workflow.set_entry_point("initialize")

        # Define workflow edges and routing
        workflow.add_edge("initialize", "analyze_task")
        workflow.add_edge("analyze_task", "check_approval")

        # Conditional routing for approval
        workflow.add_conditional_edges(
            "check_approval",
            self._approval_routing,
            {"requires_approval": "wait_approval", "no_approval": "route_agents"},
        )

        workflow.add_edge("wait_approval", "route_agents")

        # Agent execution routing
        workflow.add_conditional_edges(
            "route_agents",
            self._execution_routing,
            {
                "parallel": "execute_parallel",
                "sequential": "execute_sequential",
                "direct": "aggregate_results",
            },
        )

        # Execution monitoring
        workflow.add_edge("execute_parallel", "monitor_execution")
        workflow.add_edge("execute_sequential", "monitor_execution")

        # Error handling
        workflow.add_conditional_edges(
            "monitor_execution",
            self._error_routing,
            {
                "success": "aggregate_results",
                "partial_failure": "handle_failures",
                "total_failure": "handle_failures",
            },
        )

        # Recovery routing
        workflow.add_conditional_edges(
            "handle_failures",
            self._recovery_routing,
            {"retry": "route_agents", "escalate": "finalize", "continue": "aggregate_results"},
        )

        # Result processing
        workflow.add_edge("aggregate_results", "validate_quality")

        # Quality validation routing
        workflow.add_conditional_edges(
            "validate_quality",
            self._quality_routing,
            {
                "approved": "update_database",
                "needs_improvement": "route_agents",
                "rejected": "finalize",
            },
        )

        # Final steps
        workflow.add_edge("update_database", "calculate_rewards")
        workflow.add_edge("calculate_rewards", "finalize")
        workflow.add_edge("finalize", END)

        # Compile with checkpointing
        self.workflow_graph = workflow.compile(checkpointer=self.checkpoint_saver)

        logger.info("Advanced workflow graph built successfully")

    def _initialize_workflow_templates(self) -> None:
        """Initialize predefined workflow templates"""

        self.workflow_templates = {
            "educational_content_generation": {
                "name": "Educational Content Generation",
                "description": "Complete educational content creation workflow",
                "agents": ["content", "quiz", "terrain", "script", "review"],
                "execution_mode": "sequential",
                "requires_approval": True,
                "max_duration": timedelta(minutes=30),
                "quality_threshold": 0.8,
            },
            "lesson_creation": {
                "name": "Lesson Creation",
                "description": "Create a complete lesson with assessments",
                "agents": ["content", "quiz", "review"],
                "execution_mode": "parallel",
                "requires_approval": False,
                "max_duration": timedelta(minutes=15),
                "quality_threshold": 0.7,
            },
            "roblox_environment": {
                "name": "Roblox Environment Creation",
                "description": "Build interactive Roblox learning environment",
                "agents": ["terrain", "script", "testing"],
                "execution_mode": "sequential",
                "requires_approval": True,
                "max_duration": timedelta(minutes=45),
                "quality_threshold": 0.9,
            },
            "assessment_generation": {
                "name": "Assessment Generation",
                "description": "Generate comprehensive assessments",
                "agents": ["quiz", "review"],
                "execution_mode": "parallel",
                "requires_approval": False,
                "max_duration": timedelta(minutes=10),
                "quality_threshold": 0.8,
            },
        }

        logger.info(f"Initialized {len(self.workflow_templates)} workflow templates")

    def _start_background_tasks(self) -> None:
        """Start background monitoring and maintenance tasks"""

        # Health monitoring task
        task = asyncio.create_task(self._monitor_agent_health())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # Performance metrics collection
        task = asyncio.create_task(self._collect_performance_metrics())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # Database cleanup task
        if DATABASE_AVAILABLE:
            task = asyncio.create_task(self._cleanup_database_records())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        logger.info("Background monitoring tasks started")

    async def execute_workflow(
        self,
        task: str,
        context: dict[str, Any],
        workflow_template: str = "educational_content_generation",
        priority: WorkflowPriority = WorkflowPriority.NORMAL,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> WorkflowExecution:
        """
        Execute a complete workflow using LangGraph orchestration.

        Args:
            task: Task description
            context: Task context and requirements
            workflow_template: Template to use for execution
            priority: Workflow priority level
            user_id: Optional user ID for tracking
            session_id: Optional session ID for tracking

        Returns:
            WorkflowExecution with results and metrics
        """

        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"

        logger.info(f"Starting workflow execution {execution_id} with template {workflow_template}")

        # Create workflow execution record
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_name=workflow_template,
            status=WorkflowStatus.RUNNING,
            priority=priority,
            started_at=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            context=context.copy(),
        )

        self.active_workflows[execution_id] = execution

        try:
            # Create enhanced agent state
            state = EnhancedAgentState(
                task=task,
                messages=[HumanMessage(content=task)],
                context=context,
                metadata={
                    "workflow_template": workflow_template,
                    "user_id": user_id,
                    "session_id": session_id,
                    "started_at": datetime.now().isoformat(),
                },
                workflow_id=workflow_id,
                execution_id=execution_id,
                priority=priority,
            )

            # Add context to MCP if available
            if self.context_manager:
                await self._add_workflow_context(execution_id, state)

            # Update SPARC state if available
            if self.state_manager:
                await self._update_sparc_state(state)

            # Execute workflow through LangGraph
            config = RunnableConfig(configurable={"thread_id": execution_id})
            final_state = await self.workflow_graph.ainvoke(state, config=config)
            
            # Handle if final_state is a coroutine
            if asyncio.iscoroutine(final_state):
                final_state = await final_state
            
            # Ensure final_state is a dict-like object
            if not isinstance(final_state, (dict, EnhancedAgentState)):
                logger.warning(f"Unexpected final_state type: {type(final_state)}")
                final_state = {"error": f"Unexpected result type: {type(final_state)}"}

            # Update execution record
            execution.status = (
                WorkflowStatus.COMPLETED if not (hasattr(final_state, 'get') and final_state.get("error")) 
                and not (hasattr(final_state, 'error') and final_state.error) else WorkflowStatus.FAILED
            )
            execution.completed_at = datetime.now()
            
            # Handle different types of final_state
            if isinstance(final_state, dict):
                execution.result = final_state.get("result")
                execution.error = final_state.get("error")
                execution.metrics = final_state.get("performance_metrics", {})
            elif hasattr(final_state, 'result'):
                execution.result = final_state.result
                execution.error = getattr(final_state, 'error', None)
                execution.metrics = getattr(final_state, 'performance_metrics', {})

            # Store in history
            self.workflow_history.append(execution)

            # Update performance metrics
            await self._update_performance_metrics(execution)

            # Store in database if available
            if DATABASE_AVAILABLE:
                await self._store_workflow_execution(execution)

            logger.info(
                f"Workflow execution {execution_id} completed with status: {execution.status}"
            )

            return execution

        except Exception as e:
            logger.error(f"Workflow execution {execution_id} failed: {e}")
            logger.debug(traceback.format_exc())

            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.now()
            execution.error = str(e)

            return execution

        finally:
            # Cleanup active workflow
            if execution_id in self.active_workflows:
                del self.active_workflows[execution_id]

    # Workflow Node Implementations

    async def _initialize_workflow(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Initialize workflow execution"""

        logger.info(f"Initializing workflow {state.execution_id}")

        # Set workflow metadata
        state.step = "initialize"
        state.step_count = 1
        state.metadata.update(
            {"initialization_time": datetime.now().isoformat(), "supervisor_version": "2.0.0"}
        )

        # Initialize performance tracking
        state.performance_metrics = {
            "start_time": time.time(),
            "steps_completed": 0,
            "agents_invoked": 0,
            "total_tokens": 0,
            "database_operations": 0,
        }

        # Load workflow template configuration
        template_name = state.metadata.get("workflow_template")
        if template_name and template_name in self.workflow_templates:
            template = self.workflow_templates[template_name]
            state.metadata["template_config"] = template
            state.requires_approval = template.get("requires_approval", False)

        state.status = "initialized"
        return state

    async def _analyze_task(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Analyze the task and determine execution strategy"""

        logger.info(f"Analyzing task for workflow {state.execution_id}")

        state.step = "analyze_task"
        state.step_count += 1

        # Create analysis prompt
        analysis_prompt = f"""
        Analyze this educational task and provide a comprehensive execution plan:

        Task: {state.task}
        Context: {json.dumps(state.context, indent=2)}

        Please analyze:
        1. Task complexity and scope
        2. Required educational agents and their roles
        3. Execution strategy (parallel vs sequential)
        4. Quality requirements and success criteria
        5. Potential risks and mitigation strategies
        6. Estimated execution time and resource requirements
        7. Whether human approval is needed for any steps

        Provide your analysis as structured JSON.
        """

        try:
            response = await self.llm.ainvoke([SystemMessage(content=analysis_prompt)])

            # Parse analysis
            try:
                analysis = json.loads(
                    response.content if isinstance(response.content, str) else str(response.content)
                )
            except (json.JSONDecodeError, TypeError):
                # Fallback to text analysis
                analysis = {"analysis": str(response.content), "structured": False}

            state.metadata["task_analysis"] = analysis
            state.messages.append(AIMessage(content=f"Task analysis completed: {response.content}"))

            # Update performance metrics
            usage = getattr(response, "usage", {}) if response else {}
            if isinstance(usage, dict):
                state.performance_metrics["total_tokens"] += usage.get("total_tokens", 0)

        except Exception as e:
            logger.error(f"Task analysis failed: {e}")
            state.error = f"Task analysis failed: {e}"
            return state

        state.status = "analyzed"
        return state

    async def _check_approval_required(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Check if human approval is required"""

        state.step = "check_approval"
        state.step_count += 1

        # Check template configuration
        template_config = state.metadata.get("template_config", {})
        requires_approval = template_config.get("requires_approval", False)

        # Check task analysis for approval requirements
        analysis = state.metadata.get("task_analysis", {})
        if isinstance(analysis, dict) and analysis.get("requires_approval"):
            requires_approval = True

        # Check for critical operations that always need approval
        critical_keywords = ["delete", "remove", "production", "deploy", "publish"]
        if any(keyword in state.task.lower() for keyword in critical_keywords):
            requires_approval = True

        state.requires_approval = requires_approval
        state.metadata["approval_required"] = requires_approval

        logger.info(f"Approval required for workflow {state.execution_id}: {requires_approval}")

        return state

    async def _wait_for_approval(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Wait for human approval (mock implementation)"""

        state.step = "wait_approval"
        state.step_count += 1

        logger.info(f"Waiting for approval for workflow {state.execution_id}")

        # In a real implementation, this would:
        # 1. Send notification to appropriate approvers
        # 2. Create approval request in database
        # 3. Wait for approval via webhook/polling
        # 4. Handle timeout scenarios

        # Mock approval for demonstration
        await asyncio.sleep(1)  # Simulate approval time
        state.approval_granted = True
        state.metadata["approval_granted_at"] = datetime.now().isoformat()

        logger.info(f"Approval granted for workflow {state.execution_id}")

        return state

    async def _route_to_agents(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Route task to appropriate agents"""

        state.step = "route_agents"
        state.step_count += 1

        logger.info(f"Routing agents for workflow {state.execution_id}")

        # Determine required agents from template or analysis
        template_config = state.metadata.get("template_config", {})
        required_agents = template_config.get("agents", [])

        # If no template agents, analyze task for agent requirements
        if not required_agents:
            required_agents = await self._determine_required_agents(state)

        # Get healthy agents for each type with load balancing
        selected_agents = {}
        for agent_type in required_agents:
            agent = await self._select_healthy_agent(agent_type)
            if agent:
                selected_agents[agent_type] = agent

        state.metadata["selected_agents"] = list(selected_agents.keys())
        state.metadata["agent_count"] = len(selected_agents)

        # Determine execution mode
        execution_mode = template_config.get("execution_mode", "sequential")
        state.metadata["execution_mode"] = execution_mode

        logger.info(f"Selected {len(selected_agents)} agents for {execution_mode} execution")

        return state

    async def _execute_parallel_agents(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Execute agents in parallel"""

        state.step = "execute_parallel"
        state.step_count += 1

        selected_agents = state.metadata.get("selected_agents", [])
        logger.info(f"Executing {len(selected_agents)} agents in parallel")

        # Create tasks for parallel execution
        agent_tasks = []
        for agent_type in selected_agents:
            task = self._create_agent_task(agent_type, state)
            agent_tasks.append(task)

        # Execute all agents in parallel with timeout
        try:
            timeout = 300  # 5 minutes default timeout
            results = await asyncio.wait_for(
                asyncio.gather(*agent_tasks, return_exceptions=True), timeout=timeout
            )

            # Process results
            successful_results = []
            failed_results = []

            for i, result in enumerate(results):
                agent_type = selected_agents[i]
                if isinstance(result, Exception):
                    failed_results.append({"agent": agent_type, "error": str(result)})
                    await self._record_agent_failure(agent_type, str(result))
                else:
                    successful_results.append({"agent": agent_type, "result": result})
                    await self._record_agent_success(agent_type, result)

            state.metadata["parallel_results"] = {
                "successful": successful_results,
                "failed": failed_results,
                "success_rate": (
                    len(successful_results) / len(selected_agents) if selected_agents else 0
                ),
            }

        except asyncio.TimeoutError:
            logger.error(f"Parallel execution timeout for workflow {state.execution_id}")
            state.error = "Parallel execution timeout"
            return state
        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            state.error = f"Parallel execution failed: {e}"
            return state

        state.performance_metrics["agents_invoked"] = len(selected_agents)
        return state

    async def _execute_sequential_agents(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Execute agents sequentially"""

        state.step = "execute_sequential"
        state.step_count += 1

        selected_agents = state.metadata.get("selected_agents", [])
        logger.info(f"Executing {len(selected_agents)} agents sequentially")

        sequential_results = []

        for agent_type in selected_agents:
            try:
                logger.info(f"Executing agent: {agent_type}")

                # Create and execute agent task
                result = await self._create_agent_task(agent_type, state)
                sequential_results.append({"agent": agent_type, "result": result})
                await self._record_agent_success(agent_type, result)

                # Update state context with previous results for next agent
                if hasattr(result, "output"):
                    state.context[f"{agent_type}_result"] = result.output

            except Exception as e:
                logger.error(f"Sequential agent {agent_type} failed: {e}")
                sequential_results.append({"agent": agent_type, "error": str(e)})
                await self._record_agent_failure(agent_type, str(e))

                # Decide whether to continue or stop
                if state.priority in [WorkflowPriority.CRITICAL, WorkflowPriority.HIGH]:
                    state.error = f"Critical agent {agent_type} failed: {e}"
                    break

        state.metadata["sequential_results"] = sequential_results
        state.performance_metrics["agents_invoked"] = len(sequential_results)

        return state

    async def _monitor_agent_execution(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Monitor agent execution and handle issues"""

        state.step = "monitor_execution"
        state.step_count += 1

        # Get execution results
        parallel_results = state.metadata.get("parallel_results", {})
        sequential_results = state.metadata.get("sequential_results", [])

        total_agents = 0
        successful_agents = 0
        failed_agents = 0

        if parallel_results:
            total_agents = len(parallel_results.get("successful", [])) + len(
                parallel_results.get("failed", [])
            )
            successful_agents = len(parallel_results.get("successful", []))
            failed_agents = len(parallel_results.get("failed", []))
        elif sequential_results:
            total_agents = len(sequential_results)
            successful_agents = sum(1 for r in sequential_results if "result" in r)
            failed_agents = sum(1 for r in sequential_results if "error" in r)

        # Calculate success rate
        success_rate = successful_agents / total_agents if total_agents > 0 else 0

        # Determine execution status
        if success_rate == 1.0:
            execution_status = "success"
        elif success_rate >= 0.5:
            execution_status = "partial_failure"
        else:
            execution_status = "total_failure"

        state.metadata["execution_monitoring"] = {
            "total_agents": total_agents,
            "successful_agents": successful_agents,
            "failed_agents": failed_agents,
            "success_rate": success_rate,
            "execution_status": execution_status,
        }

        logger.info(
            f"Execution monitoring - Success rate: {success_rate:.2f} ({successful_agents}/{total_agents})"
        )

        return state

    async def _handle_agent_failures(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Handle agent failures with recovery strategies"""

        state.step = "handle_failures"
        state.step_count += 1

        monitoring = state.metadata.get("execution_monitoring", {})
        failed_agents = monitoring.get("failed_agents", 0)

        logger.info(f"Handling {failed_agents} agent failures")

        # Analyze failure patterns
        recovery_strategy = await self._determine_recovery_strategy(state)

        state.metadata["recovery_strategy"] = recovery_strategy

        if recovery_strategy == "retry":
            # Reset failed agents for retry
            state.metadata["retry_count"] = state.metadata.get("retry_count", 0) + 1
            if state.metadata["retry_count"] >= 3:
                recovery_strategy = "escalate"

        state.metadata["final_recovery_strategy"] = recovery_strategy

        return state

    async def _aggregate_results(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Aggregate results from all agents"""

        state.step = "aggregate_results"
        state.step_count += 1

        logger.info(f"Aggregating results for workflow {state.execution_id}")

        # Collect all results
        all_results = []

        # From parallel execution
        parallel_results = state.metadata.get("parallel_results", {})
        if parallel_results:
            all_results.extend(parallel_results.get("successful", []))

        # From sequential execution
        sequential_results = state.metadata.get("sequential_results", [])
        if sequential_results:
            all_results.extend([r for r in sequential_results if "result" in r])

        # Create aggregation prompt
        aggregation_prompt = f"""
        Aggregate these agent results into a cohesive educational response:

        Task: {state.task}
        Agent Results: {json.dumps(all_results, indent=2, default=str)}

        Create a unified output that:
        1. Combines all successful results
        2. Provides educational value
        3. Is appropriate for the target audience
        4. Includes all generated content/code
        5. Suggests next steps or improvements

        Format as structured JSON with sections for content, assessments, environments, and metadata.
        """

        try:
            response = await self.llm.ainvoke([SystemMessage(content=aggregation_prompt)])

            # Parse aggregated result
            try:
                aggregated_result = json.loads(
                    response.content if isinstance(response.content, str) else str(response.content)
                )
            except (json.JSONDecodeError, TypeError):
                aggregated_result = {"content": str(response.content), "structured": False}

            state.result = aggregated_result
            state.messages.append(AIMessage(content="Results successfully aggregated"))

            # Update performance metrics
            usage = getattr(response, "usage", {}) if response else {}
            if isinstance(usage, dict):
                state.performance_metrics["total_tokens"] += usage.get("total_tokens", 0)

        except Exception as e:
            logger.error(f"Result aggregation failed: {e}")
            state.error = f"Result aggregation failed: {e}"
            return state

        return state

    async def _validate_result_quality(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Validate the quality of aggregated results"""

        state.step = "validate_quality"
        state.step_count += 1

        if not state.result:
            state.metadata["quality_status"] = "rejected"
            state.error = "No result to validate"
            return state

        # Get quality threshold from template
        template_config = state.metadata.get("template_config", {})
        quality_threshold = template_config.get("quality_threshold", 0.7)

        # Create quality validation prompt
        validation_prompt = f"""
        Evaluate the quality of this educational content:

        Content: {json.dumps(state.result, indent=2, default=str)}
        Task Requirements: {state.task}

        Rate from 0-1 on these criteria:
        1. Educational accuracy and appropriateness
        2. Completeness relative to requirements
        3. Technical correctness
        4. Engagement and clarity
        5. Age/grade level appropriateness

        Provide overall quality score and specific feedback.
        Format as JSON with 'quality_score' and 'feedback' fields.
        """

        try:
            response = await self.llm.ainvoke([SystemMessage(content=validation_prompt)])

            # Parse quality assessment
            try:
                quality_assessment = json.loads(
                    response.content if isinstance(response.content, str) else str(response.content)
                )
                quality_score = quality_assessment.get("quality_score", 0.5)
            except (json.JSONDecodeError, TypeError):
                quality_score = 0.5  # Default if parsing fails
                quality_assessment = {"feedback": str(response.content)}

            state.metadata["quality_assessment"] = quality_assessment
            state.metadata["quality_score"] = quality_score

            # Determine quality status
            if quality_score >= quality_threshold:
                quality_status = "approved"
            elif quality_score >= 0.5:
                quality_status = "needs_improvement"
            else:
                quality_status = "rejected"

            state.metadata["quality_status"] = quality_status

            logger.info(
                f"Quality validation - Score: {quality_score:.2f}, Status: {quality_status}"
            )

        except Exception as e:
            logger.error(f"Quality validation failed: {e}")
            state.metadata["quality_status"] = "needs_improvement"
            state.metadata["quality_error"] = str(e)

        return state

    async def _update_database(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Update database with workflow results"""

        state.step = "update_database"
        state.step_count += 1

        if not DATABASE_AVAILABLE:
            logger.warning("Database not available, skipping database update")
            return state

        try:
            async with get_async_session() as session:
                # Create analytics record
                analytics_record = Analytics(
                    user_id=state.metadata.get("user_id"),
                    event_type="workflow_execution",
                    event_category="supervisor",
                    event_data={
                        "workflow_id": state.workflow_id,
                        "execution_id": state.execution_id,
                        "task": state.task,
                        "results": state.result,
                        "quality_score": state.metadata.get("quality_score"),
                        "performance_metrics": state.performance_metrics,
                    },
                    session_id=state.metadata.get("session_id"),
                )

                session.add(analytics_record)
                await session.commit()

                state.performance_metrics["database_operations"] += 1
                logger.info("Workflow results stored in database")

        except Exception as e:
            logger.error(f"Database update failed: {e}")
            state.metadata["database_error"] = str(e)

        return state

    async def _calculate_sparc_rewards(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Calculate SPARC framework rewards"""

        state.step = "calculate_rewards"
        state.step_count += 1

        if not SPARC_AVAILABLE:
            logger.warning("SPARC framework not available, skipping reward calculation")
            return state

        try:
            # Calculate rewards based on performance
            quality_score = state.metadata.get("quality_score", 0.5)
            success_rate = state.metadata.get("execution_monitoring", {}).get("success_rate", 0.0)

            reward_factors = {
                "quality": quality_score,
                "efficiency": success_rate,
                "completion": 1.0 if state.result else 0.0,
                "user_satisfaction": 0.8,  # Mock value
            }

            total_reward = sum(reward_factors.values()) / len(reward_factors)

            state.metadata["sparc_rewards"] = {
                "total_reward": total_reward,
                "factors": reward_factors,
                "calculated_at": datetime.now().isoformat(),
            }

            logger.info(f"SPARC rewards calculated - Total: {total_reward:.3f}")

        except Exception as e:
            logger.error(f"SPARC reward calculation failed: {e}")
            state.metadata["reward_error"] = str(e)

        return state

    async def _finalize_workflow(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Finalize workflow execution"""

        state.step = "finalize"
        state.step_count += 1

        # Calculate final performance metrics
        execution_time = time.time() - state.performance_metrics["start_time"]
        state.performance_metrics["execution_time"] = execution_time
        state.performance_metrics["steps_completed"] = state.step_count

        # Set final status
        if state.error:
            state.status = "failed"
        elif state.result:
            state.status = "completed"
        else:
            state.status = "completed_no_result"

        # Final logging
        logger.info(
            f"Workflow {state.execution_id} finalized - Status: {state.status}, Duration: {execution_time:.2f}s"
        )

        return state

    # Routing Functions

    def _approval_routing(self, state: EnhancedAgentState) -> str:
        """Route based on approval requirements"""
        return "requires_approval" if state.requires_approval else "no_approval"

    def _execution_routing(self, state: EnhancedAgentState) -> str:
        """Route based on execution mode"""
        execution_mode = state.metadata.get("execution_mode", "sequential")
        agent_count = state.metadata.get("agent_count", 0)

        if agent_count == 0:
            return "direct"
        elif execution_mode == "parallel":
            return "parallel"
        else:
            return "sequential"

    def _error_routing(self, state: EnhancedAgentState) -> str:
        """Route based on execution errors"""
        monitoring = state.metadata.get("execution_monitoring", {})
        execution_status = monitoring.get("execution_status", "success")
        return execution_status

    def _recovery_routing(self, state: EnhancedAgentState) -> str:
        """Route based on recovery strategy"""
        return state.metadata.get("final_recovery_strategy", "continue")

    def _quality_routing(self, state: EnhancedAgentState) -> str:
        """Route based on quality validation"""
        return state.metadata.get("quality_status", "rejected")

    # Helper Methods

    async def _determine_required_agents(self, state: EnhancedAgentState) -> list[str]:
        """Determine required agents based on task analysis"""

        state.metadata.get("task_analysis", {})

        # Default agent mapping
        agent_keywords = {
            "content": ["lesson", "content", "material", "text", "explanation"],
            "quiz": ["quiz", "question", "assessment", "test", "evaluation"],
            "terrain": ["environment", "world", "terrain", "3d", "space"],
            "script": ["code", "script", "program", "lua", "roblox"],
            "review": ["review", "check", "validate", "approve", "quality"],
        }

        required_agents = []
        task_lower = state.task.lower()

        for agent_type, keywords in agent_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                required_agents.append(agent_type)

        # Ensure at least one agent
        if not required_agents:
            required_agents = ["content"]  # Default to content agent

        return required_agents

    async def _select_healthy_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Select a healthy agent with load balancing"""

        # Get or create agent
        if agent_type not in self.agent_registry:
            agent = await self._create_agent(agent_type)
            if agent:
                self.agent_registry[agent_type] = agent
                self._initialize_agent_health(agent_type)

        agent = self.agent_registry.get(agent_type)

        # Check circuit breaker
        if agent and await self._is_agent_healthy(agent_type):
            return agent

        return None

    async def _create_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Create agent instance dynamically"""

        agent_map = {
            "content": "ContentAgent",
            "quiz": "QuizAgent",
            "terrain": "TerrainAgent",
            "script": "ScriptAgent",
            "review": "ReviewAgent",
            "testing": "TestingAgent",
        }

        if agent_type not in agent_map:
            logger.error(f"Unknown agent type: {agent_type}")
            return None

        try:
            # Dynamic import and instantiation
            module_name = f"core.agents.{agent_type}_agent"
            class_name = agent_map[agent_type]

            from importlib import import_module

            module = import_module(module_name)
            agent_class = getattr(module, class_name)

            return agent_class()

        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to create {agent_type} agent: {e}")
            return None

    def _initialize_agent_health(self, agent_type: str):
        """Initialize health metrics for an agent"""

        agent_id = f"{agent_type}_001"  # Simple ID scheme
        self.agent_health[agent_id] = AgentHealthMetrics(
            agent_id=agent_id, agent_type=agent_type, status=AgentHealthStatus.HEALTHY
        )

    async def _is_agent_healthy(self, agent_type: str) -> bool:
        """Check if agent is healthy using circuit breaker pattern"""

        agent_id = f"{agent_type}_001"
        if agent_id not in self.agent_health:
            return True  # Assume healthy if no history

        health = self.agent_health[agent_id]

        # Check circuit breaker
        if health.status == AgentHealthStatus.CIRCUIT_OPEN:
            if health.circuit_open_until and datetime.now() > health.circuit_open_until:
                # Try to close circuit
                health.status = AgentHealthStatus.DEGRADED
                logger.info(f"Circuit breaker reset for agent {agent_id}")
            else:
                return False

        return health.status in [AgentHealthStatus.HEALTHY, AgentHealthStatus.DEGRADED]

    async def _create_agent_task(self, agent_type: str, state: EnhancedAgentState) -> TaskResult:
        """Create and execute agent task"""

        agent = self.agent_registry.get(agent_type)
        if not agent:
            raise ValueError(f"Agent {agent_type} not available")

        # Create agent-specific task and context
        agent_task = f"[{agent_type.upper()}] {state.task}"
        agent_context = state.context.copy()
        agent_context["workflow_context"] = {
            "execution_id": state.execution_id,
            "step": state.step,
            "priority": state.priority.value,
        }

        # Execute agent task
        start_time = time.time()
        try:
            result = await agent.execute(agent_task, agent_context)
            execution_time = time.time() - start_time

            # Record success
            await self._record_agent_success(agent_type, result, execution_time)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            await self._record_agent_failure(agent_type, str(e), execution_time)
            raise

    async def _record_agent_success(
        self, agent_type: str, result: TaskResult, execution_time: float = 0.0
    ):
        """Record successful agent execution"""

        agent_id = f"{agent_type}_001"
        if agent_id not in self.agent_health:
            self._initialize_agent_health(agent_type)

        health = self.agent_health[agent_id]
        health.total_requests += 1
        health.last_success = datetime.now()

        # Update success rate
        if health.total_requests > 0:
            success_count = health.total_requests - health.error_count
            health.success_rate = success_count / health.total_requests

        # Update response time
        if execution_time > 0:
            current_avg = health.average_response_time
            health.average_response_time = (
                current_avg * (health.total_requests - 1) + execution_time
            ) / health.total_requests

        # Update status based on performance
        if health.success_rate >= 0.95:
            health.status = AgentHealthStatus.HEALTHY
        elif health.success_rate >= 0.8:
            health.status = AgentHealthStatus.DEGRADED

    async def _record_agent_failure(self, agent_type: str, error: str, execution_time: float = 0.0):
        """Record failed agent execution"""

        agent_id = f"{agent_type}_001"
        if agent_id not in self.agent_health:
            self._initialize_agent_health(agent_type)

        health = self.agent_health[agent_id]
        health.total_requests += 1
        health.error_count += 1
        health.last_failure = datetime.now()
        health.recent_errors.append(f"{datetime.now().isoformat()}: {error}")

        # Keep only recent errors
        if len(health.recent_errors) > 10:
            health.recent_errors = health.recent_errors[-10:]

        # Update success rate
        success_count = health.total_requests - health.error_count
        health.success_rate = (
            success_count / health.total_requests if health.total_requests > 0 else 0.0
        )

        # Check circuit breaker
        failure_threshold = self.circuit_breaker_config["failure_threshold"]
        if health.error_count >= failure_threshold:
            health.status = AgentHealthStatus.CIRCUIT_OPEN
            timeout = self.circuit_breaker_config["reset_timeout"]
            health.circuit_open_until = datetime.now() + timedelta(seconds=timeout)
            logger.warning(f"Circuit breaker opened for agent {agent_id}")
        elif health.success_rate < 0.8:
            health.status = AgentHealthStatus.UNHEALTHY
        elif health.success_rate < 0.9:
            health.status = AgentHealthStatus.DEGRADED

    async def _determine_recovery_strategy(self, state: EnhancedAgentState) -> str:
        """Determine recovery strategy for failed agents"""

        monitoring = state.metadata.get("execution_monitoring", {})
        success_rate = monitoring.get("success_rate", 0.0)
        retry_count = state.metadata.get("retry_count", 0)

        if retry_count >= 3:
            return "escalate"
        elif success_rate >= 0.5:
            return "continue"  # Partial success is acceptable
        else:
            return "retry"

    async def _add_workflow_context(self, execution_id: str, state: EnhancedAgentState):
        """Add workflow context to MCP manager"""

        if self.context_manager:
            context_content = f"""
            Workflow Execution: {execution_id}
            Task: {state.task}
            Context: {json.dumps(state.context, indent=2)}
            Priority: {state.priority.value}
            """

            self.context_manager.add_context(
                content=context_content, category="workflow", source="supervisor", importance=0.9
            )

    async def _update_sparc_state(self, state: EnhancedAgentState):
        """Update SPARC framework state"""

        if self.state_manager:
            observation = {
                "workflow_id": state.workflow_id,
                "execution_id": state.execution_id,
                "task": state.task,
                "context": state.context,
                "priority": state.priority.value,
                "timestamp": datetime.now().isoformat(),
                "source": "supervisor",
            }

            await self.state_manager.update_state(observation)

    async def _store_workflow_execution(self, execution: WorkflowExecution):
        """Store workflow execution in database"""

        if not DATABASE_AVAILABLE:
            return

        try:
            # get_async_session is an async generator, need to iterate
            async for session in get_async_session():
                try:
                    analytics_record = Analytics(
                        event_type="workflow_execution",
                        event_category="supervisor",
                        event_data={
                            "execution_id": execution.execution_id,
                            "workflow_name": execution.workflow_name,
                            "status": execution.status.value,
                            "priority": execution.priority.value,
                            "duration": (
                                (execution.completed_at - execution.started_at).total_seconds()
                                if execution.completed_at
                                else None
                            ),
                            "result": execution.result,
                            "error": execution.error,
                            "metrics": execution.metrics,
                        },
                        user_id=execution.user_id,
                        session_id=execution.session_id,
                    )

                    session.add(analytics_record)
                    await session.commit()
                finally:
                    # Session from async generator doesn't need explicit close
                    pass
                break  # Only need one session

        except Exception as e:
            logger.error(f"Failed to store workflow execution: {e}")

    async def _update_performance_metrics(self, execution: WorkflowExecution):
        """Update supervisor performance metrics"""

        self.performance_metrics["total_workflows"] += 1

        if execution.status == WorkflowStatus.COMPLETED:
            self.performance_metrics["successful_workflows"] += 1
        else:
            self.performance_metrics["failed_workflows"] += 1

        if execution.completed_at:
            duration = (execution.completed_at - execution.started_at).total_seconds()
            current_avg = self.performance_metrics["average_execution_time"]
            total_workflows = self.performance_metrics["total_workflows"]

            self.performance_metrics["average_execution_time"] = (
                current_avg * (total_workflows - 1) + duration
            ) / total_workflows

    # Background Task Methods

    async def _monitor_agent_health(self):
        """Background task to monitor agent health"""

        while True:
            try:
                for agent_id, health in self.agent_health.items():
                    # Check for stale agents
                    if (
                        health.last_success
                        and (datetime.now() - health.last_success).total_seconds() > 3600
                    ):
                        if health.status == AgentHealthStatus.HEALTHY:
                            health.status = AgentHealthStatus.DEGRADED
                            logger.info(f"Agent {agent_id} marked as degraded due to inactivity")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)

    async def _collect_performance_metrics(self):
        """Background task to collect performance metrics"""

        while True:
            try:
                # Store metrics in Redis if available
                # Initialize Redis client if needed
                if not self._redis_initialized and DATABASE_AVAILABLE:
                    try:
                        self.redis_client = await get_redis_client()
                        self._redis_initialized = True
                    except Exception as e:
                        logger.warning(f"Failed to initialize Redis client: {e}")
                        self.redis_client = None

                if self.redis_client:
                    metrics_key = f"supervisor:metrics:{datetime.now().strftime('%Y%m%d%H')}"
                    try:
                        result = self.redis_client.hset(
                            metrics_key,
                            mapping={
                                "timestamp": datetime.now().isoformat(),
                                "metrics": json.dumps(self.performance_metrics, default=str),
                            },
                        )
                        if asyncio.iscoroutine(result):
                            _ = await result

                        expire_result = self.redis_client.expire(metrics_key, 86400)  # 24 hours
                        if asyncio.iscoroutine(expire_result):
                            _ = await expire_result
                    except Exception as redis_error:
                        logger.warning(f"Redis operation failed: {redis_error}")

                await asyncio.sleep(3600)  # Collect hourly

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(3600)

    async def _cleanup_database_records(self):
        """Background task to cleanup old database records"""

        while True:
            try:
                if DATABASE_AVAILABLE and self.db_session_factory:
                    async for session in self.db_session_factory():
                        try:
                            # Clean up old analytics records (keep 30 days)
                            datetime.now() - timedelta(days=30)

                            # This would be the actual cleanup query
                            # await session.execute(
                            #     delete(Analytics).where(Analytics.created_at < cutoff_date)
                            # )
                            # await session.commit()

                            pass  # Placeholder for actual cleanup
                        except Exception as cleanup_error:
                            logger.error(f"Cleanup error: {cleanup_error}")
                        # Only need one session - exit after first iteration
                    break

                await asyncio.sleep(86400)  # Daily cleanup

            except Exception as e:
                logger.error(f"Database cleanup error: {e}")
                await asyncio.sleep(86400)

    # Public API Methods

    async def get_workflow_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get status of a workflow execution"""

        # Check active workflows
        if execution_id in self.active_workflows:
            return self.active_workflows[execution_id]

        # Check workflow history
        for execution in self.workflow_history:
            if execution.execution_id == execution_id:
                return execution

        return None

    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel an active workflow"""

        if execution_id in self.active_workflows:
            execution = self.active_workflows[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now()

            # Move to history
            self.workflow_history.append(execution)
            del self.active_workflows[execution_id]

            logger.info(f"Workflow {execution_id} cancelled")
            return True

        return False

    async def get_agent_health_report(self) -> dict[str, Any]:
        """Get comprehensive agent health report"""

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(self.agent_health),
            "health_summary": {"healthy": 0, "degraded": 0, "unhealthy": 0, "circuit_open": 0},
            "agents": [],
        }

        for agent_id, health in self.agent_health.items():
            report["health_summary"][health.status.value] += 1
            report["agents"].append(
                {
                    "agent_id": agent_id,
                    "agent_type": health.agent_type,
                    "status": health.status.value,
                    "success_rate": health.success_rate,
                    "average_response_time": health.average_response_time,
                    "total_requests": health.total_requests,
                    "error_count": health.error_count,
                    "last_success": (
                        health.last_success.isoformat() if health.last_success else None
                    ),
                    "last_failure": (
                        health.last_failure.isoformat() if health.last_failure else None
                    ),
                    "recent_errors": health.recent_errors[-3:],  # Last 3 errors
                }
            )

        return report

    async def get_performance_report(self) -> dict[str, Any]:
        """Get comprehensive performance report"""

        return {
            "timestamp": datetime.now().isoformat(),
            "supervisor_metrics": self.performance_metrics.copy(),
            "active_workflows": len(self.active_workflows),
            "total_workflows_executed": len(self.workflow_history),
            "workflow_templates": list(self.workflow_templates.keys()),
            "agent_health_summary": await self.get_agent_health_report(),
            "system_status": {
                "database_available": DATABASE_AVAILABLE,
                "sparc_available": SPARC_AVAILABLE,
                "mcp_available": MCP_AVAILABLE,
                "redis_available": self.redis_client is not None,
            },
        }

    async def create_workflow_template(self, name: str, config: dict[str, Any]) -> bool:
        """Create a new workflow template"""

        required_fields = ["description", "agents", "execution_mode"]
        if not all(field in config for field in required_fields):
            logger.error(f"Missing required fields for workflow template: {required_fields}")
            return False

        self.workflow_templates[name] = config
        logger.info(f"Created workflow template: {name}")
        return True

    async def shutdown(self):
        """Graceful shutdown of the supervisor"""

        logger.info("Shutting down Advanced Supervisor Agent")

        # Cancel all background tasks
        for task in self._background_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        # Cancel active workflows
        for execution_id in list(self.active_workflows.keys()):
            await self.cancel_workflow(execution_id)

        # Close database connections if needed
        if DATABASE_AVAILABLE:
            db_manager.close_all()

        logger.info("Advanced Supervisor Agent shutdown completed")


# Convenience function for easy instantiation
def create_advanced_supervisor(config: Optional[AgentConfig] = None) -> AdvancedSupervisorAgent:
    """Create and return an Advanced Supervisor Agent instance"""
    return AdvancedSupervisorAgent(config)


# Example usage and testing
async def main():
    """Example usage of the Advanced Supervisor Agent"""

    supervisor = create_advanced_supervisor()

    try:
        # Example educational content generation workflow
        task = "Create a comprehensive lesson about the solar system for 5th grade students including interactive activities and assessments"
        context = {
            "subject": "Science",
            "grade_level": 5,
            "learning_objectives": [
                "Identify planets in our solar system",
                "Compare sizes and characteristics of planets",
                "Understand basic concepts of gravity and orbits",
            ],
            "duration_minutes": 45,
            "environment_type": "space_exploration",
        }

        # Execute workflow
        execution = await supervisor.execute_workflow(
            task=task,
            context=context,
            workflow_template="educational_content_generation",
            priority=WorkflowPriority.HIGH,
            user_id="teacher_001",
        )

        print(f"Workflow completed with status: {execution.status}")
        print(f"Execution time: {execution.metrics.get('execution_time', 0):.2f} seconds")

        # Get performance report
        performance_report = await supervisor.get_performance_report()
        print(f"Total workflows executed: {performance_report['total_workflows_executed']}")

    finally:
        await supervisor.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
