"""
ToolBoxAI Python SDK Examples
Complete examples demonstrating SDK usage patterns
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import matplotlib.pyplot as plt

from toolboxai import ToolBoxAI, ToolBoxAIAsync
from toolboxai.exceptions import (
    NotFoundError,
    AuthenticationError,
    RateLimitError,
    ValidationError
)

# ============================================
# SETUP AND AUTHENTICATION
# ============================================

# Basic initialization
client = ToolBoxAI(api_key=os.getenv("TOOLBOXAI_API_KEY"))

# Async client initialization
async_client = ToolBoxAIAsync(
    api_key=os.getenv("TOOLBOXAI_API_KEY"),
    environment="production",
    timeout=30,
    max_retries=3
)

# OAuth2 authentication for user-facing apps
oauth_client = ToolBoxAI(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    redirect_uri="https://yourapp.com/callback",
    auth_method="oauth2"
)


# ============================================
# LESSON MANAGEMENT EXAMPLES
# ============================================

def lesson_management_examples():
    """Examples for lesson management operations."""
    
    # List all available lessons with filtering
    math_lessons = client.lessons.list(
        subject="math",
        grade=5,
        difficulty="medium",
        limit=20,
        offset=0
    )
    
    print(f"Found {math_lessons.total} math lessons")
    for lesson in math_lessons.items:
        print(f"- {lesson.title} ({lesson.duration} mins)")
    
    # Get detailed lesson information
    lesson = client.lessons.get("lesson-123")
    print("Lesson details:", {
        "title": lesson.title,
        "objectives": lesson.objectives,
        "materials": lesson.materials,
        "assessments": len(lesson.assessments)
    })
    
    # Create a new lesson
    new_lesson = client.lessons.create(
        title="Introduction to Fractions",
        subject="math",
        grade=4,
        duration=45,
        objectives=[
            "Understand what fractions represent",
            "Identify numerator and denominator",
            "Compare simple fractions"
        ],
        content={
            "introduction": "Today we will learn about fractions...",
            "activities": [
                {
                    "type": "interactive",
                    "title": "Pizza Fractions",
                    "description": "Divide pizzas into equal parts"
                }
            ]
        },
        roblox_environment={
            "theme": "pizza_restaurant",
            "interactive": True
        }
    )
    
    # Update an existing lesson
    updated_lesson = client.lessons.update(
        "lesson-123",
        duration=60,
        difficulty="advanced",
        tags=["fractions", "visual-learning", "interactive"]
    )
    
    # Deploy lesson to Roblox
    deployment = client.lessons.deploy_to_roblox(
        "lesson-123",
        server_id="roblox-server-id",
        instance_type="classroom",
        max_players=30
    )
    print(f"Deployment URL: {deployment.join_url}")
    
    # Bulk operations with generator
    for lesson in client.lessons.list_all(subject="science"):
        # Process each lesson without loading all into memory
        process_lesson(lesson)


# ============================================
# ASYNC OPERATIONS
# ============================================

async def async_examples():
    """Examples using async/await for concurrent operations."""
    
    # Concurrent lesson fetching
    lesson_ids = ["lesson-1", "lesson-2", "lesson-3", "lesson-4", "lesson-5"]
    
    tasks = [async_client.lessons.get(lid) for lid in lesson_ids]
    lessons = await asyncio.gather(*tasks)
    
    for lesson in lessons:
        print(f"Loaded: {lesson.title}")
    
    # Async batch processing
    async def process_student_batch(student_ids: List[str]):
        tasks = []
        for student_id in student_ids:
            tasks.append(async_client.progress.get_overall(student_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for student_id, result in zip(student_ids, results):
            if isinstance(result, Exception):
                print(f"Error for {student_id}: {result}")
            else:
                # Safely access percent_complete attribute
                percent = getattr(result, 'percent_complete', None)
                if percent is not None:
                    print(f"Progress for {student_id}: {percent}%")
                else:
                    print(f"Progress for {student_id}: {result}")
    
    # Process students in batches
    all_students = ["student-" + str(i) for i in range(100)]
    batch_size = 10
    
    for i in range(0, len(all_students), batch_size):
        batch = all_students[i:i + batch_size]
        await process_student_batch(batch)


# ============================================
# QUIZ AND ASSESSMENT EXAMPLES
# ============================================

def quiz_examples():
    """Examples for quiz and assessment operations."""
    
    # Create a quiz
    quiz = client.quizzes.create(
        title="Fractions Assessment",
        lesson_id="lesson-123",
        quiz_type="formative",
        time_limit=600,  # 10 minutes
        questions=[
            {
                "type": "multiple_choice",
                "question": "What is 1/2 + 1/4?",
                "options": ["3/4", "2/6", "3/6", "1/3"],
                "correct_answer": 0,
                "points": 10
            },
            {
                "type": "true_false",
                "question": "1/3 is greater than 1/2",
                "correct_answer": False,
                "points": 5
            },
            {
                "type": "fill_blank",
                "question": "The top number in a fraction is called the ___",
                "correct_answer": "numerator",
                "points": 5
            }
        ],
        passing_score=70,
        randomize_questions=True
    )
    
    # Start a quiz attempt
    attempt = client.quizzes.start_attempt(
        quiz.id,
        user_id="user-123",
        timestamp=datetime.now().isoformat()
    )
    
    # Submit quiz answers
    submission = client.quizzes.submit_attempt(
        attempt.id,
        answers=[
            {"question_id": "q1", "answer": 0},      # Multiple choice
            {"question_id": "q2", "answer": False},  # True/false
            {"question_id": "q3", "answer": "numerator"}  # Fill in blank
        ],
        time_spent=485  # seconds
    )
    
    print(f"Quiz Results: Score={submission.score}, Passed={submission.passed}")
    
    # Get quiz analytics
    analytics = client.quizzes.get_analytics(quiz.id)
    print(f"Quiz Analytics:")
    print(f"  Total Attempts: {analytics.total_attempts}")
    print(f"  Average Score: {analytics.average_score:.1f}%")
    print(f"  Pass Rate: {analytics.pass_rate:.1f}%")
    print(f"  Average Time: {analytics.average_time_spent:.1f} seconds")


# ============================================
# STUDENT PROGRESS TRACKING
# ============================================

def progress_tracking_examples():
    """Examples for tracking student progress."""
    
    student_id = "student-123"
    
    # Track lesson progress
    client.progress.update(
        student_id,
        "lesson-123",
        completed=False,
        percent_complete=65,
        objectives_completed=["obj-1", "obj-2"],
        time_spent=1800,  # 30 minutes
        last_accessed_section="activities",
        checkpoint={
            "section_id": "section-3",
            "timestamp": datetime.now().isoformat()
        }
    )
    
    # Get student progress for a specific lesson
    lesson_progress = client.progress.get_for_lesson(student_id, "lesson-123")
    
    # Get overall student progress
    overall_progress = client.progress.get_overall(student_id)
    print(f"Student Progress:")
    print(f"  Lessons Completed: {overall_progress.completed_lessons}")
    print(f"  Total Time Spent: {overall_progress.total_time_spent} hours")
    print(f"  Average Quiz Score: {overall_progress.average_quiz_score:.1f}%")
    print(f"  Current Streak: {overall_progress.streak_days} days")
    
    # Generate progress report
    report = client.progress.generate_report(
        student_id,
        start_date="2024-01-01",
        end_date="2024-03-31",
        include_quizzes=True,
        include_activities=True,
        format="pdf"
    )
    
    # Save the report
    with open("progress-report.pdf", "wb") as f:
        f.write(report.data)


# ============================================
# DATA ANALYSIS WITH PANDAS
# ============================================

def data_analysis_examples():
    """Examples using pandas for data analysis."""
    
    # Get student progress as DataFrame
    df = client.analytics.get_progress_dataframe(
        class_id="class-123",
        start_date="2024-01-01",
        end_date="2024-03-31"
    )
    
    # Analyze performance by subject
    subject_performance = df.groupby("subject").agg({
        "score": ["mean", "std"],
        "time_spent": "sum",
        "completed": "count"
    })
    
    print("Performance by Subject:")
    print(subject_performance)
    
    # Find struggling students
    struggling_students = df[
        (df["score"] < 70) & 
        (df["attempts"] > 2)
    ]["student_id"].unique()
    
    print(f"Students needing help: {list(struggling_students)}")
    
    # Time series analysis
    df["date"] = pd.to_datetime(df["timestamp"])
    daily_activity = df.groupby(df["date"].dt.date).agg({
        "student_id": "nunique",
        "lesson_id": "count",
        "score": "mean"
    })
    
    # Plot trends
    fig, axes = plt.subplots(3, 1, figsize=(10, 8))
    
    daily_activity["student_id"].plot(ax=axes[0], title="Daily Active Students")
    daily_activity["lesson_id"].plot(ax=axes[1], title="Daily Lessons Completed")
    daily_activity["score"].plot(ax=axes[2], title="Daily Average Score")
    
    plt.tight_layout()
    plt.savefig("learning_trends.png")
    
    # Export to Excel with multiple sheets
    with pd.ExcelWriter("analytics_report.xlsx") as writer:
        subject_performance.to_excel(writer, sheet_name="Subject Performance")
        daily_activity.to_excel(writer, sheet_name="Daily Activity")
        df[df["student_id"].isin(struggling_students)].to_excel(
            writer, sheet_name="Struggling Students"
        )


# ============================================
# GAMIFICATION EXAMPLES
# ============================================

def gamification_examples():
    """Examples for gamification features."""
    
    user_id = "user-123"
    
    # Award XP points
    xp_result = client.gamification.award_xp(
        user_id,
        amount=100,
        reason="quiz_completion",
        source="quiz-456"
    )
    
    if xp_result.level_up:
        print(f"Level up! New level: {xp_result.new_level}")
        # Trigger celebration
        trigger_celebration(user_id, xp_result.new_level)
    
    # Unlock achievement
    achievement = client.gamification.unlock_achievement(
        user_id,
        "first_perfect_score"
    )
    print(f"Achievement unlocked: {achievement.title}")
    
    # Get user's achievements
    achievements = client.gamification.get_achievements(user_id)
    unlocked = [a for a in achievements if a.unlocked]
    print(f"Unlocked {len(unlocked)}/{len(achievements)} achievements")
    
    # Update leaderboard
    client.gamification.update_leaderboard(
        "weekly_xp",
        user_id=user_id,
        score=xp_result.total_xp
    )
    
    # Get leaderboard
    leaderboard = client.gamification.get_leaderboard(
        "weekly_xp",
        limit=10,
        timeframe="week"
    )
    
    for i, entry in enumerate(leaderboard.entries, 1):
        print(f"{i}. {entry.username}: {entry.score} XP")
    
    # Create and assign quest
    quest = client.gamification.create_quest(
        title="Math Master",
        description="Complete 5 math lessons this week",
        requirements=[
            {"type": "complete_lessons", "subject": "math", "count": 5}
        ],
        rewards={
            "xp": 500,
            "badge": "math_master",
            "items": ["golden_calculator"]
        },
        duration=timedelta(days=7)
    )
    
    client.gamification.assign_quest(user_id, quest.id)


# ============================================
# BATCH OPERATIONS
# ============================================

def batch_operations_examples():
    """Examples for batch operations."""
    
    # Batch create users
    users_data = [
        {"name": "Alice", "email": "alice@school.edu", "grade": 5},
        {"name": "Bob", "email": "bob@school.edu", "grade": 5},
        {"name": "Charlie", "email": "charlie@school.edu", "grade": 6}
    ]
    
    users = client.batch.create_users(users_data)
    
    # Batch enroll students
    student_ids = [u.id for u in users]
    enrollments = client.batch.enroll_students("course-123", student_ids)
    
    # Batch update progress with context manager
    with client.batch.progress_updater() as updater:
        for student_id in student_ids:
            for lesson_id in ["lesson-1", "lesson-2", "lesson-3"]:
                progress = calculate_progress(student_id, lesson_id)
                updater.add(student_id, lesson_id, progress)
    # Automatically commits when exiting context
    
    # Batch grade assignments
    grades_data = [
        {"assignment_id": "asn-1", "user_id": "user-1", "score": 95},
        {"assignment_id": "asn-1", "user_id": "user-2", "score": 87},
        {"assignment_id": "asn-1", "user_id": "user-3", "score": 92}
    ]
    
    grades = client.batch.grade_assignments(grades_data)
    print(f"Graded {len(grades)} assignments")


# ============================================
# CONTENT GENERATION WITH AI
# ============================================

def content_generation_examples():
    """Examples for AI-powered content generation."""
    
    # Generate lesson from topic
    lesson = client.ai.generate_lesson(
        topic="Introduction to Solar System",
        grade_level=6,
        duration=45,
        learning_objectives=[
            "Name the planets in order",
            "Understand planet characteristics",
            "Explain Earth's position"
        ],
        include_activities=True,
        include_quiz=True
    )
    
    print(f"Generated lesson: {lesson.title}")
    
    # Generate quiz questions
    questions = client.ai.generate_quiz_questions(
        topic="Fractions",
        difficulty="medium",
        count=10,
        question_types=["multiple_choice", "true_false", "fill_blank"],
        bloom_levels=["remember", "understand", "apply"]
    )
    
    for q in questions:
        print(f"Q: {q.question}")
        print(f"A: {q.correct_answer}")
    
    # Generate Roblox environment description
    environment = client.ai.generate_environment(
        lesson_title="Ancient Egypt",
        learning_objectives=["Understand pyramid construction", "Learn about pharaohs"],
        environment_style="historical",
        interactive_elements=["pyramid_builder", "hieroglyphics_decoder", "mummy_museum"]
    )
    
    print(f"Environment: {environment.description}")
    
    # Generate personalized feedback
    feedback = client.ai.generate_feedback(
        student_id="student-123",
        quiz_results={"score": 75, "missed_topics": ["denominators", "simplification"]},
        learning_style="visual",
        encouragement_level="high"
    )
    
    print(f"Feedback: {feedback.message}")


# ============================================
# LMS INTEGRATION EXAMPLES
# ============================================

def lms_integration_examples():
    """Examples for LMS integrations."""
    
    # Canvas integration
    canvas = client.integrations.canvas.setup(
        domain="school.instructure.com",
        access_token=os.getenv("CANVAS_TOKEN")
    )
    
    # Sync courses from Canvas
    courses = client.integrations.canvas.sync_courses()
    print(f"Synced {len(courses)} courses from Canvas")
    
    # Export grades to Canvas
    client.integrations.canvas.export_grades(
        "course-123",
        assignment_id="canvas-assignment-id",
        grades=[
            {"student_id": "student-1", "score": 95},
            {"student_id": "student-2", "score": 87}
        ]
    )
    
    # Google Classroom integration
    google_classroom = client.integrations.google_classroom.setup(
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )
    
    # Create assignment in Google Classroom
    client.integrations.google_classroom.create_assignment(
        course_id="google-course-id",
        title="Fractions Practice",
        description="Complete the fractions lesson and quiz",
        lesson_id="lesson-123",
        due_date="2024-12-20T23:59:59Z"
    )
    
    # Schoology integration
    schoology = client.integrations.schoology.setup(
        consumer_key=os.getenv("SCHOOLOGY_KEY"),
        consumer_secret=os.getenv("SCHOOLOGY_SECRET")
    )
    
    # Import roster from Schoology
    roster = client.integrations.schoology.import_roster("section-id")
    print(f"Imported {len(roster.students)} students")


# ============================================
# ANALYTICS AND REPORTING
# ============================================

def analytics_examples():
    """Examples for analytics and reporting."""
    
    # Get classroom analytics
    class_analytics = client.analytics.get_classroom(
        "class-123",
        start_date="2024-01-01",
        end_date="2024-03-31",
        metrics=["engagement", "performance", "progress"]
    )
    
    print("Class Analytics:")
    print(f"  Average Engagement: {class_analytics.engagement.average:.1f}%")
    print(f"  Top Performers: {class_analytics.performance.top5}")
    print(f"  Completion Rate: {class_analytics.progress.completion_rate:.1f}%")
    
    # Get learning patterns
    learning_patterns = client.analytics.get_learning_patterns("user-123")
    print("Learning Patterns:")
    print(f"  Preferred Time: {learning_patterns.preferred_study_time}")
    print(f"  Avg Session: {learning_patterns.avg_session_duration} mins")
    print(f"  Strong Subjects: {learning_patterns.subject_strengths}")
    print(f"  Improvement Areas: {learning_patterns.areas_for_improvement}")
    
    # Generate custom report
    report = client.analytics.generate_report(
        report_type="performance_summary",
        entity_type="school",
        entity_id="school-123",
        date_range={
            "start": "2024-01-01",
            "end": "2024-12-31"
        },
        include_charts=True,
        format="html"
    )
    
    # Save report
    with open("performance_report.html", "w") as f:
        f.write(report.content)
    
    # Track custom events
    client.analytics.track_event(
        "lesson_interaction",
        user_id="user-123",
        lesson_id="lesson-456",
        action="clicked_help_button",
        timestamp=datetime.now().isoformat(),
        metadata={
            "section": "quiz",
            "question_number": 3
        }
    )


# ============================================
# ERROR HANDLING
# ============================================

def error_handling_examples():
    """Examples for error handling."""
    
    # Basic error handling
    try:
        lesson = client.lessons.get("invalid-id")
    except NotFoundError as e:
        print(f"Lesson not found: {e.message}")
        # Show user-friendly error
    except AuthenticationError as e:
        print(f"Auth failed: {e.message}")
        # Redirect to login
    except RateLimitError as e:
        print(f"Rate limited. Retry after {e.retry_after} seconds")
        # Implement retry logic
        import time
        time.sleep(e.retry_after)
        # Retry request
    except ValidationError as e:
        print(f"Validation error: {e.errors}")
        # Show validation errors to user
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Log to error tracking service
    
    # Using error handler decorator
    @client.error_handler
    def safe_operation():
        # This operation will have automatic error handling
        return client.lessons.get("lesson-123")
    
    # Global error handler
    def global_error_handler(error):
        """Global error handling function."""
        print(f"API Error: {error}")
        
        # Send to error tracking service
        import sentry_sdk
        sentry_sdk.capture_exception(error)
        
        # Notify admins for critical errors
        if error.severity == "critical":
            notify_admins(error)
    
    client.set_error_handler(global_error_handler)


# ============================================
# WEBHOOKS AND EVENTS
# ============================================

def webhook_examples():
    """Examples for webhook handling."""
    
    # Register webhook endpoint
    webhook = client.webhooks.register(
        url="https://yourapp.com/webhooks/toolboxai",
        events=[
            "lesson.completed",
            "quiz.submitted",
            "achievement.unlocked",
            "user.leveled_up"
        ],
        secret=os.getenv("WEBHOOK_SECRET")
    )
    
    print(f"Webhook registered: {webhook.id}")
    
    # Flask webhook handler example
    from flask import Flask, request
    import hmac
    import hashlib
    
    app = Flask(__name__)
    
    @app.route("/webhooks/toolboxai", methods=["POST"])
    def handle_webhook():
        # Verify webhook signature
        signature = request.headers.get("X-ToolBoxAI-Signature")
        webhook_secret = os.getenv("WEBHOOK_SECRET")
        
        if not webhook_secret:
            return "Webhook secret not configured", 500
        
        expected_sig = hmac.new(
            webhook_secret.encode(),
            request.data,
            hashlib.sha256
        ).hexdigest()
        
        if signature != expected_sig:
            return "Invalid signature", 401
        
        # Process webhook event
        event = request.json
        if not event:
            return "Invalid request body", 400
            
        event_type = event.get("type")
        if not event_type:
            return "Missing event type", 400
        
        if event_type == "lesson.completed":
            handle_lesson_completed(event.get("data", {}))
        elif event_type == "quiz.submitted":
            handle_quiz_submitted(event.get("data", {}))
        elif event_type == "achievement.unlocked":
            handle_achievement_unlocked(event.get("data", {}))
        elif event_type == "user.leveled_up":
            handle_level_up(event.get("data", {}))
        
        return "OK", 200


# ============================================
# UTILITY FUNCTIONS
# ============================================

def process_lesson(lesson):
    """Process a single lesson."""
    print(f"Processing: {lesson.title}")


def calculate_progress(student_id: str, lesson_id: str) -> int:
    """Calculate student progress for a lesson."""
    # Implementation would calculate actual progress
    return 75


def trigger_celebration(user_id: str, level: int):
    """Trigger celebration for level up."""
    print(f"Celebrating level {level} for user {user_id}")


def notify_admins(error):
    """Notify administrators of critical errors."""
    print(f"Notifying admins of error: {error}")


def handle_lesson_completed(data):
    """Handle lesson completion webhook."""
    print(f"Lesson completed: {data}")


def handle_quiz_submitted(data):
    """Handle quiz submission webhook."""
    print(f"Quiz submitted: {data}")


def handle_achievement_unlocked(data):
    """Handle achievement unlock webhook."""
    print(f"Achievement unlocked: {data}")


def handle_level_up(data):
    """Handle level up webhook."""
    print(f"Level up: {data}")


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Main function to run all examples."""
    try:
        print("Starting ToolBoxAI Python SDK Examples...\n")
        
        # Run synchronous examples
        lesson_management_examples()
        quiz_examples()
        progress_tracking_examples()
        data_analysis_examples()
        gamification_examples()
        batch_operations_examples()
        content_generation_examples()
        lms_integration_examples()
        analytics_examples()
        error_handling_examples()
        webhook_examples()
        
        # Run async examples
        print("\nRunning async examples...")
        asyncio.run(async_examples())
        
        print("\nAll examples completed successfully!")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()