"""
Error Aggregation Intelligence Agent

Specialized agent for collecting, categorizing, and prioritizing errors
from multiple sources with intelligent routing and alerting.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass
import redis.asyncio as redis
from pydantic import BaseModel, Field

from core.agents.error_handling.base_error_agent import (
    BaseErrorAgent,
    ErrorAgentConfig,
    ErrorState,
    ErrorType,
    ErrorPriority
)

logger = logging.getLogger(__name__)


class AggregatedError(BaseModel):
    """Model for aggregated error information"""
    aggregation_id: str = Field(description="Unique aggregation identifier")
    error_states: List[ErrorState] = Field(description="Individual error states")
    count: int = Field(description="Total error count")
    first_seen: str = Field(description="First occurrence timestamp")
    last_seen: str = Field(description="Last occurrence timestamp")
    sources: List[str] = Field(description="Error sources")
    severity_score: float = Field(description="Calculated severity score")
    assigned_agent: Optional[str] = Field(description="Agent assigned to handle")
    resolution_status: str = Field(description="Current resolution status")


class ErrorQueue(BaseModel):
    """Model for error processing queue"""
    queue_id: str = Field(description="Queue identifier")
    priority: ErrorPriority = Field(description="Queue priority level")
    errors: List[ErrorState] = Field(description="Errors in queue")
    processing_order: List[str] = Field(description="Order of processing")
    assigned_agents: Dict[str, str] = Field(description="Error to agent mapping")


@dataclass
class AggregationConfig(ErrorAgentConfig):
    """Configuration for error aggregation"""
    redis_url: str = "redis://localhost:6379"
    aggregation_window: int = 60  # seconds
    alert_threshold: int = 10
    priority_weights: Dict[str, float] = None


class ErrorAggregationIntelligenceAgent(BaseErrorAgent):
    """
    Agent for intelligent error aggregation and routing.

    Capabilities:
    - Multi-source error collection
    - Intelligent categorization
    - Priority-based queuing
    - Agent assignment optimization
    - Alert generation
    - Deduplication
    """

    def __init__(self, config: Optional[AggregationConfig] = None):
        if config is None:
            config = AggregationConfig(
                name="ErrorAggregationIntelligenceAgent",
                model="gpt-4",
                temperature=0.2,
                priority_weights={
                    "frequency": 0.3,
                    "severity": 0.4,
                    "impact": 0.3
                }
            )

        super().__init__(config)
        self.aggregation_config = config

        # Aggregation state
        self.aggregated_errors: Dict[str, AggregatedError] = {}
        self.error_queues: Dict[ErrorPriority, ErrorQueue] = {}
        self.agent_assignments: Dict[str, str] = {}

        # Initialize queues
        self._initialize_queues()

        # Redis connection for distributed aggregation
        self.redis_client = None

        logger.info("Initialized Error Aggregation Intelligence Agent")

    def _initialize_queues(self):
        """Initialize priority queues"""
        for priority in ErrorPriority:
            self.error_queues[priority] = ErrorQueue(
                queue_id=f"queue_{priority.value}",
                priority=priority,
                errors=[],
                processing_order=[],
                assigned_agents={}
            )

    async def _init_redis(self):
        """Initialize Redis connection"""
        if not self.redis_client:
            try:
                self.redis_client = await redis.from_url(
                    self.aggregation_config.redis_url,
                    decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("Connected to Redis for error aggregation")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_client = None

    async def aggregate_errors(
        self,
        errors: List[ErrorState],
        source: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Aggregate errors from a source.

        Args:
            errors: List of errors to aggregate
            source: Source of the errors

        Returns:
            Aggregation results with routing decisions
        """
        await self._init_redis()

        aggregation_results = {
            "total_errors": len(errors),
            "aggregated_groups": [],
            "queue_assignments": {},
            "agent_assignments": {},
            "alerts_generated": []
        }

        # Group similar errors
        error_groups = self._group_similar_errors(errors)

        # Process each group
        for group_key, group_errors in error_groups.items():
            # Create or update aggregated error
            aggregated = self._create_aggregated_error(group_errors, source)
            self.aggregated_errors[aggregated.aggregation_id] = aggregated
            aggregation_results["aggregated_groups"].append(aggregated.aggregation_id)

            # Calculate priority and assign to queue
            priority = self._calculate_aggregate_priority(aggregated)
            self._assign_to_queue(aggregated, priority)
            aggregation_results["queue_assignments"][aggregated.aggregation_id] = priority.name

            # Assign optimal agent
            agent = await self._assign_optimal_agent(aggregated)
            if agent:
                aggregation_results["agent_assignments"][aggregated.aggregation_id] = agent

            # Check for alerts
            if aggregated.count >= self.aggregation_config.alert_threshold:
                alert = self._generate_alert(aggregated)
                aggregation_results["alerts_generated"].append(alert)

        # Store in Redis if available
        if self.redis_client:
            await self._store_aggregation_redis(aggregation_results)

        return aggregation_results

    def _group_similar_errors(self, errors: List[ErrorState]) -> Dict[str, List[ErrorState]]:
        """Group similar errors together"""
        groups = defaultdict(list)

        for error in errors:
            # Create grouping key based on error type and key characteristics
            group_key = f"{error['error_type'].value}_{error.get('file_path', 'unknown')}"
            groups[group_key].append(error)

        return groups

    def _create_aggregated_error(
        self,
        errors: List[ErrorState],
        source: str
    ) -> AggregatedError:
        """Create aggregated error from group"""
        timestamps = [e["timestamp"] for e in errors]

        return AggregatedError(
            aggregation_id=f"agg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.aggregated_errors)}",
            error_states=errors,
            count=len(errors),
            first_seen=min(timestamps),
            last_seen=max(timestamps),
            sources=[source],
            severity_score=self._calculate_severity_score(errors),
            assigned_agent=None,
            resolution_status="pending"
        )

    def _calculate_severity_score(self, errors: List[ErrorState]) -> float:
        """Calculate severity score for error group"""
        weights = self.aggregation_config.priority_weights

        # Frequency component
        frequency_score = min(len(errors) / 10, 1.0) * weights["frequency"]

        # Severity component (based on priority)
        priority_scores = {"LOW": 0.2, "MEDIUM": 0.4, "HIGH": 0.6, "CRITICAL": 0.8, "EMERGENCY": 1.0}
        avg_priority = sum(priority_scores.get(e["priority"].name, 0.5) for e in errors) / len(errors)
        severity_score = avg_priority * weights["severity"]

        # Impact component (based on affected components)
        affected_components = set()
        for error in errors:
            affected_components.update(error.get("affected_components", []))
        impact_score = min(len(affected_components) / 5, 1.0) * weights["impact"]

        return frequency_score + severity_score + impact_score

    def _calculate_aggregate_priority(self, aggregated: AggregatedError) -> ErrorPriority:
        """Calculate priority for aggregated error"""
        if aggregated.severity_score >= 0.8:
            return ErrorPriority.EMERGENCY
        elif aggregated.severity_score >= 0.6:
            return ErrorPriority.CRITICAL
        elif aggregated.severity_score >= 0.4:
            return ErrorPriority.HIGH
        elif aggregated.severity_score >= 0.2:
            return ErrorPriority.MEDIUM
        else:
            return ErrorPriority.LOW

    def _assign_to_queue(self, aggregated: AggregatedError, priority: ErrorPriority):
        """Assign aggregated error to appropriate queue"""
        queue = self.error_queues[priority]
        queue.errors.extend(aggregated.error_states)
        queue.processing_order.append(aggregated.aggregation_id)

    async def _assign_optimal_agent(self, aggregated: AggregatedError) -> Optional[str]:
        """Assign optimal agent based on error characteristics"""
        # Agent selection logic based on error type
        primary_error_type = aggregated.error_states[0]["error_type"]

        agent_map = {
            ErrorType.SYNTAX: "ErrorCorrectionAgent",
            ErrorType.RUNTIME: "AdvancedDebuggingAgent",
            ErrorType.PERFORMANCE: "PerformanceMonitorAgent",
            ErrorType.SECURITY: "DependencySecurityAgent",
            ErrorType.INTEGRATION: "IntegrationTestingCoordinator"
        }

        return agent_map.get(primary_error_type, "ErrorCorrectionAgent")

    def _generate_alert(self, aggregated: AggregatedError) -> Dict[str, Any]:
        """Generate alert for high-frequency errors"""
        return {
            "alert_id": f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "aggregation_id": aggregated.aggregation_id,
            "severity": "HIGH",
            "message": f"High frequency error detected: {aggregated.count} occurrences",
            "recommended_action": "Immediate investigation required",
            "timestamp": datetime.now().isoformat()
        }

    async def _store_aggregation_redis(self, results: Dict[str, Any]):
        """Store aggregation results in Redis"""
        if self.redis_client:
            try:
                key = f"aggregation:{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                await self.redis_client.setex(
                    key,
                    3600,  # 1 hour TTL
                    json.dumps(results, default=str)
                )
            except Exception as e:
                logger.error(f"Failed to store in Redis: {e}")

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        status = {}
        for priority, queue in self.error_queues.items():
            status[priority.name] = {
                "count": len(queue.errors),
                "pending": len(queue.processing_order),
                "assigned": len(queue.assigned_agents)
            }
        return status

    async def process_next_error(self, priority: ErrorPriority) -> Optional[ErrorState]:
        """Process next error from priority queue"""
        queue = self.error_queues[priority]
        if queue.processing_order:
            aggregation_id = queue.processing_order.pop(0)
            if aggregation_id in self.aggregated_errors:
                aggregated = self.aggregated_errors[aggregation_id]
                if aggregated.error_states:
                    return aggregated.error_states[0]
        return None