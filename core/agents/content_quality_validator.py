"""
Content Quality Validator Agent

Comprehensive quality validation for educational content generated for Roblox environments.
Validates educational value, technical quality, safety, and compliance with standards.

Author: ToolboxAI Team
Created: 2025-09-19
Version: 2.0.0
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from core.agents.base_agent import AgentConfig, BaseAgent

logger = logging.getLogger(__name__)


class ValidationCategory(Enum):
    """Categories of content validation"""

    EDUCATIONAL_VALUE = "educational_value"
    TECHNICAL_QUALITY = "technical_quality"
    SAFETY_COMPLIANCE = "safety_compliance"
    ENGAGEMENT_DESIGN = "engagement_design"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    LOCALIZATION = "localization"
    MONETIZATION = "monetization"


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""

    CRITICAL = "critical"  # Must fix before deployment
    HIGH = "high"  # Should fix before deployment
    MEDIUM = "medium"  # Can fix after deployment
    LOW = "low"  # Minor improvements
    INFO = "info"  # Suggestions only


@dataclass
class ValidationIssue:
    """Represents a validation issue found in content"""

    category: ValidationCategory
    severity: ValidationSeverity
    description: str
    location: Optional[str] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    fixed: bool = False


@dataclass
class ValidationReport:
    """Comprehensive validation report for content"""

    content_id: str
    validated_at: datetime = field(default_factory=datetime.now)

    # Overall scores (0-1 scale)
    overall_score: float = 0.0
    educational_score: float = 0.0
    technical_score: float = 0.0
    safety_score: float = 0.0
    engagement_score: float = 0.0
    accessibility_score: float = 0.0

    # Detailed findings
    issues: list[ValidationIssue] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Recommendations
    recommendations: list[str] = field(default_factory=list)
    best_practices: list[str] = field(default_factory=list)

    # Compliance
    compliant: bool = False
    compliance_details: dict[str, bool] = field(default_factory=dict)

    # Metadata
    validation_duration: float = 0.0
    validator_version: str = "2.0.0"


class ContentQualityValidator(BaseAgent):
    """
    Specialized agent for validating educational content quality

    Performs comprehensive validation across multiple dimensions:
    - Educational alignment and value
    - Technical quality and performance
    - Safety and age-appropriateness
    - Accessibility standards
    - Engagement design principles
    """

    def __init__(self):
        """Initialize the content quality validator"""

        config = AgentConfig(
            name="ContentQualityValidator",
            model="gpt-4-turbo-preview",
            temperature=0.2,  # Lower temperature for consistent validation
            max_retries=3,
            timeout=300,
            verbose=True,
            system_prompt=self._get_validator_system_prompt(),
        )

        super().__init__(config)

        # Validation rules and thresholds
        self.validation_rules = self._load_validation_rules()
        self.quality_thresholds = self._load_quality_thresholds()

        # Roblox-specific validators
        self.script_patterns = self._load_script_patterns()
        self.asset_validators = self._load_asset_validators()

        logger.info("Content Quality Validator initialized")

    def _get_validator_system_prompt(self) -> str:
        """Get the system prompt for the validator"""
        return """You are an expert Content Quality Validator for educational Roblox experiences.

Your responsibilities include:

1. **Educational Validation**:
   - Verify alignment with learning objectives
   - Check age-appropriate content
   - Ensure pedagogical soundness
   - Validate assessment methods

2. **Technical Validation**:
   - Check Luau script quality and security
   - Validate performance optimization
   - Ensure cross-platform compatibility
   - Verify asset optimization

3. **Safety & Compliance**:
   - COPPA compliance verification
   - Content rating appropriateness
   - Privacy protection measures
   - Community guidelines adherence

4. **Engagement & Design**:
   - Game mechanics evaluation
   - User experience assessment
   - Progression system validation
   - Reward structure analysis

5. **Accessibility**:
   - WCAG 2.1 compliance
   - Color contrast verification
   - Text readability assessment
   - Control accessibility

