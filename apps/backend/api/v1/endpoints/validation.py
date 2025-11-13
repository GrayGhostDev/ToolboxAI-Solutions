"""
Roblox Script Validation API Endpoints

Provides REST API endpoints for comprehensive Roblox Lua script validation
including syntax checking, security analysis, educational content validation,
quality assessment, and platform compliance verification.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

# Import validation components
from core.validation import ValidationEngine, ValidationRequest
from core.validation.educational_validator import GradeLevel, LearningObjective, Subject
from core.validation.validation_engine import ComprehensiveReport, ValidationStatus

# Handle imports safely for user authentication
try:
    from apps.backend.api.auth.auth import get_current_user
except ImportError:
    try:
        from auth.auth import get_current_user
    except ImportError:
        # Fallback for development
        def get_current_user():
            from pydantic import BaseModel

            class MockUser(BaseModel):
                email: str = "test@example.com"
                role: str = "teacher"
                id: str | None = "test_user_id"

            return MockUser()


# User model fallback
try:
    from apps.backend.models.schemas import User
except ImportError:

    class User(BaseModel):
        email: str
        role: str
        id: str | None = None


logger = logging.getLogger(__name__)

# Create router
validation_router = APIRouter(prefix="/validation", tags=["Script Validation"])

# Global validation engine instance
validation_engine = ValidationEngine()


class ValidationType(str, Enum):
    """Types of validation to perform"""

    SYNTAX_ONLY = "syntax_only"
    SECURITY_ONLY = "security_only"
    QUALITY_ONLY = "quality_only"
    COMPLIANCE_ONLY = "compliance_only"
    EDUCATIONAL_ONLY = "educational_only"
    COMPREHENSIVE = "comprehensive"


class ReportFormat(str, Enum):
    """Report output formats"""

    JSON = "json"
    SUMMARY = "summary"
    DETAILED = "detailed"


# Request Models
class ScriptValidationRequest(BaseModel):
    """Request for script validation"""

    script_code: str = Field(
        ..., min_length=1, max_length=1000000, description="Lua script code to validate"
    )
    script_name: str = Field(..., min_length=1, max_length=100, description="Name of the script")
    validation_type: ValidationType = Field(
        default=ValidationType.COMPREHENSIVE, description="Type of validation"
    )

    # Educational context (optional)
    grade_level: GradeLevel | None = Field(
        None, description="Target grade level for educational validation"
    )
    subject: Subject | None = Field(None, description="Educational subject")
    learning_objectives: list[str] | None = Field(
        None, description="Learning objectives to validate against"
    )

    # Validation options
    strict_mode: bool = Field(default=False, description="Enable strict validation mode")
    include_suggestions: bool = Field(default=True, description="Include auto-fix suggestions")
    educational_context: bool = Field(default=True, description="Validate for educational use")

    @field_validator("script_code")
    def validate_script_code(cls, v):
        if not v.strip():
            raise ValueError("Script code cannot be empty")
        # Basic safety check for obviously malicious content
        dangerous_patterns = ["getfenv", "setfenv", "loadstring", "debug."]
        for pattern in dangerous_patterns:
            if pattern in v.lower():
                logger.warning(f"Potentially dangerous pattern detected: {pattern}")
        return v

    @field_validator("learning_objectives")
    def validate_learning_objectives(cls, v):
        if v:
            for obj in v:
                if len(obj.strip()) < 10:
                    raise ValueError("Learning objectives must be at least 10 characters")
        return v


class BatchValidationRequest(BaseModel):
    """Request for batch validation of multiple scripts"""

    scripts: list[ScriptValidationRequest] = Field(
        ..., min_items=1, max_items=10, description="Scripts to validate"
    )
    parallel_processing: bool = Field(default=True, description="Process scripts in parallel")


class ValidationConfigRequest(BaseModel):
    """Request to update validation configuration"""

    strict_mode_default: bool | None = None
    educational_context_default: bool | None = None
    max_script_size: int | None = None
    timeout_seconds: int | None = None


# Response Models
class ValidationSummary(BaseModel):
    """Summary of validation results"""

    script_name: str
    overall_status: ValidationStatus
    overall_score: float
    validation_duration_ms: float
    critical_issues_count: int
    warnings_count: int
    deployment_ready: bool
    educational_ready: bool
    platform_compliant: bool


class ValidationResponse(BaseModel):
    """Response for script validation"""

    success: bool
    validation_id: str
    summary: ValidationSummary
    report: dict[str, Any] | None = None
    report_url: str | None = None
    timestamp: datetime


class BatchValidationResponse(BaseModel):
    """Response for batch validation"""

    success: bool
    batch_id: str
    total_scripts: int
    processed_scripts: int
    failed_scripts: int
    results: list[ValidationSummary]
    timestamp: datetime


class ValidationStatsResponse(BaseModel):
    """Validation statistics response"""

    total_validations: int
    passed_validations: int
    failed_validations: int
    average_score: float
    common_issues: dict[str, int]
    last_updated: datetime


# ============================================================================
# VALIDATION ENDPOINTS
# ============================================================================


@validation_router.post(
    "/validate", response_model=ValidationResponse, status_code=status.HTTP_200_OK
)
async def validate_script(
    request: ScriptValidationRequest,
    background_tasks: BackgroundTasks,
    report_format: ReportFormat = ReportFormat.JSON,
    current_user: User = Depends(get_current_user),
) -> ValidationResponse:
    """
    Validate a Roblox Lua script for syntax, security, quality, and compliance.

    Performs comprehensive validation including:
    - Syntax and semantic checking
    - Security vulnerability analysis
    - Educational content appropriateness
    - Code quality assessment
    - Roblox platform compliance

    Args:
        request: Script validation request with code and parameters
        report_format: Format for the validation report
        current_user: Authenticated user

    Returns:
        ValidationResponse with results and report

    Raises:
        HTTPException: If validation fails or user lacks permissions
    """
    try:
        # Check user permissions
        if current_user.role.lower() not in ["teacher", "admin", "developer"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for script validation",
            )

        logger.info(
            f"Starting validation for script '{request.script_name}' by user {current_user.email}"
        )

        # Convert learning objectives to proper format
        learning_objectives = []
        if request.learning_objectives:
            for i, obj_text in enumerate(request.learning_objectives):
                learning_objectives.append(
                    LearningObjective(
                        id=f"obj_{i}",
                        description=obj_text,
                        grade_level=request.grade_level or GradeLevel.ELEMENTARY,
                        subject=request.subject or Subject.COMPUTER_SCIENCE,
                        bloom_level="understand",  # Default level
                    )
                )

        # Create validation request
        validation_request = ValidationRequest(
            script_code=request.script_code,
            script_name=request.script_name,
            grade_level=request.grade_level,
            subject=request.subject,
            learning_objectives=learning_objectives,
            educational_context=request.educational_context,
            strict_mode=request.strict_mode,
            include_suggestions=request.include_suggestions,
        )

        # Perform validation based on type
        if request.validation_type == ValidationType.COMPREHENSIVE:
            report = await validation_engine.validate_script(validation_request)
        else:
            # For specific validation types, we'll still run comprehensive but filter results
            report = await validation_engine.validate_script(validation_request)
            report = _filter_report_by_type(report, request.validation_type)

        # Generate validation ID
        validation_id = f"val_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.script_name[:10]}"

        # Create summary
        summary = ValidationSummary(
            script_name=request.script_name,
            overall_status=report.overall_status,
            overall_score=report.overall_score,
            validation_duration_ms=report.validation_duration_ms,
            critical_issues_count=len(report.critical_issues),
            warnings_count=len(report.warnings),
            deployment_ready=report.deployment_ready,
            educational_ready=report.educational_ready,
            platform_compliant=report.platform_compliant,
        )

        # Format report based on requested format
        if report_format == ReportFormat.JSON:
            formatted_report = json.loads(validation_engine.export_report(report, "json"))
        elif report_format == ReportFormat.SUMMARY:
            formatted_report = {"summary": validation_engine.export_report(report, "summary")}
        else:  # DETAILED
            formatted_report = json.loads(validation_engine.export_report(report, "json"))

        # Store report in background (would typically save to database)
        background_tasks.add_task(
            _store_validation_report, validation_id, report, current_user.email
        )

        logger.info(
            f"Validation completed for script '{request.script_name}' - Status: {report.overall_status.value}"
        )

        return ValidationResponse(
            success=True,
            validation_id=validation_id,
            summary=summary,
            report=formatted_report,
            report_url=f"/api/v1/validation/reports/{validation_id}",
            timestamp=datetime.now(),
        )

    except ValueError as e:
        logger.error(f"Validation request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Validation failed: {str(e)}"
        )


@validation_router.post(
    "/validate/batch", response_model=BatchValidationResponse, status_code=status.HTTP_200_OK
)
async def validate_scripts_batch(
    request: BatchValidationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> BatchValidationResponse:
    """
    Validate multiple Roblox Lua scripts in batch.

    Efficiently processes multiple scripts with optional parallel processing.
    Useful for validating entire projects or curriculum sets.

    Args:
        request: Batch validation request with multiple scripts
        current_user: Authenticated user

    Returns:
        BatchValidationResponse with results for all scripts
    """
    try:
        # Check user permissions
        if current_user.role.lower() not in ["teacher", "admin", "developer"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for batch validation",
            )

        logger.info(
            f"Starting batch validation of {len(request.scripts)} scripts by user {current_user.email}"
        )

        # Convert requests to validation requests
        validation_requests = []
        for script_req in request.scripts:
            learning_objectives = []
            if script_req.learning_objectives:
                for i, obj_text in enumerate(script_req.learning_objectives):
                    learning_objectives.append(
                        LearningObjective(
                            id=f"obj_{i}",
                            description=obj_text,
                            grade_level=script_req.grade_level or GradeLevel.ELEMENTARY,
                            subject=script_req.subject or Subject.COMPUTER_SCIENCE,
                            bloom_level="understand",
                        )
                    )

            validation_requests.append(
                ValidationRequest(
                    script_code=script_req.script_code,
                    script_name=script_req.script_name,
                    grade_level=script_req.grade_level,
                    subject=script_req.subject,
                    learning_objectives=learning_objectives,
                    educational_context=script_req.educational_context,
                    strict_mode=script_req.strict_mode,
                    include_suggestions=script_req.include_suggestions,
                )
            )

        # Perform batch validation
        if request.parallel_processing:
            reports = await validation_engine.batch_validate(validation_requests)
        else:
            reports = []
            for val_req in validation_requests:
                report = await validation_engine.validate_script(val_req)
                reports.append(report)

        # Generate batch ID
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create summaries
        results = []
        failed_count = 0

        for report in reports:
            summary = ValidationSummary(
                script_name=report.script_name,
                overall_status=report.overall_status,
                overall_score=report.overall_score,
                validation_duration_ms=report.validation_duration_ms,
                critical_issues_count=len(report.critical_issues),
                warnings_count=len(report.warnings),
                deployment_ready=report.deployment_ready,
                educational_ready=report.educational_ready,
                platform_compliant=report.platform_compliant,
            )
            results.append(summary)

            if report.overall_status == ValidationStatus.FAILED:
                failed_count += 1

        # Store batch results in background
        background_tasks.add_task(_store_batch_results, batch_id, reports, current_user.email)

        logger.info(f"Batch validation completed - {len(reports)} processed, {failed_count} failed")

        return BatchValidationResponse(
            success=True,
            batch_id=batch_id,
            total_scripts=len(request.scripts),
            processed_scripts=len(reports),
            failed_scripts=failed_count,
            results=results,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Batch validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch validation failed: {str(e)}",
        )


@validation_router.get("/reports/{validation_id}", response_model=dict[str, Any])
async def get_validation_report(
    validation_id: str,
    format: ReportFormat = ReportFormat.JSON,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Retrieve a previously generated validation report.

    Args:
        validation_id: ID of the validation report
        format: Format for the report output
        current_user: Authenticated user

    Returns:
        Validation report in requested format
    """
    # This would typically retrieve from database
    # For now, return a placeholder response
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=f"Validation report {validation_id} not found"
    )


