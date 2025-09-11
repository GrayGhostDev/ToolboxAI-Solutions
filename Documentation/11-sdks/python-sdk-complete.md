# ToolboxAI Python SDK - Complete Documentation

## Installation

```bash
pip install toolboxai-sdk
```

Or install from source:

```bash
git clone https://github.com/toolboxai/python-sdk.git
cd python-sdk
pip install -e .
```

## Quick Start

```python
from toolboxai import ToolboxAI

# Initialize client
client = ToolboxAI(
    api_key="your-api-key",
    base_url="https://api.toolboxai.com"  # Optional
)

# Authenticate
await client.auth.login("teacher@example.com", "password")

# Generate content
content = await client.content.generate(
    subject="Mathematics",
    grade_level=7,
    learning_objectives=["Understand fractions"]
)

print(f"Generated: {content.title}")
```

## Complete SDK Reference

### Client Initialization

```python
from toolboxai import ToolboxAI, Config
from toolboxai.types import Environment

# Basic initialization
client = ToolboxAI(api_key="your-api-key")

# Advanced configuration
config = Config(
    api_key="your-api-key",
    base_url="https://api.toolboxai.com",
    ws_url="wss://ws.toolboxai.com",
    environment=Environment.PRODUCTION,
    timeout=30,  # seconds
    max_retries=3,
    retry_delay=1,  # seconds
    enable_logging=True,
    log_level="INFO"
)

client = ToolboxAI(config=config)
```

### Authentication Module

```python
from toolboxai.auth import AuthManager, TokenStorage
from toolboxai.exceptions import AuthenticationError

class CustomTokenStorage(TokenStorage):
    """Custom token storage implementation"""
    
    async def save_tokens(self, access_token: str, refresh_token: str):
        # Save to secure storage
        pass
    
    async def load_tokens(self) -> tuple[str, str]:
        # Load from storage
        return access_token, refresh_token
    
    async def clear_tokens(self):
        # Clear stored tokens
        pass

# Use custom storage
auth = AuthManager(
    base_url="https://api.toolboxai.com",
    token_storage=CustomTokenStorage()
)

# Login methods
try:
    # Email/password login
    user = await auth.login("user@example.com", "password")
    
    # OAuth login
    user = await auth.oauth_login(provider="google", token="oauth-token")
    
    # API key authentication
    auth.set_api_key("your-api-key")
    
except AuthenticationError as e:
    print(f"Authentication failed: {e}")

# Token management
await auth.refresh_token()
is_valid = await auth.validate_token()
await auth.logout()

# Get current user
user = await auth.get_current_user()
print(f"Logged in as: {user.name} ({user.role})")
```

### Content Generation Module

```python
from toolboxai.content import ContentGenerator
from toolboxai.types import (
    ContentType, Subject, Difficulty, 
    EnvironmentType, Language
)

generator = client.content

# Generate lesson with all options
lesson = await generator.generate_lesson(
    subject=Subject.MATHEMATICS,
    grade_level=7,
    learning_objectives=[
        "Understand fractions",
        "Add and subtract fractions",
        "Convert fractions to decimals"
    ],
    content_type=ContentType.LESSON,
    environment_type=EnvironmentType.CLASSROOM,
    difficulty=Difficulty.MEDIUM,
    include_quiz=True,
    include_activities=True,
    include_roblox=True,
    language=Language.ENGLISH,
    duration_minutes=45,
    custom_instructions="Focus on visual learning"
)

# Access generated content
print(f"Title: {lesson.title}")
print(f"Content: {lesson.content.main_content}")
print(f"Activities: {lesson.content.activities}")
print(f"Quiz: {lesson.quiz}")
print(f"Roblox Scripts: {lesson.roblox_integration}")

# Generate quiz only
quiz = await generator.generate_quiz(
    subject=Subject.SCIENCE,
    grade_level=8,
    num_questions=10,
    difficulty=Difficulty.HARD,
    question_types=["multiple_choice", "true_false"],
    time_limit_seconds=600
)

# Generate activity
activity = await generator.generate_activity(
    subject=Subject.HISTORY,
    grade_level=6,
    activity_type="interactive_timeline",
    topic="Ancient Egypt"
)

# Batch generation
contents = await generator.generate_batch([
    {
        "subject": "Math",
        "grade_level": 5,
        "content_type": "lesson"
    },
    {
        "subject": "Science", 
        "grade_level": 5,
        "content_type": "quiz"
    }
])
```

