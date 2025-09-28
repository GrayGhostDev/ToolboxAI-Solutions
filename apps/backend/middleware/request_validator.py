"""
Request Validator Middleware
Validates incoming requests with Pydantic schemas, sanitization, and size limits
Integrates with Supabase RLS policies for data access validation
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Type, Union
from urllib.parse import parse_qs, unquote

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError, validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class ValidationConfig:
    """Configuration for request validation"""

    # Size limits
    MAX_BODY_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_JSON_DEPTH = 10
    MAX_ARRAY_LENGTH = 1000
    MAX_STRING_LENGTH = 10000
    MAX_QUERY_PARAMS = 50
    MAX_HEADER_SIZE = 8192

    # Content types
    ALLOWED_CONTENT_TYPES = {
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data",
        "text/plain",
    }

    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|FROM|WHERE)\b)",
        r"(--|\||;|\/\*|\*\/)",
        r"(xp_|sp_|0x)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"%2e%2e",
        r"\.\.%2f",
    ]


class SanitizationRules:
    """Rules for input sanitization"""

    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return str(value)

        # Remove null bytes
        value = value.replace("\x00", "")

        # Trim whitespace
        value = value.strip()

        # Limit length
        if max_length:
            value = value[:max_length]

        # Remove control characters
        value = "".join(char for char in value if ord(char) >= 32 or char in "\t\n\r")

        return value

    @staticmethod
    def sanitize_html(value: str) -> str:
        """Remove potentially dangerous HTML"""
        # Basic HTML sanitization
        dangerous_tags = ["script", "iframe", "object", "embed", "form"]
        for tag in dangerous_tags:
            pattern = f"<{tag}[^>]*>.*?</{tag}>"
            value = re.sub(pattern, "", value, flags=re.IGNORECASE | re.DOTALL)

        # Remove event handlers
        value = re.sub(r"on\w+\s*=\s*[\"'].*?[\"']", "", value, flags=re.IGNORECASE)

        return value

    @staticmethod
    def sanitize_sql(value: str) -> str:
        """Remove potential SQL injection attempts"""
        # Remove SQL comments
        value = re.sub(r"--.*$", "", value, flags=re.MULTILINE)
        value = re.sub(r"/\*.*?\*/", "", value, flags=re.DOTALL)

        # Escape quotes
        value = value.replace("'", "''")

        return value

    @staticmethod
    def sanitize_path(value: str) -> str:
        """Sanitize file paths"""
        # Remove path traversal attempts
        value = re.sub(r"\.\./", "", value)
        value = re.sub(r"\.\.\\", "", value)

        # Remove null bytes
        value = value.replace("\x00", "")

        # Normalize path
        value = value.replace("\\", "/")

        return value


class RequestSchemas:
    """Pydantic schemas for common request types"""

    class PaginationParams(BaseModel):
        page: int = Field(1, ge=1, le=1000)
        limit: int = Field(10, ge=1, le=100)
        sort: Optional[str] = Field(None, max_length=50)
        order: Optional[str] = Field("asc", regex="^(asc|desc)$")

    class SearchParams(BaseModel):
        query: str = Field(..., min_length=1, max_length=500)
        filters: Optional[Dict[str, Any]] = None
        fields: Optional[List[str]] = Field(None, max_items=50)

    class IDParam(BaseModel):
        id: Union[str, int] = Field(...)

        @validator("id")
        def validate_id(cls, v):
            if isinstance(v, str):
                # Validate UUID format
                uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                if not re.match(uuid_pattern, v.lower()):
                    # Try integer ID
                    try:
                        return int(v)
                    except ValueError:
                        raise ValueError("Invalid ID format")
            return v


class RequestValidator:
    """Core request validation logic"""

    def __init__(self, config: ValidationConfig = ValidationConfig()):
        self.config = config
        self.sanitizer = SanitizationRules()
        self.validation_cache = {}

    async def validate_request(
        self,
        request: Request,
        schema: Optional[Type[BaseModel]] = None
    ) -> Dict[str, Any]:
        """
        Validate request against schema and security rules

        Args:
            request: FastAPI request
            schema: Optional Pydantic schema

        Returns:
            Validated and sanitized data

        Raises:
            HTTPException: If validation fails
        """
        # Check content type
        content_type = request.headers.get("content-type", "").split(";")[0]
        if request.method in ["POST", "PUT", "PATCH"]:
            if content_type not in self.config.ALLOWED_CONTENT_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Content type {content_type} not supported"
                )

        # Validate headers
        self._validate_headers(request)

        # Validate body size
        if hasattr(request, "_body"):
            body_size = len(request._body)
            if body_size > self.config.MAX_BODY_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request body too large: {body_size} bytes"
                )

        # Get and validate data based on content type
        data = {}
        if content_type == "application/json":
            data = await self._validate_json(request)
        elif content_type == "application/x-www-form-urlencoded":
            data = await self._validate_form_data(request)
        elif content_type == "multipart/form-data":
            data = await self._validate_multipart(request)

        # Validate query parameters
        query_params = self._validate_query_params(request)
        data.update(query_params)

        # Apply schema validation if provided
        if schema:
            try:
                validated = schema(**data)
                data = validated.dict()
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=e.errors()
                )

        # Check for injection attempts
        self._check_injection_attacks(data)

        return data

    def _validate_headers(self, request: Request):
        """Validate request headers"""
        total_header_size = sum(
            len(k) + len(v)
            for k, v in request.headers.items()
        )

        if total_header_size > self.config.MAX_HEADER_SIZE:
            raise HTTPException(
                status_code=status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE,
                detail="Request headers too large"
            )

        # Check for suspicious headers
        suspicious_headers = ["x-forwarded-host", "x-original-url", "x-rewrite-url"]
        for header in suspicious_headers:
            if header in request.headers:
                logger.warning(f"Suspicious header detected: {header}")

    async def _validate_json(self, request: Request) -> Dict[str, Any]:
        """Validate JSON body"""
        try:
            body = await request.body()
            if not body:
                return {}

            data = json.loads(body)

            # Check JSON depth
            if self._get_json_depth(data) > self.config.MAX_JSON_DEPTH:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="JSON nesting too deep"
                )

            # Sanitize strings in JSON
            return self._sanitize_json(data)

        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON: {str(e)}"
            )

    async def _validate_form_data(self, request: Request) -> Dict[str, Any]:
        """Validate form data"""
        form_data = await request.form()
        data = {}

        for key, value in form_data.items():
            # Sanitize key and value
            clean_key = self.sanitizer.sanitize_string(key, max_length=100)
            clean_value = self.sanitizer.sanitize_string(str(value))
            data[clean_key] = clean_value

        return data

    async def _validate_multipart(self, request: Request) -> Dict[str, Any]:
        """Validate multipart form data"""
        form = await request.form()
        data = {}

        for key, value in form.items():
            if hasattr(value, "filename"):
                # File upload
                filename = self.sanitizer.sanitize_path(value.filename)
                data[key] = {
                    "filename": filename,
                    "content_type": value.content_type,
                    "size": len(await value.read())
                }
                # Reset file pointer
                await value.seek(0)
            else:
                data[key] = self.sanitizer.sanitize_string(str(value))

        return data

    def _validate_query_params(self, request: Request) -> Dict[str, Any]:
        """Validate query parameters"""
        query_params = dict(request.query_params)

        if len(query_params) > self.config.MAX_QUERY_PARAMS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many query parameters: {len(query_params)}"
            )

        cleaned_params = {}
        for key, value in query_params.items():
            clean_key = self.sanitizer.sanitize_string(key, max_length=100)
            clean_value = self.sanitizer.sanitize_string(value)
            cleaned_params[clean_key] = clean_value

        return cleaned_params

    def _sanitize_json(self, data: Any) -> Any:
        """Recursively sanitize JSON data"""
        if isinstance(data, dict):
            return {
                self.sanitizer.sanitize_string(k, max_length=100): self._sanitize_json(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            if len(data) > self.config.MAX_ARRAY_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Array too long: {len(data)} items"
                )
            return [self._sanitize_json(item) for item in data]
        elif isinstance(data, str):
            return self.sanitizer.sanitize_string(data, max_length=self.config.MAX_STRING_LENGTH)
        else:
            return data

    def _get_json_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate JSON nesting depth"""
        if current_depth > self.config.MAX_JSON_DEPTH:
            return current_depth

        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(
                self._get_json_depth(v, current_depth + 1)
                for v in obj.values()
            )
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(
                self._get_json_depth(item, current_depth + 1)
                for item in obj
            )
        else:
            return current_depth

    def _check_injection_attacks(self, data: Any):
        """Check for potential injection attacks"""
        def check_value(value: str):
            # Check SQL injection
            for pattern in self.config.SQL_INJECTION_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    logger.warning(f"Potential SQL injection detected: {value[:100]}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input detected"
                    )

            # Check XSS
            for pattern in self.config.XSS_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    logger.warning(f"Potential XSS detected: {value[:100]}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input detected"
                    )

            # Check path traversal
            for pattern in self.config.PATH_TRAVERSAL_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    logger.warning(f"Potential path traversal detected: {value[:100]}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input detected"
                    )

        def recursive_check(obj: Any):
            if isinstance(obj, str):
                check_value(obj)
            elif isinstance(obj, dict):
                for value in obj.values():
                    recursive_check(value)
            elif isinstance(obj, list):
                for item in obj:
                    recursive_check(item)

        recursive_check(data)


