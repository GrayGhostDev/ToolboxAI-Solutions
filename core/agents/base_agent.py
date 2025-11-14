"""
Base Agent Class - Foundation for all specialized agents

Provides core functionality for LangChain-based agents with SPARC integration.
"""

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TypedDict

# Import enhanced LangChain compatibility layer
try:
    from core.langchain_enhanced_compat import (
        BaseMessage,
        ChatPromptTemplate,
        HumanMessage,
        MessagesPlaceholder,
        SystemMessage,
        get_chat_model,
        validate_langchain_environment,
    )

    ENHANCED_COMPAT_AVAILABLE = True
except ImportError:
    # Fallback to original imports
    from langchain_core.messages import (
        BaseMessage,
        HumanMessage,
        SystemMessage,
    )
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    ENHANCED_COMPAT_AVAILABLE = False

    # Check if we should use mock LLM
    USE_MOCK_LLM = not os.getenv("OPENAI_API_KEY") or os.getenv("USE_MOCK_LLM") == "true"

    if USE_MOCK_LLM:
        # Use mock LLM for testing
        from tests.fixtures.agents.mock_llm import MockChatModel as ChatOpenAI

        logger = logging.getLogger(__name__)
        logger.info("Using Mock LLM for testing (no OpenAI API key required)")
    else:
        # Use real OpenAI
        from langchain_openai import ChatOpenAI

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status enumeration"""

    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


class AgentCapability(Enum):
    """Agent capabilities for routing"""

    CONTENT_GENERATION = "content_generation"
    EDUCATIONAL_SUPPORT = "educational_support"
    ANALYSIS = "analysis"
    VALIDATION = "validation"
    ASSESSMENT = "assessment"
    ADAPTATION = "adaptation"
    ORCHESTRATION = "orchestration"


class AgentPriority(Enum):
    """Task priority levels"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentConfig:
    """Configuration for agent initialization"""

    name: str = "BaseAgent"
    model: str = "gpt-3.5-turbo"  # Using accessible model
    temperature: float = 0.7
    max_retries: int = 3
    timeout: int = 300  # seconds
    verbose: bool = False
    memory_enabled: bool = True
    max_context_length: int = 128000
    max_tokens: int = 4096  # Maximum tokens for response generation
    tools: list[Any] = field(default_factory=list)
    system_prompt: str = ""


class AgentState(TypedDict):
    """State schema for agent execution"""

    messages: list[BaseMessage]
    task: str
    context: dict[str, Any]
    metadata: dict[str, Any]
    status: str
    result: Any | None
    error: str | None
    timestamp: str
    iterations: int
    max_iterations: int