### Quiz Management Module

```python
from toolboxai.quiz import QuizManager, QuizBuilder
from toolboxai.types import QuestionType, QuizDifficulty

quiz_manager = client.quiz

# Build quiz programmatically
builder = QuizBuilder()
builder.set_title("Math Fundamentals Quiz")
builder.set_subject(Subject.MATHEMATICS)
builder.set_grade_level(7)
builder.set_difficulty(QuizDifficulty.MEDIUM)
builder.set_time_limit(minutes=30)

# Add questions
builder.add_question(
    text="What is 15 + 27?",
    type=QuestionType.MULTIPLE_CHOICE,
    options=["42", "41", "43", "40"],
    correct_answer="42",
    points=1,
    explanation="15 + 27 = 42",
    media={
        "image_url": "https://example.com/math.png"
    }
)

builder.add_question(
    text="Is 7 a prime number?",
    type=QuestionType.TRUE_FALSE,
    correct_answer=True,
    points=1
)

# Create quiz
quiz = await quiz_manager.create(builder.build())
print(f"Quiz created: {quiz.id}")

# Get quiz
quiz = await quiz_manager.get(quiz_id="quiz-123")

# List quizzes with filters
quizzes = await quiz_manager.list(
    subject=Subject.MATHEMATICS,
    grade_level=7,
    difficulty=QuizDifficulty.MEDIUM,
    created_after="2024-01-01",
    limit=10
)

# Submit quiz answers
result = await quiz_manager.submit(
    quiz_id=quiz.id,
    answers=[
        {"question_id": "q1", "answer": "42"},
        {"question_id": "q2", "answer": "True"}
    ],
    time_taken_seconds=300
)

print(f"Score: {result.score}/{result.total_points} ({result.percentage}%)")
print(f"Passed: {result.passed}")
print(f"XP Earned: {result.xp_earned}")

# Get quiz results
results = await quiz_manager.get_results(
    quiz_id=quiz.id,
    user_id="user-123"  # Optional
)

# Quiz analytics
analytics = await quiz_manager.get_analytics(
    quiz_id=quiz.id,
    include_question_stats=True
)
print(f"Average score: {analytics.average_score}")
print(f"Completion rate: {analytics.completion_rate}")
```

### Progress Tracking Module

```python
from toolboxai.progress import ProgressTracker
from toolboxai.types import MetricType, TimeRange

tracker = client.progress

# Get user progress
progress = await tracker.get_user_progress(
    user_id="user-123",  # Optional, defaults to current user
    course_id="course-456"  # Optional
)

print(f"Overall progress: {progress.overall_progress}%")
print(f"Lessons completed: {progress.lessons_completed}/{progress.total_lessons}")
print(f"Average quiz score: {progress.average_quiz_score}%")
print(f"Time spent: {progress.time_spent_minutes} minutes")

# Get course progress
course_progress = await tracker.get_course_progress(
    course_id="course-456"
)

for user_progress in course_progress.user_progress:
    print(f"{user_progress.user_name}: {user_progress.percentage}%")

# Update progress
await tracker.update_progress(
    course_id="course-456",
    lesson_id="lesson-789",
    completed=True,
    score=85,
    time_spent_seconds=1800
)

# Get achievements
achievements = await tracker.get_achievements(
    user_id="user-123"
)

for achievement in achievements:
    print(f"🏆 {achievement.name}: {achievement.description}")
    print(f"   Earned: {achievement.earned_at}")

# Get leaderboard
leaderboard = await tracker.get_leaderboard(
    course_id="course-456",
    time_range=TimeRange.WEEKLY,
    limit=10
)

for rank, entry in enumerate(leaderboard.entries, 1):
    print(f"{rank}. {entry.user_name}: {entry.score} points")
```

