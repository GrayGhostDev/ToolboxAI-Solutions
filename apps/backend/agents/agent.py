"""
Agent Management Module for ToolboxAI Roblox Environment

Manages agent initialization, agent pools, task routing, and result aggregation.
Integrates with the LangChain/LangGraph multi-agent system, SPARC framework,
and swarm intelligence coordination.
"""

import asyncio
import json
import logging

# Import agents from other modules
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import redis
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    # Fallback for compatibility
    from langchain_community.chat_models import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from apps.backend.api.auth.auth import get_current_user
from apps.backend.core.config import settings
from apps.backend.models.schemas import ContentRequest, ContentResponse, User
from .tools import ALL_TOOLS

# Import placeholder agent classes
from .agent_classes import (
    ContentGenerationAgent,
    QuizGenerationAgent,
    TerrainGenerationAgent,
    ScriptGenerationAgent,
    CodeReviewAgent
)

logger = logging.getLogger(__name__)


sys.path.append(str(Path(__file__).parent.parent))

try:
    from core.agents.content_agent import ContentAgent  # type: ignore
    from core.agents.orchestrator import Orchestrator as OrchestrationEngine  # type: ignore
    from core.agents.quiz_agent import QuizAgent  # type: ignore
    from core.agents.review_agent import ReviewAgent  # type: ignore
    from core.agents.script_agent import ScriptAgent  # type: ignore
    from core.agents.supervisor import SupervisorAgent  # type: ignore
    from core.agents.terrain_agent import TerrainAgent  # type: ignore
    from core.coordinators.main_coordinator import MainCoordinator  # type: ignore
    from core.sparc.state_manager import StateManager  # type: ignore
    from core.swarm.swarm_controller import SwarmController  # type: ignore
    from core.mcp.context_manager import MCPContextManager as ContextManager  # type: ignore
    from core.mcp.server import MCPServer  # type: ignore
