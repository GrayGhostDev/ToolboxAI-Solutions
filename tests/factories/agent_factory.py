"""AI Agent-related test data factories."""

import factory
from factory import fuzzy
from faker import Faker
from datetime import datetime, timezone, timedelta
import json
from .base_factory import DictFactory, AsyncMixin

fake = Faker()


class AgentTaskFactory(DictFactory, AsyncMixin):
    """Factory for AI agent tasks."""

    id = factory.LazyFunction(lambda: fake.uuid4())
    task_type = fuzzy.FuzzyChoice([
        "content_generation", "quiz_creation", "assessment_grading",
        "code_optimization", "security_validation", "performance_analysis"
    ])

    # Task details
    title = factory.LazyFunction(lambda: fake.catch_phrase())
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=500))
    priority = fuzzy.FuzzyChoice(["low", "medium", "high", "critical"])

    # Input parameters
    @factory.lazy_attribute
    def input_params(self):
        """Generate task-specific input parameters."""
        if self.task_type == "content_generation":
            return {
                "subject": fake.random_element(["Math", "Science", "English"]),
                "grade_level": fake.random_int(1, 12),
                "topic": fake.sentence(),
                "length": fake.random_element(["short", "medium", "long"]),
                "style": fake.random_element(["formal", "conversational", "interactive"]),
            }
        elif self.task_type == "quiz_creation":
            return {
                "num_questions": fake.random_int(5, 20),
                "difficulty": fake.random_element(["easy", "medium", "hard"]),
                "question_types": fake.random_elements(
                    ["multiple_choice", "true_false", "short_answer", "essay"],
                    length=fake.random_int(1, 4)
                ),
                "topic": fake.sentence(),
            }
        elif self.task_type == "code_optimization":
            return {
                "language": "luau",
                "optimization_goals": fake.random_elements(
                    ["performance", "memory", "readability", "security"],
                    length=fake.random_int(1, 3)
                ),
                "script_type": fake.random_element(["ServerScript", "LocalScript", "ModuleScript"]),
            }
        else:
            return {
                "param1": fake.word(),
                "param2": fake.random_int(1, 100),
                "param3": fake.boolean(),
            }

    # Execution details
    status = fuzzy.FuzzyChoice(["pending", "in_progress", "completed", "failed", "cancelled"])
    created_at = factory.LazyFunction(lambda: fake.date_time_this_week().isoformat())
    started_at = factory.LazyFunction(
        lambda: fake.date_time_this_week().isoformat() if fake.boolean() else None
    )
    completed_at = factory.LazyFunction(
        lambda: fake.date_time_this_week().isoformat() if fake.boolean() else None
    )

    # Agent assignment
    assigned_agent = factory.LazyFunction(
        lambda: fake.random_element(["ContentAgent", "QuizAgent", "OptimizationAgent", None])
    )
    agent_version = factory.LazyFunction(lambda: f"v{fake.random_int(1, 3)}.{fake.random_int(0, 9)}")

    # Execution metrics
    execution_time_ms = factory.LazyFunction(lambda: fake.random_int(100, 30000))
    tokens_used = factory.LazyFunction(lambda: fake.random_int(100, 10000))
    cost_estimate = factory.LazyFunction(lambda: round(fake.random.uniform(0.01, 1.0), 4))

    # Retry information
    retry_count = factory.LazyFunction(lambda: fake.random_int(0, 3))
    max_retries = 3

    # Error details (if failed)
    @factory.lazy_attribute
    def error_details(self):
        """Generate error details if task failed."""
        if self.status == "failed":
            return {
                "error_type": fake.random_element([
                    "TimeoutError", "ValidationError", "APIError",
                    "RateLimitError", "InsufficientContextError"
                ]),
                "error_message": fake.sentence(),
                "error_code": fake.random_element(["E001", "E002", "E003", "E004"]),
                "stack_trace": fake.text(max_nb_chars=500) if fake.boolean() else None,
            }
        return None

    # SPARC framework metadata
    sparc_metadata = factory.LazyFunction(
        lambda: {
            "specification": fake.paragraph(),
            "pseudocode": fake.text(max_nb_chars=300),
            "accuracy_check": fake.boolean(),
            "review_notes": fake.sentence() if fake.boolean() else None,
            "conclusion": fake.paragraph(),
        }
    )

    @classmethod
    def batch_create(cls, task_type: str, count: int = 5, **kwargs):
        """Create a batch of related tasks."""
        return [
            cls.create(
                task_type=task_type,
                priority=fake.random_element(["low", "medium", "high"]),
                **kwargs
            )
            for _ in range(count)
        ]