### Analytics Module

```python
from toolboxai.analytics import Analytics
from toolboxai.types import DateRange, GroupBy
from datetime import datetime, timedelta

analytics = client.analytics

# Get dashboard data
dashboard = await analytics.get_dashboard(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    metrics=[
        MetricType.ENGAGEMENT,
        MetricType.PERFORMANCE,
        MetricType.PROGRESS
    ]
)

print(f"Total users: {dashboard.summary.total_users}")
print(f"Active users: {dashboard.summary.active_users}")
print(f"Content generated: {dashboard.summary.content_generated}")

# Get detailed metrics
metrics = await analytics.get_metrics(
    metric_type=MetricType.ENGAGEMENT,
    group_by=GroupBy.DAY,
    filters={
        "grade_level": 7,
        "subject": "Mathematics"
    }
)

for data_point in metrics.data:
    print(f"{data_point.date}: {data_point.value}")

# Custom analytics query
custom_data = await analytics.query(
    query="""
    SELECT 
        subject,
        AVG(score) as avg_score,
        COUNT(*) as total_quizzes
    FROM quiz_results
    WHERE created_at > :start_date
    GROUP BY subject
    """,
    params={
        "start_date": datetime.now() - timedelta(days=7)
    }
)

# Export analytics
report = await analytics.export_report(
    report_type="weekly_summary",
    format="pdf",
    email="admin@school.edu"
)
print(f"Report exported: {report.url}")
```

### WebSocket Real-time Module

```python
from toolboxai.websocket import WebSocketClient, MessageHandler
from toolboxai.types import WebSocketEvent
import asyncio

# Create WebSocket client
ws = client.websocket

# Define event handlers
class MyHandler(MessageHandler):
    async def on_content_update(self, data):
        print(f"Content updated: {data}")
    
    async def on_quiz_result(self, data):
        print(f"Quiz completed: Score {data['score']}")
    
    async def on_progress_update(self, data):
        print(f"Progress: {data['percentage']}%")
    
    async def on_notification(self, data):
        print(f"📢 {data['message']}")
    
    async def on_error(self, error):
        print(f"Error: {error}")

# Connect with handlers
handler = MyHandler()
await ws.connect(handler)

# Subscribe to channels
await ws.subscribe([
    "course_updates",
    "quiz_results",
    "notifications"
])

# Send custom message
await ws.send(
    event_type=WebSocketEvent.CUSTOM,
    data={"action": "ping"}
)

# Unsubscribe from channel
await ws.unsubscribe(["quiz_results"])

# Disconnect
await ws.disconnect()

# Alternative: Context manager
async with client.websocket.session() as ws:
    await ws.subscribe(["notifications"])
    
    # Listen for 60 seconds
    await asyncio.sleep(60)
```

### Agent Management Module

```python
from toolboxai.agents import AgentManager, AgentType
from toolboxai.types import AgentTask

agent_manager = client.agents

# Get agent status
status = await agent_manager.get_status()
for agent in status.agents:
    print(f"{agent.name}: {agent.status} ({agent.tasks_completed} tasks)")

# Execute agent task
result = await agent_manager.execute_task(
    agent_type=AgentType.CONTENT,
    task=AgentTask(
        action="generate_lesson",
        params={
            "subject": "Physics",
            "topic": "Gravity",
            "grade_level": 9
        }
    )
)

# Batch agent execution
results = await agent_manager.execute_batch([
    {
        "agent_type": AgentType.QUIZ,
        "task": {"action": "generate_quiz", "params": {...}}
    },
    {
        "agent_type": AgentType.TERRAIN,
        "task": {"action": "generate_terrain", "params": {...}}
    }
])

# Monitor agent performance
performance = await agent_manager.get_performance(
    agent_type=AgentType.CONTENT,
    time_range=TimeRange.DAILY
)
print(f"Average processing time: {performance.avg_processing_time}s")
print(f"Success rate: {performance.success_rate}%")
```

### Roblox Integration Module