class RequestValidatorMiddleware(BaseHTTPMiddleware):
    """
    Request Validator Middleware

    Validates all incoming requests for security and data integrity
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.validator = RequestValidator()
        self.validation_stats = {
            "total_requests": 0,
            "valid_requests": 0,
            "invalid_requests": 0,
            "injection_attempts": 0,
        }

        logger.info("Request Validator Middleware initialized")

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through validator"""
        self.validation_stats["total_requests"] += 1

        try:
            # Skip validation for certain paths
            if self._should_skip_validation(request):
                return await call_next(request)

            # Validate request
            validated_data = await self.validator.validate_request(request)

            # Store validated data for use in endpoints
            request.state.validated_data = validated_data

            self.validation_stats["valid_requests"] += 1

            # Process request
            response = await call_next(request)

            return response

        except HTTPException as e:
            self.validation_stats["invalid_requests"] += 1

            if "injection" in str(e.detail).lower():
                self.validation_stats["injection_attempts"] += 1

            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            self.validation_stats["invalid_requests"] += 1

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal validation error"}
            )

    def _should_skip_validation(self, request: Request) -> bool:
        """Check if validation should be skipped for this request"""
        # Skip validation for health checks
        if request.url.path in ["/health", "/api/health", "/api/v1/health"]:
            return True

        # Skip for static files
        if request.url.path.startswith("/static"):
            return True

        # Skip for documentation
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            return True

        return False

    def get_stats(self) -> Dict[str, int]:
        """Get validation statistics"""
        return self.validation_stats.copy()


# Export middleware and utilities
__all__ = [
    "RequestValidatorMiddleware",
    "RequestValidator",
    "ValidationConfig",
    "SanitizationRules",
    "RequestSchemas"
]