class AgentResponseFactory(DictFactory):
    """Factory for AI agent responses."""

    id = factory.LazyFunction(lambda: fake.uuid4())
    task_id = factory.LazyFunction(lambda: fake.uuid4())
    agent_name = fuzzy.FuzzyChoice([
        "ContentAgent", "QuizAgent", "OptimizationAgent",
        "SecurityAgent", "AssessmentAgent"
    ])

    # Response content
    @factory.lazy_attribute
    def content(self):
        """Generate response content based on agent type."""
        if "Content" in self.agent_name:
            return {
                "type": "educational_content",
                "title": fake.catch_phrase(),
                "body": fake.text(max_nb_chars=2000),
                "summary": fake.paragraph(),
                "keywords": fake.words(nb=10),
                "learning_objectives": [fake.sentence() for _ in range(5)],
            }
        elif "Quiz" in self.agent_name:
            return {
                "type": "quiz",
                "questions": [
                    {
                        "id": fake.uuid4(),
                        "question": fake.sentence().replace(".", "?"),
                        "options": [fake.sentence() for _ in range(4)],
                        "correct_answer": fake.random_int(0, 3),
                        "explanation": fake.paragraph(),
                    }
                    for _ in range(fake.random_int(5, 10))
                ],
                "total_points": fake.random_int(50, 100),
                "time_limit": fake.random_int(10, 60),
            }
        elif "Optimization" in self.agent_name:
            return {
                "type": "optimization_result",
                "original_metrics": {
                    "execution_time": fake.random_int(100, 1000),
                    "memory_usage": fake.random_int(1000, 10000),
                    "complexity": fake.random_element(["O(n)", "O(n²)", "O(log n)"]),
                },
                "optimized_metrics": {
                    "execution_time": fake.random_int(50, 500),
                    "memory_usage": fake.random_int(500, 5000),
                    "complexity": "O(n)",
                },
                "improvements": [fake.sentence() for _ in range(fake.random_int(3, 7))],
                "code_diff": fake.text(max_nb_chars=500),
            }
        else:
            return {
                "type": "generic",
                "result": fake.paragraph(),
                "metadata": {fake.word(): fake.word() for _ in range(3)},
            }

    # Response metadata
    confidence_score = factory.LazyFunction(lambda: round(fake.random.uniform(0.7, 1.0), 3))
    model_used = fuzzy.FuzzyChoice(["gpt-4", "gpt-3.5-turbo", "claude-3", "mock-llm"])

    # Processing details
    processing_time_ms = factory.LazyFunction(lambda: fake.random_int(100, 5000))
    tokens_input = factory.LazyFunction(lambda: fake.random_int(100, 2000))
    tokens_output = factory.LazyFunction(lambda: fake.random_int(100, 4000))

    # Quality metrics
    quality_score = factory.LazyFunction(lambda: round(fake.random.uniform(0.6, 1.0), 2))
    human_review_status = fuzzy.FuzzyChoice(["pending", "approved", "needs_revision", "rejected", None])
    human_feedback = factory.LazyFunction(
        lambda: fake.paragraph() if fake.boolean(chance_of_getting_true=30) else None
    )

    # Chain of thought
    reasoning_steps = factory.LazyFunction(
        lambda: [
            {
                "step": i + 1,
                "action": fake.sentence(),
                "reasoning": fake.paragraph(),
                "confidence": round(fake.random.uniform(0.5, 1.0), 2),
            }
            for i in range(fake.random_int(3, 8))
        ]
    )

    # Validation results
    validation = factory.LazyFunction(
        lambda: {
            "is_valid": fake.boolean(chance_of_getting_true=90),
            "checks_passed": fake.random_int(8, 10),
            "checks_failed": fake.random_int(0, 2),
            "warnings": [fake.sentence() for _ in range(fake.random_int(0, 3))],
        }
    )

    # Timestamps
    created_at = factory.LazyFunction(lambda: fake.date_time_this_week().isoformat())

    @classmethod
    def with_revisions(cls, num_revisions: int = 3, **kwargs):
        """Create response with revision history."""
        response = cls.create(**kwargs)
        response["revisions"] = [
            {
                "version": i + 1,
                "timestamp": fake.date_time_this_week().isoformat(),
                "changes": fake.paragraph(),
                "author": fake.random_element(["AI", "Human Reviewer"]),
            }
            for i in range(num_revisions)
        ]
        return response


class AgentConversationFactory(DictFactory):
    """Factory for agent conversation/chat histories."""

    id = factory.LazyFunction(lambda: fake.uuid4())
    session_id = factory.LazyFunction(lambda: fake.uuid4())
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    # Conversation metadata
    started_at = factory.LazyFunction(lambda: fake.date_time_this_week().isoformat())
    ended_at = factory.LazyFunction(
        lambda: (datetime.now(timezone.utc) + timedelta(minutes=fake.random_int(5, 60))).isoformat()
    )

    # Messages
    @factory.lazy_attribute
    def messages(self):
        """Generate conversation messages."""
        num_messages = fake.random_int(5, 20)
        messages = []

        for i in range(num_messages):
            role = "user" if i % 2 == 0 else "assistant"

            if role == "user":
                content = fake.random_element([
                    "Create a quiz about " + fake.word(),
                    "Explain " + fake.catch_phrase(),
                    "Generate content for " + fake.sentence(),
                    "Help me understand " + fake.word(),
                    fake.question(),
                ])
            else:
                content = fake.paragraph()

            messages.append({
                "id": fake.uuid4(),
                "role": role,
                "content": content,
                "timestamp": (
                    datetime.now(timezone.utc) + timedelta(minutes=i)
                ).isoformat(),
                "tokens": fake.random_int(10, 500),
            })

        return messages

    # Context
    context = factory.LazyFunction(
        lambda: {
            "subject": fake.random_element(["Math", "Science", "English", "History"]),
            "grade_level": fake.random_int(1, 12),
            "user_role": fake.random_element(["student", "teacher", "admin"]),
            "session_type": fake.random_element(["tutoring", "content_creation", "assessment"]),
        }
    )

    # Metrics
    total_tokens = factory.LazyFunction(lambda: fake.random_int(500, 10000))
    total_cost = factory.LazyFunction(lambda: round(fake.random.uniform(0.01, 5.0), 4))
    user_satisfaction = factory.LazyFunction(lambda: fake.random_int(1, 5) if fake.boolean() else None)

    # Tags and categorization
    tags = factory.LazyFunction(
        lambda: fake.words(nb=fake.random_int(3, 8))
    )

    category = fuzzy.FuzzyChoice([
        "homework_help", "content_creation", "quiz_generation",
        "code_review", "general_inquiry"
    ])