Always provide specific, actionable feedback with severity levels and improvement suggestions.
"""

    def _load_validation_rules(self) -> dict[str, Any]:
        """Load validation rules for different content aspects"""
        return {
            "educational": {
                "min_learning_objectives": 3,
                "max_cognitive_load": 7,
                "required_assessment_types": ["formative", "summative"],
                "bloom_levels": ["remember", "understand", "apply", "analyze"],
            },
            "technical": {
                "max_script_complexity": 100,  # Cyclomatic complexity
                "max_asset_size_mb": 10,
                "min_fps": 30,
                "max_memory_usage_mb": 512,
                "required_error_handling": True,
            },
            "safety": {
                "prohibited_patterns": [
                    r"personal\s+information",
                    r"real\s+name",
                    r"phone\s+number",
                    r"address",
                    r"email",
                ],
                "age_ratings": {
                    "E": {"min_age": 0, "max_age": 10},
                    "E10+": {"min_age": 10, "max_age": 13},
                    "T": {"min_age": 13, "max_age": 18},
                },
            },
            "engagement": {
                "min_interaction_frequency": 30,  # seconds
                "max_idle_time": 120,  # seconds
                "required_feedback_types": ["visual", "audio", "haptic"],
                "progression_requirements": ["clear_goals", "milestones", "rewards"],
            },
        }

    def _load_quality_thresholds(self) -> dict[str, float]:
        """Load quality score thresholds"""
        return {
            "minimum_overall": 0.7,
            "minimum_educational": 0.8,
            "minimum_technical": 0.6,
            "minimum_safety": 0.9,
            "minimum_engagement": 0.6,
            "minimum_accessibility": 0.7,
        }

    def _load_script_patterns(self) -> dict[str, Any]:
        """Load Roblox Luau script validation patterns"""
        return {
            "security_vulnerabilities": [
                r"loadstring",  # Dynamic code execution
                r"getfenv",  # Environment manipulation
                r"setfenv",  # Environment manipulation
                r"rawset",  # Bypassing metatables
            ],
            "performance_issues": [
                r"while\s+true\s+do(?!\s*wait)",  # Infinite loops without yields
                r"for\s+.*\s+in\s+pairs.*FindFirstChild",  # Inefficient searches
                r"\.Parent\.Parent\.Parent",  # Deep parent chains
            ],
            "best_practices": {
                "use_services": r"game\.(Workspace|Players|ReplicatedStorage)",
                "proper_waits": r"wait\(\)|task\.wait\(\)",
                "event_cleanup": r":Disconnect\(\)",
                "type_checking": r"typeof\(.*\)\s*==",
            },
        }

    def _load_asset_validators(self) -> dict[str, Any]:
        """Load asset validation criteria"""
        return {
            "textures": {
                "max_resolution": 2048,
                "supported_formats": ["png", "jpg", "tga"],
                "max_file_size_mb": 5,
            },
            "models": {"max_polygons": 10000, "max_draw_calls": 50, "required_lods": 3},
            "audio": {
                "max_duration_seconds": 120,
                "supported_formats": ["mp3", "ogg"],
                "max_file_size_mb": 10,
            },
        }

    async def validate_content(
        self, content: dict[str, Any], content_type: str, target_age: int = 10
    ) -> ValidationReport:
        """
        Main entry point for content validation

        Args:
            content: Content to validate
            content_type: Type of content (lesson, quiz, activity, etc.)
            target_age: Target age for the content

        Returns:
            Comprehensive validation report
        """
        logger.info(f"Starting validation for {content_type} content")

        report = ValidationReport(content_id=content.get("id", "unknown"))

        start_time = datetime.now()

        try:
            # Run all validation categories in parallel
            validation_tasks = [
                self._validate_educational_value(content, content_type, report),
                self._validate_technical_quality(content, report),
                self._validate_safety_compliance(content, target_age, report),
                self._validate_engagement_design(content, report),
                self._validate_accessibility(content, report),
                self._validate_performance(content, report),
            ]

            results = await asyncio.gather(*validation_tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Validation task {i} failed: {result}")
                    report.issues.append(
                        ValidationIssue(
                            category=ValidationCategory.TECHNICAL_QUALITY,
                            severity=ValidationSeverity.HIGH,
                            description=f"Validation error: {str(result)}",
                        )
                    )

            # Calculate overall scores
            report.overall_score = self._calculate_overall_score(report)

            # Determine compliance
            report.compliant = self._check_compliance(report)

            # Generate recommendations
            report.recommendations = self._generate_recommendations(report)

        except Exception as e:
            logger.error(f"Content validation failed: {e}")
            report.issues.append(
                ValidationIssue(
                    category=ValidationCategory.TECHNICAL_QUALITY,
                    severity=ValidationSeverity.CRITICAL,
                    description=f"Critical validation failure: {str(e)}",
                )
            )

        finally:
            report.validation_duration = (datetime.now() - start_time).total_seconds()

        return report

    async def _validate_educational_value(
        self, content: dict[str, Any], content_type: str, report: ValidationReport
    ) -> None:
        """Validate educational value and alignment"""

        rules = self.validation_rules["educational"]
        score = 1.0

        # Check learning objectives
        objectives = content.get("learning_objectives", [])
        if len(objectives) < rules["min_learning_objectives"]:
            report.issues.append(
                ValidationIssue(
                    category=ValidationCategory.EDUCATIONAL_VALUE,
                    severity=ValidationSeverity.HIGH,
                    description=f"Insufficient learning objectives: {len(objectives)} < {rules['min_learning_objectives']}",
                    suggestion="Add more specific learning objectives",
                )
            )
            score -= 0.2
        else:
            report.passed_checks.append("Adequate learning objectives")

        # Validate Bloom's taxonomy coverage
        bloom_coverage = self._check_bloom_coverage(objectives, rules["bloom_levels"])
        if bloom_coverage < 0.5:
            report.issues.append(
                ValidationIssue(
                    category=ValidationCategory.EDUCATIONAL_VALUE,
                    severity=ValidationSeverity.MEDIUM,
                    description="Limited cognitive level coverage",
                    suggestion="Include higher-order thinking activities",
                )
            )
            score -= 0.1

        # Check assessment integration
        if content_type in ["lesson", "activity"]:
            assessments = content.get("assessments", [])
            if not self._has_required_assessments(assessments, rules["required_assessment_types"]):
                report.issues.append(
                    ValidationIssue(
                        category=ValidationCategory.EDUCATIONAL_VALUE,
                        severity=ValidationSeverity.MEDIUM,
                        description="Missing required assessment types",
                        suggestion="Add both formative and summative assessments",
                    )
                )
                score -= 0.15

        report.educational_score = max(0, score)

    async def _validate_technical_quality(
        self, content: dict[str, Any], report: ValidationReport
    ) -> None:
        """Validate technical quality of scripts and assets"""

        self.validation_rules["technical"]
        score = 1.0

        # Validate scripts
        scripts = content.get("scripts", [])
        for script in scripts:
            script_issues = self._validate_script(script)
            report.issues.extend(script_issues)
            if script_issues:
                score -= 0.1 * len(
                    [
                        i
                        for i in script_issues
                        if i.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH]
                    ]
                )

        # Validate assets
        assets = content.get("assets", [])
        for asset in assets:
            asset_issues = self._validate_asset(asset)
            report.issues.extend(asset_issues)
            if asset_issues:
                score -= 0.05 * len(
                    [i for i in asset_issues if i.severity == ValidationSeverity.HIGH]
                )

        # Check error handling
        if not self._has_proper_error_handling(scripts):
            report.issues.append(
                ValidationIssue(
                    category=ValidationCategory.TECHNICAL_QUALITY,
                    severity=ValidationSeverity.HIGH,
                    description="Missing error handling in scripts",
                    suggestion="Add try-catch blocks and error recovery",
                )
            )
            score -= 0.15

        report.technical_score = max(0, score)

    async def _validate_safety_compliance(
        self, content: dict[str, Any], target_age: int, report: ValidationReport
    ) -> None:
        """Validate safety and compliance requirements"""

        rules = self.validation_rules["safety"]
        score = 1.0

        # Check for prohibited content patterns
        content_text = self._extract_all_text(content)
        for pattern in rules["prohibited_patterns"]:
            if re.search(pattern, content_text, re.IGNORECASE):
                report.issues.append(
                    ValidationIssue(
                        category=ValidationCategory.SAFETY_COMPLIANCE,
                        severity=ValidationSeverity.CRITICAL,
                        description=f"Prohibited content pattern detected: {pattern}",
                        suggestion="Remove personal information requests",
                    )
                )
                score -= 0.3

        # Verify age appropriateness
        age_rating = self._determine_age_rating(content)
        if not self._is_age_appropriate(age_rating, target_age, rules["age_ratings"]):
            report.issues.append(
                ValidationIssue(
                    category=ValidationCategory.SAFETY_COMPLIANCE,
                    severity=ValidationSeverity.HIGH,
                    description=f"Content not appropriate for age {target_age}",
                    suggestion="Adjust content complexity and themes",
                )
            )
            score -= 0.2

        # Check COPPA compliance
        if target_age < 13:
            coppa_issues = self._check_coppa_compliance(content)
            report.issues.extend(coppa_issues)
            if coppa_issues:
                score -= 0.2

        report.safety_score = max(0, score)
        report.compliance_details["COPPA"] = (
            len([i for i in report.issues if "COPPA" in i.description]) == 0
        )

    async def _validate_engagement_design(
        self, content: dict[str, Any], report: ValidationReport
    ) -> None:
        """Validate engagement and game design principles"""

        rules = self.validation_rules["engagement"]
        score = 1.0

        # Check interaction frequency
        interactions = content.get("interactions", [])
        if not interactions:
            report.issues.append(
                ValidationIssue(
                    category=ValidationCategory.ENGAGEMENT_DESIGN,
                    severity=ValidationSeverity.HIGH,
                    description="No interactive elements found",
                    suggestion="Add interactive gameplay elements",
                )
            )
            score -= 0.3

        # Validate feedback mechanisms
        feedback_types = content.get("feedback_types", [])
        missing_feedback = [
            ft for ft in rules["required_feedback_types"] if ft not in feedback_types
        ]
        if missing_feedback:
            report.issues.append(
                ValidationIssue(
                    category=ValidationCategory.ENGAGEMENT_DESIGN,
                    severity=ValidationSeverity.MEDIUM,
                    description=f"Missing feedback types: {missing_feedback}",
                    suggestion="Add visual and audio feedback for actions",
                )
            )
            score -= 0.1

        # Check progression system
        progression = content.get("progression", {})
        if not self._has_valid_progression(progression, rules["progression_requirements"]):
            report.issues.append(
                ValidationIssue(
                    category=ValidationCategory.ENGAGEMENT_DESIGN,
                    severity=ValidationSeverity.MEDIUM,
                    description="Incomplete progression system",
                    suggestion="Add clear goals, milestones, and rewards",
                )
            )
            score -= 0.15

        report.engagement_score = max(0, score)

    async def _validate_accessibility(
        self, content: dict[str, Any], report: ValidationReport
    ) -> None:
        """Validate accessibility standards"""

        score = 1.0

        # Check color contrast
        ui_elements = content.get("ui_elements", [])
        contrast_issues = self._check_color_contrast(ui_elements)
        if contrast_issues:
            report.issues.extend(contrast_issues)
            score -= 0.1 * len(contrast_issues)

        # Validate text readability
        text_elements = content.get("text_elements", [])
        readability_issues = self._check_readability(text_elements)
        if readability_issues:
            report.issues.extend(readability_issues)
            score -= 0.05 * len(readability_issues)

        # Check control accessibility
        controls = content.get("controls", [])
        if not self._has_accessible_controls(controls):
            report.issues.append(
                ValidationIssue(
                    category=ValidationCategory.ACCESSIBILITY,
                    severity=ValidationSeverity.MEDIUM,
                    description="Controls not fully accessible",
                    suggestion="Add keyboard navigation and screen reader support",
                )
            )
            score -= 0.15

        report.accessibility_score = max(0, score)

    async def _validate_performance(
        self, content: dict[str, Any], report: ValidationReport
    ) -> None:
        """Validate performance characteristics"""

        rules = self.validation_rules["technical"]
        score = 1.0

        # Estimate performance metrics
        estimated_fps = self._estimate_fps(content)
        if estimated_fps < rules["min_fps"]:
            report.issues.append(
                ValidationIssue(
                    category=ValidationCategory.PERFORMANCE,
                    severity=ValidationSeverity.HIGH,
                    description=f"Low estimated FPS: {estimated_fps}",
                    suggestion="Optimize rendering and reduce complexity",
                )
            )
            score -= 0.2

        # Check memory usage
        estimated_memory = self._estimate_memory_usage(content)
        if estimated_memory > rules["max_memory_usage_mb"]:
            report.issues.append(
                ValidationIssue(
                    category=ValidationCategory.PERFORMANCE,
                    severity=ValidationSeverity.HIGH,
                    description=f"High memory usage: {estimated_memory}MB",
                    suggestion="Optimize assets and reduce memory footprint",
                )
            )
            score -= 0.15

        # Validate asset optimization
        assets = content.get("assets", [])
        unoptimized = [a for a in assets if not self._is_asset_optimized(a)]
        if unoptimized:
            report.warnings.append(f"{len(unoptimized)} unoptimized assets detected")
            score -= 0.05

        # Performance score is factored into technical score
        report.technical_score = min(report.technical_score, score)

    def _validate_script(self, script: dict[str, Any]) -> list[ValidationIssue]:
        """Validate a single script"""
        issues = []
        code = script.get("code", "")

        # Check for security vulnerabilities
        for pattern in self.script_patterns["security_vulnerabilities"]:
            if re.search(pattern, code):
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.TECHNICAL_QUALITY,
                        severity=ValidationSeverity.CRITICAL,
                        description=f"Security vulnerability: {pattern}",
                        location=script.get("name", "unknown"),
                        suggestion="Remove unsafe code patterns",
                    )
                )

        # Check for performance issues
        for pattern in self.script_patterns["performance_issues"]:
            if re.search(pattern, code):
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.PERFORMANCE,
                        severity=ValidationSeverity.HIGH,
                        description=f"Performance issue detected",
                        location=script.get("name", "unknown"),
                        suggestion="Optimize script for better performance",
                    )
                )

        return issues

    def _validate_asset(self, asset: dict[str, Any]) -> list[ValidationIssue]:
        """Validate a single asset"""
        issues = []
        asset_type = asset.get("type", "unknown")

        if asset_type in self.asset_validators:
            validator = self.asset_validators[asset_type]

            # Check file size
            file_size_mb = asset.get("file_size_mb", 0)
            if file_size_mb > validator.get("max_file_size_mb", float("inf")):
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.PERFORMANCE,
                        severity=ValidationSeverity.HIGH,
                        description=f"Asset too large: {file_size_mb}MB",
                        location=asset.get("name", "unknown"),
                        suggestion="Compress or optimize the asset",
                    )
                )

        return issues

    def _check_bloom_coverage(self, objectives: list[str], required_levels: list[str]) -> float:
        """Check coverage of Bloom's taxonomy levels"""
        covered = 0
        for level in required_levels:
            if any(level.lower() in obj.lower() for obj in objectives):
                covered += 1
        return covered / len(required_levels) if required_levels else 0

    def _has_required_assessments(self, assessments: list[dict], required_types: list[str]) -> bool:
        """Check if required assessment types are present"""
        assessment_types = [a.get("type", "") for a in assessments]
        return all(rt in assessment_types for rt in required_types)

    def _has_proper_error_handling(self, scripts: list[dict]) -> bool:
        """Check if scripts have proper error handling"""
        for script in scripts:
            code = script.get("code", "")
            if "pcall" not in code and "xpcall" not in code:
                return False
        return True

    def _extract_all_text(self, content: dict[str, Any]) -> str:
        """Extract all text content for analysis"""
        text_parts = []

        def extract_recursive(obj):
            if isinstance(obj, str):
                text_parts.append(obj)
            elif isinstance(obj, dict):
                for value in obj.values():
                    extract_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)

        extract_recursive(content)
        return " ".join(text_parts)

    def _determine_age_rating(self, content: dict[str, Any]) -> str:
        """Determine appropriate age rating for content"""
        # Simplified implementation
        complexity = content.get("complexity", "medium")
        if complexity == "low":
            return "E"
        elif complexity == "medium":
            return "E10+"
        else:
            return "T"

    def _is_age_appropriate(self, rating: str, target_age: int, ratings: dict) -> bool:
        """Check if content rating is appropriate for target age"""
        if rating in ratings:
            age_range = ratings[rating]
            return age_range["min_age"] <= target_age <= age_range["max_age"]
        return True

    def _check_coppa_compliance(self, content: dict[str, Any]) -> list[ValidationIssue]:
        """Check COPPA compliance for content targeting children under 13"""
        issues = []

        # Check for data collection
        if content.get("collects_data", False):
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.SAFETY_COMPLIANCE,
                    severity=ValidationSeverity.CRITICAL,
                    description="COPPA: Data collection from children under 13",
                    suggestion="Remove data collection or add parental consent",
                )
            )

        return issues

    def _has_valid_progression(self, progression: dict, requirements: list[str]) -> bool:
        """Check if progression system meets requirements"""
        return all(req in progression for req in requirements)

    def _check_color_contrast(self, ui_elements: list[dict]) -> list[ValidationIssue]:
        """Check color contrast for accessibility"""
        issues = []
        # Simplified - would use actual contrast calculation
        for element in ui_elements:
            if element.get("contrast_ratio", 4.5) < 4.5:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.ACCESSIBILITY,
                        severity=ValidationSeverity.MEDIUM,
                        description="Insufficient color contrast",
                        location=element.get("name", "unknown"),
                        suggestion="Increase contrast to at least 4.5:1",
                    )
                )
        return issues

    def _check_readability(self, text_elements: list[dict]) -> list[ValidationIssue]:
        """Check text readability"""
        issues = []
        for element in text_elements:
            if element.get("font_size", 12) < 12:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.ACCESSIBILITY,
                        severity=ValidationSeverity.LOW,
                        description="Font size too small",
                        location=element.get("name", "unknown"),
                        suggestion="Use minimum 12pt font size",
                    )
                )
        return issues

    def _has_accessible_controls(self, controls: list[dict]) -> bool:
        """Check if controls are accessible"""
        return all(c.get("keyboard_accessible", False) for c in controls)

    def _estimate_fps(self, content: dict[str, Any]) -> float:
        """Estimate FPS based on content complexity"""
        # Simplified estimation
        base_fps = 60
        complexity = content.get("complexity_score", 0.5)
        return base_fps * (1 - complexity * 0.5)

    def _estimate_memory_usage(self, content: dict[str, Any]) -> float:
        """Estimate memory usage in MB"""
        # Simplified estimation
        base_memory = 100
        assets = content.get("assets", [])
        scripts = content.get("scripts", [])
        return base_memory + len(assets) * 10 + len(scripts) * 2

    def _is_asset_optimized(self, asset: dict[str, Any]) -> bool:
        """Check if an asset is optimized"""
        return asset.get("optimized", False)

    def _calculate_overall_score(self, report: ValidationReport) -> float:
        """Calculate overall quality score"""
        scores = [
            report.educational_score * 0.30,
            report.technical_score * 0.20,
            report.safety_score * 0.25,
            report.engagement_score * 0.15,
            report.accessibility_score * 0.10,
        ]
        return sum(scores)

    def _check_compliance(self, report: ValidationReport) -> bool:
        """Check if content meets compliance requirements"""
        thresholds = self.quality_thresholds

        # Check critical issues
        critical_issues = [i for i in report.issues if i.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            return False

        # Check minimum scores
        return (
            report.overall_score >= thresholds["minimum_overall"]
            and report.educational_score >= thresholds["minimum_educational"]
            and report.safety_score >= thresholds["minimum_safety"]
        )

    def _generate_recommendations(self, report: ValidationReport) -> list[str]:
        """Generate improvement recommendations based on validation results"""
        recommendations = []

        # Score-based recommendations
        if report.educational_score < 0.8:
            recommendations.append(
                "Enhance educational value by adding more learning objectives and assessments"
            )

        if report.technical_score < 0.7:
            recommendations.append(
                "Improve technical quality through code optimization and error handling"
            )

        if report.engagement_score < 0.7:
            recommendations.append(
                "Increase engagement with more interactive elements and feedback mechanisms"
            )

        # Issue-based recommendations
        high_priority_issues = [
            i
            for i in report.issues
            if i.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH]
        ]
        if high_priority_issues:
            recommendations.append(
                f"Address {len(high_priority_issues)} high-priority issues before deployment"
            )

        return recommendations

    async def _process_task(self, state: dict[str, Any]) -> Any:
        """Process a validation task"""
        content = state.get("content", {})
        content_type = state.get("content_type", "lesson")
        target_age = state.get("target_age", 10)

        report = await self.validate_content(content, content_type, target_age)

        return {
            "validation_report": report.__dict__,
            "compliant": report.compliant,
            "overall_score": report.overall_score,
            "issues_count": len(report.issues),
            "recommendations": report.recommendations,
        }

    async def auto_fix_issues(
        self, content: dict[str, Any], report: ValidationReport
    ) -> tuple[dict[str, Any], list[ValidationIssue]]:
        """
        Attempt to automatically fix certain validation issues

        Args:
            content: Content to fix
            report: Validation report with issues

        Returns:
            Fixed content and list of fixed issues
        """
        fixed_content = content.copy()
        fixed_issues = []

        for issue in report.issues:
            if issue.auto_fixable and not issue.fixed:
                try:
                    fixed_content = await self._apply_auto_fix(fixed_content, issue)
                    issue.fixed = True
                    fixed_issues.append(issue)
                except Exception as e:
                    logger.error(f"Failed to auto-fix issue: {e}")

        return fixed_content, fixed_issues

    async def _apply_auto_fix(
        self, content: dict[str, Any], issue: ValidationIssue
    ) -> dict[str, Any]:
        """Apply automatic fix for an issue"""
        # Implementation would depend on specific issue types
        # This is a placeholder for the auto-fix logic
        return content
