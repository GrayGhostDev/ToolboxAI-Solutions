"""
Security Middleware for FastAPI Application

Comprehensive security features including:
- Rate limiting with sliding window
- DDoS protection
- Request size limiting
- Secrets redaction in logs
- API key validation
- Circuit breaker for external services
"""

import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import uuid4

import redis
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from .rate_limit_manager import get_rate_limit_manager, RateLimitConfig, RateLimitMode

logger = logging.getLogger(__name__)

# Constants
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_RATE_LIMIT = 100  # requests per minute
BURST_RATE_LIMIT = 200  # burst allowance
SLIDING_WINDOW_SECONDS = 60
CIRCUIT_BREAKER_THRESHOLD = 5  # failures before opening
CIRCUIT_BREAKER_TIMEOUT = 30  # seconds to wait before half-open


class RateLimitExceeded(HTTPException):
    """Rate limit exceeded exception"""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""

    requests_per_minute: int = DEFAULT_RATE_LIMIT
    burst_limit: int = BURST_RATE_LIMIT
    window_seconds: int = SLIDING_WINDOW_SECONDS
    exclude_paths: Set[str] = field(default_factory=lambda: {"/health", "/metrics"})
    by_endpoint: Dict[str, int] = field(default_factory=dict)


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = CIRCUIT_BREAKER_THRESHOLD
    timeout_seconds: int = CIRCUIT_BREAKER_TIMEOUT
    excluded_services: Set[str] = field(default_factory=set)


class RateLimiter:
    """Rate limiter that uses the centralized rate limit manager"""

    def __init__(
        self, config: RateLimitConfig, redis_client: Optional[redis.Redis] = None
    ):
        self.config = config
        self.redis_client = redis_client
        # Use centralized manager
        self.manager = get_rate_limit_manager()
        self.cleanup_task: Optional[asyncio.Task] = None

    async def check_rate_limit(
        self, identifier: str, endpoint: str = ""
    ) -> Tuple[bool, int]:
        """
        Check if request is within rate limit
        Returns: (allowed, retry_after_seconds)
        """
        limit = self.config.by_endpoint.get(endpoint, self.config.requests_per_minute)
        
        return await self.manager.check_rate_limit(
            identifier=identifier,
            endpoint=endpoint,
            max_requests=limit,
            window_seconds=self.config.window_seconds,
            source="middleware"
        )

    async def start_cleanup(self):
        """Start periodic cleanup of old entries"""
        await self.manager.start_cleanup()

    async def stop_cleanup(self):
        """Stop cleanup task"""
        await self.manager.stop_cleanup()


class CircuitBreaker:
    """Circuit breaker for external service calls"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.circuits: Dict[str, Dict[str, Any]] = {}

    def _get_circuit(self, service_name: str) -> Dict[str, Any]:
        """Get or create circuit for service"""
        if service_name not in self.circuits:
            self.circuits[service_name] = {
                "state": CircuitState.CLOSED,
                "failures": 0,
                "last_failure": None,
                "last_success": None,
            }
        return self.circuits[service_name]

    async def call(self, service_name: str, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if service_name in self.config.excluded_services:
            return await func(*args, **kwargs)

        circuit = self._get_circuit(service_name)

        # Check circuit state
        if circuit["state"] == CircuitState.OPEN:
            if self._should_attempt_reset(circuit):
                circuit["state"] = CircuitState.HALF_OPEN
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Service {service_name} is temporarily unavailable",
                )

        try:
            # Execute function
            result = await func(*args, **kwargs)

            # Success - reset circuit
            circuit["failures"] = 0
            circuit["last_success"] = datetime.now()
            if circuit["state"] == CircuitState.HALF_OPEN:
                circuit["state"] = CircuitState.CLOSED
                logger.info(f"Circuit breaker for {service_name} closed")

            return result

        except Exception as e:
            # Failure - update circuit
            circuit["failures"] += 1
            circuit["last_failure"] = datetime.now()

            if circuit["failures"] >= self.config.failure_threshold:
                circuit["state"] = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker for {service_name} opened after {circuit['failures']} failures"
                )

            raise e

    def _should_attempt_reset(self, circuit: Dict[str, Any]) -> bool:
        """Check if we should attempt to reset the circuit"""
        if not circuit["last_failure"]:
            return True

        time_since_failure = (datetime.now() - circuit["last_failure"]).total_seconds()
        return time_since_failure >= self.config.timeout_seconds

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for all services"""
        return {
            service: {
                "state": circuit["state"].value,
                "failures": circuit["failures"],
                "last_failure": (
                    circuit["last_failure"].isoformat()
                    if circuit["last_failure"]
                    else None
                ),
                "last_success": (
                    circuit["last_success"].isoformat()
                    if circuit["last_success"]
                    else None
                ),
            }
            for service, circuit in self.circuits.items()
        }


