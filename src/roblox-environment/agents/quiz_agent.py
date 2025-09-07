"""
Quiz Agent - Specializes in creating interactive quizzes and assessments

Generates educational assessments for Roblox learning environments.
"""

import logging
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field

from .base_agent import BaseAgent, AgentConfig, AgentState, TaskResult

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
                model="gpt-4",
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
        """Process quiz generation task"""
        task = state["task"]
        context = state["context"]

        # Extract parameters
        subject = context.get("subject", "General")
        topic = context.get("topic", "General Knowledge")
        grade_level = context.get("grade_level", "6-8")
        num_questions = context.get("num_questions", 10)
        difficulty = context.get("difficulty", "medium")
        question_types = context.get("question_types", ["multiple_choice"])
        learning_objectives = context.get("learning_objectives", [])

        # Generate quiz
        quiz = await self._generate_quiz(
            subject=subject,
            topic=topic,
            grade_level=grade_level,
            num_questions=num_questions,
            difficulty=difficulty,
            question_types=question_types,
            objectives=learning_objectives,
        )

        # Generate Lua implementation
        lua_implementation = self._generate_lua_quiz_script(quiz)

        # Create feedback system
        feedback_system = self._create_feedback_system(quiz)

        # Package result
        result = {
            "quiz": quiz.dict(),
            "lua_script": lua_implementation,
            "feedback_system": feedback_system,
            "metadata": {
                "subject": subject,
                "topic": topic,
                "grade_level": grade_level,
                "generated_at": datetime.now().isoformat(),
            },
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
