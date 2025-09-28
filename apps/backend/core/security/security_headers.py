"""
Security Headers Middleware for FastAPI Application

Implements comprehensive security headers following OWASP guidelines:
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
- Additional security measures
"""

import logging
from typing import Dict, Optional, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security headers middleware for production deployment

    Features:
    - CSP with nonce generation for inline scripts
    - HSTS with preload support
    - Frame protection against clickjacking
    - MIME sniffing protection
    - XSS protection headers
    - Referrer policy controls
    - Permissions policy restrictions
    - Security audit logging
    """

    def __init__(
        self,
        app: ASGIApp,
        environment: str = "production",
        allowed_origins: List[str] = None,
        enable_hsts: bool = True,
        enable_csp: bool = True,
        enable_audit_logging: bool = True,
        custom_headers: Dict[str, str] = None,
    ):
        super().__init__(app)
        self.environment = environment
        self.allowed_origins = allowed_origins or []
        self.enable_hsts = enable_hsts
        self.enable_csp = enable_csp
        self.enable_audit_logging = enable_audit_logging
        self.custom_headers = custom_headers or {}

        # Generate nonce for CSP inline scripts
        self._nonce_cache = {}

    async def dispatch(self, request: Request, call_next):
        """Apply security headers to all responses"""

        # Generate request ID for tracking
        request_id = f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{id(request)}"

        try:
            # Process request
            response = await call_next(request)

            # Apply security headers
            self._apply_security_headers(request, response, request_id)

            # Log security metrics if enabled
            if self.enable_audit_logging:
                await self._log_security_metrics(request, response, request_id)

            return response

        except Exception as e:
            logger.error(f"Security middleware error for {request_id}: {str(e)}")
            raise

    def _apply_security_headers(self, request: Request, response: Response, request_id: str):
        """Apply comprehensive security headers"""

        # Generate CSP nonce for this request
        nonce = self._generate_nonce(request_id)

        # Core Security Headers
        headers = {
            # Content Security Policy
            "Content-Security-Policy": self._build_csp_header(nonce) if self.enable_csp else None,
            # HTTP Strict Transport Security
            "Strict-Transport-Security": (
                "max-age=31536000; includeSubDomains; preload"
                if self.enable_hsts and self.environment == "production"
                else None
            ),
            # Frame Options (Clickjacking Protection)
            "X-Frame-Options": "DENY",
            # Content Type Options (MIME Sniffing Protection)
            "X-Content-Type-Options": "nosniff",
            # XSS Protection
            "X-XSS-Protection": "1; mode=block",
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # Permissions Policy (Feature Policy)
            "Permissions-Policy": self._build_permissions_policy(),
            # Server Information Hiding
            "Server": "ToolboxAI-Secure",
            # Additional Security Headers
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
            # Cache Control for Sensitive Responses
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0",
            # Request Tracking
            "X-Request-ID": request_id,
            # Security Audit
            "X-Security-Audit": f"enabled-{datetime.utcnow().strftime('%Y%m%d')}",
        }

        # Add development-specific headers
        if self.environment != "production":
            headers.update({"X-Debug-Mode": "enabled", "X-Environment": self.environment})

            # Relax some restrictions for development
            headers["Content-Security-Policy"] = self._build_dev_csp_header(nonce)
            headers["Cross-Origin-Resource-Policy"] = "cross-origin"

        # Apply custom headers
        headers.update(self.custom_headers)

        # Set headers on response (skip None values)
        for header_name, header_value in headers.items():
            if header_value is not None:
                response.headers[header_name] = header_value

        # Store nonce in response for template rendering
        if hasattr(response, "context"):
            response.context = getattr(response, "context", {})
            response.context["csp_nonce"] = nonce

    def _build_csp_header(self, nonce: str) -> str:
        """Build production Content Security Policy header"""

        # Determine allowed origins
        origins = " ".join(self.allowed_origins) if self.allowed_origins else "'self'"

        csp_directives = [
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}' 'strict-dynamic'",
            f"style-src 'self' 'nonce-{nonce}' 'unsafe-inline'",  # unsafe-inline needed for some UI libraries
            f"img-src 'self' data: https:",
            f"font-src 'self' data:",
            f"connect-src 'self' {origins}",
            "frame-src 'none'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
            "manifest-src 'self'",
            "media-src 'self'",
            "worker-src 'self'",
            "upgrade-insecure-requests",
        ]

        return "; ".join(csp_directives)

    def _build_dev_csp_header(self, nonce: str) -> str:
        """Build development Content Security Policy header (more permissive)"""

        csp_directives = [
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}' 'unsafe-eval' 'unsafe-inline' localhost:* 127.0.0.1:*",
            f"style-src 'self' 'nonce-{nonce}' 'unsafe-inline' localhost:* 127.0.0.1:*",
            "img-src 'self' data: https: http: localhost:* 127.0.0.1:*",
            "font-src 'self' data: localhost:* 127.0.0.1:*",
            "connect-src 'self' localhost:* 127.0.0.1:* ws: wss:",
            "frame-src 'self' localhost:* 127.0.0.1:*",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "manifest-src 'self'",
            "media-src 'self'",
            "worker-src 'self' blob:",
        ]

        return "; ".join(csp_directives)

    def _build_permissions_policy(self) -> str:
        """Build Permissions Policy header"""

        permissions = [
            "camera=()",
            "microphone=()",
            "geolocation=()",
            "fullscreen=(self)",
            "payment=()",
            "usb=()",
            "serial=()",
            "bluetooth=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
            "ambient-light-sensor=()",
            "autoplay=(self)",
            "encrypted-media=(self)",
            "picture-in-picture=()",
        ]

        return ", ".join(permissions)

    def _generate_nonce(self, request_id: str) -> str:
        """Generate CSP nonce for inline scripts"""

        import hashlib
        import secrets

        # Generate secure nonce
        nonce_source = f"{request_id}_{secrets.token_hex(16)}"
        nonce = hashlib.sha256(nonce_source.encode()).hexdigest()[:16]

        # Cache for potential reuse within request
        self._nonce_cache[request_id] = nonce

        return nonce

    async def _log_security_metrics(self, request: Request, response: Response, request_id: str):
        """Log security metrics for monitoring"""

        try:
            # Extract security-relevant information
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("User-Agent", "unknown")
            method = request.method
            path = str(request.url.path)
            status_code = response.status_code

            # Check for suspicious patterns
            suspicious_indicators = []

            # Check for potential SQL injection patterns
            if any(
                keyword in path.lower()
                for keyword in ["union", "select", "drop", "insert", "update"]
            ):
                suspicious_indicators.append("potential_sql_injection")

            # Check for XSS patterns
            if any(
                pattern in path.lower()
                for pattern in ["<script", "javascript:", "onerror=", "onload="]
            ):
                suspicious_indicators.append("potential_xss")

            # Check for path traversal
            if "../" in path or "..\\" in path:
                suspicious_indicators.append("path_traversal_attempt")

            # Check for suspicious user agents
            suspicious_uas = ["sqlmap", "nikto", "burp", "nmap", "masscan"]
            if any(ua in user_agent.lower() for ua in suspicious_uas):
                suspicious_indicators.append("suspicious_user_agent")

            # Log metrics
            if suspicious_indicators:
                logger.warning(
                    f"SECURITY_ALERT - Request {request_id}: "
                    f"IP={client_ip}, Method={method}, Path={path}, "
                    f"Status={status_code}, Indicators={suspicious_indicators}, "
                    f"UserAgent={user_agent[:100]}"
                )
            else:
                logger.info(
                    f"SECURITY_AUDIT - Request {request_id}: "
                    f"IP={client_ip}, Method={method}, Path={path}, "
                    f"Status={status_code}"
                )

        except Exception as e:
            logger.error(f"Error logging security metrics: {str(e)}")


class DDoSProtectionMiddleware(BaseHTTPMiddleware):
    """
    DDoS Protection Middleware

    Features:
    - Request rate limiting per IP
    - Burst detection
    - Automatic IP blocking
    - Attack pattern recognition
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        burst_threshold: int = 20,
        block_duration: int = 300,  # 5 minutes
        enable_auto_block: bool = True,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_threshold = burst_threshold
        self.block_duration = block_duration
        self.enable_auto_block = enable_auto_block

        # In-memory tracking (use Redis in production)
        self.request_counts = {}
        self.blocked_ips = {}
        self.burst_detection = {}

    async def dispatch(self, request: Request, call_next):
        """Check for DDoS patterns and block if necessary"""

        client_ip = request.client.host if request.client else "unknown"
        current_time = datetime.utcnow().timestamp()

        # Check if IP is blocked
        if self._is_ip_blocked(client_ip, current_time):
            logger.warning(f"Blocked DDoS attempt from {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests", "retry_after": self.block_duration},
                headers={"Retry-After": str(self.block_duration)},
            )

        # Track request
        if self._should_block_ip(client_ip, current_time):
            if self.enable_auto_block:
                self._block_ip(client_ip, current_time)
                logger.warning(f"Auto-blocked IP {client_ip} for DDoS patterns")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "DDoS protection triggered",
                        "retry_after": self.block_duration,
                    },
                    headers={"Retry-After": str(self.block_duration)},
                )

        return await call_next(request)

    def _is_ip_blocked(self, ip: str, current_time: float) -> bool:
        """Check if IP is currently blocked"""

        if ip not in self.blocked_ips:
            return False

        block_time, duration = self.blocked_ips[ip]
        if current_time - block_time > duration:
            # Block expired, remove it
            del self.blocked_ips[ip]
            return False

        return True

    def _should_block_ip(self, ip: str, current_time: float) -> bool:
        """Determine if IP should be blocked based on request patterns"""

        # Initialize tracking for new IPs
        if ip not in self.request_counts:
            self.request_counts[ip] = []
            self.burst_detection[ip] = []

        # Clean old requests (older than 1 minute)
        self.request_counts[ip] = [
            req_time for req_time in self.request_counts[ip] if current_time - req_time < 60
        ]

        # Clean old burst detection (older than 10 seconds)
        self.burst_detection[ip] = [
            req_time for req_time in self.burst_detection[ip] if current_time - req_time < 10
        ]

        # Add current request
        self.request_counts[ip].append(current_time)
        self.burst_detection[ip].append(current_time)

        # Check rate limit
        if len(self.request_counts[ip]) > self.requests_per_minute:
            return True

        # Check burst threshold
        if len(self.burst_detection[ip]) > self.burst_threshold:
            return True

        return False

    def _block_ip(self, ip: str, current_time: float):
        """Block an IP address"""

        self.blocked_ips[ip] = (current_time, self.block_duration)

        # Log the blocking event
        logger.warning(
            f"DDoS_PROTECTION - Blocked IP {ip} for {self.block_duration} seconds. "
            f"Rate: {len(self.request_counts.get(ip, []))} req/min, "
            f"Burst: {len(self.burst_detection.get(ip, []))} req/10s"
        )


def create_security_middleware(
    environment: str = "production",
    allowed_origins: List[str] = None,
    enable_ddos_protection: bool = True,
    **kwargs,
) -> List[BaseHTTPMiddleware]:
    """
    Create security middleware stack

    Returns list of middleware to add to FastAPI app
    """

    middleware_stack = []

    # Security Headers Middleware
    middleware_stack.append(
        SecurityHeadersMiddleware(
            environment=environment, allowed_origins=allowed_origins, **kwargs
        )
    )

    # DDoS Protection Middleware
    if enable_ddos_protection:
        middleware_stack.append(
            DDoSProtectionMiddleware(
                requests_per_minute=100 if environment == "production" else 1000,
                burst_threshold=30 if environment == "production" else 100,
                enable_auto_block=environment == "production",
            )
        )

    return middleware_stack
