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
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    # Fallback for compatibility
    from langchain_community.chat_models import ChatOpenAI

from apps.backend.api.auth.auth import get_current_user
from apps.backend.core.config import settings
from apps.backend.models.schemas import ContentRequest, ContentResponse, User
from langgraph.prebuilt import create_react_agent

# Import placeholder agent classes
from .agent_classes import (
    CodeReviewAgent,
    ContentGenerationAgent,
    QuizGenerationAgent,
    ScriptGenerationAgent,
    TerrainGenerationAgent,
)
from .tools import ALL_TOOLS

logger = logging.getLogger(__name__)


sys.path.append(str(Path(__file__).parent.parent))

try:
    from core.agents.content_agent import ContentAgent  # type: ignore
    from core.agents.orchestrator import (
        Orchestrator as OrchestrationEngine,  # type: ignore
    )
    from core.agents.quiz_agent import QuizAgent  # type: ignore
    from core.agents.review_agent import ReviewAgent  # type: ignore
    from core.agents.script_agent import ScriptAgent  # type: ignore
    from core.agents.supervisor import SupervisorAgent  # type: ignore
    from core.agents.terrain_agent import TerrainAgent  # type: ignore
    from core.coordinators.main_coordinator import MainCoordinator  # type: ignore
    from core.mcp.context_manager import (
        MCPContextManager as ContextManager,  # type: ignore
    )
    from core.mcp.server import MCPServer  # type: ignore
    from core.sparc.state_manager import StateManager  # type: ignore
    from core.swarm.swarm_controller import SwarmController  # type: ignore
