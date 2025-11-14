"""
Enhanced Swarm Intelligence Coordinator
======================================

Advanced coordination system for multi-agent educational content generation
with intelligent task distribution, consensus mechanisms, and performance optimization.

Features:
- Dynamic agent specialization and allocation
- Real-time consensus and quality assessment
- Educational context-aware task distribution
- Performance-based agent selection
- Fault tolerance and recovery mechanisms
- Adaptive load balancing
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

import numpy as np

from .swarm_controller import SwarmController
from .task_distributor import TaskPriority
from .worker_pool import WorkerAgent

logger = logging.getLogger(__name__)


class CoordinationStrategy(Enum):
    """Coordination strategies for swarm intelligence"""

    HIERARCHICAL = "hierarchical"  # Leader-follower structure
    DEMOCRATIC = "democratic"  # Equal voting and consensus
    COMPETITIVE = "competitive"  # Agents compete for tasks
    COLLABORATIVE = "collaborative"  # Agents work together
    ADAPTIVE = "adaptive"  # Strategy adapts to context
    SPECIALIST = "specialist"  # Task-specific specialization


class EducationalComplexity(Enum):
    """Educational complexity levels"""

    ELEMENTARY = "elementary"  # K-5
    MIDDLE = "middle"  # 6-8
    HIGH = "high"  # 9-12
    ADVANCED = "advanced"  # Post-secondary


@dataclass
class EducationalTask:
    """Enhanced task with educational context"""

    task_id: str = field(default_factory=lambda: str(uuid4()))
    task_type: str = ""
    priority: TaskPriority = TaskPriority.NORMAL

    # Educational context
    subject_area: str = "general"
    grade_level: int = 5
    learning_objectives: list[str] = field(default_factory=list)
    content_type: str = "lesson"
    difficulty_level: str = "medium"

    # Task parameters
    parameters: dict[str, Any] = field(default_factory=dict)
    requirements: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)

    # Execution context
    timeout: float = 300.0
    retry_attempts: int = 3
    dependencies: list[str] = field(default_factory=list)

    # Quality requirements
    quality_threshold: float = 0.8
    educational_standards: list[str] = field(default_factory=list)
    accessibility_requirements: list[str] = field(default_factory=list)

    # Timing and deadlines
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    estimated_duration: float = 60.0  # seconds

    @property
    def complexity_level(self) -> EducationalComplexity:
        """Determine complexity level based on grade"""
        if self.grade_level <= 5:
            return EducationalComplexity.ELEMENTARY
        elif self.grade_level <= 8:
            return EducationalComplexity.MIDDLE
        elif self.grade_level <= 12:
            return EducationalComplexity.HIGH
        else:
            return EducationalComplexity.ADVANCED

    @property
    def urgency_score(self) -> float:
        """Calculate urgency score (0-1)"""
        if not self.deadline:
            return 0.5

        time_remaining = (self.deadline - datetime.now()).total_seconds()
        if time_remaining <= 0:
            return 1.0

        # Normalize to 24 hours
        urgency = max(0.0, 1.0 - (time_remaining / 86400))
        return min(1.0, urgency)


@dataclass
class AgentCapability:
    """Enhanced agent capability definition"""

    capability_id: str
    name: str
    description: str

    # Specialization areas
    subject_specializations: list[str] = field(default_factory=list)
    grade_level_range: tuple[int, int] = (1, 12)
    content_types: list[str] = field(default_factory=list)

    # Performance metrics
    quality_score: float = 0.8
    speed_score: float = 0.8
    reliability_score: float = 0.8
    educational_expertise: float = 0.8

    # Task preferences
    preferred_complexity: EducationalComplexity = EducationalComplexity.MIDDLE
    max_concurrent_tasks: int = 3
    average_task_time: float = 120.0  # seconds


@dataclass
class SwarmCoordinationResult:
    """Result of swarm coordination"""

    coordination_id: str
    success: bool

    # Task execution results
    completed_tasks: list[dict[str, Any]]
    failed_tasks: list[dict[str, Any]]

    # Performance metrics
    total_execution_time: float
    average_quality_score: float
    agent_utilization: dict[str, float]

    # Educational metrics
    learning_objectives_coverage: float
    curriculum_alignment_score: float
    content_quality_assessment: dict[str, float]

    # Coordination metrics
    consensus_scores: list[float]
    coordination_efficiency: float
    resource_utilization: float

    # Insights and recommendations
    performance_insights: list[str] = field(default_factory=list)
    optimization_suggestions: list[str] = field(default_factory=list)
    quality_improvements: list[str] = field(default_factory=list)


class EnhancedSwarmCoordinator:
    """
    Enhanced Swarm Intelligence Coordinator for Educational Content Generation

    Provides sophisticated coordination of multiple AI agents with focus on
    educational quality, performance optimization, and adaptive strategies.
    """

    def __init__(
        self,
        swarm_controller: SwarmController,
        coordination_strategy: CoordinationStrategy = CoordinationStrategy.ADAPTIVE,
    ):
        """Initialize enhanced coordinator"""
        self.swarm_controller = swarm_controller
        self.coordination_strategy = coordination_strategy
        self.coordination_id = str(uuid4())

        # Enhanced components
        self.educational_task_analyzer = EducationalTaskAnalyzer()
        self.agent_performance_tracker = AgentPerformanceTracker()
        self.quality_assessor = SwarmQualityAssessor()
        self.coordination_optimizer = CoordinationOptimizer()

        # Coordination state
        self.active_coordinations: dict[str, dict[str, Any]] = {}
        self.coordination_history: list[SwarmCoordinationResult] = []

        # Agent management
        self.agent_capabilities: dict[str, AgentCapability] = {}
        self.agent_assignments: dict[str, list[str]] = {}  # agent_id -> task_ids
        self.agent_performance: dict[str, dict[str, float]] = {}

        # Educational context tracking
        self.subject_specialists: dict[str, list[str]] = {}  # subject -> agent_ids
        self.grade_level_experts: dict[int, list[str]] = {}  # grade -> agent_ids
        self.content_type_specialists: dict[str, list[str]] = {}  # type -> agent_ids

        # Performance optimization
        self.task_execution_history: deque = deque(maxlen=1000)
        self.coordination_metrics: dict[str, float] = {}

        # Real-time monitoring
        self.monitoring_tasks: set[asyncio.Task] = set()
        self.monitoring_enabled = True

        logger.info(
            f"Enhanced Swarm Coordinator initialized with strategy: {coordination_strategy}"
        )

    async def initialize(self):
        """Initialize the enhanced coordinator"""
        try:
            # Initialize component systems
            await self.educational_task_analyzer.initialize()
            await self.agent_performance_tracker.initialize()
            await self.quality_assessor.initialize()

            # Analyze existing agent capabilities
            await self._analyze_agent_capabilities()

            # Build specialization mappings
            await self._build_specialization_mappings()

            # Start performance monitoring
            await self._start_performance_monitoring()

            logger.info("Enhanced Swarm Coordinator fully initialized")

        except Exception as e:
            logger.error(f"Failed to initialize enhanced coordinator: {e}")
            raise

    async def coordinate_educational_content_generation(
        self,
        educational_tasks: list[EducationalTask],
        coordination_config: Optional[dict[str, Any]] = None,
    ) -> SwarmCoordinationResult:
        """
        Coordinate swarm for educational content generation

        Args:
            educational_tasks: List of educational tasks to execute
            coordination_config: Optional coordination configuration

        Returns:
            SwarmCoordinationResult with comprehensive execution results
        """
        coordination_id = str(uuid4())
        start_time = time.time()

        try:
            # Analyze and optimize task distribution
            optimized_tasks = await self.educational_task_analyzer.analyze_and_optimize_tasks(
                educational_tasks
            )

            # Determine optimal coordination strategy
            effective_strategy = await self._determine_coordination_strategy(
                optimized_tasks, coordination_config
            )

            # Track active coordination
            self.active_coordinations[coordination_id] = {
                "start_time": start_time,
                "strategy": effective_strategy,
                "tasks": optimized_tasks,
                "progress": 0.0,
                "agents_allocated": [],
            }

            logger.info(
                f"Starting swarm coordination {coordination_id} with {len(optimized_tasks)} tasks "
                f"using {effective_strategy.value} strategy"
            )

            # Execute coordination strategy
            execution_result = await self._execute_coordination_strategy(
                coordination_id,
                effective_strategy,
                optimized_tasks,
                coordination_config or {},
            )

            # Calculate comprehensive metrics
            execution_time = time.time() - start_time
            coordination_metrics = await self._calculate_coordination_metrics(
                execution_result, execution_time
            )

            # Assess educational quality
            educational_assessment = await self.quality_assessor.assess_educational_outcomes(
                execution_result["completed_tasks"], educational_tasks
            )

            # Generate insights and recommendations
            insights = await self._generate_coordination_insights(
                execution_result, coordination_metrics, educational_assessment
            )

            # Create comprehensive result
            coordination_result = SwarmCoordinationResult(
                coordination_id=coordination_id,
                success=len(execution_result["failed_tasks"]) == 0,
                completed_tasks=execution_result["completed_tasks"],
                failed_tasks=execution_result["failed_tasks"],
                total_execution_time=execution_time,
                average_quality_score=coordination_metrics["average_quality"],
                agent_utilization=coordination_metrics["agent_utilization"],
                learning_objectives_coverage=educational_assessment["objectives_coverage"],
                curriculum_alignment_score=educational_assessment["curriculum_alignment"],
                content_quality_assessment=educational_assessment["quality_metrics"],
                consensus_scores=coordination_metrics["consensus_scores"],
                coordination_efficiency=coordination_metrics["efficiency"],
                resource_utilization=coordination_metrics["resource_utilization"],
                performance_insights=insights["performance"],
                optimization_suggestions=insights["optimization"],
                quality_improvements=insights["quality"],
            )

            # Store result and clean up
            self.coordination_history.append(coordination_result)
            del self.active_coordinations[coordination_id]

            # Update agent performance tracking
            await self.agent_performance_tracker.update_performance_metrics(
                execution_result, coordination_metrics
            )

            logger.info(
                f"Swarm coordination {coordination_id} completed: "
                f"success={coordination_result.success}, "
                f"time={execution_time:.2f}s, "
                f"quality={coordination_result.average_quality_score:.2f}"
            )

            return coordination_result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Swarm coordination failed: {str(e)}"
            logger.error(f"{error_msg} (ID: {coordination_id})")

            # Clean up on failure
            self.active_coordinations.pop(coordination_id, None)

            # Return failure result
            return SwarmCoordinationResult(
                coordination_id=coordination_id,
                success=False,
                completed_tasks=[],
                failed_tasks=[{"error": error_msg, "tasks": educational_tasks}],
                total_execution_time=execution_time,
                average_quality_score=0.0,
                agent_utilization={},
                learning_objectives_coverage=0.0,
                curriculum_alignment_score=0.0,
                content_quality_assessment={},
                consensus_scores=[],
                coordination_efficiency=0.0,
                resource_utilization=0.0,
                performance_insights=[error_msg],
                optimization_suggestions=["Review task requirements and agent availability"],
                quality_improvements=["Implement better error handling and recovery"],
            )

    async def _execute_coordination_strategy(
        self,
        coordination_id: str,
        strategy: CoordinationStrategy,
        tasks: list[EducationalTask],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute specific coordination strategy"""

        if strategy == CoordinationStrategy.HIERARCHICAL:
            return await self._execute_hierarchical_coordination(coordination_id, tasks, config)
        elif strategy == CoordinationStrategy.DEMOCRATIC:
            return await self._execute_democratic_coordination(coordination_id, tasks, config)
        elif strategy == CoordinationStrategy.COMPETITIVE:
            return await self._execute_competitive_coordination(coordination_id, tasks, config)
        elif strategy == CoordinationStrategy.COLLABORATIVE:
            return await self._execute_collaborative_coordination(coordination_id, tasks, config)
        elif strategy == CoordinationStrategy.SPECIALIST:
            return await self._execute_specialist_coordination(coordination_id, tasks, config)
        elif strategy == CoordinationStrategy.ADAPTIVE:
            return await self._execute_adaptive_coordination(coordination_id, tasks, config)
        else:
            raise ValueError(f"Unknown coordination strategy: {strategy}")

    async def _execute_specialist_coordination(
        self, coordination_id: str, tasks: list[EducationalTask], config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute specialist coordination where agents are matched to their expertise"""

        completed_tasks = []
        failed_tasks = []

        # Group tasks by specialization requirements
        task_groups = await self._group_tasks_by_specialization(tasks)

        # Execute each group with specialized agents
        for specialization, task_group in task_groups.items():
            logger.info(f"Executing {len(task_group)} tasks for specialization: {specialization}")

            # Get specialized agents for this group
            specialist_agents = await self._get_specialist_agents(specialization, len(task_group))

            if not specialist_agents:
                logger.warning(f"No specialist agents available for {specialization}")
                failed_tasks.extend(
                    [
                        {"task": task, "error": "No specialist agents available"}
                        for task in task_group
                    ]
                )
                continue

            # Execute tasks with specialists
            try:
                group_results = await self._execute_tasks_with_specialists(
                    task_group, specialist_agents, coordination_id
                )

                completed_tasks.extend(group_results["completed"])
                failed_tasks.extend(group_results["failed"])

            except Exception as e:
                logger.error(f"Specialist execution failed for {specialization}: {e}")
                failed_tasks.extend([{"task": task, "error": str(e)} for task in task_group])

        return {
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "strategy": "specialist",
            "coordination_id": coordination_id,
        }

    async def _execute_collaborative_coordination(
        self, coordination_id: str, tasks: list[EducationalTask], config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute collaborative coordination where agents work together"""

        completed_tasks = []
        failed_tasks = []

        # Create collaborative groups for complex tasks
        collaboration_groups = await self._create_collaboration_groups(tasks)

        for group_id, group_info in collaboration_groups.items():
            group_tasks = group_info["tasks"]
            required_capabilities = group_info["capabilities"]

            logger.info(f"Executing collaborative group {group_id} with {len(group_tasks)} tasks")

            # Assemble collaborative team
            team_agents = await self._assemble_collaborative_team(
                required_capabilities, len(group_tasks)
            )

            if len(team_agents) < 2:
                logger.warning(f"Insufficient agents for collaboration in group {group_id}")
                failed_tasks.extend(
                    [
                        {"task": task, "error": "Insufficient collaborative agents"}
                        for task in group_tasks
                    ]
                )
                continue

            # Execute collaborative workflow
            try:
                collaboration_result = await self._execute_collaborative_workflow(
                    group_tasks, team_agents, coordination_id
                )

                completed_tasks.extend(collaboration_result["completed"])
                failed_tasks.extend(collaboration_result["failed"])

            except Exception as e:
                logger.error(f"Collaborative execution failed for group {group_id}: {e}")
                failed_tasks.extend([{"task": task, "error": str(e)} for task in group_tasks])

        return {
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "strategy": "collaborative",
            "coordination_id": coordination_id,
        }

    async def _execute_adaptive_coordination(
        self, coordination_id: str, tasks: list[EducationalTask], config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute adaptive coordination that changes strategy based on performance"""

        completed_tasks = []
        failed_tasks = []

        # Start with an initial strategy based on task analysis
        current_strategy = await self._analyze_optimal_initial_strategy(tasks)

        # Execute tasks in batches, adapting strategy as needed
        task_batches = await self._create_adaptive_batches(tasks)

        for batch_idx, batch in enumerate(task_batches):
            logger.info(
                f"Executing adaptive batch {batch_idx + 1}/{len(task_batches)} with strategy: {current_strategy.value}"
            )

            # Execute current batch with current strategy
            batch_result = await self._execute_coordination_strategy(
                f"{coordination_id}_batch_{batch_idx}", current_strategy, batch, config
            )

            # Assess batch performance
            batch_performance = await self._assess_batch_performance(batch_result, batch)

            # Adapt strategy if performance is below threshold
            if batch_performance["quality_score"] < config.get("adaptation_threshold", 0.7):
                new_strategy = await self._select_adaptive_strategy(
                    current_strategy, batch_performance, tasks[batch_idx * len(batch) :]
                )

                if new_strategy != current_strategy:
                    logger.info(
                        f"Adapting strategy from {current_strategy.value} to {new_strategy.value}"
                    )
                    current_strategy = new_strategy

            # Collect results
            completed_tasks.extend(batch_result["completed_tasks"])
            failed_tasks.extend(batch_result["failed_tasks"])

        return {
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "strategy": "adaptive",
            "coordination_id": coordination_id,
            "final_strategy": current_strategy.value,
        }

    async def _determine_coordination_strategy(
        self, tasks: list[EducationalTask], config: Optional[dict[str, Any]]
    ) -> CoordinationStrategy:
        """Determine optimal coordination strategy based on tasks and context"""

        if self.coordination_strategy != CoordinationStrategy.ADAPTIVE:
            return self.coordination_strategy

        # Analyze task characteristics
        task_analysis = await self._analyze_task_characteristics(tasks)

        # Consider resource availability
        resource_status = await self._assess_resource_availability()

        # Strategy selection logic
        if (
            task_analysis["specialization_diversity"] > 0.8
            and resource_status["specialist_availability"] > 0.7
        ):
            return CoordinationStrategy.SPECIALIST
        elif (
            task_analysis["complexity_score"] > 0.7
            and resource_status["collaboration_capacity"] > 0.6
        ):
            return CoordinationStrategy.COLLABORATIVE
        elif task_analysis["urgency_score"] > 0.8:
            return CoordinationStrategy.COMPETITIVE
        elif task_analysis["consensus_requirements"] > 0.6:
            return CoordinationStrategy.DEMOCRATIC
        elif task_analysis["hierarchy_benefits"] > 0.7:
            return CoordinationStrategy.HIERARCHICAL
        else:
            return CoordinationStrategy.ADAPTIVE

    async def _analyze_task_characteristics(self, tasks: list[EducationalTask]) -> dict[str, float]:
        """Analyze characteristics of task set"""

        if not tasks:
            return {}

        # Calculate various metrics
        specializations = set()
        complexities = []
        urgencies = []
        subjects = set()
        grade_levels = set()

        for task in tasks:
            # Collect specialization requirements
            if task.subject_area:
                specializations.add(task.subject_area)
                subjects.add(task.subject_area)

            # Collect complexity indicators
            complexity = self._estimate_task_complexity(task)
            complexities.append(complexity)

            # Collect urgency scores
            urgencies.append(task.urgency_score)

            # Collect grade levels
            grade_levels.add(task.grade_level)

        return {
            "specialization_diversity": len(specializations) / max(1, len(tasks)),
            "complexity_score": sum(complexities) / len(complexities) if complexities else 0.5,
            "urgency_score": sum(urgencies) / len(urgencies) if urgencies else 0.5,
            "subject_diversity": len(subjects) / max(1, len(tasks)),
            "grade_level_spread": len(grade_levels) / max(1, len(tasks)),
            "consensus_requirements": self._estimate_consensus_requirements(tasks),
            "hierarchy_benefits": self._estimate_hierarchy_benefits(tasks),
        }

    def _estimate_task_complexity(self, task: EducationalTask) -> float:
        """Estimate complexity of a single task"""
        complexity_factors = []

        # Grade level complexity
        complexity_factors.append(task.grade_level / 12.0)

        # Subject complexity
        subject_complexity = {
            "math": 0.8,
            "science": 0.9,
            "physics": 0.95,
            "english": 0.6,
            "history": 0.7,
            "art": 0.4,
        }
        complexity_factors.append(subject_complexity.get(task.subject_area.lower(), 0.5))

        # Learning objectives count
        complexity_factors.append(min(1.0, len(task.learning_objectives) / 5.0))

        # Content type complexity
        content_complexity = {
            "lesson": 0.6,
            "quiz": 0.4,
            "project": 0.9,
            "simulation": 0.95,
            "assessment": 0.7,
        }
        complexity_factors.append(content_complexity.get(task.content_type, 0.5))

        return sum(complexity_factors) / len(complexity_factors)

    def _estimate_consensus_requirements(self, tasks: list[EducationalTask]) -> float:
        """Estimate how much consensus is needed for task set"""
        consensus_indicators = 0.0

        # High-stakes content requires more consensus
        for task in tasks:
            if task.content_type in ["assessment", "project"]:
                consensus_indicators += 0.3
            if task.quality_threshold > 0.85:
                consensus_indicators += 0.2
            if len(task.educational_standards) > 3:
                consensus_indicators += 0.2

        return min(1.0, consensus_indicators / len(tasks))

    def _estimate_hierarchy_benefits(self, tasks: list[EducationalTask]) -> float:
        """Estimate benefits of hierarchical coordination"""
        hierarchy_indicators = 0.0

        # Sequential dependencies favor hierarchy
        total_dependencies = sum(len(task.dependencies) for task in tasks)
        hierarchy_indicators += min(0.5, total_dependencies / len(tasks))

        # Varying complexity levels favor hierarchy
        complexities = [self._estimate_task_complexity(task) for task in tasks]
        complexity_variance = np.var(complexities) if complexities else 0
        hierarchy_indicators += min(0.5, complexity_variance * 2)

        return hierarchy_indicators

    async def _analyze_agent_capabilities(self):
        """Analyze capabilities of available agents"""
        try:
            # Get worker pool from swarm controller
            worker_pool = self.swarm_controller.worker_pool
            workers = worker_pool.get_available_workers()

            for worker in workers:
                # Extract capabilities from worker
                capabilities = await self._extract_worker_capabilities(worker)
                self.agent_capabilities[worker.worker_id] = capabilities

                # Initialize performance tracking
                self.agent_performance[worker.worker_id] = {
                    "tasks_completed": 0,
                    "average_quality": 0.8,
                    "average_time": 120.0,
                    "success_rate": 1.0,
                    "specialization_scores": {},
                }

            logger.info(f"Analyzed capabilities for {len(workers)} agents")

        except Exception as e:
            logger.error(f"Failed to analyze agent capabilities: {e}")

    async def _extract_worker_capabilities(self, worker: WorkerAgent) -> AgentCapability:
        """Extract capabilities from worker agent"""
        # This would integrate with actual worker capability detection
        # For now, create a default capability profile

        return AgentCapability(
            capability_id=f"cap_{worker.worker_id}",
            name=f"Agent {worker.worker_id} Capabilities",
            description=f"Educational content generation capabilities for {worker.worker_id}",
            subject_specializations=getattr(worker, "specializations", ["general"]),
            grade_level_range=(1, 12),
            content_types=["lesson", "quiz", "activity"],
            quality_score=0.8,
            speed_score=0.8,
            reliability_score=0.9,
            educational_expertise=0.7,
        )

    async def _build_specialization_mappings(self):
        """Build mappings of agents to specializations"""
        for agent_id, capability in self.agent_capabilities.items():
            # Map by subject specializations
            for subject in capability.subject_specializations:
                if subject not in self.subject_specialists:
                    self.subject_specialists[subject] = []
                self.subject_specialists[subject].append(agent_id)

            # Map by grade level range
            start_grade, end_grade = capability.grade_level_range
            for grade in range(start_grade, end_grade + 1):
                if grade not in self.grade_level_experts:
                    self.grade_level_experts[grade] = []
                self.grade_level_experts[grade].append(agent_id)

            # Map by content types
            for content_type in capability.content_types:
                if content_type not in self.content_type_specialists:
                    self.content_type_specialists[content_type] = []
                self.content_type_specialists[content_type].append(agent_id)

    async def _start_performance_monitoring(self):
        """Start real-time performance monitoring"""
        if not self.monitoring_enabled:
            return

        # Start coordination monitoring
        monitor_task = asyncio.create_task(self._monitor_coordination_performance())
        self.monitoring_tasks.add(monitor_task)
        monitor_task.add_done_callback(self.monitoring_tasks.discard)

        # Start agent monitoring
        agent_monitor_task = asyncio.create_task(self._monitor_agent_performance())
        self.monitoring_tasks.add(agent_monitor_task)
        agent_monitor_task.add_done_callback(self.monitoring_tasks.discard)

        logger.info("Performance monitoring started for enhanced swarm coordinator")

    async def _monitor_coordination_performance(self):
        """Monitor overall coordination performance"""
        while self.monitoring_enabled:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds

                # Calculate current performance metrics
                current_metrics = await self._calculate_current_performance_metrics()

                # Store metrics for analysis
                self.coordination_metrics.update(current_metrics)

                # Log performance alerts
                if current_metrics.get("average_quality", 1.0) < 0.7:
                    logger.warning(
                        f"Low coordination quality detected: {current_metrics['average_quality']:.2f}"
                    )

                if current_metrics.get("efficiency", 1.0) < 0.6:
                    logger.warning(
                        f"Low coordination efficiency detected: {current_metrics['efficiency']:.2f}"
                    )

            except Exception as e:
                logger.error(f"Coordination monitoring error: {e}")
                await asyncio.sleep(60)

    async def _monitor_agent_performance(self):
        """Monitor individual agent performance"""
        while self.monitoring_enabled:
            try:
                await asyncio.sleep(45)  # Monitor every 45 seconds

                # Update agent performance metrics
                for agent_id in self.agent_capabilities:
                    agent_metrics = await self._calculate_agent_performance_metrics(agent_id)
                    self.agent_performance[agent_id].update(agent_metrics)

                # Identify underperforming agents
                underperformers = [
                    agent_id
                    for agent_id, metrics in self.agent_performance.items()
                    if metrics.get("success_rate", 1.0) < 0.7
                ]

                if underperformers:
                    logger.warning(f"Underperforming agents detected: {underperformers}")

            except Exception as e:
                logger.error(f"Agent monitoring error: {e}")
                await asyncio.sleep(60)

    async def get_coordination_status(self) -> dict[str, Any]:
        """Get comprehensive coordination status"""
        return {
            "coordinator_id": self.coordination_id,
            "strategy": self.coordination_strategy.value,
            "active_coordinations": len(self.active_coordinations),
            "total_coordinations": len(self.coordination_history),
            "agent_capabilities": len(self.agent_capabilities),
            "specialization_mappings": {
                "subjects": len(self.subject_specialists),
                "grade_levels": len(self.grade_level_experts),
                "content_types": len(self.content_type_specialists),
            },
            "performance_metrics": self.coordination_metrics,
            "monitoring_active": self.monitoring_enabled,
            "swarm_status": (
                await self.swarm_controller.get_status() if self.swarm_controller else None
            ),
        }

    async def shutdown(self):
        """Gracefully shutdown the enhanced coordinator"""
        logger.info("Shutting down Enhanced Swarm Coordinator")

        # Stop monitoring
        self.monitoring_enabled = False
        for task in self.monitoring_tasks:
            task.cancel()

        # Wait for active coordinations
        if self.active_coordinations:
            logger.info(f"Waiting for {len(self.active_coordinations)} active coordinations")
            while self.active_coordinations:
                await asyncio.sleep(1)

        # Shutdown components
        if hasattr(self.educational_task_analyzer, "shutdown"):
            await self.educational_task_analyzer.shutdown()

        if hasattr(self.agent_performance_tracker, "shutdown"):
            await self.agent_performance_tracker.shutdown()

        logger.info("Enhanced Swarm Coordinator shutdown complete")


# Supporting classes for enhanced coordination


class EducationalTaskAnalyzer:
    """Analyzes and optimizes educational tasks for swarm execution"""

    async def initialize(self):
        """Initialize the task analyzer"""
        pass

    async def analyze_and_optimize_tasks(
        self, tasks: list[EducationalTask]
    ) -> list[EducationalTask]:
        """Analyze and optimize task list for better execution"""
        optimized_tasks = []

        for task in tasks:
            # Optimize task parameters
            optimized_task = await self._optimize_single_task(task)
            optimized_tasks.append(optimized_task)

        # Optimize task ordering
        optimized_tasks = await self._optimize_task_order(optimized_tasks)

        return optimized_tasks

    async def _optimize_single_task(self, task: EducationalTask) -> EducationalTask:
        """Optimize individual task parameters"""
        # Adjust timeout based on complexity
        complexity = self._calculate_task_complexity(task)
        base_timeout = 300.0
        task.timeout = base_timeout * (1.0 + complexity)

        # Adjust quality threshold based on content type
        if task.content_type in ["assessment", "project"]:
            task.quality_threshold = max(0.85, task.quality_threshold)

        return task

    def _calculate_task_complexity(self, task: EducationalTask) -> float:
        """Calculate task complexity score"""
        complexity_factors = []

        # Grade level factor
        complexity_factors.append(task.grade_level / 12.0)

        # Subject factor
        subject_complexity = {
            "math": 0.8,
            "science": 0.9,
            "physics": 0.95,
            "english": 0.6,
            "history": 0.7,
            "art": 0.4,
        }
        complexity_factors.append(subject_complexity.get(task.subject_area.lower(), 0.5))

        # Learning objectives factor
        complexity_factors.append(min(1.0, len(task.learning_objectives) / 5.0))

        return sum(complexity_factors) / len(complexity_factors)

    async def _optimize_task_order(self, tasks: list[EducationalTask]) -> list[EducationalTask]:
        """Optimize task execution order"""

        # Sort by priority, then by dependencies, then by urgency
        def sort_key(task):
            return (
                -task.priority.value,  # Higher priority first
                len(task.dependencies),  # Fewer dependencies first
                -task.urgency_score,  # Higher urgency first
            )

        return sorted(tasks, key=sort_key)


class AgentPerformanceTracker:
    """Tracks and analyzes agent performance over time"""

    def __init__(self):
        self.performance_history = defaultdict(list)
        self.performance_trends = defaultdict(dict)

    async def initialize(self):
        """Initialize performance tracker"""
        pass

    async def update_performance_metrics(
        self, execution_result: dict[str, Any], coordination_metrics: dict[str, Any]
    ):
        """Update performance metrics based on execution results"""
        # Extract agent performance from execution results
        for completed_task in execution_result.get("completed_tasks", []):
            agent_id = completed_task.get("agent_id")
            if agent_id:
                performance_data = {
                    "timestamp": datetime.now(),
                    "quality_score": completed_task.get("quality_score", 0.8),
                    "execution_time": completed_task.get("execution_time", 120.0),
                    "success": True,
                }
                self.performance_history[agent_id].append(performance_data)

        # Track failed tasks
        for failed_task in execution_result.get("failed_tasks", []):
            agent_id = failed_task.get("agent_id")
            if agent_id:
                performance_data = {
                    "timestamp": datetime.now(),
                    "quality_score": 0.0,
                    "execution_time": failed_task.get("execution_time", 0.0),
                    "success": False,
                    "error": failed_task.get("error", "Unknown error"),
                }
                self.performance_history[agent_id].append(performance_data)

        # Update performance trends
        await self._update_performance_trends()

    async def _update_performance_trends(self):
        """Calculate performance trends for all agents"""
        for agent_id, history in self.performance_history.items():
            if len(history) >= 5:  # Minimum data points for trend analysis
                recent_history = history[-20:]  # Last 20 executions

                # Calculate trends
                quality_scores = [h["quality_score"] for h in recent_history]
                execution_times = [h["execution_time"] for h in recent_history]
                success_rate = sum(1 for h in recent_history if h["success"]) / len(recent_history)

                self.performance_trends[agent_id] = {
                    "average_quality": sum(quality_scores) / len(quality_scores),
                    "average_execution_time": sum(execution_times) / len(execution_times),
                    "success_rate": success_rate,
                    "trend_direction": self._calculate_trend_direction(quality_scores),
                    "consistency_score": self._calculate_consistency(quality_scores),
                }

    def _calculate_trend_direction(self, scores: list[float]) -> str:
        """Calculate if performance is improving, declining, or stable"""
        if len(scores) < 5:
            return "insufficient_data"

        first_half = scores[: len(scores) // 2]
        second_half = scores[len(scores) // 2 :]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        diff = second_avg - first_avg

        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"

    def _calculate_consistency(self, scores: list[float]) -> float:
        """Calculate consistency score (lower variance = higher consistency)"""
        if len(scores) < 2:
            return 1.0

        variance = np.var(scores)
        # Convert variance to consistency score (0-1, higher is better)
        consistency = max(0.0, 1.0 - variance * 4)  # Scale variance appropriately
        return consistency


class SwarmQualityAssessor:
    """Assesses educational quality of swarm-generated content"""

    async def initialize(self):
        """Initialize quality assessor"""
        pass

    async def assess_educational_outcomes(
        self,
        completed_tasks: list[dict[str, Any]],
        original_tasks: list[EducationalTask],
    ) -> dict[str, Any]:
        """Assess educational quality of completed tasks"""

        assessment = {
            "objectives_coverage": 0.0,
            "curriculum_alignment": 0.0,
            "quality_metrics": {},
            "educational_effectiveness": 0.0,
            "accessibility_compliance": 0.0,
        }

        if not completed_tasks:
            return assessment

        # Calculate learning objectives coverage
        assessment["objectives_coverage"] = await self._calculate_objectives_coverage(
            completed_tasks, original_tasks
        )

        # Calculate curriculum alignment
        assessment["curriculum_alignment"] = await self._calculate_curriculum_alignment(
            completed_tasks, original_tasks
        )

        # Calculate detailed quality metrics
        assessment["quality_metrics"] = await self._calculate_detailed_quality_metrics(
            completed_tasks
        )

        # Calculate educational effectiveness
        assessment["educational_effectiveness"] = await self._calculate_educational_effectiveness(
            completed_tasks, original_tasks
        )

        # Calculate accessibility compliance
        assessment["accessibility_compliance"] = await self._calculate_accessibility_compliance(
            completed_tasks
        )

        return assessment

    async def _calculate_objectives_coverage(
        self,
        completed_tasks: list[dict[str, Any]],
        original_tasks: list[EducationalTask],
    ) -> float:
        """Calculate how well learning objectives are covered"""

        all_objectives = set()
        covered_objectives = set()

        for original_task in original_tasks:
            all_objectives.update(original_task.learning_objectives)

        for completed_task in completed_tasks:
            task_objectives = completed_task.get("learning_objectives_covered", [])
            covered_objectives.update(task_objectives)

        if not all_objectives:
            return 1.0

        coverage_ratio = len(covered_objectives) / len(all_objectives)
        return min(1.0, coverage_ratio)

    async def _calculate_curriculum_alignment(
        self,
        completed_tasks: list[dict[str, Any]],
        original_tasks: list[EducationalTask],
    ) -> float:
        """Calculate curriculum standards alignment"""

        all_standards = set()
        aligned_standards = set()

        for original_task in original_tasks:
            all_standards.update(original_task.educational_standards)

        for completed_task in completed_tasks:
            task_standards = completed_task.get("curriculum_standards_met", [])
            aligned_standards.update(task_standards)

        if not all_standards:
            return 0.8  # Default score if no standards specified

        alignment_ratio = len(aligned_standards) / len(all_standards)
        return min(1.0, alignment_ratio)

    async def _calculate_detailed_quality_metrics(
        self, completed_tasks: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Calculate detailed quality metrics"""

        metrics = {
            "content_quality": 0.0,
            "instructional_design": 0.0,
            "engagement_potential": 0.0,
            "assessment_validity": 0.0,
            "technical_accuracy": 0.0,
        }

        if not completed_tasks:
            return metrics

        # Aggregate quality scores across all tasks
        for metric_key in metrics.keys():
            scores = [
                task.get("quality_metrics", {}).get(metric_key, 0.0) for task in completed_tasks
            ]
            if scores:
                metrics[metric_key] = sum(scores) / len(scores)

        return metrics

    async def _calculate_educational_effectiveness(
        self,
        completed_tasks: list[dict[str, Any]],
        original_tasks: list[EducationalTask],
    ) -> float:
        """Calculate overall educational effectiveness"""

        effectiveness_factors = []

        # Content appropriateness for grade levels
        for i, completed_task in enumerate(completed_tasks):
            if i < len(original_tasks):
                original_task = original_tasks[i]
                appropriateness = self._assess_grade_appropriateness(
                    completed_task, original_task.grade_level
                )
                effectiveness_factors.append(appropriateness)

        # Subject matter accuracy
        subject_accuracy = sum(
            task.get("subject_accuracy_score", 0.8) for task in completed_tasks
        ) / len(completed_tasks)
        effectiveness_factors.append(subject_accuracy)

        # Pedagogical soundness
        pedagogical_score = sum(
            task.get("pedagogical_score", 0.8) for task in completed_tasks
        ) / len(completed_tasks)
        effectiveness_factors.append(pedagogical_score)

        return (
            sum(effectiveness_factors) / len(effectiveness_factors)
            if effectiveness_factors
            else 0.0
        )

    def _assess_grade_appropriateness(
        self, completed_task: dict[str, Any], target_grade: int
    ) -> float:
        """Assess if content is appropriate for target grade level"""
        content_grade_level = completed_task.get("estimated_grade_level", target_grade)

        # Calculate appropriateness based on grade level difference
        grade_diff = abs(content_grade_level - target_grade)

        if grade_diff == 0:
            return 1.0
        elif grade_diff == 1:
            return 0.8
        elif grade_diff == 2:
            return 0.6
        else:
            return 0.3

    async def _calculate_accessibility_compliance(
        self, completed_tasks: list[dict[str, Any]]
    ) -> float:
        """Calculate accessibility compliance score"""

        accessibility_scores = []

        for task in completed_tasks:
            accessibility_features = task.get("accessibility_features", [])

            # Standard accessibility checklist
            required_features = [
                "alt_text",
                "captions",
                "keyboard_navigation",
                "high_contrast",
                "screen_reader_support",
            ]

            compliance_ratio = len(accessibility_features) / len(required_features)
            accessibility_scores.append(min(1.0, compliance_ratio))

        return (
            sum(accessibility_scores) / len(accessibility_scores) if accessibility_scores else 0.0
        )


class CoordinationOptimizer:
    """Optimizes coordination strategies based on performance data"""

    def __init__(self):
        self.optimization_history = []
        self.strategy_performance = defaultdict(list)

    async def optimize_coordination_strategy(
        self,
        current_performance: dict[str, Any],
        task_characteristics: dict[str, Any],
        resource_status: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate optimization recommendations"""

        recommendations = {
            "strategy_adjustments": [],
            "resource_reallocation": {},
            "performance_improvements": [],
            "quality_enhancements": [],
        }

        # Analyze current performance gaps
        performance_gaps = self._identify_performance_gaps(current_performance)

        # Generate strategy adjustments
        if performance_gaps.get("coordination_efficiency", 0) < 0.7:
            recommendations["strategy_adjustments"].append(
                "Consider switching to specialist coordination"
            )

        if performance_gaps.get("quality_consistency", 0) < 0.8:
            recommendations["strategy_adjustments"].append(
                "Implement democratic consensus for quality assurance"
            )

        # Generate resource recommendations
        if resource_status.get("load_imbalance", 0) > 0.3:
            recommendations["resource_reallocation"] = self._generate_reallocation_plan(
                resource_status
            )

        # Generate performance improvement suggestions
        recommendations["performance_improvements"] = self._generate_performance_improvements(
            current_performance, task_characteristics
        )

        return recommendations

    def _identify_performance_gaps(self, performance: dict[str, Any]) -> dict[str, float]:
        """Identify areas where performance is below optimal"""

        optimal_thresholds = {
            "coordination_efficiency": 0.8,
            "quality_consistency": 0.85,
            "resource_utilization": 0.75,
            "task_completion_rate": 0.95,
        }

        gaps = {}
        for metric, threshold in optimal_thresholds.items():
            current_value = performance.get(metric, 0.0)
            if current_value < threshold:
                gaps[metric] = threshold - current_value

        return gaps

    def _generate_reallocation_plan(self, resource_status: dict[str, Any]) -> dict[str, Any]:
        """Generate resource reallocation plan"""

        plan = {
            "agent_reassignments": [],
            "workload_redistribution": {},
            "specialization_adjustments": [],
        }

        # Identify overloaded and underutilized agents
        agent_loads = resource_status.get("agent_utilization", {})

        overloaded = [agent for agent, load in agent_loads.items() if load > 0.9]
        underutilized = [agent for agent, load in agent_loads.items() if load < 0.3]

        if overloaded and underutilized:
            plan["agent_reassignments"] = [
                {
                    "from_agent": overloaded[0],
                    "to_agent": underutilized[0],
                    "task_transfer_ratio": 0.3,
                }
            ]

        return plan

    def _generate_performance_improvements(
        self, performance: dict[str, Any], task_characteristics: dict[str, Any]
    ) -> list[str]:
        """Generate specific performance improvement suggestions"""

        improvements = []

        # Quality-based improvements
        if performance.get("average_quality", 0) < 0.8:
            improvements.append("Implement multi-agent review process for quality assurance")
            improvements.append("Add specialized quality assessment agents")

        # Efficiency-based improvements
        if performance.get("coordination_efficiency", 0) < 0.7:
            improvements.append("Optimize task batching and parallel execution")
            improvements.append("Implement predictive task scheduling")

        # Task-specific improvements
        if task_characteristics.get("complexity_variance", 0) > 0.5:
            improvements.append("Implement complexity-based agent matching")
            improvements.append("Add adaptive timeout mechanisms")

        return improvements
