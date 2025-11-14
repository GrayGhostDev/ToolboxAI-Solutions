"""
Code Quality Checker for Roblox Lua Scripts

Enforces coding standards, checks for best practices,
and provides quality metrics for educational content.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class QualityLevel(Enum):
    """Code quality levels"""

    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"  # 70-89
    FAIR = "fair"  # 50-69
    POOR = "poor"  # 30-49
    UNACCEPTABLE = "unacceptable"  # 0-29


@dataclass
class QualityIssue:
    """Represents a code quality issue"""

    severity: str  # 'info', 'warning', 'error'
    line_number: int
    column: int
    rule: str
    message: str
    suggestion: Optional[str] = None
    impact: str = "maintainability"  # maintainability, performance, readability


@dataclass
class QualityMetrics:
    """Code quality metrics"""

    lines_of_code: int
    logical_lines: int
    comment_lines: int
    blank_lines: int
    function_count: int
    complexity_score: float
    maintainability_score: float
    readability_score: float
    documentation_score: float
    test_coverage: float


@dataclass
class QualityReport:
    """Complete code quality report"""

    overall_score: float
    quality_level: QualityLevel
    metrics: QualityMetrics
    issues: list[QualityIssue]
    recommendations: list[str]
    best_practices_followed: list[str]
    areas_for_improvement: list[str]


class CodeQualityChecker:
    """
    Comprehensive code quality checker for Roblox Lua scripts
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Naming convention patterns
        self.naming_patterns = {
            "variable_camelCase": r"^[a-z][a-zA-Z0-9]*$",
            "constant_UPPER": r"^[A-Z][A-Z0-9_]*$",
            "function_camelCase": r"^[a-z][a-zA-Z0-9]*$",
            "class_PascalCase": r"^[A-Z][a-zA-Z0-9]*$",
            "private_underscore": r"^_[a-zA-Z0-9]*$",
        }

        # Code smell patterns
        self.code_smells = {
            "long_function": {
                "pattern": r"function\s+\w+.*?end",
                "threshold": 50,  # lines
                "message": "Function is too long and should be split",
            },
            "deep_nesting": {
                "pattern": r"(\s+if\s+.*then\s+.*if\s+.*then\s+.*if)",
                "threshold": 3,
                "message": "Too many nested conditions, consider refactoring",
            },
            "magic_numbers": {
                "pattern": r"\b(?<![\w\.])\d{2,}\b(?![\w\.])",
                "threshold": 3,
                "message": "Magic numbers should be replaced with named constants",
            },
            "duplicate_code": {
                "pattern": r"(.{20,}?).*?\1",
                "threshold": 2,
                "message": "Duplicate code detected, consider extracting to function",
            },
        }

        # Best practice patterns
        self.best_practices = {
            "error_handling": [
                r"pcall\s*\(",
                r"xpcall\s*\(",
                r"if\s+.*error.*then",
                r"local\s+success,\s*result",
            ],
            "proper_comments": [
                r"--\s+[A-Z].*",  # Comments starting with capital letter
                r"--\[\[.*\]\]",  # Block comments
                r"--\s+TODO:",  # TODO comments
                r"--\s+FIXME:",  # FIXME comments
            ],
            "local_variables": [r"local\s+\w+\s*=", r"local\s+function"],
            "service_caching": [
                r"local\s+\w+\s*=\s*game:GetService",
                r"local\s+.*Service\s*=",
            ],
            "connection_management": [
                r"\.Disconnect\s*\(\s*\)",
                r"connection\s*=.*:Connect",
                r"local\s+connection",
            ],
        }

        # Performance anti-patterns
        self.performance_issues = {
            "expensive_operations": [
                r"workspace:GetDescendants\s*\(\s*\)",
                r"for\s+.*in\s+pairs\s*\(\s*workspace\s*\)",
                r"while\s+true\s+do(?!.*wait)",
                r"repeat(?!.*wait).*until",
            ],
            "inefficient_patterns": [
                r"table\.insert\s*\(.*#.*\)",  # Inefficient table insertion
                r"string\..*\s*\.\.\s*string\.",  # String concatenation in loop
                r"game\.Players:GetPlayers\s*\(\s*\)\s*\[",  # Direct indexing of GetPlayers
            ],
        }

        # Documentation patterns
        self.documentation_patterns = {
            "function_docs": r"--\[\[.*?\]\]\s*function",
            "module_header": r"--\[\[.*?Module.*?\]\]",
            "parameter_docs": r"--\s*@param",
            "return_docs": r"--\s*@return",
            "example_docs": r"--\s*@example",
        }

        # Roblox-specific best practices
        self.roblox_patterns = {
            "proper_service_usage": [
                r'game:GetService\s*\(\s*["\'][^"\']+["\']\s*\)',
                r"local\s+.*=\s*game:GetService",
            ],
            "wait_usage": [
                r"task\.wait\s*\(",
                r"wait\s*\(\s*[0-9.]+\s*\)",  # wait with explicit time
                r"RunService\.Heartbeat:Wait\s*\(\s*\)",
            ],
            "instance_creation": [
                r'Instance\.new\s*\(\s*["\'][^"\']+["\']\s*\)',
                r"local\s+.*=\s*Instance\.new",
            ],
        }

    def check_quality(self, lua_code: str, script_name: str = "unknown") -> QualityReport:
        """
        Perform comprehensive quality check on Lua code

        Args:
            lua_code: The Lua code to check
            script_name: Name of the script for reporting

        Returns:
            QualityReport with quality assessment
        """
        issues = []

        # Calculate basic metrics
        metrics = self._calculate_metrics(lua_code)

        # Check coding standards
        self._check_naming_conventions(lua_code, issues)
        self._check_code_smells(lua_code, issues)
        self._check_performance_issues(lua_code, issues)

        # Check best practices
        best_practices = self._check_best_practices(lua_code, issues)

        # Check Roblox-specific practices
        self._check_roblox_practices(lua_code, issues)

        # Calculate quality scores
        complexity_score = self._calculate_complexity_score(lua_code)
        maintainability_score = self._calculate_maintainability_score(lua_code, issues)
        readability_score = self._calculate_readability_score(lua_code, issues)
        documentation_score = self._calculate_documentation_score(lua_code)

        # Update metrics
        metrics.complexity_score = complexity_score
        metrics.maintainability_score = maintainability_score
        metrics.readability_score = readability_score
        metrics.documentation_score = documentation_score

        # Calculate overall score
        overall_score = self._calculate_overall_score(metrics, issues)

        # Determine quality level
        quality_level = self._determine_quality_level(overall_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(issues, metrics, best_practices)

        # Identify areas for improvement
        areas_for_improvement = self._identify_improvement_areas(issues)

        return QualityReport(
            overall_score=overall_score,
            quality_level=quality_level,
            metrics=metrics,
            issues=issues,
            recommendations=recommendations,
            best_practices_followed=best_practices,
            areas_for_improvement=areas_for_improvement,
        )

    def _calculate_metrics(self, lua_code: str) -> QualityMetrics:
        """Calculate basic code metrics"""
        lines = lua_code.split("\n")

        total_lines = len(lines)
        logical_lines = 0
        comment_lines = 0
        blank_lines = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith("--"):
                comment_lines += 1
            else:
                logical_lines += 1

        # Count functions
        function_count = len(re.findall(r"\bfunction\b", lua_code, re.IGNORECASE))

        # Mock test coverage (would need actual test analysis)
        test_coverage = 0.0

        return QualityMetrics(
            lines_of_code=total_lines,
            logical_lines=logical_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=function_count,
            complexity_score=0,  # Will be calculated separately
            maintainability_score=0,  # Will be calculated separately
            readability_score=0,  # Will be calculated separately
            documentation_score=0,  # Will be calculated separately
            test_coverage=test_coverage,
        )

    def _check_naming_conventions(self, lua_code: str, issues: list[QualityIssue]):
        """Check naming convention compliance"""
        lines = lua_code.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Check variable declarations
            var_matches = re.finditer(r"local\s+([a-zA-Z_]\w*)\s*=", line)
            for match in var_matches:
                var_name = match.group(1)

                # Check if it's a constant (all uppercase)
                if var_name.isupper():
                    if not re.match(self.naming_patterns["constant_UPPER"], var_name):
                        issues.append(
                            QualityIssue(
                                severity="warning",
                                line_number=line_num,
                                column=match.start(1),
                                rule="naming_conventions",
                                message=f"Constant '{var_name}' should follow UPPER_CASE convention",
                                suggestion=f"Rename to follow UPPER_CASE pattern",
                                impact="readability",
                            )
                        )
                # Check if it's a private variable (starts with _)
                elif var_name.startswith("_"):
                    if not re.match(self.naming_patterns["private_underscore"], var_name):
                        issues.append(
                            QualityIssue(
                                severity="info",
                                line_number=line_num,
                                column=match.start(1),
                                rule="naming_conventions",
                                message=f"Private variable '{var_name}' naming could be improved",
                                suggestion="Use clear, descriptive names even for private variables",
                                impact="readability",
                            )
                        )
                # Regular variable
                else:
                    if not re.match(self.naming_patterns["variable_camelCase"], var_name):
                        issues.append(
                            QualityIssue(
                                severity="info",
                                line_number=line_num,
                                column=match.start(1),
                                rule="naming_conventions",
                                message=f"Variable '{var_name}' should follow camelCase convention",
                                suggestion=f"Consider renaming to camelCase",
                                impact="readability",
                            )
                        )

            # Check function declarations
            func_matches = re.finditer(r"function\s+([a-zA-Z_]\w*)\s*\(", line)
            for match in func_matches:
                func_name = match.group(1)
                if not re.match(self.naming_patterns["function_camelCase"], func_name):
                    issues.append(
                        QualityIssue(
                            severity="warning",
                            line_number=line_num,
                            column=match.start(1),
                            rule="naming_conventions",
                            message=f"Function '{func_name}' should follow camelCase convention",
                            suggestion="Use camelCase for function names",
                            impact="readability",
                        )
                    )

    def _check_code_smells(self, lua_code: str, issues: list[QualityIssue]):
        """Check for code smells"""
        lines = lua_code.split("\n")

        # Check for long functions
        function_pattern = r"function\s+\w+.*?end"
        function_matches = re.finditer(function_pattern, lua_code, re.DOTALL | re.IGNORECASE)

        for match in function_matches:
            function_code = match.group(0)
            function_lines = function_code.count("\n") + 1

            if function_lines > 50:
                line_num = lua_code[: match.start()].count("\n") + 1
                issues.append(
                    QualityIssue(
                        severity="warning",
                        line_number=line_num,
                        column=1,
                        rule="code_smells",
                        message=f"Function is too long ({function_lines} lines)",
                        suggestion="Consider splitting into smaller functions",
                        impact="maintainability",
                    )
                )

        # Check for deep nesting
        for line_num, line in enumerate(lines, 1):
            indent_level = (len(line) - len(line.lstrip())) // 4  # Assuming 4-space indents

            if indent_level > 4:
                issues.append(
                    QualityIssue(
                        severity="warning",
                        line_number=line_num,
                        column=1,
                        rule="code_smells",
                        message=f"Deep nesting detected (level {indent_level})",
                        suggestion="Consider extracting nested logic into functions",
                        impact="readability",
                    )
                )

        # Check for magic numbers
        magic_numbers = re.finditer(r"\b(?<![.\w])\d{2,}\b(?![.\w])", lua_code)
        for match in magic_numbers:
            number = match.group(0)
            # Skip common acceptable numbers
            if number not in ["100", "180", "360", "255", "256", "1000"]:
                line_num = lua_code[: match.start()].count("\n") + 1
                issues.append(
                    QualityIssue(
                        severity="info",
                        line_number=line_num,
                        column=match.start() - lua_code.rfind("\n", 0, match.start()),
                        rule="code_smells",
                        message=f"Magic number '{number}' should be a named constant",
                        suggestion=f"Replace {number} with a descriptive constant",
                        impact="maintainability",
                    )
                )

    def _check_performance_issues(self, lua_code: str, issues: list[QualityIssue]):
        """Check for performance issues"""
        lines = lua_code.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Check for expensive operations
            for pattern in self.performance_issues["expensive_operations"]:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(
                        QualityIssue(
                            severity="warning",
                            line_number=line_num,
                            column=1,
                            rule="performance",
                            message="Potentially expensive operation detected",
                            suggestion="Consider caching or optimizing this operation",
                            impact="performance",
                        )
                    )

            # Check for inefficient patterns
            for pattern in self.performance_issues["inefficient_patterns"]:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(
                        QualityIssue(
                            severity="info",
                            line_number=line_num,
                            column=1,
                            rule="performance",
                            message="Inefficient code pattern detected",
                            suggestion="Consider using more efficient alternatives",
                            impact="performance",
                        )
                    )

    def _check_best_practices(self, lua_code: str, issues: list[QualityIssue]) -> list[str]:
        """Check for best practices and return list of practices followed"""
        followed_practices = []

        for practice_name, patterns in self.best_practices.items():
            practice_found = False
            for pattern in patterns:
                if re.search(pattern, lua_code, re.IGNORECASE):
                    practice_found = True
                    break

            if practice_found:
                followed_practices.append(practice_name)
            else:
                # Add suggestion for missing best practice
                suggestions = {
                    "error_handling": "Add error handling with pcall/xpcall",
                    "proper_comments": "Add descriptive comments for complex logic",
                    "local_variables": "Use local variables to limit scope",
                    "service_caching": "Cache Roblox services for better performance",
                    "connection_management": "Properly manage event connections",
                }

                if practice_name in suggestions:
                    issues.append(
                        QualityIssue(
                            severity="info",
                            line_number=1,
                            column=1,
                            rule="best_practices",
                            message=f"Best practice not followed: {practice_name}",
                            suggestion=suggestions[practice_name],
                            impact="maintainability",
                        )
                    )

        return followed_practices

    def _check_roblox_practices(self, lua_code: str, issues: list[QualityIssue]):
        """Check Roblox-specific best practices"""
        # Check for proper service usage
        service_usage = bool(re.search(r"game:GetService", lua_code, re.IGNORECASE))
        direct_service_access = bool(re.search(r"game\.\w+Service", lua_code, re.IGNORECASE))

        if direct_service_access and not service_usage:
            issues.append(
                QualityIssue(
                    severity="warning",
                    line_number=1,
                    column=1,
                    rule="roblox_practices",
                    message="Direct service access detected, use game:GetService() instead",
                    suggestion="Replace game.ServiceName with game:GetService('ServiceName')",
                    impact="maintainability",
                )
            )

        # Check for proper wait usage
        old_wait = bool(re.search(r"\bwait\s*\(\s*\)", lua_code))  # wait() without arguments
        if old_wait:
            issues.append(
                QualityIssue(
                    severity="info",
                    line_number=1,
                    column=1,
                    rule="roblox_practices",
                    message="Consider using task.wait() instead of wait()",
                    suggestion="Replace wait() with task.wait() for better performance",
                    impact="performance",
                )
            )

    def _calculate_complexity_score(self, lua_code: str) -> float:
        """Calculate cyclomatic complexity score"""
        # Count decision points
        decision_keywords = [
            r"\bif\b",
            r"\belseif\b",
            r"\bwhile\b",
            r"\bfor\b",
            r"\brepeat\b",
            r"\band\b",
            r"\bor\b",
            r"\bfunction\b",
        ]

        complexity = 1  # Base complexity

        for keyword in decision_keywords:
            complexity += len(re.findall(keyword, lua_code, re.IGNORECASE))

        # Normalize to 0-100 scale (10 = good, 20+ = complex)
        normalized_complexity = max(0, 100 - (complexity * 5))

        return normalized_complexity

    def _calculate_maintainability_score(self, lua_code: str, issues: list[QualityIssue]) -> float:
        """Calculate maintainability score"""
        base_score = 100.0

        # Deduct points for maintainability issues
        for issue in issues:
            if issue.impact == "maintainability":
                if issue.severity == "error":
                    base_score -= 15
                elif issue.severity == "warning":
                    base_score -= 10
                elif issue.severity == "info":
                    base_score -= 5

        # Factor in code size (larger code is harder to maintain)
        lines = len(lua_code.split("\n"))
        if lines > 500:
            base_score -= 10
        elif lines > 200:
            base_score -= 5

        return max(0, base_score)

    def _calculate_readability_score(self, lua_code: str, issues: list[QualityIssue]) -> float:
        """Calculate readability score"""
        base_score = 100.0

        # Deduct points for readability issues
        for issue in issues:
            if issue.impact == "readability":
                if issue.severity == "error":
                    base_score -= 10
                elif issue.severity == "warning":
                    base_score -= 7
                elif issue.severity == "info":
                    base_score -= 3

        # Factor in comment ratio
        lines = lua_code.split("\n")
        comment_ratio = sum(1 for line in lines if line.strip().startswith("--")) / len(lines)

        if comment_ratio > 0.1:  # Good comment ratio
            base_score += 5
        elif comment_ratio < 0.05:  # Poor comment ratio
            base_score -= 10

        return max(0, base_score)

    def _calculate_documentation_score(self, lua_code: str) -> float:
        """Calculate documentation score"""
        base_score = 0.0

        # Check for different types of documentation
        if re.search(self.documentation_patterns["function_docs"], lua_code, re.DOTALL):
            base_score += 30

        if re.search(self.documentation_patterns["module_header"], lua_code, re.DOTALL):
            base_score += 20

        if re.search(self.documentation_patterns["parameter_docs"], lua_code):
            base_score += 20

        if re.search(self.documentation_patterns["return_docs"], lua_code):
            base_score += 15

        if re.search(self.documentation_patterns["example_docs"], lua_code):
            base_score += 15

        return min(100, base_score)

    def _calculate_overall_score(
        self, metrics: QualityMetrics, issues: list[QualityIssue]
    ) -> float:
        """Calculate overall quality score"""
        # Weight different aspects
        weights = {
            "complexity": 0.2,
            "maintainability": 0.3,
            "readability": 0.25,
            "documentation": 0.15,
            "issues": 0.1,
        }

        # Calculate issue penalty
        issue_penalty = 0
        for issue in issues:
            if issue.severity == "error":
                issue_penalty += 10
            elif issue.severity == "warning":
                issue_penalty += 5
            elif issue.severity == "info":
                issue_penalty += 2

        issue_score = max(0, 100 - issue_penalty)

        # Calculate weighted score
        overall_score = (
            metrics.complexity_score * weights["complexity"]
            + metrics.maintainability_score * weights["maintainability"]
            + metrics.readability_score * weights["readability"]
            + metrics.documentation_score * weights["documentation"]
            + issue_score * weights["issues"]
        )

        return min(100, max(0, overall_score))

    def _determine_quality_level(self, overall_score: float) -> QualityLevel:
        """Determine quality level based on score"""
        if overall_score >= 90:
            return QualityLevel.EXCELLENT
        elif overall_score >= 70:
            return QualityLevel.GOOD
        elif overall_score >= 50:
            return QualityLevel.FAIR
        elif overall_score >= 30:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE

    def _generate_recommendations(
        self,
        issues: list[QualityIssue],
        metrics: QualityMetrics,
        best_practices: list[str],
    ) -> list[str]:
        """Generate improvement recommendations"""
        recommendations = []

        # Count issues by type
        issue_counts = {}
        for issue in issues:
            issue_counts[issue.rule] = issue_counts.get(issue.rule, 0) + 1

        # Generate specific recommendations
        if issue_counts.get("naming_conventions", 0) > 3:
            recommendations.append("Establish and follow consistent naming conventions")

        if issue_counts.get("code_smells", 0) > 2:
            recommendations.append("Refactor code to eliminate code smells")

        if issue_counts.get("performance", 0) > 1:
            recommendations.append("Optimize performance-critical sections")

        if metrics.documentation_score < 50:
            recommendations.append("Add comprehensive documentation and comments")

        if metrics.complexity_score < 60:
            recommendations.append("Reduce code complexity by breaking down large functions")

        # Best practice recommendations
        if "error_handling" not in best_practices:
            recommendations.append("Implement proper error handling with pcall/xpcall")

        if "service_caching" not in best_practices:
            recommendations.append("Cache Roblox services for better performance")

        if "connection_management" not in best_practices:
            recommendations.append("Properly manage event connections to prevent memory leaks")

        # General recommendations
        recommendations.extend(
            [
                "Use meaningful variable and function names",
                "Keep functions small and focused on single responsibilities",
                "Add unit tests to improve code reliability",
                "Regular code reviews to maintain quality standards",
            ]
        )

        return recommendations

    def _identify_improvement_areas(self, issues: list[QualityIssue]) -> list[str]:
        """Identify main areas that need improvement"""
        areas = {}

        for issue in issues:
            if issue.impact not in areas:
                areas[issue.impact] = 0
            areas[issue.impact] += 1

        # Sort by frequency
        sorted_areas = sorted(areas.items(), key=lambda x: x[1], reverse=True)

        # Return top 3 areas
        return [area[0] for area in sorted_areas[:3]]
