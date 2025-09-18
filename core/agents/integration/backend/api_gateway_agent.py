"""
API Gateway Agent - Manages API endpoint creation, versioning, and documentation

This agent handles:
- Dynamic API endpoint creation and management
- API versioning and backward compatibility
- OpenAPI/Swagger documentation generation
- Request/response transformation
- Rate limiting and throttling
- API health monitoring
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field

from ..base_integration_agent import (
    BaseIntegrationAgent,
    IntegrationPlatform,
    IntegrationEvent,
    TaskResult
)
from core.agents.base_agent import AgentConfig

# Try to import SPARC if available
try:
    from core.sparc.reasoning_engine import SPARCContext
except ImportError:
    # SPARC not available, use placeholder
    class SPARCContext:
        pass

logger = logging.getLogger(__name__)


class APIVersion(Enum):
    """API version enumeration"""
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"


@dataclass
class APIEndpoint:
    """API endpoint definition"""
    path: str
    method: str
    version: APIVersion
    handler: Optional[Any] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    rate_limit: Optional[int] = None  # Requests per minute
    authentication_required: bool = True
    roles_allowed: List[str] = field(default_factory=list)
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None


@dataclass
class APIMetrics:
    """Metrics for API endpoints"""
    endpoint_path: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_latency_ms: float = 0.0
    last_accessed: Optional[datetime] = None
    error_rate: float = 0.0


class RateLimiter:
    """Simple rate limiter for API endpoints"""

    def __init__(self, max_requests: int, time_window: timedelta):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, List[datetime]] = {}

    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client"""
        now = datetime.utcnow()

        if client_id not in self.requests:
            self.requests[client_id] = []

        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < self.time_window
        ]

        # Check if under limit
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(now)
            return True

        return False


