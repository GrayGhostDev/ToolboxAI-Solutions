"""Content-related test data factories."""

import factory
from factory import fuzzy
from faker import Faker
from typing import List, Dict, Any
from .base_factory import DictFactory, AsyncMixin
import json

fake = Faker()


class ContentFactory(DictFactory, AsyncMixin):
    """Factory for educational content."""

    id = factory.LazyFunction(lambda: fake.uuid4())
    title = factory.LazyFunction(lambda: fake.catch_phrase())
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=500))
    subject = fuzzy.FuzzyChoice([
        "Mathematics", "Science", "English", "History",
        "Geography", "Computer Science", "Art", "Music"
    ])
    grade_level = factory.LazyFunction(lambda: fake.random_int(1, 12))
    difficulty = fuzzy.FuzzyChoice(["beginner", "intermediate", "advanced"])

    # Content details
    content_type = fuzzy.FuzzyChoice(["lesson", "quiz", "assignment", "project", "video"])
    duration_minutes = factory.LazyFunction(lambda: fake.random_int(15, 120))

    # Rich content
    body = factory.LazyFunction(lambda: fake.text(max_nb_chars=2000))

    # Media attachments
    attachments = factory.LazyFunction(
        lambda: [
            {
                "id": fake.uuid4(),
                "type": fake.random_element(["pdf", "video", "image", "audio"]),
                "url": fake.url(),
                "title": fake.file_name(),
                "size_bytes": fake.random_int(1000, 10000000),
            }
            for _ in range(fake.random_int(0, 5))
        ]
    )

    # Learning objectives
    objectives = factory.LazyFunction(
        lambda: [fake.sentence() for _ in range(fake.random_int(3, 7))]
    )

    # Tags and keywords
    tags = factory.LazyFunction(
        lambda: fake.words(nb=fake.random_int(3, 10))
    )

    # Metadata
    author_id = factory.LazyFunction(lambda: fake.uuid4())
    created_at = factory.LazyFunction(lambda: fake.date_time_this_year().isoformat())
    updated_at = factory.LazyFunction(lambda: fake.date_time_this_month().isoformat())
    published = factory.LazyFunction(lambda: fake.boolean(chance_of_getting_true=80))

    # Statistics
    views = factory.LazyFunction(lambda: fake.random_int(0, 10000))
    likes = factory.LazyFunction(lambda: fake.random_int(0, 1000))
    comments_count = factory.LazyFunction(lambda: fake.random_int(0, 100))

    # AI-generated fields
    ai_generated = factory.LazyFunction(lambda: fake.boolean())
    ai_model = factory.LazyFunction(
        lambda: fake.random_element(["gpt-4", "claude-3", "llama-2", None])
    )
    ai_confidence = factory.LazyFunction(lambda: round(fake.random.uniform(0.7, 1.0), 2))

    @classmethod
    def with_quiz(cls, num_questions: int = 5, **kwargs):
        """Create content with quiz questions."""
        content = cls.create(content_type="quiz", **kwargs)
        content["quiz_data"] = QuizFactory.create(num_questions=num_questions)
        return content

    @classmethod
    def with_rubric(cls, **kwargs):
        """Create content with assessment rubric."""
        content = cls.create(**kwargs)
        content["rubric"] = {
            "criteria": [
                {
                    "name": fake.word(),
                    "description": fake.sentence(),
                    "points": fake.random_int(1, 10),
                    "levels": [
                        {"level": i, "description": fake.sentence(), "points": i}
                        for i in range(1, 5)
                    ]
                }
                for _ in range(fake.random_int(3, 6))
            ],
            "total_points": fake.random_int(50, 100),
        }
        return content