class TaskResult(BaseModel):
    """Result model for agent tasks"""

    success: bool
    output: Any
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    execution_time: float = 0.0
    tokens_used: int = 0

    @classmethod
    def create(
        cls,
        *,
        success: bool,
        output: Any,
        metadata: dict[str, Any] | None = None,
        error: str | None = None,
        execution_time: float = 0.0,
        tokens_used: int = 0,
    ) -> "TaskResult":
        data = {
            "success": success,
            "output": output,
            "metadata": metadata or {},
            "error": error,
            "execution_time": execution_time,
            "tokens_used": tokens_used,
        }
        from typing import Any, cast

        return cast(Any, cls)(**data)  # type: ignore[reportCallIssue]


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.

    Provides:
    - LangChain integration
    - SPARC framework hooks
    - Memory management
    - Error handling
    - Metrics tracking
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.status = AgentStatus.IDLE
        self.llm = self._initialize_llm()
        self.memory = []
        self.metrics = {
            "tasks_processed": 0,
            "total_tokens": 0,
            "errors": 0,
            "average_execution_time": 0.0,
        }
        self.current_task = None
        self.tools = config.tools

        # Initialize prompt template
        self.prompt = self._create_prompt_template()

        # Validate LangChain environment if enhanced compatibility is available
        if ENHANCED_COMPAT_AVAILABLE:
            self._validate_environment()

        logger.info(
            f"Initialized {self.name} agent with {'enhanced' if ENHANCED_COMPAT_AVAILABLE else 'legacy'} LangChain support"
        )

    def _initialize_llm(self):
        """Initialize the language model using enhanced compatibility layer"""
        if ENHANCED_COMPAT_AVAILABLE:
            # Use enhanced compatibility layer
            return get_chat_model(
                model_name=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
            )
        else:
            # Fallback to direct initialization
            # Fix for LangChain httpx client incompatibility with OpenAI SDK
            # Explicitly set http_client=None to prevent LangChain from creating wrapped clients
            return ChatOpenAI(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=None,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
                http_client=None,  # Prevent httpx client wrapper incompatibility
                http_async_client=None,  # Prevent async httpx client wrapper incompatibility
            )

    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create the base prompt template"""
        system_prompt = self.config.system_prompt or self._get_default_system_prompt()

        return ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                MessagesPlaceholder(variable_name="history", optional=True),
                HumanMessage(content="{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad", optional=True),
            ]
        )

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for the agent"""
        return f"""You are {self.name}, an intelligent agent specialized in Roblox educational content generation.

Your responsibilities:
- Process tasks efficiently and accurately
- Provide detailed, actionable outputs
- Maintain context across interactions
- Report errors clearly
- Optimize for educational value and engagement

Always structure your responses clearly and provide Lua code when applicable.
"""

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> TaskResult:
        """
        Execute a task with the given context.

        Args:
            task: Task description
            context: Optional context dictionary

        Returns:
            TaskResult with execution details
        """
        start_time = datetime.now()
        self.status = AgentStatus.PROCESSING
        self.current_task = task

        try:
            # Prepare state
            state = self._prepare_state(task, context)

            # Process task
            result = await self._process_task(state)

            # Update metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(True, execution_time)

            # Create result
            task_result = TaskResult.create(
                success=True,
                output=result,
                metadata={
                    "agent": self.name,
                    "task": task,
                    "timestamp": datetime.now().isoformat(),
                },
                execution_time=execution_time,
            )

            # Store in memory if enabled
            if self.config.memory_enabled:
                self._store_memory(task, task_result)

            self.status = AgentStatus.COMPLETED
            return task_result

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error(f"{self.name} error processing task: {e}")

            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(False, execution_time)

            self.status = AgentStatus.ERROR

            return TaskResult.create(
                success=False, output=None, error=str(e), execution_time=execution_time
            )
        finally:
            self.current_task = None

    def _prepare_state(self, task: str, context: dict[str, Any] | None) -> AgentState:
        """Prepare the agent state for task execution"""
        return AgentState(
            messages=[HumanMessage(content=task)],
            task=task,
            context=context or {},
            metadata={"agent": self.name},
            status="processing",
            result=None,
            error=None,
            timestamp=datetime.now().isoformat(),
            iterations=0,
            max_iterations=10,
        )

    @abstractmethod
    async def _process_task(self, state: AgentState) -> Any:
        """
        Process the task - must be implemented by subclasses.

        Args:
            state: Current agent state

        Returns:
            Task result
        """
        pass

    def _update_metrics(self, success: bool, execution_time: float):
        """Update agent metrics"""
        self.metrics["tasks_processed"] += 1

        if not success:
            self.metrics["errors"] += 1

        # Update average execution time
        current_avg = self.metrics["average_execution_time"]
        total_tasks = self.metrics["tasks_processed"]
        self.metrics["average_execution_time"] = (
            current_avg * (total_tasks - 1) + execution_time
        ) / total_tasks

    def _store_memory(self, task: str, result: TaskResult):
        """Store task and result in memory"""
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "success": result.success,
            "output_summary": str(result.output)[:200] if result.output else None,
            "error": result.error,
        }

        self.memory.append(memory_entry)

        # Limit memory size
        max_memory_size = 100
        if len(self.memory) > max_memory_size:
            self.memory = self.memory[-max_memory_size:]

    async def collaborate(
        self,
        other_agent: "BaseAgent",
        task: str,
        context: dict[str, Any] | None = None,
    ) -> TaskResult:
        """
        Collaborate with another agent on a task.

        Args:
            other_agent: Agent to collaborate with
            task: Task description
            context: Optional context

        Returns:
            Combined result from collaboration
        """
        logger.info(f"{self.name} collaborating with {other_agent.name}")

        # Execute tasks in parallel
        results = await asyncio.gather(
            self.execute(f"Your part: {task}", context),
            other_agent.execute(f"Your part: {task}", context),
        )

        # Combine results
        combined_output = {
            self.name: results[0].output,
            other_agent.name: results[1].output,
        }

        collaboration_result = TaskResult.create(
            success=all(r.success for r in results),
            output=combined_output,
            metadata={"collaboration": True, "agents": [self.name, other_agent.name]},
        )

        # Trigger testing validation if collaboration was successful and involves code generation
        if collaboration_result.success and context and context.get("trigger_testing", True):
            await self._trigger_post_collaboration_testing(collaboration_result, context)

        return collaboration_result

    async def _trigger_post_collaboration_testing(
        self, result: TaskResult, context: dict[str, Any]
    ):
        """Trigger testing validation after successful collaboration"""
        try:
            # Import here to avoid circular imports
            from .testing_agent import TestingAgent

            # Check if we need testing validation
            code_related_agents = ["ScriptAgent", "TerrainAgent", "ContentAgent"]
            agents_involved = result.metadata.get("agents", [])

            if any(agent in str(agents_involved) for agent in code_related_agents):
                logger.info("Triggering post-collaboration testing validation")

                # Create testing agent for validation
                testing_agent = TestingAgent()

                # Determine primary agent for test type selection
                primary_agent = agents_involved[0] if agents_involved else self.name

                # Trigger validation testing
                await testing_agent.trigger_post_completion_tests(primary_agent, result.output)

                logger.info("Post-collaboration testing validation completed")

        except Exception as e:
            logger.warning(f"Post-collaboration testing failed: {e}")
            # Don't fail the collaboration due to testing issues

    async def trigger_testing_validation(
        self, task_result: TaskResult, test_context: dict[str, Any] | None = None
    ):
        """
        Trigger testing validation after completing a significant task.

        Args:
            task_result: Result from the completed task
            test_context: Optional testing context
        """
        try:
            # Import here to avoid circular imports
            from .testing_agent import TestingAgent

            logger.info(f"{self.name} triggering testing validation")

            # Create testing agent
            testing_agent = TestingAgent()

            # Prepare testing context
            context = test_context or {}
            context.update(
                {
                    "triggered_by": self.name,
                    "task_completed": True,
                    "original_task_success": task_result.success,
                }
            )

            # Trigger appropriate tests based on agent type and task result
            if task_result.success:
                validation_result = await testing_agent.validate_agent_output(
                    self.name, task_result.output
                )

                logger.info(
                    f"Testing validation result: {validation_result.get('validation_result', 'unknown')}"
                )

                return validation_result
            else:
                logger.info("Skipping testing validation due to failed task")
                return None

        except Exception as e:
            logger.warning(f"Testing validation failed: {e}")
            return None

    def add_tool(self, tool: Any):
        """Add a tool to the agent's toolkit"""
        self.tools.append(tool)
        logger.info(f"Added tool to {self.name}: {tool}")

    def get_status(self) -> dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "status": self.status.value,
            "current_task": self.current_task,
            "metrics": self.metrics,
            "memory_size": len(self.memory),
            "tools_count": len(self.tools),
        }

    def reset(self):
        """Reset agent state"""
        self.status = AgentStatus.IDLE
        self.current_task = None
        self.memory.clear()
        logger.info(f"{self.name} agent reset")

    def get_memory_context(self, limit: int = 5) -> list[dict[str, Any]]:
        """Get recent memory entries for context"""
        return self.memory[-limit:] if self.memory else []

    async def reflect(self) -> dict[str, Any]:
        """
        Agent self-reflection on performance and improvements.

        Returns:
            Reflection analysis
        """
        reflection_prompt = f"""Analyze your recent performance:
        Tasks processed: {self.metrics['tasks_processed']}
        Error rate: {self.metrics['errors'] / max(1, self.metrics['tasks_processed']) * 100:.1f}%
        Average execution time: {self.metrics['average_execution_time']:.2f}s

        Recent tasks: {self.get_memory_context(3)}

        Provide insights on:
        1. Performance trends
        2. Common error patterns
        3. Suggested improvements
        """

        response = await self.llm.ainvoke(reflection_prompt)

        return {
            "reflection": response.content,
            "metrics": self.metrics,
            "timestamp": datetime.now().isoformat(),
        }

    def _validate_environment(self):
        """Validate LangChain environment and log any issues"""
        if ENHANCED_COMPAT_AVAILABLE:
            try:
                validation_results = validate_langchain_environment()
                if validation_results["issues"]:
                    logger.warning(
                        f"LangChain environment issues detected for {self.name}: {validation_results['issues']}"
                    )
                else:
                    logger.debug(f"LangChain environment validated successfully for {self.name}")
            except Exception as e:
                logger.warning(f"Failed to validate LangChain environment for {self.name}: {e}")

    def get_environment_status(self) -> dict[str, Any]:
        """Get detailed environment status for this agent"""
        status = {
            "agent_name": self.name,
            "enhanced_compat_available": ENHANCED_COMPAT_AVAILABLE,
            "model_config": {
                "model": self.config.model,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            },
        }

        if ENHANCED_COMPAT_AVAILABLE:
            try:
                status["langchain_validation"] = validate_langchain_environment()
            except Exception as e:
                status["langchain_validation"] = {"error": str(e)}

        return status

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', status={self.status.value}, enhanced_compat={ENHANCED_COMPAT_AVAILABLE})>"
