"""
Lua Script Syntax and Semantic Validator

Validates Lua script syntax, checks for semantic errors, and ensures
Roblox API compatibility.
"""

import logging
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ValidationSeverity(Enum):
    """Validation issue severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in Lua code"""

    severity: ValidationSeverity
    line: int
    column: int
    message: str
    rule: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of Lua script validation"""

    success: bool
    issues: list[ValidationIssue]
    syntax_valid: bool
    api_compatible: bool
    performance_score: float
    memory_score: float
    complexity_score: float
    total_lines: int
    function_count: int
    variable_count: int


class LuaScriptValidator:
    """
    Comprehensive Lua script validator for Roblox educational content
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Roblox API services and methods
        self.roblox_services = {
            "workspace",
            "game",
            "Players",
            "ReplicatedStorage",
            "ReplicatedFirst",
            "ServerScriptService",
            "ServerStorage",
            "StarterGui",
            "StarterPack",
            "StarterPlayer",
            "Lighting",
            "SoundService",
            "TweenService",
            "RunService",
            "UserInputService",
            "ContextActionService",
            "GuiService",
            "PathfindingService",
            "DataStoreService",
            "HttpService",
            "TeleportService",
            "MessagingService",
            "MarketplaceService",
            "BadgeService",
            "GroupService",
            "Teams",
            "Debris",
            "Chat",
            "TextService",
        }

        # Dangerous patterns that should be avoided
        self.dangerous_patterns = {
            r"getfenv\s*\(": "getfenv can be used for exploiting",
            r"setfenv\s*\(": "setfenv can be used for exploiting",
            r"loadstring\s*\(": "loadstring can execute arbitrary code",
            r"debug\.": "Debug library can be exploited",
            r"_G\s*\[": "Global table manipulation can be dangerous",
            r"while\s+true\s+do\s*$": "Infinite loop without yield detected",
            r"for\s+.*\s+do\s*$": "Potential infinite loop without yield",
            r"repeat\s*$": "Potential infinite loop without yield",
            r"rawget\s*\(": "Raw table access can bypass metamethods",
            r"rawset\s*\(": "Raw table modification can bypass metamethods",
        }

        # Performance warning patterns
        self.performance_patterns = {
            r"pairs\s*\(\s*workspace\s*\)": "Iterating workspace children can be expensive",
            r"workspace:GetChildren\s*\(\s*\)": "GetChildren() on workspace can be expensive",
            r"workspace:GetDescendants\s*\(\s*\)": "GetDescendants() on workspace is very expensive",
            r"game\.Players:GetPlayers\s*\(\s*\)": "GetPlayers() should be cached if used repeatedly",
            r"while\s+.*\s+do(?!.*wait)": "Loop without wait() may cause lag",
            r"for\s+.*\s+do(?!.*wait)": "Long loop without wait() may cause lag",
        }

        # Memory leak patterns
        self.memory_patterns = {
            r"\.Changed:Connect\s*\(": "Event connections should be stored and disconnected",
            r"\.Touched:Connect\s*\(": "Touched events should be properly managed",
            r"RunService\..*:Connect\s*\(": "RunService connections should be disconnected",
            r"UserInputService\..*:Connect\s*\(": "Input connections should be managed",
            r"while\s+true.*spawn\s*\(": "Spawning in infinite loops can cause memory leaks",
        }

        # Roblox-specific syntax patterns
        self.roblox_patterns = {
            r'game:GetService\s*\(\s*["\'](\w+)["\']\s*\)': "Valid service access",
            r"script\.Parent": "Valid script parent access",
            r"workspace\.(\w+)": "Workspace child access",
            r'Instance\.new\s*\(\s*["\'](\w+)["\']\s*\)': "Instance creation",
        }

    def validate_script(self, lua_code: str, script_name: str = "unknown") -> ValidationResult:
        """
        Main validation method that runs all checks on Lua code

        Args:
            lua_code: The Lua code to validate
            script_name: Name of the script for reporting

        Returns:
            ValidationResult with all findings
        """
        issues = []

        # Basic validation
        if not lua_code or not lua_code.strip():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    line=1,
                    column=1,
                    message="Script is empty",
                    rule="empty_script",
                )
            )
            return ValidationResult(
                success=False,
                issues=issues,
                syntax_valid=False,
                api_compatible=False,
                performance_score=0.0,
                memory_score=0.0,
                complexity_score=0.0,
                total_lines=0,
                function_count=0,
                variable_count=0,
            )

        # Syntax validation
        syntax_valid = self._validate_syntax(lua_code, issues)

        # Semantic validation
        self._validate_semantics(lua_code, issues)

        # Roblox API validation
        api_compatible = self._validate_roblox_api(lua_code, issues)

        # Security validation
        self._validate_security(lua_code, issues)

        # Performance validation
        performance_score = self._validate_performance(lua_code, issues)

        # Memory validation
        memory_score = self._validate_memory_usage(lua_code, issues)

        # Code metrics
        metrics = self._calculate_metrics(lua_code)
        complexity_score = self._calculate_complexity(lua_code)

        # Determine overall success
        has_errors = any(
            issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
            for issue in issues
        )

        return ValidationResult(
            success=not has_errors,
            issues=issues,
            syntax_valid=syntax_valid,
            api_compatible=api_compatible,
            performance_score=performance_score,
            memory_score=memory_score,
            complexity_score=complexity_score,
            total_lines=metrics["lines"],
            function_count=metrics["functions"],
            variable_count=metrics["variables"],
        )

    def _validate_syntax(self, lua_code: str, issues: list[ValidationIssue]) -> bool:
        """
        Validate Lua syntax using luac if available, otherwise basic pattern matching
        """
        try:
            # Try using luac if available (this would need luac installed)
            with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as temp_file:
                temp_file.write(lua_code)
                temp_file.flush()

                try:
                    result = subprocess.run(
                        ["luac", "-p", temp_file.name],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )

                    if result.returncode != 0:
                        # Parse luac error output
                        error_lines = result.stderr.strip().split("\n")
                        for error_line in error_lines:
                            match = re.search(r"(\d+):\s*(.+)", error_line)
                            if match:
                                line_num = int(match.group(1))
                                error_msg = match.group(2)
                                issues.append(
                                    ValidationIssue(
                                        severity=ValidationSeverity.ERROR,
                                        line=line_num,
                                        column=1,
                                        message=f"Syntax error: {error_msg}",
                                        rule="syntax_error",
                                    )
                                )
                        return False

                finally:
                    os.unlink(temp_file.name)

        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Fallback to basic syntax checking
            return self._basic_syntax_check(lua_code, issues)

        return True

    def _basic_syntax_check(self, lua_code: str, issues: list[ValidationIssue]) -> bool:
        """
        Basic syntax checking using pattern matching
        """
        lines = lua_code.split("\n")
        syntax_valid = True

        # Track block structures
        block_stack = []

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("--"):
                continue

            # Check for unmatched brackets
            open_brackets = line.count("(") - line.count(")")
            open_square = line.count("[") - line.count("]")
            open_curly = line.count("{") - line.count("}")

            if open_brackets < 0 or open_square < 0 or open_curly < 0:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        line=line_num,
                        column=1,
                        message="Unmatched closing bracket",
                        rule="unmatched_bracket",
                    )
                )
                syntax_valid = False

            # Check block structures
            if re.search(r"\b(function|if|for|while|repeat|do)\b", line):
                if not line.endswith("end") and "then" not in line and "do" not in line:
                    block_stack.append(line_num)

            if line.endswith("end"):
                if not block_stack:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            line=line_num,
                            column=1,
                            message="Unexpected 'end' statement",
                            rule="unexpected_end",
                        )
                    )
                    syntax_valid = False
                else:
                    block_stack.pop()

        # Check for unclosed blocks
        if block_stack:
            for block_line in block_stack:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        line=block_line,
                        column=1,
                        message="Unclosed block statement",
                        rule="unclosed_block",
                    )
                )
            syntax_valid = False

        return syntax_valid

    def _validate_semantics(self, lua_code: str, issues: list[ValidationIssue]):
        """
        Validate semantic correctness
        """
        lines = lua_code.split("\n")

        # Track variable declarations and usage
        declared_vars = set()
        used_vars = set()

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Skip comments
            if line.startswith("--"):
                continue

            # Check for variable declarations
            var_declarations = re.findall(r"local\s+(\w+)", line)
            declared_vars.update(var_declarations)

            # Check for variable usage
            var_usage = re.findall(r"\b(\w+)\s*[=<>!~]", line)
            used_vars.update(var_usage)

            # Check for undefined variables (basic check)
            undefined_vars = re.findall(r"\b([a-zA-Z_]\w*)\s*\(", line)
            for var in undefined_vars:
                if var not in declared_vars and var not in self.roblox_services:
                    if not any(service in var for service in self.roblox_services):
                        issues.append(
                            ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                line=line_num,
                                column=line.find(var) + 1,
                                message=f"Potentially undefined function: {var}",
                                rule="undefined_function",
                                suggestion=f"Ensure {var} is defined or check spelling",
                            )
                        )

    def _validate_roblox_api(self, lua_code: str, issues: list[ValidationIssue]) -> bool:
        """
        Validate Roblox API usage
        """
        lines = lua_code.split("\n")
        api_compatible = True

        for line_num, line in enumerate(lines, 1):
            # Check for deprecated API usage
            deprecated_apis = {
                "workspace.Name": "Use workspace directly instead of workspace.Name",
                "game.Workspace": "Use workspace instead of game.Workspace",
                "game.Players.LocalPlayer": "Only use in LocalScripts",
                "script.LocalPlayer": "Use Players.LocalPlayer instead",
                "wait()": "Consider using task.wait() instead of wait()",
                "spawn()": "Consider using task.spawn() instead of spawn()",
                "delay()": "Consider using task.delay() instead of delay()",
            }

            for deprecated, suggestion in deprecated_apis.items():
                if deprecated in line:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            line=line_num,
                            column=line.find(deprecated) + 1,
                            message=f"Deprecated API usage: {deprecated}",
                            rule="deprecated_api",
                            suggestion=suggestion,
                        )
                    )

            # Check for proper service usage
            service_pattern = r'game:GetService\s*\(\s*["\'](\w+)["\']\s*\)'
            matches = re.finditer(service_pattern, line)
            for match in matches:
                service_name = match.group(1)
                if service_name not in self.roblox_services:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            line=line_num,
                            column=match.start() + 1,
                            message=f"Invalid Roblox service: {service_name}",
                            rule="invalid_service",
                        )
                    )
                    api_compatible = False

        return api_compatible

    def _validate_security(self, lua_code: str, issues: list[ValidationIssue]):
        """
        Check for security vulnerabilities
        """
        lines = lua_code.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pattern, message in self.dangerous_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.CRITICAL,
                            line=line_num,
                            column=1,
                            message=message,
                            rule="security_risk",
                            suggestion="Remove or replace with safe alternative",
                        )
                    )

    def _validate_performance(self, lua_code: str, issues: list[ValidationIssue]) -> float:
        """
        Check for performance issues and return performance score (0-100)
        """
        lines = lua_code.split("\n")
        performance_issues = 0
        total_checks = len(self.performance_patterns)

        for line_num, line in enumerate(lines, 1):
            for pattern, message in self.performance_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            line=line_num,
                            column=1,
                            message=message,
                            rule="performance_warning",
                            suggestion="Consider optimizing this operation",
                        )
                    )
                    performance_issues += 1

        # Calculate performance score
        if total_checks == 0:
            return 100.0

        performance_score = max(0, 100 - (performance_issues * 10))
        return performance_score

    def _validate_memory_usage(self, lua_code: str, issues: list[ValidationIssue]) -> float:
        """
        Check for memory leak patterns and return memory score (0-100)
        """
        lines = lua_code.split("\n")
        memory_issues = 0

        for line_num, line in enumerate(lines, 1):
            for pattern, message in self.memory_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            line=line_num,
                            column=1,
                            message=message,
                            rule="memory_warning",
                            suggestion="Store connection and disconnect when done",
                        )
                    )
                    memory_issues += 1

        # Check for proper disconnection patterns
        has_disconnects = bool(re.search(r"\.Disconnect\s*\(\s*\)", lua_code, re.IGNORECASE))
        if not has_disconnects and memory_issues > 0:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    line=1,
                    column=1,
                    message="Event connections found but no disconnection code detected",
                    rule="missing_disconnect",
                    suggestion="Add connection:Disconnect() when appropriate",
                )
            )

        memory_score = max(0, 100 - (memory_issues * 15))
        return memory_score

    def _calculate_metrics(self, lua_code: str) -> dict[str, int]:
        """
        Calculate basic code metrics
        """
        lines = lua_code.split("\n")
        non_empty_lines = [
            line for line in lines if line.strip() and not line.strip().startswith("--")
        ]

        function_count = len(re.findall(r"\bfunction\b", lua_code, re.IGNORECASE))
        local_var_count = len(re.findall(r"\blocal\s+\w+", lua_code, re.IGNORECASE))

        return {
            "lines": len(non_empty_lines),
            "functions": function_count,
            "variables": local_var_count,
        }

    def _calculate_complexity(self, lua_code: str) -> float:
        """
        Calculate cyclomatic complexity score (0-100, lower is better)
        """
        # Count decision points
        decision_keywords = [
            r"\bif\b",
            r"\belseif\b",
            r"\bwhile\b",
            r"\bfor\b",
            r"\brepeat\b",
            r"\band\b",
            r"\bor\b",
        ]

        complexity = 1  # Base complexity

        for keyword in decision_keywords:
            complexity += len(re.findall(keyword, lua_code, re.IGNORECASE))

        # Normalize to 0-100 scale (10+ complexity points = 100 complexity score)
        complexity_score = min(100, complexity * 10)

        return complexity_score

    def generate_fix_suggestions(self, issues: list[ValidationIssue]) -> list[str]:
        """
        Generate automatic fix suggestions for common issues
        """
        suggestions = []

        for issue in issues:
            if issue.rule == "deprecated_api" and "wait()" in issue.message:
                suggestions.append("Replace wait() with task.wait() for better performance")
            elif issue.rule == "performance_warning" and "workspace" in issue.message:
                suggestions.append("Cache workspace references or use more specific selectors")
            elif issue.rule == "memory_warning":
                suggestions.append(
                    "Store event connections and disconnect them when no longer needed"
                )
            elif issue.rule == "security_risk":
                suggestions.append(
                    "Remove dangerous function calls or replace with safe alternatives"
                )

        return list(set(suggestions))  # Remove duplicates