class QuizFactory(DictFactory):
    """Factory for quiz generation."""

    id = factory.LazyFunction(lambda: fake.uuid4())
    title = factory.LazyFunction(lambda: f"{fake.word().title()} Quiz")
    instructions = factory.LazyFunction(lambda: fake.paragraph())
    time_limit_minutes = factory.LazyFunction(lambda: fake.random_int(10, 60))
    attempts_allowed = factory.LazyFunction(lambda: fake.random_int(1, 3))
    shuffle_questions = factory.LazyFunction(lambda: fake.boolean())
    show_correct_answers = factory.LazyFunction(lambda: fake.boolean())

    @factory.lazy_attribute
    def questions(self):
        """Generate quiz questions."""
        num_questions = getattr(self, "num_questions", fake.random_int(5, 20))
        questions = []

        for i in range(num_questions):
            question_type = fake.random_element(["multiple_choice", "true_false", "short_answer", "essay"])

            if question_type == "multiple_choice":
                options = [fake.sentence() for _ in range(4)]
                question = {
                    "id": fake.uuid4(),
                    "type": "multiple_choice",
                    "question": fake.sentence().replace(".", "?"),
                    "options": options,
                    "correct_answer": fake.random_int(0, 3),
                    "points": fake.random_int(1, 5),
                    "explanation": fake.paragraph(),
                }
            elif question_type == "true_false":
                question = {
                    "id": fake.uuid4(),
                    "type": "true_false",
                    "question": fake.sentence(),
                    "correct_answer": fake.boolean(),
                    "points": fake.random_int(1, 3),
                    "explanation": fake.paragraph(),
                }
            elif question_type == "short_answer":
                question = {
                    "id": fake.uuid4(),
                    "type": "short_answer",
                    "question": fake.sentence().replace(".", "?"),
                    "expected_keywords": fake.words(nb=fake.random_int(3, 7)),
                    "points": fake.random_int(5, 10),
                    "max_length": fake.random_int(100, 500),
                }
            else:  # essay
                question = {
                    "id": fake.uuid4(),
                    "type": "essay",
                    "question": fake.paragraph(),
                    "points": fake.random_int(10, 25),
                    "min_words": fake.random_int(100, 300),
                    "rubric": {
                        "content": fake.random_int(1, 10),
                        "organization": fake.random_int(1, 10),
                        "grammar": fake.random_int(1, 5),
                    }
                }

            questions.append(question)

        return questions

    @factory.lazy_attribute
    def total_points(self):
        """Calculate total points from questions."""
        return sum(q.get("points", 0) for q in self.questions)

    @factory.lazy_attribute
    def passing_score(self):
        """Set passing score as percentage of total."""
        return int(self.total_points * 0.7)  # 70% to pass


class AssessmentFactory(DictFactory):
    """Factory for student assessments."""

    id = factory.LazyFunction(lambda: fake.uuid4())
    student_id = factory.LazyFunction(lambda: fake.uuid4())
    content_id = factory.LazyFunction(lambda: fake.uuid4())
    quiz_id = factory.LazyFunction(lambda: fake.uuid4())

    # Submission details
    submitted_at = factory.LazyFunction(lambda: fake.date_time_this_week().isoformat())
    time_taken_minutes = factory.LazyFunction(lambda: fake.random_int(5, 120))
    attempt_number = factory.LazyFunction(lambda: fake.random_int(1, 3))

    # Answers
    @factory.lazy_attribute
    def answers(self):
        """Generate student answers."""
        num_questions = fake.random_int(5, 20)
        answers = []

        for i in range(num_questions):
            answer_type = fake.random_element(["multiple_choice", "true_false", "short_answer", "essay"])

            if answer_type == "multiple_choice":
                answer = {
                    "question_id": fake.uuid4(),
                    "answer": fake.random_int(0, 3),
                    "time_spent_seconds": fake.random_int(10, 180),
                }
            elif answer_type == "true_false":
                answer = {
                    "question_id": fake.uuid4(),
                    "answer": fake.boolean(),
                    "time_spent_seconds": fake.random_int(5, 60),
                }
            elif answer_type == "short_answer":
                answer = {
                    "question_id": fake.uuid4(),
                    "answer": fake.text(max_nb_chars=200),
                    "time_spent_seconds": fake.random_int(30, 300),
                }
            else:  # essay
                answer = {
                    "question_id": fake.uuid4(),
                    "answer": fake.text(max_nb_chars=1000),
                    "time_spent_seconds": fake.random_int(300, 1800),
                }

            answers.append(answer)

        return answers

    # Grading
    score = factory.LazyFunction(lambda: fake.random_int(0, 100))
    points_earned = factory.LazyFunction(lambda: fake.random_int(0, 100))
    points_possible = 100
    grade = factory.LazyFunction(
        lambda: fake.random_element(["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"])
    )
    passed = factory.LazyFunction(lambda: fake.boolean(chance_of_getting_true=75))

    # Feedback
    feedback = factory.LazyFunction(lambda: fake.paragraph())

    # AI grading
    ai_graded = factory.LazyFunction(lambda: fake.boolean())
    ai_feedback = factory.LazyFunction(
        lambda: {
            "strengths": [fake.sentence() for _ in range(fake.random_int(2, 4))],
            "improvements": [fake.sentence() for _ in range(fake.random_int(1, 3))],
            "suggestions": [fake.sentence() for _ in range(fake.random_int(1, 3))],
        }
    )

    # Teacher review
    teacher_reviewed = factory.LazyFunction(lambda: fake.boolean())
    teacher_comments = factory.LazyFunction(lambda: fake.text(max_nb_chars=500) if fake.boolean() else None)