class SecretRedactor:
    """Redacts sensitive information from logs and responses"""

    # Patterns to redact
    SENSITIVE_PATTERNS = [
        r"api[_-]?key",
        r"secret",
        r"password",
        r"token",
        r"auth",
        r"credential",
        r"private[_-]?key",
    ]

    @staticmethod
    def redact_dict(data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
        """Recursively redact sensitive values from dictionary"""
        if depth > 10:  # Prevent infinite recursion
            return data

        redacted = {}
        for key, value in data.items():
            # Check if key contains sensitive pattern
            is_sensitive = any(
                pattern in key.lower() for pattern in SecretRedactor.SENSITIVE_PATTERNS
            )

            if is_sensitive:
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = SecretRedactor.redact_dict(value, depth + 1)
            elif isinstance(value, list):
                redacted[key] = SecretRedactor.redact_list(value, depth + 1)
            elif isinstance(value, str) and len(value) > 20:
                # Check if value looks like a secret (long random string)
                if SecretRedactor._looks_like_secret(value):
                    redacted[key] = "***REDACTED***"
                else:
                    redacted[key] = value
            else:
                redacted[key] = value

        return redacted

    @staticmethod
    def redact_list(data: List[Any], depth: int = 0) -> List[Any]:
        """Recursively redact sensitive values from list"""
        if depth > 10:
            return data

        redacted = []
        for item in data:
            if isinstance(item, dict):
                redacted.append(SecretRedactor.redact_dict(item, depth + 1))
            elif isinstance(item, list):
                redacted.append(SecretRedactor.redact_list(item, depth + 1))
            else:
                redacted.append(item)

        return redacted

    @staticmethod
    def _looks_like_secret(value: str) -> bool:
        """Check if string looks like a secret"""
        # Long string with high entropy
        if len(value) < 20:
            return False

        # Check for common secret patterns
        secret_prefixes = ["sk_", "pk_", "api_", "key_", "token_", "bearer "]
        return any(value.lower().startswith(prefix) for prefix in secret_prefixes)

    @staticmethod
    def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """Redact sensitive headers"""
        sensitive_headers = {
            "authorization",
            "x-api-key",
            "x-auth-token",
            "cookie",
            "set-cookie",
            "x-csrf-token",
        }

        redacted = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                redacted[key] = "***REDACTED***"
            else:
                redacted[key] = value

        return redacted


class SecurityMiddleware(BaseHTTPMiddleware):
    """Main security middleware combining all security features"""

    def __init__(
        self,
        app: ASGIApp,
        rate_limit_config: Optional[RateLimitConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        redis_client: Optional[redis.Redis] = None,
        enable_request_id: bool = True,
        max_request_size: int = MAX_REQUEST_SIZE,
    ):
        super().__init__(app)
        
        # Convert old config to new format if needed
        if rate_limit_config is None:
            from .rate_limit_manager import RateLimitConfig as NewRateLimitConfig
            rate_limit_config = NewRateLimitConfig()
        
        self.rate_limiter = RateLimiter(
            rate_limit_config, redis_client
        )
        self.circuit_breaker = CircuitBreaker(
            circuit_breaker_config or CircuitBreakerConfig()
        )
        self.secret_redactor = SecretRedactor()
        self.enable_request_id = enable_request_id
        self.max_request_size = max_request_size

        # Start cleanup task
        asyncio.create_task(self.rate_limiter.start_cleanup())

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with security checks"""
        start_time = time.time()

        # Add request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        if self.enable_request_id:
            request.state.request_id = request_id

        # Check request size
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > self.max_request_size:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request body too large"},
                )

        # Get client identifier
        client_id = self._get_client_identifier(request)

        # Skip rate limiting for OPTIONS requests (CORS preflight)
        # Check if path is excluded from rate limiting
        if (request.method != "OPTIONS" and 
            request.url.path not in self.rate_limiter.config.exclude_paths):
            # Check rate limit
            allowed, retry_after = await self.rate_limiter.check_rate_limit(
                client_id, request.url.path
            )

            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"},
                    headers={"Retry-After": str(retry_after)},
                )

        # Log request (with redacted sensitive data)
        self._log_request(request, request_id)

        try:
            # Process request
            response = await call_next(request)

            # Add security headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

            # Add timing header
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            logger.error(f"Request {request_id} failed: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error", "request_id": request_id},
            )

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier for rate limiting"""
        # Try to get authenticated user ID
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"

        # Try to get API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Hash API key for privacy
            return f"api:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Safely handle X-Forwarded-For header (SonarQube: S2259)
            ip_parts = forwarded_for.split(",")
            if ip_parts:
                client_ip = ip_parts[0].strip()

        return f"ip:{client_ip}"

    def _log_request(self, request: Request, request_id: str):
        """Log request with redacted sensitive information"""
        # Redact sensitive headers
        safe_headers = self.secret_redactor.redact_headers(dict(request.headers))

        logger.info(
            f"Request {request_id}: {request.method} {request.url.path} "
            f"from {self._get_client_identifier(request)}"
        )
        logger.debug(f"Request headers: {safe_headers}")


# Convenience function to create middleware with default config
def create_security_middleware(
    app: ASGIApp, redis_url: Optional[str] = None
) -> SecurityMiddleware:
    """Create security middleware with default configuration"""
    redis_client = None
    if redis_url:
        try:
            redis_client = redis.from_url(redis_url)
            redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed, using local rate limiting: {e}")

    return SecurityMiddleware(
        app=app,
        rate_limit_config=RateLimitConfig(
            requests_per_minute=100,
            burst_limit=200,
            by_endpoint={
                "/generate_content": 30,  # More restrictive for expensive operations
                "/api/v1/agent/execute": 20,
            },
        ),
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=5,
            timeout_seconds=30,
            excluded_services={"health", "metrics"},
        ),
        redis_client=redis_client,
        enable_request_id=True,
        max_request_size=10 * 1024 * 1024,  # 10MB
    )
