"""Natural Language Understanding Agent for Educational Content Processing

This agent processes natural language inputs to extract educational intent,
entities, and context for Roblox content generation workflows.
"""

import asyncio
import re
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.agents.base_agent import BaseAgent, AgentConfig, AgentState, TaskResult
from .llm_integration import LLMIntegration, LLMConfig, LLMProvider

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Types of educational intents that can be extracted."""

    # Content Creation Intents
    CREATE_LESSON = "create_lesson"
    CREATE_QUIZ = "create_quiz"
    CREATE_GAME = "create_game"
    CREATE_SIMULATION = "create_simulation"
    CREATE_ENVIRONMENT = "create_environment"

    # Modification Intents
    MODIFY_CONTENT = "modify_content"
    ADD_FEATURE = "add_feature"
    REMOVE_FEATURE = "remove_feature"

    # Query Intents
    GET_HELP = "get_help"
    EXPLAIN_CONCEPT = "explain_concept"
    LIST_OPTIONS = "list_options"

    # Assessment Intents
    CREATE_ASSESSMENT = "create_assessment"
    REVIEW_PROGRESS = "review_progress"
    GENERATE_REPORT = "generate_report"

    # Collaboration Intents
    SHARE_CONTENT = "share_content"
    INVITE_COLLABORATOR = "invite_collaborator"
    REQUEST_FEEDBACK = "request_feedback"

    # Performance & Analytics Intents
    ANALYZE_PERFORMANCE = "analyze_performance"
    PROVIDE_FEEDBACK = "provide_feedback"

    # Control Intents
    DELEGATE_CONTROL = "delegate_control"
    START_SESSION = "start_session"
    END_SESSION = "end_session"
    CONFIRM_ACTION = "confirm_action"


class EntityType(Enum):
    """Types of entities that can be extracted from educational requests."""

    # Educational Entities
    GRADE_LEVEL = "grade_level"
    SUBJECT = "subject"
    TOPIC = "topic"
    LEARNING_OBJECTIVE = "learning_objective"
    CURRICULUM_STANDARD = "curriculum_standard"

    # Content Entities
    CONTENT_TYPE = "content_type"
    ACTIVITY_TYPE = "activity_type"
    ASSESSMENT_TYPE = "assessment_type"
    DIFFICULTY_LEVEL = "difficulty_level"

    # User Entities
    STUDENT_COUNT = "student_count"
    USER_ROLE = "user_role"
    CLASS_NAME = "class_name"

    # Game/Environment Entities
    GAME_STYLE = "game_style"
    ENVIRONMENT_THEME = "environment_theme"
    MECHANICS = "mechanics"
    ASSETS = "assets"

    # Temporal Entities
    DURATION = "duration"
    DEADLINE = "deadline"
    SCHEDULE = "schedule"

    # Descriptive Entities
    DESCRIPTION = "description"
    REQUIREMENTS = "requirements"
    CONSTRAINTS = "constraints"


@dataclass
class NLUConfig(AgentConfig):
    """Configuration for the NLU Agent."""

    intent_threshold: float = 0.7  # Confidence threshold for intent classification
    entity_threshold: float = 0.6  # Confidence threshold for entity extraction
    context_window: int = 5  # Number of previous messages to consider for context
    use_spell_correction: bool = True
    use_synonym_expansion: bool = True
    language_model: str = "educational"  # Specialized educational language model

    # Educational-specific settings
    grade_level_range: Tuple[int, int] = (1, 12)  # K-12
    supported_subjects: List[str] = field(default_factory=lambda: [
        "math", "science", "history", "english", "art", "music",
        "physical_education", "computer_science", "social_studies"
    ])

    # Pattern matching configurations
    enable_pattern_matching: bool = True
    custom_patterns: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExtractedIntent:
    """Represents an extracted intent from user input."""

    intent_type: IntentType
    confidence: float
    raw_text: str
    normalized_text: str
    keywords: List[str] = field(default_factory=list)
    modifiers: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExtractedEntity:
    """Represents an extracted entity from user input."""

    entity_type: EntityType
    value: Any
    confidence: float
    start_pos: int
    end_pos: int
    raw_text: str
    normalized_value: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NLUResult:
    """Complete NLU processing result."""

    intents: List[ExtractedIntent]
    entities: List[ExtractedEntity]
    sentiment: str  # positive, negative, neutral
    language: str
    educational_context: Dict[str, Any]
    suggestions: List[str]
    requires_clarification: bool
    clarification_questions: List[str]
    processing_time: float
    raw_input: str
    processed_input: str


class NLUAgent(BaseAgent):
    """
    Natural Language Understanding Agent for processing educational requests.

    This agent serves as the entry point for all natural language inputs,
    extracting intent, entities, and context to guide the content generation workflow.
    """

    def __init__(self, config: Optional[NLUConfig] = None):
        """Initialize the NLU Agent."""
        super().__init__(config or NLUConfig())
        self.config: NLUConfig = self.config

        # Pattern matchers for common educational patterns
        self._init_pattern_matchers()

        # Intent keywords mapping
        self._init_intent_keywords()

        # Initialize LLM integration for intelligent understanding
        llm_config = LLMConfig(
            provider=LLMProvider.MOCK,  # Will auto-detect if API keys are available
            temperature=0.7
        )
        self.llm_integration = LLMIntegration(llm_config)
        self.conversation_history = []
        self.accumulated_context = {}

        # Entity patterns
        self._init_entity_patterns()

        # Educational vocabulary
        self._init_educational_vocabulary()

        logger.info("NLU Agent initialized with educational focus")

    def _init_pattern_matchers(self):
        """Initialize regex patterns for common educational requests."""
        self.patterns = {
            # Grade level patterns
            "grade_level": [
                (r'(\d+)(?:st|nd|rd|th)\s*grade', lambda m: f"{m.group(1)}th grade"),
                (r'grade\s*(\d+)', lambda m: f"{m.group(1)}th grade"),
                (r'(kindergarten|k-\d+|pre-?k)', lambda m: m.group(1).lower()),
                (r'(elementary|middle|high)\s*school', lambda m: m.group(1).lower()),
            ],

            # Subject patterns
            "subject": [
                (r'(math|mathematics|algebra|geometry|calculus)', lambda m: "math"),
                (r'(science|biology|chemistry|physics|earth science)', lambda m: "science"),
                (r'(history|social studies|geography|civics)', lambda m: "history"),
                (r'(english|ela|language arts|reading|writing)', lambda m: "english"),
                (r'(computer science|coding|programming|cs)', lambda m: "computer_science"),
            ],

            # Learning activity patterns
            "activity": [
                (r'(quiz|test|assessment|exam)', lambda m: "assessment"),
                (r'(game|play|fun|interactive)', lambda m: "game"),
                (r'(simulation|model|demonstrate)', lambda m: "simulation"),
                (r'(lesson|tutorial|teach|explain)', lambda m: "lesson"),
                (r'(project|build|create|make)', lambda m: "project"),
            ],

            # Temporal patterns
            "duration": [
                (r'(\d+)\s*(minute|min|m)s?', lambda m: f"{m.group(1)}_minutes"),
                (r'(\d+)\s*(hour|hr|h)s?', lambda m: f"{m.group(1)}_hours"),
                (r'(\d+)\s*(day|d)s?', lambda m: f"{m.group(1)}_days"),
                (r'(\d+)\s*(week|w)s?', lambda m: f"{m.group(1)}_weeks"),
            ],

            # Student count patterns
            "student_count": [
                (r'(\d+)\s*student', lambda m: int(m.group(1))),
                (r'class\s*of\s*(\d+)', lambda m: int(m.group(1))),
                (r'about\s*(\d+)\s*kid', lambda m: int(m.group(1))),
                (r'(\d+)\s*learner', lambda m: int(m.group(1))),
            ],
        }

    def _init_intent_keywords(self):
        """Initialize keyword mappings for intent classification."""
        self.intent_keywords = {
            IntentType.CREATE_LESSON: [
                "create", "make", "build", "design", "lesson", "tutorial",
                "teach", "explain", "show", "demonstrate"
            ],
            IntentType.CREATE_QUIZ: [
                "quiz", "test", "assess", "evaluate", "question",
                "examination", "check", "measure"
            ],
            IntentType.CREATE_GAME: [
                "game", "play", "fun", "gamify", "interactive",
                "engage", "entertainment", "adventure"
            ],
            IntentType.CREATE_SIMULATION: [
                "simulate", "model", "demonstrate", "visualize",
                "represent", "replicate", "emulate"
            ],
            IntentType.CREATE_ENVIRONMENT: [
                "environment", "world", "space", "area", "scene",
                "setting", "place", "location"
            ],
            IntentType.MODIFY_CONTENT: [
                "change", "modify", "update", "edit", "adjust",
                "alter", "revise", "improve"
            ],
            IntentType.ADD_FEATURE: [
                "add", "include", "append", "insert", "incorporate",
                "integrate", "attach"
            ],
            IntentType.GET_HELP: [
                "help", "assist", "support", "guide", "how",
                "what", "explain", "understand"
            ],
            IntentType.CREATE_ASSESSMENT: [
                "assessment", "evaluate", "grade", "score", "rubric",
                "criteria", "measure", "benchmark"
            ],
            IntentType.DELEGATE_CONTROL: [
                "go ahead", "make it", "you decide", "create something",
                "surprise me", "your choice", "do it"
            ],
        }

    def _init_entity_patterns(self):
        """Initialize patterns for entity extraction."""
        self.entity_patterns = {
            EntityType.GRADE_LEVEL: self.patterns["grade_level"],
            EntityType.SUBJECT: self.patterns["subject"],
            EntityType.ACTIVITY_TYPE: self.patterns["activity"],
            EntityType.DURATION: self.patterns["duration"],
            EntityType.STUDENT_COUNT: self.patterns["student_count"],

            # Additional entity patterns
            EntityType.DIFFICULTY_LEVEL: [
                (r'(easy|simple|basic|beginner)', lambda m: "beginner"),
                (r'(medium|moderate|intermediate)', lambda m: "intermediate"),
                (r'(hard|difficult|challenging|advanced)', lambda m: "advanced"),
            ],

            EntityType.GAME_STYLE: [
                (r'(adventure|rpg|role-?playing)', lambda m: "adventure"),
                (r'(puzzle|brain|logic)', lambda m: "puzzle"),
                (r'(action|platformer|runner)', lambda m: "action"),
                (r'(simulation|tycoon|builder)', lambda m: "simulation"),
                (r'(educational|learning|teaching)', lambda m: "educational"),
            ],

            EntityType.ENVIRONMENT_THEME: [
                (r'(space|solar|planet|galaxy)', lambda m: "space"),
                (r'(ocean|underwater|marine|sea)', lambda m: "ocean"),
                (r'(forest|jungle|nature|woods)', lambda m: "forest"),
                (r'(city|urban|town|metropolis)', lambda m: "city"),
                (r'(historical|ancient|past|medieval)', lambda m: "historical"),
            ],
        }

    def _init_educational_vocabulary(self):
        """Initialize educational-specific vocabulary and concepts."""
        self.educational_vocab = {
            "learning_objectives": [
                "understand", "analyze", "apply", "create", "evaluate",
                "remember", "synthesize", "compare", "contrast", "identify"
            ],
            "curriculum_standards": [
                "common core", "ngss", "state standards", "national standards",
                "learning targets", "essential questions", "big ideas"
            ],
            "pedagogical_terms": [
                "differentiation", "scaffolding", "formative", "summative",
                "authentic assessment", "project-based", "inquiry-based",
                "collaborative", "hands-on", "experiential"
            ],
            "engagement_strategies": [
                "gamification", "interactive", "collaborative", "competitive",
                "rewards", "badges", "leaderboard", "achievements", "progress"
            ],
        }

    async def process(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> NLUResult:
        """
        Process natural language input to extract intent and entities.

        Args:
            input_text: The raw user input
            context: Optional context from previous messages

        Returns:
            NLUResult containing extracted information
        """
        start_time = asyncio.get_event_loop().time()

        # Preprocess input
        processed_text = self._preprocess_text(input_text)

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": input_text})

        # Update accumulated context
        if context:
            self.accumulated_context.update(context)

        # Try LLM-based understanding first for better context awareness
        llm_result = None
        try:
            llm_result = await self.llm_integration.understand_intent(
                input_text,
                self.conversation_history[-10:],  # Last 10 messages for context
                self.accumulated_context
            )

            # Update accumulated context with what was understood
            if llm_result.get("entities"):
                self.accumulated_context.update(llm_result["entities"])

        except Exception as e:
            logger.debug(f"LLM understanding failed, falling back to rules: {e}")

        # Extract intents (use LLM result if available, otherwise use rules)
        if llm_result and llm_result.get("intent") != "unknown":
            # Convert LLM intent string to IntentType
            intent_str = llm_result.get("intent", "unknown")
            try:
                intent_type = IntentType(intent_str)
                intents = [Intent(type=intent_type, confidence=llm_result.get("confidence", 0.5))]
            except ValueError:
                # Fall back to rule-based extraction
                intents = await self._extract_intents(processed_text, context)
        else:
            intents = await self._extract_intents(processed_text, context)

        # Extract entities
        entities = await self._extract_entities(processed_text, context)

        # Analyze sentiment
        sentiment = self._analyze_sentiment(processed_text)

        # Build educational context
        educational_context = self._build_educational_context(intents, entities, context)

        # Generate suggestions
        suggestions = self._generate_suggestions(intents, entities, educational_context)

        # Check if clarification is needed (use LLM result if available)
        if llm_result and llm_result.get("clarifications_needed"):
            requires_clarification = bool(llm_result["clarifications_needed"])
            questions = llm_result["clarifications_needed"]
        else:
            requires_clarification, questions = self._check_clarification_needed(
                intents, entities, educational_context
            )

        processing_time = asyncio.get_event_loop().time() - start_time

        result = NLUResult(
            intents=intents,
            entities=entities,
            sentiment=sentiment,
            language="en",  # TODO: Add language detection
            educational_context=educational_context,
            suggestions=suggestions,
            requires_clarification=requires_clarification,
            clarification_questions=questions,
            processing_time=processing_time,
            raw_input=input_text,
            processed_input=processed_text
        )

        logger.info(f"NLU processing completed in {processing_time:.3f}s")
        return result

    def _preprocess_text(self, text: str) -> str:
        """Preprocess input text for analysis."""
        # Convert to lowercase for pattern matching
        processed = text.lower().strip()

        # Expand contractions
        contractions = {
            "don't": "do not",
            "won't": "will not",
            "can't": "cannot",
            "n't": " not",
            "'re": " are",
            "'ve": " have",
            "'ll": " will",
            "'d": " would",
            "'m": " am",
        }
        for contraction, expansion in contractions.items():
            processed = processed.replace(contraction, expansion)

        # Remove extra whitespace
        processed = re.sub(r'\s+', ' ', processed)

        return processed

    async def _extract_intents(
        self, text: str, context: Optional[Dict[str, Any]]
    ) -> List[ExtractedIntent]:
        """Extract intents from processed text."""
        intents = []

        # Check for each intent type
        for intent_type, keywords in self.intent_keywords.items():
            score = 0
            matched_keywords = []

            for keyword in keywords:
                if keyword in text:
                    score += 1
                    matched_keywords.append(keyword)

            # Calculate confidence
            if matched_keywords:
                confidence = min(1.0, score / len(keywords) + 0.3)

                if confidence >= self.config.intent_threshold:
                    intent = ExtractedIntent(
                        intent_type=intent_type,
                        confidence=confidence,
                        raw_text=text,
                        normalized_text=text,
                        keywords=matched_keywords
                    )
                    intents.append(intent)

        # Sort by confidence
        intents.sort(key=lambda x: x.confidence, reverse=True)

        # If no clear intent, try to infer from context
        if not intents and context:
            intents = self._infer_intent_from_context(text, context)

        return intents

    async def _extract_entities(
        self, text: str, context: Optional[Dict[str, Any]]
    ) -> List[ExtractedEntity]:
        """Extract entities from processed text."""
        entities = []

        for entity_type, patterns in self.entity_patterns.items():
            for pattern, normalizer in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)

                for match in matches:
                    value = normalizer(match) if normalizer else match.group(0)

                    entity = ExtractedEntity(
                        entity_type=entity_type,
                        value=value,
                        confidence=0.8,  # Base confidence for pattern match
                        start_pos=match.start(),
                        end_pos=match.end(),
                        raw_text=match.group(0),
                        normalized_value=value
                    )
                    entities.append(entity)

        # Deduplicate overlapping entities
        entities = self._deduplicate_entities(entities)

        return entities

    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove duplicate or overlapping entities."""
        if not entities:
            return entities

        # Sort by position and confidence
        entities.sort(key=lambda e: (e.start_pos, -e.confidence))

        deduped = []
        last_end = -1

        for entity in entities:
            # Check for overlap
            if entity.start_pos >= last_end:
                deduped.append(entity)
                last_end = entity.end_pos

        return deduped

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze the sentiment of the input text."""
        positive_words = ["great", "good", "excellent", "wonderful", "love", "excited", "fun"]
        negative_words = ["bad", "difficult", "hard", "confused", "stuck", "problem", "issue"]

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _build_educational_context(
        self,
        intents: List[ExtractedIntent],
        entities: List[ExtractedEntity],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build comprehensive educational context from extracted information."""
        educational_context = {
            "primary_intent": intents[0].intent_type.value if intents else None,
            "all_intents": [i.intent_type.value for i in intents],
            "confidence": intents[0].confidence if intents else 0.0,
        }

        # Extract key educational parameters
        for entity in entities:
            if entity.entity_type == EntityType.GRADE_LEVEL:
                educational_context["grade_level"] = entity.normalized_value
            elif entity.entity_type == EntityType.SUBJECT:
                educational_context["subject"] = entity.normalized_value
            elif entity.entity_type == EntityType.TOPIC:
                educational_context["topic"] = entity.normalized_value
            elif entity.entity_type == EntityType.STUDENT_COUNT:
                educational_context["class_size"] = entity.normalized_value
            elif entity.entity_type == EntityType.DIFFICULTY_LEVEL:
                educational_context["difficulty"] = entity.normalized_value
            elif entity.entity_type == EntityType.GAME_STYLE:
                educational_context["game_style"] = entity.normalized_value
            elif entity.entity_type == EntityType.DURATION:
                educational_context["duration"] = entity.normalized_value

        # Merge with existing context
        if context:
            for key, value in context.items():
                if key not in educational_context:
                    educational_context[key] = value

        return educational_context

    def _generate_suggestions(
        self,
        intents: List[ExtractedIntent],
        entities: List[ExtractedEntity],
        educational_context: Dict[str, Any]
    ) -> List[str]:
        """Generate helpful suggestions based on extracted information."""
        suggestions = []

        # Check for missing critical information
        if not educational_context.get("grade_level"):
            suggestions.append("Consider specifying the grade level for better content alignment")

        if not educational_context.get("subject"):
            suggestions.append("Adding a subject area will help create more focused content")

        if not educational_context.get("topic"):
            suggestions.append("Specifying a topic will make the content more targeted")

        # Intent-specific suggestions
        if intents and intents[0].intent_type == IntentType.CREATE_QUIZ:
            if not educational_context.get("difficulty"):
                suggestions.append("Consider specifying difficulty level for the quiz")
            suggestions.append("You might want to specify the number of questions")

        elif intents and intents[0].intent_type == IntentType.CREATE_GAME:
            if not educational_context.get("game_style"):
                suggestions.append("Choosing a game style (puzzle, adventure, etc.) will enhance engagement")

        return suggestions

    def _check_clarification_needed(
        self,
        intents: List[ExtractedIntent],
        entities: List[ExtractedEntity],
        educational_context: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Check if clarification is needed and generate questions."""
        questions = []

        # No clear intent
        if not intents or intents[0].confidence < 0.5:
            questions.append("What would you like to create? (lesson, quiz, game, or simulation)")
            return True, questions

        # Missing critical information for content creation
        primary_intent = intents[0].intent_type

        if primary_intent in [
            IntentType.CREATE_LESSON,
            IntentType.CREATE_QUIZ,
            IntentType.CREATE_GAME,
            IntentType.CREATE_SIMULATION
        ]:
            if not educational_context.get("grade_level"):
                questions.append("What grade level is this for?")

            if not educational_context.get("subject"):
                questions.append("What subject area should this cover?")

            if not educational_context.get("topic"):
                questions.append("What specific topic would you like to focus on?")

        return len(questions) > 0, questions

    def _infer_intent_from_context(
        self, text: str, context: Dict[str, Any]
    ) -> List[ExtractedIntent]:
        """Infer intent from context when direct extraction fails."""
        intents = []

        # Check if this might be a continuation
        if context.get("last_intent"):
            # User might be providing additional information
            intent = ExtractedIntent(
                intent_type=IntentType(context["last_intent"]),
                confidence=0.6,
                raw_text=text,
                normalized_text=text,
                keywords=[],
                modifiers={"inferred": True}
            )
            intents.append(intent)

        # Check for confirmation patterns
        if any(word in text for word in ["yes", "ok", "sure", "go", "proceed"]):
            intent = ExtractedIntent(
                intent_type=IntentType.CONFIRM_ACTION,
                confidence=0.7,
                raw_text=text,
                normalized_text=text,
                keywords=["confirmation"]
            )
            intents.append(intent)

        return intents

    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """
        Execute an NLU task.

        Args:
            task: Task specification containing input text and context

        Returns:
            TaskResult with NLU processing results
        """
        try:
            input_text = task.get("input_text", "")
            context = task.get("context", {})

            # Process the input
            result = await self.process(input_text, context)

            # Convert to serializable format
            output = {
                "intents": [
                    {
                        "type": intent.intent_type.value,
                        "confidence": intent.confidence,
                        "keywords": intent.keywords
                    }
                    for intent in result.intents
                ],
                "entities": [
                    {
                        "type": entity.entity_type.value,
                        "value": entity.value,
                        "confidence": entity.confidence
                    }
                    for entity in result.entities
                ],
                "educational_context": result.educational_context,
                "sentiment": result.sentiment,
                "suggestions": result.suggestions,
                "requires_clarification": result.requires_clarification,
                "clarification_questions": result.clarification_questions,
            }

            return TaskResult(
                success=True,
                result=output,
                metadata={
                    "processing_time": result.processing_time,
                    "input_length": len(input_text),
                    "intent_count": len(result.intents),
                    "entity_count": len(result.entities)
                }
            )

        except Exception as e:
            logger.error(f"NLU task execution failed: {e}")
            return TaskResult(
                success=False,
                error=str(e),
                metadata={"task": task}
            )

    async def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this NLU agent."""
        return {
            "agent_type": "nlu",
            "capabilities": [
                "intent_classification",
                "entity_extraction",
                "context_understanding",
                "educational_focus",
                "clarification_generation",
                "sentiment_analysis"
            ],
            "supported_intents": [intent.value for intent in IntentType],
            "supported_entities": [entity.value for entity in EntityType],
            "supported_subjects": self.config.supported_subjects,
            "grade_range": self.config.grade_level_range,
            "languages": ["en"],
            "max_context_window": self.config.context_window
        }

    async def _process_task(self, state: AgentState) -> Any:
        """
        Process a task through NLU.

        This implements the abstract method from BaseAgent.

        Args:
            state: Current agent state containing the task

        Returns:
            NLUResult with extracted information
        """
        # Extract the task from the first message
        task_text = ""
        if state["messages"]:
            # Get the content from the first message
            first_message = state["messages"][0]
            if hasattr(first_message, "content"):
                task_text = first_message.content
            else:
                task_text = str(first_message)
        else:
            task_text = state.get("task", "")

        # Process through NLU
        result = await self.process(task_text, state.get("context"))

        return result