"""
Enhanced Base Integration Agent - Foundation for all integration agents

Extends the BaseAgent with integration-specific capabilities including:
- Multi-platform communication support
- Standardized error handling and retry mechanisms
- Integration-specific metrics and monitoring
- Event-driven architecture support
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from abc import abstractmethod

from core.agents.base_agent import BaseAgent, AgentConfig, AgentState, TaskResult
from core.sparc.reasoning_engine import ReasoningEngine, SPARCContext
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class IntegrationPlatform(Enum):
    """Supported integration platforms"""
    BACKEND = "backend"
    FRONTEND = "frontend"
    ROBLOX = "roblox"
    DATABASE = "database"
    CACHE = "cache"
    MESSAGING = "messaging"


class IntegrationEvent(BaseModel):
    """Event model for integration agents"""
    event_id: str
    event_type: str
    source_platform: IntegrationPlatform
    target_platform: Optional[IntegrationPlatform] = None
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class CircuitBreakerState(Enum):
    """Circuit breaker states for fault tolerance"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance"""
    failure_threshold: int = 5
    recovery_timeout: timedelta = field(default_factory=lambda: timedelta(seconds=60))
    half_open_requests: int = 3

    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    success_count: int = 0

    def record_success(self):
        """Record successful operation"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_requests:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("Circuit breaker closed after successful recovery")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0

    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.success_count = 0
            logger.warning("Circuit breaker reopened after failure in half-open state")

    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time:
                time_since_failure = datetime.utcnow() - self.last_failure_time
                if time_since_failure >= self.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                    logger.info("Circuit breaker entering half-open state")
                    return True
            return False
        else:  # HALF_OPEN
            return self.success_count < self.half_open_requests


@dataclass
class IntegrationMetrics:
    """Metrics tracking for integration operations"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    events_processed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    def record_request(self, success: bool, latency_ms: float):
        """Record request metrics"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.total_latency_ms += latency_ms

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def average_latency_ms(self) -> float:
        """Calculate average latency"""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests


class BaseIntegrationAgent(BaseAgent):
    """
    Enhanced base class for integration agents with cross-platform capabilities
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize integration agent with enhanced capabilities"""
        super().__init__(config)

        # Integration-specific components
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.metrics = IntegrationMetrics()
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff delays in seconds

        # Platform connections
        self.platform_clients: Dict[IntegrationPlatform, Any] = {}

        # Event queue for async processing
        self.event_queue: asyncio.Queue = asyncio.Queue()

        # Initialize SPARC reasoning for integration decisions
        self._init_integration_reasoning()

    def _init_integration_reasoning(self):
        """Initialize SPARC reasoning for integration logic"""
        self.integration_prompts = {
            "analyze": "Analyze the integration requirements and identify key challenges",
            "plan": "Create a detailed integration plan with steps and dependencies",
            "execute": "Execute the integration with proper error handling",
            "validate": "Validate the integration results and ensure data consistency",
            "optimize": "Optimize the integration for performance and reliability"
        }

    async def connect_platform(self, platform: IntegrationPlatform, client: Any):
        """Connect to a specific platform"""
        self.platform_clients[platform] = client
        logger.info(f"Connected to platform: {platform.value}")

    async def disconnect_platform(self, platform: IntegrationPlatform):
        """Disconnect from a specific platform"""
        if platform in self.platform_clients:
            # Cleanup if needed
            del self.platform_clients[platform]
            logger.info(f"Disconnected from platform: {platform.value}")

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler for specific event types"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def emit_event(self, event: IntegrationEvent):
        """Emit an integration event"""
        await self.event_queue.put(event)

        # Process handlers for this event type
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler for {event.event_type}: {e}")

    async def process_event_queue(self):
        """Process events from the queue"""
        while True:
            try:
                event = await self.event_queue.get()
                await self._process_integration_event(event)
                self.metrics.events_processed += 1
            except Exception as e:
                logger.error(f"Error processing event: {e}")
            await asyncio.sleep(0.01)  # Small delay to prevent CPU spinning

    @abstractmethod
    async def _process_integration_event(self, event: IntegrationEvent):
        """Process an integration event - must be implemented by subclasses"""
        pass

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        max_retries: int = 3,
        circuit_breaker_key: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Execute a function with retry logic and circuit breaker"""

        # Check circuit breaker if configured
        if circuit_breaker_key:
            if circuit_breaker_key not in self.circuit_breakers:
                self.circuit_breakers[circuit_breaker_key] = CircuitBreaker()

            breaker = self.circuit_breakers[circuit_breaker_key]
            if not breaker.can_execute():
                raise Exception(f"Circuit breaker is open for {circuit_breaker_key}")

        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                start_time = datetime.utcnow()
                result = await func(*args, **kwargs)

                # Record success
                latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                self.metrics.record_request(True, latency_ms)

                if circuit_breaker_key:
                    self.circuit_breakers[circuit_breaker_key].record_success()

                return result

            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

                # Record failure
                if circuit_breaker_key:
                    self.circuit_breakers[circuit_breaker_key].record_failure()

                if attempt < max_retries:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                    self.metrics.record_request(False, latency_ms)

        raise last_exception

    async def validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate data against a schema"""
        # Basic schema validation - can be enhanced with jsonschema
        for field, field_type in schema.items():
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False

            # Type checking can be enhanced
            if not isinstance(data[field], field_type):
                logger.error(f"Invalid type for field {field}: expected {field_type}, got {type(data[field])}")
                return False

        return True

    async def transform_data(
        self,
        data: Dict[str, Any],
        source_platform: IntegrationPlatform,
        target_platform: IntegrationPlatform
    ) -> Dict[str, Any]:
        """Transform data between platforms"""
        # Default implementation - override in subclasses for specific transformations
        transformed = data.copy()
        transformed["_source_platform"] = source_platform.value
        transformed["_target_platform"] = target_platform.value
        transformed["_transformed_at"] = datetime.utcnow().isoformat()

        return transformed

    async def sync_data(
        self,
        source_platform: IntegrationPlatform,
        target_platform: IntegrationPlatform,
        data: Dict[str, Any]
    ) -> TaskResult:
        """Synchronize data between platforms"""
        try:
            # Transform data for target platform
            transformed_data = await self.transform_data(data, source_platform, target_platform)

            # Get platform clients
            if target_platform not in self.platform_clients:
                return TaskResult(
                    success=False,
                    output=None,
                    error=f"Not connected to platform: {target_platform.value}"
                )

            target_client = self.platform_clients[target_platform]

            # Perform sync operation (platform-specific implementation needed)
            # This is a placeholder - actual implementation depends on platform
            result = await self._platform_specific_sync(target_client, transformed_data)

            return TaskResult(
                success=True,
                output=result,
                metadata={
                    "source_platform": source_platform.value,
                    "target_platform": target_platform.value,
                    "data_size": len(json.dumps(data))
                }
            )

        except Exception as e:
            logger.error(f"Error syncing data: {e}")
            return TaskResult(
                success=False,
                output=None,
                error=str(e)
            )

    async def _platform_specific_sync(self, client: Any, data: Dict[str, Any]) -> Any:
        """Platform-specific sync implementation - override in subclasses"""
        # Default implementation - just return the data
        return data

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on integration agent"""
        health_status = {
            "agent": self.config.name,
            "status": "healthy",
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": self.metrics.success_rate,
                "average_latency_ms": self.metrics.average_latency_ms,
                "events_processed": self.metrics.events_processed
            },
            "platforms": {},
            "circuit_breakers": {}
        }

        # Check platform connections
        for platform in self.platform_clients:
            health_status["platforms"][platform.value] = "connected"

        # Check circuit breakers
        for key, breaker in self.circuit_breakers.items():
            health_status["circuit_breakers"][key] = {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count
            }

        # Overall status
        if any(breaker.state == CircuitBreakerState.OPEN for breaker in self.circuit_breakers.values()):
            health_status["status"] = "degraded"

        return health_status

    async def cleanup(self):
        """Cleanup resources"""
        # Disconnect from all platforms
        for platform in list(self.platform_clients.keys()):
            await self.disconnect_platform(platform)

        # Clear event queue
        while not self.event_queue.empty():
            self.event_queue.get_nowait()

        await super().cleanup()