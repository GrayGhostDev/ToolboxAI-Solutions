"""
Assessment schema definitions
"""

from ..models.schemas import (
    DifficultyLevel,
    Quiz,
    QuizOption,
    QuizQuestion,
    QuizResponse,
    QuizType,
)

# Assessment-related schemas
AssessmentRequest = Quiz
AssessmentResponse = QuizResponse
Question = QuizQuestion
Option = QuizOption
QuestionType = QuizType
Difficulty = DifficultyLevel

__all__ = [
    "Quiz",
    "QuizQuestion",
    "QuizOption",
    "QuizResponse",
    "QuizType",
    "DifficultyLevel",
    "AssessmentRequest",
    "AssessmentResponse",
    "Question",
    "Option",
    "QuestionType",
    "Difficulty",
]