@validation_router.get("/statistics", response_model=ValidationStatsResponse)
async def get_validation_statistics(
    current_user: User = Depends(get_current_user),
) -> ValidationStatsResponse:
    """
    Get validation statistics and metrics.

    Returns:
        ValidationStatsResponse with usage statistics
    """
    try:
        stats = validation_engine.get_validation_statistics()

        return ValidationStatsResponse(
            total_validations=stats["total_validations"],
            passed_validations=stats["passed_validations"],
            failed_validations=stats["failed_validations"],
            average_score=stats["average_score"],
            common_issues=stats["common_issues"],
            last_updated=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Failed to get validation statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve validation statistics",
        )


@validation_router.post("/templates/secure", response_model=dict[str, str])
async def generate_secure_template(
    template_type: str, current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    """
    Generate secure code templates for common Roblox patterns.

    Args:
        template_type: Type of template to generate (remote_event, data_validation, etc.)
        current_user: Authenticated user

    Returns:
        Generated secure code template
    """
    try:
        # Import security analyzer for template generation
        from core.validation.security_analyzer import SecurityAnalyzer

        security_analyzer = SecurityAnalyzer()
        template_code = security_analyzer.generate_secure_template(template_type)

        if not template_code or "Template not found" in template_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template type '{template_type}' not found",
            )

        return {
            "template_type": template_type,
            "code": template_code,
            "generated_at": datetime.now().isoformat(),
            "generated_by": current_user.email,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate secure template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate template: {str(e)}",
        )


