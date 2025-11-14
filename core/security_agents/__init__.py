"""Compatibility layer for legacy security agent imports.

The previous implementation placed the security agents under
``core.security``. After introducing the lightweight stubs for the
pre-commit hook, the canonical entry point moved to
``core.security_compliance_stub``. This module re-exports the stub classes so
existing imports (``from core.security_agents import ...``) continue to work.
"""

from core.security_compliance_stub import (  # noqa: F401
    ComplianceChecker,
    SecretRotator,
    SecurityCoordinator,
    VulnerabilityScanner,
)

__all__ = [
    "VulnerabilityScanner",
    "ComplianceChecker",
    "SecretRotator",
    "SecurityCoordinator",
]
