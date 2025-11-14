"""Educational Validation Agent for Content Quality Assurance

This agent validates educational content for quality, appropriateness,
accuracy, and compliance with educational standards and safety guidelines.
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from ..base_agent import AgentConfig, BaseAgent, TaskResult


class ValidationStatus(Enum):
    """Status of content validation."""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    PENDING_REVIEW = "pending_review"
    CONDITIONALLY_APPROVED = "conditionally_approved"


class ValidationCategory(Enum):
    """Categories of validation checks."""

    CONTENT_ACCURACY = "content_accuracy"
    AGE_APPROPRIATENESS = "age_appropriateness"
    SAFETY_COMPLIANCE = "safety_compliance"
    EDUCATIONAL_VALUE = "educational_value"
    ACCESSIBILITY = "accessibility"
    CULTURAL_SENSITIVITY = "cultural_sensitivity"
    TECHNICAL_QUALITY = "technical_quality"
    ENGAGEMENT_POTENTIAL = "engagement_potential"
    CURRICULUM_ALIGNMENT = "curriculum_alignment"


class SeverityLevel(Enum):
    """Severity levels for validation issues."""

    CRITICAL = "critical"  # Must fix before approval
    HIGH = "high"  # Should fix before approval
    MEDIUM = "medium"  # Recommended to fix
    LOW = "low"  # Minor suggestion
    INFO = "info"  # Informational only


class ContentRating(Enum):
    """Content rating for age appropriateness."""

    EC = "early_childhood"  # Ages 3-6
    E = "everyone"  # Ages 6+
    E10 = "everyone_10+"  # Ages 10+
    T = "teen"  # Ages 13+
    M = "mature"  # Ages 17+


@dataclass
class ValidationIssue:
    """Individual validation issue found in content."""

    issue_id: str
    category: ValidationCategory
    severity: SeverityLevel
    description: str
    location: Optional[str] = None
    suggestion: Optional[str] = None
    rule_violated: Optional[str] = None
    evidence: Optional[str] = None
    auto_fixable: bool = False
    fixed: bool = False


@dataclass
class ValidationRule:
    """Rule for content validation."""

    rule_id: str
    category: ValidationCategory
    name: str
    description: str
    check_function: str  # Name of function to execute
    severity: SeverityLevel
    applicable_grades: list[str]
    applicable_subjects: list[str]
    enabled: bool = True


@dataclass
class ValidationResult:
    """Complete validation result for content."""

    content_id: str
    validation_id: str
    timestamp: datetime
    status: ValidationStatus
    overall_score: float  # 0-100

    # Category scores
    category_scores: dict[ValidationCategory, float]

    # Issues found
    issues: list[ValidationIssue]
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int

    # Recommendations
    recommendations: list[str]
    required_changes: list[str]
    suggested_improvements: list[str]

    # Compliance
    content_rating: ContentRating
    compliant_standards: list[str]
    non_compliant_standards: list[str]

    # Additional metadata
    validator_version: str = "1.0.0"
    validation_duration: float = 0.0
    auto_fixes_applied: int = 0
    manual_review_required: bool = False


@dataclass
class SafetyCheck:
    """Safety check for content."""

    check_id: str
    category: str
    passed: bool
    details: str
    flagged_content: Optional[list[str]] = None


@dataclass
class AccessibilityCheck:
    """Accessibility compliance check."""

    standard: str  # WCAG 2.1, Section 508, etc.
    level: str  # A, AA, AAA
    passed: bool
    violations: list[str]
    recommendations: list[str]


class EducationalValidationAgent(BaseAgent):
    """
    Agent for validating educational content quality and appropriateness.

    Capabilities:
    - Content accuracy verification
    - Age appropriateness checking
    - Safety and compliance validation
    - Educational value assessment
    - Accessibility checking
    - Cultural sensitivity review
    """

    def __init__(self):
        """Initialize the Educational Validation Agent."""
        config = AgentConfig(name="EducationalValidationAgent")
        super().__init__(config)

        # Initialize validation rules
        self.validation_rules = self._initialize_validation_rules()

        # Content filters
        self.inappropriate_words = self._load_inappropriate_words()
        self.educational_keywords = self._load_educational_keywords()

        # Grade-level reading formulas coefficients
        self.readability_formulas = {
            "flesch_kincaid": {
                "sentence_weight": 0.39,
                "syllable_weight": 11.8,
                "constant": -15.59,
            },
            "gunning_fog": {"complex_word_weight": 0.4, "sentence_weight": 100},
            "coleman_liau": {
                "character_weight": 0.0588,
                "sentence_weight": 0.296,
                "constant": -15.8,
            },
        }

        # Safety guidelines
        self.safety_guidelines = self._initialize_safety_guidelines()

    async def process(self, task_data: dict[str, Any]) -> TaskResult:
        """
        Process validation request.

        Args:
            task_data: Contains content to validate and validation parameters

        Returns:
            TaskResult with validation results
        """
        validation_type = task_data.get("validation_type", "comprehensive")

        try:
            if validation_type == "comprehensive":
                result = await self.comprehensive_validation(task_data)
            elif validation_type == "quick_check":
                result = await self.quick_validation(task_data)
            elif validation_type == "safety_only":
                result = await self.safety_validation(task_data)
            elif validation_type == "accessibility":
                result = await self.accessibility_validation(task_data)
            elif validation_type == "curriculum":
                result = await self.curriculum_validation(task_data)
            elif validation_type == "age_appropriate":
                result = await self.age_appropriateness_check(task_data)
            else:
                result = await self.comprehensive_validation(task_data)

            return TaskResult(
                success=True,
                data=result,
                metadata={
                    "validation_type": validation_type,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            return TaskResult(success=False, data={}, error=str(e))

    async def comprehensive_validation(self, data: dict[str, Any]) -> dict[str, Any]:
        """Perform comprehensive content validation."""
        content = data["content"]
        content_type = data.get("content_type", "lesson")
        grade_level = data.get("grade_level", "5")
        subject = data.get("subject", "general")

        validation_start = datetime.now()
        issues = []
        category_scores = {}

        # Run all validation categories
        validation_tasks = [
            self._validate_content_accuracy(content, subject),
            self._validate_age_appropriateness(content, grade_level),
            self._validate_safety_compliance(content),
            self._validate_educational_value(content, content_type),
            self._validate_accessibility(content),
            self._validate_cultural_sensitivity(content),
            self._validate_technical_quality(content),
            self._validate_engagement_potential(content, grade_level),
            self._validate_curriculum_alignment(content, grade_level, subject),
        ]

        results = await asyncio.gather(*validation_tasks)

        # Compile results
        for category, (score, category_issues) in enumerate(results):
            category_type = list(ValidationCategory)[category]
            category_scores[category_type] = score
            issues.extend(category_issues)

        # Calculate overall score
        overall_score = sum(category_scores.values()) / len(category_scores)

        # Count issues by severity
        issue_counts = self._count_issues_by_severity(issues)

        # Determine validation status
        status = self._determine_validation_status(
            overall_score, issue_counts["critical"], issue_counts["high"]
        )

        # Generate recommendations
        recommendations = await self._generate_recommendations(issues, category_scores)
        required_changes = [
            issue.suggestion
            for issue in issues
            if issue.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH] and issue.suggestion
        ]
        suggested_improvements = [
            issue.suggestion
            for issue in issues
            if issue.severity in [SeverityLevel.MEDIUM, SeverityLevel.LOW] and issue.suggestion
        ]

        # Determine content rating
        content_rating = await self._determine_content_rating(content, grade_level)

        # Check standards compliance
        compliant_standards, non_compliant = await self._check_standards_compliance(
            content, grade_level, subject
        )

        validation_result = ValidationResult(
            content_id=data.get("content_id", "unknown"),
            validation_id=f"val_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now(),
            status=status,
            overall_score=overall_score,
            category_scores=category_scores,
            issues=issues,
            critical_issues=issue_counts["critical"],
            high_issues=issue_counts["high"],
            medium_issues=issue_counts["medium"],
            low_issues=issue_counts["low"],
            recommendations=recommendations,
            required_changes=required_changes,
            suggested_improvements=suggested_improvements,
            content_rating=content_rating,
            compliant_standards=compliant_standards,
            non_compliant_standards=non_compliant,
            validation_duration=(datetime.now() - validation_start).total_seconds(),
            manual_review_required=issue_counts["critical"] > 0 or issue_counts["high"] > 3,
        )

        return {
            "validation_result": self._result_to_dict(validation_result),
            "summary": {
                "status": status.value,
                "score": overall_score,
                "can_publish": status
                in [ValidationStatus.APPROVED, ValidationStatus.CONDITIONALLY_APPROVED],
                "needs_review": validation_result.manual_review_required,
                "top_issues": self._get_top_issues(issues, 5),
            },
            "action_items": {
                "required": required_changes[:5],
                "suggested": suggested_improvements[:5],
            },
        }

    async def quick_validation(self, data: dict[str, Any]) -> dict[str, Any]:
        """Perform quick validation check on key criteria."""
        content = data["content"]
        grade_level = data.get("grade_level", "5")

        # Quick checks only
        safety_check = await self._quick_safety_check(content)
        appropriateness_check = await self._quick_appropriateness_check(content, grade_level)
        quality_check = await self._quick_quality_check(content)

        passed = all(
            [
                safety_check["passed"],
                appropriateness_check["passed"],
                quality_check["passed"],
            ]
        )

        return {
            "passed": passed,
            "checks": {
                "safety": safety_check,
                "appropriateness": appropriateness_check,
                "quality": quality_check,
            },
            "recommendation": (
                "Proceed with full validation" if passed else "Address issues before proceeding"
            ),
        }

    async def safety_validation(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate content for safety compliance only."""
        content = data["content"]

        safety_checks = []

        # Check for inappropriate content
        inappropriate = await self._check_inappropriate_content(content)
        safety_checks.append(
            SafetyCheck(
                check_id="inappropriate_content",
                category="language",
                passed=not inappropriate["found"],
                details=inappropriate["details"],
                flagged_content=inappropriate.get("flagged", []),
            )
        )

        # Check for violence/dangerous content
        violence = await self._check_violence_content(content)
        safety_checks.append(
            SafetyCheck(
                check_id="violence_check",
                category="content",
                passed=not violence["found"],
                details=violence["details"],
                flagged_content=violence.get("flagged", []),
            )
        )

        # Check for privacy/personal information
        privacy = await self._check_privacy_compliance(content)
        safety_checks.append(
            SafetyCheck(
                check_id="privacy_check",
                category="privacy",
                passed=privacy["compliant"],
                details=privacy["details"],
                flagged_content=privacy.get("flagged", []),
            )
        )

        # Check for copyright/plagiarism
        copyright_check = await self._check_copyright_compliance(content)
        safety_checks.append(
            SafetyCheck(
                check_id="copyright_check",
                category="legal",
                passed=copyright_check["compliant"],
                details=copyright_check["details"],
                flagged_content=copyright_check.get("flagged", []),
            )
        )

        # Overall safety status
        all_passed = all(check.passed for check in safety_checks)

        return {
            "safe_for_students": all_passed,
            "safety_checks": [
                {
                    "id": check.check_id,
                    "category": check.category,
                    "passed": check.passed,
                    "details": check.details,
                    "flagged": check.flagged_content,
                }
                for check in safety_checks
            ],
            "risk_level": "low" if all_passed else "high",
            "recommendations": self._generate_safety_recommendations(safety_checks),
        }

    async def accessibility_validation(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate content for accessibility compliance."""
        content = data["content"]
        standard = data.get("standard", "WCAG 2.1")
        level = data.get("level", "AA")

        checks = []

        # Text accessibility
        text_check = await self._check_text_accessibility(content)
        checks.append(
            AccessibilityCheck(
                standard=standard,
                level=level,
                passed=text_check["compliant"],
                violations=text_check.get("violations", []),
                recommendations=text_check.get("recommendations", []),
            )
        )

        # Media accessibility
        if data.get("has_media", False):
            media_check = await self._check_media_accessibility(content)
            checks.append(
                AccessibilityCheck(
                    standard=standard,
                    level=level,
                    passed=media_check["compliant"],
                    violations=media_check.get("violations", []),
                    recommendations=media_check.get("recommendations", []),
                )
            )

        # Interactive elements accessibility
        if data.get("has_interactive", False):
            interactive_check = await self._check_interactive_accessibility(content)
            checks.append(
                AccessibilityCheck(
                    standard=standard,
                    level=level,
                    passed=interactive_check["compliant"],
                    violations=interactive_check.get("violations", []),
                    recommendations=interactive_check.get("recommendations", []),
                )
            )

        all_compliant = all(check.passed for check in checks)

        return {
            "accessible": all_compliant,
            "standard": standard,
            "level": level,
            "compliance_checks": [
                {
                    "standard": check.standard,
                    "level": check.level,
                    "passed": check.passed,
                    "violations": check.violations,
                    "recommendations": check.recommendations,
                }
                for check in checks
            ],
            "accessibility_score": (
                sum(1 for check in checks if check.passed) / len(checks) * 100 if checks else 100
            ),
            "improvement_guide": await self._generate_accessibility_guide(checks),
        }

    async def curriculum_validation(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate content against curriculum standards."""
        content = data["content"]
        grade_level = data["grade_level"]
        subject = data["subject"]
        standards = data.get("standards", ["Common Core", "NGSS"])

        alignment_results = {}

        for standard in standards:
            alignment = await self._check_standard_alignment(
                content, standard, grade_level, subject
            )
            alignment_results[standard] = alignment

        # Calculate overall alignment score
        overall_alignment = (
            sum(result["score"] for result in alignment_results.values()) / len(alignment_results)
            if alignment_results
            else 0
        )

        return {
            "curriculum_aligned": overall_alignment >= 0.7,
            "alignment_score": overall_alignment,
            "standards_checked": standards,
            "alignment_details": alignment_results,
            "gaps_identified": self._identify_curriculum_gaps(alignment_results),
            "recommendations": await self._generate_curriculum_recommendations(
                alignment_results, grade_level, subject
            ),
        }

    async def age_appropriateness_check(self, data: dict[str, Any]) -> dict[str, Any]:
        """Check if content is age-appropriate."""
        content = data["content"]
        grade_level = data["grade_level"]

        # Calculate readability scores
        readability = await self._calculate_readability(content)

        # Check vocabulary complexity
        vocabulary = await self._analyze_vocabulary_complexity(content, grade_level)

        # Check concept complexity
        concepts = await self._analyze_concept_complexity(content, grade_level)

        # Check content themes
        themes = await self._analyze_content_themes(content, grade_level)

        # Determine appropriate grade range
        appropriate_grades = self._determine_appropriate_grades(readability, vocabulary, concepts)

        # Check if target grade is in appropriate range
        is_appropriate = self._grade_in_range(grade_level, appropriate_grades)

        return {
            "age_appropriate": is_appropriate,
            "target_grade": grade_level,
            "recommended_grades": appropriate_grades,
            "readability_scores": readability,
            "vocabulary_analysis": vocabulary,
            "concept_complexity": concepts,
            "theme_analysis": themes,
            "adjustments_needed": self._suggest_age_adjustments(
                grade_level, appropriate_grades, readability, vocabulary
            ),
        }

    # Validation helper methods

    async def _validate_content_accuracy(
        self, content: str, subject: str
    ) -> tuple[float, list[ValidationIssue]]:
        """Validate content accuracy for the subject."""
        issues = []
        score = 100.0

        # Check for factual errors (simplified check)
        factual_errors = await self._check_factual_accuracy(content, subject)
        for error in factual_errors:
            issues.append(
                ValidationIssue(
                    issue_id=f"accuracy_{len(issues)}",
                    category=ValidationCategory.CONTENT_ACCURACY,
                    severity=SeverityLevel.HIGH,
                    description=error["description"],
                    location=error.get("location"),
                    suggestion=error.get("correction"),
                    evidence=error.get("source"),
                )
            )
            score -= 10

        # Check for outdated information
        if await self._contains_outdated_info(content):
            issues.append(
                ValidationIssue(
                    issue_id=f"accuracy_{len(issues)}",
                    category=ValidationCategory.CONTENT_ACCURACY,
                    severity=SeverityLevel.MEDIUM,
                    description="Content may contain outdated information",
                    suggestion="Update with current information",
                )
            )
            score -= 5

        return max(0, score), issues

    async def _validate_age_appropriateness(
        self, content: str, grade_level: str
    ) -> tuple[float, list[ValidationIssue]]:
        """Validate age appropriateness of content."""
        issues = []
        score = 100.0

        # Check readability
        readability = await self._calculate_readability(content)
        target_level = self._grade_to_reading_level(grade_level)

        if abs(readability["grade_level"] - target_level) > 2:
            issues.append(
                ValidationIssue(
                    issue_id=f"age_{len(issues)}",
                    category=ValidationCategory.AGE_APPROPRIATENESS,
                    severity=SeverityLevel.HIGH,
                    description=f"Reading level ({readability['grade_level']}) doesn't match target grade ({target_level})",
                    suggestion="Adjust vocabulary and sentence complexity",
                )
            )
            score -= 20

        # Check for age-inappropriate content
        inappropriate = await self._check_age_inappropriate_content(content, grade_level)
        for item in inappropriate:
            issues.append(
                ValidationIssue(
                    issue_id=f"age_{len(issues)}",
                    category=ValidationCategory.AGE_APPROPRIATENESS,
                    severity=SeverityLevel.CRITICAL,
                    description=item["description"],
                    location=item.get("location"),
                    suggestion=item.get("suggestion"),
                )
            )
            score -= 25

        return max(0, score), issues

    async def _validate_safety_compliance(
        self, content: str
    ) -> tuple[float, list[ValidationIssue]]:
        """Validate safety compliance of content."""
        issues = []
        score = 100.0

        # Check for inappropriate language
        bad_words = self._find_inappropriate_words(content)
        for word in bad_words:
            issues.append(
                ValidationIssue(
                    issue_id=f"safety_{len(issues)}",
                    category=ValidationCategory.SAFETY_COMPLIANCE,
                    severity=SeverityLevel.CRITICAL,
                    description=f"Inappropriate language detected",
                    location=word["position"],
                    suggestion="Remove or replace inappropriate language",
                    auto_fixable=True,
                )
            )
            score -= 30

        # Check for unsafe instructions
        unsafe = await self._check_unsafe_instructions(content)
        for instruction in unsafe:
            issues.append(
                ValidationIssue(
                    issue_id=f"safety_{len(issues)}",
                    category=ValidationCategory.SAFETY_COMPLIANCE,
                    severity=SeverityLevel.CRITICAL,
                    description="Potentially unsafe instruction",
                    location=instruction.get("location"),
                    suggestion="Add safety warnings or remove unsafe content",
                )
            )
            score -= 25

        return max(0, score), issues

    async def _validate_educational_value(
        self, content: str, content_type: str
    ) -> tuple[float, list[ValidationIssue]]:
        """Validate educational value of content."""
        issues = []
        score = 100.0

        # Check for learning objectives
        has_objectives = await self._check_learning_objectives(content)
        if not has_objectives:
            issues.append(
                ValidationIssue(
                    issue_id=f"edu_{len(issues)}",
                    category=ValidationCategory.EDUCATIONAL_VALUE,
                    severity=SeverityLevel.MEDIUM,
                    description="No clear learning objectives stated",
                    suggestion="Add explicit learning objectives at the beginning",
                )
            )
            score -= 15

        # Check for educational keywords
        edu_density = self._calculate_educational_density(content)
        if edu_density < 0.05:  # Less than 5% educational keywords
            issues.append(
                ValidationIssue(
                    issue_id=f"edu_{len(issues)}",
                    category=ValidationCategory.EDUCATIONAL_VALUE,
                    severity=SeverityLevel.MEDIUM,
                    description="Low educational content density",
                    suggestion="Increase educational content and reduce filler",
                )
            )
            score -= 10

        # Check for assessment/practice
        if content_type in ["lesson", "tutorial"] and not await self._has_assessment(content):
            issues.append(
                ValidationIssue(
                    issue_id=f"edu_{len(issues)}",
                    category=ValidationCategory.EDUCATIONAL_VALUE,
                    severity=SeverityLevel.LOW,
                    description="No assessment or practice activities",
                    suggestion="Add questions or activities to reinforce learning",
                )
            )
            score -= 5

        return max(0, score), issues

    async def _validate_accessibility(self, content: str) -> tuple[float, list[ValidationIssue]]:
        """Validate accessibility of content."""
        issues = []
        score = 100.0

        # Check for alt text (if content has images)
        if "[image]" in content.lower() or "<img" in content.lower():
            if not re.search(r'alt=["\'](.*?)["\']', content):
                issues.append(
                    ValidationIssue(
                        issue_id=f"access_{len(issues)}",
                        category=ValidationCategory.ACCESSIBILITY,
                        severity=SeverityLevel.HIGH,
                        description="Images missing alt text",
                        suggestion="Add descriptive alt text to all images",
                    )
                )
                score -= 15

        # Check for heading structure
        if not self._has_proper_heading_structure(content):
            issues.append(
                ValidationIssue(
                    issue_id=f"access_{len(issues)}",
                    category=ValidationCategory.ACCESSIBILITY,
                    severity=SeverityLevel.MEDIUM,
                    description="Improper heading structure",
                    suggestion="Use hierarchical heading structure (H1, H2, H3...)",
                )
            )
            score -= 10

        # Check color contrast mentions
        if "color" in content.lower() and not await self._check_color_contrast_mentions(content):
            issues.append(
                ValidationIssue(
                    issue_id=f"access_{len(issues)}",
                    category=ValidationCategory.ACCESSIBILITY,
                    severity=SeverityLevel.LOW,
                    description="Color may be only way to convey information",
                    suggestion="Ensure color is not the only method to convey information",
                )
            )
            score -= 5

        return max(0, score), issues

    async def _validate_cultural_sensitivity(
        self, content: str
    ) -> tuple[float, list[ValidationIssue]]:
        """Validate cultural sensitivity of content."""
        issues = []
        score = 100.0

        # Check for cultural bias
        biases = await self._check_cultural_bias(content)
        for bias in biases:
            issues.append(
                ValidationIssue(
                    issue_id=f"culture_{len(issues)}",
                    category=ValidationCategory.CULTURAL_SENSITIVITY,
                    severity=SeverityLevel.HIGH,
                    description=bias["description"],
                    location=bias.get("location"),
                    suggestion=bias.get("suggestion", "Consider more inclusive language"),
                )
            )
            score -= 15

        # Check for diverse representation
        if not await self._has_diverse_representation(content):
            issues.append(
                ValidationIssue(
                    issue_id=f"culture_{len(issues)}",
                    category=ValidationCategory.CULTURAL_SENSITIVITY,
                    severity=SeverityLevel.LOW,
                    description="Limited diverse representation",
                    suggestion="Include diverse examples and perspectives",
                )
            )
            score -= 5

        return max(0, score), issues

    async def _validate_technical_quality(
        self, content: str
    ) -> tuple[float, list[ValidationIssue]]:
        """Validate technical quality of content."""
        issues = []
        score = 100.0

        # Check for spelling errors
        spelling_errors = await self._check_spelling(content)
        if spelling_errors:
            issues.append(
                ValidationIssue(
                    issue_id=f"tech_{len(issues)}",
                    category=ValidationCategory.TECHNICAL_QUALITY,
                    severity=SeverityLevel.MEDIUM,
                    description=f"Found {len(spelling_errors)} spelling errors",
                    suggestion="Correct spelling errors",
                    auto_fixable=True,
                )
            )
            score -= min(20, len(spelling_errors) * 2)

        # Check for grammar errors
        grammar_errors = await self._check_grammar(content)
        if grammar_errors:
            issues.append(
                ValidationIssue(
                    issue_id=f"tech_{len(issues)}",
                    category=ValidationCategory.TECHNICAL_QUALITY,
                    severity=SeverityLevel.MEDIUM,
                    description=f"Found {len(grammar_errors)} grammar issues",
                    suggestion="Fix grammar issues",
                    auto_fixable=True,
                )
            )
            score -= min(15, len(grammar_errors) * 1.5)

        # Check formatting consistency
        if not self._check_formatting_consistency(content):
            issues.append(
                ValidationIssue(
                    issue_id=f"tech_{len(issues)}",
                    category=ValidationCategory.TECHNICAL_QUALITY,
                    severity=SeverityLevel.LOW,
                    description="Inconsistent formatting",
                    suggestion="Ensure consistent formatting throughout",
                )
            )
            score -= 5

        return max(0, score), issues

    async def _validate_engagement_potential(
        self, content: str, grade_level: str
    ) -> tuple[float, list[ValidationIssue]]:
        """Validate engagement potential of content."""
        issues = []
        score = 100.0

        # Check for interactive elements
        if not await self._has_interactive_elements(content):
            issues.append(
                ValidationIssue(
                    issue_id=f"engage_{len(issues)}",
                    category=ValidationCategory.ENGAGEMENT_POTENTIAL,
                    severity=SeverityLevel.LOW,
                    description="No interactive elements",
                    suggestion="Add interactive elements like questions or activities",
                )
            )
            score -= 10

        # Check for multimedia references
        if not self._has_multimedia_references(content):
            issues.append(
                ValidationIssue(
                    issue_id=f"engage_{len(issues)}",
                    category=ValidationCategory.ENGAGEMENT_POTENTIAL,
                    severity=SeverityLevel.LOW,
                    description="No multimedia content",
                    suggestion="Consider adding images, videos, or audio",
                )
            )
            score -= 5

        # Check for real-world connections
        if not await self._has_real_world_connections(content):
            issues.append(
                ValidationIssue(
                    issue_id=f"engage_{len(issues)}",
                    category=ValidationCategory.ENGAGEMENT_POTENTIAL,
                    severity=SeverityLevel.LOW,
                    description="Limited real-world connections",
                    suggestion="Add examples that connect to students' lives",
                )
            )
            score -= 5

        return max(0, score), issues

    async def _validate_curriculum_alignment(
        self, content: str, grade_level: str, subject: str
    ) -> tuple[float, list[ValidationIssue]]:
        """Validate curriculum alignment of content."""
        issues = []
        score = 100.0

        # Check standard alignment
        standards_mentioned = self._extract_standards_references(content)
        if not standards_mentioned:
            issues.append(
                ValidationIssue(
                    issue_id=f"curr_{len(issues)}",
                    category=ValidationCategory.CURRICULUM_ALIGNMENT,
                    severity=SeverityLevel.MEDIUM,
                    description="No curriculum standards referenced",
                    suggestion="Add relevant curriculum standard references",
                )
            )
            score -= 15

        # Check grade-appropriate skills
        skills = await self._extract_skills_taught(content)
        inappropriate_skills = self._check_skill_grade_alignment(skills, grade_level)
        for skill in inappropriate_skills:
            issues.append(
                ValidationIssue(
                    issue_id=f"curr_{len(issues)}",
                    category=ValidationCategory.CURRICULUM_ALIGNMENT,
                    severity=SeverityLevel.MEDIUM,
                    description=f"Skill '{skill}' may not align with grade {grade_level}",
                    suggestion=f"Verify skill alignment with {grade_level} standards",
                )
            )
            score -= 5

        return max(0, score), issues

    # Helper methods

    def _initialize_validation_rules(self) -> list[ValidationRule]:
        """Initialize validation rules."""
        return [
            ValidationRule(
                rule_id="no_violence",
                category=ValidationCategory.SAFETY_COMPLIANCE,
                name="No Violence",
                description="Content must not contain violence",
                check_function="_check_violence_content",
                severity=SeverityLevel.CRITICAL,
                applicable_grades=["all"],
                applicable_subjects=["all"],
            ),
            ValidationRule(
                rule_id="age_appropriate_language",
                category=ValidationCategory.AGE_APPROPRIATENESS,
                name="Age Appropriate Language",
                description="Language must be appropriate for age group",
                check_function="_check_age_inappropriate_content",
                severity=SeverityLevel.HIGH,
                applicable_grades=["all"],
                applicable_subjects=["all"],
            ),
            # Add more rules as needed
        ]

    def _load_inappropriate_words(self) -> set[str]:
        """Load list of inappropriate words."""
        # This would typically load from a file or database
        return {
            "violence",
            "drug",
            "alcohol",
            "weapon",
            # Add more as needed (keeping it minimal for example)
        }

    def _load_educational_keywords(self) -> set[str]:
        """Load educational keywords."""
        return {
            "learn",
            "understand",
            "explore",
            "discover",
            "practice",
            "analyze",
            "create",
            "evaluate",
            "apply",
            "remember",
            "solve",
            "investigate",
            "experiment",
            "observe",
            "conclude",
        }

    def _initialize_safety_guidelines(self) -> dict[str, Any]:
        """Initialize safety guidelines."""
        return {
            "prohibited_topics": ["violence", "drugs", "inappropriate content"],
            "age_restrictions": {
                "K-2": ["complex math", "abstract concepts"],
                "3-5": ["advanced algebra", "sensitive topics"],
                "6-8": ["explicit content"],
                "9-12": ["age-inappropriate content"],
            },
        }

    def _result_to_dict(self, result: ValidationResult) -> dict[str, Any]:
        """Convert ValidationResult to dictionary."""
        return {
            "content_id": result.content_id,
            "validation_id": result.validation_id,
            "timestamp": result.timestamp.isoformat(),
            "status": result.status.value,
            "overall_score": result.overall_score,
            "category_scores": {k.value: v for k, v in result.category_scores.items()},
            "issues": [
                {
                    "id": issue.issue_id,
                    "category": issue.category.value,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "location": issue.location,
                    "suggestion": issue.suggestion,
                    "auto_fixable": issue.auto_fixable,
                }
                for issue in result.issues
            ],
            "issue_counts": {
                "critical": result.critical_issues,
                "high": result.high_issues,
                "medium": result.medium_issues,
                "low": result.low_issues,
            },
            "recommendations": result.recommendations,
            "required_changes": result.required_changes,
            "suggested_improvements": result.suggested_improvements,
            "content_rating": result.content_rating.value,
            "compliant_standards": result.compliant_standards,
            "non_compliant_standards": result.non_compliant_standards,
            "metadata": {
                "validator_version": result.validator_version,
                "validation_duration": result.validation_duration,
                "auto_fixes_applied": result.auto_fixes_applied,
                "manual_review_required": result.manual_review_required,
            },
        }

    def _count_issues_by_severity(self, issues: list[ValidationIssue]) -> dict[str, int]:
        """Count issues by severity level."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        for issue in issues:
            counts[issue.severity.value] += 1

        return counts

    def _determine_validation_status(
        self, score: float, critical_issues: int, high_issues: int
    ) -> ValidationStatus:
        """Determine overall validation status."""
        if critical_issues > 0:
            return ValidationStatus.REJECTED
        elif high_issues > 3 or score < 60:
            return ValidationStatus.NEEDS_REVISION
        elif high_issues > 0 or score < 80:
            return ValidationStatus.CONDITIONALLY_APPROVED
        elif score >= 80:
            return ValidationStatus.APPROVED
        else:
            return ValidationStatus.PENDING_REVIEW

    async def _calculate_readability(self, content: str) -> dict[str, float]:
        """Calculate readability scores."""
        # Simple readability calculation (would use proper library in production)
        sentences = content.count(".") + content.count("!") + content.count("?")
        words = len(content.split())
        syllables = sum(self._count_syllables(word) for word in content.split())

        if sentences == 0 or words == 0:
            return {"grade_level": 0, "reading_ease": 100}

        # Flesch-Kincaid Grade Level
        grade_level = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59

        # Flesch Reading Ease
        reading_ease = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)

        return {
            "grade_level": max(0, min(18, grade_level)),
            "reading_ease": max(0, min(100, reading_ease)),
        }

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)."""
        vowels = "aeiouAEIOU"
        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Ensure at least one syllable
        return max(1, syllable_count)

    def _find_inappropriate_words(self, content: str) -> list[dict[str, Any]]:
        """Find inappropriate words in content."""
        found = []
        content_lower = content.lower()

        for word in self.inappropriate_words:
            if word in content_lower:
                # Find position
                pos = content_lower.find(word)
                found.append(
                    {
                        "word": word,
                        "position": pos,
                        "context": content[max(0, pos - 20) : min(len(content), pos + 20)],
                    }
                )

        return found

    def _calculate_educational_density(self, content: str) -> float:
        """Calculate density of educational keywords."""
        words = content.lower().split()
        if not words:
            return 0

        educational_count = sum(
            1 for word in words if any(edu_word in word for edu_word in self.educational_keywords)
        )

        return educational_count / len(words)

    async def _process_task(self, state: "AgentState") -> Any:
        """
        Process the task for this educational agent.

        This implements the abstract method from BaseAgent.

        Args:
            state: Current agent state containing the task

        Returns:
            Task result
        """

        # Extract the task
        task = state.get("task", "")
        context = state.get("context", {})

        # For now, return a simple response
        # This will be replaced with actual LLM integration
        return {
            "agent": self.__class__.__name__,
            "task": task,
            "status": "completed",
            "result": f"{self.__class__.__name__} processed task: {task[:100] if task else 'No task'}...",
            "context": context,
        }
