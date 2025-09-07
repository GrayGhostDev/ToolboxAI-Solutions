"""
Load Balancer - Resource optimization and allocation for swarm intelligence.

This module provides comprehensive load balancing capabilities including dynamic
resource allocation, performance monitoring, bottleneck detection, and
educational content optimization with predictive scaling and quality-aware distribution.
"""

import asyncio
import time
import statistics
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
from collections import deque, defaultdict
import heapq
import psutil
import json

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Enumeration of load balancing strategies."""

    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    RESOURCE_AWARE = "resource_aware"
    QUALITY_AWARE = "quality_aware"
    EDUCATIONAL_OPTIMIZED = "educational_optimized"
    ADAPTIVE = "adaptive"


class ResourceType(Enum):
    """Types of resources to monitor and balance."""

    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    STORAGE = "storage"
    TASK_QUEUE = "task_queue"
    EDUCATIONAL_CONTEXT = "educational_context"


@dataclass
class ResourceMetrics:
    """Comprehensive resource usage metrics."""

    timestamp: datetime = field(default_factory=datetime.now)

    # System resources
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_usage_percent: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0

    # Task-specific metrics
    active_tasks: int = 0
    queued_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_task_duration: float = 0.0

    # Quality metrics
    quality_score: float = 0.0
    error_rate: float = 0.0
    throughput_per_minute: float = 0.0
    response_time_ms: float = 0.0

    # Educational-specific metrics
    content_generation_rate: float = 0.0
    curriculum_alignment_score: float = 0.0
    student_engagement_prediction: float = 0.0

    # Derived metrics
    overall_utilization: float = 0.0
    health_score: float = 1.0
    bottleneck_indicators: List[str] = field(default_factory=list)

    def calculate_overall_utilization(self):
        """Calculate overall resource utilization."""
        cpu_weight = 0.4
        memory_weight = 0.3
        task_weight = 0.3

        task_utilization = min(100.0, (self.active_tasks + self.queued_tasks) * 10)

        self.overall_utilization = (
            cpu_weight * self.cpu_percent
            + memory_weight * self.memory_percent
            + task_weight * task_utilization
        ) / 100.0

    def calculate_health_score(self):
        """Calculate overall health score (0.0 = critical, 1.0 = excellent)."""
        health_factors = []

        # CPU health (penalize high usage)
        if self.cpu_percent < 70:
            health_factors.append(1.0)
        elif self.cpu_percent < 85:
            health_factors.append(0.7)
        else:
            health_factors.append(0.3)

        # Memory health
        if self.memory_percent < 80:
            health_factors.append(1.0)
        elif self.memory_percent < 90:
            health_factors.append(0.6)
        else:
            health_factors.append(0.2)

        # Error rate health
        if self.error_rate < 0.01:  # Less than 1%
            health_factors.append(1.0)
        elif self.error_rate < 0.05:  # Less than 5%
            health_factors.append(0.7)
        else:
            health_factors.append(0.4)

        # Quality health
        if self.quality_score > 0.8:
            health_factors.append(1.0)
        elif self.quality_score > 0.6:
            health_factors.append(0.8)
        else:
            health_factors.append(0.5)

        self.health_score = statistics.mean(health_factors) if health_factors else 0.5

    def detect_bottlenecks(self):
        """Detect potential bottlenecks."""
        self.bottleneck_indicators.clear()

        if self.cpu_percent > 85:
            self.bottleneck_indicators.append("High CPU usage")

        if self.memory_percent > 85:
            self.bottleneck_indicators.append("High memory usage")

        if self.queued_tasks > self.active_tasks * 2:
            self.bottleneck_indicators.append("Task queue backlog")

        if self.error_rate > 0.1:
            self.bottleneck_indicators.append("High error rate")

        if self.average_task_duration > 300:  # 5 minutes
            self.bottleneck_indicators.append("Slow task execution")

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_usage_percent": self.disk_usage_percent,
            "active_tasks": self.active_tasks,
            "queued_tasks": self.queued_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "average_task_duration": self.average_task_duration,
            "quality_score": self.quality_score,
            "error_rate": self.error_rate,
            "throughput_per_minute": self.throughput_per_minute,
            "response_time_ms": self.response_time_ms,
            "content_generation_rate": self.content_generation_rate,
            "curriculum_alignment_score": self.curriculum_alignment_score,
            "student_engagement_prediction": self.student_engagement_prediction,
            "overall_utilization": self.overall_utilization,
            "health_score": self.health_score,
            "bottleneck_indicators": self.bottleneck_indicators,
        }


@dataclass
class WorkerResourceState:
    """Resource state for a specific worker."""

    worker_id: str
    metrics: ResourceMetrics
    load_factor: float = 0.0
    capability_score: float = 1.0
    educational_specialization_score: float = 1.0
    historical_performance: deque = field(default_factory=lambda: deque(maxlen=100))
    last_updated: datetime = field(default_factory=datetime.now)

    # Predictive metrics
    predicted_completion_time: float = 0.0
    predicted_quality_score: float = 0.8
    workload_trend: str = "stable"  # increasing, stable, decreasing

    def update_performance_history(self, task_duration: float, quality_score: float):
        """Update historical performance data."""
        self.historical_performance.append(
            {
                "timestamp": datetime.now(),
                "duration": task_duration,
                "quality": quality_score,
            }
        )

        # Update predictions
        if len(self.historical_performance) >= 3:
            recent_durations = [
                p["duration"] for p in list(self.historical_performance)[-10:]
            ]
            recent_qualities = [
                p["quality"] for p in list(self.historical_performance)[-10:]
            ]

            self.predicted_completion_time = statistics.mean(recent_durations)
            self.predicted_quality_score = statistics.mean(recent_qualities)

            # Determine trend
            if len(recent_durations) >= 5:
                first_half = recent_durations[: len(recent_durations) // 2]
                second_half = recent_durations[len(recent_durations) // 2 :]

                if statistics.mean(second_half) > statistics.mean(first_half) * 1.1:
                    self.workload_trend = "increasing"
                elif statistics.mean(second_half) < statistics.mean(first_half) * 0.9:
                    self.workload_trend = "decreasing"
                else:
                    self.workload_trend = "stable"


@dataclass
class LoadBalancingConfig:
    """Configuration for load balancing behavior."""

    strategy: LoadBalancingStrategy = LoadBalancingStrategy.EDUCATIONAL_OPTIMIZED
    enable_adaptive_strategy: bool = True
    enable_predictive_scaling: bool = True
    enable_quality_optimization: bool = True

    # Monitoring intervals
    metrics_collection_interval: int = 10  # seconds
    rebalancing_interval: int = 30  # seconds
    prediction_interval: int = 60  # seconds

    # Thresholds
    cpu_threshold: float = 85.0
    memory_threshold: float = 85.0
    queue_threshold: int = 50
    error_rate_threshold: float = 0.1
    quality_threshold: float = 0.7

    # Educational optimizations
    prioritize_subject_experts: bool = True
    balance_grade_level_distribution: bool = True
    optimize_curriculum_alignment: bool = True

    # Weights for composite scoring
    performance_weight: float = 0.4
    quality_weight: float = 0.3
    educational_weight: float = 0.3

    # Batch processing
    enable_batch_optimization: bool = False
    batch_size_target: int = 5
    batch_timeout: float = 30.0


class LoadBalancer:
    """
    Advanced load balancer for educational content generation with
    resource optimization, predictive scaling, quality-aware distribution,
    and educational domain-specific optimizations.
    """

    def __init__(
        self,
        strategy: str = "educational_optimized",
        config: Optional[LoadBalancingConfig] = None,
    ):
        # Convert string to enum
        try:
            self.strategy = LoadBalancingStrategy(strategy)
        except ValueError:
            logger.warning(f"Unknown strategy '{strategy}', using default")
            self.strategy = LoadBalancingStrategy.EDUCATIONAL_OPTIMIZED

        self.config = config or LoadBalancingConfig()
        self.config.strategy = self.strategy

        # Worker state management
        self.worker_states: Dict[str, WorkerResourceState] = {}
        self.worker_selection_history: deque = deque(maxlen=1000)

        # Load balancing state
        self._round_robin_index = 0
        self._weighted_round_robin_weights: Dict[str, int] = {}

        # Resource monitoring
        self.system_metrics: ResourceMetrics = ResourceMetrics()
        self.metrics_history: deque = deque(maxlen=1000)

        # Performance tracking
        self.allocation_history: List[Dict[str, Any]] = []
        self.bottleneck_alerts: List[Dict[str, Any]] = []

        # Educational optimization
        self.subject_workload_distribution: Dict[str, int] = defaultdict(int)
        self.grade_level_distribution: Dict[int, int] = defaultdict(int)
        self.curriculum_coverage_tracking: Dict[str, float] = defaultdict(float)

        # Predictive modeling
        self.load_predictions: Dict[str, float] = {}
        self.capacity_forecasts: Dict[str, Dict[str, float]] = {}

        # Batch processing
        self.batch_mode_enabled = False
        self.pending_batch_tasks: List[Any] = []
        self.batch_formation_time: Optional[datetime] = None

        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._rebalancing_task: Optional[asyncio.Task] = None
        self._prediction_task: Optional[asyncio.Task] = None

        logger.info(f"LoadBalancer initialized with strategy: {self.strategy}")

    async def initialize(self):
        """Initialize the load balancer and start background processes."""
        try:
            # Collect initial system metrics
            await self._collect_system_metrics()

            # Start background monitoring tasks
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self._rebalancing_task = asyncio.create_task(self._rebalancing_loop())

            if self.config.enable_predictive_scaling:
                self._prediction_task = asyncio.create_task(self._prediction_loop())

            logger.info("LoadBalancer initialized successfully")

        except (ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.error(f"Failed to initialize LoadBalancer: {e}")
            raise

    async def shutdown(self):
        """Gracefully shutdown the load balancer."""
        try:
            # Cancel background tasks
            tasks = [
                self._monitoring_task,
                self._rebalancing_task,
                self._prediction_task,
            ]

            for task in tasks:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            # Process any pending batch tasks
            if self.batch_mode_enabled and self.pending_batch_tasks:
                logger.info(
                    f"Processing {len(self.pending_batch_tasks)} pending batch tasks..."
                )
                # This would trigger batch processing

            logger.info("LoadBalancer shutdown completed")

        except (ValueError, TypeError, RuntimeError, asyncio.CancelledError) as e:
            logger.error(f"Error during LoadBalancer shutdown: {e}")

    async def register_worker(
        self,
        worker_id: str,
        capabilities: List[str],
        educational_specializations: Optional[List[str]] = None,
    ):
        """Register a new worker with the load balancer."""
        initial_metrics = ResourceMetrics()
        await self._collect_worker_metrics(worker_id, initial_metrics)

        worker_state = WorkerResourceState(worker_id=worker_id, metrics=initial_metrics)

        # Calculate educational specialization score
        if educational_specializations:
            worker_state.educational_specialization_score = (
                len(educational_specializations) * 0.1 + 1.0
            )

        self.worker_states[worker_id] = worker_state

        # Initialize weighted round robin weights
        self._weighted_round_robin_weights[worker_id] = 1

        logger.info(f"Registered worker {worker_id} with capabilities: {capabilities}")

    async def unregister_worker(self, worker_id: str):
        """Unregister a worker from the load balancer."""
        self.worker_states.pop(worker_id, None)
        self._weighted_round_robin_weights.pop(worker_id, None)

        logger.info(f"Unregistered worker {worker_id}")

    async def select_worker(
        self, available_workers: List[Any], task: Optional[Any] = None
    ) -> Any:
        """
        Select the best worker for task assignment based on load balancing strategy.

        Args:
            available_workers: List of available worker agents
            task: Optional task object with context for selection

        Returns:
            Selected worker agent
        """
        if not available_workers:
            return None

        if len(available_workers) == 1:
            worker = available_workers[0]
            await self._record_selection(worker.worker_id, task)
            return worker

        # Update worker states before selection
        await self._update_worker_states(available_workers)

        # Select based on strategy
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            selected_worker = await self._select_round_robin(available_workers)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            selected_worker = await self._select_weighted_round_robin(available_workers)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            selected_worker = await self._select_least_connections(available_workers)
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            selected_worker = await self._select_least_response_time(available_workers)
        elif self.strategy == LoadBalancingStrategy.RESOURCE_AWARE:
            selected_worker = await self._select_resource_aware(available_workers)
        elif self.strategy == LoadBalancingStrategy.QUALITY_AWARE:
            selected_worker = await self._select_quality_aware(available_workers, task)
        elif self.strategy == LoadBalancingStrategy.EDUCATIONAL_OPTIMIZED:
            selected_worker = await self._select_educational_optimized(
                available_workers, task
            )
        elif self.strategy == LoadBalancingStrategy.ADAPTIVE:
            selected_worker = await self._select_adaptive(available_workers, task)
        else:
            # Default to resource-aware
            selected_worker = await self._select_resource_aware(available_workers)

        if selected_worker:
            await self._record_selection(selected_worker.worker_id, task)

        return selected_worker

    async def update_worker_performance(
        self,
        worker_id: str,
        task_duration: float,
        quality_score: float,
        success: bool = True,
    ):
        """Update worker performance metrics after task completion."""
        if worker_id not in self.worker_states:
            return

        worker_state = self.worker_states[worker_id]

        # Update performance history
        worker_state.update_performance_history(task_duration, quality_score)

        # Update weighted round robin weights based on performance
        if success and quality_score > 0.8:
            self._weighted_round_robin_weights[worker_id] += 1
        elif not success or quality_score < 0.5:
            self._weighted_round_robin_weights[worker_id] = max(
                1, self._weighted_round_robin_weights[worker_id] - 1
            )

        # Record allocation outcome
        self.allocation_history.append(
            {
                "timestamp": datetime.now(),
                "worker_id": worker_id,
                "task_duration": task_duration,
                "quality_score": quality_score,
                "success": success,
            }
        )

        # Limit history size
        if len(self.allocation_history) > 10000:
            self.allocation_history = self.allocation_history[-5000:]

    async def get_metrics(self) -> ResourceMetrics:
        """Get current system resource metrics."""
        await self._collect_system_metrics()
        return self.system_metrics

    async def get_worker_metrics(self, worker_id: str) -> Optional[ResourceMetrics]:
        """Get resource metrics for a specific worker."""
        if worker_id not in self.worker_states:
            return None

        return self.worker_states[worker_id].metrics

    async def get_load_balancing_status(self) -> Dict[str, Any]:
        """Get comprehensive load balancing status."""
        # Calculate distribution statistics
        worker_loads = {
            worker_id: state.load_factor
            for worker_id, state in self.worker_states.items()
        }

        # Recent allocation distribution
        recent_allocations = self.allocation_history[-100:]  # Last 100 allocations
        allocation_distribution = defaultdict(int)
        for allocation in recent_allocations:
            allocation_distribution[allocation["worker_id"]] += 1

        # Performance trends
        recent_quality_scores = [
            a["quality_score"] for a in recent_allocations if a["success"]
        ]
        avg_quality = (
            statistics.mean(recent_quality_scores) if recent_quality_scores else 0.0
        )

        return {
            "strategy": self.strategy.value,
            "total_workers": len(self.worker_states),
            "system_metrics": self.system_metrics.to_dict(),
            "worker_loads": worker_loads,
            "allocation_distribution": dict(allocation_distribution),
            "average_quality_score": avg_quality,
            "recent_bottleneck_alerts": self.bottleneck_alerts[-10:],
            "subject_distribution": dict(self.subject_workload_distribution),
            "grade_level_distribution": dict(self.grade_level_distribution),
            "batch_mode_enabled": self.batch_mode_enabled,
            "pending_batch_tasks": len(self.pending_batch_tasks),
            "load_predictions": self.load_predictions.copy(),
        }

    async def enable_batch_mode(self):
        """Enable batch processing mode for optimized resource usage."""
        self.batch_mode_enabled = True
        self.batch_formation_time = datetime.now()
        logger.info("Batch mode enabled")

    async def disable_batch_mode(self):
        """Disable batch processing mode."""
        # Process any pending tasks
        if self.pending_batch_tasks:
            await self._process_batch_tasks()

        self.batch_mode_enabled = False
        self.batch_formation_time = None
        logger.info("Batch mode disabled")

    async def predict_resource_needs(
        self, time_horizon_minutes: int = 60
    ) -> Dict[str, Any]:
        """Predict future resource needs based on current trends."""
        if not self.metrics_history:
            return {"prediction": "insufficient_data"}

        # Analyze historical trends
        recent_metrics = list(self.metrics_history)[-20:]  # Last 20 data points

        if len(recent_metrics) < 5:
            return {"prediction": "insufficient_data"}

        # Calculate trends
        cpu_trend = self._calculate_trend([m.cpu_percent for m in recent_metrics])
        memory_trend = self._calculate_trend([m.memory_percent for m in recent_metrics])
        task_trend = self._calculate_trend(
            [m.active_tasks + m.queued_tasks for m in recent_metrics]
        )

        # Project future values
        current_cpu = recent_metrics[-1].cpu_percent
        current_memory = recent_metrics[-1].memory_percent
        current_tasks = (
            recent_metrics[-1].active_tasks + recent_metrics[-1].queued_tasks
        )

        # Simple linear projection
        time_factor = time_horizon_minutes / 10.0  # Trend per 10-minute interval

        predicted_cpu = max(0, min(100, current_cpu + cpu_trend * time_factor))
        predicted_memory = max(0, min(100, current_memory + memory_trend * time_factor))
        predicted_tasks = max(0, current_tasks + task_trend * time_factor)

        # Determine scaling recommendations
        scaling_recommendation = "maintain"
        if (
            predicted_cpu > 80
            or predicted_memory > 80
            or predicted_tasks > current_tasks * 1.5
        ):
            scaling_recommendation = "scale_up"
        elif (
            predicted_cpu < 30
            and predicted_memory < 50
            and predicted_tasks < current_tasks * 0.7
        ):
            scaling_recommendation = "scale_down"

        return {
            "prediction": "success",
            "time_horizon_minutes": time_horizon_minutes,
            "predicted_cpu_percent": predicted_cpu,
            "predicted_memory_percent": predicted_memory,
            "predicted_active_tasks": predicted_tasks,
            "scaling_recommendation": scaling_recommendation,
            "confidence": 0.7,  # Static confidence for now
            "trends": {
                "cpu_trend": cpu_trend,
                "memory_trend": memory_trend,
                "task_trend": task_trend,
            },
        }

    # Private methods

    async def _monitoring_loop(self):
        """Background loop for monitoring system and worker metrics."""
        while True:
            try:
                # Collect system metrics
                await self._collect_system_metrics()

                # Detect bottlenecks
                await self._detect_bottlenecks()

                # Update load predictions
                if self.config.enable_predictive_scaling:
                    await self._update_load_predictions()

                await asyncio.sleep(self.config.metrics_collection_interval)

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.config.metrics_collection_interval)

    async def _rebalancing_loop(self):
        """Background loop for load rebalancing decisions."""
        while True:
            try:
                # Check if rebalancing is needed
                if await self._should_rebalance():
                    await self._perform_rebalancing()

                # Adaptive strategy adjustment
                if self.config.enable_adaptive_strategy:
                    await self._adjust_strategy()

                await asyncio.sleep(self.config.rebalancing_interval)

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(f"Error in rebalancing loop: {e}")
                await asyncio.sleep(self.config.rebalancing_interval)

    async def _prediction_loop(self):
        """Background loop for predictive analysis."""
        while True:
            try:
                # Update capacity forecasts
                await self._update_capacity_forecasts()

                # Educational workload analysis
                await self._analyze_educational_workload_patterns()

                await asyncio.sleep(self.config.prediction_interval)

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(f"Error in prediction loop: {e}")
                await asyncio.sleep(self.config.prediction_interval)

    async def _collect_system_metrics(self):
        """Collect current system resource metrics."""
        try:
            # Get system metrics using psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            network = psutil.net_io_counters()

            # Update system metrics
            self.system_metrics = ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=disk.percent,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
            )

            # Calculate derived metrics
            self.system_metrics.calculate_overall_utilization()
            self.system_metrics.calculate_health_score()
            self.system_metrics.detect_bottlenecks()

            # Add to history
            self.metrics_history.append(self.system_metrics)

        except (ValueError, TypeError, RuntimeError, OSError) as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def _collect_worker_metrics(self, worker_id: str, metrics: ResourceMetrics):
        """Collect metrics for a specific worker."""
        # This would collect worker-specific metrics
        # For now, use system metrics as base
        metrics.cpu_percent = self.system_metrics.cpu_percent
        metrics.memory_percent = self.system_metrics.memory_percent

        # Update derived metrics
        metrics.calculate_overall_utilization()
        metrics.calculate_health_score()
        metrics.detect_bottlenecks()

    async def _update_worker_states(self, workers: List[Any]):
        """Update resource states for all workers."""
        for worker in workers:
            worker_id = worker.worker_id

            if worker_id not in self.worker_states:
                continue

            worker_state = self.worker_states[worker_id]

            # Update metrics
            await self._collect_worker_metrics(worker_id, worker_state.metrics)

            # Update load factor
            worker_state.load_factor = await worker.get_load_factor()

            # Update capability score
            if hasattr(worker, "get_capabilities_score"):
                # This would be called with a task if available
                worker_state.capability_score = 1.0  # Default for now

            worker_state.last_updated = datetime.now()

    async def _select_round_robin(self, workers: List[Any]) -> Any:
        """Select worker using round-robin strategy."""
        selected_worker = workers[self._round_robin_index % len(workers)]
        self._round_robin_index = (self._round_robin_index + 1) % len(workers)
        return selected_worker

    async def _select_weighted_round_robin(self, workers: List[Any]) -> Any:
        """Select worker using weighted round-robin strategy."""
        # Build weighted list
        weighted_workers = []
        for worker in workers:
            weight = self._weighted_round_robin_weights.get(worker.worker_id, 1)
            weighted_workers.extend([worker] * weight)

        if not weighted_workers:
            return workers[0]

        selected_worker = weighted_workers[
            self._round_robin_index % len(weighted_workers)
        ]
        self._round_robin_index = (self._round_robin_index + 1) % len(weighted_workers)
        return selected_worker

    async def _select_least_connections(self, workers: List[Any]) -> Any:
        """Select worker with least active connections/tasks."""
        return min(
            workers, key=lambda w: w.current_tasks if hasattr(w, "current_tasks") else 0
        )

    async def _select_least_response_time(self, workers: List[Any]) -> Any:
        """Select worker with least average response time."""
        best_worker = workers[0]
        best_time = float("inf")

        for worker in workers:
            worker_id = worker.worker_id
            if worker_id in self.worker_states:
                predicted_time = self.worker_states[worker_id].predicted_completion_time
                if predicted_time < best_time:
                    best_time = predicted_time
                    best_worker = worker

        return best_worker

    async def _select_resource_aware(self, workers: List[Any]) -> Any:
        """Select worker based on resource utilization."""
        best_worker = workers[0]
        best_utilization = 1.0

        for worker in workers:
            worker_id = worker.worker_id
            if worker_id in self.worker_states:
                state = self.worker_states[worker_id]
                utilization = state.metrics.overall_utilization

                if utilization < best_utilization:
                    best_utilization = utilization
                    best_worker = worker

        return best_worker

    async def _select_quality_aware(
        self, workers: List[Any], task: Optional[Any] = None
    ) -> Any:
        """Select worker based on predicted quality outcomes."""
        best_worker = workers[0]
        best_quality_score = 0.0

        for worker in workers:
            worker_id = worker.worker_id
            if worker_id in self.worker_states:
                state = self.worker_states[worker_id]

                # Combine predicted quality with current load
                quality_score = state.predicted_quality_score
                load_penalty = state.load_factor * 0.3  # Penalize high load

                adjusted_score = quality_score - load_penalty

                if adjusted_score > best_quality_score:
                    best_quality_score = adjusted_score
                    best_worker = worker

        return best_worker

    async def _select_educational_optimized(
        self, workers: List[Any], task: Optional[Any] = None
    ) -> Any:
        """Select worker optimized for educational content generation."""
        if not task:
            return await self._select_resource_aware(workers)

        best_worker = workers[0]
        best_score = 0.0

        # Extract educational context
        educational_context = getattr(task, "educational_context", {})
        subject = educational_context.get("subject", "")
        grade_level = educational_context.get("grade_level", 0)

        for worker in workers:
            worker_id = worker.worker_id
            score = 0.0

            # Base performance score
            if worker_id in self.worker_states:
                state = self.worker_states[worker_id]
                score += state.predicted_quality_score * self.config.quality_weight
                score += (1.0 - state.load_factor) * self.config.performance_weight
                score += (
                    state.educational_specialization_score
                    * self.config.educational_weight
                )

            # Educational specialization bonus
            if hasattr(worker, "educational_specializations"):
                specializations = getattr(worker, "educational_specializations", [])
                if subject in specializations:
                    score += 0.3  # Subject match bonus

            # Load balancing for educational content
            if self.config.balance_grade_level_distribution:
                current_distribution = self.grade_level_distribution.get(grade_level, 0)
                avg_distribution = sum(self.grade_level_distribution.values()) / max(
                    1, len(self.grade_level_distribution)
                )

                if current_distribution < avg_distribution:
                    score += 0.1  # Bonus for underrepresented grade level

            if score > best_score:
                best_score = score
                best_worker = worker

        return best_worker

    async def _select_adaptive(
        self, workers: List[Any], task: Optional[Any] = None
    ) -> Any:
        """Select worker using adaptive strategy based on current conditions."""
        # Analyze current system state to choose best sub-strategy
        system_load = self.system_metrics.overall_utilization
        error_rate = self.system_metrics.error_rate

        if system_load > 0.8:
            # High load - prioritize resource efficiency
            return await self._select_resource_aware(workers)
        elif error_rate > 0.1:
            # High error rate - prioritize quality
            return await self._select_quality_aware(workers, task)
        elif task and hasattr(task, "educational_context"):
            # Educational task - use educational optimization
            return await self._select_educational_optimized(workers, task)
        else:
            # Normal conditions - use weighted round robin
            return await self._select_weighted_round_robin(workers)

    async def _record_selection(self, worker_id: str, task: Optional[Any] = None):
        """Record worker selection for analysis and optimization."""
        selection_record = {
            "timestamp": datetime.now(),
            "worker_id": worker_id,
            "task_type": getattr(task, "task_type", "unknown") if task else "unknown",
            "strategy": self.strategy.value,
        }

        # Add educational context if available
        if task and hasattr(task, "educational_context"):
            context = task.educational_context
            selection_record.update(
                {
                    "subject": context.get("subject", ""),
                    "grade_level": context.get("grade_level", 0),
                }
            )

            # Update educational distribution tracking
            if "subject" in context:
                self.subject_workload_distribution[context["subject"]] += 1
            if "grade_level" in context:
                self.grade_level_distribution[context["grade_level"]] += 1

        self.worker_selection_history.append(selection_record)

    async def _detect_bottlenecks(self):
        """Detect system bottlenecks and generate alerts."""
        current_time = datetime.now()

        # Check system-level bottlenecks
        if self.system_metrics.cpu_percent > self.config.cpu_threshold:
            alert = {
                "timestamp": current_time,
                "type": "cpu_bottleneck",
                "severity": (
                    "high" if self.system_metrics.cpu_percent > 90 else "medium"
                ),
                "message": f"CPU usage at {self.system_metrics.cpu_percent:.1f}%",
                "recommendation": "Consider scaling up or optimizing CPU-intensive tasks",
            }
            self.bottleneck_alerts.append(alert)

        if self.system_metrics.memory_percent > self.config.memory_threshold:
            alert = {
                "timestamp": current_time,
                "type": "memory_bottleneck",
                "severity": (
                    "high" if self.system_metrics.memory_percent > 90 else "medium"
                ),
                "message": f"Memory usage at {self.system_metrics.memory_percent:.1f}%",
                "recommendation": "Consider scaling up or optimizing memory usage",
            }
            self.bottleneck_alerts.append(alert)

        # Check worker-level bottlenecks
        overloaded_workers = []
        for worker_id, state in self.worker_states.items():
            if state.load_factor > 0.9:
                overloaded_workers.append(worker_id)

        if overloaded_workers:
            alert = {
                "timestamp": current_time,
                "type": "worker_overload",
                "severity": "medium",
                "message": f"{len(overloaded_workers)} workers overloaded: {overloaded_workers[:3]}",
                "recommendation": "Redistribute tasks or add more workers",
            }
            self.bottleneck_alerts.append(alert)

        # Limit alert history
        if len(self.bottleneck_alerts) > 1000:
            self.bottleneck_alerts = self.bottleneck_alerts[-500:]

    async def _should_rebalance(self) -> bool:
        """Determine if load rebalancing is needed."""
        if len(self.worker_states) < 2:
            return False

        # Check load variance
        load_factors = [state.load_factor for state in self.worker_states.values()]
        if len(load_factors) < 2:
            return False

        load_variance = statistics.variance(load_factors)

        # Rebalance if high variance in load or any worker overloaded
        return (
            load_variance > 0.1
            or any(load > 0.9 for load in load_factors)
            or any(
                len(state.metrics.bottleneck_indicators) > 0
                for state in self.worker_states.values()
            )
        )

    async def _perform_rebalancing(self):
        """Perform load rebalancing operations."""
        logger.info("Performing load rebalancing...")

        # Update weighted round robin weights based on current performance
        for worker_id, state in self.worker_states.items():
            current_weight = self._weighted_round_robin_weights.get(worker_id, 1)

            # Increase weight for underloaded, high-quality workers
            if state.load_factor < 0.5 and state.predicted_quality_score > 0.8:
                new_weight = min(10, current_weight + 1)
            # Decrease weight for overloaded or poor-quality workers
            elif state.load_factor > 0.8 or state.predicted_quality_score < 0.6:
                new_weight = max(1, current_weight - 1)
            else:
                new_weight = current_weight

            self._weighted_round_robin_weights[worker_id] = new_weight

        logger.info("Load rebalancing completed")

    async def _adjust_strategy(self):
        """Adjust load balancing strategy based on current performance."""
        if not self.allocation_history:
            return

        # Analyze recent performance
        recent_allocations = self.allocation_history[-100:]

        success_rate = sum(1 for a in recent_allocations if a["success"]) / len(
            recent_allocations
        )
        avg_quality = statistics.mean(
            [a["quality_score"] for a in recent_allocations if a["success"]]
        )

        # Switch strategies based on performance
        current_strategy = self.strategy

        if success_rate < 0.9:
            # Low success rate - prioritize resource awareness
            self.strategy = LoadBalancingStrategy.RESOURCE_AWARE
        elif avg_quality < 0.7:
            # Low quality - prioritize quality awareness
            self.strategy = LoadBalancingStrategy.QUALITY_AWARE
        else:
            # Good performance - use educational optimization
            self.strategy = LoadBalancingStrategy.EDUCATIONAL_OPTIMIZED

        if current_strategy != self.strategy:
            logger.info(
                f"Adaptive strategy changed from {current_strategy.value} to {self.strategy.value}"
            )

    async def _update_load_predictions(self):
        """Update load predictions based on historical trends."""
        for worker_id, state in self.worker_states.items():
            if len(state.historical_performance) >= 5:
                # Simple trend analysis
                recent_performances = list(state.historical_performance)[-10:]
                durations = [p["duration"] for p in recent_performances]

                # Predict future load based on trend
                if len(durations) >= 3:
                    trend = self._calculate_trend(durations)
                    current_avg = statistics.mean(durations)
                    predicted_load = max(
                        0.0, min(1.0, (current_avg + trend) / 300.0)
                    )  # Normalize to 0-1

                    self.load_predictions[worker_id] = predicted_load

    async def _update_capacity_forecasts(self):
        """Update capacity forecasts for resource planning."""
        # Forecast system capacity based on trends
        if len(self.metrics_history) >= 10:
            recent_metrics = list(self.metrics_history)[-20:]

            cpu_values = [m.cpu_percent for m in recent_metrics]
            memory_values = [m.memory_percent for m in recent_metrics]
            task_values = [m.active_tasks + m.queued_tasks for m in recent_metrics]

            # Calculate forecasts for next hour
            cpu_forecast = self._forecast_value(cpu_values, 6)  # 6 intervals (1 hour)
            memory_forecast = self._forecast_value(memory_values, 6)
            task_forecast = self._forecast_value(task_values, 6)

            self.capacity_forecasts["system"] = {
                "cpu_forecast": cpu_forecast,
                "memory_forecast": memory_forecast,
                "task_forecast": task_forecast,
                "timestamp": datetime.now(),
            }

    async def _analyze_educational_workload_patterns(self):
        """Analyze patterns in educational workload for optimization."""
        # Analyze subject distribution trends
        if self.subject_workload_distribution:
            total_tasks = sum(self.subject_workload_distribution.values())
            subject_ratios = {
                subject: count / total_tasks
                for subject, count in self.subject_workload_distribution.items()
            }

            # Identify underrepresented subjects
            avg_ratio = 1.0 / len(subject_ratios) if subject_ratios else 0
            underrepresented = [
                subject
                for subject, ratio in subject_ratios.items()
                if ratio < avg_ratio * 0.7
            ]

            if underrepresented:
                logger.info(f"Underrepresented subjects detected: {underrepresented}")

        # Similar analysis for grade levels
        if self.grade_level_distribution:
            total_tasks = sum(self.grade_level_distribution.values())
            grade_ratios = {
                grade: count / total_tasks
                for grade, count in self.grade_level_distribution.items()
            }

            # This could inform worker specialization recommendations

    async def _process_batch_tasks(self):
        """Process pending batch tasks."""
        if not self.pending_batch_tasks:
            return

        logger.info(f"Processing batch of {len(self.pending_batch_tasks)} tasks")

        # Group tasks by similarity for batch processing
        task_groups = self._group_similar_tasks(self.pending_batch_tasks)

        # Process each group
        for group in task_groups:
            # This would trigger actual batch processing
            logger.info(f"Processing task group of size {len(group)}")

        # Clear pending tasks
        self.pending_batch_tasks.clear()

    def _group_similar_tasks(self, tasks: List[Any]) -> List[List[Any]]:
        """Group similar tasks for batch processing."""
        # Simple grouping by task type
        groups = defaultdict(list)

        for task in tasks:
            task_type = getattr(task, "task_type", "unknown")
            groups[task_type].append(task)

        return list(groups.values())

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate simple linear trend in values."""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))

        # Linear regression slope
        denominator = n * x2_sum - x_sum * x_sum
        if denominator == 0:
            return 0.0

        slope = (n * xy_sum - x_sum * y_sum) / denominator
        return slope

    def _forecast_value(
        self, historical_values: List[float], periods_ahead: int
    ) -> float:
        """Simple forecasting using linear trend."""
        if len(historical_values) < 2:
            return historical_values[0] if historical_values else 0.0

        trend = self._calculate_trend(historical_values)
        current_value = historical_values[-1]

        # Simple linear projection
        forecasted_value = current_value + trend * periods_ahead

        # Apply bounds based on historical data
        min_val = min(historical_values)
        max_val = max(historical_values)

        # Allow some extrapolation beyond historical bounds
        lower_bound = min_val - (max_val - min_val) * 0.2
        upper_bound = max_val + (max_val - min_val) * 0.2

        return max(lower_bound, min(upper_bound, forecasted_value))
