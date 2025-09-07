"""
API Versioning Support for FastAPI Application

Comprehensive versioning strategies:
- URL path versioning (e.g., /api/v1/, /api/v2/)
- Header-based versioning (e.g., Accept: application/vnd.api+json;version=1.0)
- Query parameter versioning (e.g., ?version=1.0)
- Content negotiation
- Backward compatibility management
"""

import functools
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class VersionStrategy(Enum):
    """API versioning strategies"""

    URL_PATH = "url_path"
    HEADER = "header"
    QUERY_PARAM = "query_param"
    CONTENT_TYPE = "content_type"


class APIVersion(BaseModel):
    """API version definition"""

    major: int
    minor: int
    patch: int = 0
    pre_release: Optional[str] = None
    build: Optional[str] = None

    def __str__(self):
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            version += f"-{self.pre_release}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __lt__(self, other):
        return (self.major, self.minor, self.patch) < (
            other.major,
            other.minor,
            other.patch,
        )

    def __le__(self, other):
        return (self.major, self.minor, self.patch) <= (
            other.major,
            other.minor,
            other.patch,
        )

    def is_compatible_with(self, other: "APIVersion") -> bool:
        """Check if this version is compatible with another"""
        # Major version must match for compatibility
        return self.major == other.major

    @classmethod
    def parse(cls, version_string: str) -> "APIVersion":
        """Parse version string into APIVersion object"""
        # Regular expression for semantic versioning
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.]+))?(?:\+([a-zA-Z0-9.]+))?$"
        match = re.match(pattern, version_string.strip())

        if not match:
            # Try simpler format (e.g., "1.0", "v2")
            simple_pattern = r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?$"
            match = re.match(simple_pattern, version_string.strip())

            if not match:
                raise ValueError(f"Invalid version format: {version_string}")

            major = int(match.group(1))
            minor = int(match.group(2)) if match.group(2) else 0
            patch = int(match.group(3)) if match.group(3) else 0
            return cls(major=major, minor=minor, patch=patch)

        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        pre_release = match.group(4)
        build = match.group(5)

        return cls(
            major=major, minor=minor, patch=patch, pre_release=pre_release, build=build
        )


class VersionedEndpoint:
    """Represents a versioned API endpoint"""

    def __init__(
        self,
        path: str,
        method: str,
        handler: Callable,
        version: APIVersion,
        deprecated: bool = False,
        sunset_date: Optional[datetime] = None,
    ):
        self.path = path
        self.method = method
        self.handler = handler
        self.version = version
        self.deprecated = deprecated
        self.sunset_date = sunset_date

    def matches(self, path: str, method: str, version: APIVersion) -> bool:
        """Check if this endpoint matches the request"""
        return (
            self.path == path
            and self.method.upper() == method.upper()
            and self.version.is_compatible_with(version)
        )