@validation_router.get("/checklists/security", response_model=dict[str, list[str]])
async def get_security_checklist(
    current_user: User = Depends(get_current_user),
) -> dict[str, list[str]]:
    """
    Get security checklist for developers.

    Returns:
        Security checklist organized by categories
    """
    try:
        from core.validation.security_analyzer import SecurityAnalyzer

        security_analyzer = SecurityAnalyzer()
        checklist = security_analyzer.get_security_checklist()

        return checklist

    except Exception as e:
        logger.error(f"Failed to get security checklist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security checklist",
        )


@validation_router.get("/checklists/compliance", response_model=dict[str, list[str]])
async def get_compliance_checklist(
    current_user: User = Depends(get_current_user),
) -> dict[str, list[str]]:
    """
    Get Roblox compliance checklist.

    Returns:
        Compliance checklist organized by categories
    """
    try:
        from core.validation.roblox_compliance import RobloxComplianceChecker

        compliance_checker = RobloxComplianceChecker()
        checklist = compliance_checker.get_compliance_checklist()

        return checklist

    except Exception as e:
        logger.error(f"Failed to get compliance checklist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compliance checklist",
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _filter_report_by_type(
    report: ComprehensiveReport, validation_type: ValidationType
) -> ComprehensiveReport:
    """Filter comprehensive report based on validation type"""
    # For specific validation types, we could filter out irrelevant sections
    # For now, return the full report with a note about the type
    report.script_name = f"{report.script_name} ({validation_type.value})"
    return report


async def _store_validation_report(
    validation_id: str, report: ComprehensiveReport, user_email: str
):
    """Store validation report (background task)"""
    try:
        # This would typically save to database
        logger.info(f"Storing validation report {validation_id} for user {user_email}")
        # await database.store_validation_report(validation_id, report, user_email)
    except Exception as e:
        logger.error(f"Failed to store validation report {validation_id}: {str(e)}")


async def _store_batch_results(batch_id: str, reports: list[ComprehensiveReport], user_email: str):
    """Store batch validation results (background task)"""
    try:
        # This would typically save to database
        logger.info(f"Storing batch results {batch_id} for user {user_email}")
        # await database.store_batch_results(batch_id, reports, user_email)
    except Exception as e:
        logger.error(f"Failed to store batch results {batch_id}: {str(e)}")


# Export router
__all__ = ["validation_router"]
