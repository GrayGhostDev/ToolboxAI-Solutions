"""
Security Headers Middleware for FastAPI

Implements comprehensive security headers following OWASP recommendations:
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add comprehensive security headers to all responses
    """

    def __init__(
        self,
        app,
        *,
        hsts_max_age: int = 31536000,  # 1 year
        csp_policy: Optional[str] = None,
        enable_hsts: bool = True,
        enable_xss_protection: bool = True,
        custom_headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.enable_hsts = enable_hsts
        self.enable_xss_protection = enable_xss_protection
        self.custom_headers = custom_headers or {}

        # Default CSP policy - restrictive but functional for API
        self.csp_policy = csp_policy or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:5179 http://127.0.0.1:5179 ws://localhost:5179 ws://127.0.0.1:5179; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add comprehensive security headers
        security_headers = self._get_security_headers(request)

        for header, value in security_headers.items():
            if value:  # Only add non-empty headers
                response.headers[header] = value

        return response

    def _get_security_headers(self, request: Request) -> Dict[str, str]:
        """
        Generate security headers based on request context
        """
        headers = {}

        # X-Frame-Options: Prevent clickjacking
        headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options: Prevent MIME sniffing
        headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection: Enable XSS filtering (legacy but still useful)
        if self.enable_xss_protection:
            headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Control referrer information
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        headers["Content-Security-Policy"] = self.csp_policy

        # HTTP Strict Transport Security (only for HTTPS)
        if self.enable_hsts and request.url.scheme == "https":
            headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}; includeSubDomains; preload"

        # Permissions Policy (Feature Policy successor)
        headers["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "interest-cohort=(), "
            "payment=(), "
            "usb=(), "
            "accelerometer=(), "
            "gyroscope=(), "
            "magnetometer=()"
        )

        # X-Robots-Tag: Control search engine indexing
        headers["X-Robots-Tag"] = "noindex, nofollow, nosnippet, noarchive"

        # X-DNS-Prefetch-Control: Control DNS prefetching
        headers["X-DNS-Prefetch-Control"] = "off"

        # Clear-Site-Data: Clear site data on logout endpoints
        if request.url.path.endswith("/logout"):
            headers["Clear-Site-Data"] = '"cache", "cookies", "storage", "executionContexts"'

        # Server header removal (hide server information)
        headers["Server"] = "ToolBoxAI"

        # Add any custom headers
        headers.update(self.custom_headers)

        return headers


def get_csp_policy_for_environment(environment: str = "development") -> str:
    """
    Get environment-specific CSP policy
    """
    if environment == "production":
        return (
            "default-src 'self'; "
            "script-src 'self' 'sha256-YOUR_SCRIPT_HASH_HERE'; "
            "style-src 'self' 'sha256-YOUR_STYLE_HASH_HERE'; "
            "img-src 'self' https: data:; "
            "font-src 'self' https:; "
            "connect-src 'self' https://api.toolboxai.com wss://api.toolboxai.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    elif environment == "staging":
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' https: data:; "
            "font-src 'self' https:; "
            "connect-src 'self' https://staging.toolboxai.com wss://staging.toolboxai.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    else:  # development
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:5179 http://127.0.0.1:5179 ws://localhost:5179 ws://127.0.0.1:5179; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )


class SecurityHeadersConfig:
    """
    Configuration class for security headers
    """

    def __init__(
        self,
        environment: str = "development",
        hsts_max_age: int = 31536000,
        enable_hsts: bool = True,
        enable_xss_protection: bool = True,
        custom_csp: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ):
        self.environment = environment
        self.hsts_max_age = hsts_max_age
        self.enable_hsts = enable_hsts
        self.enable_xss_protection = enable_xss_protection
        self.custom_csp = custom_csp
        self.custom_headers = custom_headers or {}

    def get_csp_policy(self) -> str:
        """Get CSP policy for the configured environment"""
        return self.custom_csp or get_csp_policy_for_environment(self.environment)

    def get_middleware(self):
        """Get configured security headers middleware"""
        return SecurityHeadersMiddleware(
            app=None,  # Will be set by FastAPI
            hsts_max_age=self.hsts_max_age,
            csp_policy=self.get_csp_policy(),
            enable_hsts=self.enable_hsts,
            enable_xss_protection=self.enable_xss_protection,
            custom_headers=self.custom_headers
        )