except ImportError as e:
    logger.warning(
        "Could not import agent modules: %s. Some features may be limited.", e
    )

    # Create placeholder classes for basic functionality
    class SupervisorAgent:
        "Supervisor agent for hierarchical task orchestration"

        def __init__(self, llm=None, *args, **kwargs):
            "Initialize supervisor agent with LangGraph state management"
            self.llm = llm or ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
            self.chat_history = InMemoryChatMessageHistory()
            
            # Initialize sub-agent references (lazy initialization)
            self.agents = {}
            self._agents_initialized = False
            
            # Configure routing patterns
            self.routing_patterns = {
                "quiz": ["quiz", "assessment", "question", "test"],
                "terrain": ["terrain", "environment", "world", "landscape"],
                "script": ["script", "lua", "code", "programming"],
                "review": ["review", "check", "validate", "security"],
                "content": ["content", "lesson", "curriculum", "educational"]
            }
            
            # Agent load tracking
            self.agent_load = {}
            self.max_retries = 3
            logger.info("SupervisorAgent initialized with routing patterns")
        
        def _init_agents(self):
            """Initialize agents on first use"""
            if not self._agents_initialized:
                self.agents = {
                    "content": ContentGenerationAgent(self.llm),
                    "quiz": QuizGenerationAgent(self.llm),
                    "terrain": TerrainGenerationAgent(self.llm),
                    "script": ScriptGenerationAgent(self.llm),
                    "review": CodeReviewAgent(self.llm)
                }
                self.agent_load = {agent: 0 for agent in self.agents.keys()}
                self._agents_initialized = True
                logger.info("SupervisorAgent initialized %d sub-agents", len(self.agents))

        async def route_task(self, task_description: str, context: dict = None, *args, **kwargs):
            "Route task to appropriate agent based on intelligent analysis"
            self._init_agents()  # Initialize agents if not already done
            task_lower = task_description.lower()
            
            # Analyze task description for routing
            selected_agent = None
            max_score = 0
            
            for agent_type, patterns in self.routing_patterns.items():
                score = sum(1 for pattern in patterns if pattern in task_lower)
                if score > max_score:
                    max_score = score
                    selected_agent = agent_type
            
            # Consider agent load for load balancing
            if selected_agent and self.agent_load[selected_agent] > 5:
                # Find alternative agent with lower load
                for agent in sorted(self.agent_load.keys(), key=lambda x: self.agent_load[x]):
                    if self.agent_load[agent] < 3:
                        logger.info("Load balancing: Routing from %s to %s", selected_agent, agent)
                        selected_agent = agent
                        break
            
            # Default fallback to content agent
            if not selected_agent:
                selected_agent = "content"
                logger.warning("No specific routing pattern matched, defaulting to content agent")
            
            # Update load tracking
            self.agent_load[selected_agent] += 1
            
            logger.info("Routing task to %s agent: %s", selected_agent, task_description[:50])
            return selected_agent

    # Agent classes are now imported at module level from agent_classes.py

    class OrchestrationEngine:
        def __init__(self, *args, **kwargs):
            # TODO: Initialize orchestration engine
            # - Set up workflow definitions
            # - Configure parallel execution
            # - Initialize state management
            pass

        async def orchestrate(self, *args, **kwargs):
            # TODO: Implement workflow orchestration
            # - Define execution order
            # - Manage dependencies between agents
            # - Handle parallel task execution
            # - Aggregate results from multiple agents
            return {}

    class StateManager:
        def __init__(self, *args, **kwargs):
            # TODO: Initialize SPARC state manager
            # - Set up state tracking
            # - Initialize policy engine
            # - Configure reward calculator
            # - Set up context window
            pass

        async def execute_cycle(self, *args, **kwargs):
            # TODO: Implement SPARC cycle execution
            # - Observe current state
            # - Apply policy to determine action
            # - Execute action
            # - Calculate reward
            # - Update context
            return {}

    class SwarmController:
        def __init__(self, *args, **kwargs):
            # TODO: Initialize swarm controller
            # - Set up worker pool
            # - Configure load balancing
            # - Initialize consensus mechanism
            pass

        async def distribute_tasks(self, *args, **kwargs):
            # TODO: Implement task distribution
            # - Split tasks for parallel execution
            # - Assign to available workers
            # - Monitor execution progress
            # - Collect and consolidate results
            return []
    
    class ContextManager:
        "Context manager for MCP (Model Context Protocol)"
        
        def __init__(self, max_tokens=128000, max_context_size=8192, **kwargs):
            self.max_tokens = max_tokens
            self.max_context_size = max_context_size
            self.context_history = []
            self.current_context = {}
        
        async def update_context(self, key: str, value: Any):
            "Update context with new information"
            self.current_context[key] = value
            self.context_history.append({
                "timestamp": datetime.now(timezone.utc),
                "key": key,
                "value": value
            })
            return True
        
        async def get_context(self, key: str = None):
            "Get current context or specific key"
            if key:
                return self.current_context.get(key)
            return self.current_context
        
        async def clear_context(self):
            "Clear current context"
            self.current_context = {}
            return True
    
    class MCPServer:
        "MCP Server for WebSocket context management"
        
        def __init__(self, host="127.0.0.1", port=9876):
            self.host = host
            self.port = port
            self.context_manager = ContextManager()
        
        async def start(self):
            "Start MCP server"
            logger.info(f"MCP Server starting on {self.host}:{self.port}")
            return True
        
        async def broadcast_context(self, context: dict):
            "Broadcast context updates to connected clients"
            return True

    class MainCoordinator:
        def __init__(self, *args, **kwargs):
            # TODO: Initialize main coordinator
            # - Set up component references
            # - Configure communication channels
            # - Initialize monitoring
            pass

        async def coordinate(self, *args, **kwargs):
            # TODO: Implement high-level coordination
            # - Manage overall workflow
            # - Coordinate between systems
            # - Handle error recovery
            # - Provide status updates
            return {}


# Redis client for agent coordination
try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connection established for agent coordination")
except Exception as e:
    logger.warning("Redis connection failed: %s. Using in-memory coordination.", e)
    redis_client = None


