"""
Base Agent Class - Foundation for all specialized agents

Provides core functionality for LangChain-based agents with SPARC integration.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, TypedDict
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.schema import AgentAction, AgentFinish
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status enumeration"""

    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


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
    model: str = "gpt-4"
    temperature: float = 0.7
    max_retries: int = 3
    timeout: int = 300  # seconds
    verbose: bool = False
    memory_enabled: bool = True
    max_context_length: int = 128000
    tools: List[Any] = field(default_factory=list)
    system_prompt: str = ""


class AgentState(TypedDict):
    """State schema for agent execution"""

    messages: List[BaseMessage]
    task: str
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    status: str
    result: Optional[Any]
    error: Optional[str]
    timestamp: str
    iterations: int
    max_iterations: int


class TaskResult(BaseModel):
    """Result model for agent tasks"""

    success: bool
    output: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0


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
        self.metrics = {"tasks_processed": 0, "total_tokens": 0, "errors": 0, "average_execution_time": 0.0}
        self.current_task = None
        self.tools = config.tools

        # Initialize prompt template
        self.prompt = self._create_prompt_template()

        logger.info(f"Initialized {self.name} agent")

    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the language model"""
        return ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=None,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create the base prompt template"""
        system_prompt = self.config.system_prompt or self._get_default_system_prompt()

        return ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                MessagesPlaceholder(variable_name="history"),
                HumanMessage(content="{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
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

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskResult:
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
            task_result = TaskResult(
                success=True,
                output=result,
                metadata={"agent": self.name, "task": task, "timestamp": datetime.now().isoformat()},
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

            return TaskResult(success=False, output=None, error=str(e), execution_time=execution_time)
        finally:
            self.current_task = None

    def _prepare_state(self, task: str, context: Optional[Dict[str, Any]]) -> AgentState:
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
        self.metrics["average_execution_time"] = (current_avg * (total_tasks - 1) + execution_time) / total_tasks

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
        self, other_agent: "BaseAgent", task: str, context: Optional[Dict[str, Any]] = None
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
            self.execute(f"Your part: {task}", context), other_agent.execute(f"Your part: {task}", context)
        )

        # Combine results
        combined_output = {self.name: results[0].output, other_agent.name: results[1].output}

        return TaskResult(
            success=all(r.success for r in results),
            output=combined_output,
            metadata={"collaboration": True, "agents": [self.name, other_agent.name]},
        )

    def add_tool(self, tool: Any):
        """Add a tool to the agent's toolkit"""
        self.tools.append(tool)
        logger.info(f"Added tool to {self.name}: {tool}")

    def get_status(self) -> Dict[str, Any]:
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

    def get_memory_context(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent memory entries for context"""
        return self.memory[-limit:] if self.memory else []

    async def reflect(self) -> Dict[str, Any]:
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

        return {"reflection": response.content, "metrics": self.metrics, "timestamp": datetime.now().isoformat()}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', status={self.status.value})>"
