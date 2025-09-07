"""
Supervisor Agent - Orchestrates and manages other agents

Uses LangGraph for hierarchical task delegation and supervision.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from enum import Enum

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain.tools import Tool

from .base_agent import BaseAgent, AgentConfig, AgentState, TaskResult, AgentPriority

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks the supervisor can handle"""

    CONTENT_GENERATION = "content_generation"
    QUIZ_CREATION = "quiz_creation"
    TERRAIN_BUILDING = "terrain_building"
    SCRIPT_DEVELOPMENT = "script_development"
    REVIEW_OPTIMIZATION = "review_optimization"
    COMPLEX_WORKFLOW = "complex_workflow"


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
                model="gpt-4",
                temperature=0.3,  # Lower temperature for more consistent decisions
                system_prompt=self._get_supervisor_prompt(),
            )
        super().__init__(config)

        # Agent registry
        self.managed_agents: Dict[str, BaseAgent] = {}

        # Workflow graph
        self.workflow = self._build_workflow_graph()

        # Task queue
        self.task_queue: List[Dict[str, Any]] = []

        # Performance tracking
        self.agent_performance: Dict[str, Dict[str, Any]] = {}

    def _get_supervisor_prompt(self) -> str:
        """Get specialized prompt for supervisor agent"""
        return """You are the Supervisor Agent responsible for orchestrating a team of specialized agents to create educational Roblox environments.

Your team includes:
1. Content Agent - Educational content and curriculum alignment
2. Quiz Agent - Interactive quiz and assessment creation
3. Terrain Agent - 3D environment and terrain generation
4. Script Agent - Lua script development for Roblox
5. Review Agent - Code review and optimization

Your responsibilities:
- Analyze incoming tasks and determine the best agent(s) to handle them
- Coordinate multi-agent workflows for complex tasks
- Monitor agent performance and handle errors
- Aggregate and synthesize results from multiple agents
- Ensure educational quality and technical correctness

When routing tasks:
- Consider agent specializations and current workload
- Identify dependencies between subtasks
- Determine if parallel or sequential execution is needed
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
            "route", self._routing_decision, {"delegate": "delegate", "direct": END, "escalate": END}
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

        if "escalate" in routing.lower():
            return "escalate"
        elif "direct" in routing.lower() or "no delegation" in routing.lower():
            return "direct"
        else:
            return "delegate"

    async def _delegate_task(self, state: AgentState) -> AgentState:
        """Delegate task to appropriate agent(s)"""
        routing = state["metadata"].get("routing_decision", "")

        # Parse routing decision to identify agents and strategy
        delegations = self._parse_routing_decision(routing)

        if not delegations:
            state["error"] = "Failed to parse routing decision"
            return state

        # Execute delegations
        results = []

        for delegation in delegations:
            agent_type = delegation["agent"]
            subtask = delegation["task"]

            # Get or create agent
            agent = self._get_or_create_agent(agent_type)

            if agent:
                # Execute subtask
                result = await agent.execute(subtask, state["context"])
                results.append({"agent": agent_type, "task": subtask, "result": result})

                # Track performance
                self._track_agent_performance(agent_type, result)
            else:
                logger.warning(f"Agent {agent_type} not available")

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

    def _parse_routing_decision(self, routing: str) -> List[Dict[str, str]]:
        """Parse routing decision into actionable delegations"""
        delegations = []

        # Simple parsing logic - in production, use more sophisticated parsing
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

    def _get_agent_class_map(self) -> Dict[str, type]:
        """Get mapping of agent types to classes (whitelist approach)"""
        # Import all agents at once for better security
        from .content_agent import ContentAgent
        from .quiz_agent import QuizAgent
        from .terrain_agent import TerrainAgent
        from .script_agent import ScriptAgent
        from .review_agent import ReviewAgent

        return {
            "content": ContentAgent,
            "quiz": QuizAgent,
            "terrain": TerrainAgent,
            "script": ScriptAgent,
            "review": ReviewAgent,
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
        # Execute workflow
        final_state = await self.workflow.ainvoke(state)

        return final_state.get("result", "Task processing completed")

    async def delegate_complex_task(self, task: str, requirements: Dict[str, Any]) -> TaskResult:
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

    def get_agent_status_report(self) -> Dict[str, Any]:
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
