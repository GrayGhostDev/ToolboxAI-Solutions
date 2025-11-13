"""
Circuit Breaker Pattern Implementation for FastAPI

Provides resilience and fault tolerance for service calls by preventing
cascading failures and giving failing services time to recover.

Based on production best practices for 2025 with async support.
"""

import asyncio
import logging
import random
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Service is failing, requests are blocked
    HALF_OPEN = "half_open"  # Testing if service has recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""

    def __init__(self, message: str, circuit_name: str, wait_time: float):
        super().__init__(message)
        self.circuit_name = circuit_name
        self.wait_time = wait_time


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""

    # Failure thresholds
    failure_threshold: int = 5  # Number of failures before opening
    failure_rate_threshold: float = 0.5  # Failure rate before opening (50%)
    success_threshold: int = 2  # Successes needed in half-open to close

    # Timing
    timeout: float = 10.0  # Timeout for each call (seconds)
    reset_timeout: float = 30.0  # Time before trying half-open (seconds)

    # Window for rate calculation
    window_size: int = 10  # Number of recent calls to track

    # Behavior
    expected_exceptions: tuple = (Exception,)  # Exceptions that trigger the breaker
    excluded_exceptions: tuple = ()  # Exceptions that don't trigger the breaker
    fallback: Callable | None = None  # Fallback function when open

    # Monitoring
    enable_monitoring: bool = True
    enable_metrics: bool = True

    # Advanced features
    enable_jitter: bool = True  # Add random jitter to prevent thundering herd
    max_jitter: float = 5.0  # Maximum jitter in seconds
    enable_gradual_recovery: bool = True  # Gradually increase traffic in half-open


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring"""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    fallback_calls: int = 0

    state_transitions: list[dict[str, Any]] = field(default_factory=list)
    recent_calls: deque = field(default_factory=lambda: deque(maxlen=100))

    last_failure_time: datetime | None = None
    last_success_time: datetime | None = None
    circuit_opened_at: datetime | None = None

    def add_call(self, success: bool, duration: float, error: Exception | None = None):
        """Record a call"""
        self.total_calls += 1
        call_record = {
            "timestamp": datetime.now(),
            "success": success,
            "duration": duration,
            "error": str(error) if error else None,
        }
        self.recent_calls.append(call_record)

        if success:
            self.successful_calls += 1
            self.last_success_time = datetime.now()
        else:
            self.failed_calls += 1
            self.last_failure_time = datetime.now()

    def get_failure_rate(self, window: int = 10) -> float:
        """Calculate recent failure rate"""
        if not self.recent_calls:
            return 0.0

        recent = list(self.recent_calls)[-window:]
        if not recent:
            return 0.0

        failures = sum(1 for call in recent if not call["success"])
        return failures / len(recent)

    def get_avg_response_time(self, window: int = 10) -> float:
        """Calculate average response time"""
        if not self.recent_calls:
            return 0.0

        recent = list(self.recent_calls)[-window:]
        if not recent:
            return 0.0

        durations = [call["duration"] for call in recent if call["duration"] is not None]
        return sum(durations) / len(durations) if durations else 0.0


class CircuitBreaker:
    """
    Circuit Breaker implementation with async support

    Usage:
        breaker = CircuitBreaker("api_service", failure_threshold=5)

        @breaker
        async def call_api():
            return await external_api_call()
    """

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.metrics = CircuitBreakerMetrics()

        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

        logger.info(f"Circuit breaker '{name}' initialized with state: {self.state.value}")

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""

        # Check if circuit is open
        if await self._should_reject():
            self.metrics.rejected_calls += 1

            # Try fallback if available
            if self.config.fallback:
                self.metrics.fallback_calls += 1
                return await self._execute_fallback(*args, **kwargs)

            # Calculate wait time with jitter
            wait_time = self._get_wait_time()
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is {self.state.value}", self.name, wait_time
            )

        # Execute the function
        start_time = time.time()
        try:
            # Add timeout
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
            else:
                result = func(*args, **kwargs)

            duration = time.time() - start_time
            await self._on_success(duration)
            return result

        except self.config.excluded_exceptions:
            # Don't count excluded exceptions as failures
            duration = time.time() - start_time
            self.metrics.add_call(True, duration)
            raise

        except self.config.expected_exceptions as e:
            duration = time.time() - start_time
            await self._on_failure(duration, e)
            raise

    async def _should_reject(self) -> bool:
        """Check if request should be rejected"""
        async with self._lock:
            if self.state == CircuitBreakerState.CLOSED:
                return False

            if self.state == CircuitBreakerState.OPEN:
                # Check if enough time has passed to try half-open
                if (
                    self._last_failure_time
                    and time.time() - self._last_failure_time >= self.config.reset_timeout
                ):
                    await self._transition_to_half_open()
                    return False
                return True

            if self.state == CircuitBreakerState.HALF_OPEN:
                # In gradual recovery, allow some requests through
                if self.config.enable_gradual_recovery:
                    # Allow progressively more traffic
                    allow_probability = min(0.1 * (self._success_count + 1), 1.0)
                    return random.random() > allow_probability
                # Otherwise, allow one request at a time
                return self._half_open_calls > 0

        return False

    async def _on_success(self, duration: float):
        """Handle successful call"""
        async with self._lock:
            self.metrics.add_call(True, duration)

            if self.state == CircuitBreakerState.HALF_OPEN:
                self._success_count += 1
                self._half_open_calls = max(0, self._half_open_calls - 1)

                if self._success_count >= self.config.success_threshold:
                    await self._transition_to_closed()

            elif self.state == CircuitBreakerState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    async def _on_failure(self, duration: float, error: Exception):
        """Handle failed call"""
        async with self._lock:
            self.metrics.add_call(False, duration, error)
            self._last_failure_time = time.time()

            if self.state == CircuitBreakerState.CLOSED:
                self._failure_count += 1

                # Check both absolute threshold and failure rate
                failure_rate = self.metrics.get_failure_rate(self.config.window_size)

                if (
                    self._failure_count >= self.config.failure_threshold
                    or failure_rate >= self.config.failure_rate_threshold
                ):
                    await self._transition_to_open()

            elif self.state == CircuitBreakerState.HALF_OPEN:
                # Single failure in half-open reopens the circuit
                await self._transition_to_open()

    async def _transition_to_open(self):
        """Transition to open state"""
        self.state = CircuitBreakerState.OPEN
        self._failure_count = 0
        self._success_count = 0
        self.metrics.circuit_opened_at = datetime.now()

        self.metrics.state_transitions.append(
            {
                "timestamp": datetime.now(),
                "from_state": self.state.value,
                "to_state": CircuitBreakerState.OPEN.value,
                "reason": "failure_threshold_exceeded",
            }
        )

        logger.warning(f"Circuit breaker '{self.name}' opened due to failures")

    async def _transition_to_half_open(self):
        """Transition to half-open state"""
        self.state = CircuitBreakerState.HALF_OPEN
        self._success_count = 0
        self._failure_count = 0
        self._half_open_calls = 0

        self.metrics.state_transitions.append(
            {
                "timestamp": datetime.now(),
                "from_state": CircuitBreakerState.OPEN.value,
                "to_state": CircuitBreakerState.HALF_OPEN.value,
                "reason": "testing_recovery",
            }
        )

        logger.info(f"Circuit breaker '{self.name}' half-opened for testing")

    async def _transition_to_closed(self):
        """Transition to closed state"""
        self.state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0

        self.metrics.state_transitions.append(
            {
                "timestamp": datetime.now(),
                "from_state": self.state.value,
                "to_state": CircuitBreakerState.CLOSED.value,
                "reason": "service_recovered",
            }
        )

        logger.info(f"Circuit breaker '{self.name}' closed - service recovered")

    def _get_wait_time(self) -> float:
        """Calculate wait time with optional jitter"""
        base_wait = self.config.reset_timeout

        if self.config.enable_jitter:
            jitter = random.uniform(0, min(self.config.max_jitter, base_wait * 0.1))
            return base_wait + jitter

        return base_wait

    async def _execute_fallback(self, *args, **kwargs) -> Any:
        """Execute fallback function"""
        if self.config.fallback:
            if asyncio.iscoroutinefunction(self.config.fallback):
                return await self.config.fallback(*args, **kwargs)
            return self.config.fallback(*args, **kwargs)
        return None

    def __call__(self, func: Callable) -> Callable:
        """Decorator usage"""

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(self.call(func, *args, **kwargs))

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    async def reset(self):
        """Manually reset the circuit breaker"""
        async with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' manually reset")

    def get_status(self) -> dict[str, Any]:
        """Get current status and metrics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "metrics": {
                "total_calls": self.metrics.total_calls,
                "successful_calls": self.metrics.successful_calls,
                "failed_calls": self.metrics.failed_calls,
                "rejected_calls": self.metrics.rejected_calls,
                "fallback_calls": self.metrics.fallback_calls,
                "failure_rate": self.metrics.get_failure_rate(),
                "avg_response_time": self.metrics.get_avg_response_time(),
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "reset_timeout": self.config.reset_timeout,
                "timeout": self.config.timeout,
            },
            "last_failure": (
                self.metrics.last_failure_time.isoformat()
                if self.metrics.last_failure_time
                else None
            ),
            "circuit_opened_at": (
                self.metrics.circuit_opened_at.isoformat()
                if self.metrics.circuit_opened_at
                else None
            ),
        }


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
    """Get or create a circuit breaker instance"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def circuit_breaker(name: str | None = None, **config_kwargs) -> Callable:
    """
    Decorator for applying circuit breaker to functions

    Usage:
        @circuit_breaker("external_api", failure_threshold=3)
        async def call_external_api():
            return await make_request()
    """

    def decorator(func: Callable) -> Callable:
        breaker_name = name or func.__name__
        config = CircuitBreakerConfig(**config_kwargs) if config_kwargs else None
        breaker = get_circuit_breaker(breaker_name, config)
        return breaker(func)

    return decorator


async def get_all_circuit_breakers_status() -> dict[str, Any]:
    """Get status of all circuit breakers"""
    return {name: breaker.get_status() for name, breaker in _circuit_breakers.items()}
