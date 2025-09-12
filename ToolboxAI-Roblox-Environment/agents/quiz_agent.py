"""
Quiz Agent - Specializes in creating interactive quizzes and assessments

Generates educational assessments for Roblox learning environments.
"""

import logging
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import uuid
import asyncio
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field

from .base_agent import BaseAgent, AgentConfig, AgentState, TaskResult

# Add project paths for database imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Database integration
try:
    from database.repositories import (
        QuizRepository, ContentRepository, 
        LessonRepository, ProgressRepository,
        AnalyticsRepository
    )
    from database.models import (
        Quiz as DBQuiz, QuizQuestion as DBQuizQuestion,
        QuizAttempt, QuizResponse, DifficultyLevel
    )
    from database.connection_manager import get_session
    DATABASE_AVAILABLE = True
except ImportError as e:
    DATABASE_AVAILABLE = False
    # Define DifficultyLevel locally if database models not available
    from enum import Enum
    class DifficultyLevel(Enum):
        BEGINNER = "beginner"
        INTERMEDIATE = "intermediate"
        ADVANCED = "advanced"
        EXPERT = "expert"
    QuizRepository = None
    ContentRepository = None
    
# SPARC Framework integration
try:
    from sparc.state_manager import StateManager
    from sparc.policy_engine import PolicyEngine
    from sparc.action_executor import ActionExecutor
    from sparc.reward_calculator import RewardCalculator
    from sparc.context_tracker import ContextTracker
    SPARC_AVAILABLE = True
except ImportError:
    SPARC_AVAILABLE = False
    StateManager = None
    PolicyEngine = None
    
# MCP Context management
try:
    from mcp.context_manager import MCPContextManager
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MCPContextManager = None

# Environment configuration
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from config.environment import get_environment_config
    env_config = get_environment_config()
except ImportError as e:
    # If still can't import, create a minimal fallback
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import config.environment: {e}")
    
    class FallbackConfig:
        def __init__(self):
            self.use_mock_llm = os.getenv("USE_MOCK_LLM", "true").lower() == "true"
            self.use_mock_database = False
            self.use_mock_services = False
            self.bypass_rate_limit = True
            self.debug_mode = True
            self.log_level = "DEBUG"
            self.require_auth = False
            self.validate_ssl = False
            self.cache_enabled = True
    
    env_config = FallbackConfig()

logger = logging.getLogger(__name__)


class QuizQuestion(BaseModel):
    """Model for a quiz question"""

    question: str
    options: List[str]
    correct_answer: int  # Index of correct option
    explanation: str
    difficulty: str = "medium"
    points: int = 10
    category: str = "general"
    hint: Optional[str] = None


class Quiz(BaseModel):
    """Model for a complete quiz"""

    title: str
    description: str
    questions: List[QuizQuestion]
    time_limit: Optional[int] = None  # in seconds
    passing_score: int = 70  # percentage
    randomize: bool = True
    allow_review: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QuizAgent(BaseAgent):
    """
    Agent specialized in creating quizzes and assessments.

    Capabilities:
    - Multiple choice question generation
    - True/false questions
    - Fill-in-the-blank questions
    - Matching exercises
    - Adaptive difficulty
    - Immediate feedback generation
    - Progress tracking integration
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="QuizAgent",
                model="gpt-3.5-turbo",
                temperature=0.5,  # Lower temperature for more consistent questions
                system_prompt=self._get_quiz_prompt(),
            )
        super().__init__(config)

        # Question type templates
        self.question_types = ["multiple_choice", "true_false", "fill_blank", "matching", "ordering", "short_answer"]

        # Difficulty levels
        self.difficulty_levels = {
            "easy": {"options": 3, "hints": True, "points": 5},
            "medium": {"options": 4, "hints": False, "points": 10},
            "hard": {"options": 5, "hints": False, "points": 15},
            "expert": {"options": 6, "hints": False, "points": 20},
        }

        # Bloom's Taxonomy levels for question design
        self.blooms_levels = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
        
        # Initialize database repositories if available
        self.quiz_repo = None
        self.content_repo = None
        self.analytics_repo = None
        self.db_session = None
        
        # Initialize SPARC components if available
        if SPARC_AVAILABLE:
            self.state_manager = StateManager()
            self.policy_engine = PolicyEngine()
            self.action_executor = ActionExecutor()
            self.reward_calculator = RewardCalculator()
            self.context_tracker = ContextTracker()
        else:
            self.state_manager = None
            self.policy_engine = None
            
        # Initialize MCP context manager if available
        if MCP_AVAILABLE:
            self.mcp_context = MCPContextManager(
                server_url="ws://127.0.0.1:9876",
                agent_name="QuizAgent"
            )
        else:
            self.mcp_context = None
            
        # Track quiz generation metrics
        self.generation_metrics = {
            "total_quizzes": 0,
            "total_questions": 0,
            "average_quality_score": 0.0,
            "database_saves": 0,
            "api_calls": 0
        }

    def _get_quiz_prompt(self) -> str:
        """Get specialized prompt for quiz generation"""
        return """You are a Quiz and Assessment Specialist for educational Roblox games.

