"""
Enhanced SPARC Framework Orchestrator
====================================

Advanced orchestration system that integrates all SPARC components for optimal
educational content generation with real-time adaptation and performance optimization.

Features:
- Intelligent agent coordination with specialization
- Real-time performance monitoring and optimization
- Educational quality assessment and improvement
- Adaptive learning pathways
- Multi-modal content generation
- Comprehensive error handling and recovery
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from core.agents.base_agent import BaseAgent
from core.swarm import SwarmController, create_educational_swarm

from .action_executor import ActionExecutor
from .context_tracker import ContextTracker
from .policy_engine import PolicyEngine
from .reward_calculator import RewardCalculator
from .state_manager import StateManager

logger = logging.getLogger(__name__)


class OrchestrationStrategy(Enum):
    """Orchestration strategies for different educational scenarios"""
    SEQUENTIAL = "sequential"          # One agent at a time
    PARALLEL = "parallel"             # Multiple agents simultaneously
    COMPETITIVE = "competitive"       # Agents compete for best result
    COLLABORATIVE = "collaborative"   # Agents work together
    ADAPTIVE = "adaptive"             # Strategy adapts based on context
    SWARM_INTELLIGENCE = "swarm"     # Full swarm coordination


class QualityThreshold(Enum):
    """Quality thresholds for educational content"""
    MINIMUM = 0.6
    ACCEPTABLE = 0.7
    GOOD = 0.8
    EXCELLENT = 0.9


@dataclass
class OrchestrationConfig:
    """Configuration for enhanced orchestration"""
    strategy: OrchestrationStrategy = OrchestrationStrategy.ADAPTIVE
    quality_threshold: float = QualityThreshold.GOOD.value
    max_concurrent_agents: int = 5
    timeout_seconds: int = 300
    retry_attempts: int = 3
    enable_swarm_mode: bool = True
    adaptive_optimization: bool = True
    real_time_monitoring: bool = True
    educational_analytics: bool = True

    # Agent specialization settings
    content_specialists: int = 2
    quiz_specialists: int = 1
    terrain_specialists: int = 1
    review_specialists: int = 1

    # Performance optimization
    cache_enabled: bool = True
    compression_enabled: bool = True
    load_balancing: bool = True


@dataclass
class OrchestrationResult:
    """Result of orchestrated content generation"""
    success: bool
    orchestration_id: str
    generated_content: dict[str, Any]
    quality_metrics: dict[str, float]
    execution_time: float
    agents_used: list[str]
    strategy_applied: OrchestrationStrategy
    educational_analytics: dict[str, Any]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    optimization_suggestions: list[str] = field(default_factory=list)


class EnhancedSPARCOrchestrator:
    """
    Enhanced SPARC Framework Orchestrator

    Provides intelligent coordination of all SPARC components with advanced
    educational optimization, real-time adaptation, and performance monitoring.
    """

    def __init__(self, config: OrchestrationConfig = None):
        """Initialize enhanced orchestrator"""
        self.config = config or OrchestrationConfig()
        self.orchestration_id = str(uuid4())

        # Core SPARC components
        self.state_manager = StateManager(
            history_size=2000,
            compression_threshold=1000,
            persistence_interval=30.0,
            prediction_enabled=True
        )

        self.policy_engine = PolicyEngine()
        self.action_executor = ActionExecutor(
            max_parallel=self.config.max_concurrent_agents,
            timeout=self.config.timeout_seconds,
            retry_attempts=self.config.retry_attempts
        )
        self.reward_calculator = RewardCalculator()
        self.context_tracker = ContextTracker()

        # Swarm intelligence
        self.swarm_controller: Optional[SwarmController] = None
        self.swarm_enabled = self.config.enable_swarm_mode

        # Agent management
        self.specialized_agents: dict[str, list[BaseAgent]] = {}
        self.agent_performance: dict[str, dict[str, Any]] = {}

        # Orchestration tracking
        self.active_orchestrations: dict[str, dict[str, Any]] = {}
        self.orchestration_history: list[OrchestrationResult] = []

        # Performance optimization
        self.content_cache: dict[str, Any] = {}
        self.quality_assessor = EducationalQualityAssessor()
        self.performance_optimizer = PerformanceOptimizer()

        # Real-time monitoring
        self.monitoring_enabled = self.config.real_time_monitoring
        self.monitoring_tasks: set[asyncio.Task] = set()

        logger.info(f"Enhanced SPARC Orchestrator initialized with strategy: {self.config.strategy}")

    async def initialize(self) -> None:
        """Initialize all orchestrator components"""
        try:
            # Initialize core components
            await self.state_manager.initialize_state({
                "orchestrator_id": self.orchestration_id,
                "strategy": self.config.strategy.value,
                "initialization_time": datetime.now().isoformat()
            })

            await self.policy_engine.initialize()
            await self.context_tracker.initialize()

            # Initialize swarm if enabled
            if self.swarm_enabled:
                self.swarm_controller = await create_educational_swarm(
                    max_workers=self.config.max_concurrent_agents
                )
                await self.swarm_controller.initialize()

            # Initialize specialized agents
            await self._initialize_specialized_agents()

            # Start monitoring if enabled
            if self.monitoring_enabled:
                await self._start_real_time_monitoring()

            logger.info("Enhanced SPARC Orchestrator fully initialized")

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise

    async def generate_educational_content(
        self,
        request: dict[str, Any],
        strategy: Optional[OrchestrationStrategy] = None
    ) -> OrchestrationResult:
        """
        Generate educational content using enhanced orchestration

        Args:
            request: Content generation request with educational parameters
            strategy: Optional specific strategy to use

        Returns:
            OrchestrationResult with generated content and analytics
        """
        start_time = time.time()
        orchestration_id = str(uuid4())

        try:
            # Extract and validate educational context
            educational_context = self._extract_educational_context(request)
            await self._validate_educational_requirements(educational_context)

            # Determine optimal orchestration strategy
            effective_strategy = strategy or await self._determine_optimal_strategy(
                educational_context
            )

            # Update state with orchestration start
            await self.state_manager.update_state({
                "type": "orchestration_start",
                "orchestration_id": orchestration_id,
                "strategy": effective_strategy.value,
                "educational_context": educational_context,
                "timestamp": datetime.now().isoformat()
            })

            # Track active orchestration
            self.active_orchestrations[orchestration_id] = {
                "start_time": start_time,
                "strategy": effective_strategy,
                "context": educational_context,
                "agents_allocated": [],
                "progress": 0.0
            }

            # Execute orchestration based on strategy
            result = await self._execute_orchestration_strategy(
                orchestration_id,
                effective_strategy,
                educational_context,
                request
            )

            # Calculate execution time
            execution_time = time.time() - start_time

            # Assess educational quality
            quality_metrics = await self.quality_assessor.assess_content_quality(
                result.get("content", {}),
                educational_context
            )

            # Calculate educational analytics
            educational_analytics = await self._calculate_educational_analytics(
                result,
                educational_context,
                execution_time
            )

            # Create orchestration result
            orchestration_result = OrchestrationResult(
                success=True,
                orchestration_id=orchestration_id,
                generated_content=result,
                quality_metrics=quality_metrics,
                execution_time=execution_time,
                agents_used=self.active_orchestrations[orchestration_id]["agents_allocated"],
                strategy_applied=effective_strategy,
                educational_analytics=educational_analytics
            )

            # Update state with completion
            await self.state_manager.update_state({
                "type": "orchestration_complete",
                "orchestration_id": orchestration_id,
                "success": True,
                "execution_time": execution_time,
                "quality_metrics": quality_metrics,
                "timestamp": datetime.now().isoformat()
            })

            # Store in history
            self.orchestration_history.append(orchestration_result)

            # Clean up active orchestration
            del self.active_orchestrations[orchestration_id]

            logger.info(
                f"Educational content generation completed: {orchestration_id} "
                f"(time: {execution_time:.2f}s, quality: {quality_metrics.get('overall_quality', 0):.2f})"
            )

            return orchestration_result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Orchestration failed: {str(e)}"
            logger.error(f"{error_msg} (ID: {orchestration_id})")

            # Update state with failure
            await self.state_manager.update_state({
                "type": "orchestration_failed",
                "orchestration_id": orchestration_id,
                "error": str(e),
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            })

            # Clean up if needed
            self.active_orchestrations.pop(orchestration_id, None)

            # Return failure result
            return OrchestrationResult(
                success=False,
                orchestration_id=orchestration_id,
                generated_content={},
                quality_metrics={},
                execution_time=execution_time,
                agents_used=[],
                strategy_applied=strategy or OrchestrationStrategy.SEQUENTIAL,
                educational_analytics={},
                errors=[error_msg]
            )

    async def _execute_orchestration_strategy(
        self,
        orchestration_id: str,
        strategy: OrchestrationStrategy,
        educational_context: dict[str, Any],
        request: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute specific orchestration strategy"""

        if strategy == OrchestrationStrategy.SEQUENTIAL:
            return await self._execute_sequential_strategy(
                orchestration_id, educational_context, request
            )
        elif strategy == OrchestrationStrategy.PARALLEL:
            return await self._execute_parallel_strategy(
                orchestration_id, educational_context, request
            )
        elif strategy == OrchestrationStrategy.COMPETITIVE:
            return await self._execute_competitive_strategy(
                orchestration_id, educational_context, request
            )
        elif strategy == OrchestrationStrategy.COLLABORATIVE:
            return await self._execute_collaborative_strategy(
                orchestration_id, educational_context, request
            )
        elif strategy == OrchestrationStrategy.SWARM_INTELLIGENCE:
            return await self._execute_swarm_strategy(
                orchestration_id, educational_context, request
            )
        elif strategy == OrchestrationStrategy.ADAPTIVE:
            return await self._execute_adaptive_strategy(
                orchestration_id, educational_context, request
            )
        else:
            raise ValueError(f"Unknown orchestration strategy: {strategy}")

    async def _execute_swarm_strategy(
        self,
        orchestration_id: str,
        educational_context: dict[str, Any],
        request: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute swarm intelligence strategy for optimal content generation"""

        if not self.swarm_controller:
            logger.warning("Swarm controller not available, falling back to parallel strategy")
            return await self._execute_parallel_strategy(orchestration_id, educational_context, request)

        # Create swarm tasks for different content components
        swarm_tasks = []

        # Main content generation task
        content_task = {
            "task_id": f"{orchestration_id}_content",
            "type": "content_generation",
            "priority": "high",
            "context": educational_context,
            "parameters": request,
            "specializations": ["content_generation", "curriculum_design"]
        }
        swarm_tasks.append(content_task)

        # Quiz generation if requested
        if request.get("include_quiz", False):
            quiz_task = {
                "task_id": f"{orchestration_id}_quiz",
                "type": "quiz_creation",
                "priority": "medium",
                "context": educational_context,
                "parameters": {**request, "content_type": "quiz"},
                "specializations": ["assessment_creation", "question_generation"]
            }
            swarm_tasks.append(quiz_task)

        # Terrain/environment generation if Roblox content
        if request.get("environment_type") == "roblox":
            terrain_task = {
                "task_id": f"{orchestration_id}_terrain",
                "type": "terrain_generation",
                "priority": "medium",
                "context": educational_context,
                "parameters": {**request, "content_type": "environment"},
                "specializations": ["3d_modeling", "environment_design"]
            }
            swarm_tasks.append(terrain_task)

        # Execute swarm tasks
        try:
            results = await self.swarm_controller.execute_batch_tasks(swarm_tasks)

            # Track agents used
            agents_used = []
            for task_result in results:
                if "worker_id" in task_result:
                    agents_used.append(task_result["worker_id"])

            self.active_orchestrations[orchestration_id]["agents_allocated"] = agents_used

            # Combine results
            combined_result = {
                "strategy": "swarm_intelligence",
                "orchestration_id": orchestration_id,
                "content": {},
                "scripts": [],
                "assets": [],
                "swarm_metrics": {}
            }

            for task_result in results:
                task_type = task_result.get("task_type", "unknown")
                if task_type == "content_generation":
                    combined_result["content"].update(task_result.get("content", {}))
                elif task_type == "quiz_creation":
                    combined_result["quiz_data"] = task_result.get("content", {})
                elif task_type == "terrain_generation":
                    combined_result["environment_data"] = task_result.get("content", {})

                # Collect scripts and assets
                combined_result["scripts"].extend(task_result.get("scripts", []))
                combined_result["assets"].extend(task_result.get("assets", []))

            # Add swarm performance metrics
            combined_result["swarm_metrics"] = {
                "tasks_executed": len(swarm_tasks),
                "workers_used": len(set(agents_used)),
                "parallel_efficiency": len(swarm_tasks) / max(1, len(set(agents_used))),
                "consensus_quality": await self._calculate_swarm_consensus_quality(results)
            }

            return combined_result

        except Exception as e:
            logger.error(f"Swarm strategy execution failed: {e}")
            # Fallback to collaborative strategy
            return await self._execute_collaborative_strategy(orchestration_id, educational_context, request)

    async def _execute_collaborative_strategy(
        self,
        orchestration_id: str,
        educational_context: dict[str, Any],
        request: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute collaborative strategy where agents work together"""

        # Phase 1: Content ideation and planning
        planning_agents = await self._get_specialized_agents("content_planning", 2)
        planning_results = []

        for agent in planning_agents:
            planning_context = {
                **educational_context,
                "phase": "planning",
                "collaboration_mode": True
            }
            result = await agent.execute(planning_context)
            planning_results.append(result)

        # Synthesize planning results
        combined_plan = await self._synthesize_planning_results(planning_results)

        # Phase 2: Collaborative content generation
        content_agents = await self._get_specialized_agents("content_generation", 2)
        generation_tasks = []

        for i, agent in enumerate(content_agents):
            agent_context = {
                **educational_context,
                "phase": "generation",
                "collaboration_plan": combined_plan,
                "agent_role": f"generator_{i+1}",
                "peer_coordination": True
            }
            task = asyncio.create_task(agent.execute(agent_context))
            generation_tasks.append(task)

        # Wait for generation completion
        generation_results = await asyncio.gather(*generation_tasks)

        # Phase 3: Collaborative review and synthesis
        review_agent = await self._get_specialized_agents("content_review", 1)
        if review_agent:
            review_context = {
                **educational_context,
                "phase": "review",
                "content_variants": generation_results,
                "synthesis_required": True
            }
            final_result = await review_agent[0].execute(review_context)
        else:
            # Manual synthesis if no review agent
            final_result = await self._synthesize_generation_results(generation_results)

        # Track collaboration metrics
        collaboration_metrics = {
            "agents_collaborated": len(planning_agents) + len(content_agents) + (1 if review_agent else 0),
            "phases_completed": 3,
            "consensus_score": await self._calculate_collaboration_consensus(generation_results),
            "synthesis_quality": await self._assess_synthesis_quality(final_result, educational_context)
        }

        return {
            "strategy": "collaborative",
            "orchestration_id": orchestration_id,
            "content": final_result.get("content", {}),
            "scripts": final_result.get("scripts", []),
            "assets": final_result.get("assets", []),
            "collaboration_metrics": collaboration_metrics,
            "planning_data": combined_plan
        }

    async def _execute_adaptive_strategy(
        self,
        orchestration_id: str,
        educational_context: dict[str, Any],
        request: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute adaptive strategy that changes based on context and performance"""

        # Analyze context to determine best initial strategy
        initial_strategy = await self._analyze_context_for_strategy(educational_context, request)

        logger.info(f"Adaptive strategy starting with: {initial_strategy.value}")

        # Execute initial strategy
        try:
            result = await self._execute_orchestration_strategy(
                orchestration_id, initial_strategy, educational_context, request
            )

            # Assess result quality
            quality_score = await self._assess_intermediate_quality(result, educational_context)

            # Adapt if quality is below threshold
            if quality_score < self.config.quality_threshold:
                logger.info(f"Quality below threshold ({quality_score:.2f}), adapting strategy")

                # Try a different strategy
                adaptive_strategy = await self._select_adaptive_strategy(
                    initial_strategy, quality_score, educational_context
                )

                if adaptive_strategy != initial_strategy:
                    logger.info(f"Switching to adaptive strategy: {adaptive_strategy.value}")

                    # Execute new strategy
                    adaptive_result = await self._execute_orchestration_strategy(
                        orchestration_id, adaptive_strategy, educational_context, request
                    )

                    # Compare results and use better one
                    adaptive_quality = await self._assess_intermediate_quality(
                        adaptive_result, educational_context
                    )

                    if adaptive_quality > quality_score:
                        result = adaptive_result
                        result["adaptation_applied"] = True
                        result["original_strategy"] = initial_strategy.value
                        result["final_strategy"] = adaptive_strategy.value
                        result["quality_improvement"] = adaptive_quality - quality_score

            result["adaptive_metrics"] = {
                "initial_strategy": initial_strategy.value,
                "final_quality": await self._assess_intermediate_quality(result, educational_context),
                "adaptation_triggered": "adaptation_applied" in result
            }

            return result

        except Exception as e:
            logger.error(f"Adaptive strategy failed: {e}")
            # Fallback to simple sequential strategy
            return await self._execute_sequential_strategy(orchestration_id, educational_context, request)

    # Helper methods for orchestration

    async def _determine_optimal_strategy(self, educational_context: dict[str, Any]) -> OrchestrationStrategy:
        """Determine optimal orchestration strategy based on context"""

        if not self.config.adaptive_optimization:
            return self.config.strategy

        # Analyze context factors
        complexity_score = self._calculate_content_complexity(educational_context)
        urgency_score = self._calculate_urgency_score(educational_context)
        resource_availability = await self._assess_resource_availability()

        # Strategy selection logic
        if complexity_score > 0.8 and resource_availability > 0.7:
            return OrchestrationStrategy.SWARM_INTELLIGENCE
        elif complexity_score > 0.6 and resource_availability > 0.5:
            return OrchestrationStrategy.COLLABORATIVE
        elif urgency_score > 0.8:
            return OrchestrationStrategy.PARALLEL
        elif complexity_score < 0.3:
            return OrchestrationStrategy.SEQUENTIAL
        else:
            return OrchestrationStrategy.ADAPTIVE

    def _calculate_content_complexity(self, educational_context: dict[str, Any]) -> float:
        """Calculate content complexity score (0-1)"""
        complexity_factors = []

        # Grade level factor
        grade_level = educational_context.get("grade_level", 5)
        complexity_factors.append(min(1.0, grade_level / 12.0))

        # Subject complexity
        subject_complexity = {
            "math": 0.8, "science": 0.9, "physics": 0.95, "chemistry": 0.9,
            "english": 0.6, "history": 0.7, "geography": 0.5, "art": 0.4
        }
        subject = educational_context.get("subject_area", "").lower()
        complexity_factors.append(subject_complexity.get(subject, 0.5))

        # Learning objectives count
        objectives = educational_context.get("learning_objectives", [])
        complexity_factors.append(min(1.0, len(objectives) / 5.0))

        # Content type complexity
        content_type_complexity = {
            "lesson": 0.6, "quiz": 0.4, "project": 0.9,
            "simulation": 0.95, "assessment": 0.7
        }
        content_type = educational_context.get("content_type", "lesson")
        complexity_factors.append(content_type_complexity.get(content_type, 0.5))

        return sum(complexity_factors) / len(complexity_factors) if complexity_factors else 0.5

    def _calculate_urgency_score(self, educational_context: dict[str, Any]) -> float:
        """Calculate urgency score based on deadlines and priorities"""
        urgency_factors = []

        # Check for deadline
        deadline = educational_context.get("deadline")
        if deadline:
            try:
                deadline_dt = datetime.fromisoformat(deadline)
                time_remaining = (deadline_dt - datetime.now()).total_seconds()
                if time_remaining > 0:
                    # Higher urgency as deadline approaches
                    urgency_factors.append(max(0.0, 1.0 - (time_remaining / 86400)))  # 24 hours baseline
                else:
                    urgency_factors.append(1.0)  # Past deadline
            except:
                urgency_factors.append(0.5)  # Default if parsing fails

        # Priority level
        priority = educational_context.get("priority", "normal")
        priority_scores = {"low": 0.2, "normal": 0.5, "high": 0.8, "critical": 1.0}
        urgency_factors.append(priority_scores.get(priority, 0.5))

        return sum(urgency_factors) / len(urgency_factors) if urgency_factors else 0.5

    async def _assess_resource_availability(self) -> float:
        """Assess available computational resources"""
        resource_factors = []

        # Agent availability
        available_agents = sum(len(agents) for agents in self.specialized_agents.values())
        max_agents = self.config.max_concurrent_agents * 4  # Estimate total capacity
        resource_factors.append(available_agents / max(1, max_agents))

        # Swarm availability
        if self.swarm_controller:
            swarm_capacity = await self.swarm_controller.get_capacity_status()
            resource_factors.append(swarm_capacity.get("available_capacity", 0.5))

        # System load (simplified)
        active_orchestrations = len(self.active_orchestrations)
        max_concurrent = 5  # Estimated max concurrent orchestrations
        load_factor = 1.0 - (active_orchestrations / max(1, max_concurrent))
        resource_factors.append(max(0.0, load_factor))

        return sum(resource_factors) / len(resource_factors) if resource_factors else 0.5

    async def _initialize_specialized_agents(self):
        """Initialize pools of specialized agents for different tasks"""

        specialization_configs = {
            "content_generation": self.config.content_specialists,
            "quiz_creation": self.config.quiz_specialists,
            "terrain_generation": self.config.terrain_specialists,
            "content_review": self.config.review_specialists,
            "content_planning": 2,
            "quality_assessment": 1
        }

        for specialization, count in specialization_configs.items():
            agents = []
            for i in range(count):
                agent = await self._create_specialized_agent(specialization, i)
                if agent:
                    agents.append(agent)

            self.specialized_agents[specialization] = agents
            logger.info(f"Initialized {len(agents)} agents for {specialization}")

    async def _create_specialized_agent(self, specialization: str, agent_id: int) -> Optional[BaseAgent]:
        """Create a specialized agent for specific tasks"""
        try:
            # This would integrate with the actual agent creation system
            # For now, we'll create a mock specialized agent

            from core.agents.base_agent import AgentCapability, AgentConfig, BaseAgent

            config = AgentConfig(
                agent_id=f"{specialization}_{agent_id}",
                name=f"{specialization.title()} Agent {agent_id}",
                capabilities=[
                    AgentCapability.CONTENT_GENERATION if "content" in specialization
                    else AgentCapability.ASSESSMENT_CREATION if "quiz" in specialization
                    else AgentCapability.ENVIRONMENT_DESIGN if "terrain" in specialization
                    else AgentCapability.QUALITY_REVIEW
                ],
                specialization=specialization,
                educational_focus=True
            )

            agent = BaseAgent(config)
            await agent.initialize()

            return agent

        except Exception as e:
            logger.error(f"Failed to create specialized agent {specialization}_{agent_id}: {e}")
            return None

    async def _get_specialized_agents(self, specialization: str, count: int) -> list[BaseAgent]:
        """Get available specialized agents for a task"""
        available_agents = self.specialized_agents.get(specialization, [])

        # Return up to the requested count of agents
        return available_agents[:count]

    def _extract_educational_context(self, request: dict[str, Any]) -> dict[str, Any]:
        """Extract educational context from request"""
        return {
            "subject_area": request.get("subject", "general"),
            "grade_level": request.get("grade_level", 5),
            "learning_objectives": request.get("learning_objectives", []),
            "content_type": request.get("content_type", "lesson"),
            "difficulty_level": request.get("difficulty", "medium"),
            "student_profile": request.get("student_profile", {}),
            "curriculum_standards": request.get("curriculum_standards", []),
            "accessibility_requirements": request.get("accessibility", []),
            "time_constraints": request.get("time_limit"),
            "priority": request.get("priority", "normal")
        }

    async def _validate_educational_requirements(self, educational_context: dict[str, Any]):
        """Validate educational requirements are met"""
        required_fields = ["subject_area", "grade_level"]

        for field in required_fields:
            if not educational_context.get(field):
                raise ValueError(f"Missing required educational field: {field}")

        # Validate grade level
        grade_level = educational_context["grade_level"]
        if not isinstance(grade_level, int) or not (1 <= grade_level <= 12):
            raise ValueError(f"Invalid grade level: {grade_level} (must be 1-12)")

    async def _start_real_time_monitoring(self):
        """Start real-time monitoring tasks"""
        if not self.monitoring_enabled:
            return

        # Start performance monitoring
        perf_task = asyncio.create_task(self._monitor_performance())
        self.monitoring_tasks.add(perf_task)
        perf_task.add_done_callback(self.monitoring_tasks.discard)

        # Start quality monitoring
        quality_task = asyncio.create_task(self._monitor_quality())
        self.monitoring_tasks.add(quality_task)
        quality_task.add_done_callback(self.monitoring_tasks.discard)

        # Start resource monitoring
        resource_task = asyncio.create_task(self._monitor_resources())
        self.monitoring_tasks.add(resource_task)
        resource_task.add_done_callback(self.monitoring_tasks.discard)

        logger.info("Real-time monitoring started")

    async def _monitor_performance(self):
        """Monitor orchestration performance"""
        while self.monitoring_enabled:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds

                # Analyze current performance
                performance_metrics = await self._calculate_performance_metrics()

                # Log performance insights
                if performance_metrics["average_execution_time"] > 120:  # > 2 minutes
                    logger.warning(f"High execution times detected: {performance_metrics['average_execution_time']:.1f}s")

                if performance_metrics["success_rate"] < 0.8:  # < 80% success
                    logger.warning(f"Low success rate detected: {performance_metrics['success_rate']:.2f}")

                # Store performance data
                await self.state_manager.update_state({
                    "type": "performance_monitoring",
                    "metrics": performance_metrics,
                    "timestamp": datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer before retry

    async def _monitor_quality(self):
        """Monitor educational content quality"""
        while self.monitoring_enabled:
            try:
                await asyncio.sleep(45)  # Monitor every 45 seconds

                # Analyze recent quality metrics
                quality_trends = await self._analyze_quality_trends()

                # Alert on quality issues
                if quality_trends["average_quality"] < self.config.quality_threshold:
                    logger.warning(f"Quality below threshold: {quality_trends['average_quality']:.2f}")

                # Store quality data
                await self.state_manager.update_state({
                    "type": "quality_monitoring",
                    "trends": quality_trends,
                    "timestamp": datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Quality monitoring error: {e}")
                await asyncio.sleep(60)

    async def _monitor_resources(self):
        """Monitor system resources and capacity"""
        while self.monitoring_enabled:
            try:
                await asyncio.sleep(20)  # Monitor every 20 seconds

                # Check resource utilization
                resource_status = await self._get_resource_status()

                # Alert on resource constraints
                if resource_status["cpu_usage"] > 0.9:
                    logger.warning(f"High CPU usage: {resource_status['cpu_usage']:.2f}")

                if resource_status["memory_usage"] > 0.85:
                    logger.warning(f"High memory usage: {resource_status['memory_usage']:.2f}")

                # Store resource data
                await self.state_manager.update_state({
                    "type": "resource_monitoring",
                    "status": resource_status,
                    "timestamp": datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(60)

    async def get_orchestration_status(self) -> dict[str, Any]:
        """Get comprehensive orchestration status"""
        return {
            "orchestrator_id": self.orchestration_id,
            "config": {
                "strategy": self.config.strategy.value,
                "quality_threshold": self.config.quality_threshold,
                "max_concurrent_agents": self.config.max_concurrent_agents,
                "swarm_enabled": self.swarm_enabled
            },
            "active_orchestrations": len(self.active_orchestrations),
            "total_orchestrations": len(self.orchestration_history),
            "specialized_agents": {
                spec: len(agents) for spec, agents in self.specialized_agents.items()
            },
            "monitoring_active": self.monitoring_enabled,
            "swarm_status": await self._get_swarm_status() if self.swarm_controller else None,
            "performance_summary": await self._get_performance_summary()
        }

    async def shutdown(self):
        """Gracefully shutdown orchestrator"""
        logger.info("Shutting down Enhanced SPARC Orchestrator")

        # Stop monitoring
        self.monitoring_enabled = False
        for task in self.monitoring_tasks:
            task.cancel()

        # Wait for active orchestrations to complete
        if self.active_orchestrations:
            logger.info(f"Waiting for {len(self.active_orchestrations)} active orchestrations to complete")
            while self.active_orchestrations:
                await asyncio.sleep(1)

        # Shutdown swarm
        if self.swarm_controller:
            await self.swarm_controller.shutdown()

        # Shutdown agents
        for agent_list in self.specialized_agents.values():
            for agent in agent_list:
                if hasattr(agent, 'shutdown'):
                    await agent.shutdown()

        logger.info("Enhanced SPARC Orchestrator shutdown complete")


# Supporting classes for enhanced orchestration

class EducationalQualityAssessor:
    """Assesses educational quality of generated content"""

    async def assess_content_quality(
        self,
        content: dict[str, Any],
        educational_context: dict[str, Any]
    ) -> dict[str, float]:
        """Assess educational quality metrics"""

        quality_metrics = {
            "overall_quality": 0.0,
            "content_appropriateness": 0.0,
            "learning_objective_alignment": 0.0,
            "engagement_potential": 0.0,
            "accessibility_score": 0.0,
            "curriculum_compliance": 0.0
        }

        if not content:
            return quality_metrics

        # Content appropriateness assessment
        quality_metrics["content_appropriateness"] = self._assess_content_appropriateness(
            content, educational_context
        )

        # Learning objective alignment
        quality_metrics["learning_objective_alignment"] = self._assess_objective_alignment(
            content, educational_context
        )

        # Engagement potential
        quality_metrics["engagement_potential"] = self._assess_engagement_potential(content)

        # Accessibility score
        quality_metrics["accessibility_score"] = self._assess_accessibility(content)

        # Curriculum compliance
        quality_metrics["curriculum_compliance"] = self._assess_curriculum_compliance(
            content, educational_context
        )

        # Calculate overall quality
        quality_scores = [v for v in quality_metrics.values() if v > 0]
        quality_metrics["overall_quality"] = (
            sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        )

        return quality_metrics

    def _assess_content_appropriateness(
        self, content: dict[str, Any], educational_context: dict[str, Any]
    ) -> float:
        """Assess if content is appropriate for grade level and subject"""
        appropriateness_factors = []

        grade_level = educational_context.get("grade_level", 5)

        # Check reading level
        if "text_content" in content:
            reading_level = self._estimate_reading_level(content["text_content"])
            expected_level = grade_level
            level_match = 1.0 - abs(reading_level - expected_level) / 12.0
            appropriateness_factors.append(max(0.0, level_match))

        # Check concept complexity
        if "concepts" in content:
            concept_complexity = self._estimate_concept_complexity(content["concepts"])
            expected_complexity = grade_level / 12.0
            complexity_match = 1.0 - abs(concept_complexity - expected_complexity)
            appropriateness_factors.append(max(0.0, complexity_match))

        return sum(appropriateness_factors) / len(appropriateness_factors) if appropriateness_factors else 0.5

    def _assess_objective_alignment(
        self, content: dict[str, Any], educational_context: dict[str, Any]
    ) -> float:
        """Assess alignment with learning objectives"""
        learning_objectives = educational_context.get("learning_objectives", [])
        if not learning_objectives:
            return 0.5  # Neutral score if no objectives specified

        alignment_score = 0.0
        content_text = str(content)  # Simple text representation

        for objective in learning_objectives:
            objective_words = objective.lower().split()
            content_words = content_text.lower().split()

            # Simple keyword overlap assessment
            overlap = len(set(objective_words) & set(content_words))
            objective_score = overlap / max(1, len(objective_words))
            alignment_score += objective_score

        return alignment_score / len(learning_objectives)

    def _assess_engagement_potential(self, content: dict[str, Any]) -> float:
        """Assess potential for student engagement"""
        engagement_factors = []

        # Interactive elements
        interactive_count = len(content.get("interactive_elements", []))
        engagement_factors.append(min(1.0, interactive_count / 3.0))

        # Multimedia content
        multimedia_count = len(content.get("multimedia_elements", []))
        engagement_factors.append(min(1.0, multimedia_count / 2.0))

        # Gamification elements
        gamification_score = content.get("gamification_score", 0.0)
        engagement_factors.append(gamification_score)

        # Variety in content types
        content_types = len(set(content.get("content_types", [])))
        engagement_factors.append(min(1.0, content_types / 4.0))

        return sum(engagement_factors) / len(engagement_factors) if engagement_factors else 0.3

    def _assess_accessibility(self, content: dict[str, Any]) -> float:
        """Assess accessibility features"""
        accessibility_features = content.get("accessibility_features", [])

        standard_features = [
            "alt_text", "captions", "transcripts", "high_contrast",
            "large_text", "audio_descriptions", "keyboard_navigation",
            "screen_reader_compatible"
        ]

        feature_score = len(accessibility_features) / len(standard_features)
        return min(1.0, feature_score)

    def _assess_curriculum_compliance(
        self, content: dict[str, Any], educational_context: dict[str, Any]
    ) -> float:
        """Assess compliance with curriculum standards"""
        curriculum_standards = educational_context.get("curriculum_standards", [])
        if not curriculum_standards:
            return 0.7  # Default score if no standards specified

        compliance_score = 0.0
        content_standards = content.get("curriculum_alignment", [])

        if content_standards:
            # Calculate overlap with required standards
            overlap = len(set(curriculum_standards) & set(content_standards))
            compliance_score = overlap / len(curriculum_standards)
        else:
            # Estimate compliance based on subject and grade level
            educational_context.get("subject_area", "")
            educational_context.get("grade_level", 5)

            # Simple heuristic based on content completeness
            completeness = len(content) / 10.0  # Assume 10 fields indicate complete content
            compliance_score = min(1.0, completeness)

        return compliance_score

    def _estimate_reading_level(self, text: str) -> float:
        """Estimate reading level of text (simplified)"""
        if not text:
            return 5.0

        # Simple heuristics based on sentence and word length
        sentences = text.split('. ')
        words = text.split()

        avg_sentence_length = len(words) / max(1, len(sentences))
        avg_word_length = sum(len(word) for word in words) / max(1, len(words))

        # Simplified Flesch-Kincaid grade level approximation
        reading_level = 0.39 * avg_sentence_length + 11.8 * (avg_word_length / 4.7) - 15.59

        return max(1.0, min(12.0, reading_level))

    def _estimate_concept_complexity(self, concepts: list[str]) -> float:
        """Estimate complexity of concepts (0-1 scale)"""
        if not concepts:
            return 0.5

        # Simple complexity estimation based on concept names
        complexity_keywords = {
            "basic": 0.2, "simple": 0.2, "introduction": 0.3,
            "intermediate": 0.5, "advanced": 0.8, "complex": 0.9,
            "analysis": 0.7, "synthesis": 0.8, "evaluation": 0.9
        }

        total_complexity = 0.0
        for concept in concepts:
            concept_lower = concept.lower()
            complexity = 0.5  # Default complexity

            for keyword, score in complexity_keywords.items():
                if keyword in concept_lower:
                    complexity = score
                    break

            total_complexity += complexity

        return total_complexity / len(concepts)


class PerformanceOptimizer:
    """Optimizes orchestration performance based on historical data"""

    def __init__(self):
        self.performance_history = []
        self.optimization_rules = []

    async def optimize_orchestration(
        self,
        educational_context: dict[str, Any],
        historical_performance: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate optimization recommendations"""

        optimizations = {
            "recommended_strategy": None,
            "agent_allocation": {},
            "timeout_adjustments": {},
            "quality_improvements": [],
            "performance_predictions": {}
        }

        if not historical_performance:
            return optimizations

        # Analyze strategy performance
        strategy_performance = self._analyze_strategy_performance(historical_performance)
        optimizations["recommended_strategy"] = max(
            strategy_performance, key=strategy_performance.get
        )

        # Optimize agent allocation
        optimizations["agent_allocation"] = self._optimize_agent_allocation(
            educational_context, historical_performance
        )

        # Adjust timeouts based on complexity
        optimizations["timeout_adjustments"] = self._optimize_timeouts(
            educational_context, historical_performance
        )

        # Quality improvement suggestions
        optimizations["quality_improvements"] = self._suggest_quality_improvements(
            educational_context, historical_performance
        )

        return optimizations

    def _analyze_strategy_performance(self, historical_performance: list[dict[str, Any]]) -> dict[str, float]:
        """Analyze performance of different strategies"""
        strategy_scores = {}

        for perf in historical_performance:
            strategy = perf.get("strategy", "unknown")
            quality = perf.get("quality_score", 0.0)
            execution_time = perf.get("execution_time", 0.0)

            # Combined score: quality weighted more than speed
            score = 0.7 * quality + 0.3 * (1.0 / max(1.0, execution_time / 60.0))

            if strategy not in strategy_scores:
                strategy_scores[strategy] = []
            strategy_scores[strategy].append(score)

        # Average scores per strategy
        return {
            strategy: sum(scores) / len(scores)
            for strategy, scores in strategy_scores.items()
        }

    def _optimize_agent_allocation(
        self,
        educational_context: dict[str, Any],
        historical_performance: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Optimize agent allocation based on content requirements"""

        subject = educational_context.get("subject_area", "general")
        grade_level = educational_context.get("grade_level", 5)
        content_type = educational_context.get("content_type", "lesson")

        # Base allocation
        allocation = {
            "content_generation": 2,
            "quiz_creation": 1,
            "terrain_generation": 1,
            "content_review": 1
        }

        # Adjust based on subject
        if subject.lower() in ["math", "science", "physics", "chemistry"]:
            allocation["content_generation"] += 1  # More complex content needs

        # Adjust based on grade level
        if grade_level >= 9:  # High school
            allocation["content_review"] += 1  # More rigorous review needed

        # Adjust based on content type
        if content_type == "project":
            allocation["content_generation"] += 2
            allocation["terrain_generation"] += 1
        elif content_type == "assessment":
            allocation["quiz_creation"] += 1
            allocation["content_review"] += 1

        return allocation

    def _optimize_timeouts(
        self,
        educational_context: dict[str, Any],
        historical_performance: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Optimize timeouts based on content complexity"""

        complexity_score = self._calculate_content_complexity_score(educational_context)

        base_timeout = 300.0  # 5 minutes
        complexity_multiplier = 1.0 + complexity_score

        return {
            "content_generation": base_timeout * complexity_multiplier,
            "quiz_creation": base_timeout * 0.7,  # Typically faster
            "terrain_generation": base_timeout * 1.2,  # Typically slower
            "content_review": base_timeout * 0.5  # Quick review
        }

    def _suggest_quality_improvements(
        self,
        educational_context: dict[str, Any],
        historical_performance: list[dict[str, Any]]
    ) -> list[str]:
        """Suggest quality improvements based on patterns"""

        suggestions = []

        # Analyze quality patterns
        recent_quality = [
            perf.get("quality_score", 0.0)
            for perf in historical_performance[-10:]
        ]

        if recent_quality:
            avg_quality = sum(recent_quality) / len(recent_quality)

            if avg_quality < 0.7:
                suggestions.append("Consider using collaborative strategy for better quality")
                suggestions.append("Increase review agent allocation")
                suggestions.append("Add specialized agents for subject area")

            if avg_quality < 0.6:
                suggestions.append("Enable swarm intelligence for consensus-based quality")
                suggestions.append("Implement additional validation steps")

        # Subject-specific suggestions
        subject = educational_context.get("subject_area", "").lower()
        if subject in ["math", "science", "physics"]:
            suggestions.append("Ensure mathematical accuracy validation")
            suggestions.append("Include step-by-step solution verification")

        return suggestions

    def _calculate_content_complexity_score(self, educational_context: dict[str, Any]) -> float:
        """Calculate complexity score for content"""
        complexity_factors = []

        # Grade level complexity
        grade_level = educational_context.get("grade_level", 5)
        complexity_factors.append(grade_level / 12.0)

        # Subject complexity
        subject_scores = {
            "math": 0.8, "science": 0.9, "physics": 0.95,
            "english": 0.6, "history": 0.7, "art": 0.4
        }
        subject = educational_context.get("subject_area", "").lower()
        complexity_factors.append(subject_scores.get(subject, 0.5))

        # Learning objectives count
        objectives_count = len(educational_context.get("learning_objectives", []))
        complexity_factors.append(min(1.0, objectives_count / 5.0))

        return sum(complexity_factors) / len(complexity_factors)