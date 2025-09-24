"""
Validation Engine - Orchestrates all validation components

Main engine that coordinates syntax validation, security analysis,
educational content validation, quality checking, and compliance verification.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time
from datetime import datetime

from .lua_validator import LuaScriptValidator, ValidationResult
from .security_analyzer import SecurityAnalyzer, SecurityReport
from .educational_validator import EducationalContentValidator, EducationalReport, GradeLevel, Subject, LearningObjective
from .quality_checker import CodeQualityChecker, QualityReport
from .roblox_compliance import RobloxComplianceChecker, ComplianceReport


class ValidationStatus(Enum):
    """Overall validation status"""
    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class ValidationRequest:
    """Request for script validation"""
    script_code: str
    script_name: str
    grade_level: Optional[GradeLevel] = None
    subject: Optional[Subject] = None
    learning_objectives: Optional[List[LearningObjective]] = None
    educational_context: bool = True
    strict_mode: bool = False
    include_suggestions: bool = True


@dataclass
class ComprehensiveReport:
    """Complete validation report combining all aspects"""
    # Metadata
    script_name: str
    validation_timestamp: str
    validation_duration_ms: float
    overall_status: ValidationStatus
    overall_score: float  # 0-100

    # Individual reports
    syntax_validation: ValidationResult
    security_analysis: SecurityReport
    educational_validation: Optional[EducationalReport]
    quality_assessment: QualityReport
    compliance_check: ComplianceReport

    # Summary
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    auto_fix_suggestions: List[str]

    # Scores breakdown
    scores: Dict[str, float]

    # Ready for deployment
    deployment_ready: bool
    educational_ready: bool
    platform_compliant: bool


class ValidationEngine:
    """
    Main validation engine that orchestrates all validation components
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialize all validators
        self.lua_validator = LuaScriptValidator()
        self.security_analyzer = SecurityAnalyzer()
        self.educational_validator = EducationalContentValidator()
        self.quality_checker = CodeQualityChecker()
        self.compliance_checker = RobloxComplianceChecker()

        # Validation statistics
        self.stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'failed_validations': 0,
            'average_score': 0.0,
            'common_issues': {}
        }

    async def validate_script(self, request: ValidationRequest) -> ComprehensiveReport:
        """
        Perform comprehensive validation of a Roblox Lua script

        Args:
            request: ValidationRequest with script and parameters

        Returns:
            ComprehensiveReport with complete analysis
        """
        start_time = time.time()

        try:
            self.logger.info(f"Starting validation for script: {request.script_name}")

            # Run all validations concurrently for better performance
            validation_tasks = []

            # Syntax and semantic validation
            validation_tasks.append(
                self._run_syntax_validation(request.script_code, request.script_name)
            )

            # Security analysis
            validation_tasks.append(
                self._run_security_analysis(request.script_code, request.script_name)
            )

            # Quality assessment
            validation_tasks.append(
                self._run_quality_assessment(request.script_code, request.script_name)
            )

            # Compliance check
            validation_tasks.append(
                self._run_compliance_check(request.script_code, request.script_name, request.educational_context)
            )

            # Educational validation (if context provided)
            if request.educational_context and request.grade_level and request.subject:
                validation_tasks.append(
                    self._run_educational_validation(
                        request.script_code, request.grade_level,
                        request.subject, request.learning_objectives or []
                    )
                )
            else:
                validation_tasks.append(self._create_empty_educational_report())

            # Execute all validations
            results = await asyncio.gather(*validation_tasks, return_exceptions=True)

            # Extract results
            syntax_result = results[0] if not isinstance(results[0], Exception) else self._create_error_syntax_result(str(results[0]))
            security_result = results[1] if not isinstance(results[1], Exception) else self._create_error_security_result(str(results[1]))
            quality_result = results[2] if not isinstance(results[2], Exception) else self._create_error_quality_result(str(results[2]))
            compliance_result = results[3] if not isinstance(results[3], Exception) else self._create_error_compliance_result(str(results[3]))
            educational_result = results[4] if not isinstance(results[4], Exception) else self._create_empty_educational_report()

            # Calculate validation duration
            duration_ms = (time.time() - start_time) * 1000

            # Generate comprehensive report
            report = self._generate_comprehensive_report(
                request, syntax_result, security_result, educational_result,
                quality_result, compliance_result, duration_ms
            )

            # Update statistics
            self._update_statistics(report)

            self.logger.info(f"Validation completed for {request.script_name} in {duration_ms:.2f}ms")
            return report

        except Exception as e:
            self.logger.error(f"Validation failed for {request.script_name}: {str(e)}")
            duration_ms = (time.time() - start_time) * 1000
            return self._create_error_report(request, str(e), duration_ms)

    async def _run_syntax_validation(self, script_code: str, script_name: str) -> ValidationResult:
        """Run syntax validation"""
        return self.lua_validator.validate_script(script_code, script_name)

    async def _run_security_analysis(self, script_code: str, script_name: str) -> SecurityReport:
        """Run security analysis"""
        return self.security_analyzer.analyze_security(script_code, script_name)

    async def _run_educational_validation(self, script_code: str, grade_level: GradeLevel,
                                        subject: Subject, learning_objectives: List[LearningObjective]) -> EducationalReport:
        """Run educational validation"""
        return self.educational_validator.validate_educational_content(
            script_code, grade_level, subject, learning_objectives
        )

    async def _run_quality_assessment(self, script_code: str, script_name: str) -> QualityReport:
        """Run quality assessment"""
        return self.quality_checker.check_quality(script_code, script_name)

    async def _run_compliance_check(self, script_code: str, script_name: str, educational_context: bool) -> ComplianceReport:
        """Run compliance check"""
        return self.compliance_checker.check_compliance(script_code, script_name, educational_context)

    async def _create_empty_educational_report(self) -> Optional[EducationalReport]:
        """Create empty educational report when not applicable"""
        return None

    def _generate_comprehensive_report(self, request: ValidationRequest, syntax_result: ValidationResult,
                                     security_result: SecurityReport, educational_result: Optional[EducationalReport],
                                     quality_result: QualityReport, compliance_result: ComplianceReport,
                                     duration_ms: float) -> ComprehensiveReport:
        """Generate comprehensive validation report"""

        # Collect all critical issues
        critical_issues = []

        # From syntax validation
        critical_issues.extend([
            issue.message for issue in syntax_result.issues
            if issue.severity.value in ['error', 'critical']
        ])

        # From security analysis
        critical_issues.extend([
            finding.description for finding in security_result.findings
            if finding.threat_level.value in ['high', 'critical']
        ])

        # From compliance check
        critical_issues.extend(compliance_result.critical_issues)

        # Collect warnings
        warnings = []

        # From syntax validation
        warnings.extend([
            issue.message for issue in syntax_result.issues
            if issue.severity.value == 'warning'
        ])

        # From security analysis
        warnings.extend([
            finding.description for finding in security_result.findings
            if finding.threat_level.value == 'medium'
        ])

        # From quality assessment
        warnings.extend([
            issue.message for issue in quality_result.issues
            if issue.severity == 'warning'
        ])

        # From compliance check
        warnings.extend(compliance_result.warnings)

        # From educational validation
        if educational_result:
            warnings.extend([
                issue.description for issue in educational_result.issues
                if issue.severity == 'warning'
            ])

        # Collect recommendations
        recommendations = []
        recommendations.extend(security_result.recommendations)
        recommendations.extend(quality_result.recommendations)
        recommendations.extend(compliance_result.recommendations)

        if educational_result:
            recommendations.extend(educational_result.recommendations)

        # Collect auto-fix suggestions
        auto_fix_suggestions = []
        auto_fix_suggestions.extend(self.lua_validator.generate_fix_suggestions(syntax_result.issues))

        # Calculate individual scores
        scores = {
            'syntax': 100.0 if syntax_result.success else 0.0,
            'security': security_result.overall_score,
            'quality': quality_result.overall_score,
            'compliance': self._calculate_compliance_score(compliance_result),
            'educational': self._calculate_educational_score(educational_result) if educational_result else None
        }

        # Calculate overall score
        score_values = [score for score in scores.values() if score is not None]
        overall_score = sum(score_values) / len(score_values) if score_values else 0.0

        # Determine overall status
        overall_status = self._determine_overall_status(
            syntax_result, security_result, quality_result, compliance_result, educational_result
        )

        # Determine readiness flags
        deployment_ready = (
            syntax_result.success and
            security_result.overall_score >= 70 and
            compliance_result.overall_compliance.value in ['compliant', 'warning'] and
            not critical_issues
        )

        educational_ready = deployment_ready and (
            educational_result is None or
            (educational_result.content_rating.value in ['appropriate', 'needs_review'] and
             educational_result.educational_value_score >= 60)
        )

        platform_compliant = compliance_result.platform_ready

        return ComprehensiveReport(
            script_name=request.script_name,
            validation_timestamp=datetime.now().isoformat(),
            validation_duration_ms=duration_ms,
            overall_status=overall_status,
            overall_score=overall_score,
            syntax_validation=syntax_result,
            security_analysis=security_result,
            educational_validation=educational_result,
            quality_assessment=quality_result,
            compliance_check=compliance_result,
            critical_issues=list(set(critical_issues)),  # Remove duplicates
            warnings=list(set(warnings)),
            recommendations=list(set(recommendations)),
            auto_fix_suggestions=auto_fix_suggestions,
            scores=scores,
            deployment_ready=deployment_ready,
            educational_ready=educational_ready,
            platform_compliant=platform_compliant
        )

    def _calculate_compliance_score(self, compliance_result: ComplianceReport) -> float:
        """Calculate compliance score from compliance level"""
        compliance_scores = {
            'compliant': 100.0,
            'warning': 75.0,
            'violation': 50.0,
            'critical_violation': 0.0
        }
        return compliance_scores.get(compliance_result.overall_compliance.value, 0.0)

    def _calculate_educational_score(self, educational_result: EducationalReport) -> float:
        """Calculate educational score"""
        if not educational_result:
            return None

        # Weight different aspects
        weights = {
            'content_rating': 0.3,
            'educational_value': 0.3,
            'engagement': 0.2,
            'accessibility': 0.2
        }

        # Convert content rating to score
        rating_scores = {
            'appropriate': 100.0,
            'needs_review': 75.0,
            'inappropriate': 25.0,
            'blocked': 0.0
        }

        content_score = rating_scores.get(educational_result.content_rating.value, 0.0)

        overall_score = (
            content_score * weights['content_rating'] +
            educational_result.educational_value_score * weights['educational_value'] +
            educational_result.engagement_score * weights['engagement'] +
            educational_result.accessibility_score * weights['accessibility']
        )

        return overall_score

    def _determine_overall_status(self, syntax_result: ValidationResult, security_result: SecurityReport,
                                quality_result: QualityReport, compliance_result: ComplianceReport,
                                educational_result: Optional[EducationalReport]) -> ValidationStatus:
        """Determine overall validation status"""

        # Check for critical failures
        if not syntax_result.success:
            return ValidationStatus.FAILED

        if security_result.threat_level.value == 'critical':
            return ValidationStatus.FAILED

        if compliance_result.overall_compliance.value == 'critical_violation':
            return ValidationStatus.FAILED

        if educational_result and educational_result.content_rating.value == 'blocked':
            return ValidationStatus.FAILED

        # Check for warnings
        has_warnings = (
            security_result.threat_level.value in ['high', 'medium'] or
            compliance_result.overall_compliance.value in ['violation', 'warning'] or
            quality_result.overall_score < 70 or
            (educational_result and educational_result.content_rating.value == 'needs_review')
        )

        if has_warnings:
            return ValidationStatus.PASSED_WITH_WARNINGS

        return ValidationStatus.PASSED

    def _update_statistics(self, report: ComprehensiveReport):
        """Update validation statistics"""
        self.stats['total_validations'] += 1

        if report.overall_status in [ValidationStatus.PASSED, ValidationStatus.PASSED_WITH_WARNINGS]:
            self.stats['passed_validations'] += 1
        else:
            self.stats['failed_validations'] += 1

        # Update average score
        current_avg = self.stats['average_score']
        total = self.stats['total_validations']
        self.stats['average_score'] = (current_avg * (total - 1) + report.overall_score) / total

        # Track common issues
        for issue in report.critical_issues + report.warnings:
            self.stats['common_issues'][issue] = self.stats['common_issues'].get(issue, 0) + 1

    def _create_error_report(self, request: ValidationRequest, error_message: str,
                           duration_ms: float) -> ComprehensiveReport:
        """Create error report when validation fails"""
        return ComprehensiveReport(
            script_name=request.script_name,
            validation_timestamp=datetime.now().isoformat(),
            validation_duration_ms=duration_ms,
            overall_status=ValidationStatus.ERROR,
            overall_score=0.0,
            syntax_validation=self._create_error_syntax_result(error_message),
            security_analysis=self._create_error_security_result(error_message),
            educational_validation=None,
            quality_assessment=self._create_error_quality_result(error_message),
            compliance_check=self._create_error_compliance_result(error_message),
            critical_issues=[f"Validation error: {error_message}"],
            warnings=[],
            recommendations=["Fix validation errors and try again"],
            auto_fix_suggestions=[],
            scores={'error': 0.0},
            deployment_ready=False,
            educational_ready=False,
            platform_compliant=False
        )

    def _create_error_syntax_result(self, error_message: str) -> ValidationResult:
        """Create error syntax result"""
        from .lua_validator import ValidationIssue, ValidationSeverity

        return ValidationResult(
            success=False,
            issues=[ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                line=1,
                column=1,
                message=f"Validation error: {error_message}",
                rule="validation_error"
            )],
            syntax_valid=False,
            api_compatible=False,
            performance_score=0.0,
            memory_score=0.0,
            complexity_score=0.0,
            total_lines=0,
            function_count=0,
            variable_count=0
        )

    def _create_error_security_result(self, error_message: str) -> SecurityReport:
        """Create error security result"""
        from .security_analyzer import SecurityFinding, SecurityThreat, ExploitType

        return SecurityReport(
            overall_score=0.0,
            threat_level=SecurityThreat.CRITICAL,
            findings=[SecurityFinding(
                threat_level=SecurityThreat.CRITICAL,
                exploit_type=ExploitType.CODE_INJECTION,
                line_number=1,
                column=1,
                description=f"Validation error: {error_message}",
                code_snippet="",
                mitigation="Fix validation errors"
            )],
            remote_events_secure=False,
            input_validation_present=False,
            rate_limiting_present=False,
            authentication_checks=False,
            recommendations=[f"Fix validation error: {error_message}"],
            compliant_with_standards=False
        )

    def _create_error_quality_result(self, error_message: str) -> QualityReport:
        """Create error quality result"""
        from .quality_checker import QualityIssue, QualityMetrics, QualityLevel

        return QualityReport(
            overall_score=0.0,
            quality_level=QualityLevel.UNACCEPTABLE,
            metrics=QualityMetrics(
                lines_of_code=0, logical_lines=0, comment_lines=0, blank_lines=0,
                function_count=0, complexity_score=0, maintainability_score=0,
                readability_score=0, documentation_score=0, test_coverage=0
            ),
            issues=[QualityIssue(
                severity='error',
                line_number=1,
                column=1,
                rule='validation_error',
                message=f"Validation error: {error_message}"
            )],
            recommendations=[f"Fix validation error: {error_message}"],
            best_practices_followed=[],
            areas_for_improvement=['error_handling']
        )

    def _create_error_compliance_result(self, error_message: str) -> ComplianceReport:
        """Create error compliance result"""
        from .roblox_compliance import ComplianceViolation, ComplianceLevel, ViolationType

        return ComplianceReport(
            overall_compliance=ComplianceLevel.CRITICAL_VIOLATION,
            violations=[ComplianceViolation(
                violation_type=ViolationType.TECHNICAL_VIOLATION,
                severity=ComplianceLevel.CRITICAL_VIOLATION,
                line_number=1,
                description=f"Validation error: {error_message}",
                policy_reference="Validation Error",
                recommendation="Fix validation errors"
            )],
            compliant_areas=[],
            warnings=[],
            critical_issues=[f"Validation error: {error_message}"],
            platform_ready=False,
            moderation_risk="high",
            recommendations=[f"Fix validation error: {error_message}"]
        )

    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return self.stats.copy()

    def export_report(self, report: ComprehensiveReport, format: str = "json") -> str:
        """Export validation report in specified format"""
        if format.lower() == "json":
            return json.dumps(asdict(report), indent=2, default=str)
        elif format.lower() == "summary":
            return self._generate_summary_report(report)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _generate_summary_report(self, report: ComprehensiveReport) -> str:
        """Generate human-readable summary report"""
        summary = f"""
ToolBoxAI Roblox Script Validation Report
=========================================

Script: {report.script_name}
Status: {report.overall_status.value.upper()}
Overall Score: {report.overall_score:.1f}/100
Validation Time: {report.validation_duration_ms:.2f}ms

SCORES BREAKDOWN:
- Syntax & Semantics: {report.scores.get('syntax', 0):.1f}/100
- Security Analysis: {report.scores.get('security', 0):.1f}/100
- Code Quality: {report.scores.get('quality', 0):.1f}/100
- Platform Compliance: {report.scores.get('compliance', 0):.1f}/100
{f"- Educational Value: {report.scores.get('educational', 0):.1f}/100" if report.scores.get('educational') else ""}

READINESS STATUS:
- Deployment Ready: {'✓' if report.deployment_ready else '✗'}
- Educational Ready: {'✓' if report.educational_ready else '✗'}
- Platform Compliant: {'✓' if report.platform_compliant else '✗'}

CRITICAL ISSUES: {len(report.critical_issues)}
{chr(10).join(f"- {issue}" for issue in report.critical_issues[:5])}
{f"... and {len(report.critical_issues) - 5} more" if len(report.critical_issues) > 5 else ""}

WARNINGS: {len(report.warnings)}
{chr(10).join(f"- {warning}" for warning in report.warnings[:3])}
{f"... and {len(report.warnings) - 3} more" if len(report.warnings) > 3 else ""}

TOP RECOMMENDATIONS:
{chr(10).join(f"- {rec}" for rec in report.recommendations[:5])}

Generated by ToolBoxAI Validation Engine
        """
        return summary.strip()

    async def batch_validate(self, requests: List[ValidationRequest]) -> List[ComprehensiveReport]:
        """Validate multiple scripts in batch"""
        tasks = [self.validate_script(request) for request in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        reports = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_report = self._create_error_report(
                    requests[i], str(result), 0.0
                )
                reports.append(error_report)
            else:
                reports.append(result)

        return reports