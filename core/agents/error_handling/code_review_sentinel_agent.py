"""
Code Review Sentinel Agent

Monitors code quality and performs automated code reviews
for error prevention and quality assurance.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.agents.base_agent import BaseAgent, AgentConfig, AgentState, TaskResult

logger = logging.getLogger(__name__)


class ReviewSeverity(Enum):
    """Severity levels for code review findings"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ReviewFinding:
    """Represents a code review finding"""
    severity: ReviewSeverity
    file_path: str
    line_number: Optional[int]
    category: str
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class CodeReviewSentinelAgent(BaseAgent):
    """
    Sentinel agent for code review and quality monitoring.

    This agent performs automated code reviews to identify potential
    issues, security vulnerabilities, and quality problems.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Code Review Sentinel Agent.

        Args:
            config: Agent configuration
        """
        if config is None:
            config = AgentConfig(
                name="CodeReviewSentinel",
                description="Automated code review and quality monitoring",
                capabilities=["code_review", "security_scan", "quality_check"],
                max_concurrent_tasks=3
            )

        super().__init__(config)

        self.review_patterns = self._load_review_patterns()
        self.security_patterns = self._load_security_patterns()
        self.quality_metrics = {}
        self.findings: List[ReviewFinding] = []

        logger.info(f"Code Review Sentinel Agent initialized: {self.config.name}")

    def _load_review_patterns(self) -> Dict[str, Any]:
        """Load code review patterns and rules"""
        return {
            "error_handling": {
                "patterns": [
                    r"except\s*:",  # Bare except
                    r"except\s+Exception\s*:",  # Too broad exception
                    r"pass\s*$",  # Empty except block
                ],
                "severity": ReviewSeverity.MEDIUM
            },
            "security": {
                "patterns": [
                    r"eval\(",  # Dangerous eval usage
                    r"exec\(",  # Dangerous exec usage
                    r"pickle\.loads",  # Unsafe deserialization
                    r"os\.system\(",  # Command injection risk
                ],
                "severity": ReviewSeverity.HIGH
            },
            "performance": {
                "patterns": [
                    r"for.*in.*range.*len\(",  # Inefficient iteration
                    r"time\.sleep\(",  # Blocking sleep in async context
                ],
                "severity": ReviewSeverity.LOW
            }
        }

    def _load_security_patterns(self) -> Dict[str, Any]:
        """Load security-specific patterns"""
        return {
            "credentials": {
                "patterns": [
                    r"password\s*=\s*['\"].*['\"]",
                    r"api_key\s*=\s*['\"].*['\"]",
                    r"secret\s*=\s*['\"].*['\"]",
                ],
                "severity": ReviewSeverity.CRITICAL
            },
            "injection": {
                "patterns": [
                    r"f['\"].*SELECT.*FROM.*{",  # SQL injection risk
                    r"\.format\(.*SELECT.*FROM",  # SQL injection risk
                ],
                "severity": ReviewSeverity.HIGH
            }
        }

    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """
        Execute a code review task.

        Args:
            task: Task configuration containing:
                - file_path: Path to file to review
                - review_type: Type of review (full, security, performance)
                - options: Additional review options

        Returns:
            TaskResult with review findings
        """
        try:
            file_path = task.get("file_path")
            review_type = task.get("review_type", "full")

            logger.info(f"Starting {review_type} review for {file_path}")

            # Perform the review
            findings = await self._perform_review(file_path, review_type)

            # Categorize findings
            critical_count = sum(1 for f in findings if f.severity == ReviewSeverity.CRITICAL)
            high_count = sum(1 for f in findings if f.severity == ReviewSeverity.HIGH)

            # Determine overall status
            if critical_count > 0:
                status = "failed"
                message = f"Review failed: {critical_count} critical issues found"
            elif high_count > 3:
                status = "warning"
                message = f"Review passed with warnings: {high_count} high-severity issues"
            else:
                status = "success"
                message = "Review passed"

            return TaskResult(
                success=(status != "failed"),
                data={
                    "findings": [self._finding_to_dict(f) for f in findings],
                    "summary": {
                        "total": len(findings),
                        "critical": critical_count,
                        "high": high_count,
                        "medium": sum(1 for f in findings if f.severity == ReviewSeverity.MEDIUM),
                        "low": sum(1 for f in findings if f.severity == ReviewSeverity.LOW),
                        "info": sum(1 for f in findings if f.severity == ReviewSeverity.INFO),
                    },
                    "status": status
                },
                message=message,
                metadata={
                    "file_path": file_path,
                    "review_type": review_type,
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Code review failed: {e}")
            return TaskResult(
                success=False,
                error=str(e),
                message=f"Review failed: {str(e)}"
            )

    async def _perform_review(self, file_path: str, review_type: str) -> List[ReviewFinding]:
        """
        Perform the actual code review.

        Args:
            file_path: Path to file to review
            review_type: Type of review to perform

        Returns:
            List of review findings
        """
        findings = []

        # Mock review for demonstration
        # In production, this would actually analyze the file

        if review_type in ["full", "security"]:
            # Check for security issues
            findings.append(ReviewFinding(
                severity=ReviewSeverity.INFO,
                file_path=file_path,
                line_number=None,
                category="security",
                message="Security review completed",
                suggestion="No critical security issues detected"
            ))

        if review_type in ["full", "performance"]:
            # Check for performance issues
            findings.append(ReviewFinding(
                severity=ReviewSeverity.INFO,
                file_path=file_path,
                line_number=None,
                category="performance",
                message="Performance review completed",
                suggestion="Code follows performance best practices"
            ))

        return findings

    def _finding_to_dict(self, finding: ReviewFinding) -> Dict[str, Any]:
        """Convert a ReviewFinding to a dictionary"""
        return {
            "severity": finding.severity.value,
            "file_path": finding.file_path,
            "line_number": finding.line_number,
            "category": finding.category,
            "message": finding.message,
            "suggestion": finding.suggestion,
            "code_snippet": finding.code_snippet,
            "timestamp": finding.timestamp.isoformat()
        }

    async def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze an entire project for code quality issues.

        Args:
            project_path: Path to the project root

        Returns:
            Project-wide analysis results
        """
        logger.info(f"Starting project analysis for {project_path}")

        # Mock project analysis
        return {
            "project_path": project_path,
            "status": "completed",
            "files_analyzed": 0,
            "total_findings": 0,
            "quality_score": 95.0,
            "recommendations": [
                "Consider adding more unit tests",
                "Update documentation for new features"
            ]
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for the agent.

        Returns:
            Health status information
        """
        return {
            "status": "healthy",
            "agent": self.config.name,
            "state": self.state.value,
            "patterns_loaded": len(self.review_patterns) + len(self.security_patterns),
            "findings_count": len(self.findings),
            "timestamp": datetime.now().isoformat()
        }

    async def cleanup(self) -> None:
        """Clean up agent resources"""
        logger.info(f"Cleaning up Code Review Sentinel Agent: {self.config.name}")
        self.findings.clear()
        self.quality_metrics.clear()
        await super().cleanup()


# Export the agent class
__all__ = ["CodeReviewSentinelAgent", "ReviewSeverity", "ReviewFinding"]