"""Context Extraction Module for Educational Content Understanding

Provides deep context extraction capabilities for educational conversations,
maintaining state across multiple interactions and building comprehensive
educational context for content generation.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class LearningObjectiveLevel(Enum):
    """Bloom's Taxonomy levels for learning objectives."""
    
    REMEMBER = "remember"  # Recall facts and basic concepts
    UNDERSTAND = "understand"  # Explain ideas or concepts
    APPLY = "apply"  # Use information in new situations
    ANALYZE = "analyze"  # Draw connections among ideas
    EVALUATE = "evaluate"  # Justify a stand or decision
    CREATE = "create"  # Produce new or original work


class CurriculumStandard(Enum):
    """Common curriculum standards."""
    
    COMMON_CORE = "common_core"
    NGSS = "ngss"  # Next Generation Science Standards
    STATE_STANDARDS = "state_standards"
    IB = "ib"  # International Baccalaureate
    AP = "ap"  # Advanced Placement
    CUSTOM = "custom"


class EngagementStrategy(Enum):
    """Student engagement strategies."""
    
    GAMIFICATION = "gamification"
    COLLABORATIVE = "collaborative"
    PROJECT_BASED = "project_based"
    INQUIRY_BASED = "inquiry_based"
    PROBLEM_BASED = "problem_based"
    EXPERIENTIAL = "experiential"
    FLIPPED_CLASSROOM = "flipped_classroom"
    DIFFERENTIATED = "differentiated"


