"""
Educational Content Validator

Validates Roblox scripts for educational appropriateness,
learning objective alignment, and curriculum standards compliance.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class GradeLevel(Enum):
    """Educational grade levels"""
    K = "kindergarten"
    ELEMENTARY = "elementary"  # Grades 1-5
    MIDDLE = "middle"         # Grades 6-8
    HIGH = "high"            # Grades 9-12
    COLLEGE = "college"      # Post-secondary


class Subject(Enum):
    """Educational subjects"""
    MATH = "mathematics"
    SCIENCE = "science"
    ENGLISH = "english"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    ART = "art"
    MUSIC = "music"
    PHYSICAL_EDUCATION = "physical_education"
    COMPUTER_SCIENCE = "computer_science"
    FOREIGN_LANGUAGE = "foreign_language"


class ContentRating(Enum):
    """Content appropriateness ratings"""
    APPROPRIATE = "appropriate"
    NEEDS_REVIEW = "needs_review"
    INAPPROPRIATE = "inappropriate"
    BLOCKED = "blocked"


@dataclass
class EducationalIssue:
    """Represents an educational content issue"""
    severity: str  # 'info', 'warning', 'error'
    line_number: int
    description: str
    category: str
    suggestion: Optional[str] = None
    affects_learning: bool = False


@dataclass
class LearningObjective:
    """Represents a learning objective"""
    id: str
    description: str
    grade_level: GradeLevel
    subject: Subject
    bloom_level: str  # remember, understand, apply, analyze, evaluate, create
    measurable: bool = True


@dataclass
class EducationalReport:
    """Complete educational validation report"""
    appropriate_for_grade: bool
    subject_aligned: bool
    learning_objectives_met: List[str]
    content_rating: ContentRating
    accessibility_score: float
    engagement_score: float
    educational_value_score: float
    issues: List[EducationalIssue]
    recommendations: List[str]
    curriculum_standards_met: List[str]


class EducationalContentValidator:
    """
    Validates Roblox Lua scripts for educational appropriateness and effectiveness
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Age-appropriate content patterns
        self.inappropriate_patterns = {
            'violence': [
                r'\b(kill|murder|blood|gore|death|die|weapon|gun|knife|sword|fight|attack|destroy)\b',
                r'\b(explode|explosion|bomb|missile|rocket|war|battle|combat)\b'
            ],
            'inappropriate_language': [
                r'\b(stupid|dumb|idiot|hate|shut up|loser)\b',
                r'\b(damn|hell|crap)\b'  # Mild profanity for younger audiences
            ],
            'adult_themes': [
                r'\b(alcohol|beer|wine|drunk|smoking|cigarette|drug)\b',
                r'\b(romantic|dating|kiss|love|marriage)\b'  # May be inappropriate for very young
            ],
            'scary_content': [
                r'\b(scary|horror|nightmare|monster|ghost|demon|devil|evil)\b',
                r'\b(dark|darkness|shadow|creepy|spooky)\b'
            ]
        }

        # Educational quality indicators
        self.educational_patterns = {
            'learning_activities': [
                r'\b(quiz|question|answer|learn|study|practice|exercise)\b',
                r'\b(problem|solve|solution|calculate|measure|experiment)\b',
                r'\b(discover|explore|investigate|research|analyze)\b'
            ],
            'feedback_mechanisms': [
                r'\b(feedback|score|progress|achievement|reward|badge)\b',
                r'\b(correct|incorrect|right|wrong|hint|help)\b'
            ],
            'collaboration': [
                r'\b(team|group|collaborate|share|discuss|communicate)\b',
                r'\b(together|partner|peer|friend|classmate)\b'
            ],
            'assessment': [
                r'\b(test|exam|assessment|grade|evaluate|check)\b',
                r'\b(rubric|criteria|standard|objective|goal)\b'
            ]
        }

        # Accessibility patterns
        self.accessibility_patterns = {
            'visual_accessibility': [
                r'Color3\.new\s*\([^)]*\)',  # Color usage
                r'TextSize\s*=',             # Text size settings
                r'Font\s*=',                 # Font selection
                r'BackgroundTransparency'    # Transparency for readability
            ],
            'audio_accessibility': [
                r'SoundService',
                r'Volume\s*=',
                r'\.Stopped\s*:',
                r'AudioDeviceInput'
            ],
            'motor_accessibility': [
                r'UserInputService',
                r'ContextActionService',
                r'GuiService',
                r'TouchEnabled'
            ]
        }

        # Engagement indicators
        self.engagement_patterns = {
            'interactivity': [
                r'MouseButton1Click',
                r'TouchTap',
                r'UserInputService',
                r'ContextActionService'
            ],
            'gamification': [
                r'\b(point|score|level|achievement|badge|reward|prize)\b',
                r'\b(leaderboard|ranking|competition|challenge)\b'
            ],
            'progression': [
                r'\b(unlock|progress|advance|next|continue|complete)\b',
                r'\b(beginner|intermediate|advanced|master)\b'
            ]
        }

        # Grade-appropriate complexity indicators
        self.complexity_patterns = {
            GradeLevel.K: {
                'simple_concepts': [r'\b(color|shape|number|letter|count)\b'],
                'basic_interactions': [r'MouseButton1Click', r'TouchTap']
            },
            GradeLevel.ELEMENTARY: {
                'math_concepts': [r'\b(add|subtract|multiply|divide|fraction|decimal)\b'],
                'reading_concepts': [r'\b(read|write|spell|vocabulary|grammar)\b']
            },
            GradeLevel.MIDDLE: {
                'advanced_math': [r'\b(algebra|geometry|equation|formula|graph)\b'],
                'science_concepts': [r'\b(experiment|hypothesis|variable|data|conclusion)\b']
            },
            GradeLevel.HIGH: {
                'complex_concepts': [r'\b(function|derivative|integral|theorem|proof)\b'],
                'critical_thinking': [r'\b(analyze|evaluate|synthesize|argue|debate)\b']
            }
        }

        # Curriculum standards (Common Core, NGSS, etc.)
        self.curriculum_standards = {
            'math_common_core': {
                'K': ['counting', 'number_recognition', 'basic_addition'],
                '1-2': ['place_value', 'addition_subtraction', 'measurement'],
                '3-5': ['multiplication', 'division', 'fractions', 'geometry'],
                '6-8': ['ratios', 'expressions', 'equations', 'statistics'],
                '9-12': ['algebra', 'geometry', 'trigonometry', 'calculus']
            },
            'science_ngss': {
                'K-2': ['weather', 'animals', 'plants', 'matter'],
                '3-5': ['ecosystems', 'earth_changes', 'energy', 'motion'],
                '6-8': ['cells', 'genetics', 'chemistry', 'physics'],
                '9-12': ['biology', 'chemistry', 'physics', 'earth_science']
            }
        }

    def validate_educational_content(self, lua_code: str, grade_level: GradeLevel,
                                   subject: Subject, learning_objectives: List[LearningObjective]) -> EducationalReport:
        """
        Validate educational content for appropriateness and effectiveness

        Args:
            lua_code: The Lua code to validate
            grade_level: Target grade level
            subject: Educational subject
            learning_objectives: List of learning objectives to check

        Returns:
            EducationalReport with validation results
        """
        issues = []

        # Check content appropriateness
        content_rating = self._check_content_appropriateness(lua_code, grade_level, issues)

        # Check grade level appropriateness
        appropriate_for_grade = self._check_grade_appropriateness(lua_code, grade_level, issues)

        # Check subject alignment
        subject_aligned = self._check_subject_alignment(lua_code, subject, issues)

        # Check learning objectives
        objectives_met = self._check_learning_objectives(lua_code, learning_objectives, issues)

        # Calculate accessibility score
        accessibility_score = self._calculate_accessibility_score(lua_code, issues)

        # Calculate engagement score
        engagement_score = self._calculate_engagement_score(lua_code, issues)

        # Calculate educational value score
        educational_value_score = self._calculate_educational_value(lua_code, issues)

        # Check curriculum standards
        standards_met = self._check_curriculum_standards(lua_code, grade_level, subject)

        # Generate recommendations
        recommendations = self._generate_educational_recommendations(issues, grade_level, subject)

        return EducationalReport(
            appropriate_for_grade=appropriate_for_grade,
            subject_aligned=subject_aligned,
            learning_objectives_met=objectives_met,
            content_rating=content_rating,
            accessibility_score=accessibility_score,
            engagement_score=engagement_score,
            educational_value_score=educational_value_score,
            issues=issues,
            recommendations=recommendations,
            curriculum_standards_met=standards_met
        )

    def _check_content_appropriateness(self, lua_code: str, grade_level: GradeLevel,
                                     issues: List[EducationalIssue]) -> ContentRating:
        """Check if content is appropriate for the target audience"""
        lines = lua_code.split('\n')
        inappropriate_count = 0
        total_checks = 0

        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower()

            for category, patterns in self.inappropriate_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, line_lower, re.IGNORECASE)
                    for match in matches:
                        total_checks += 1

                        # Age-specific severity
                        if grade_level in [GradeLevel.K, GradeLevel.ELEMENTARY]:
                            severity = 'error' if category in ['violence', 'inappropriate_language'] else 'warning'
                        elif grade_level == GradeLevel.MIDDLE:
                            severity = 'warning' if category in ['violence', 'adult_themes'] else 'info'
                        else:  # High school and above
                            severity = 'info' if category in ['scary_content'] else 'warning'

                        issues.append(EducationalIssue(
                            severity=severity,
                            line_number=line_num,
                            description=f"Potentially inappropriate content ({category}): {match.group()}",
                            category='content_appropriateness',
                            suggestion=f"Consider age-appropriate alternatives for {match.group()}",
                            affects_learning=severity == 'error'
                        ))

                        if severity == 'error':
                            inappropriate_count += 1

        # Determine content rating
        if inappropriate_count > 0:
            return ContentRating.INAPPROPRIATE
        elif any(issue.severity == 'warning' for issue in issues if issue.category == 'content_appropriateness'):
            return ContentRating.NEEDS_REVIEW
        else:
            return ContentRating.APPROPRIATE

    def _check_grade_appropriateness(self, lua_code: str, grade_level: GradeLevel,
                                   issues: List[EducationalIssue]) -> bool:
        """Check if content complexity matches grade level"""
        complexity_indicators = self.complexity_patterns.get(grade_level, {})
        found_indicators = 0
        expected_indicators = 0

        for category, patterns in complexity_indicators.items():
            expected_indicators += len(patterns)
            for pattern in patterns:
                if re.search(pattern, lua_code, re.IGNORECASE):
                    found_indicators += 1

        # Check for overly complex concepts for younger grades
        if grade_level in [GradeLevel.K, GradeLevel.ELEMENTARY]:
            advanced_patterns = [
                r'\b(algorithm|variable|function|loop|condition)\b',
                r'\b(derivative|integral|theorem|proof|hypothesis)\b'
            ]
            for pattern in advanced_patterns:
                matches = re.finditer(pattern, lua_code, re.IGNORECASE)
                for match in matches:
                    line_num = lua_code[:match.start()].count('\n') + 1
                    issues.append(EducationalIssue(
                        severity='warning',
                        line_number=line_num,
                        description=f"Concept may be too advanced for {grade_level.value}: {match.group()}",
                        category='grade_appropriateness',
                        suggestion="Consider simplifying or providing scaffolding"
                    ))

        # Check for overly simple concepts for older grades
        if grade_level in [GradeLevel.HIGH, GradeLevel.COLLEGE]:
            simple_patterns = [
                r'\b(count|color|shape|letter)\b'
            ]
            for pattern in simple_patterns:
                matches = re.finditer(pattern, lua_code, re.IGNORECASE)
                for match in matches:
                    line_num = lua_code[:match.start()].count('\n') + 1
                    issues.append(EducationalIssue(
                        severity='info',
                        line_number=line_num,
                        description=f"Concept may be too simple for {grade_level.value}: {match.group()}",
                        category='grade_appropriateness',
                        suggestion="Consider adding complexity or advanced applications"
                    ))

        return found_indicators >= expected_indicators * 0.3  # At least 30% match

    def _check_subject_alignment(self, lua_code: str, subject: Subject,
                               issues: List[EducationalIssue]) -> bool:
        """Check if content aligns with the specified subject"""
        subject_keywords = {
            Subject.MATH: [
                r'\b(math|number|calculate|equation|formula|geometry|algebra)\b',
                r'\b(add|subtract|multiply|divide|fraction|decimal|percent)\b'
            ],
            Subject.SCIENCE: [
                r'\b(science|experiment|hypothesis|data|conclusion|observe)\b',
                r'\b(physics|chemistry|biology|earth|space|energy|matter)\b'
            ],
            Subject.ENGLISH: [
                r'\b(read|write|grammar|vocabulary|literature|story|poem)\b',
                r'\b(sentence|paragraph|essay|character|plot|theme)\b'
            ],
            Subject.HISTORY: [
                r'\b(history|historical|past|ancient|civilization|culture)\b',
                r'\b(timeline|event|era|period|century|decade|war|peace)\b'
            ],
            Subject.COMPUTER_SCIENCE: [
                r'\b(code|program|algorithm|function|variable|loop|condition)\b',
                r'\b(computer|software|hardware|network|internet|data)\b'
            ]
        }

        keywords = subject_keywords.get(subject, [])
        if not keywords:
            return True  # Unknown subject, assume aligned

        alignment_score = 0
        total_keywords = len(keywords)

        for pattern in keywords:
            if re.search(pattern, lua_code, re.IGNORECASE):
                alignment_score += 1

        alignment_ratio = alignment_score / total_keywords if total_keywords > 0 else 0

        if alignment_ratio < 0.2:  # Less than 20% alignment
            issues.append(EducationalIssue(
                severity='warning',
                line_number=1,
                description=f"Content may not align well with {subject.value}",
                category='subject_alignment',
                suggestion=f"Consider adding more {subject.value}-specific content or activities"
            ))
            return False

        return True

    def _check_learning_objectives(self, lua_code: str, objectives: List[LearningObjective],
                                 issues: List[EducationalIssue]) -> List[str]:
        """Check which learning objectives are addressed in the code"""
        met_objectives = []

        for objective in objectives:
            # Create search patterns based on objective description
            objective_words = re.findall(r'\w+', objective.description.lower())

            # Look for evidence of objective implementation
            evidence_found = False
            for word in objective_words:
                if len(word) > 3:  # Skip short words
                    pattern = rf'\b{re.escape(word)}\b'
                    if re.search(pattern, lua_code, re.IGNORECASE):
                        evidence_found = True
                        break

            if evidence_found:
                met_objectives.append(objective.id)
            else:
                issues.append(EducationalIssue(
                    severity='info',
                    line_number=1,
                    description=f"Learning objective may not be addressed: {objective.description}",
                    category='learning_objectives',
                    suggestion=f"Add activities or content related to: {objective.description}",
                    affects_learning=True
                ))

        return met_objectives

    def _calculate_accessibility_score(self, lua_code: str, issues: List[EducationalIssue]) -> float:
        """Calculate accessibility score (0-100)"""
        accessibility_features = 0
        total_features = 0

        for category, patterns in self.accessibility_patterns.items():
            total_features += len(patterns)
            for pattern in patterns:
                if re.search(pattern, lua_code, re.IGNORECASE):
                    accessibility_features += 1

        # Check for specific accessibility considerations
        accessibility_checks = [
            (r'TextSize\s*=\s*[2-9]\d', 'Adequate text size'),
            (r'BackgroundTransparency\s*=\s*0\.[0-4]', 'Good contrast'),
            (r'UserInputService.*TouchEnabled', 'Touch support'),
            (r'ContextActionService', 'Keyboard alternatives'),
        ]

        for pattern, description in accessibility_checks:
            total_features += 1
            if re.search(pattern, lua_code, re.IGNORECASE):
                accessibility_features += 1
            else:
                issues.append(EducationalIssue(
                    severity='info',
                    line_number=1,
                    description=f"Accessibility feature missing: {description}",
                    category='accessibility',
                    suggestion=f"Consider implementing {description} for better accessibility"
                ))

        return (accessibility_features / total_features * 100) if total_features > 0 else 50

    def _calculate_engagement_score(self, lua_code: str, issues: List[EducationalIssue]) -> float:
        """Calculate engagement score (0-100)"""
        engagement_features = 0
        total_features = 0

        for category, patterns in self.engagement_patterns.items():
            total_features += len(patterns)
            for pattern in patterns:
                if re.search(pattern, lua_code, re.IGNORECASE):
                    engagement_features += 1

        # Check for specific engagement features
        engagement_checks = [
            (r'MouseButton1Click|TouchTap', 'Interactive elements'),
            (r'\b(score|point|achievement)\b', 'Progress tracking'),
            (r'\b(feedback|response|result)\b', 'Immediate feedback'),
            (r'\b(challenge|puzzle|game)\b', 'Challenging activities'),
        ]

        for pattern, description in engagement_checks:
            total_features += 1
            if re.search(pattern, lua_code, re.IGNORECASE):
                engagement_features += 1
            else:
                issues.append(EducationalIssue(
                    severity='info',
                    line_number=1,
                    description=f"Engagement feature missing: {description}",
                    category='engagement',
                    suggestion=f"Consider adding {description} to increase engagement"
                ))

        return (engagement_features / total_features * 100) if total_features > 0 else 30

    def _calculate_educational_value(self, lua_code: str, issues: List[EducationalIssue]) -> float:
        """Calculate educational value score (0-100)"""
        educational_features = 0
        total_features = 0

        for category, patterns in self.educational_patterns.items():
            total_features += len(patterns)
            for pattern in patterns:
                if re.search(pattern, lua_code, re.IGNORECASE):
                    educational_features += 1

        # Bonus for specific educational patterns
        educational_bonuses = [
            (r'\b(quiz|test|question)\b.*\b(answer|response)\b', 'Assessment integration'),
            (r'\b(hint|help|tutorial)\b', 'Learning support'),
            (r'\b(progress|track|monitor)\b', 'Progress tracking'),
            (r'\b(collaborate|team|group)\b', 'Collaborative learning'),
        ]

        for pattern, description in educational_bonuses:
            total_features += 1
            if re.search(pattern, lua_code, re.IGNORECASE | re.DOTALL):
                educational_features += 1

        return (educational_features / total_features * 100) if total_features > 0 else 40

    def _check_curriculum_standards(self, lua_code: str, grade_level: GradeLevel,
                                  subject: Subject) -> List[str]:
        """Check alignment with curriculum standards"""
        met_standards = []

        # This is a simplified implementation
        # In practice, this would use more sophisticated matching
        if subject == Subject.MATH:
            standards = self.curriculum_standards.get('math_common_core', {})
            grade_key = self._get_grade_key(grade_level)
            grade_standards = standards.get(grade_key, [])

            for standard in grade_standards:
                if re.search(rf'\b{standard}\b', lua_code, re.IGNORECASE):
                    met_standards.append(f"CCSS.MATH.{grade_key}.{standard}")

        elif subject == Subject.SCIENCE:
            standards = self.curriculum_standards.get('science_ngss', {})
            grade_key = self._get_grade_key(grade_level)
            grade_standards = standards.get(grade_key, [])

            for standard in grade_standards:
                if re.search(rf'\b{standard}\b', lua_code, re.IGNORECASE):
                    met_standards.append(f"NGSS.{grade_key}.{standard}")

        return met_standards

    def _get_grade_key(self, grade_level: GradeLevel) -> str:
        """Convert grade level to curriculum standard key"""
        mapping = {
            GradeLevel.K: 'K',
            GradeLevel.ELEMENTARY: '3-5',
            GradeLevel.MIDDLE: '6-8',
            GradeLevel.HIGH: '9-12',
            GradeLevel.COLLEGE: '9-12'  # Use high school standards as fallback
        }
        return mapping.get(grade_level, '6-8')

    def _generate_educational_recommendations(self, issues: List[EducationalIssue],
                                            grade_level: GradeLevel, subject: Subject) -> List[str]:
        """Generate educational improvement recommendations"""
        recommendations = []

        # Count issues by category
        issue_categories = {}
        for issue in issues:
            issue_categories[issue.category] = issue_categories.get(issue.category, 0) + 1

        # Generate specific recommendations based on issues
        if issue_categories.get('content_appropriateness', 0) > 0:
            recommendations.append(f"Review content for {grade_level.value} appropriateness")

        if issue_categories.get('accessibility', 0) > 2:
            recommendations.append("Improve accessibility features for diverse learners")

        if issue_categories.get('engagement', 0) > 2:
            recommendations.append("Add more interactive and engaging elements")

        if issue_categories.get('learning_objectives', 0) > 0:
            recommendations.append("Align content more closely with learning objectives")

        # Subject-specific recommendations
        if subject == Subject.MATH:
            recommendations.extend([
                "Include visual representations of mathematical concepts",
                "Provide multiple problem-solving approaches",
                "Add real-world application examples"
            ])
        elif subject == Subject.SCIENCE:
            recommendations.extend([
                "Include hands-on virtual experiments",
                "Add data collection and analysis activities",
                "Connect concepts to real-world phenomena"
            ])

        # Grade-specific recommendations
        if grade_level in [GradeLevel.K, GradeLevel.ELEMENTARY]:
            recommendations.extend([
                "Use simple, clear language",
                "Include visual and audio cues",
                "Provide frequent positive feedback"
            ])
        elif grade_level == GradeLevel.MIDDLE:
            recommendations.extend([
                "Include collaborative learning opportunities",
                "Add scaffolding for complex concepts",
                "Encourage exploration and discovery"
            ])
        elif grade_level in [GradeLevel.HIGH, GradeLevel.COLLEGE]:
            recommendations.extend([
                "Include higher-order thinking activities",
                "Provide opportunities for creativity",
                "Connect to career applications"
            ])

        return list(set(recommendations))  # Remove duplicates