```python
from toolboxai.roblox import RobloxIntegration, ScriptType
from toolboxai.types import TerrainType, InteractionType

roblox = client.roblox

# Generate Roblox scripts
scripts = await roblox.generate_scripts(
    lesson_id="lesson-123",
    terrain_type=TerrainType.CLASSROOM,
    interactions=[
        InteractionType.QUIZ_STATION,
        InteractionType.ACTIVITY_ZONE,
        InteractionType.REWARD_CHEST
    ]
)

print(f"Terrain script: {scripts.terrain_script[:100]}...")
print(f"UI script: {scripts.ui_script[:100]}...")
print(f"Game logic: {scripts.game_logic[:100]}...")

# Deploy to Roblox
deployment = await roblox.deploy(
    place_id="123456789",
    scripts=scripts,
    auto_publish=True
)

print(f"Deployed to: {deployment.place_url}")
print(f"Version: {deployment.version}")

# Sync with Roblox Studio
sync_result = await roblox.sync_studio(
    place_id="123456789",
    sync_assets=True,
    sync_scripts=True
)

# Get Roblox analytics
roblox_analytics = await roblox.get_analytics(
    place_id="123456789",
    metrics=["play_time", "completion_rate", "engagement"]
)
```

### User Management Module

```python
from toolboxai.users import UserManager, UserRole
from toolboxai.types import UserUpdate

user_manager = client.users

# Get current user
me = await user_manager.get_me()
print(f"Current user: {me.name} ({me.email})")

# Get user by ID
user = await user_manager.get(user_id="user-123")

# Update user profile
updated = await user_manager.update(
    user_id=me.id,
    update=UserUpdate(
        name="New Name",
        grade_level=8,
        avatar_url="https://example.com/avatar.png",
        preferences={
            "theme": "dark",
            "notifications": True
        }
    )
)

# List users (admin only)
users = await user_manager.list(
    role=UserRole.STUDENT,
    grade_level=7,
    active=True,
    limit=50
)

# Create user (admin only)
new_user = await user_manager.create(
    email="newstudent@school.edu",
    name="New Student",
    role=UserRole.STUDENT,
    grade_level=7,
    password="TempPassword123!"
)

# Delete user (admin only)
await user_manager.delete(user_id="user-456")

# Bulk operations (admin only)
results = await user_manager.bulk_create([
    {"email": "student1@school.edu", "name": "Student 1", ...},
    {"email": "student2@school.edu", "name": "Student 2", ...}
])
```

### Error Handling

```python
from toolboxai.exceptions import (
    ToolboxAIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError
)

try:
    content = await client.content.generate(...)
    
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Refresh token or re-login
    await client.auth.refresh_token()
    
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after} seconds")
    await asyncio.sleep(e.retry_after)
    
except ValidationError as e:
    print(f"Invalid request: {e}")
    print(f"Validation errors: {e.errors}")
    
except NotFoundError as e:
    print(f"Resource not found: {e}")
    
except ServerError as e:
    print(f"Server error: {e}")
    # Implement exponential backoff
    
except ToolboxAIError as e:
    print(f"API error: {e}")
```

### Async Context Manager

```python
# Use as async context manager
async with ToolboxAI(api_key="your-key") as client:
    await client.auth.login("user@example.com", "password")
    
    content = await client.content.generate(
        subject="Math",
        grade_level=7,
        learning_objectives=["Fractions"]
    )
    
    # WebSocket automatically connects
    await client.websocket.subscribe(["notifications"])
    
# Automatically disconnects and cleans up
```

### Pagination

```python
from toolboxai.pagination import Paginator

# Automatic pagination
paginator = Paginator(client.quiz.list)

async for quiz in paginator.items(
    subject="Mathematics",
    grade_level=7
):
    print(f"Quiz: {quiz.title}")

# Manual pagination
page = await client.quiz.list(
    limit=10,
    offset=0
)

while page.has_next:
    for quiz in page.items:
        print(quiz.title)
    
    page = await page.next()
```

### Caching

