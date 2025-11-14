"""
ToolBoxAI Security Agent Framework
=================================

Comprehensive security monitoring system with specialized sub-agents
for continuous security validation during Phase 1.5 fixes.

Architecture:
- Sub-Agent 1: Vulnerability Scanner (Real-time scanning)
- Sub-Agent 2: Compliance Checker (OWASP 2025 validation)
- Sub-Agent 3: Secret Rotator (Automated key rotation)

Security Score Target: Maintain 95%+ at all times
"""

from .compliance_checker import ComplianceChecker
from .secret_rotator import SecretRotator
from .security_coordinator import SecurityCoordinator
from .vulnerability_scanner import VulnerabilityScanner

__version__ = "1.0.0"
__author__ = "ToolBoxAI Security Team"

# Security monitoring exports
__all__ = [
    "VulnerabilityScanner",
    "ComplianceChecker",
    "SecretRotator",
    "SecurityCoordinator",
]