class AgentPool:
    """Manages a pool of agents for efficient resource utilization"""

    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.agents: Dict[str, List[Any]] = {}
        self.active_agents: Dict[str, int] = {}
        self._lock = asyncio.Lock()
        self.executor = ThreadPoolExecutor(max_workers=pool_size)

        # Initialize agent pools
        self._initialize_pools()

    def _initialize_pools(self):
        """Initialize agent pools for different types"""
        agent_types = ["content", "quiz", "terrain", "script", "review"]

        for agent_type in agent_types:
            self.agents[agent_type] = []
            self.active_agents[agent_type] = 0

            # Create initial pool of agents
            for _ in range(min(2, self.pool_size)):  # Start with 2 agents per type
                agent = self._create_agent(agent_type)
                self.agents[agent_type].append(agent)

        logger.info("Initialized agent pools with %d types", len(agent_types))

    def _create_agent(self, agent_type: str) -> Any:
        """Create an agent of specified type"""
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
        )

        if agent_type == "content":
            return ContentGenerationAgent(llm=llm, tools=ALL_TOOLS)
        elif agent_type == "quiz":
            return QuizGenerationAgent(llm=llm, tools=ALL_TOOLS)
        elif agent_type == "terrain":
            return TerrainGenerationAgent(llm=llm, tools=ALL_TOOLS)
        elif agent_type == "script":
            return ScriptGenerationAgent(llm=llm, tools=ALL_TOOLS)
        elif agent_type == "review":
            return CodeReviewAgent(llm=llm, tools=ALL_TOOLS)
        else:
            # Default to content agent
            return ContentGenerationAgent(llm=llm, tools=ALL_TOOLS)

    async def get_agent(self, agent_type: str) -> Any:
        """Get an available agent from the pool"""
        async with self._lock:
            if not self.agents.get(agent_type):
                # Create agent if pool is empty
                agent = self._create_agent(agent_type)
                self.agents[agent_type] = [agent]

            if self.agents[agent_type]:
                agent = self.agents[agent_type].pop(0)
                self.active_agents[agent_type] += 1
                return agent

            # If no agents available, create a new one
            agent = self._create_agent(agent_type)
            self.active_agents[agent_type] += 1
            return agent

    async def return_agent(self, agent: Any, agent_type: str):
        """Return an agent to the pool"""
        async with self._lock:
            if len(self.agents[agent_type]) < self.pool_size:
                self.agents[agent_type].append(agent)

            self.active_agents[agent_type] = max(0, self.active_agents[agent_type] - 1)

    def get_pool_status(self) -> Dict[str, Dict[str, int]]:
        """Get current pool status"""
        status = {}
        for agent_type, agents_list in self.agents.items():
            status[agent_type] = {
                "available": len(agents_list),
                "active": self.active_agents[agent_type],
                "total": len(agents_list) + self.active_agents[agent_type],
            }
        return status


