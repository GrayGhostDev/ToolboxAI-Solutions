"""
CORS Security Configuration Module

Implements secure Cross-Origin Resource Sharing (CORS) configuration
following OWASP best practices and FastAPI official documentation.

References:
- https://fastapi.tiangolo.com/tutorial/cors/
- https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
"""

import logging
import re
from typing import List, Optional, Set
from urllib.parse import urlparse
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)


class SecureCORSConfig:
    """
    Secure CORS configuration with origin validation and logging
    """

    def __init__(
        self,
        environment: str = "production",
        allowed_origins: Optional[List[str]] = None,
        allowed_origins_regex: Optional[str] = None,
        allow_credentials: bool = True,
        allowed_methods: Optional[List[str]] = None,
        allowed_headers: Optional[List[str]] = None,
        exposed_headers: Optional[List[str]] = None,
        max_age: int = 600,
    ):
        """
        Initialize secure CORS configuration

        Args:
            environment: Current environment (development/staging/production)
            allowed_origins: List of allowed origins (no wildcards in production)
            allowed_origins_regex: Regex pattern for dynamic origin validation
            allow_credentials: Whether to allow credentials in CORS requests
            allowed_methods: List of allowed HTTP methods
            allowed_headers: List of allowed request headers
            exposed_headers: List of headers exposed to the browser
            max_age: Max age for preflight cache in seconds
        """
        self.environment = environment
        self.allow_credentials = allow_credentials
        self.max_age = max_age

        # Set default allowed origins based on environment
        if allowed_origins is None:
            if environment == "development":
                # Development: Allow common local development ports
                self.allowed_origins = [
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                    "http://localhost:5174",
                    "http://127.0.0.1:5174",
                    "http://localhost:5175",
                    "http://127.0.0.1:5175",
                    "http://localhost:5176",
                    "http://127.0.0.1:5176",
                    "http://localhost:5177",
                    "http://127.0.0.1:5177",
                    "http://localhost:5178",
                    "http://127.0.0.1:5178",
                    "http://localhost:5179",
                    "http://127.0.0.1:5179",
                    # Vercel deployments
                    "https://toolboxai-dashboard.vercel.app",
                    "https://toolboxai-solutions.vercel.app",
                    # Render backend
                    "https://toolboxai-backend.onrender.com",
                ]
            else:
                # Production: Explicit allowed origins for Vercel and Render
                self.allowed_origins = [
                    "https://toolboxai-dashboard.vercel.app",
                    "https://toolboxai-solutions.vercel.app",
                    "https://toolboxai-backend.onrender.com",
                ]
                logger.info(f"Production CORS configured with origins: {self.allowed_origins}")
        else:
            # Validate and sanitize origins
            self.allowed_origins = self._validate_origins(allowed_origins)

        # Set regex pattern for dynamic validation
        self.allowed_origins_regex = allowed_origins_regex
        if allowed_origins_regex:
            try:
                self.origin_pattern = re.compile(allowed_origins_regex)
            except re.error as e:
                logger.error(f"Invalid CORS origin regex pattern: {e}")
                self.origin_pattern = None
        else:
            self.origin_pattern = None

        # Set allowed methods (be specific, avoid wildcards)
        if allowed_methods is None:
            self.allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        else:
            self.allowed_methods = allowed_methods

        # Set allowed headers (be specific in production)
        if allowed_headers is None:
            if environment == "development":
                self.allowed_headers = [
                    "Accept",
                    "Accept-Language",
                    "Content-Language",
                    "Content-Type",
                    "Authorization",
                    "X-Requested-With",
                    "X-Request-ID",
                    "X-Session-ID",
                    "Origin",
                    "User-Agent",
                ]
            else:
                # Production: Be more restrictive
                self.allowed_headers = [
                    "Accept",
                    "Content-Type",
                    "Authorization",
                    "X-Request-ID",
                ]
        else:
            self.allowed_headers = allowed_headers

        # Set exposed headers (limit in production)
        if exposed_headers is None:
            self.exposed_headers = [
                "X-Request-ID",
                "X-Process-Time",
                "Content-Type",
                "Content-Length",
            ]
        else:
            self.exposed_headers = exposed_headers

        # Convert to sets for faster lookup
        self.allowed_origins_set = set(self.allowed_origins)
        self.allowed_methods_set = set(self.allowed_methods)
        self.allowed_headers_set = set([h.lower() for h in self.allowed_headers])

        # Log configuration
        logger.info(f"CORS configured for {environment} environment")
        logger.info(f"Allowed origins: {self.allowed_origins}")
        logger.info(f"Allowed methods: {self.allowed_methods}")

    def _validate_origins(self, origins: List[str]) -> List[str]:
        """
        Validate and sanitize origin URLs

        Args:
            origins: List of origin URLs to validate

        Returns:
            List of validated origins
        """
        validated = []

        for origin in origins:
            # Skip wildcards in production
            if origin == "*":
                if self.environment != "development":
                    logger.error("Wildcard origin (*) not allowed in production")
                    continue
                else:
                    logger.warning("Using wildcard origin (*) in development - not secure!")
                    validated.append(origin)
                    continue

            # Validate URL format
            try:
                parsed = urlparse(origin)
                if not parsed.scheme or not parsed.netloc:
                    logger.warning(f"Invalid origin format: {origin}")
                    continue

                # Only allow http and https protocols
                if parsed.scheme not in ["http", "https"]:
                    logger.warning(f"Invalid protocol in origin: {origin}")
                    continue

                # Reconstruct origin without path
                clean_origin = f"{parsed.scheme}://{parsed.netloc}"
                validated.append(clean_origin)

            except Exception as e:
                logger.error(f"Error validating origin {origin}: {e}")

        return validated

    def is_origin_allowed(self, origin: str) -> bool:
        """
        Check if an origin is allowed

        Args:
            origin: The origin to check

        Returns:
            True if origin is allowed, False otherwise
        """
        if not origin:
            return False

        # Check exact match
        if origin in self.allowed_origins_set:
            return True

        # Check regex pattern if configured
        if self.origin_pattern:
            if self.origin_pattern.match(origin):
                return True

        # Log rejected origin
        logger.warning(f"CORS: Rejected origin: {origin}")
        return False

    def get_cors_headers(self, origin: str) -> dict:
        """
        Get CORS headers for a specific origin

        Args:
            origin: The request origin

        Returns:
            Dictionary of CORS headers
        """
        headers = {}

        if self.is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin

            if self.allow_credentials:
                headers["Access-Control-Allow-Credentials"] = "true"

            if self.exposed_headers:
                headers["Access-Control-Expose-Headers"] = ", ".join(self.exposed_headers)

        return headers

    def get_preflight_headers(self, origin: str, request_method: str, request_headers: str) -> dict:
        """
        Get CORS headers for preflight requests

        Args:
            origin: The request origin
            request_method: The requested method
            request_headers: The requested headers

        Returns:
            Dictionary of CORS preflight headers
        """
        headers = self.get_cors_headers(origin)

        if headers:  # Only add preflight headers if origin is allowed
            headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
            headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
            headers["Access-Control-Max-Age"] = str(self.max_age)

        return headers