except ImportError as e:
    logger.warning("Could not import agent modules: %s. Some features may be limited.", e)

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
                "content": ["content", "lesson", "curriculum", "educational"],
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
                    "review": CodeReviewAgent(self.llm),
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
            """Initialize orchestration engine with workflow definitions and parallel execution"""
            # Set up workflow definitions
            self.workflow_definitions = {
                "content_generation": [
                    {"agent": "content", "action": "generate_content", "parallel": False},
                    {"agent": "quiz", "action": "generate_quiz", "parallel": True},
                    {"agent": "terrain", "action": "generate_terrain", "parallel": True},
                    {"agent": "script", "action": "generate_script", "parallel": False},
                    {"agent": "review", "action": "review_code", "parallel": False},
                ],
                "assessment_creation": [
                    {"agent": "quiz", "action": "generate_quiz", "parallel": False},
                    {"agent": "script", "action": "generate_script", "parallel": False},
                    {"agent": "review", "action": "review_code", "parallel": False},
                ],
                "environment_setup": [
                    {"agent": "terrain", "action": "generate_terrain", "parallel": False},
                    {"agent": "script", "action": "generate_script", "parallel": True},
                    {"agent": "review", "action": "review_code", "parallel": False},
                ],
            }

            # Configure parallel execution
            self.max_parallel_workers = kwargs.get("max_workers", 5)
            self.execution_timeout = kwargs.get("timeout", 300)
            self.retry_attempts = kwargs.get("retry_attempts", 3)

            # Initialize state management
            self.execution_state = {}
            self.task_dependencies = {}

            logger.info(
                "OrchestrationEngine initialized with %d workflows", len(self.workflow_definitions)
            )

        async def orchestrate(self, workflow_name: str, context: dict, *args, **kwargs):
            """Implement workflow orchestration with dependency management and parallel execution"""
            if workflow_name not in self.workflow_definitions:
                logger.error("Unknown workflow: %s", workflow_name)
                return {"error": f"Unknown workflow: {workflow_name}"}

            workflow = self.workflow_definitions[workflow_name]
            results = {}
            parallel_tasks = []

            # Initialize execution state
            execution_id = str(uuid.uuid4())
            self.execution_state[execution_id] = {
                "workflow": workflow_name,
                "status": "running",
                "started_at": datetime.now(timezone.utc),
                "context": context,
            }

            try:
                for step in workflow:
                    agent_name = step["agent"]
                    action = step["action"]
                    is_parallel = step.get("parallel", False)

                    if is_parallel:
                        # Queue for parallel execution
                        parallel_tasks.append((agent_name, action, context))
                    else:
                        # Execute parallel tasks if any queued
                        if parallel_tasks:
                            parallel_results = await self._execute_parallel_tasks(parallel_tasks)
                            results.update(parallel_results)
                            parallel_tasks = []

                        # Execute sequential task
                        result = await self._execute_task(agent_name, action, context, results)
                        results[f"{agent_name}_{action}"] = result

                # Execute any remaining parallel tasks
                if parallel_tasks:
                    parallel_results = await self._execute_parallel_tasks(parallel_tasks)
                    results.update(parallel_results)

                # Update execution state
                self.execution_state[execution_id]["status"] = "completed"
                self.execution_state[execution_id]["completed_at"] = datetime.now(timezone.utc)
                self.execution_state[execution_id]["results"] = results

                logger.info("Workflow %s completed successfully", workflow_name)
                return {
                    "execution_id": execution_id,
                    "workflow": workflow_name,
                    "status": "completed",
                    "results": results,
                }

            except Exception as e:
                logger.error("Workflow %s failed: %s", workflow_name, str(e))
                self.execution_state[execution_id]["status"] = "failed"
                self.execution_state[execution_id]["error"] = str(e)
                return {
                    "execution_id": execution_id,
                    "workflow": workflow_name,
                    "status": "failed",
                    "error": str(e),
                }

        async def _execute_task(
            self, agent_name: str, action: str, context: dict, previous_results: dict
        ):
            """Execute a single task with retry logic"""
            for attempt in range(self.retry_attempts):
                try:
                    # Simulate task execution (would call actual agent in production)
                    logger.info("Executing %s.%s (attempt %d)", agent_name, action, attempt + 1)
                    await asyncio.sleep(0.1)  # Simulate work
                    return {
                        "status": "completed",
                        "agent": agent_name,
                        "action": action,
                        "attempt": attempt + 1,
                    }
                except Exception as e:
                    if attempt == self.retry_attempts - 1:
                        raise e
                    logger.warning("Task %s.%s failed, retrying: %s", agent_name, action, str(e))
                    await asyncio.sleep(2**attempt)  # Exponential backoff

        async def _execute_parallel_tasks(self, tasks: list):
            """Execute tasks in parallel with proper error handling"""
            results = {}
            futures = []

            for agent_name, action, context in tasks:
                future = asyncio.create_task(self._execute_task(agent_name, action, context, {}))
                futures.append((f"{agent_name}_{action}", future))

            for key, future in futures:
                try:
                    results[key] = await future
                except Exception as e:
                    logger.error("Parallel task %s failed: %s", key, str(e))
                    results[key] = {"status": "failed", "error": str(e)}

            return results

    class StateManager:
        def __init__(self, *args, **kwargs):
            """Initialize SPARC state manager with comprehensive state tracking and policy engine"""
            # Set up state tracking
            self.state = {}  # Current environment state
            self.state_history = []  # Historical states for analysis
            self.max_history_size = kwargs.get("max_history", 1000)

            # Initialize policy engine
            self.policy = self._initialize_policy()
            self.policy_parameters = {
                "learning_rate": kwargs.get("learning_rate", 0.01),
                "exploration_rate": kwargs.get("exploration_rate", 0.1),
                "discount_factor": kwargs.get("discount_factor", 0.95),
            }

            # Configure reward calculator
            self.reward_calculator = {
                "success_weight": kwargs.get("success_weight", 1.0),
                "efficiency_weight": kwargs.get("efficiency_weight", 0.5),
                "quality_weight": kwargs.get("quality_weight", 0.8),
                "user_satisfaction_weight": kwargs.get("user_satisfaction_weight", 1.2),
            }
            self.rewards = {}  # Reward tracking

            # Set up context window
            self.context = {}  # User context
            self.context_window_size = kwargs.get("context_window_size", 10)
            self.context_history = []

            logger.info("StateManager initialized with SPARC framework")

        def _initialize_policy(self):
            """Initialize educational policy with adaptive learning parameters"""
            return {
                "learning_style": "adaptive",
                "difficulty_adjustment": "dynamic",
                "feedback_frequency": "immediate",
                "assessment_interval": 5,  # Questions after 5 activities
                "reward_threshold": 0.7,  # 70% success for reward
                "personalization_enabled": True,
                "collaborative_learning": True,
            }

        async def execute_cycle(self, task: dict, user_context: dict = None):
            """Implement SPARC cycle execution with comprehensive state management"""
            cycle_id = str(uuid.uuid4())
            cycle_start = datetime.now(timezone.utc)

            try:
                # State: Observe current environment
                current_state = await self._observe_state()

                # Policy: Make decision based on state and context
                self.context = user_context or {}
                action = await self._apply_policy(current_state, self.context)

                # Action: Execute the decided action
                result = await self._execute_action(action)

                # Reward: Calculate learning outcome
                reward = await self._calculate_reward(result, current_state, action)

                # Context: Update for next cycle
                await self._update_context(action, result, reward)

                # Store cycle results
                cycle_result = {
                    "cycle_id": cycle_id,
                    "timestamp": cycle_start.isoformat(),
                    "state": current_state,
                    "action": action,
                    "result": result,
                    "reward": reward,
                    "context": self.context,
                    "execution_time": (datetime.now(timezone.utc) - cycle_start).total_seconds(),
                }

                # Update state history
                self._update_state_history(cycle_result)

                logger.info("SPARC cycle completed: Action=%s, Reward=%f", action["type"], reward)

                return cycle_result

            except Exception as e:
                logger.error("SPARC cycle failed: %s", str(e))
                return {
                    "cycle_id": cycle_id,
                    "timestamp": cycle_start.isoformat(),
                    "status": "failed",
                    "error": str(e),
                    "execution_time": (datetime.now(timezone.utc) - cycle_start).total_seconds(),
                }

        async def _observe_state(self):
            """Observe current environment state with comprehensive metrics"""
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "active_users": len(self.context.get("users", [])),
                "content_loaded": self.state.get("content_loaded", True),
                "quiz_active": self.state.get("quiz_active", False),
                "environment_ready": self.state.get("environment_ready", True),
                "system_performance": {
                    "cpu_usage": 0.3,  # Would be actual metrics in production
                    "memory_usage": 0.5,
                    "response_time": 0.1,
                },
                "learning_metrics": {
                    "engagement_level": self.context.get("engagement_level", 0.8),
                    "difficulty_level": self.context.get("difficulty_level", "medium"),
                    "progress_rate": self.context.get("progress_rate", 0.75),
                },
            }

        async def _apply_policy(self, state: dict, context: dict):
            """Apply policy to determine optimal action based on current state"""
            # Analyze current situation
            content_needed = not state.get("content_loaded", True)
            assessment_due = context.get("assessment_due", False)
            user_struggling = context.get("performance_score", 0.8) < 0.6
            engagement_low = state.get("learning_metrics", {}).get("engagement_level", 0.8) < 0.5

            # Policy decision logic
            if content_needed:
                action = {"type": "load_content", "priority": "high", "urgency": "immediate"}
            elif user_struggling:
                action = {
                    "type": "provide_assistance",
                    "priority": "high",
                    "method": "adaptive_hints",
                }
            elif engagement_low:
                action = {
                    "type": "increase_engagement",
                    "priority": "medium",
                    "method": "gamification",
                }
            elif assessment_due:
                action = {
                    "type": "start_assessment",
                    "priority": "medium",
                    "assessment_type": "adaptive",
                }
            else:
                action = {"type": "continue_lesson", "priority": "low", "mode": "standard"}

            # Add personalization parameters
            action["personalization"] = {
                "learning_style": context.get("learning_style", "visual"),
                "pace": context.get("preferred_pace", "normal"),
                "difficulty_preference": context.get("difficulty_preference", "adaptive"),
            }

            return action

        async def _execute_action(self, action: dict):
            """Execute the decided action with comprehensive result tracking"""
            action_start = datetime.now(timezone.utc)

            try:
                logger.info("Executing action: %s", action["type"])
                await asyncio.sleep(0.1)  # Simulate action execution

                result = {
                    "success": True,
                    "action_type": action["type"],
                    "execution_time": (datetime.now(timezone.utc) - action_start).total_seconds(),
                }

                return result

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "action_type": action["type"],
                    "execution_time": (datetime.now(timezone.utc) - action_start).total_seconds(),
                }

        async def _calculate_reward(self, result: dict, state: dict, action: dict):
            """Calculate reward based on learning outcomes and system performance"""
            base_reward = 1.0 if result.get("success", False) else 0.0

            # Performance-based adjustments
            execution_time = result.get("execution_time", 0)
            if execution_time < 0.1:
                efficiency_bonus = 0.2
            elif execution_time < 0.5:
                efficiency_bonus = 0.1
            else:
                efficiency_bonus = -0.1

            # Context-based adjustments
            context_bonus = 0.0
            if self.context.get("first_attempt", True):
                context_bonus += 0.2  # Bonus for first attempt success

            if action.get("priority") == "high" and result.get("success"):
                context_bonus += 0.3  # High priority task completion bonus

            # Calculate final reward
            total_reward = (
                base_reward * self.reward_calculator["success_weight"]
                + efficiency_bonus * self.reward_calculator["efficiency_weight"]
                + context_bonus * self.reward_calculator["quality_weight"]
            )

            return max(min(total_reward, 2.0), -1.0)  # Cap reward between -1 and 2

        async def _update_context(self, action: dict, result: dict, reward: float):
            """Update context for next cycle with comprehensive state tracking"""
            # Update action history
            self.context["last_action"] = action["type"]
            self.context["last_reward"] = reward
            self.context["total_rewards"] = self.context.get("total_rewards", 0) + reward
            self.context["action_count"] = self.context.get("action_count", 0) + 1

        def _update_state_history(self, cycle_result: dict):
            """Update state history with size management"""
            self.state_history.append(cycle_result)

            # Maintain history size limit
            if len(self.state_history) > self.max_history_size:
                self.state_history = self.state_history[-self.max_history_size :]

    class SwarmController:
        def __init__(self, num_workers: int = 5, *args, **kwargs):
            """Initialize swarm controller with worker pool and load balancing"""
            # Set up worker pool
            self.num_workers = num_workers
            self.workers = []
            self.task_queue = asyncio.Queue()
            self.results_queue = asyncio.Queue()
            self.active_tasks = {}

            # Configure load balancing
            self.load_balancer = {
                "strategy": kwargs.get("load_strategy", "round_robin"),
                "worker_loads": [0] * num_workers,
                "max_tasks_per_worker": kwargs.get("max_tasks_per_worker", 10),
            }

            # Initialize consensus mechanism
            self.consensus_config = {
                "threshold": kwargs.get("consensus_threshold", 0.7),
                "voting_method": kwargs.get("voting_method", "majority"),
                "min_votes": kwargs.get("min_votes", 3),
            }

            logger.info("SwarmController initialized with %d workers", num_workers)

        async def distribute_tasks(self, tasks: list, consensus_required: bool = False):
            """Implement task distribution with parallel execution and consensus"""
            if not tasks:
                return []

            logger.info("Distributing %d tasks across swarm", len(tasks))

            # Queue all tasks
            for task in tasks:
                await self.task_queue.put(task)

            # Start workers
            workers = [
                asyncio.create_task(self._worker(f"worker_{i}"))
                for i in range(min(self.num_workers, len(tasks)))
            ]

            # Wait for all tasks to complete
            await self.task_queue.join()

            # Cancel workers
            for worker in workers:
                worker.cancel()

            # Gather results
            results = []
            while not self.results_queue.empty():
                results.append(await self.results_queue.get())

            # Apply consensus if required
            if consensus_required and len(results) > 1:
                results = await self._apply_consensus(results)

            logger.info("Distributed %d tasks, completed %d", len(tasks), len(results))
            return results

        async def _worker(self, worker_id: str):
            """Worker coroutine for processing tasks with load balancing"""
            while True:
                try:
                    task = await self.task_queue.get()

                    # Update worker load
                    worker_index = int(worker_id.split("_")[1])
                    self.load_balancer["worker_loads"][worker_index] += 1

                    # Process task
                    result = await self._process_task(task, worker_id)
                    await self.results_queue.put(result)

                    # Update worker load
                    self.load_balancer["worker_loads"][worker_index] -= 1

                    self.task_queue.task_done()

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("Worker %s error: %s", worker_id, str(e))
                    self.task_queue.task_done()

        async def _process_task(self, task: dict, worker_id: str):
            """Process individual task with comprehensive result tracking"""
            task_start = datetime.now(timezone.utc)
            task_id = task.get("id", str(uuid.uuid4()))

            logger.debug("Worker %s processing task: %s", worker_id, task_id)

            try:
                # Simulate task processing based on task type
                task_type = task.get("type", "unknown")
                processing_time = task.get("complexity", 1) * 0.1  # Simulate variable complexity

                await asyncio.sleep(processing_time)

                # Generate result based on task type
                if task_type == "content_generation":
                    result_data = {
                        "content": f"Generated content for {task.get('topic', 'unknown')}",
                        "quality_score": 0.85,
                    }
                elif task_type == "quiz_generation":
                    result_data = {
                        "questions": [{"id": f"q{i}", "text": f"Question {i}"} for i in range(5)],
                        "difficulty": "medium",
                    }
                elif task_type == "terrain_generation":
                    result_data = {
                        "terrain_data": "3D terrain model",
                        "environment_type": task.get("environment", "classroom"),
                    }
                else:
                    result_data = {"processed": True, "task_type": task_type}

                return {
                    "task_id": task_id,
                    "worker": worker_id,
                    "result": result_data,
                    "status": "completed",
                    "execution_time": (datetime.now(timezone.utc) - task_start).total_seconds(),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            except Exception as e:
                return {
                    "task_id": task_id,
                    "worker": worker_id,
                    "status": "failed",
                    "error": str(e),
                    "execution_time": (datetime.now(timezone.utc) - task_start).total_seconds(),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        async def _apply_consensus(self, results: list):
            """Apply consensus mechanism to results using voting"""
            if len(results) < self.consensus_config["min_votes"]:
                logger.warning(
                    "Insufficient results for consensus: %d < %d",
                    len(results),
                    self.consensus_config["min_votes"],
                )
                return results

            consensus_results = []

            # Group results by task_id
            grouped_results = {}
            for result in results:
                task_id = result.get("task_id")
                if task_id not in grouped_results:
                    grouped_results[task_id] = []
                grouped_results[task_id].append(result)

            # Apply consensus to each group
            for task_id, group in grouped_results.items():
                if len(group) == 1:
                    consensus_results.extend(group)
                    continue

                # Voting-based consensus
                if self.consensus_config["voting_method"] == "majority":
                    consensus_result = self._majority_vote(group)
                elif self.consensus_config["voting_method"] == "quality_weighted":
                    consensus_result = self._quality_weighted_vote(group)
                else:
                    consensus_result = group[0]  # Fallback to first result

                # Check if consensus threshold is met
                consensus_score = self._calculate_consensus_score(group, consensus_result)
                if consensus_score >= self.consensus_config["threshold"]:
                    consensus_result["consensus_score"] = consensus_score
                    consensus_result["consensus_achieved"] = True
                    consensus_results.append(consensus_result)
                else:
                    # If consensus not achieved, return all results with flag
                    for result in group:
                        result["consensus_achieved"] = False
                        result["consensus_score"] = consensus_score
                    consensus_results.extend(group)

            return consensus_results

        def _majority_vote(self, results: list):
            """Apply majority voting to select best result"""
            # Simple majority vote based on success status
            successful_results = [r for r in results if r.get("status") == "completed"]

            if successful_results:
                # Return result with best execution time among successful ones
                return min(successful_results, key=lambda r: r.get("execution_time", float("inf")))
            else:
                # If no successful results, return the one with least severe error
                return min(results, key=lambda r: len(r.get("error", "")))

        def _quality_weighted_vote(self, results: list):
            """Apply quality-weighted voting to select best result"""

            def calculate_quality_score(result):
                base_score = 1.0 if result.get("status") == "completed" else 0.0

                # Execution time factor (faster is better)
                time_factor = max(0, 1.0 - result.get("execution_time", 1.0))

                # Quality score from result data
                quality_score = result.get("result", {}).get("quality_score", 0.5)

                return base_score * 0.5 + time_factor * 0.2 + quality_score * 0.3

            # Return result with highest quality score
            return max(results, key=calculate_quality_score)

        def _calculate_consensus_score(self, results: list, consensus_result: dict):
            """Calculate consensus score based on agreement between results"""
            if len(results) <= 1:
                return 1.0

            agreement_count = 0
            total_comparisons = 0

            for result in results:
                total_comparisons += 1

                # Check status agreement
                if result.get("status") == consensus_result.get("status"):
                    agreement_count += 0.5

                # Check execution time similarity (within 50% range)
                consensus_time = consensus_result.get("execution_time", 0)
                result_time = result.get("execution_time", 0)
                if consensus_time > 0 and abs(result_time - consensus_time) / consensus_time < 0.5:
                    agreement_count += 0.5

            return agreement_count / total_comparisons if total_comparisons > 0 else 0.0

        def get_swarm_metrics(self):
            """Get comprehensive swarm performance metrics"""
            return {
                "workers": {
                    "total_workers": self.num_workers,
                    "worker_loads": self.load_balancer["worker_loads"],
                    "average_load": sum(self.load_balancer["worker_loads"]) / self.num_workers,
                },
                "tasks": {
                    "queue_size": self.task_queue.qsize(),
                    "results_pending": self.results_queue.qsize(),
                    "active_tasks": len(self.active_tasks),
                },
                "consensus": {
                    "threshold": self.consensus_config["threshold"],
                    "voting_method": self.consensus_config["voting_method"],
                    "min_votes": self.consensus_config["min_votes"],
                },
            }

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
            self.context_history.append(
                {"timestamp": datetime.now(timezone.utc), "key": key, "value": value}
            )
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
        from langchain_openai import ChatOpenAI

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

    def _aggregate_content_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
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

    async def _aggregate_quiz_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
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
            best_result["quiz"]["questions"] = unique_questions[:20]  # Limit to 20 questions

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
            aggregated["content"] = await self._aggregate_content_results(content_results)

        if quiz_results:
            aggregated["quiz"] = await self._aggregate_quiz_results(quiz_results)

        return aggregated

    async def _default_aggregation(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
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
            await self.mcp_context.update_context(
                "learning_objectives", request.learning_objectives
            )

            # 2. Initialize SPARC state for this task
            sparc_state = await self.sparc_manager.initialize_state(
                {
                    "task_id": task_id,
                    "environment": request.environment_type,
                    "subject": request.subject,
                    "grade_level": request.grade_level,
                    "objectives": request.learning_objectives,
                    "user_context": {
                        "user_id": user.id if user else None,
                        "role": user.role if user else None,
                    },
                }
            )

            # 3. Route task to appropriate agents
            agent_types = await self.task_router.route_task("generate_content", request.dict())

            logger.info(f"Task {task_id} routed to agents: {agent_types}")

            # 4. Use Swarm for parallel agent execution
            swarm_tasks = []
            for agent_type in agent_types:
                swarm_tasks.append(
                    {
                        "agent_type": agent_type,
                        "request": request.dict(),
                        "task_id": task_id,
                        "context": await self.mcp_context.get_context(),
                    }
                )

            # Execute via swarm controller for parallel processing
            if hasattr(self.swarm_controller, "distribute_tasks"):
                swarm_results = await self.swarm_controller.distribute_tasks(swarm_tasks)
            else:
                # Fallback to regular parallel execution
                swarm_results = await self._execute_agents_parallel(agent_types, request, task_id)

            # 5. Update SPARC state with agent results
            await self.sparc_manager.update_state(
                {
                    "task_id": task_id,
                    "agent_results": swarm_results,
                    "action": "content_generation_complete",
                }
            )

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
                    "mcp_context": await self.mcp_context.get_context(),
                }
            )

            # 9. Calculate reward using SPARC
            reward = await self.sparc_manager.calculate_reward(
                {
                    "task_id": task_id,
                    "result": final_result,
                    "objectives_met": len(request.learning_objectives),
                    "execution_time": (datetime.now(timezone.utc) - start_time).total_seconds(),
                }
            )

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
            await self.mcp_server.broadcast_context(
                {"task_id": task_id, "status": "completed", "reward": reward, "content_id": task_id}
            )

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
                    status["available"] + status["active"] > 0 for status in pool_status.values()
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