class TaskRouter:
    """Routes tasks to appropriate agents based on content and context"""

    def __init__(self, supervisor_agent: SupervisorAgent):
        self.supervisor = supervisor_agent
        self.routing_rules = {
            "generate_content": ["content", "terrain", "script"],
            "create_quiz": ["quiz", "content"],
            "generate_terrain": ["terrain"],
            "create_script": ["script"],
            "review_code": ["review"],
            "comprehensive": ["content", "quiz", "terrain", "script", "review"],
        }

    async def route_task(self, task_type: str, task_data: Dict[str, Any]) -> List[str]:
        """Route task to appropriate agent types"""

        # Use supervisor agent for intelligent routing
        try:
            routing_decision = await self.supervisor.route_task(
                {
                    "task_type": task_type,
                    "task_data": task_data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            if isinstance(routing_decision, str):
                return [routing_decision]
            elif isinstance(routing_decision, list):
                return routing_decision
        except TypeError as e:
            logger.error("Supervisor routing failed: %s", e)

        # Fallback to rule-based routing
        agent_types = self.routing_rules.get(task_type, ["content"])

        # Enhance routing based on task complexity
        if task_data.get("include_quiz", False) and "quiz" not in agent_types:
            agent_types.append("quiz")

        if task_data.get("environment_type") and "terrain" not in agent_types:
            agent_types.append("terrain")

        return agent_types


class ResultAggregator:
    """Aggregates results from multiple agents"""

    def __init__(self):
        self.aggregation_strategies = {
            "content_generation": self._aggregate_content_results,
            "quiz_creation": self._aggregate_quiz_results,
            "comprehensive": self._aggregate_comprehensive_results,
        }

    async def aggregate_results(
        self, task_type: str, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate results from multiple agents"""
        strategy = self.aggregation_strategies.get(task_type, self._default_aggregation)

        try:
            if asyncio.iscoroutinefunction(strategy):
                aggregated = await strategy(results)
            else:
                aggregated = strategy(results)

            # Add metadata
            aggregated["aggregation_metadata"] = {
                "task_type": task_type,
                "num_agents": len(results),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "aggregation_strategy": strategy.__name__,
            }

            return aggregated

        except (TypeError, ValueError, AttributeError, KeyError) as e:
            logger.error("Result aggregation failed: %s", e)
            return self._fallback_aggregation(results)

    def _merge_content(self, aggregated: Dict[str, Any], result: Dict[str, Any]):
        """Merge content from result into aggregated"""
        if "content" in result:
            aggregated["content"].update(result["content"])
        if "scripts" in result:
            aggregated["scripts"].extend(result["scripts"])

    def _merge_terrain(self, aggregated: Dict[str, Any], result: Dict[str, Any]):
        """Merge terrain using most detailed version"""
        if "terrain" in result and result["terrain"]:
            if not aggregated["terrain"] or len(str(result["terrain"])) > len(
                str(aggregated["terrain"])
            ):
                aggregated["terrain"] = result["terrain"]

    def _merge_resources(self, aggregated: Dict[str, Any], result: Dict[str, Any]):
        """Merge resource requirements"""
        aggregated["estimated_build_time"] += result.get("estimated_build_time", 0)
        if "resource_requirements" in result:
            for resource, amount in result["resource_requirements"].items():
                aggregated["resource_requirements"][resource] = (
                    aggregated["resource_requirements"].get(resource, 0) + amount
                )
        if (
            "game_mechanics" in result
            and result["game_mechanics"]
            and not aggregated["game_mechanics"]
        ):
            aggregated["game_mechanics"] = result["game_mechanics"]

    def _aggregate_content_results(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate content generation results"""
        if not results:
            return {}

        aggregated = {
            "content": {},
            "scripts": [],
            "terrain": None,
            "game_mechanics": None,
            "estimated_build_time": 0,
            "resource_requirements": {},
        }

        for result in results:
            self._merge_content(aggregated, result)
            self._merge_terrain(aggregated, result)
            self._merge_resources(aggregated, result)

        return aggregated

    async def _aggregate_quiz_results(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate quiz generation results"""
        if not results:
            return {}

        # Use the best quiz result (highest quality score)
        best_result = max(results, key=lambda x: x.get("quality_score", 0))

        # Combine questions from all results if beneficial
        all_questions = []
        for result in results:
            if "quiz" in result and "questions" in result["quiz"]:
                all_questions.extend(result["quiz"]["questions"])

        # Remove duplicates and select best questions
        unique_questions = []
        seen_questions = set()

        for question in all_questions:
            question_text = question.get("question_text", "")
            if question_text not in seen_questions:
                unique_questions.append(question)
                seen_questions.add(question_text)

        # Update best result with combined questions
        if "quiz" in best_result:
            best_result["quiz"]["questions"] = unique_questions[
                :20
            ]  # Limit to 20 questions

        return best_result

    async def _aggregate_comprehensive_results(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate comprehensive task results"""
        # Combine content and quiz results
        content_results = [r for r in results if r.get("type") == "content"]
        quiz_results = [r for r in results if r.get("type") == "quiz"]

        aggregated = {}

        if content_results:
            aggregated["content"] = await self._aggregate_content_results(
                content_results
            )

        if quiz_results:
            aggregated["quiz"] = await self._aggregate_quiz_results(quiz_results)

        return aggregated

    async def _default_aggregation(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Default aggregation strategy"""
        if not results:
            return {}

        # Simply merge all results
        aggregated = {}
        for result in results:
            aggregated.update(result)

        return aggregated

    def _fallback_aggregation(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback aggregation in case of errors"""
        return {
            "results": results,
            "error": "Aggregation failed, returning raw results",
            "num_results": len(results),
        }


class AgentManager:
    """Main agent management class"""

    def __init__(self):
        self.agent_pool = AgentPool(pool_size=settings.MAX_CONCURRENT_GENERATIONS)
        self.supervisor = SupervisorAgent()
        self.task_router = TaskRouter(self.supervisor)
        self.result_aggregator = ResultAggregator()
        self.orchestrator = OrchestrationEngine()
        self.sparc_manager = StateManager()
        # Initialize swarm controller (disabled for now, requires full configuration)
        self.swarm_controller = None  # SwarmController requires complex initialization
        self.main_coordinator = MainCoordinator()
        
        # Initialize MCP for context management
        self.mcp_context = ContextManager(max_tokens=16384)
        self.mcp_server = MCPServer(port=9876)

        # Task tracking
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[Dict[str, Any]] = []

        logger.info("AgentManager initialized with all components")

    async def generate_content(
        self, request: ContentRequest, user: Optional[User] = None
    ) -> ContentResponse:
        """Generate educational content using multi-agent system with SPARC, Swarm, and MCP"""

        task_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)

        # Track task
        self.active_tasks[task_id] = {
            "task_type": "generate_content",
            "request": request.dict(),
            "user_id": user.id if user else None,
            "start_time": start_time,
            "status": "processing",
        }

        try:
            # 1. Update MCP context with request information
            await self.mcp_context.update_context("task_id", task_id)
            await self.mcp_context.update_context("user", user.dict() if user else None)
            await self.mcp_context.update_context("request", request.dict())
            await self.mcp_context.update_context("subject", request.subject)
            await self.mcp_context.update_context("grade_level", request.grade_level)
            await self.mcp_context.update_context("learning_objectives", request.learning_objectives)
            
            # 2. Initialize SPARC state for this task
            sparc_state = await self.sparc_manager.initialize_state({
                "task_id": task_id,
                "environment": request.environment_type,
                "subject": request.subject,
                "grade_level": request.grade_level,
                "objectives": request.learning_objectives,
                "user_context": {
                    "user_id": user.id if user else None,
                    "role": user.role if user else None
                }
            })
            
            # 3. Route task to appropriate agents
            agent_types = await self.task_router.route_task(
                "generate_content", request.dict()
            )

            logger.info(f"Task {task_id} routed to agents: {agent_types}")
            
            # 4. Use Swarm for parallel agent execution
            swarm_tasks = []
            for agent_type in agent_types:
                swarm_tasks.append({
                    "agent_type": agent_type,
                    "request": request.dict(),
                    "task_id": task_id,
                    "context": await self.mcp_context.get_context()
                })
            
            # Execute via swarm controller for parallel processing
            if hasattr(self.swarm_controller, 'distribute_tasks'):
                swarm_results = await self.swarm_controller.distribute_tasks(swarm_tasks)
            else:
                # Fallback to regular parallel execution
                swarm_results = await self._execute_agents_parallel(
                    agent_types, request, task_id
                )
            
            # 5. Update SPARC state with agent results
            await self.sparc_manager.update_state({
                "task_id": task_id,
                "agent_results": swarm_results,
                "action": "content_generation_complete"
            })

            # 6. Aggregate results
            aggregated_result = await self.result_aggregator.aggregate_results(
                "content_generation", swarm_results
            )
            
            # 7. Update MCP context with results
            await self.mcp_context.update_context("aggregated_results", aggregated_result)
            await self.mcp_context.update_context("status", "finalizing")

            # 8. Use main coordinator for final orchestration
            final_result = await self.main_coordinator.coordinate(
                {
                    "task_id": task_id,
                    "task_type": "content_generation",
                    "agent_results": aggregated_result,
                    "request": request.dict(),
                    "sparc_state": sparc_state,
                    "mcp_context": await self.mcp_context.get_context()
                }
            )
            
            # 9. Calculate reward using SPARC
            reward = await self.sparc_manager.calculate_reward({
                "task_id": task_id,
                "result": final_result,
                "objectives_met": len(request.learning_objectives),
                "execution_time": (datetime.now(timezone.utc) - start_time).total_seconds()
            })

            # 10. Create response
            response = ContentResponse(
                success=True,
                message="Content generated successfully using SPARC, Swarm, and MCP integration",
                content=final_result.get("content", {}),
                scripts=final_result.get("scripts", []),
                terrain=final_result.get("terrain"),
                game_mechanics=final_result.get("game_mechanics"),
                estimated_build_time=final_result.get("estimated_build_time", 0),
                resource_requirements=final_result.get("resource_requirements", {}),
                content_id=task_id,  # Include unique content ID
            )
            
            # 11. Broadcast context update via MCP
            await self.mcp_server.broadcast_context({
                "task_id": task_id,
                "status": "completed",
                "reward": reward,
                "content_id": task_id
            })

            # Update task status
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["end_time"] = datetime.now(timezone.utc)
            self.active_tasks[task_id]["reward"] = reward
            self.active_tasks[task_id]["duration"] = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds()

            # Archive task
            self.task_history.append(self.active_tasks.pop(task_id))

            logger.info(f"Task {task_id} completed successfully")
            return response

        except Exception as e:
            logger.error(f"Content generation failed for task {task_id}: {e}")

            # Update task status
            self.active_tasks[task_id]["status"] = "failed"
            self.active_tasks[task_id]["error"] = str(e)
            self.active_tasks[task_id]["end_time"] = datetime.now(timezone.utc)

            # Archive failed task
            self.task_history.append(self.active_tasks.pop(task_id))

            # Return error response
            return ContentResponse(
                success=False,
                message=f"Content generation failed: {str(e)}",
                content_id=task_id,  # Include content ID even in error
                content={},
                scripts=[],
                terrain=None,
                game_mechanics=None,
                estimated_build_time=0,
                resource_requirements={},
            )

    async def _execute_agents_parallel(
        self, agent_types: List[str], request: ContentRequest, task_id: str
    ) -> List[Dict[str, Any]]:
        """Execute multiple agents in parallel"""

        async def execute_single_agent(agent_type: str) -> Dict[str, Any]:
            agent = await self.agent_pool.get_agent(agent_type)

            try:
                if agent_type == "content":
                    result = await agent.generate_content(request.dict())
                elif agent_type == "quiz":
                    result = await agent.generate_quiz(request.dict())
                elif agent_type == "terrain":
                    result = await agent.generate_terrain(request.dict())
                elif agent_type == "script":
                    result = await agent.generate_script(request.dict())
                elif agent_type == "review":
                    result = await agent.review_code({"content": request.dict()})
                else:
                    result = {}

                # Add type metadata
                result["type"] = agent_type
                result["agent_id"] = getattr(agent, "id", agent_type)

                return result

            finally:
                await self.agent_pool.return_agent(agent, agent_type)

        # Execute all agents concurrently
        tasks = [execute_single_agent(agent_type) for agent_type in agent_types]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Agent {agent_types[i]} failed: {result}")
            else:
                valid_results.append(result)

        return valid_results

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        return self.active_tasks.get(task_id)

    async def list_active_tasks(self) -> List[Dict[str, Any]]:
        """List all active tasks"""
        return list(self.active_tasks.values())

    async def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get task history"""
        return self.task_history[-limit:]

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get agent pool status"""
        pool_status = self.agent_pool.get_pool_status()

        return {
            "pool_status": pool_status,
            "active_tasks": len(self.active_tasks),
            "total_tasks_processed": len(self.task_history),
            "system_health": (
                "healthy"
                if all(
                    status["available"] + status["active"] > 0
                    for status in pool_status.values()
                )
                else "degraded"
            ),
        }

    async def shutdown(self):
        """Graceful shutdown of agent manager"""
        logger.info("Shutting down AgentManager...")

        # Wait for active tasks to complete (with timeout)
        timeout = 60  # 1 minute timeout
        start_time = datetime.now(timezone.utc)

        while (
            self.active_tasks
            and (datetime.now(timezone.utc) - start_time).total_seconds() < timeout
        ):
            await asyncio.sleep(1)

        if self.active_tasks:
            logger.warning(f"Shutting down with {len(self.active_tasks)} active tasks")

        # Shutdown thread pool
        if hasattr(self.agent_pool, "executor"):
            self.agent_pool.executor.shutdown(wait=True)

        logger.info("AgentManager shutdown completed")


# Global agent manager instance
agent_manager = AgentManager()


# Convenience functions for external use
async def initialize_agents():
    """Initialize the agent system"""
    logger.info("Initializing agent system")
    # Agent manager is already initialized
    return agent_manager


async def generate_educational_content(
    request: ContentRequest, user: Optional[User] = None
) -> ContentResponse:
    """Generate educational content"""
    return await agent_manager.generate_content(request, user)


async def get_agent_health():
    """Get agent system health status"""
    return await agent_manager.get_agent_status()


async def shutdown_agents():
    """Shutdown agent system"""
    await agent_manager.shutdown()


# Export public interface
__all__ = [
    "AgentManager",
    "AgentPool",
    "TaskRouter",
    "ResultAggregator",
    "agent_manager",
    "initialize_agents",
    "generate_educational_content",
    "get_agent_health",
    "shutdown_agents",
]
