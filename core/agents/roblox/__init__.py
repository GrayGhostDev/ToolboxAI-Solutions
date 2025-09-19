"""
Roblox Agent Suite for Educational Platform Integration

A comprehensive suite of specialized agents for managing
Roblox educational content, security, optimization, and analytics.
"""

from .roblox_content_generation_agent import (
    RobloxContentGenerationAgent,
    RobloxAsset,
    GenerationRequest
)
from .roblox_script_optimization_agent import (
    RobloxScriptOptimizationAgent,
    OptimizationLevel,
    PerformanceIssue,
    OptimizationResult
)
from .roblox_security_validation_agent import (
    RobloxSecurityValidationAgent,
    ThreatLevel,
    VulnerabilityType,
    SecurityVulnerability,
    SecurityReport
)

__all__ = [
    "RobloxContentGenerationAgent",
    "RobloxScriptOptimizationAgent",
    "RobloxSecurityValidationAgent",
    "RobloxAsset",
    "GenerationRequest",
    "OptimizationLevel",
    "PerformanceIssue",
    "OptimizationResult",
    "ThreatLevel",
    "VulnerabilityType",
    "SecurityVulnerability",
    "SecurityReport",
]

# Version info
__version__ = "1.0.0"
__author__ = "ToolBoxAI Solutions"