class APIGatewayAgent(BaseIntegrationAgent):
    """
    API Gateway Agent for managing API endpoints and documentation
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize API Gateway Agent"""
        if config is None:
            config = AgentConfig(
                name="APIGatewayAgent",
                system_prompt="""You are an API Gateway Agent responsible for:
                - Managing API endpoint creation and versioning
                - Generating OpenAPI documentation
                - Handling request/response transformations
                - Monitoring API health and performance
                - Implementing rate limiting and security
                """
            )
        super().__init__(config)

        # API management
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.routers: Dict[APIVersion, APIRouter] = {}
        self.endpoint_metrics: Dict[str, APIMetrics] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}

        # Documentation
        self.api_documentation: Dict[APIVersion, Dict[str, Any]] = {}

        # Initialize routers for each version
        for version in APIVersion:
            self.routers[version] = APIRouter(prefix=f"/api/{version.value}")

    async def register_endpoint(
        self,
        endpoint: APIEndpoint
    ) -> TaskResult:
        """Register a new API endpoint"""
        try:
            endpoint_key = f"{endpoint.version.value}:{endpoint.method}:{endpoint.path}"

            # Check if endpoint already exists
            if endpoint_key in self.endpoints:
                if not endpoint.deprecated:
                    logger.warning(f"Endpoint already exists: {endpoint_key}")

            # Store endpoint definition
            self.endpoints[endpoint_key] = endpoint

            # Initialize metrics
            self.endpoint_metrics[endpoint_key] = APIMetrics(endpoint_path=endpoint_key)

            # Setup rate limiter if specified
            if endpoint.rate_limit:
                self.rate_limiters[endpoint_key] = RateLimiter(
                    max_requests=endpoint.rate_limit,
                    time_window=timedelta(minutes=1)
                )

            # Update documentation
            await self._update_api_documentation(endpoint.version)

            logger.info(f"Registered endpoint: {endpoint_key}")

            return TaskResult(
                success=True,
                output={
                    "endpoint": endpoint_key,
                    "version": endpoint.version.value,
                    "path": endpoint.path,
                    "method": endpoint.method
                },
                metadata={"registered_at": datetime.utcnow().isoformat()}
            )

        except Exception as e:
            logger.error(f"Error registering endpoint: {e}")
            return TaskResult(
                success=False,
                output=None,
                error=str(e)
            )

    async def deprecate_endpoint(
        self,
        path: str,
        method: str,
        version: APIVersion,
        deprecation_message: str = ""
    ) -> TaskResult:
        """Mark an endpoint as deprecated"""
        try:
            endpoint_key = f"{version.value}:{method}:{path}"

            if endpoint_key not in self.endpoints:
                return TaskResult(
                    success=False,
                    output=None,
                    error=f"Endpoint not found: {endpoint_key}"
                )

            # Mark as deprecated
            self.endpoints[endpoint_key].deprecated = True

            # Emit deprecation event
            await self.emit_event(IntegrationEvent(
                event_id=f"deprecation_{endpoint_key}",
                event_type="api_endpoint_deprecated",
                source_platform=IntegrationPlatform.BACKEND,
                payload={
                    "endpoint": endpoint_key,
                    "message": deprecation_message,
                    "deprecated_at": datetime.utcnow().isoformat()
                }
            ))

            logger.info(f"Deprecated endpoint: {endpoint_key}")

            return TaskResult(
                success=True,
                output={"endpoint": endpoint_key, "deprecated": True}
            )

        except Exception as e:
            logger.error(f"Error deprecating endpoint: {e}")
            return TaskResult(
                success=False,
                output=None,
                error=str(e)
            )

    async def transform_request(
        self,
        request_data: Dict[str, Any],
        source_version: APIVersion,
        target_version: APIVersion
    ) -> Dict[str, Any]:
        """Transform request between API versions"""
        # Use SPARC reasoning for complex transformations
        context = SPARCContext(
            situation=f"Transform request from {source_version.value} to {target_version.value}",
            parameters={"request_data": request_data},
            actions=["analyze_differences", "map_fields", "apply_transformations"],
            results={},
            conclusions=[]
        )

        # Default transformation (can be enhanced with version-specific logic)
        transformed = request_data.copy()

        # Version-specific transformations
        if source_version == APIVersion.V1 and target_version == APIVersion.V2:
            # Example: V1 to V2 transformations
            if "user_id" in transformed:
                transformed["userId"] = transformed.pop("user_id")  # camelCase in V2

        elif source_version == APIVersion.V2 and target_version == APIVersion.V3:
            # Example: V2 to V3 transformations
            if "userId" in transformed:
                transformed["user"] = {"id": transformed.pop("userId")}  # Nested in V3

        transformed["_api_version"] = target_version.value
        transformed["_transformed_from"] = source_version.value

        return transformed

    async def validate_request(
        self,
        endpoint_key: str,
        request_data: Dict[str, Any],
        client_id: str
    ) -> Tuple[bool, Optional[str]]:
        """Validate incoming request"""
        # Check if endpoint exists
        if endpoint_key not in self.endpoints:
            return False, "Endpoint not found"

        endpoint = self.endpoints[endpoint_key]

        # Check if deprecated
        if endpoint.deprecated:
            logger.warning(f"Deprecated endpoint accessed: {endpoint_key}")

        # Check rate limit
        if endpoint_key in self.rate_limiters:
            if not self.rate_limiters[endpoint_key].is_allowed(client_id):
                return False, "Rate limit exceeded"

        # Validate schema if defined
        if endpoint.request_schema:
            if not await self.validate_schema(request_data, endpoint.request_schema):
                return False, "Schema validation failed"

        return True, None

    async def record_request_metrics(
        self,
        endpoint_key: str,
        success: bool,
        latency_ms: float
    ):
        """Record metrics for an API request"""
        if endpoint_key not in self.endpoint_metrics:
            self.endpoint_metrics[endpoint_key] = APIMetrics(endpoint_path=endpoint_key)

        metrics = self.endpoint_metrics[endpoint_key]
        metrics.total_requests += 1

        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1

        # Update average latency
        metrics.average_latency_ms = (
            (metrics.average_latency_ms * (metrics.total_requests - 1) + latency_ms)
            / metrics.total_requests
        )

        metrics.last_accessed = datetime.utcnow()

        # Calculate error rate
        if metrics.total_requests > 0:
            metrics.error_rate = metrics.failed_requests / metrics.total_requests

    async def generate_openapi_spec(
        self,
        version: APIVersion
    ) -> Dict[str, Any]:
        """Generate OpenAPI specification for API version"""
        endpoints_for_version = {
            key: endpoint for key, endpoint in self.endpoints.items()
            if endpoint.version == version
        }

        paths = {}
        for endpoint_key, endpoint in endpoints_for_version.items():
            path = endpoint.path
            method = endpoint.method.lower()

            if path not in paths:
                paths[path] = {}

            paths[path][method] = {
                "summary": endpoint.description,
                "tags": endpoint.tags,
                "deprecated": endpoint.deprecated,
                "security": [{"bearerAuth": []}] if endpoint.authentication_required else [],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": endpoint.response_schema or {"type": "object"}
                            }
                        }
                    },
                    "400": {"description": "Bad request"},
                    "401": {"description": "Unauthorized"},
                    "429": {"description": "Rate limit exceeded"},
                    "500": {"description": "Internal server error"}
                }
            }

            if endpoint.request_schema:
                paths[path][method]["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": endpoint.request_schema
                        }
                    }
                }

        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": f"ToolboxAI API {version.value}",
                "version": version.value,
                "description": "Educational Platform API"
            },
            "servers": [
                {"url": f"http://127.0.0.1:8008/api/{version.value}"}
            ],
            "paths": paths,
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            }
        }

        return spec

    async def _update_api_documentation(self, version: APIVersion):
        """Update API documentation for a version"""
        self.api_documentation[version] = await self.generate_openapi_spec(version)

    async def _process_integration_event(self, event: IntegrationEvent):
        """Process integration events for API Gateway"""
        if event.event_type == "endpoint_creation_request":
            # Handle dynamic endpoint creation
            endpoint_data = event.payload
            endpoint = APIEndpoint(
                path=endpoint_data["path"],
                method=endpoint_data["method"],
                version=APIVersion[endpoint_data["version"]],
                description=endpoint_data.get("description", ""),
                tags=endpoint_data.get("tags", []),
                rate_limit=endpoint_data.get("rate_limit"),
                authentication_required=endpoint_data.get("authentication_required", True)
            )
            await self.register_endpoint(endpoint)

        elif event.event_type == "endpoint_metrics_request":
            # Return metrics for specific endpoint
            endpoint_key = event.payload.get("endpoint_key")
            if endpoint_key in self.endpoint_metrics:
                metrics = self.endpoint_metrics[endpoint_key]
                await self.emit_event(IntegrationEvent(
                    event_id=f"metrics_response_{event.event_id}",
                    event_type="endpoint_metrics_response",
                    source_platform=IntegrationPlatform.BACKEND,
                    payload={
                        "endpoint": endpoint_key,
                        "metrics": {
                            "total_requests": metrics.total_requests,
                            "success_rate": (
                                metrics.successful_requests / metrics.total_requests
                                if metrics.total_requests > 0 else 0
                            ),
                            "average_latency_ms": metrics.average_latency_ms,
                            "error_rate": metrics.error_rate
                        }
                    },
                    correlation_id=event.correlation_id
                ))

    async def monitor_api_health(self) -> Dict[str, Any]:
        """Monitor overall API health"""
        total_endpoints = len(self.endpoints)
        active_endpoints = sum(1 for e in self.endpoints.values() if not e.deprecated)
        deprecated_endpoints = total_endpoints - active_endpoints

        # Calculate aggregate metrics
        total_requests = sum(m.total_requests for m in self.endpoint_metrics.values())
        total_errors = sum(m.failed_requests for m in self.endpoint_metrics.values())
        overall_error_rate = total_errors / total_requests if total_requests > 0 else 0

        # Find problematic endpoints
        high_error_endpoints = [
            key for key, metrics in self.endpoint_metrics.items()
            if metrics.error_rate > 0.1  # More than 10% error rate
        ]

        slow_endpoints = [
            key for key, metrics in self.endpoint_metrics.items()
            if metrics.average_latency_ms > 1000  # More than 1 second
        ]

        health = {
            "status": "healthy" if overall_error_rate < 0.05 else "degraded",
            "endpoints": {
                "total": total_endpoints,
                "active": active_endpoints,
                "deprecated": deprecated_endpoints
            },
            "metrics": {
                "total_requests": total_requests,
                "overall_error_rate": overall_error_rate,
                "high_error_endpoints": high_error_endpoints,
                "slow_endpoints": slow_endpoints
            },
            "versions": list(self.api_documentation.keys())
        }

        return health

    async def execute_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskResult:
        """Execute API Gateway specific tasks"""
        if task == "register_endpoint":
            return await self.register_endpoint(context["endpoint"])
        elif task == "deprecate_endpoint":
            return await self.deprecate_endpoint(
                path=context["path"],
                method=context["method"],
                version=context["version"],
                deprecation_message=context.get("message", "")
            )
        elif task == "generate_documentation":
            spec = await self.generate_openapi_spec(context["version"])
            return TaskResult(success=True, output=spec)
        elif task == "monitor_health":
            health = await self.monitor_api_health()
            return TaskResult(success=True, output=health)
        else:
            return await super().execute_task(task, context)