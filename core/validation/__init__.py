"""
ToolBoxAI Roblox Lua Script Validation System

Comprehensive validation framework for Roblox Lua scripts in the educational platform.
Provides syntax checking, security analysis, educational content validation, and quality assessment.
"""

from .lua_validator import LuaScriptValidator
from .security_analyzer import SecurityAnalyzer
from .educational_validator import EducationalContentValidator
from .quality_checker import CodeQualityChecker
from .roblox_compliance import RobloxComplianceChecker
from .validation_engine import ValidationEngine

__all__ = [
    'LuaScriptValidator',
    'SecurityAnalyzer',
    'EducationalContentValidator',
    'CodeQualityChecker',
    'RobloxComplianceChecker',
    'ValidationEngine'
]

__version__ = "1.0.0"