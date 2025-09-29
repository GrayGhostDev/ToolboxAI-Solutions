"""
Enhanced CORS Security Configuration for ToolBoxAI Solutions
Replaces wildcard CORS with environment-specific allowed origins
"""

import os
import logging
from typing import List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CORSConfig:
    """
    Manages CORS configuration with security best practices
    No wildcard origins allowed in production
    """

    def __init__(self, environment: str = None):
        """
        Initialize CORS configuration

        Args:
            environment: Environment name (development, staging, production)
        """
        self.environment = environment or os.getenv("ENV", "development").lower()
        self._allowed_origins = None
        self._allowed_methods = None
        self._allowed_headers = None

    @property
    def allowed_origins(self) -> List[str]:
        """Get allowed origins based on environment"""
        if self._allowed_origins is None:
            self._allowed_origins = self._get_allowed_origins()
        return self._allowed_origins

    @property
    def allowed_methods(self) -> List[str]:
        """Get allowed HTTP methods"""
        if self._allowed_methods is None:
            self._allowed_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
        return self._allowed_methods

    @property
    def allowed_headers(self) -> List[str]:
        """Get allowed headers"""
        if self._allowed_headers is None:
            self._allowed_headers = [
                "Content-Type",
                "Authorization",
                "X-Requested-With",
                "Accept",
                "Origin",
                "Access-Control-Request-Method",
                "Access-Control-Request-Headers",
                "X-CSRF-Token",
            ]
        return self._allowed_headers

    def _get_allowed_origins(self) -> List[str]:
        """
        Get allowed origins based on environment
        NEVER use wildcards in production
        """
        # First, check for explicit ALLOWED_ORIGINS environment variable
        env_origins = os.getenv("ALLOWED_ORIGINS", "")
        if env_origins and env_origins != "*":
            origins = [
                origin.strip()
                for origin in env_origins.split(",")
                if origin.strip() and origin.strip() != "*"
            ]
            if origins:
                logger.info(f"Using explicit allowed origins from environment: {origins}")
                return origins

        # Environment-specific defaults
        if self.environment in ("production", "prod"):
            # Production: Only specific domains
            origins = [
                "https://app.toolboxai.solutions",
                "https://toolboxai.solutions",
                "https://www.toolboxai.solutions",
                "https://dashboard.toolboxai.solutions",
                "https://api.toolboxai.solutions",
            ]

            # Add CloudFront distribution if configured
            cloudfront_domain = os.getenv("CLOUDFRONT_DOMAIN")
            if cloudfront_domain:
                origins.append(f"https://{cloudfront_domain}")

        elif self.environment in ("staging", "stage"):
            # Staging: Staging domains and some development access
            origins = [
                "https://staging.toolboxai.solutions",
                "https://staging-app.toolboxai.solutions",
                "https://staging-dashboard.toolboxai.solutions",
                "http://localhost:3000",  # For testing from local
                "http://localhost:5173",
                "http://localhost:5179",
            ]

        else:
            # Development: Local development origins
            origins = []

            # Common development ports
            dev_ports = [
                3000,  # React default
                5173,  # Vite default
                5174,  # Vite alternate
                5175,  # Vite alternate
                5176,  # Vite alternate
                5177,  # Vite alternate
                5178,  # Vite alternate
                5179,  # Dashboard current port
                5180,  # Dashboard alternate
                8008,  # Backend FastAPI
                8009,  # Backend alternate
            ]

            # Add localhost and 127.0.0.1 for each port
            for port in dev_ports:
                origins.extend([f"http://localhost:{port}", f"http://127.0.0.1:{port}"])

            # Add custom development domain if set
            dev_domain = os.getenv("DEV_DOMAIN")
            if dev_domain:
                origins.append(f"http://{dev_domain}")
                origins.append(f"https://{dev_domain}")

        # Log the configuration
        logger.info(f"CORS configuration for {self.environment} environment:")
        logger.info(f"  Allowed origins: {len(origins)} domains")

        if self.environment in ("production", "prod"):
            logger.info("  Production CORS security enabled - no wildcards")
        elif self.environment in ("development", "dev"):
            logger.info("  Development CORS - local origins allowed")

        return origins

    def is_origin_allowed(self, origin: str) -> bool:
        """
        Check if an origin is allowed

        Args:
            origin: Origin to check

        Returns:
            True if origin is allowed, False otherwise
        """
        if not origin:
            return False

        # Never allow wildcard in production
        if origin == "*" and self.environment in ("production", "prod"):
            logger.warning(f"Wildcard origin blocked in production")
            return False

        # Check against allowed origins
        allowed = origin in self.allowed_origins

        if not allowed:
            # Try to parse and check without trailing slash
            try:
                parsed = urlparse(origin)
                origin_no_slash = f"{parsed.scheme}://{parsed.netloc}"
                allowed = origin_no_slash in self.allowed_origins
            except Exception:
                pass

        if not allowed:
            logger.warning(f"CORS request from unauthorized origin: {origin}")

        return allowed

    def get_cors_options(self) -> dict:
        """
        Get CORS options for FastAPI CORSMiddleware

        Returns:
            Dictionary of CORS options
        """
        return {
            "allow_origins": self.allowed_origins,
            "allow_credentials": True,
            "allow_methods": self.allowed_methods,
            "allow_headers": self.allowed_headers,
            "expose_headers": ["Content-Length", "X-Request-ID", "X-Process-Time"],
            "max_age": 3600,  # Cache preflight requests for 1 hour
        }

    def get_cors_headers(self, origin: str = None) -> dict:
        """
        Get CORS headers for manual response

        Args:
            origin: Request origin

        Returns:
            Dictionary of CORS headers
        """
        headers = {}

        if origin and self.is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
            headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
            headers["Access-Control-Max-Age"] = "3600"

        return headers

    def validate_configuration(self) -> bool:
        """
        Validate CORS configuration for security issues

        Returns:
            True if configuration is secure, False otherwise
        """
        issues = []

        # Check for wildcards in production
        if self.environment in ("production", "prod"):
            if "*" in self.allowed_origins:
                issues.append("Wildcard origin (*) found in production configuration")

            for origin in self.allowed_origins:
                # Check for HTTP in production
                if origin.startswith("http://") and "localhost" not in origin:
                    issues.append(f"Insecure HTTP origin in production: {origin}")

        # Check for empty origins
        if not self.allowed_origins:
            issues.append("No allowed origins configured")

        # Check for suspicious patterns
        for origin in self.allowed_origins:
            if origin.endswith("."):
                issues.append(f"Invalid origin with trailing dot: {origin}")
            if " " in origin:
                issues.append(f"Origin contains whitespace: {origin}")

        # Log issues
        if issues:
            for issue in issues:
                logger.error(f"CORS Security Issue: {issue}")
            return False

        logger.info("CORS configuration validation passed")
        return True


# Singleton instance
_cors_config = None


def get_cors_config() -> CORSConfig:
    """Get or create the global CORS configuration instance"""
    global _cors_config
    if _cors_config is None:
        _cors_config = CORSConfig()
        # Validate on creation
        if not _cors_config.validate_configuration():
            logger.warning("CORS configuration has security issues")
    return _cors_config


def apply_cors_to_app(app):
    """
    Apply CORS configuration to FastAPI app

    Args:
        app: FastAPI application instance
    """
    from fastapi.middleware.cors import CORSMiddleware

    cors_config = get_cors_config()

    # Remove any existing CORS middleware
    app.middleware_stack = [m for m in app.middleware_stack if not isinstance(m, CORSMiddleware)]

    # Add CORS middleware with secure configuration
    app.add_middleware(CORSMiddleware, **cors_config.get_cors_options())

    logger.info(f"Applied secure CORS configuration to app")
    logger.info(f"  Environment: {cors_config.environment}")
    logger.info(f"  Allowed origins: {len(cors_config.allowed_origins)}")

    return app
