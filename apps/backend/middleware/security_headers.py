"""
Security Headers Middleware
Implements comprehensive security headers and secure error handling
"""

import hashlib
import json
import logging
import re
import secrets
import traceback
from datetime import datetime, timezone
from typing import Any

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add comprehensive security headers to all responses

    Features:
    - HSTS (HTTP Strict Transport Security)
    - CSP (Content Security Policy)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    - CORS headers
    - Cache control for sensitive endpoints
    """

    def __init__(
        self,
        app,
        enable_hsts: bool = True,
        enable_csp: bool = True,
        csp_directives: dict[str, str] | None = None,
        frame_options: str = "DENY",
        enable_nonce: bool = True,
        report_uri: str | None = None,
    ):
        """
        Initialize Security Headers Middleware

        Args:
            app: FastAPI application
            enable_hsts: Enable HSTS header
            enable_csp: Enable Content Security Policy
            csp_directives: Custom CSP directives
            frame_options: X-Frame-Options value (DENY, SAMEORIGIN)
            enable_nonce: Generate CSP nonce for inline scripts
            report_uri: URI for CSP violation reports
        """
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.enable_csp = enable_csp
        self.frame_options = frame_options
        self.enable_nonce = enable_nonce
        self.report_uri = report_uri

        # Default CSP directives
        self.csp_directives = csp_directives or {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src": "'self' https://fonts.gstatic.com",
            "img-src": "'self' data: https:",
            "connect-src": "'self' wss: https:",
            "frame-ancestors": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
            "upgrade-insecure-requests": "",
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and add security headers to response

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response with security headers
        """
        # Generate CSP nonce if enabled
        nonce = None
        if self.enable_nonce:
            nonce = secrets.token_urlsafe(16)
            request.state.csp_nonce = nonce

        try:
            # Process request
            response = await call_next(request)

            # Add security headers
            self._add_security_headers(response, request, nonce)

            return response

        except Exception as e:
            # Log error securely (no sensitive data)
            logger.error(f"Request failed: {e.__class__.__name__}")

            # Return secure error response
            return self._create_secure_error_response(e, request)

    def _add_security_headers(self, response: Response, request: Request, nonce: str | None = None):
        """
        Add security headers to response

        Args:
            response: Response object
            request: Request object
            nonce: CSP nonce for inline scripts
        """
        # HSTS - Force HTTPS
        if self.enable_hsts and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Content Security Policy
        if self.enable_csp:
            csp_header = self._build_csp_header(nonce)
            response.headers["Content-Security-Policy"] = csp_header

            # Report-only version for testing
            if self.report_uri:
                response.headers["Content-Security-Policy-Report-Only"] = (
                    csp_header + f"; report-uri {self.report_uri}"
                )

        # X-Frame-Options - Prevent clickjacking
        response.headers["X-Frame-Options"] = self.frame_options

        # X-Content-Type-Options - Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection - Legacy XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy - Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )

        # Cache-Control for sensitive endpoints
        if self._is_sensitive_endpoint(request.url.path):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # Remove server header to avoid information disclosure
        response.headers.pop("Server", None)

        # Add custom security header
        response.headers["X-ToolboxAI-Security"] = "enabled"

    def _build_csp_header(self, nonce: str | None = None) -> str:
        """
        Build Content Security Policy header

        Args:
            nonce: Nonce for inline scripts

        Returns:
            CSP header string
        """
        directives = []

        for directive, value in self.csp_directives.items():
            if directive == "script-src" and nonce:
                # Add nonce to script-src
                value = f"{value} 'nonce-{nonce}'"

            if value:
                directives.append(f"{directive} {value}")
            else:
                directives.append(directive)

        return "; ".join(directives)

    def _is_sensitive_endpoint(self, path: str) -> bool:
        """
        Check if endpoint handles sensitive data

        Args:
            path: Request path

        Returns:
            True if endpoint is sensitive
        """
        sensitive_patterns = [
            r"/api/v1/auth/",
            r"/api/v1/users/",
            r"/api/v1/admin/",
            r"/api/v1/gdpr/",
            r"/api/v1/payments/",
        ]

        for pattern in sensitive_patterns:
            if re.match(pattern, path):
                return True

        return False

    def _create_secure_error_response(self, error: Exception, request: Request) -> JSONResponse:
        """
        Create secure error response without leaking sensitive information

        Args:
            error: Exception that occurred
            request: Request object

        Returns:
            Secure JSON error response
        """
        # Generate error ID for tracking
        error_id = hashlib.sha256(
            f"{datetime.now(timezone.utc).isoformat()}_{id(error)}".encode()
        ).hexdigest()[:16]

        # Log full error internally
        logger.error(f"Error {error_id}: {traceback.format_exc()}")

        # Determine status code
        if isinstance(error, HTTPException):
            status_code = error.status_code
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        # Create safe error message
        if status_code < 500:
            # Client errors can include more detail
            message = str(error) if isinstance(error, HTTPException) else "Bad Request"
        else:
            # Server errors should be generic
            message = "An internal error occurred"

        # Create error response
        error_response = {
            "error": {
                "id": error_id,
                "message": message,
                "status": status_code,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": str(request.url.path),
            }
        }

        # Add debug info only in development
        if request.app.debug:
            error_response["error"]["debug"] = {
                "type": error.__class__.__name__,
                "detail": str(error),
            }

        return JSONResponse(
            status_code=status_code, content=error_response, headers={"X-Error-ID": error_id}
        )