Your expertise includes:
- Creating engaging, age-appropriate quiz questions
- Designing assessments aligned with learning objectives
- Implementing Bloom's Taxonomy in question design
- Providing constructive feedback and explanations
- Ensuring accessibility and fairness in assessments

When creating quizzes:
1. Align questions with specific learning objectives
2. Use clear, unambiguous language
3. Provide plausible distractors for multiple choice
4. Include explanations for correct answers
5. Vary question difficulty and types
6. Avoid trick questions or confusing wording
7. Ensure cultural sensitivity and inclusion
8. Design for the Roblox platform's interactive nature

Question Quality Criteria:
- Relevance to learning objectives
- Appropriate cognitive level
- Clear and concise wording
- Single correct answer (for objective questions)
- Educational value in both question and feedback"""

    async def _process_task(self, state: AgentState) -> Any:
        """Process quiz generation task with database and SPARC integration"""
        task = state["task"]
        context = state["context"]
        
        # Initialize database session if available
        await self._init_database_session()

        # Extract parameters
        subject = context.get("subject", "General")
        topic = context.get("topic", "General Knowledge")
        grade_level = context.get("grade_level", "6-8")
        num_questions = context.get("num_questions", 10)
        difficulty = context.get("difficulty", "medium")
        question_types = context.get("question_types", ["multiple_choice"])
        learning_objectives = context.get("learning_objectives", [])
        lesson_id = context.get("lesson_id")  # Optional lesson association
        user_id = context.get("user_id")  # Optional for adaptive quiz
        
        # SPARC: Initialize state tracking
        sparc_state = None
        if self.state_manager:
            sparc_state = await self.state_manager.update_state({
                "agent": "QuizAgent",
                "task": task,
                "subject": subject,
                "topic": topic,
                "grade_level": grade_level
            })
            
        # Get curriculum standards from database if available
        if DATABASE_AVAILABLE and self.content_repo and lesson_id:
            try:
                # Fetch real curriculum standards from database
                standards = await self._fetch_curriculum_standards(lesson_id)
                if standards:
                    learning_objectives.extend(standards)
            except Exception as e:
                logger.warning(f"Failed to fetch curriculum standards: {e}")

        # Generate quiz with real data integration
        quiz = await self._generate_quiz(
            subject=subject,
            topic=topic,
            grade_level=grade_level,
            num_questions=num_questions,
            difficulty=difficulty,
            question_types=question_types,
            objectives=learning_objectives
        )
        
        # SPARC: Execute quiz generation action
        if self.action_executor and sparc_state:
            try:
                action_result = await self.action_executor.execute({
                    "action": "generate_quiz",
                    "quiz_data": quiz.model_dump(),
                    "state": sparc_state
                })
            except Exception as e:
                logger.warning(f"Failed to execute SPARC action: {e}")

        # Save quiz to database if available
        db_quiz_id = None
        if DATABASE_AVAILABLE and self.quiz_repo and lesson_id:
            try:
                db_quiz_id = await self._save_quiz_to_database(
                    quiz, lesson_id, context.get("created_by_id")
                )
                self.generation_metrics["database_saves"] += 1
            except Exception as e:
                logger.warning(f"Failed to save quiz to database: {e}")

        # Generate Lua implementation
        lua_implementation = self._generate_lua_quiz_script(quiz)

        # Create feedback system
        feedback_system = self._create_feedback_system(quiz)
        
        # SPARC: Calculate rewards based on quiz quality
        quality_score = 0.0
        if self.reward_calculator:
            quality_score = await self.reward_calculator.calculate_rewards({
                "quiz": quiz.model_dump(),
                "num_questions": len(quiz.questions),
                "has_explanations": all(q.explanation for q in quiz.questions),
                "has_hints": any(q.hint for q in quiz.questions),
                "difficulty_variety": len(set(q.difficulty for q in quiz.questions))
            })
            
        # Update MCP context if available
        if self.mcp_context:
            try:
                await self.mcp_context.update_context({
                    "quiz_generated": {
                        "id": str(db_quiz_id) if db_quiz_id else None,
                        "title": quiz.title,
                        "subject": subject,
                        "topic": topic,
                        "num_questions": len(quiz.questions),
                        "quality_score": quality_score
                    }
                })
            except Exception as e:
                logger.warning(f"Failed to update MCP context: {e}")
        
        # Track analytics if available
        if DATABASE_AVAILABLE and self.analytics_repo:
            try:
                await self.analytics_repo.track_event(
                    event_type="quiz_generated",
                    user_id=user_id,
                    event_data={
                        "quiz_id": str(db_quiz_id) if db_quiz_id else None,
                        "subject": subject,
                        "topic": topic,
                        "num_questions": num_questions,
                        "quality_score": quality_score
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to track analytics: {e}")
        
        # Update metrics
        self.generation_metrics["total_quizzes"] += 1
        self.generation_metrics["total_questions"] += len(quiz.questions)
        self.generation_metrics["api_calls"] += 1
        
        # Commit database changes if needed
        if self.db_session:
            try:
                await self.db_session.commit()
            except Exception as e:
                logger.error(f"Failed to commit database changes: {e}")
                await self.db_session.rollback()

        # Package result with enhanced metadata
        result = {
            "quiz": quiz.model_dump(),
            "lua_script": lua_implementation,
            "feedback_system": feedback_system,
            "database_id": str(db_quiz_id) if db_quiz_id else None,
            "quality_score": quality_score,
            "metadata": {
                "subject": subject,
                "topic": topic,
                "grade_level": grade_level,
                "generated_at": datetime.now().isoformat(),
                "sparc_tracked": sparc_state is not None,
                "database_saved": db_quiz_id is not None,
                "mcp_updated": self.mcp_context is not None
            },
            "metrics": self.generation_metrics.copy()
        }

        return result

    async def _generate_quiz(
        self,
        subject: str,
        topic: str,
        grade_level: str,
        num_questions: int,
        difficulty: str,
        question_types: List[str],
        objectives: List[str],
    ) -> Quiz:
        """Generate a complete quiz"""

        # Create quiz generation prompt
        objectives_text = (
            "\n".join(f"- {obj}" for obj in objectives) if objectives else "- Assess understanding of the topic"
        )

        prompt = f"""Create a quiz for a Roblox educational game:

Subject: {subject}
Topic: {topic}
Grade Level: {grade_level}
Number of Questions: {num_questions}
Difficulty: {difficulty}
Question Types: {', '.join(question_types)}

Learning Objectives:
{objectives_text}

Generate {num_questions} questions that:
1. Test different cognitive levels (Bloom's Taxonomy)
2. Are age-appropriate for {grade_level}
3. Include clear answer choices (for multiple choice)
4. Have educational explanations for each answer
5. Progressively increase in difficulty

For each question provide:
- Question text
- 4 answer options (for multiple choice)
- Correct answer index (0-3)
- Explanation why the answer is correct
- A helpful hint (for easy mode)
- Difficulty level (easy/medium/hard)
- Points value

Format as JSON."""

        response = await self.llm.ainvoke(prompt)

        # Parse response and create quiz questions
        questions = self._parse_quiz_response(response.content, num_questions)

        # Create quiz object
        quiz = Quiz(
            title=f"{topic} Quiz",
            description=f"Test your knowledge of {topic} in {subject}",
            questions=questions,
            time_limit=60 * num_questions,  # 60 seconds per question
            passing_score=70,
            randomize=True,
            allow_review=True,
            metadata={"subject": subject, "grade_level": grade_level, "objectives": objectives},
        )

        return quiz
    
    async def _init_database_session(self):
        """Initialize database session if available"""
        if DATABASE_AVAILABLE and not self.db_session:
            try:
                self.db_session = await get_session()
                self.quiz_repo = QuizRepository(self.db_session)
                self.content_repo = ContentRepository(self.db_session)
                self.analytics_repo = AnalyticsRepository(self.db_session)
            except Exception as e:
                logger.warning(f"Failed to initialize database session: {e}")
                # Set instance variables to None to indicate database unavailability
                self.db_session = None
                self.quiz_repo = None
                self.content_repo = None
                self.analytics_repo = None
    
    async def _fetch_curriculum_standards(self, lesson_id: str) -> List[str]:
        """Fetch real curriculum standards from database"""
        standards = []
        try:
            if self.content_repo:
                # Get lesson content to extract learning objectives
                content_items = await self.content_repo.get_by_lesson(
                    uuid.UUID(lesson_id)
                )
                for item in content_items:
                    if item.metadata and "learning_objectives" in item.metadata:
                        standards.extend(item.metadata["learning_objectives"])
        except Exception as e:
            logger.warning(f"Error fetching curriculum standards: {e}")
        return standards
    
    async def _save_quiz_to_database(
        self, 
        quiz: Quiz, 
        lesson_id: str,
        created_by_id: Optional[str] = None
    ) -> uuid.UUID:
        """Save generated quiz to database"""
        if not self.quiz_repo:
            return None
            
        try:
            # Create quiz in database
            db_quiz = await self.quiz_repo.create(
                title=quiz.title,
                description=quiz.description,
                lesson_id=uuid.UUID(lesson_id) if lesson_id else None,
                created_by_id=uuid.UUID(created_by_id) if created_by_id else None,
                quiz_type="multiple_choice",
                time_limit=quiz.time_limit,
                passing_score=quiz.passing_score,
                max_attempts=3,
                randomize_questions=quiz.randomize,
                show_feedback=quiz.allow_review,
                metadata=quiz.metadata,
                is_active=True
            )
            
            # Add questions to database
            for idx, question in enumerate(quiz.questions):
                db_question = DBQuizQuestion(
                    quiz_id=db_quiz.id,
                    question_text=question.question,
                    question_type="multiple_choice",
                    options=question.options,
                    correct_answer=question.options[question.correct_answer],
                    explanation=question.explanation,
                    hint=question.hint,
                    points=question.points,
                    order_index=idx,
                    difficulty=self._map_difficulty(question.difficulty),
                    metadata={"category": question.category}
                )
                self.db_session.add(db_question)
            
            await self.db_session.flush()
            return db_quiz.id
            
        except Exception as e:
            logger.error(f"Failed to save quiz to database: {e}")
            raise
    
    def _map_difficulty(self, difficulty: str) -> DifficultyLevel:
        """Map string difficulty to enum"""
        mapping = {
            "easy": DifficultyLevel.BEGINNER,
            "beginner": DifficultyLevel.BEGINNER,
            "medium": DifficultyLevel.INTERMEDIATE,
            "intermediate": DifficultyLevel.INTERMEDIATE,
            "hard": DifficultyLevel.ADVANCED,
            "advanced": DifficultyLevel.ADVANCED,
            "expert": DifficultyLevel.EXPERT
        }
        return mapping.get(difficulty.lower(), DifficultyLevel.INTERMEDIATE)

    def _parse_quiz_response(self, response: str, num_questions: int) -> List[QuizQuestion]:
        """Parse LLM response into quiz questions"""
        questions = []

        try:
            # Try to parse as JSON first
            data = json.loads(response)
            if isinstance(data, list):
                for item in data[:num_questions]:
                    question = QuizQuestion(
                        question=item.get("question", ""),
                        options=item.get("options", ["A", "B", "C", "D"]),
                        correct_answer=item.get("correct_answer", 0),
                        explanation=item.get("explanation", ""),
                        difficulty=item.get("difficulty", "medium"),
                        points=item.get("points", 10),
                        hint=item.get("hint"),
                    )
                    questions.append(question)
        except json.JSONDecodeError:
            # Fallback to text parsing
            # Create sample questions if parsing fails
            for i in range(num_questions):
                question = QuizQuestion(
                    question=f"Sample question {i+1} from the topic",
                    options=[f"Option A", f"Option B", f"Option C", f"Option D"],
                    correct_answer=random.randint(0, 3),
                    explanation="This is the correct answer because...",
                    difficulty="medium",
                    points=10,
                    hint="Think about the main concept",
                )
                questions.append(question)

        return questions

    def _generate_lua_quiz_script(self, quiz: Quiz) -> str:
        """Generate Lua script for Roblox quiz implementation"""

        script = f"""-- Quiz: {quiz.title}
-- Generated by QuizAgent

local QuizModule = {{}}
QuizModule.__index = QuizModule

-- Quiz Data
local QUIZ_DATA = {{
    title = "{quiz.title}",
    description = "{quiz.description}",
    timeLimit = {quiz.time_limit or 0},
    passingScore = {quiz.passing_score},
    questions = {{
"""

        # Add questions
        for i, question in enumerate(quiz.questions, 1):
            script += f"""        {{
            question = "{question.question.replace('"', '\\"')}",
            options = {{
"""
            for option in question.options:
                script += f'                "{option.replace('"', '\\"')}",\n'

            script += f"""            }},
            correctAnswer = {question.correct_answer + 1},  -- Lua arrays start at 1
            explanation = "{question.explanation.replace('"', '\\"')}",
            points = {question.points},
            difficulty = "{question.difficulty}",
            hint = "{question.hint or 'No hint available'}"
        }},
"""

        script += """    }
}

function QuizModule.new(gui)
    local self = setmetatable({}, QuizModule)
    self.gui = gui
    self.currentQuestion = 1
    self.score = 0
    self.answers = {}
    self.startTime = tick()
    self.timeLeft = QUIZ_DATA.timeLimit
    
    return self
end

function QuizModule:StartQuiz()
    print("Starting quiz: " .. QUIZ_DATA.title)
    self:LoadQuestion(1)
    if QUIZ_DATA.timeLimit > 0 then
        self:StartTimer()
    end
end

function QuizModule:LoadQuestion(questionNumber)
    if questionNumber > #QUIZ_DATA.questions then
        self:EndQuiz()
        return
    end
    
    local questionData = QUIZ_DATA.questions[questionNumber]
    self.currentQuestion = questionNumber
    
    -- Update UI
    self:UpdateQuestionDisplay(questionData)
    self:UpdateProgressBar()
end

function QuizModule:UpdateQuestionDisplay(questionData)
    -- Update question text
    local questionLabel = self.gui.QuestionFrame.QuestionText
    questionLabel.Text = questionData.question
    
    -- Update options
    local optionsFrame = self.gui.QuestionFrame.OptionsFrame
    for i, option in ipairs(questionData.options) do
        local button = optionsFrame:FindFirstChild("Option" .. i)
        if button then
            button.Text = option
            button.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
        end
    end
    
    -- Update question number
    local progressLabel = self.gui.QuestionFrame.ProgressLabel
    progressLabel.Text = "Question " .. self.currentQuestion .. " of " .. #QUIZ_DATA.questions
end

function QuizModule:SelectAnswer(optionNumber)
    local questionData = QUIZ_DATA.questions[self.currentQuestion]
    local isCorrect = optionNumber == questionData.correctAnswer
    
    -- Store answer
    self.answers[self.currentQuestion] = {
        selected = optionNumber,
        correct = questionData.correctAnswer,
        isCorrect = isCorrect
    }
    
    -- Update score
    if isCorrect then
        self.score = self.score + questionData.points
        self:ShowFeedback(true, questionData.explanation)
    else
        self:ShowFeedback(false, questionData.explanation)
    end
    
    -- Auto-advance after delay
    wait(2)
    self:NextQuestion()
end

function QuizModule:ShowFeedback(isCorrect, explanation)
    local feedbackFrame = self.gui.FeedbackFrame
    feedbackFrame.Visible = true
    
    if isCorrect then
        feedbackFrame.BackgroundColor3 = Color3.fromRGB(0, 255, 0)
        feedbackFrame.StatusText.Text = "Correct!"
    else
        feedbackFrame.BackgroundColor3 = Color3.fromRGB(255, 0, 0)
        feedbackFrame.StatusText.Text = "Incorrect"
    end
    
    feedbackFrame.ExplanationText.Text = explanation
end

function QuizModule:NextQuestion()
    self:LoadQuestion(self.currentQuestion + 1)
end

function QuizModule:EndQuiz()
    -- Calculate final score
    local percentage = (self.score / self:GetMaxScore()) * 100
    local passed = percentage >= QUIZ_DATA.passingScore
    
    -- Show results
    self:ShowResults(percentage, passed)
    
    -- Fire completion event
    game.ReplicatedStorage.QuizCompleted:Fire({
        score = self.score,
        percentage = percentage,
        passed = passed,
        timeSpent = tick() - self.startTime
    })
end

function QuizModule:GetMaxScore()
    local maxScore = 0
    for _, question in ipairs(QUIZ_DATA.questions) do
        maxScore = maxScore + question.points
    end
    return maxScore
end

function QuizModule:ShowResults(percentage, passed)
    local resultsFrame = self.gui.ResultsFrame
    resultsFrame.Visible = true
    
    resultsFrame.ScoreText.Text = string.format("Score: %d/%d (%.1f%%)", 
        self.score, self:GetMaxScore(), percentage)
    
    if passed then
        resultsFrame.StatusText.Text = "PASSED!"
        resultsFrame.StatusText.TextColor3 = Color3.fromRGB(0, 255, 0)
    else
        resultsFrame.StatusText.Text = "Try Again"
        resultsFrame.StatusText.TextColor3 = Color3.fromRGB(255, 255, 0)
    end
end

function QuizModule:StartTimer()
    spawn(function()
        while self.timeLeft > 0 do
            wait(1)
            self.timeLeft = self.timeLeft - 1
            self:UpdateTimerDisplay()
            
            if self.timeLeft <= 0 then
                self:EndQuiz()
                break
            end
        end
    end)
end

function QuizModule:UpdateTimerDisplay()
    local timerLabel = self.gui.TimerFrame.TimerText
    local minutes = math.floor(self.timeLeft / 60)
    local seconds = self.timeLeft % 60
    timerLabel.Text = string.format("%d:%02d", minutes, seconds)
    
    -- Change color when time is running out
    if self.timeLeft <= 30 then
        timerLabel.TextColor3 = Color3.fromRGB(255, 0, 0)
    elseif self.timeLeft <= 60 then
        timerLabel.TextColor3 = Color3.fromRGB(255, 255, 0)
    end
end

function QuizModule:UpdateProgressBar()
    local progressBar = self.gui.ProgressFrame.ProgressBar
    local progress = (self.currentQuestion - 1) / #QUIZ_DATA.questions
    progressBar.Size = UDim2.new(progress, 0, 1, 0)
end

return QuizModule
"""

        return script

    def _create_feedback_system(self, quiz: Quiz) -> Dict[str, Any]:
        """Create a comprehensive feedback system for the quiz"""

        feedback_system = {
            "immediate_feedback": [],
            "summary_feedback": {},
            "improvement_suggestions": [],
            "achievement_triggers": [],
        }

        # Generate immediate feedback for each question
        for i, question in enumerate(quiz.questions):
            feedback_system["immediate_feedback"].append(
                {
                    "question_index": i,
                    "correct_feedback": f"Great job! {question.explanation}",
                    "incorrect_feedback": f"Not quite. {question.explanation}",
                    "hint_available": question.hint is not None,
                    "hint_text": question.hint,
                }
            )

        # Summary feedback templates
        feedback_system["summary_feedback"] = {
            "excellent": "Outstanding! You've mastered this topic!",
            "good": "Well done! You have a solid understanding.",
            "passing": "Good effort! You passed, but there's room for improvement.",
            "needs_work": "Keep practicing! Review the material and try again.",
        }

        # Achievement triggers
        feedback_system["achievement_triggers"] = [
            {"condition": "percentage >= 100", "achievement": "Perfect Score!"},
            {"condition": "percentage >= 90", "achievement": "Quiz Master"},
            {"condition": "time_spent < time_limit * 0.5", "achievement": "Speed Demon"},
            {"condition": "first_attempt and passed", "achievement": "First Try Success"},
        ]

        return feedback_system

    async def generate_adaptive_quiz(self, student_performance: Dict[str, Any], subject: str, topic: str) -> Quiz:
        """Generate an adaptive quiz based on student performance"""

        # Analyze student performance
        weak_areas = student_performance.get("weak_areas", [])
        skill_level = student_performance.get("skill_level", "intermediate")

        prompt = f"""Create an adaptive quiz based on student performance:

Student Profile:
- Skill Level: {skill_level}
- Weak Areas: {weak_areas}
- Previous Score: {student_performance.get('last_score', 'N/A')}

Subject: {subject}
Topic: {topic}

Generate questions that:
1. Target identified weak areas
2. Gradually increase in difficulty
3. Provide scaffolding for challenging concepts
4. Include review of previously missed topics
5. Adapt to the student's skill level

Create 8-10 questions with appropriate difficulty progression."""

        response = await self.llm.ainvoke(prompt)

        # Parse and create adaptive quiz
        questions = self._parse_quiz_response(response.content, 10)

        quiz = Quiz(
            title=f"Adaptive {topic} Quiz",
            description=f"Personalized quiz based on your learning progress",
            questions=questions,
            time_limit=None,  # No time limit for adaptive quizzes
            passing_score=60,  # Lower passing score for adaptive
            randomize=False,  # Keep adaptive order
            metadata={"type": "adaptive", "student_profile": student_performance},
        )
        
        # Save adaptive quiz to database if available
        if DATABASE_AVAILABLE and self.quiz_repo:
            try:
                await self._save_quiz_to_database(
                    quiz, 
                    lesson_id=None,  # Adaptive quizzes may not have lesson
                    created_by_id=user_id
                )
            except Exception as e:
                logger.warning(f"Failed to save adaptive quiz: {e}")

        return quiz

    async def create_quiz_from_content(self, content: str, num_questions: int = 5) -> Quiz:
        """Create a quiz from provided educational content"""

        prompt = f"""Create a quiz based on this educational content:

{content[:2000]}...

Generate {num_questions} multiple-choice questions that:
1. Test key concepts from the content
2. Include varied difficulty levels
3. Have clear, unambiguous wording
4. Include educational explanations

Format as a structured quiz."""

        response = await self.llm.ainvoke(prompt)

        questions = self._parse_quiz_response(response.content, num_questions)

        quiz = Quiz(
            title="Content-Based Quiz",
            description="Test your understanding of the material",
            questions=questions,
            metadata={"source": "content_extraction"},
        )

        return quiz
    
    async def get_quiz_statistics(
        self, 
        quiz_id: str
    ) -> Dict[str, Any]:
        """Get quiz statistics from database"""
        if not DATABASE_AVAILABLE or not self.quiz_repo:
            return {"error": "Database not available"}
        
        try:
            quiz_uuid = uuid.UUID(quiz_id)
            
            # Get quiz with attempts
            quiz = await self.quiz_repo.get_with_questions(quiz_uuid)
            if not quiz:
                return {"error": "Quiz not found"}
            
            # Get attempt statistics
            stmt = f"""SELECT 
                          COUNT(*) as total_attempts,
                          AVG(percentage) as avg_score,
                          MAX(percentage) as highest_score,
                          MIN(percentage) as lowest_score,
                          AVG(time_taken) as avg_time
                       FROM quiz_attempts 
                       WHERE quiz_id = '{quiz_uuid}' 
                       AND status = 'completed'"""
            
            result = await self.db_session.execute(stmt)
            stats = result.fetchone()
            
            return {
                "quiz_id": quiz_id,
                "title": quiz.title,
                "total_attempts": stats.total_attempts or 0,
                "average_score": float(stats.avg_score or 0),
                "highest_score": float(stats.highest_score or 0),
                "lowest_score": float(stats.lowest_score or 0),
                "average_time_seconds": int(stats.avg_time or 0),
                "num_questions": len(quiz.questions),
                "passing_score": quiz.passing_score
            }
            
        except Exception as e:
            logger.error(f"Failed to get quiz statistics: {e}")
            return {"error": str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent generation metrics"""
        avg_quality = (
            self.generation_metrics["average_quality_score"] 
            if self.generation_metrics["total_quizzes"] == 0
            else self.generation_metrics["average_quality_score"] / self.generation_metrics["total_quizzes"]
        )
        
        return {
            **self.generation_metrics,
            "average_quality_score": avg_quality,
            "database_integration": DATABASE_AVAILABLE,
            "sparc_integration": SPARC_AVAILABLE,
            "mcp_integration": MCP_AVAILABLE
        }