```python
from toolboxai.cache import CacheConfig, CacheStrategy

# Configure caching
cache_config = CacheConfig(
    strategy=CacheStrategy.LRU,
    max_size=100,
    ttl_seconds=300
)

client = ToolboxAI(
    api_key="your-key",
    cache_config=cache_config
)

# Cached requests
content1 = await client.content.get("content-123")  # API call
content2 = await client.content.get("content-123")  # From cache

# Clear cache
client.cache.clear()

# Disable cache for specific request
content = await client.content.get(
    "content-123",
    use_cache=False
)
```

### Logging

```python
import logging
from toolboxai.logging import setup_logging

# Setup logging
setup_logging(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    file="toolboxai.log"
)

# Or use custom logger
logger = logging.getLogger("my_app")
client = ToolboxAI(
    api_key="your-key",
    logger=logger
)
```

### Testing Support

```python
from toolboxai.testing import MockClient, create_test_data
import pytest

@pytest.fixture
def mock_client():
    return MockClient()

@pytest.fixture
def test_data():
    return create_test_data()

async def test_content_generation(mock_client, test_data):
    # Mock responses
    mock_client.content.generate.return_value = test_data.lesson
    
    # Test your code
    result = await mock_client.content.generate(
        subject="Math",
        grade_level=7,
        learning_objectives=["Test"]
    )
    
    assert result.title == test_data.lesson.title
    mock_client.content.generate.assert_called_once()
```

### Environment Variables

```python
# Auto-load from environment
import os

os.environ["TOOLBOXAI_API_KEY"] = "your-key"
os.environ["TOOLBOXAI_BASE_URL"] = "https://api.toolboxai.com"

# Client auto-configures from environment
client = ToolboxAI()  # No parameters needed
```

### Type Hints and IDE Support

```python
from toolboxai import ToolboxAI
from toolboxai.types import Content, Quiz, User
from typing import List, Optional

async def generate_content_for_class(
    client: ToolboxAI,
    subject: str,
    grade: int
) -> List[Content]:
    """Generate content for entire class."""
    contents: List[Content] = []
    
    for topic in ["Lesson 1", "Lesson 2", "Lesson 3"]:
        content: Content = await client.content.generate(
            subject=subject,
            grade_level=grade,
            learning_objectives=[topic]
        )
        contents.append(content)
    
    return contents

# Full IDE autocomplete and type checking support
```

## Migration Guide

### From v1.x to v2.x

```python
# Old (v1.x)
from toolboxai import Client
client = Client(api_key="key")
content = client.generate_content(...)

# New (v2.x)  
from toolboxai import ToolboxAI
client = ToolboxAI(api_key="key")
content = await client.content.generate(...)
```

### From REST API to SDK

```python
# Before (using requests)
import requests

response = requests.post(
    "https://api.toolboxai.com/content/generate",
    headers={"Authorization": f"Bearer {token}"},
    json={"subject": "Math", "grade_level": 7}
)
content = response.json()

# After (using SDK)
from toolboxai import ToolboxAI

client = ToolboxAI(api_key="key")
content = await client.content.generate(
    subject="Math",
    grade_level=7
)
```

## Performance Optimization

```python
# Connection pooling
from toolboxai.client import ConnectionPool

pool = ConnectionPool(
    max_connections=10,
    max_keepalive_connections=5,
    keepalive_expiry=600
)

client = ToolboxAI(
    api_key="key",
    connection_pool=pool
)

# Batch operations
contents = await client.content.generate_batch([
    {"subject": "Math", "grade_level": 5},
    {"subject": "Science", "grade_level": 5}
], concurrent=True)

# Stream large responses
async for chunk in client.content.generate_stream(
    subject="History",
    grade_level=8,
    stream=True
):
    print(chunk, end="")
```

## Contributing

```bash
# Clone repository
git clone https://github.com/toolboxai/python-sdk.git
cd python-sdk

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linting
black .
flake8 .
mypy .

# Build documentation
cd docs && make html
```

## Support

- Documentation: https://docs.toolboxai.com/sdk/python
- GitHub Issues: https://github.com/toolboxai/python-sdk/issues
- Discord: https://discord.gg/toolboxai
- Email: sdk-support@toolboxai.com