class VersionManager:
    """Manages API versions and routing"""

    def __init__(
        self,
        default_version: str = "1.0.0",
        strategy: VersionStrategy = VersionStrategy.URL_PATH,
        header_name: str = "X-API-Version",
        query_param_name: str = "version",
    ):
        self.default_version = APIVersion.parse(default_version)
        self.strategy = strategy
        self.header_name = header_name
        self.query_param_name = query_param_name
        self.versions: Dict[str, APIVersion] = {}
        self.endpoints: List[VersionedEndpoint] = []
        self.routers: Dict[str, APIRouter] = {}

    def register_version(self, version_string: str) -> APIVersion:
        """Register a new API version"""
        version = APIVersion.parse(version_string)
        self.versions[str(version)] = version
        logger.info(f"Registered API version: {version}")
        return version

    def create_versioned_router(
        self, version: str, prefix: str = None, **kwargs
    ) -> APIRouter:
        """Create a router for a specific API version"""
        api_version = self.register_version(version)

        if self.strategy == VersionStrategy.URL_PATH:
            prefix = prefix or f"/api/v{api_version.major}"

        router = APIRouter(prefix=prefix, **kwargs)
        self.routers[str(api_version)] = router

        # Add version info to router
        router.version = api_version

        return router

    def get_version_from_request(self, request: Request) -> APIVersion:
        """Extract API version from request based on strategy"""
        version = None

        if self.strategy == VersionStrategy.URL_PATH:
            # Extract version from URL path
            path_match = re.match(r"/api/v(\d+)", request.url.path)
            if path_match:
                version = f"{path_match.group(1)}.0.0"

        elif self.strategy == VersionStrategy.HEADER:
            # Get version from header
            version = request.headers.get(self.header_name)

        elif self.strategy == VersionStrategy.QUERY_PARAM:
            # Get version from query parameter
            version = request.query_params.get(self.query_param_name)

        elif self.strategy == VersionStrategy.CONTENT_TYPE:
            # Extract version from content type
            content_type = request.headers.get("Accept", "")
            version_match = re.search(r"version=([0-9.]+)", content_type)
            if version_match:
                version = version_match.group(1)

        # Parse and return version, or use default
        if version:
            try:
                return APIVersion.parse(version)
            except ValueError:
                logger.warning(f"Invalid version format: {version}")

        return self.default_version

    def version_deprecated(
        self, sunset_date: Optional[datetime] = None, message: str = None
    ):
        """Decorator to mark an endpoint as deprecated"""

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Get response object if available
                response = kwargs.get("response")
                if response:
                    response.headers["X-API-Deprecated"] = "true"
                    if sunset_date:
                        response.headers["X-API-Sunset"] = sunset_date.isoformat()
                    if message:
                        response.headers["X-API-Deprecation-Message"] = message

                # Log deprecation warning
                logger.warning(f"Deprecated endpoint called: {func.__name__}")

                return await func(*args, **kwargs)

            wrapper._deprecated = True
            wrapper._sunset_date = sunset_date
            return wrapper

        return decorator

    def validate_version(self, min_version: str = None, max_version: str = None):
        """Decorator to validate API version requirements"""

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                version = self.get_version_from_request(request)

                if min_version:
                    min_ver = APIVersion.parse(min_version)
                    if version < min_ver:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Minimum API version required: {min_version}",
                        )

                if max_version:
                    max_ver = APIVersion.parse(max_version)
                    if version > max_ver:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Maximum API version supported: {max_version}",
                        )

                return await func(request, *args, **kwargs)

            return wrapper

        return decorator


class VersionNegotiator:
    """Handles content negotiation for API versions"""

    def __init__(self, supported_versions: List[str]):
        self.supported_versions = [APIVersion.parse(v) for v in supported_versions]

    def negotiate(self, accept_header: str) -> Optional[APIVersion]:
        """Negotiate the best version based on Accept header"""
        # Parse accept header for version preferences
        preferences = self._parse_accept_header(accept_header)

        for pref_version, quality in preferences:
            for supported in self.supported_versions:
                if supported.is_compatible_with(pref_version):
                    return supported

        return None

    def _parse_accept_header(
        self, accept_header: str
    ) -> List[Tuple[APIVersion, float]]:
        """Parse Accept header for version preferences"""
        preferences = []

        # Extract version preferences from accept header
        parts = accept_header.split(",")
        for part in parts:
            part = part.strip()

            # Look for version in content type
            version_match = re.search(r"version=([0-9.]+)", part)
            if version_match:
                version_str = version_match.group(1)

                # Extract quality factor
                quality = 1.0
                q_match = re.search(r"q=([0-9.]+)", part)
                if q_match:
                    quality = float(q_match.group(1))

                try:
                    version = APIVersion.parse(version_str)
                    preferences.append((version, quality))
                except ValueError:
                    continue

        # Sort by quality factor (descending)
        preferences.sort(key=lambda x: x[1], reverse=True)

        return preferences