class CORSMiddlewareWithLogging(CORSMiddleware):
    """
    Enhanced CORS middleware with security logging
    """

    def __init__(self, app: ASGIApp, cors_config: SecureCORSConfig, **kwargs):
        """
        Initialize CORS middleware with secure configuration

        Args:
            app: The ASGI application
            cors_config: Secure CORS configuration
            **kwargs: Additional arguments for CORSMiddleware
        """
        self.cors_config = cors_config

        # Initialize parent with secure settings
        super().__init__(
            app,
            allow_origins=cors_config.allowed_origins,
            allow_origin_regex=cors_config.allowed_origins_regex,
            allow_credentials=cors_config.allow_credentials,
            allow_methods=cors_config.allowed_methods,
            allow_headers=cors_config.allowed_headers,
            expose_headers=cors_config.exposed_headers,
            max_age=cors_config.max_age,
            **kwargs,
        )

        self.violation_count = 0
        self.violations_by_origin = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Handle CORS with enhanced logging
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        origin = headers.get("origin")

        # Log CORS request
        if origin:
            method = scope["method"]
            path = scope["path"]

            # Check if origin is allowed
            if not self.cors_config.is_origin_allowed(origin):
                self.violation_count += 1
                self.violations_by_origin[origin] = self.violations_by_origin.get(origin, 0) + 1

                logger.warning(
                    f"CORS violation #{self.violation_count}: "
                    f"Origin={origin}, Method={method}, Path={path}, "
                    f"Total violations from origin={self.violations_by_origin[origin]}"
                )

                # Check for potential attack patterns
                if self.violations_by_origin[origin] > 10:
                    logger.error(
                        f"Potential CORS attack detected from origin: {origin} "
                        f"({self.violations_by_origin[origin]} violations)"
                    )

        # Continue with standard CORS handling
        await super().__call__(scope, receive, send)


def create_cors_middleware(
    environment: str,
    allowed_origins: Optional[List[str]] = None,
    allowed_origins_regex: Optional[str] = None,
    **kwargs,
) -> CORSMiddlewareWithLogging:
    """
    Factory function to create secure CORS middleware

    Args:
        environment: Current environment (development/staging/production)
        allowed_origins: List of allowed origins
        allowed_origins_regex: Regex pattern for dynamic origins
        **kwargs: Additional configuration options

    Returns:
        Configured CORS middleware instance
    """
    cors_config = SecureCORSConfig(
        environment=environment,
        allowed_origins=allowed_origins,
        allowed_origins_regex=allowed_origins_regex,
        **kwargs,
    )

    def middleware(app: ASGIApp) -> CORSMiddlewareWithLogging:
        return CORSMiddlewareWithLogging(app, cors_config)

    return middleware


# Export for easy import
__all__ = ["SecureCORSConfig", "CORSMiddlewareWithLogging", "create_cors_middleware"]
