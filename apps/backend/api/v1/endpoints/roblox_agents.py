"""
API endpoints for Roblox AI Agent Suite

Provides REST API access to:
- Content generation
- Script optimization
- Security validation
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime
import json
import logging

from apps.backend.core.deps import get_current_user
from database.models import User

# Import types from correct location
from apps.backend.models.schemas import SubjectType, ActivityType

# Import Roblox agents
try:
    from core.agents.roblox.roblox_content_generation_agent import RobloxContentGenerationAgent
    from core.agents.roblox.roblox_script_optimization_agent import (
        RobloxScriptOptimizationAgent,
        OptimizationLevel,
    )
    from core.agents.roblox.roblox_security_validation_agent import RobloxSecurityValidationAgent

    AGENTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Roblox agents not available: {e}")
    AGENTS_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/roblox-agents", tags=["Roblox AI Agents"])


# Request/Response Models
class ContentGenerationRequest(BaseModel):
    """Request model for content generation"""

    subject: str = Field(..., description="Educational subject (Math, Science, etc.)")
    topic: str = Field(..., description="Specific topic within the subject")
    grade_level: int = Field(..., ge=1, le=12, description="Grade level (1-12)")
    activity_type: str = Field(..., description="Type of activity (quiz, lesson, experiment, etc.)")
    accessibility_features: List[str] = Field(
        default=["text-to-speech", "high-contrast"], description="Accessibility features to include"
    )
    language: str = Field(default="English", description="Content language")
    num_questions: Optional[int] = Field(
        default=5, ge=1, le=20, description="Number of questions for quizzes"
    )


class ScriptOptimizationRequest(BaseModel):
    """Request model for script optimization"""

    script_code: str = Field(..., description="Luau script code to optimize")
    optimization_level: str = Field(
        default="balanced", description="Optimization level: conservative, balanced, or aggressive"
    )
    preserve_comments: bool = Field(default=True, description="Whether to preserve comments")
    script_type: str = Field(default="ServerScript", description="Type of script")


class SecurityValidationRequest(BaseModel):
    """Request model for security validation"""

    script_code: str = Field(..., description="Luau script code to validate")
    script_type: str = Field(
        default="ServerScript",
        description="Type of script: ServerScript, LocalScript, or ModuleScript",
    )
    strict_mode: bool = Field(default=True, description="Enable strict security checks")


class ContentGenerationResponse(BaseModel):
    """Response model for content generation"""

    success: bool
    content_id: str
    subject: str
    topic: str
    grade_level: int
    scripts: Dict[str, str]  # Script name -> Luau code
    assets: List[Dict[str, Any]]
    accessibility_features: List[str]
    metadata: Dict[str, Any]
    generation_time: float


class OptimizationResponse(BaseModel):
    """Response model for script optimization"""

    success: bool
    original_lines: int
    optimized_lines: int
    original_code: str
    optimized_code: str
    issues_found: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    optimization_level: str
    performance_gain: str
    compatibility_notes: List[str]


class SecurityValidationResponse(BaseModel):
    """Response model for security validation"""

    success: bool
    scan_id: str
    risk_score: float
    vulnerabilities: List[Dict[str, Any]]
    compliance_status: Dict[str, bool]
    recommendations: List[str]
    blocked_patterns: List[str]
    safe_patterns: List[str]
    report_markdown: str


# Initialize agents (singleton pattern)
_content_agent = None
_optimization_agent = None
_security_agent = None


def get_content_agent():
    """Get or create content generation agent"""
    global _content_agent
    if not AGENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Content generation agent not available")

    if _content_agent is None:
        _content_agent = RobloxContentGenerationAgent()
    return _content_agent


def get_optimization_agent():
    """Get or create optimization agent"""
    global _optimization_agent
    if not AGENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Optimization agent not available")

    if _optimization_agent is None:
        _optimization_agent = RobloxScriptOptimizationAgent()
    return _optimization_agent


def get_security_agent():
    """Get or create security validation agent"""
    global _security_agent
    if not AGENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Security validation agent not available")

    if _security_agent is None:
        _security_agent = RobloxSecurityValidationAgent()
    return _security_agent


@router.get("/status")
async def get_agents_status(current_user: User = Depends(get_current_user)):
    """Check if Roblox agents are available and ready"""
    return {
        "available": AGENTS_AVAILABLE,
        "agents": {
            "content_generation": _content_agent is not None,
            "script_optimization": _optimization_agent is not None,
            "security_validation": _security_agent is not None,
        },
        "version": "1.0.0",
    }


@router.post("/generate-content", response_model=ContentGenerationResponse)
async def generate_educational_content(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Generate educational content for Roblox

    This endpoint uses AI to generate complete educational experiences including:
    - Luau scripts for game mechanics
    - Quiz systems
    - Interactive elements
    - Accessibility features
    """
    try:
        start_time = datetime.now()
        agent = get_content_agent()

        # Map string values to enums (if using enums in agent)
        subject_map = {
            "Math": "MATHEMATICS",
            "Mathematics": "MATHEMATICS",
            "Science": "SCIENCE",
            "History": "HISTORY",
            "Language": "LANGUAGE",
            "Geography": "GEOGRAPHY",
            "Art": "ART",
            "Music": "MUSIC",
            "Computer Science": "COMPUTER_SCIENCE",
        }

        activity_map = {
            "quiz": "QUIZ",
            "lesson": "LESSON",
            "experiment": "EXPERIMENT",
            "exploration": "EXPLORATION",
            "interactive": "INTERACTIVE",
        }

        # Generate content using the agent
        result = agent.generate_educational_content(
            subject=subject_map.get(request.subject, request.subject),
            topic=request.topic,
            grade_level=request.grade_level,
            activity_type=activity_map.get(request.activity_type.lower(), request.activity_type),
            accessibility_features=request.accessibility_features,
            num_questions=(
                request.num_questions if request.activity_type.lower() == "quiz" else None
            ),
        )

        # Calculate generation time
        generation_time = (datetime.now() - start_time).total_seconds()

        # Log the generation for analytics
        logger.info(
            f"Generated educational content for {current_user.username}: "
            f"{request.subject}/{request.topic} Grade {request.grade_level}"
        )

        return ContentGenerationResponse(
            success=True,
            content_id=f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            subject=request.subject,
            topic=request.topic,
            grade_level=request.grade_level,
            scripts=result.get("scripts", {}),
            assets=result.get("assets", []),
            accessibility_features=request.accessibility_features,
            metadata={
                "generator": "RobloxContentGenerationAgent",
                "user": current_user.username,
                "timestamp": datetime.now().isoformat(),
            },
            generation_time=generation_time,
        )

    except Exception as e:
        logger.error(f"Content generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@router.post("/optimize-script", response_model=OptimizationResponse)
async def optimize_luau_script(
    request: ScriptOptimizationRequest, current_user: User = Depends(get_current_user)
):
    """
    Optimize a Roblox Luau script for performance

    This endpoint analyzes and optimizes scripts by:
    - Detecting performance bottlenecks
    - Optimizing loops and table operations
    - Improving memory management
    - Applying Roblox-specific optimizations
    """
    try:
        agent = get_optimization_agent()

        # Map optimization level
        level_map = {
            "conservative": OptimizationLevel.CONSERVATIVE,
            "balanced": OptimizationLevel.BALANCED,
            "aggressive": OptimizationLevel.AGGRESSIVE,
        }

        # Optimize the script
        result = agent.optimize_script(
            request.script_code,
            optimization_level=level_map.get(
                request.optimization_level.lower(), OptimizationLevel.BALANCED
            ),
            preserve_comments=request.preserve_comments,
        )

        # Format issues for response
        issues = [
            {
                "severity": issue.severity,
                "location": issue.location,
                "type": issue.issue_type,
                "description": issue.description,
                "suggestion": issue.suggestion,
                "impact": issue.estimated_impact,
            }
            for issue in result.issues_found
        ]

        logger.info(
            f"Optimized script for {current_user.username}: "
            f"{len(result.issues_found)} issues found"
        )

        return OptimizationResponse(
            success=True,
            original_lines=result.metrics.get("original_lines", 0),
            optimized_lines=result.metrics.get("optimized_lines", 0),
            original_code=result.original_code,
            optimized_code=result.optimized_code,
            issues_found=issues,
            metrics=result.metrics,
            optimization_level=request.optimization_level,
            performance_gain=result.metrics.get("estimated_performance_gain", "Unknown"),
            compatibility_notes=result.compatibility_notes,
        )

    except Exception as e:
        logger.error(f"Script optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Script optimization failed: {str(e)}")


@router.post("/validate-security", response_model=SecurityValidationResponse)
async def validate_script_security(
    request: SecurityValidationRequest, current_user: User = Depends(get_current_user)
):
    """
    Validate security of a Roblox Luau script

    This endpoint performs comprehensive security analysis:
    - Detects dangerous functions (loadstring, etc.)
    - Identifies authentication vulnerabilities
    - Checks input validation
    - Validates compliance with Roblox ToS
    """
    try:
        agent = get_security_agent()

        # Validate the script
        report = agent.validate_script(request.script_code, script_type=request.script_type)

        # Format vulnerabilities for response
        vulnerabilities = [
            {
                "threat_level": vuln.threat_level.value,
                "type": vuln.vulnerability_type.value,
                "location": vuln.location,
                "description": vuln.description,
                "impact": vuln.impact,
                "remediation": vuln.remediation,
                "cvss_score": vuln.cvss_score,
                "exploitable": vuln.exploitable,
            }
            for vuln in report.vulnerabilities
        ]

        # Generate markdown report
        report_markdown = agent.generate_security_report_markdown(report)

        logger.info(
            f"Security validation for {current_user.username}: "
            f"Risk score {report.risk_score:.1f}/10"
        )

        return SecurityValidationResponse(
            success=True,
            scan_id=report.scan_id,
            risk_score=report.risk_score,
            vulnerabilities=vulnerabilities,
            compliance_status=report.compliance_status,
            recommendations=report.recommendations,
            blocked_patterns=report.blocked_patterns,
            safe_patterns=report.safe_patterns,
            report_markdown=report_markdown,
        )

    except Exception as e:
        logger.error(f"Security validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Security validation failed: {str(e)}")


@router.post("/batch-validate")
async def batch_validate_scripts(
    scripts: List[SecurityValidationRequest],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Validate multiple scripts in batch

    Useful for scanning entire projects or multiple files at once.
    """
    if len(scripts) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 scripts per batch")

    try:
        agent = get_security_agent()
        results = []

        for script_request in scripts:
            report = agent.validate_script(
                script_request.script_code, script_type=script_request.script_type
            )

            results.append(
                {
                    "script_type": script_request.script_type,
                    "risk_score": report.risk_score,
                    "critical_issues": len(
                        [v for v in report.vulnerabilities if v.threat_level.value == "critical"]
                    ),
                    "high_issues": len(
                        [v for v in report.vulnerabilities if v.threat_level.value == "high"]
                    ),
                    "compliant": report.compliance_status.get("roblox_tos_compliant", False),
                }
            )

        logger.info(
            f"Batch validation for {current_user.username}: " f"{len(scripts)} scripts validated"
        )

        return {
            "success": True,
            "scripts_validated": len(scripts),
            "results": results,
            "summary": {
                "avg_risk_score": sum(r["risk_score"] for r in results) / len(results),
                "total_critical": sum(r["critical_issues"] for r in results),
                "total_high": sum(r["high_issues"] for r in results),
                "all_compliant": all(r["compliant"] for r in results),
            },
        }

    except Exception as e:
        logger.error(f"Batch validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch validation failed: {str(e)}")


@router.get("/templates")
async def get_content_templates(current_user: User = Depends(get_current_user)):
    """Get available content generation templates"""
    return {
        "subjects": [
            "Mathematics",
            "Science",
            "History",
            "Language",
            "Geography",
            "Art",
            "Music",
            "Computer Science",
        ],
        "activity_types": ["quiz", "lesson", "experiment", "exploration", "interactive"],
        "grade_levels": list(range(1, 13)),
        "accessibility_features": [
            "text-to-speech",
            "high-contrast",
            "subtitles",
            "colorblind-mode",
            "keyboard-navigation",
            "screen-reader",
        ],
        "optimization_levels": ["conservative", "balanced", "aggressive"],
        "script_types": ["ServerScript", "LocalScript", "ModuleScript"],
    }


# Export router
__all__ = ["router"]