@dataclass
class EducationalContext:
    """Comprehensive educational context for content generation."""
    
    # Core educational parameters
    grade_level: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None
    subtopics: List[str] = field(default_factory=list)
    
    # Learning objectives
    learning_objectives: List[str] = field(default_factory=list)
    objective_levels: List[LearningObjectiveLevel] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    
    # Curriculum alignment
    curriculum_standards: List[CurriculumStandard] = field(default_factory=list)
    standard_codes: List[str] = field(default_factory=list)  # e.g., "CCSS.MATH.CONTENT.4.NF.B.3"
    
    # Classroom context
    class_size: Optional[int] = None
    student_age_range: Tuple[int, int] = (0, 0)
    special_needs: List[str] = field(default_factory=list)
    language_learners: bool = False
    technology_access: str = "standard"  # limited, standard, advanced
    
    # Content preferences
    content_type: Optional[str] = None  # lesson, quiz, game, simulation
    activity_duration: Optional[int] = None  # in minutes
    difficulty_level: str = "medium"  # easy, medium, hard
    engagement_strategies: List[EngagementStrategy] = field(default_factory=list)
    
    # Assessment parameters
    assessment_type: Optional[str] = None  # formative, summative
    assessment_format: Optional[str] = None  # multiple_choice, open_ended, performance
    rubric_criteria: List[str] = field(default_factory=list)
    
    # Game/Environment specifics
    game_style: Optional[str] = None
    environment_theme: Optional[str] = None
    mechanics: List[str] = field(default_factory=list)
    narrative_elements: List[str] = field(default_factory=list)
    
    # Accessibility requirements
    accessibility_features: List[str] = field(default_factory=list)
    language_support: List[str] = field(default_factory=list)
    visual_aids_required: bool = False
    audio_support: bool = False
    
    # Metadata
    context_id: str = field(default_factory=lambda: f"ctx_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    confidence_score: float = 0.0
    completeness_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary format."""
        data = asdict(self)
        # Convert enums to strings
        data['objective_levels'] = [level.value for level in self.objective_levels]
        data['curriculum_standards'] = [std.value for std in self.curriculum_standards]
        data['engagement_strategies'] = [strat.value for strat in self.engagement_strategies]
        # Convert datetime to ISO format
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    def calculate_completeness(self) -> float:
        """Calculate how complete the educational context is."""
        required_fields = [
            self.grade_level,
            self.subject,
            self.topic,
            len(self.learning_objectives) > 0,
            self.content_type
        ]
        
        optional_fields = [
            self.class_size,
            len(self.curriculum_standards) > 0,
            self.activity_duration,
            len(self.engagement_strategies) > 0,
            self.assessment_type
        ]
        
        required_score = sum(1 for field in required_fields if field) / len(required_fields)
        optional_score = sum(1 for field in optional_fields if field) / len(optional_fields)
        
        # Weight required fields more heavily
        self.completeness_score = (required_score * 0.7) + (optional_score * 0.3)
        return self.completeness_score
    
    def get_missing_critical_fields(self) -> List[str]:
        """Get list of missing critical fields."""
        missing = []
        
        if not self.grade_level:
            missing.append("grade_level")
        if not self.subject:
            missing.append("subject")
        if not self.topic:
            missing.append("topic")
        if not self.content_type:
            missing.append("content_type")
        if not self.learning_objectives:
            missing.append("learning_objectives")
            
        return missing


class ContextExtractor:
    """Advanced context extraction for educational conversations."""
    
    def __init__(self):
        """Initialize the context extractor."""
        self.contexts: Dict[str, EducationalContext] = {}  # Store contexts by conversation ID
        self.extraction_patterns = self._init_extraction_patterns()
        self.curriculum_mapping = self._init_curriculum_mapping()
        self.grade_level_mapping = self._init_grade_level_mapping()
        
        logger.info("Context Extractor initialized")
    
    def _init_extraction_patterns(self) -> Dict[str, List[Tuple[str, Any]]]:
        """Initialize pattern matching for context extraction."""
        return {
            "learning_objectives": [
                (r"students? (?:will|should) (?:be able to )?(\w+)", lambda m: m.group(1)),
                (r"learn(?:ing)? (?:to|about|how) ([^.?!]+)", lambda m: m.group(1)),
                (r"objective:?\s*([^.?!]+)", lambda m: m.group(1)),
                (r"goal:?\s*([^.?!]+)", lambda m: m.group(1)),
            ],
            
            "success_criteria": [
                (r"success (?:criteria|criterion):?\s*([^.?!]+)", lambda m: m.group(1)),
                (r"students? (?:must|need to) ([^.?!]+)", lambda m: m.group(1)),
                (r"demonstrate (?:that|their) ([^.?!]+)", lambda m: m.group(1)),
            ],
            
            "special_needs": [
                (r"(special needs?|iep|504|accommodation)", lambda m: "special_needs"),
                (r"(dyslexia|adhd|autism|visual impairment)", lambda m: m.group(1)),
                (r"(learning disabilit(?:y|ies))", lambda m: "learning_disability"),
            ],
            
            "engagement_strategies": [
                (r"(gamifi(?:ed|cation))", lambda m: EngagementStrategy.GAMIFICATION),
                (r"(collaborat(?:ive|ion))", lambda m: EngagementStrategy.COLLABORATIVE),
                (r"(project[- ]based)", lambda m: EngagementStrategy.PROJECT_BASED),
                (r"(inquiry[- ]based)", lambda m: EngagementStrategy.INQUIRY_BASED),
                (r"(hands[- ]on|experiential)", lambda m: EngagementStrategy.EXPERIENTIAL),
            ],
            
            "accessibility": [
                (r"(screen reader|text[- ]to[- ]speech)", lambda m: "screen_reader"),
                (r"(closed caption|subtitle)", lambda m: "closed_captions"),
                (r"(high contrast|color blind)", lambda m: "visual_accessibility"),
                (r"(simple language|easy read)", lambda m: "simplified_language"),
            ],
        }
    
    def _init_curriculum_mapping(self) -> Dict[str, Dict[str, Any]]:
        """Initialize curriculum standard mappings."""
        return {
            "math": {
                "common_core": {
                    "K": ["CC.K.OA", "CC.K.NBT", "CC.K.MD", "CC.K.G"],
                    "1": ["CC.1.OA", "CC.1.NBT", "CC.1.MD", "CC.1.G"],
                    "2": ["CC.2.OA", "CC.2.NBT", "CC.2.MD", "CC.2.G"],
                    "3": ["CC.3.OA", "CC.3.NBT", "CC.3.NF", "CC.3.MD", "CC.3.G"],
                    "4": ["CC.4.OA", "CC.4.NBT", "CC.4.NF", "CC.4.MD", "CC.4.G"],
                    "5": ["CC.5.OA", "CC.5.NBT", "CC.5.NF", "CC.5.MD", "CC.5.G"],
                },
                "topics": {
                    "fractions": ["NF", "fractions", "parts", "whole"],
                    "geometry": ["G", "shapes", "angles", "area", "perimeter"],
                    "algebra": ["OA", "equations", "variables", "expressions"],
                    "measurement": ["MD", "length", "weight", "volume", "time"],
                }
            },
            "science": {
                "ngss": {
                    "K-2": ["K-PS", "K-LS", "K-ESS", "K-ETS"],
                    "3-5": ["3-PS", "3-LS", "3-ESS", "4-PS", "4-LS", "4-ESS", "5-PS", "5-LS", "5-ESS"],
                    "MS": ["MS-PS", "MS-LS", "MS-ESS", "MS-ETS"],
                    "HS": ["HS-PS", "HS-LS", "HS-ESS", "HS-ETS"],
                },
                "topics": {
                    "physics": ["PS", "force", "motion", "energy", "matter"],
                    "life_science": ["LS", "biology", "ecosystem", "organism", "cell"],
                    "earth_science": ["ESS", "earth", "solar system", "weather", "climate"],
                    "engineering": ["ETS", "design", "problem solving", "technology"],
                }
            }
        }
    
    def _init_grade_level_mapping(self) -> Dict[str, Tuple[int, int]]:
        """Initialize grade level to age mapping."""
        return {
            "kindergarten": (5, 6),
            "1st grade": (6, 7),
            "2nd grade": (7, 8),
            "3rd grade": (8, 9),
            "4th grade": (9, 10),
            "5th grade": (10, 11),
            "6th grade": (11, 12),
            "7th grade": (12, 13),
            "8th grade": (13, 14),
            "9th grade": (14, 15),
            "10th grade": (15, 16),
            "11th grade": (16, 17),
            "12th grade": (17, 18),
            "elementary": (6, 11),
            "middle school": (11, 14),
            "high school": (14, 18),
        }
    
    async def extract_context(
        self,
        text: str,
        existing_context: Optional[EducationalContext] = None,
        conversation_id: Optional[str] = None
    ) -> EducationalContext:
        """
        Extract educational context from text.
        
        Args:
            text: Input text to process
            existing_context: Previous context to update
            conversation_id: ID for context storage
            
        Returns:
            Updated educational context
        """
        # Use existing context or create new
        if existing_context:
            context = existing_context
        elif conversation_id and conversation_id in self.contexts:
            context = self.contexts[conversation_id]
        else:
            context = EducationalContext()
        
        # Extract various context elements
        await self._extract_learning_objectives(text, context)
        await self._extract_curriculum_alignment(text, context)
        await self._extract_engagement_strategies(text, context)
        await self._extract_accessibility_requirements(text, context)
        await self._extract_assessment_criteria(text, context)
        
        # Infer additional context
        self._infer_bloom_levels(context)
        self._infer_age_range(context)
        
        # Update metadata
        context.updated_at = datetime.now()
        context.calculate_completeness()
        
        # Store context if conversation ID provided
        if conversation_id:
            self.contexts[conversation_id] = context
        
        logger.info(f"Context extracted with completeness: {context.completeness_score:.2f}")
        return context
    
    async def _extract_learning_objectives(self, text: str, context: EducationalContext):
        """Extract learning objectives from text."""
        patterns = self.extraction_patterns["learning_objectives"]
        
        for pattern, extractor in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                objective = extractor(match)
                if objective and objective not in context.learning_objectives:
                    context.learning_objectives.append(objective)
    
    async def _extract_curriculum_alignment(self, text: str, context: EducationalContext):
        """Extract curriculum standards and alignment."""
        # Check for explicit standard mentions
        if "common core" in text.lower():
            if CurriculumStandard.COMMON_CORE not in context.curriculum_standards:
                context.curriculum_standards.append(CurriculumStandard.COMMON_CORE)
        
        if "ngss" in text.lower() or "next generation science" in text.lower():
            if CurriculumStandard.NGSS not in context.curriculum_standards:
                context.curriculum_standards.append(CurriculumStandard.NGSS)
        
        # Extract standard codes (e.g., "CCSS.MATH.4.NF.B.3")
        code_pattern = r"[A-Z]{2,}[\.\-][A-Z0-9\.\-]+"
        codes = re.findall(code_pattern, text)
        for code in codes:
            if code not in context.standard_codes:
                context.standard_codes.append(code)
    
    async def _extract_engagement_strategies(self, text: str, context: EducationalContext):
        """Extract engagement strategies from text."""
        patterns = self.extraction_patterns["engagement_strategies"]
        
        for pattern, strategy_type in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                if strategy_type not in context.engagement_strategies:
                    context.engagement_strategies.append(strategy_type)
    
    async def _extract_accessibility_requirements(self, text: str, context: EducationalContext):
        """Extract accessibility requirements."""
        patterns = self.extraction_patterns["accessibility"]
        
        for pattern, feature in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                if feature not in context.accessibility_features:
                    context.accessibility_features.append(feature)
        
        # Check for special needs
        special_patterns = self.extraction_patterns["special_needs"]
        for pattern, need_type in special_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                if need_type not in context.special_needs:
                    context.special_needs.append(need_type)
                    # Enable relevant accessibility features
                    if "visual" in need_type.lower():
                        context.audio_support = True
                    if "hearing" in need_type.lower():
                        context.visual_aids_required = True
    
    async def _extract_assessment_criteria(self, text: str, context: EducationalContext):
        """Extract assessment-related information."""
        # Assessment type
        if any(word in text.lower() for word in ["formative", "check understanding", "practice"]):
            context.assessment_type = "formative"
        elif any(word in text.lower() for word in ["summative", "final", "exam", "test"]):
            context.assessment_type = "summative"
        
        # Assessment format
        if "multiple choice" in text.lower() or "mcq" in text.lower():
            context.assessment_format = "multiple_choice"
        elif "open ended" in text.lower() or "essay" in text.lower():
            context.assessment_format = "open_ended"
        elif "performance" in text.lower() or "demonstration" in text.lower():
            context.assessment_format = "performance"
        
        # Extract rubric criteria
        criteria_patterns = self.extraction_patterns["success_criteria"]
        for pattern, extractor in criteria_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                criterion = extractor(match)
                if criterion and criterion not in context.rubric_criteria:
                    context.rubric_criteria.append(criterion)
    
    def _infer_bloom_levels(self, context: EducationalContext):
        """Infer Bloom's taxonomy levels from learning objectives."""
        bloom_keywords = {
            LearningObjectiveLevel.REMEMBER: ["recall", "identify", "recognize", "name", "list"],
            LearningObjectiveLevel.UNDERSTAND: ["explain", "describe", "summarize", "interpret"],
            LearningObjectiveLevel.APPLY: ["apply", "use", "implement", "solve", "demonstrate"],
            LearningObjectiveLevel.ANALYZE: ["analyze", "compare", "contrast", "examine", "investigate"],
            LearningObjectiveLevel.EVALUATE: ["evaluate", "judge", "assess", "critique", "justify"],
            LearningObjectiveLevel.CREATE: ["create", "design", "develop", "construct", "produce"],
        }
        
        for objective in context.learning_objectives:
            objective_lower = objective.lower()
            for level, keywords in bloom_keywords.items():
                if any(keyword in objective_lower for keyword in keywords):
                    if level not in context.objective_levels:
                        context.objective_levels.append(level)
    
    def _infer_age_range(self, context: EducationalContext):
        """Infer student age range from grade level."""
        if context.grade_level:
            grade_lower = context.grade_level.lower()
            for grade, age_range in self.grade_level_mapping.items():
                if grade in grade_lower:
                    context.student_age_range = age_range
                    break
    
    def get_context_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of the educational context for a conversation."""
        if conversation_id not in self.contexts:
            return None
        
        context = self.contexts[conversation_id]
        return {
            "context_id": context.context_id,
            "completeness": context.completeness_score,
            "grade_level": context.grade_level,
            "subject": context.subject,
            "topic": context.topic,
            "content_type": context.content_type,
            "missing_fields": context.get_missing_critical_fields(),
            "learning_objectives_count": len(context.learning_objectives),
            "has_curriculum_alignment": len(context.curriculum_standards) > 0,
            "has_accessibility": len(context.accessibility_features) > 0,
            "updated_at": context.updated_at.isoformat()
        }
    
    def merge_contexts(
        self,
        context1: EducationalContext,
        context2: EducationalContext
    ) -> EducationalContext:
        """Merge two educational contexts, preserving all information."""
        merged = EducationalContext()
        
        # Merge single-value fields (prefer non-None values)
        for field in ['grade_level', 'subject', 'topic', 'content_type', 
                      'class_size', 'activity_duration', 'difficulty_level',
                      'assessment_type', 'assessment_format', 'game_style',
                      'environment_theme']:
            value1 = getattr(context1, field)
            value2 = getattr(context2, field)
            setattr(merged, field, value2 if value2 is not None else value1)
        
        # Merge list fields (combine unique values)
        for field in ['subtopics', 'learning_objectives', 'success_criteria',
                      'standard_codes', 'special_needs', 'mechanics',
                      'narrative_elements', 'accessibility_features',
                      'language_support', 'rubric_criteria']:
            list1 = getattr(context1, field)
            list2 = getattr(context2, field)
            combined = list(set(list1 + list2))
            setattr(merged, field, combined)
        
        # Merge enum list fields
        merged.objective_levels = list(set(context1.objective_levels + context2.objective_levels))
        merged.curriculum_standards = list(set(context1.curriculum_standards + context2.curriculum_standards))
        merged.engagement_strategies = list(set(context1.engagement_strategies + context2.engagement_strategies))
        
        # Merge boolean fields (OR operation)
        merged.language_learners = context1.language_learners or context2.language_learners
        merged.visual_aids_required = context1.visual_aids_required or context2.visual_aids_required
        merged.audio_support = context1.audio_support or context2.audio_support
        
        # Update metadata
        merged.created_at = min(context1.created_at, context2.created_at)
        merged.updated_at = datetime.now()
        merged.calculate_completeness()
        
        return merged