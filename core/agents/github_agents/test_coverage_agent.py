"""
Test Coverage Agent for analyzing code coverage and generating reports.

This agent analyzes test coverage for Python (pytest-cov) and JavaScript/TypeScript (jest, vitest) projects:
- Validates minimum coverage thresholds
- Generates detailed coverage reports (lines, branches, functions, statements)
- Identifies untested code paths and critical functions
- Blocks deployments if coverage is below threshold
- Tracks coverage trends over time
- Provides actionable recommendations for improving coverage
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import yaml

from .base_github_agent import BaseGitHubAgent

logger = logging.getLogger(__name__)


@dataclass
class CoverageMetrics:
    """Represents coverage metrics for a specific type."""

    lines_covered: int = 0
    lines_total: int = 0
    branches_covered: int = 0
    branches_total: int = 0
    functions_covered: int = 0
    functions_total: int = 0
    statements_covered: int = 0
    statements_total: int = 0

    @property
    def line_coverage_percent(self) -> float:
        """Calculate line coverage percentage."""
        return (self.lines_covered / max(self.lines_total, 1)) * 100

    @property
    def branch_coverage_percent(self) -> float:
        """Calculate branch coverage percentage."""
        return (self.branches_covered / max(self.branches_total, 1)) * 100

    @property
    def function_coverage_percent(self) -> float:
        """Calculate function coverage percentage."""
        return (self.functions_covered / max(self.functions_total, 1)) * 100

    @property
    def statement_coverage_percent(self) -> float:
        """Calculate statement coverage percentage."""
        return (self.statements_covered / max(self.statements_total, 1)) * 100

    @property
    def overall_coverage_percent(self) -> float:
        """Calculate overall coverage percentage (lines + branches)."""
        total_elements = self.lines_total + self.branches_total
        covered_elements = self.lines_covered + self.branches_covered
        return (covered_elements / max(total_elements, 1)) * 100


@dataclass
class FileCoverage:
    """Coverage information for a specific file."""

    file_path: str
    metrics: CoverageMetrics
    uncovered_lines: List[int] = field(default_factory=list)
    uncovered_branches: List[Tuple[int, int]] = field(default_factory=list)
    critical_functions: List[str] = field(default_factory=list)
    is_critical_file: bool = False

    @property
    def needs_attention(self) -> bool:
        """Determine if this file needs attention based on coverage."""
        return (
            self.metrics.line_coverage_percent < 80 or
            self.is_critical_file and self.metrics.line_coverage_percent < 95 or
            len(self.uncovered_lines) > 20
        )


@dataclass
class UncoveredCodePath:
    """Represents an uncovered critical code path."""

    file_path: str
    function_name: str
    start_line: int
    end_line: int
    complexity_score: int
    is_public_api: bool
    is_error_handler: bool
    description: str = ""

    @property
    def priority_score(self) -> int:
        """Calculate priority score for addressing this path."""
        score = self.complexity_score
        if self.is_public_api:
            score += 10
        if self.is_error_handler:
            score += 5
        return score


@dataclass
class CoverageThresholds:
    """Coverage threshold configuration."""

    min_line_coverage: float = 80.0
    min_branch_coverage: float = 75.0
    min_function_coverage: float = 85.0
    critical_file_min_coverage: float = 95.0
    allow_coverage_decrease: bool = False
    max_coverage_decrease: float = 5.0


@dataclass
class CoverageReport:
    """Comprehensive coverage analysis report."""

    timestamp: datetime
    repository_path: str
    python_coverage: Optional[CoverageMetrics] = None
    javascript_coverage: Optional[CoverageMetrics] = None
    file_coverages: List[FileCoverage] = field(default_factory=list)
    uncovered_critical_paths: List[UncoveredCodePath] = field(default_factory=list)
    coverage_trends: Dict[str, List[float]] = field(default_factory=dict)
    thresholds: CoverageThresholds = field(default_factory=CoverageThresholds)
    recommendations: List[str] = field(default_factory=list)
    meets_thresholds: bool = False
    overall_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "repository_path": self.repository_path,
            "python_coverage": {
                "lines_covered": self.python_coverage.lines_covered,
                "lines_total": self.python_coverage.lines_total,
                "line_coverage_percent": self.python_coverage.line_coverage_percent,
                "branches_covered": self.python_coverage.branches_covered,
                "branches_total": self.python_coverage.branches_total,
                "branch_coverage_percent": self.python_coverage.branch_coverage_percent,
                "functions_covered": self.python_coverage.functions_covered,
                "functions_total": self.python_coverage.functions_total,
                "function_coverage_percent": self.python_coverage.function_coverage_percent,
                "overall_coverage_percent": self.python_coverage.overall_coverage_percent,
            } if self.python_coverage else None,
            "javascript_coverage": {
                "lines_covered": self.javascript_coverage.lines_covered,
                "lines_total": self.javascript_coverage.lines_total,
                "line_coverage_percent": self.javascript_coverage.line_coverage_percent,
                "branches_covered": self.javascript_coverage.branches_covered,
                "branches_total": self.javascript_coverage.branches_total,
                "branch_coverage_percent": self.javascript_coverage.branch_coverage_percent,
                "functions_covered": self.javascript_coverage.functions_covered,
                "functions_total": self.javascript_coverage.functions_total,
                "function_coverage_percent": self.javascript_coverage.function_coverage_percent,
                "overall_coverage_percent": self.javascript_coverage.overall_coverage_percent,
            } if self.javascript_coverage else None,
            "file_coverages": [
                {
                    "file_path": fc.file_path,
                    "line_coverage_percent": fc.metrics.line_coverage_percent,
                    "branch_coverage_percent": fc.metrics.branch_coverage_percent,
                    "uncovered_lines_count": len(fc.uncovered_lines),
                    "needs_attention": fc.needs_attention,
                    "is_critical_file": fc.is_critical_file,
                }
                for fc in self.file_coverages
            ],
            "uncovered_critical_paths": [
                {
                    "file_path": ucp.file_path,
                    "function_name": ucp.function_name,
                    "start_line": ucp.start_line,
                    "end_line": ucp.end_line,
                    "complexity_score": ucp.complexity_score,
                    "is_public_api": ucp.is_public_api,
                    "is_error_handler": ucp.is_error_handler,
                    "priority_score": ucp.priority_score,
                    "description": ucp.description,
                }
                for ucp in self.uncovered_critical_paths
            ],
            "coverage_trends": self.coverage_trends,
            "thresholds": {
                "min_line_coverage": self.thresholds.min_line_coverage,
                "min_branch_coverage": self.thresholds.min_branch_coverage,
                "min_function_coverage": self.thresholds.min_function_coverage,
                "critical_file_min_coverage": self.thresholds.critical_file_min_coverage,
            },
            "recommendations": self.recommendations,
            "meets_thresholds": self.meets_thresholds,
            "overall_score": self.overall_score,
        }


class TestCoverageAgent(BaseGitHubAgent):
    """Agent for analyzing and managing test coverage across Python and JavaScript/TypeScript projects."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the test coverage agent.

        Args:
            config_path: Path to configuration file
        """
        super().__init__(config_path)
        self.coverage_history_file = Path("logs/coverage_history.json")
        self.coverage_history_file.parent.mkdir(parents=True, exist_ok=True)
        self.critical_file_patterns = [
            r".*/(api|core|main|app)\.py$",
            r".*/src/(index|main|app)\.(ts|tsx|js|jsx)$",
            r".*/(models|services|controllers)/.*\.py$",
            r".*/src/(api|services|utils)/.*\.(ts|tsx)$",
        ]

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for test coverage agent."""
        base_config = super()._get_default_config()
        base_config["test_coverage"] = {
            "thresholds": {
                "min_line_coverage": 80.0,
                "min_branch_coverage": 75.0,
                "min_function_coverage": 85.0,
                "critical_file_min_coverage": 95.0,
                "allow_coverage_decrease": False,
                "max_coverage_decrease": 5.0,
            },
            "python": {
                "coverage_file": "coverage.xml",
                "coverage_command": "pytest --cov --cov-report=xml",
                "critical_directories": ["core", "api", "services"],
            },
            "javascript": {
                "coverage_file": "coverage/coverage-final.json",
                "coverage_command": "npm run test:coverage",
                "critical_directories": ["src/api", "src/services", "src/utils"],
            },
            "analysis": {
                "track_trends": True,
                "identify_critical_paths": True,
                "generate_recommendations": True,
                "block_on_threshold_failure": True,
            },
        }
        return base_config

    async def analyze(self, **kwargs) -> Dict[str, Any]:
        """Perform comprehensive coverage analysis.

        Args:
            **kwargs: Analysis parameters
                - target_directory: Directory to analyze (default: repository root)
                - run_tests: Whether to run tests first (default: True)
                - update_trends: Whether to update coverage trends (default: True)

        Returns:
            Analysis results with coverage metrics and recommendations
        """
        try:
            target_directory = kwargs.get("target_directory") or self.get_repository_root()
            run_tests = kwargs.get("run_tests", True)
            update_trends = kwargs.get("update_trends", True)

            if not target_directory:
                return {
                    "success": False,
                    "error": "Not in a git repository or target directory not specified"
                }

            logger.info(f"Starting coverage analysis for {target_directory}")

            # Initialize report
            report = CoverageReport(
                timestamp=datetime.now(),
                repository_path=str(target_directory),
                thresholds=self._load_thresholds(),
            )

            # Run tests and generate coverage if requested
            if run_tests:
                await self._run_coverage_tests(target_directory)

            # Analyze Python coverage
            python_coverage = await self.analyze_python_coverage(target_directory)
            if python_coverage:
                report.python_coverage = python_coverage

            # Analyze JavaScript/TypeScript coverage
            javascript_coverage = await self.analyze_javascript_coverage(target_directory)
            if javascript_coverage:
                report.javascript_coverage = javascript_coverage

            # Analyze file-level coverage
            report.file_coverages = await self._analyze_file_coverage(target_directory)

            # Identify uncovered critical paths
            report.uncovered_critical_paths = await self.identify_untested_critical_paths(
                target_directory, report.file_coverages
            )

            # Load coverage trends
            if update_trends:
                report.coverage_trends = await self._update_coverage_trends(report)

            # Check thresholds and generate recommendations
            report.meets_thresholds = await self.check_coverage_thresholds(report)
            report.recommendations = await self._generate_recommendations(report)
            report.overall_score = self._calculate_overall_score(report)

            # Log operation
            await self.log_operation("coverage_analysis", {
                "target_directory": str(target_directory),
                "python_coverage": report.python_coverage.overall_coverage_percent if report.python_coverage else None,
                "javascript_coverage": report.javascript_coverage.overall_coverage_percent if report.javascript_coverage else None,
                "meets_thresholds": report.meets_thresholds,
                "overall_score": report.overall_score,
            })

            self.update_metrics(operations_performed=1)

            return {
                "success": True,
                "report": report.to_dict(),
                "summary": {
                    "overall_score": report.overall_score,
                    "meets_thresholds": report.meets_thresholds,
                    "python_coverage": report.python_coverage.overall_coverage_percent if report.python_coverage else None,
                    "javascript_coverage": report.javascript_coverage.overall_coverage_percent if report.javascript_coverage else None,
                    "critical_paths_count": len(report.uncovered_critical_paths),
                    "recommendations_count": len(report.recommendations),
                }
            }

        except Exception as e:
            logger.error(f"Error in coverage analysis: {e}")
            self.update_metrics(errors_encountered=1)
            return {
                "success": False,
                "error": str(e)
            }

    async def analyze_python_coverage(self, target_directory: Path) -> Optional[CoverageMetrics]:
        """Analyze Python coverage from coverage.xml report.

        Args:
            target_directory: Target directory to analyze

        Returns:
            Python coverage metrics or None if not available
        """
        try:
            coverage_file = target_directory / self.config.get("test_coverage", {}).get("python", {}).get("coverage_file", "coverage.xml")

            if not coverage_file.exists():
                logger.warning(f"Python coverage file not found: {coverage_file}")
                return None

            tree = ET.parse(coverage_file)
            root = tree.getroot()

            metrics = CoverageMetrics()

            # Parse coverage metrics from XML
            coverage_elem = root.find(".//coverage")
            if coverage_elem is not None:
                metrics.lines_covered = int(coverage_elem.get("lines-covered", 0))
                metrics.lines_total = int(coverage_elem.get("lines-valid", 0))
                metrics.branches_covered = int(coverage_elem.get("branches-covered", 0))
                metrics.branches_total = int(coverage_elem.get("branches-valid", 0))

            # Count functions from packages
            for package in root.findall(".//package"):
                for class_elem in package.findall(".//class"):
                    for method in class_elem.findall(".//method"):
                        metrics.functions_total += 1
                        # Consider function covered if line rate > 0
                        line_rate = float(method.get("line-rate", 0))
                        if line_rate > 0:
                            metrics.functions_covered += 1

            metrics.statements_covered = metrics.lines_covered
            metrics.statements_total = metrics.lines_total

            logger.info(f"Python coverage: {metrics.line_coverage_percent:.1f}% lines, {metrics.branch_coverage_percent:.1f}% branches")
            return metrics

        except Exception as e:
            logger.error(f"Error analyzing Python coverage: {e}")
            return None

    async def analyze_javascript_coverage(self, target_directory: Path) -> Optional[CoverageMetrics]:
        """Analyze JavaScript/TypeScript coverage from coverage-final.json report.

        Args:
            target_directory: Target directory to analyze

        Returns:
            JavaScript coverage metrics or None if not available
        """
        try:
            coverage_file = target_directory / self.config.get("test_coverage", {}).get("javascript", {}).get("coverage_file", "coverage/coverage-final.json")

            if not coverage_file.exists():
                logger.warning(f"JavaScript coverage file not found: {coverage_file}")
                return None

            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)

            metrics = CoverageMetrics()

            # Aggregate metrics from all files
            for file_path, file_data in coverage_data.items():
                if isinstance(file_data, dict):
                    # Lines
                    lines = file_data.get("l", {})
                    for line_num, hit_count in lines.items():
                        metrics.lines_total += 1
                        if hit_count and hit_count > 0:
                            metrics.lines_covered += 1

                    # Branches
                    branches = file_data.get("b", {})
                    for branch_group in branches.values():
                        if isinstance(branch_group, list):
                            for branch_hits in branch_group:
                                metrics.branches_total += 1
                                if branch_hits and branch_hits > 0:
                                    metrics.branches_covered += 1

                    # Functions
                    functions = file_data.get("f", {})
                    for func_name, hit_count in functions.items():
                        metrics.functions_total += 1
                        if hit_count and hit_count > 0:
                            metrics.functions_covered += 1

                    # Statements
                    statements = file_data.get("s", {})
                    for stmt_id, hit_count in statements.items():
                        metrics.statements_total += 1
                        if hit_count and hit_count > 0:
                            metrics.statements_covered += 1

            logger.info(f"JavaScript coverage: {metrics.line_coverage_percent:.1f}% lines, {metrics.branch_coverage_percent:.1f}% branches")
            return metrics

        except Exception as e:
            logger.error(f"Error analyzing JavaScript coverage: {e}")
            return None

    async def identify_untested_critical_paths(self, target_directory: Path, file_coverages: List[FileCoverage]) -> List[UncoveredCodePath]:
        """Identify untested code paths in critical functions.

        Args:
            target_directory: Target directory to analyze
            file_coverages: List of file coverage information

        Returns:
            List of uncovered critical code paths
        """
        try:
            critical_paths = []

            for file_coverage in file_coverages:
                if not file_coverage.needs_attention:
                    continue

                file_path = target_directory / file_coverage.file_path

                if not file_path.exists():
                    continue

                # Analyze Python files
                if file_path.suffix == ".py":
                    paths = await self._analyze_python_critical_paths(file_path, file_coverage)
                    critical_paths.extend(paths)

                # Analyze JavaScript/TypeScript files
                elif file_path.suffix in [".js", ".jsx", ".ts", ".tsx"]:
                    paths = await self._analyze_javascript_critical_paths(file_path, file_coverage)
                    critical_paths.extend(paths)

            # Sort by priority score
            critical_paths.sort(key=lambda x: x.priority_score, reverse=True)

            logger.info(f"Identified {len(critical_paths)} uncovered critical paths")
            return critical_paths

        except Exception as e:
            logger.error(f"Error identifying critical paths: {e}")
            return []

    async def generate_coverage_report(self, format_type: str = "markdown", **kwargs) -> str:
        """Generate a formatted coverage report.

        Args:
            format_type: Report format (markdown, html, json)
            **kwargs: Additional parameters for report generation

        Returns:
            Formatted coverage report
        """
        try:
            # Run analysis first
            analysis_result = await self.analyze(**kwargs)

            if not analysis_result["success"]:
                return f"Error generating report: {analysis_result.get('error', 'Unknown error')}"

            report_data = analysis_result["report"]

            if format_type.lower() == "markdown":
                return self._generate_markdown_report(report_data)
            elif format_type.lower() == "html":
                return self._generate_html_report(report_data)
            elif format_type.lower() == "json":
                return json.dumps(report_data, indent=2)
            else:
                return f"Unsupported format type: {format_type}"

        except Exception as e:
            logger.error(f"Error generating coverage report: {e}")
            return f"Error generating report: {str(e)}"

    async def check_coverage_thresholds(self, report: CoverageReport) -> bool:
        """Check if coverage meets minimum thresholds.

        Args:
            report: Coverage report to validate

        Returns:
            True if all thresholds are met, False otherwise
        """
        try:
            thresholds = report.thresholds
            meets_thresholds = True

            # Check Python coverage thresholds
            if report.python_coverage:
                if report.python_coverage.line_coverage_percent < thresholds.min_line_coverage:
                    meets_thresholds = False
                    logger.warning(f"Python line coverage {report.python_coverage.line_coverage_percent:.1f}% below threshold {thresholds.min_line_coverage}%")

                if report.python_coverage.branch_coverage_percent < thresholds.min_branch_coverage:
                    meets_thresholds = False
                    logger.warning(f"Python branch coverage {report.python_coverage.branch_coverage_percent:.1f}% below threshold {thresholds.min_branch_coverage}%")

                if report.python_coverage.function_coverage_percent < thresholds.min_function_coverage:
                    meets_thresholds = False
                    logger.warning(f"Python function coverage {report.python_coverage.function_coverage_percent:.1f}% below threshold {thresholds.min_function_coverage}%")

            # Check JavaScript coverage thresholds
            if report.javascript_coverage:
                if report.javascript_coverage.line_coverage_percent < thresholds.min_line_coverage:
                    meets_thresholds = False
                    logger.warning(f"JavaScript line coverage {report.javascript_coverage.line_coverage_percent:.1f}% below threshold {thresholds.min_line_coverage}%")

                if report.javascript_coverage.branch_coverage_percent < thresholds.min_branch_coverage:
                    meets_thresholds = False
                    logger.warning(f"JavaScript branch coverage {report.javascript_coverage.branch_coverage_percent:.1f}% below threshold {thresholds.min_branch_coverage}%")

                if report.javascript_coverage.function_coverage_percent < thresholds.min_function_coverage:
                    meets_thresholds = False
                    logger.warning(f"JavaScript function coverage {report.javascript_coverage.function_coverage_percent:.1f}% below threshold {thresholds.min_function_coverage}%")

            # Check critical file coverage
            for file_coverage in report.file_coverages:
                if file_coverage.is_critical_file and file_coverage.metrics.line_coverage_percent < thresholds.critical_file_min_coverage:
                    meets_thresholds = False
                    logger.warning(f"Critical file {file_coverage.file_path} coverage {file_coverage.metrics.line_coverage_percent:.1f}% below threshold {thresholds.critical_file_min_coverage}%")

            return meets_thresholds

        except Exception as e:
            logger.error(f"Error checking coverage thresholds: {e}")
            return False

    async def execute_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute a specific coverage-related action.

        Args:
            action: Action to execute
            **kwargs: Action parameters

        Returns:
            Action execution results
        """
        try:
            if action == "analyze":
                return await self.analyze(**kwargs)

            elif action == "generate_report":
                format_type = kwargs.get("format", "markdown")
                report = await self.generate_coverage_report(format_type, **kwargs)
                return {
                    "success": True,
                    "report": report,
                    "format": format_type
                }

            elif action == "run_tests":
                target_directory = kwargs.get("target_directory") or self.get_repository_root()
                result = await self._run_coverage_tests(target_directory)
                return result

            elif action == "check_thresholds":
                analysis_result = await self.analyze(**kwargs)
                if analysis_result["success"]:
                    return {
                        "success": True,
                        "meets_thresholds": analysis_result["summary"]["meets_thresholds"],
                        "details": analysis_result["summary"]
                    }
                else:
                    return analysis_result

            elif action == "generate_missing_tests":
                return await self._generate_missing_tests(**kwargs)

            elif action == "update_trends":
                target_directory = kwargs.get("target_directory") or self.get_repository_root()
                report = CoverageReport(
                    timestamp=datetime.now(),
                    repository_path=str(target_directory),
                )
                trends = await self._update_coverage_trends(report)
                return {
                    "success": True,
                    "trends": trends
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [
                        "analyze", "generate_report", "run_tests",
                        "check_thresholds", "generate_missing_tests", "update_trends"
                    ]
                }

        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            self.update_metrics(errors_encountered=1)
            return {
                "success": False,
                "error": str(e)
            }

    def _load_thresholds(self) -> CoverageThresholds:
        """Load coverage thresholds from configuration."""
        threshold_config = self.config.get("test_coverage", {}).get("thresholds", {})
        return CoverageThresholds(
            min_line_coverage=threshold_config.get("min_line_coverage", 80.0),
            min_branch_coverage=threshold_config.get("min_branch_coverage", 75.0),
            min_function_coverage=threshold_config.get("min_function_coverage", 85.0),
            critical_file_min_coverage=threshold_config.get("critical_file_min_coverage", 95.0),
            allow_coverage_decrease=threshold_config.get("allow_coverage_decrease", False),
            max_coverage_decrease=threshold_config.get("max_coverage_decrease", 5.0),
        )

    async def _run_coverage_tests(self, target_directory: Path) -> Dict[str, Any]:
        """Run coverage tests for both Python and JavaScript."""
        results = {"python": None, "javascript": None}

        # Run Python coverage tests
        try:
            python_cmd = self.config.get("test_coverage", {}).get("python", {}).get("coverage_command", "pytest --cov --cov-report=xml")
            process = await asyncio.create_subprocess_shell(
                python_cmd,
                cwd=target_directory,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            results["python"] = {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
            }
        except Exception as e:
            results["python"] = {"success": False, "error": str(e)}

        # Run JavaScript coverage tests
        try:
            js_cmd = self.config.get("test_coverage", {}).get("javascript", {}).get("coverage_command", "npm run test:coverage")
            process = await asyncio.create_subprocess_shell(
                js_cmd,
                cwd=target_directory,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            results["javascript"] = {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
            }
        except Exception as e:
            results["javascript"] = {"success": False, "error": str(e)}

        return results

    async def _analyze_file_coverage(self, target_directory: Path) -> List[FileCoverage]:
        """Analyze coverage for individual files."""
        file_coverages = []

        # Analyze Python files
        python_files = list(target_directory.rglob("*.py"))
        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue

            file_coverage = await self._analyze_python_file_coverage(py_file)
            if file_coverage:
                file_coverages.append(file_coverage)

        # Analyze JavaScript/TypeScript files
        js_files = list(target_directory.rglob("*.js")) + list(target_directory.rglob("*.jsx")) + \
                  list(target_directory.rglob("*.ts")) + list(target_directory.rglob("*.tsx"))
        for js_file in js_files:
            if self._should_skip_file(js_file):
                continue

            file_coverage = await self._analyze_javascript_file_coverage(js_file)
            if file_coverage:
                file_coverages.append(file_coverage)

        return file_coverages

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped from analysis."""
        skip_patterns = [
            "test_", "_test", ".test.", "__pycache__", "node_modules",
            "coverage", "dist", "build", ".git", "venv"
        ]

        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)

    def _is_critical_file(self, file_path: str) -> bool:
        """Check if file is considered critical."""
        return any(re.match(pattern, file_path) for pattern in self.critical_file_patterns)

    async def _analyze_python_file_coverage(self, file_path: Path) -> Optional[FileCoverage]:
        """Analyze coverage for a specific Python file."""
        # This would be implemented to parse coverage data for specific files
        # For now, return a placeholder implementation
        relative_path = str(file_path.relative_to(self.get_repository_root() or Path.cwd()))
        return FileCoverage(
            file_path=relative_path,
            metrics=CoverageMetrics(lines_covered=0, lines_total=1),
            is_critical_file=self._is_critical_file(relative_path)
        )

    async def _analyze_javascript_file_coverage(self, file_path: Path) -> Optional[FileCoverage]:
        """Analyze coverage for a specific JavaScript/TypeScript file."""
        # This would be implemented to parse coverage data for specific files
        # For now, return a placeholder implementation
        relative_path = str(file_path.relative_to(self.get_repository_root() or Path.cwd()))
        return FileCoverage(
            file_path=relative_path,
            metrics=CoverageMetrics(lines_covered=0, lines_total=1),
            is_critical_file=self._is_critical_file(relative_path)
        )

    async def _analyze_python_critical_paths(self, file_path: Path, file_coverage: FileCoverage) -> List[UncoveredCodePath]:
        """Analyze critical paths in Python files."""
        critical_paths = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Simple regex to find function definitions
            function_pattern = re.compile(r'^def\s+(\w+)\s*\(.*?\):', re.MULTILINE)

            for match in function_pattern.finditer(content):
                function_name = match.group(1)
                start_line = content[:match.start()].count('\n') + 1

                # Check if function is in uncovered lines
                if any(line >= start_line and line <= start_line + 10 for line in file_coverage.uncovered_lines):
                    critical_path = UncoveredCodePath(
                        file_path=file_coverage.file_path,
                        function_name=function_name,
                        start_line=start_line,
                        end_line=start_line + 10,  # Simplified
                        complexity_score=5,  # Simplified
                        is_public_api=not function_name.startswith('_'),
                        is_error_handler='error' in function_name.lower() or 'exception' in function_name.lower(),
                        description=f"Uncovered function: {function_name}"
                    )
                    critical_paths.append(critical_path)

        except Exception as e:
            logger.error(f"Error analyzing Python critical paths in {file_path}: {e}")

        return critical_paths

    async def _analyze_javascript_critical_paths(self, file_path: Path, file_coverage: FileCoverage) -> List[UncoveredCodePath]:
        """Analyze critical paths in JavaScript/TypeScript files."""
        critical_paths = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Simple regex to find function definitions
            function_patterns = [
                re.compile(r'function\s+(\w+)\s*\(', re.MULTILINE),
                re.compile(r'const\s+(\w+)\s*=\s*(?:async\s+)?\(.*?\)\s*=>', re.MULTILINE),
                re.compile(r'(\w+)\s*:\s*(?:async\s+)?function', re.MULTILINE),
            ]

            for pattern in function_patterns:
                for match in pattern.finditer(content):
                    function_name = match.group(1)
                    start_line = content[:match.start()].count('\n') + 1

                    # Check if function is in uncovered lines
                    if any(line >= start_line and line <= start_line + 10 for line in file_coverage.uncovered_lines):
                        critical_path = UncoveredCodePath(
                            file_path=file_coverage.file_path,
                            function_name=function_name,
                            start_line=start_line,
                            end_line=start_line + 10,  # Simplified
                            complexity_score=5,  # Simplified
                            is_public_api=not function_name.startswith('_'),
                            is_error_handler='error' in function_name.lower() or 'catch' in function_name.lower(),
                            description=f"Uncovered function: {function_name}"
                        )
                        critical_paths.append(critical_path)

        except Exception as e:
            logger.error(f"Error analyzing JavaScript critical paths in {file_path}: {e}")

        return critical_paths

    async def _update_coverage_trends(self, report: CoverageReport) -> Dict[str, List[float]]:
        """Update and return coverage trends over time."""
        trends = {}

        try:
            # Load existing trends
            if self.coverage_history_file.exists():
                with open(self.coverage_history_file, 'r') as f:
                    history = json.load(f)
            else:
                history = {"entries": []}

            # Add current data
            current_entry = {
                "timestamp": report.timestamp.isoformat(),
                "python_coverage": report.python_coverage.overall_coverage_percent if report.python_coverage else None,
                "javascript_coverage": report.javascript_coverage.overall_coverage_percent if report.javascript_coverage else None,
            }

            history["entries"].append(current_entry)

            # Keep only last 50 entries
            history["entries"] = history["entries"][-50:]

            # Save updated history
            with open(self.coverage_history_file, 'w') as f:
                json.dump(history, f, indent=2)

            # Generate trends
            trends["python"] = [
                entry["python_coverage"] for entry in history["entries"]
                if entry["python_coverage"] is not None
            ]
            trends["javascript"] = [
                entry["javascript_coverage"] for entry in history["entries"]
                if entry["javascript_coverage"] is not None
            ]

        except Exception as e:
            logger.error(f"Error updating coverage trends: {e}")

        return trends

    async def _generate_recommendations(self, report: CoverageReport) -> List[str]:
        """Generate actionable recommendations based on coverage analysis."""
        recommendations = []

        # Check overall coverage
        if report.python_coverage and report.python_coverage.overall_coverage_percent < 90:
            recommendations.append(f"Python coverage is {report.python_coverage.overall_coverage_percent:.1f}%. Consider adding more unit tests.")

        if report.javascript_coverage and report.javascript_coverage.overall_coverage_percent < 90:
            recommendations.append(f"JavaScript coverage is {report.javascript_coverage.overall_coverage_percent:.1f}%. Consider adding more unit tests.")

        # Check critical paths
        high_priority_paths = [p for p in report.uncovered_critical_paths if p.priority_score > 15]
        if high_priority_paths:
            recommendations.append(f"Found {len(high_priority_paths)} high-priority uncovered critical paths. Focus on testing public APIs and error handlers.")

        # Check file-level issues
        files_needing_attention = [f for f in report.file_coverages if f.needs_attention]
        if files_needing_attention:
            recommendations.append(f"{len(files_needing_attention)} files need attention. Focus on critical files first.")

        # Check branch coverage
        if report.python_coverage and report.python_coverage.branch_coverage_percent < report.python_coverage.line_coverage_percent - 10:
            recommendations.append("Branch coverage is significantly lower than line coverage. Add tests for conditional logic.")

        # Generic recommendations
        if len(recommendations) == 0:
            recommendations.append("Coverage looks good! Consider adding integration tests to complement unit tests.")

        return recommendations

    def _calculate_overall_score(self, report: CoverageReport) -> float:
        """Calculate an overall coverage score (0-100)."""
        score = 0.0
        weights = 0.0

        if report.python_coverage:
            python_score = (
                report.python_coverage.line_coverage_percent * 0.4 +
                report.python_coverage.branch_coverage_percent * 0.3 +
                report.python_coverage.function_coverage_percent * 0.3
            )
            score += python_score * 0.5
            weights += 0.5

        if report.javascript_coverage:
            js_score = (
                report.javascript_coverage.line_coverage_percent * 0.4 +
                report.javascript_coverage.branch_coverage_percent * 0.3 +
                report.javascript_coverage.function_coverage_percent * 0.3
            )
            score += js_score * 0.5
            weights += 0.5

        return score / max(weights, 1)

    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Generate a markdown coverage report."""
        lines = ["# Test Coverage Report\n"]

        lines.append(f"**Generated:** {report_data['timestamp']}")
        lines.append(f"**Repository:** {report_data['repository_path']}")
        lines.append(f"**Overall Score:** {report_data['overall_score']:.1f}/100")
        lines.append(f"**Meets Thresholds:** {'✅ Yes' if report_data['meets_thresholds'] else '❌ No'}\n")

        # Python coverage
        if report_data.get('python_coverage'):
            py_cov = report_data['python_coverage']
            lines.extend([
                "## Python Coverage",
                f"- **Lines:** {py_cov['line_coverage_percent']:.1f}% ({py_cov['lines_covered']}/{py_cov['lines_total']})",
                f"- **Branches:** {py_cov['branch_coverage_percent']:.1f}% ({py_cov['branches_covered']}/{py_cov['branches_total']})",
                f"- **Functions:** {py_cov['function_coverage_percent']:.1f}% ({py_cov['functions_covered']}/{py_cov['functions_total']})",
                f"- **Overall:** {py_cov['overall_coverage_percent']:.1f}%\n"
            ])

        # JavaScript coverage
        if report_data.get('javascript_coverage'):
            js_cov = report_data['javascript_coverage']
            lines.extend([
                "## JavaScript/TypeScript Coverage",
                f"- **Lines:** {js_cov['line_coverage_percent']:.1f}% ({js_cov['lines_covered']}/{js_cov['lines_total']})",
                f"- **Branches:** {js_cov['branch_coverage_percent']:.1f}% ({js_cov['branches_covered']}/{js_cov['branches_total']})",
                f"- **Functions:** {js_cov['function_coverage_percent']:.1f}% ({js_cov['functions_covered']}/{js_cov['functions_total']})",
                f"- **Overall:** {js_cov['overall_coverage_percent']:.1f}%\n"
            ])

        # Critical paths
        critical_paths = report_data.get('uncovered_critical_paths', [])
        if critical_paths:
            lines.append("## Uncovered Critical Paths")
            for path in critical_paths[:10]:  # Show top 10
                lines.append(f"- **{path['function_name']}** in {path['file_path']} (Priority: {path['priority_score']})")
            if len(critical_paths) > 10:
                lines.append(f"... and {len(critical_paths) - 10} more")
            lines.append("")

        # Recommendations
        recommendations = report_data.get('recommendations', [])
        if recommendations:
            lines.append("## Recommendations")
            for rec in recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)

    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate an HTML coverage report."""
        html = f"""
        <html>
        <head>
            <title>Test Coverage Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .success {{ border-color: #4CAF50; background-color: #f1f8e9; }}
                .warning {{ border-color: #FF9800; background-color: #fff3e0; }}
                .error {{ border-color: #f44336; background-color: #ffebee; }}
                .critical-path {{ margin: 5px 0; padding: 10px; background-color: #f5f5f5; border-left: 4px solid #ff9800; }}
            </style>
        </head>
        <body>
            <h1>Test Coverage Report</h1>
            <p><strong>Generated:</strong> {report_data['timestamp']}</p>
            <p><strong>Repository:</strong> {report_data['repository_path']}</p>
            <p><strong>Overall Score:</strong> {report_data['overall_score']:.1f}/100</p>
            <p><strong>Meets Thresholds:</strong> {'✅ Yes' if report_data['meets_thresholds'] else '❌ No'}</p>
        """

        # Add coverage metrics
        if report_data.get('python_coverage'):
            py_cov = report_data['python_coverage']
            html += f"""
            <h2>Python Coverage</h2>
            <div class="metric">
                <strong>Lines:</strong> {py_cov['line_coverage_percent']:.1f}%<br>
                <strong>Branches:</strong> {py_cov['branch_coverage_percent']:.1f}%<br>
                <strong>Functions:</strong> {py_cov['function_coverage_percent']:.1f}%
            </div>
            """

        if report_data.get('javascript_coverage'):
            js_cov = report_data['javascript_coverage']
            html += f"""
            <h2>JavaScript/TypeScript Coverage</h2>
            <div class="metric">
                <strong>Lines:</strong> {js_cov['line_coverage_percent']:.1f}%<br>
                <strong>Branches:</strong> {js_cov['branch_coverage_percent']:.1f}%<br>
                <strong>Functions:</strong> {js_cov['function_coverage_percent']:.1f}%
            </div>
            """

        html += "</body></html>"
        return html

    async def _generate_missing_tests(self, **kwargs) -> Dict[str, Any]:
        """Generate suggestions for missing tests based on uncovered code."""
        try:
            target_directory = kwargs.get("target_directory") or self.get_repository_root()

            # This would be implemented to analyze code and suggest test cases
            # For now, return a placeholder implementation
            suggestions = [
                "Add unit tests for error handling in core/api.py",
                "Add integration tests for database operations",
                "Add tests for edge cases in utility functions",
                "Add tests for public API endpoints",
            ]

            return {
                "success": True,
                "suggestions": suggestions,
                "count": len(suggestions)
            }

        except Exception as e:
            logger.error(f"Error generating missing tests: {e}")
            return {
                "success": False,
                "error": str(e)
            }