class VersionedResponse:
    """Wrapper for versioned API responses"""

    def __init__(self, version: APIVersion):
        self.version = version

    def transform_response(self, data: Any, target_version: APIVersion) -> Any:
        """Transform response data for target version compatibility"""
        if self.version == target_version:
            return data

        # Apply transformation rules based on version differences
        if target_version < self.version:
            return self._downgrade_response(data, target_version)
        else:
            return self._upgrade_response(data, target_version)

    def _downgrade_response(self, data: Any, target_version: APIVersion) -> Any:
        """Downgrade response for older API version"""
        # Implement backward compatibility transformations
        # This would be customized based on specific API changes

        # Example: Remove fields added in newer versions
        if isinstance(data, dict):
            # Version 2.0 added 'metadata' field
            if self.version.major >= 2 and target_version.major < 2:
                data = data.copy()
                data.pop("metadata", None)

            # Version 1.1 added 'timestamps' field
            if self.version.minor >= 1 and target_version.minor < 1:
                data = data.copy()
                data.pop("timestamps", None)

        return data

    def _upgrade_response(self, data: Any, target_version: APIVersion) -> Any:
        """Upgrade response for newer API version"""
        # Implement forward compatibility transformations
        # This would add default values for new fields

        if isinstance(data, dict):
            data = data.copy()

            # Version 2.0 expects 'metadata' field
            if self.version.major < 2 and target_version.major >= 2:
                data["metadata"] = {}

            # Version 1.1 expects 'timestamps' field
            if self.version.minor < 1 and target_version.minor >= 1:
                data["timestamps"] = {
                    "created": None,
                    "updated": None,
                }

        return data


class APIVersionMiddleware:
    """Middleware for API versioning"""

    def __init__(self, app, version_manager: VersionManager):
        self.app = app
        self.version_manager = version_manager

    async def __call__(self, request: Request, call_next):
        # Extract API version from request
        version = self.version_manager.get_version_from_request(request)

        # Store version in request state
        request.state.api_version = version

        # Process request
        response = await call_next(request)

        # Add version headers to response
        response.headers["X-API-Version"] = str(version)
        response.headers["X-API-Version-Strategy"] = self.version_manager.strategy.value

        # Add deprecation headers if applicable
        if version < self.version_manager.default_version:
            response.headers["X-API-Version-Status"] = "deprecated"
            response.headers["X-API-Latest-Version"] = str(
                self.version_manager.default_version
            )

        return response


def create_version_manager(
    default_version: str = "1.0.0",
    strategy: VersionStrategy = VersionStrategy.URL_PATH,
) -> VersionManager:
    """Create and configure version manager"""
    manager = VersionManager(default_version=default_version, strategy=strategy)

    # Register supported versions
    manager.register_version("1.0.0")
    manager.register_version("1.1.0")
    manager.register_version("2.0.0")

    return manager


# Dependency to get current API version
async def get_api_version(request: Request) -> APIVersion:
    """Get current API version from request"""
    if hasattr(request.state, "api_version"):
        return request.state.api_version

    # Fallback to parsing from request
    version_manager = create_version_manager()
    return version_manager.get_version_from_request(request)


# Example usage of versioned endpoints
def create_versioned_endpoints(app, version_manager: VersionManager):
    """Create versioned API endpoints"""

    # Version 1.0 router
    v1_router = version_manager.create_versioned_router("1.0.0", tags=["API v1"])

    @v1_router.get("/users")
    async def get_users_v1():
        return {"version": "1.0", "users": []}

    # Version 2.0 router with breaking changes
    v2_router = version_manager.create_versioned_router("2.0.0", tags=["API v2"])

    @v2_router.get("/users")
    async def get_users_v2():
        return {
            "version": "2.0",
            "data": {"users": []},
            "metadata": {"total": 0, "page": 1},
        }

    # Register routers with app
    app.include_router(v1_router)
    app.include_router(v2_router)

    return app
