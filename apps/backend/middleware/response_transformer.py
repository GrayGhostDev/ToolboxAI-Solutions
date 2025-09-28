"""
Response Transformer Middleware
Handles response formatting, versioning, error standardization, and caching
Following 2025 FastAPI middleware patterns and Prometheus metrics integration
"""

import gzip
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import urlparse

from fastapi import HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from apps.backend.core.config import settings
from apps.backend.core.metrics import metrics

logger = logging.getLogger(__name__)


class ResponseFormat:
    """Standard response format for API responses"""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        metadata: Optional[Dict[str, Any]] = None,
        status_code: int = 200
    ) -> Dict[str, Any]:
        """Format successful response"""
        response = {
            "status": "success",
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metadata:
            response["metadata"] = metadata

        return response

    @staticmethod
    def error(
        error: str,
        details: Optional[Any] = None,
        status_code: int = 400,
        error_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format error response"""
        response = {
            "status": "error",
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if details:
            response["details"] = details

        if error_code:
            response["error_code"] = error_code

        return response

    @staticmethod
    def paginated(
        data: List[Any],
        page: int,
        limit: int,
        total: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format paginated response"""
        total_pages = (total + limit - 1) // limit if limit > 0 else 1

        response = {
            "status": "success",
            "data": data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metadata:
            response["metadata"] = metadata

        return response


class CacheManager:
    """Manages response caching headers"""

    CACHE_CONTROL_DEFAULTS = {
        "GET": {
            "/api/*/health": "no-cache",
            "/api/*/metrics": "no-cache",
            "/api/*/users/*": "private, max-age=300",
            "/api/*/content/*": "public, max-age=3600",
            "/api/*/static/*": "public, max-age=86400",
        },
        "POST": "no-store",
        "PUT": "no-store",
        "DELETE": "no-store",
        "PATCH": "no-store",
    }

    @classmethod
    def get_cache_headers(cls, method: str, path: str) -> Dict[str, str]:
        """Get appropriate cache headers for request"""
        headers = {}

        # Get method-specific defaults
        if method in cls.CACHE_CONTROL_DEFAULTS:
            if isinstance(cls.CACHE_CONTROL_DEFAULTS[method], dict):
                # Check path patterns
                for pattern, control in cls.CACHE_CONTROL_DEFAULTS[method].items():
                    if cls._matches_pattern(path, pattern):
                        headers["Cache-Control"] = control
                        break
            else:
                headers["Cache-Control"] = cls.CACHE_CONTROL_DEFAULTS[method]

        # Add ETag if not present
        if "Cache-Control" in headers and "no-store" not in headers["Cache-Control"]:
            headers["Vary"] = "Accept-Encoding"

        return headers

    @staticmethod
    def _matches_pattern(path: str, pattern: str) -> bool:
        """Check if path matches pattern with wildcards"""
        import re
        regex_pattern = pattern.replace("*", ".*")
        return bool(re.match(regex_pattern, path))

    @staticmethod
    def generate_etag(content: bytes) -> str:
        """Generate ETag for content"""
        import hashlib
        return f'W/"{hashlib.md5(content).hexdigest()}"'


class CompressionHandler:
    """Handles response compression"""

    MIN_COMPRESS_SIZE = 1024  # 1KB
    COMPRESSIBLE_TYPES = {
        "application/json",
        "text/html",
        "text/plain",
        "text/css",
        "text/javascript",
        "application/javascript",
        "application/xml",
        "text/xml",
    }

    @classmethod
    def should_compress(
        cls,
        content_type: str,
        content_length: int,
        accept_encoding: str
    ) -> bool:
        """Check if response should be compressed"""
        # Check if client accepts gzip
        if "gzip" not in accept_encoding:
            return False

        # Check content type
        base_type = content_type.split(";")[0].strip()
        if base_type not in cls.COMPRESSIBLE_TYPES:
            return False

        # Check content size
        if content_length < cls.MIN_COMPRESS_SIZE:
            return False

        return True

    @staticmethod
    def compress_content(content: bytes) -> bytes:
        """Compress content using gzip"""
        return gzip.compress(content, compresslevel=6)


class VersionTransformer:
    """Handles version-specific response transformations"""

    def __init__(self):
        self.transformations = {
            "v1": self._transform_v1,
            "v2": self._transform_v2,
            "v3": self._transform_v3,
        }

    def transform(self, data: Any, version: str) -> Any:
        """Transform data based on API version"""
        if version in self.transformations:
            return self.transformations[version](data)
        return data

    def _transform_v1(self, data: Any) -> Any:
        """Transform for API v1 (legacy format)"""
        if isinstance(data, dict):
            # V1 uses snake_case for all fields
            return self._to_snake_case(data)
        return data

    def _transform_v2(self, data: Any) -> Any:
        """Transform for API v2"""
        # V2 uses camelCase for response fields
        if isinstance(data, dict):
            return self._to_camel_case(data)
        return data

    def _transform_v3(self, data: Any) -> Any:
        """Transform for API v3 (current)"""
        # V3 uses the standard format
        return data

    def _to_snake_case(self, data: Any) -> Any:
        """Convert dict keys to snake_case"""
        if isinstance(data, dict):
            return {
                self._camel_to_snake(k): self._to_snake_case(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._to_snake_case(item) for item in data]
        return data

    def _to_camel_case(self, data: Any) -> Any:
        """Convert dict keys to camelCase"""
        if isinstance(data, dict):
            return {
                self._snake_to_camel(k): self._to_camel_case(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._to_camel_case(item) for item in data]
        return data

    @staticmethod
    def _camel_to_snake(name: str) -> str:
        """Convert camelCase to snake_case"""
        import re
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    @staticmethod
    def _snake_to_camel(name: str) -> str:
        """Convert snake_case to camelCase"""
        components = name.split("_")
        return components[0] + "".join(x.title() for x in components[1:])


class ResponseTransformerMiddleware(BaseHTTPMiddleware):
    """
    Response Transformer Middleware

    Features:
    - Consistent response formatting
    - Version-specific transformations
    - Response compression
    - Cache header management
    - Error standardization
    - Prometheus metrics integration
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.formatter = ResponseFormat()
        self.cache_manager = CacheManager()
        self.compression_handler = CompressionHandler()
        self.version_transformer = VersionTransformer()
        self.metrics_enabled = hasattr(metrics, 'response_size_histogram')

        logger.info("Response Transformer Middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process response through transformer"""
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Skip transformation for certain paths
            if self._should_skip_transformation(request):
                return response

            # Extract API version from request
            api_version = self._extract_api_version(request)

            # Process response based on type
            if isinstance(response, JSONResponse):
                response = await self._transform_json_response(
                    request, response, api_version
                )
            elif isinstance(response, StreamingResponse):
                # Don't transform streaming responses
                pass
            else:
                # Transform other response types
                response = await self._transform_generic_response(
                    request, response, api_version
                )

            # Add cache headers
            cache_headers = self.cache_manager.get_cache_headers(
                request.method, request.url.path
            )
            for key, value in cache_headers.items():
                response.headers[key] = value

            # Add performance headers
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = f"{process_time * 1000:.2f}ms"
            response.headers["X-Server-Time"] = datetime.utcnow().isoformat()

            # Record metrics if available
            if self.metrics_enabled:
                self._record_metrics(request, response, process_time)

            return response

        except HTTPException as e:
            # Format HTTP exceptions
            return JSONResponse(
                status_code=e.status_code,
                content=self.formatter.error(
                    error=e.detail,
                    status_code=e.status_code,
                    error_code=f"HTTP_{e.status_code}"
                ),
                headers={
                    "X-Process-Time": f"{(time.time() - start_time) * 1000:.2f}ms"
                }
            )

        except Exception as e:
            logger.error(f"Response transformer error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=self.formatter.error(
                    error="Internal server error",
                    status_code=500,
                    error_code="INTERNAL_ERROR"
                )
            )

    async def _transform_json_response(
        self,
        request: Request,
        response: JSONResponse,
        api_version: str
    ) -> Response:
        """Transform JSON responses"""
        # Get response body
        body = response.body

        try:
            # Parse JSON
            data = json.loads(body)

            # Apply version transformation
            transformed_data = self.version_transformer.transform(data, api_version)

            # Re-encode
            transformed_body = json.dumps(
                transformed_data,
                ensure_ascii=False,
                indent=None,
                separators=(",", ":")
            ).encode("utf-8")

            # Check if compression is needed
            accept_encoding = request.headers.get("accept-encoding", "")
            if self.compression_handler.should_compress(
                "application/json",
                len(transformed_body),
                accept_encoding
            ):
                compressed_body = self.compression_handler.compress_content(transformed_body)
                response.body = compressed_body
                response.headers["Content-Encoding"] = "gzip"
                response.headers["Content-Length"] = str(len(compressed_body))
            else:
                response.body = transformed_body
                response.headers["Content-Length"] = str(len(transformed_body))

            # Add ETag
            response.headers["ETag"] = self.cache_manager.generate_etag(response.body)

        except json.JSONDecodeError:
            # Not JSON, return as-is
            pass

        return response

    async def _transform_generic_response(
        self,
        request: Request,
        response: Response,
        api_version: str
    ) -> Response:
        """Transform generic responses"""
        # Add version header
        response.headers["X-API-Version"] = api_version
        return response

    def _should_skip_transformation(self, request: Request) -> bool:
        """Check if transformation should be skipped"""
        # Skip for health checks
        if request.url.path in ["/health", "/api/health", "/metrics"]:
            return True

        # Skip for static files
        if request.url.path.startswith("/static"):
            return True

        # Skip for documentation
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            return True

        return False

    def _extract_api_version(self, request: Request) -> str:
        """Extract API version from request"""
        # Check header first
        version_header = request.headers.get("X-API-Version")
        if version_header:
            return version_header

        # Extract from path
        path_parts = request.url.path.split("/")
        for part in path_parts:
            if part.startswith("v") and len(part) > 1:
                return part

        # Default to latest
        return "v3"

    def _record_metrics(self, request: Request, response: Response, process_time: float):
        """Record Prometheus metrics"""
        try:
            # Response size
            content_length = response.headers.get("content-length", "0")
            if hasattr(metrics, 'response_size_histogram'):
                metrics.response_size_histogram.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=response.status_code
                ).observe(float(content_length))

            # Response time
            if hasattr(metrics, 'response_time_histogram'):
                metrics.response_time_histogram.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=response.status_code
                ).observe(process_time)

        except Exception as e:
            logger.debug(f"Failed to record metrics: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get transformer statistics"""
        return {
            "compression_enabled": True,
            "cache_enabled": True,
            "version_transformation_enabled": True,
        }


# Export middleware and utilities
__all__ = [
    "ResponseTransformerMiddleware",
    "ResponseFormat",
    "CacheManager",
    "CompressionHandler",
    "VersionTransformer"
]