class SecureErrorHandler:
    """
    Secure error handler that prevents information leakage

    Features:
    - Sanitizes error messages
    - Logs full errors internally
    - Returns safe client responses
    - Tracks errors for monitoring
    """

    def __init__(self, debug_mode: bool = False):
        """
        Initialize Secure Error Handler

        Args:
            debug_mode: Whether to include debug information
        """
        self.debug_mode = debug_mode
        self.error_patterns = self._init_error_patterns()

    def _init_error_patterns(self) -> list[dict[str, Any]]:
        """Initialize patterns for sanitizing error messages"""
        return [
            {"pattern": r"(password|secret|token|key)[\s=:]+[\S]+", "replacement": "[REDACTED]"},
            {
                "pattern": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",  # IP addresses
                "replacement": "[IP_REDACTED]",
            },
            {
                "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Emails
                "replacement": "[EMAIL_REDACTED]",
            },
            {"pattern": r"/home/[\w/]+", "replacement": "[PATH_REDACTED]"},  # File paths
            {
                "pattern": r"line \d+ in [\w\.]+",  # Stack trace details
                "replacement": "[TRACE_REDACTED]",
            },
        ]

    def handle_error(
        self, error: Exception, request: Request | None = None, context: dict | None = None
    ) -> JSONResponse:
        """
        Handle error and return secure response

        Args:
            error: Exception to handle
            request: Request object if available
            context: Additional context

        Returns:
            Secure JSON response
        """
        # Generate error tracking ID
        error_id = self._generate_error_id(error)

        # Log full error
        self._log_error(error, error_id, request, context)

        # Determine error category
        error_category = self._categorize_error(error)

        # Create sanitized message
        safe_message = self._sanitize_message(str(error))

        # Build response
        response_data = {
            "error": {
                "id": error_id,
                "category": error_category,
                "message": safe_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }

        # Add request info if available
        if request:
            response_data["error"]["path"] = str(request.url.path)
            response_data["error"]["method"] = request.method

        # Add debug info if enabled
        if self.debug_mode:
            response_data["error"]["debug"] = {
                "type": error.__class__.__name__,
                "module": error.__class__.__module__,
                "original_message": str(error)[:500],  # Truncate long messages
            }

        # Determine status code
        status_code = self._get_status_code(error)

        return JSONResponse(
            status_code=status_code,
            content=response_data,
            headers={"X-Error-ID": error_id, "X-Content-Type-Options": "nosniff"},
        )

    def _generate_error_id(self, error: Exception) -> str:
        """Generate unique error ID"""
        error_string = f"{datetime.now(timezone.utc)}_{type(error)}_{id(error)}"
        return hashlib.sha256(error_string.encode()).hexdigest()[:16]

    def _log_error(
        self,
        error: Exception,
        error_id: str,
        request: Request | None = None,
        context: dict | None = None,
    ):
        """Log error with full details"""
        log_data = {
            "error_id": error_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }

        if request:
            log_data["request"] = {
                "method": request.method,
                "path": str(request.url.path),
                "query": str(request.url.query),
                "headers": self._sanitize_headers(dict(request.headers)),
                "client": request.client.host if request.client else None,
            }

        if context:
            log_data["context"] = context

        logger.error(f"Error {error_id}: {json.dumps(log_data, indent=2)}")

    def _categorize_error(self, error: Exception) -> str:
        """Categorize error for client response"""
        if isinstance(error, HTTPException):
            if error.status_code < 400:
                return "redirect"
            elif error.status_code < 500:
                return "client_error"
            else:
                return "server_error"
        elif isinstance(error, ValueError):
            return "validation_error"
        elif isinstance(error, KeyError):
            return "not_found"
        elif isinstance(error, PermissionError):
            return "permission_denied"
        elif isinstance(error, TimeoutError):
            return "timeout"
        else:
            return "internal_error"

    def _sanitize_message(self, message: str) -> str:
        """Sanitize error message to remove sensitive data"""
        sanitized = message

        for pattern_config in self.error_patterns:
            pattern = re.compile(pattern_config["pattern"], re.IGNORECASE)
            sanitized = pattern.sub(pattern_config["replacement"], sanitized)

        # Truncate long messages
        if len(sanitized) > 500:
            sanitized = sanitized[:500] + "... [truncated]"

        return sanitized

    def _sanitize_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Sanitize headers to remove sensitive values"""
        sensitive_headers = ["authorization", "cookie", "x-api-key", "x-auth-token"]

        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value

        return sanitized

    def _get_status_code(self, error: Exception) -> int:
        """Determine appropriate HTTP status code"""
        if isinstance(error, HTTPException):
            return error.status_code
        elif isinstance(error, ValueError):
            return status.HTTP_400_BAD_REQUEST
        elif isinstance(error, KeyError):
            return status.HTTP_404_NOT_FOUND
        elif isinstance(error, PermissionError):
            return status.HTTP_403_FORBIDDEN
        elif isinstance(error, TimeoutError):
            return status.HTTP_408_REQUEST_TIMEOUT
        else:
            return status.HTTP_500_INTERNAL_SERVER_ERROR


# Global error handler instance
error_handler = SecureErrorHandler()


def handle_api_error(error: Exception, request: Request = None) -> JSONResponse:
    """
    Convenience function to handle API errors

    Args:
        error: Exception to handle
        request: Request object

    Returns:
        Secure JSON response
    """
    return error_handler.handle_error(error, request)
