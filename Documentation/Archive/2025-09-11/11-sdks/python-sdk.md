# Python SDK

Official Python SDK for ToolBoxAI-Solutions. Build powerful educational applications, automate content generation, and analyze learning data with our comprehensive Python library.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Authentication](#authentication)
4. [Configuration](#configuration)
5. [API Reference](#api-reference)
6. [Type Hints](#type-hints)
7. [Async Support](#async-support)
8. [Data Analysis](#data-analysis)
9. [Error Handling](#error-handling)
10. [Advanced Features](#advanced-features)
11. [Examples](#examples)
12. [Troubleshooting](#troubleshooting)

## Installation

### pip
```bash
pip install toolboxai-sdk
```

### Poetry
```bash
poetry add toolboxai-sdk
```

### Conda
```bash
conda install -c toolboxai toolboxai-sdk
```

### Development Installation
```bash
git clone https://github.com/toolboxai/python-sdk.git
cd python-sdk
pip install -e .
```

### Requirements
- Python 3.8 or higher
- Optional: pandas for data analysis features
- Optional: aiohttp for async support

## Quick Start

### Basic Usage
```python
from toolboxai import ToolBoxAI

# Initialize client
client = ToolBoxAI(api_key="your-api-key-here")

# Get current user
user = client.users.me()
print(f"Logged in as: {user.name}")

# List lessons
lessons = client.lessons.list(grade=5, subject="math")
for lesson in lessons:
    print(f"- {lesson.title}")

# Create a quiz
quiz = client.quizzes.create(
    title="Math Quiz",
    questions=[
        {
            "type": "multiple_choice",
            "question": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "correct_answer": 1
        }
    ]
)
print(f"Created quiz: {quiz.id}")
```

## Authentication

### API Key Authentication
```python
from toolboxai import ToolBoxAI

client = ToolBoxAI(api_key="your-api-key-here")
```

### OAuth2 Authentication
```python
from toolboxai import ToolBoxAI, OAuth2Flow

# Initialize OAuth flow
oauth = OAuth2Flow(
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="https://yourapp.com/callback"
)

# Get authorization URL
auth_url = oauth.get_authorization_url(
    scope=["lessons:read", "lessons:write"],
    state="random-state-string"
)

# Handle callback
tokens = oauth.handle_callback(callback_url)

# Initialize client with tokens
client = ToolBoxAI(access_token=tokens.access_token)
```

### Environment Variables
```python
import os
from toolboxai import ToolBoxAI

# Automatically reads TOOLBOXAI_API_KEY environment variable
client = ToolBoxAI()

# Or specify different env var
client = ToolBoxAI(api_key=os.getenv("MY_API_KEY"))
```

### Token Management
```python
# Login with credentials
tokens = client.auth.login(
    email="user@example.com",
    password="password123"
)

# Set tokens
client.set_access_token(tokens.access_token)
client.set_refresh_token(tokens.refresh_token)

# Refresh token
new_tokens = client.auth.refresh_token()
client.set_access_token(new_tokens.access_token)

# Logout
client.auth.logout()
```

## Configuration

### Client Configuration
```python
from toolboxai import ToolBoxAI, Config

config = Config(
    api_key="your-api-key",
    environment="production",  # or "sandbox", "development"
    base_url="https://api.toolboxai.com",
    timeout=30,  # seconds
    max_retries=3,
    retry_delay=1.0,  # seconds
    
    # Connection pooling
    pool_connections=10,
    pool_maxsize=10,
    
    # Proxy settings
    proxy="http://proxy.example.com:8080",
    
    # SSL verification
    verify_ssl=True,
    
    # Custom headers
    headers={
        "X-Custom-Header": "value"
    }
)

client = ToolBoxAI(config=config)
```

### Logging Configuration
```python
import logging
from toolboxai import ToolBoxAI

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

client = ToolBoxAI(api_key="your-key", debug=True)

# Custom logger
logger = logging.getLogger("my_app")
client = ToolBoxAI(api_key="your-key", logger=logger)
```

## API Reference

### Users

```python
from toolboxai import ToolBoxAI
from toolboxai.models import User, UserUpdate

client = ToolBoxAI(api_key="your-key")

# Get current user
me: User = client.users.me()

# Get user by ID
user: User = client.users.get("user-id")

# Update user
update_data = UserUpdate(
    name="New Name",
    preferences={"theme": "dark"}
)
updated: User = client.users.update("user-id", update_data)

# List users (admin only)
users = client.users.list(
    role="student",
    page=1,
    per_page=20
)

# Iterate through all users
for user in client.users.iter_all(role="teacher"):
    print(user.name)

# Delete user (admin only)
client.users.delete("user-id")
```

### Lessons

```python
from toolboxai.models import Lesson, LessonCreate

# Create lesson
lesson_data = LessonCreate(
    title="Introduction to Algebra",
    description="Learn the basics of algebra",
    grade_level=7,
    subject="mathematics",
    content={
        "sections": [...]
    }
)
lesson: Lesson = client.lessons.create(lesson_data)

# Get lesson
lesson = client.lessons.get("lesson-id")

# Update lesson
lesson.title = "Updated Title"
updated = client.lessons.update(lesson)

# List lessons with filters
lessons = client.lessons.list(
    subject="science",
    grade_level=5,
    search="photosynthesis",
    sort_by="popularity",
    order="desc"
)

# Delete lesson
client.lessons.delete("lesson-id")

# Deploy to Roblox
deployment = client.lessons.deploy_to_roblox(
    lesson_id="lesson-id",
    environment_type="classroom",
    max_players=30
)

# Batch operations
lessons = client.lessons.batch_create([
    LessonCreate(title="Lesson 1", ...),
    LessonCreate(title="Lesson 2", ...),
])
```

### Quizzes

```python
from toolboxai.models import Quiz, Question, QuizAttempt

# Create quiz
quiz = client.quizzes.create(
    title="Math Quiz",
    lesson_id="lesson-id",
    questions=[
        Question(
            type="multiple_choice",
            question="What is 2 + 2?",
            options=["3", "4", "5", "6"],
            correct_answer=1,
            points=10
        )
    ],
    time_limit=600,  # 10 minutes
    passing_score=70
)

# Get quiz
quiz = client.quizzes.get("quiz-id")

# Submit quiz attempt
attempt = client.quizzes.submit(
    quiz_id="quiz-id",
    answers=[
        {"question_id": "q1", "answer": 1},
        {"question_id": "q2", "answer": "Paris"}
    ]
)

# Get results
results = client.quizzes.get_results("attempt-id")
print(f"Score: {results.score}%")

# Get quiz analytics
analytics = client.quizzes.get_analytics("quiz-id")
print(f"Average score: {analytics.average_score}")
print(f"Pass rate: {analytics.pass_rate}%")
```

### Progress Tracking

```python
from toolboxai.models import ProgressEvent, ProgressReport

# Track progress event
client.progress.track(
    user_id="user-id",
    event=ProgressEvent(
        type="lesson_completed",
        lesson_id="lesson-id",
        data={
            "time_spent": 1200,  # seconds
            "score": 95
        }
    )
)

# Get user progress
progress = client.progress.get(
    user_id="user-id",
    course_id="course-id"
)

# Get detailed analytics
analytics = client.progress.get_analytics(
    user_id="user-id",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Generate report
report = client.progress.generate_report(
    user_id="user-id",
    report_type="monthly",
    format="pdf"
)

# Save report to file
with open("report.pdf", "wb") as f:
    f.write(report.content)
```

### Gamification

```python
from toolboxai.models import Achievement, Quest, LeaderboardEntry

# Award XP
client.gamification.award_xp(
    user_id="user-id",
    amount=100,
    reason="Completed lesson"
)

# Get player profile
profile = client.gamification.get_profile("user-id")
print(f"Level: {profile.level}")
print(f"Total XP: {profile.total_xp}")

# Unlock achievement
achievement = client.gamification.unlock_achievement(
    user_id="user-id",
    achievement_id="first-lesson"
)

# Get leaderboard
leaderboard = client.gamification.get_leaderboard(
    type="weekly",
    limit=10
)
for entry in leaderboard:
    print(f"{entry.rank}. {entry.username} - {entry.score}")

# Create quest
quest = client.gamification.create_quest(
    title="Master Mathematics",
    description="Complete all math lessons",
    objectives=[...],
    rewards={
        "xp": 500,
        "badges": ["math-master"]
    }
)
```

### Content Generation (AI)

```python
from toolboxai.models import LessonPrompt, QuizPrompt

# Generate lesson from prompt
prompt = LessonPrompt(
    text="Create a lesson about photosynthesis for 5th graders",
    grade_level=5,
    duration=45,  # minutes
    include_quiz=True,
    include_activities=True
)
generated_lesson = client.ai.generate_lesson(prompt)

# Generate quiz from lesson
quiz = client.ai.generate_quiz(
    lesson_id="lesson-id",
    question_count=10,
    difficulty="medium",
    question_types=["multiple_choice", "true_false"]
)

# Generate Roblox environment
environment = client.ai.generate_environment(
    lesson_id="lesson-id",
    theme="space",
    interactive_elements=["npcs", "puzzles", "collectibles"],
    difficulty="easy"
)

# Validate content
validation = client.ai.validate_content(
    content=lesson_content,
    checks=["age_appropriate", "factual_accuracy", "bias", "readability"]
)
if validation.passed:
    print("Content is valid")
else:
    print(f"Issues found: {validation.issues}")
```

### LMS Integration

```python
# Canvas integration
client.lms.canvas.configure(
    api_url="https://your-school.instructure.com",
    api_key="canvas-api-key"
)

canvas_sync = client.lms.canvas.sync_course(
    toolbox_course_id="course-id",
    canvas_course_id="canvas-course-id",
    sync_options={
        "grades": True,
        "assignments": True,
        "students": True
    }
)

# Google Classroom integration
classroom_course = client.lms.google_classroom.import_course(
    classroom_id="classroom-id",
    import_students=True,
    import_assignments=True
)

# Export grades to LMS
export_result = client.lms.export_grades(
    course_id="course-id",
    lms_type="schoology",
    format="csv"
)
```

## Type Hints

### Using Type Hints
```python
from typing import List, Optional, Dict, Any
from toolboxai import ToolBoxAI
from toolboxai.models import Lesson, Quiz, User

def get_student_lessons(
    client: ToolBoxAI,
    student_id: str,
    subject: Optional[str] = None
) -> List[Lesson]:
    """Get all lessons for a student."""
    user: User = client.users.get(student_id)
    
    filters: Dict[str, Any] = {"grade_level": user.grade_level}
    if subject:
        filters["subject"] = subject
    
    lessons: List[Lesson] = client.lessons.list(**filters)
    return lessons

# Type checking with mypy
# mypy your_script.py
```

### Custom Types
```python
from dataclasses import dataclass
from typing import Protocol
from toolboxai.models import BaseModel

@dataclass
class CustomLesson(BaseModel):
    """Custom lesson model with additional fields."""
    title: str
    school_id: str
    district_id: str
    custom_metadata: Dict[str, Any]

# Protocol for type checking
class LessonRepository(Protocol):
    def get(self, lesson_id: str) -> Lesson: ...
    def create(self, lesson: Lesson) -> Lesson: ...
    def update(self, lesson: Lesson) -> Lesson: ...
    def delete(self, lesson_id: str) -> None: ...
```

## Async Support

### Async Client
```python
import asyncio
from toolboxai import AsyncToolBoxAI

async def main():
    # Initialize async client
    async with AsyncToolBoxAI(api_key="your-key") as client:
        # Concurrent requests
        lessons_task = client.lessons.list(grade=5)
        quizzes_task = client.quizzes.list()
        
        lessons, quizzes = await asyncio.gather(
            lessons_task,
            quizzes_task
        )
        
        print(f"Found {len(lessons)} lessons and {len(quizzes)} quizzes")
        
        # Async iteration
        async for user in client.users.iter_all():
            print(user.name)

# Run async function
asyncio.run(main())
```

### Async Context Manager
```python
async def process_lessons():
    async with AsyncToolBoxAI(api_key="your-key") as client:
        # Client is automatically closed after the block
        lessons = await client.lessons.list()
        
        # Process lessons concurrently
        tasks = [
            process_lesson(client, lesson)
            for lesson in lessons
        ]
        results = await asyncio.gather(*tasks)
        return results

async def process_lesson(client: AsyncToolBoxAI, lesson: Lesson):
    # Generate quiz for lesson
    quiz = await client.ai.generate_quiz(lesson_id=lesson.id)
    
    # Deploy to Roblox
    deployment = await client.lessons.deploy_to_roblox(lesson.id)
    
    return {"lesson": lesson, "quiz": quiz, "deployment": deployment}
```

## Data Analysis

### Pandas Integration
```python
import pandas as pd
from toolboxai import ToolBoxAI

client = ToolBoxAI(api_key="your-key")

# Get data as DataFrame
df = client.analytics.get_progress_dataframe(
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Analyze data
print(df.describe())
print(df.groupby("subject")["score"].mean())

# Export to CSV
df.to_csv("progress_report.csv", index=False)

# Advanced analysis
import matplotlib.pyplot as plt

# Plot progress over time
df["date"] = pd.to_datetime(df["timestamp"])
daily_progress = df.groupby(df["date"].dt.date)["score"].mean()
daily_progress.plot(kind="line", title="Average Daily Score")
plt.show()

# Correlation analysis
correlation = df[["time_spent", "score", "attempts"]].corr()
print(correlation)
```

### Batch Data Processing
```python
from toolboxai.utils import BatchProcessor

# Process large datasets in batches
processor = BatchProcessor(client, batch_size=100)

# Process all students
def process_student(student):
    progress = client.progress.get(user_id=student.id)
    return {
        "student_id": student.id,
        "average_score": progress.average_score,
        "completion_rate": progress.completion_rate
    }

results = processor.process_all(
    client.users.iter_all(role="student"),
    process_student,
    max_workers=10  # Parallel processing
)

# Convert to DataFrame
df = pd.DataFrame(results)
```

## Error Handling

### Exception Types
```python
from toolboxai.exceptions import (
    ToolBoxAIError,
    ValidationError,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    NotFoundError
)

try:
    lesson = client.lessons.get("lesson-id")
except NotFoundError:
    print("Lesson not found")
except ValidationError as e:
    print(f"Validation error: {e.errors}")
except AuthenticationError:
    print("Authentication failed")
    # Refresh token or re-authenticate
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
    time.sleep(e.retry_after)
    # Retry request
except NetworkError as e:
    print(f"Network error: {e}")
    # Implement retry logic
except ToolBoxAIError as e:
    print(f"API error: {e.code} - {e.message}")
```

### Retry Logic
```python
from toolboxai.utils import retry
import time

@retry(max_attempts=3, delay=1.0, backoff=2.0)
def create_lesson_with_retry(client, lesson_data):
    """Create lesson with automatic retry on failure."""
    return client.lessons.create(lesson_data)

# Custom retry logic
def robust_api_call(func, *args, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except RateLimitError as e:
            if attempt < max_retries - 1:
                time.sleep(e.retry_after)
                continue
            raise
        except NetworkError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
```

## Advanced Features

### Context Managers
```python
from toolboxai import ToolBoxAI

# Automatic resource cleanup
with ToolBoxAI(api_key="your-key") as client:
    lessons = client.lessons.list()
    # Client is automatically closed after the block

# Batch operations with context manager
with client.batch() as batch:
    batch.create_lesson(lesson1_data)
    batch.create_lesson(lesson2_data)
    batch.create_quiz(quiz_data)
    # All operations are executed when exiting the context
```

### Generators and Iterators
```python
# Memory-efficient iteration over large datasets
def process_all_students(client):
    """Process students without loading all into memory."""
    for student in client.users.iter_all(role="student"):
        # Process one student at a time
        progress = client.progress.get(user_id=student.id)
        yield {
            "student": student,
            "progress": progress
        }

# Use generator
for data in process_all_students(client):
    print(f"{data['student'].name}: {data['progress'].score}%")

# Generator with filtering
active_students = (
    student for student in client.users.iter_all()
    if student.last_login_days <= 7
)
```

### Caching
```python
from toolboxai import ToolBoxAI
from toolboxai.cache import MemoryCache, RedisCache
import redis

# Memory cache
client = ToolBoxAI(
    api_key="your-key",
    cache=MemoryCache(ttl=300)  # 5 minutes TTL
)

# Redis cache
redis_client = redis.Redis(host="localhost", port=6379, db=0)
client = ToolBoxAI(
    api_key="your-key",
    cache=RedisCache(redis_client, ttl=3600)  # 1 hour TTL
)

# Decorator for caching
from functools import lru_cache

@lru_cache(maxsize=128)
def get_lesson_cached(lesson_id: str) -> Lesson:
    return client.lessons.get(lesson_id)
```

### Webhooks
```python
from flask import Flask, request
from toolboxai.webhooks import WebhookHandler

app = Flask(__name__)
webhook_handler = WebhookHandler(secret="your-webhook-secret")

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    # Verify signature
    signature = request.headers.get("X-ToolBoxAI-Signature")
    if not webhook_handler.verify_signature(request.data, signature):
        return "Invalid signature", 401
    
    # Process event
    event = request.json
    if event["type"] == "lesson.created":
        handle_lesson_created(event["data"])
    elif event["type"] == "quiz.submitted":
        handle_quiz_submitted(event["data"])
    
    return "OK", 200

def handle_lesson_created(lesson_data):
    print(f"New lesson created: {lesson_data['title']}")

def handle_quiz_submitted(quiz_data):
    print(f"Quiz submitted: {quiz_data['score']}%")
```

### CLI Tool
```python
import click
from toolboxai import ToolBoxAI

@click.group()
@click.option("--api-key", envvar="TOOLBOXAI_API_KEY")
@click.pass_context
def cli(ctx, api_key):
    """ToolBoxAI command line interface."""
    ctx.obj = ToolBoxAI(api_key=api_key)

@cli.command()
@click.argument("grade", type=int)
@click.argument("subject")
@click.pass_obj
def list_lessons(client, grade, subject):
    """List lessons by grade and subject."""
    lessons = client.lessons.list(grade=grade, subject=subject)
    for lesson in lessons:
        click.echo(f"- {lesson.title} (ID: {lesson.id})")

@cli.command()
@click.argument("title")
@click.option("--grade", type=int, default=5)
@click.pass_obj
def create_lesson(client, title, grade):
    """Create a new lesson."""
    lesson = client.lessons.create(
        title=title,
        grade_level=grade
    )
    click.echo(f"Created lesson: {lesson.id}")

if __name__ == "__main__":
    cli()
```

## Examples

### Complete Application
```python
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from toolboxai import AsyncToolBoxAI
from toolboxai.models import LessonCreate, QuizCreate

class EducationPlatform:
    def __init__(self, api_key: str):
        self.client = AsyncToolBoxAI(api_key=api_key)
    
    async def create_weekly_curriculum(
        self, 
        grade: int, 
        subject: str, 
        week_number: int
    ):
        """Create a week's worth of lessons and quizzes."""
        curriculum = []
        
        for day in range(5):  # Monday to Friday
            # Generate lesson
            lesson_prompt = f"""
            Create a {subject} lesson for grade {grade}, 
            week {week_number}, day {day + 1}
            """
            
            lesson = await self.client.ai.generate_lesson(
                prompt=lesson_prompt,
                grade_level=grade,
                duration=45
            )
            
            # Generate quiz
            quiz = await self.client.ai.generate_quiz(
                lesson_id=lesson.id,
                question_count=5
            )
            
            # Deploy to Roblox
            environment = await self.client.lessons.deploy_to_roblox(
                lesson_id=lesson.id
            )
            
            curriculum.append({
                "day": day + 1,
                "lesson": lesson,
                "quiz": quiz,
                "environment": environment
            })
        
        return curriculum
    
    async def analyze_student_performance(
        self, 
        student_id: str, 
        days: int = 30
    ):
        """Analyze student performance over time."""
        # Get progress data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        progress = await self.client.progress.get_analytics(
            user_id=student_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(progress.daily_metrics)
        
        # Calculate metrics
        metrics = {
            "average_score": df["score"].mean(),
            "improvement_rate": df["score"].pct_change().mean(),
            "consistency": df["score"].std(),
            "best_subject": df.groupby("subject")["score"].mean().idxmax(),
            "weak_areas": df[df["score"] < 70]["topic"].unique().tolist(),
            "study_time": df["time_spent"].sum() / 60,  # Convert to hours
            "engagement_score": self._calculate_engagement(df)
        }
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            student_id, 
            metrics
        )
        
        return {
            "metrics": metrics,
            "recommendations": recommendations,
            "chart_data": df.to_dict("records")
        }
    
    def _calculate_engagement(self, df: pd.DataFrame) -> float:
        """Calculate engagement score based on various factors."""
        login_frequency = len(df) / df["date"].nunique()
        completion_rate = df["completed"].mean()
        interaction_rate = df["interactions"].mean() / df["time_spent"].mean()
        
        engagement = (
            login_frequency * 0.3 + 
            completion_rate * 0.4 + 
            interaction_rate * 0.3
        ) * 100
        
        return min(engagement, 100)
    
    async def _generate_recommendations(
        self, 
        student_id: str, 
        metrics: dict
    ) -> list:
        """Generate personalized recommendations."""
        recommendations = []
        
        if metrics["average_score"] < 70:
            recommendations.append({
                "type": "remedial",
                "message": "Consider additional practice in weak areas",
                "resources": await self._get_remedial_resources(
                    metrics["weak_areas"]
                )
            })
        
        if metrics["consistency"] > 15:
            recommendations.append({
                "type": "consistency",
                "message": "Work on maintaining consistent performance",
                "tips": [
                    "Set regular study schedule",
                    "Take breaks to avoid fatigue",
                    "Review material regularly"
                ]
            })
        
        return recommendations
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close()

# Usage
async def main():
    async with EducationPlatform(api_key="your-key") as platform:
        # Create curriculum
        curriculum = await platform.create_weekly_curriculum(
            grade=5,
            subject="science",
            week_number=1
        )
        
        # Analyze performance
        analysis = await platform.analyze_student_performance(
            student_id="student-123",
            days=30
        )
        
        print(f"Average Score: {analysis['metrics']['average_score']:.1f}%")
        print(f"Best Subject: {analysis['metrics']['best_subject']}")
        print(f"Study Time: {analysis['metrics']['study_time']:.1f} hours")

if __name__ == "__main__":
    asyncio.run(main())
```

## Troubleshooting

### Common Issues

#### SSL Certificate Errors
```python
# Disable SSL verification (not recommended for production)
client = ToolBoxAI(api_key="your-key", verify_ssl=False)

# Custom CA bundle
client = ToolBoxAI(
    api_key="your-key",
    verify_ssl="/path/to/ca-bundle.crt"
)
```

#### Proxy Configuration
```python
# HTTP proxy
client = ToolBoxAI(
    api_key="your-key",
    proxy="http://proxy.example.com:8080"
)

# SOCKS proxy
client = ToolBoxAI(
    api_key="your-key",
    proxy="socks5://proxy.example.com:1080"
)

# Proxy with authentication
client = ToolBoxAI(
    api_key="your-key",
    proxy="http://user:pass@proxy.example.com:8080"
)
```

#### Memory Issues with Large Datasets
```python
# Use generators instead of lists
def process_large_dataset(client):
    # Bad - loads all into memory
    # all_users = client.users.list(limit=10000)
    
    # Good - processes one at a time
    for user in client.users.iter_all():
        process_user(user)
        
# Use chunking for batch operations
from toolboxai.utils import chunk

users = client.users.iter_all()
for user_chunk in chunk(users, size=100):
    process_batch(user_chunk)
```

### Debug Mode
```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

client = ToolBoxAI(api_key="your-key", debug=True)

# Log all requests and responses
client.set_debug_callback(lambda req, resp: 
    print(f"Request: {req}\nResponse: {resp}")
)
```

### Performance Profiling
```python
import cProfile
import pstats
from io import StringIO

def profile_code():
    """Profile API calls for performance optimization."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Code to profile
    client = ToolBoxAI(api_key="your-key")
    lessons = client.lessons.list(limit=100)
    for lesson in lessons:
        client.quizzes.list(lesson_id=lesson.id)
    
    profiler.disable()
    
    # Print stats
    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")
    stats.print_stats(10)
    print(stream.getvalue())
```

## Migration

### Migrating from v1 to v2
```python
# v1 (deprecated)
from toolboxai import Client
client = Client(api_key)
lessons = client.get_lessons()

# v2 (current)
from toolboxai import ToolBoxAI
client = ToolBoxAI(api_key=api_key)
lessons = client.lessons.list()
```

See [Migration Guide](https://github.com/toolboxai/python-sdk/blob/main/MIGRATION.md) for detailed instructions.

## Testing

### Unit Testing
```python
import unittest
from unittest.mock import Mock, patch
from toolboxai import ToolBoxAI

class TestLessonOperations(unittest.TestCase):
    def setUp(self):
        self.client = ToolBoxAI(api_key="test-key")
    
    @patch("toolboxai.lessons.requests.get")
    def test_get_lesson(self, mock_get):
        mock_get.return_value.json.return_value = {
            "id": "lesson-123",
            "title": "Test Lesson"
        }
        
        lesson = self.client.lessons.get("lesson-123")
        
        self.assertEqual(lesson.id, "lesson-123")
        self.assertEqual(lesson.title, "Test Lesson")
        mock_get.assert_called_once()

if __name__ == "__main__":
    unittest.main()
```

### Integration Testing
```python
import pytest
from toolboxai import ToolBoxAI

@pytest.fixture
def client():
    return ToolBoxAI(api_key="test-key")

@pytest.mark.integration
def test_full_lesson_lifecycle(client):
    # Create lesson
    lesson = client.lessons.create(
        title="Test Lesson",
        grade_level=5
    )
    assert lesson.id is not None
    
    # Update lesson
    lesson.title = "Updated Test Lesson"
    updated = client.lessons.update(lesson)
    assert updated.title == "Updated Test Lesson"
    
    # Delete lesson
    client.lessons.delete(lesson.id)
    
    # Verify deletion
    with pytest.raises(NotFoundError):
        client.lessons.get(lesson.id)
```

## Support

- **Documentation**: [docs.toolboxai.com](https://docs.toolboxai.com)
- **GitHub**: [github.com/toolboxai/python-sdk](https://github.com/toolboxai/python-sdk)
- **PyPI**: [pypi.org/project/toolboxai-sdk](https://pypi.org/project/toolboxai-sdk)
- **Discord**: [discord.gg/toolboxai](https://discord.gg/toolboxai)
- **Email**: python-sdk@toolboxai.com

---

*SDK Version: 2.0.0 | API Version: v1 | Python: 3.8+ | Last Updated: September 2025*