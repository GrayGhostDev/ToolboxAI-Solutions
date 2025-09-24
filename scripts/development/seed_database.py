#!/usr/bin/env python3
"""
Database Seed Script

Creates initial data for all tables including users, courses, lessons, content, and quizzes.
Run this after migrations to populate the database with test data.
"""

import asyncio
import uuid
import random
from datetime import datetime, timedelta
from typing import List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.database import (
    db_manager, get_async_session,
    User, UserRole, Course, Lesson, Content, ContentStatus,
    DifficultyLevel, Quiz, QuizQuestion, UserProgress, UserAchievement,
    Achievement, AchievementType, Session, Enrollment, QuizAttempt
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib


def hash_password(password: str) -> str:
    """Simple password hashing for demo purposes"""
    return hashlib.sha256(password.encode()).hexdigest()


async def create_users(db: AsyncSession) -> dict:
    """Create sample users"""
    print("Creating users...")
    
    users = {
        'admin': User(
            email="admin@toolboxai.com",
            username="admin",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN,
            first_name="Admin",
            last_name="User",
            display_name="Administrator",
            is_active=True,
            is_verified=True
        ),
        'teacher1': User(
            email="teacher1@toolboxai.com",
            username="teacher1",
            password_hash=hash_password("teacher123"),
            role=UserRole.TEACHER,
            first_name="Sarah",
            last_name="Johnson",
            display_name="Ms. Johnson",
            bio="Experienced math and science teacher",
            is_active=True,
            is_verified=True
        ),
        'teacher2': User(
            email="teacher2@toolboxai.com",
            username="teacher2",
            password_hash=hash_password("teacher123"),
            role=UserRole.TEACHER,
            first_name="Michael",
            last_name="Smith",
            display_name="Mr. Smith",
            bio="English and History educator",
            is_active=True,
            is_verified=True
        ),
        'student1': User(
            email="student1@toolboxai.com",
            username="student1",
            password_hash=hash_password("student123"),
            role=UserRole.STUDENT,
            first_name="Alice",
            last_name="Williams",
            display_name="Alice",
            roblox_username="AliceGamer",
            roblox_user_id="123456",
            is_active=True,
            is_verified=True
        ),
        'student2': User(
            email="student2@toolboxai.com",
            username="student2",
            password_hash=hash_password("student123"),
            role=UserRole.STUDENT,
            first_name="Bob",
            last_name="Brown",
            display_name="Bob",
            roblox_username="BobBuilder",
            roblox_user_id="789012",
            is_active=True,
            is_verified=True
        ),
        'parent1': User(
            email="parent1@toolboxai.com",
            username="parent1",
            password_hash=hash_password("parent123"),
            role=UserRole.PARENT,
            first_name="Jennifer",
            last_name="Williams",
            display_name="Mrs. Williams",
            is_active=True,
            is_verified=True
        )
    }
    
    for user in users.values():
        db.add(user)
    
    await db.commit()
    print(f"✅ Created {len(users)} users")
    return users


async def create_courses(db: AsyncSession, users: dict) -> List[Course]:
    """Create sample courses"""
    print("Creating courses...")
    
    courses_data = [
        {
            "title": "Mathematics Grade 7",
            "code": "MATH7",
            "subject": "Mathematics",
            "grade_level": 7,
            "description": "Comprehensive 7th grade mathematics covering algebra, geometry, and statistics",
            "teacher_id": users['teacher1'].id,
            "objectives": [
                "Master algebraic expressions",
                "Understand geometric relationships",
                "Apply statistical concepts"
            ],
            "tags": ["math", "algebra", "geometry", "grade7"]
        },
        {
            "title": "Science Grade 8",
            "code": "SCI8",
            "subject": "Science",
            "grade_level": 8,
            "description": "Physical and life sciences for 8th grade students",
            "teacher_id": users['teacher1'].id,
            "objectives": [
                "Understand physics principles",
                "Explore chemistry basics",
                "Study biology fundamentals"
            ],
            "tags": ["science", "physics", "chemistry", "biology", "grade8"]
        },
        {
            "title": "English Literature Grade 9",
            "code": "ENG9",
            "subject": "English",
            "grade_level": 9,
            "description": "Classic and contemporary literature analysis",
            "teacher_id": users['teacher2'].id,
            "objectives": [
                "Analyze literary themes",
                "Improve writing skills",
                "Develop critical thinking"
            ],
            "tags": ["english", "literature", "writing", "grade9"]
        },
        {
            "title": "World History",
            "code": "HIST10",
            "subject": "History",
            "grade_level": 10,
            "description": "Comprehensive world history from ancient to modern times",
            "teacher_id": users['teacher2'].id,
            "objectives": [
                "Understand historical events",
                "Analyze cause and effect",
                "Connect past to present"
            ],
            "tags": ["history", "world", "civilization", "grade10"]
        }
    ]
    
    courses = []
    for course_data in courses_data:
        course = Course(**course_data)
        courses.append(course)
        db.add(course)
    
    await db.commit()
    print(f"✅ Created {len(courses)} courses")
    return courses


async def create_lessons(db: AsyncSession, courses: List[Course]) -> List[Lesson]:
    """Create sample lessons for each course"""
    print("Creating lessons...")
    
    lessons = []
    lesson_templates = {
        "Mathematics": [
            ("Introduction to Algebra", "Basic algebraic concepts and expressions", DifficultyLevel.BEGINNER, 45),
            ("Linear Equations", "Solving single-variable linear equations", DifficultyLevel.INTERMEDIATE, 60),
            ("Graphing Functions", "Plotting and interpreting graphs", DifficultyLevel.INTERMEDIATE, 55),
            ("Quadratic Equations", "Understanding and solving quadratics", DifficultyLevel.ADVANCED, 70),
            ("Statistics Basics", "Mean, median, mode, and range", DifficultyLevel.BEGINNER, 40)
        ],
        "Science": [
            ("Forces and Motion", "Newton's laws and motion principles", DifficultyLevel.INTERMEDIATE, 50),
            ("Energy and Work", "Types of energy and energy transfer", DifficultyLevel.INTERMEDIATE, 55),
            ("Chemical Reactions", "Basic chemistry and reactions", DifficultyLevel.ADVANCED, 65),
            ("Cell Biology", "Structure and function of cells", DifficultyLevel.INTERMEDIATE, 45),
            ("Ecosystems", "Environmental interactions and balance", DifficultyLevel.BEGINNER, 40)
        ],
        "English": [
            ("Shakespeare Introduction", "Life and works of Shakespeare", DifficultyLevel.BEGINNER, 45),
            ("Romeo and Juliet", "Analysis of the classic tragedy", DifficultyLevel.INTERMEDIATE, 60),
            ("Essay Writing", "Structure and techniques for essays", DifficultyLevel.INTERMEDIATE, 50),
            ("Poetry Analysis", "Understanding poetic devices", DifficultyLevel.ADVANCED, 55),
            ("Creative Writing", "Developing creative writing skills", DifficultyLevel.INTERMEDIATE, 45)
        ],
        "History": [
            ("Ancient Civilizations", "Egypt, Greece, and Rome", DifficultyLevel.BEGINNER, 50),
            ("Middle Ages", "Medieval Europe and feudalism", DifficultyLevel.INTERMEDIATE, 55),
            ("Renaissance", "Art, science, and cultural rebirth", DifficultyLevel.INTERMEDIATE, 45),
            ("Industrial Revolution", "Technology and social change", DifficultyLevel.ADVANCED, 60),
            ("Modern Era", "20th and 21st century events", DifficultyLevel.ADVANCED, 65)
        ]
    }
    
    for course in courses:
        templates = lesson_templates.get(course.subject, lesson_templates["Mathematics"])
        
        for idx, (title, desc, difficulty, duration) in enumerate(templates, 1):
            lesson = Lesson(
                course_id=course.id,
                title=title,
                description=desc,
                order_index=idx,
                difficulty=difficulty,
                estimated_duration=duration,
                content_type="interactive",
                learning_objectives=[
                    f"Understand {title.lower()} concepts",
                    f"Apply {title.lower()} in practice",
                    f"Evaluate {title.lower()} scenarios"
                ],
                is_published=True,
                is_active=True
            )
            
            # Add Roblox integration for some lessons
            if random.random() > 0.5:
                lesson.roblox_place_id = str(random.randint(1000000, 9999999))
                lesson.roblox_template = random.choice(["educational_world", "quiz_arena", "exploration_map"])
            
            lessons.append(lesson)
            db.add(lesson)
    
    await db.commit()
    print(f"✅ Created {len(lessons)} lessons")
    return lessons


async def create_content(db: AsyncSession, lessons: List[Lesson], users: dict) -> List[Content]:
    """Create educational content for lessons"""
    print("Creating educational content...")
    
    content_list = []
    content_types = ["video", "document", "activity", "simulation", "presentation"]
    
    for lesson in lessons:
        # Create 2-4 content items per lesson
        num_content = random.randint(2, 4)
        
        for i in range(num_content):
            content_type = random.choice(content_types)
            
            # Get subject and grade from course through lesson
            course_result = await db.execute(
                select(Course).where(Course.id == lesson.course_id)
            )
            course = course_result.scalar_one_or_none()
            
            content = Content(
                lesson_id=lesson.id,
                creator_id=random.choice([users['teacher1'].id, users['teacher2'].id]),
                title=f"{lesson.title} - {content_type.capitalize()} {i+1}",
                content_type=content_type,
                content_data={
                    "type": content_type,
                    "url": f"https://example.com/{content_type}/{lesson.id}/{i+1}",
                    "duration": random.randint(5, 30) if content_type in ["video", "presentation"] else None,
                    "interactive": content_type in ["activity", "simulation"]
                },
                subject=course.subject if course else "General",
                grade_level=course.grade_level if course else 8,
                difficulty=random.choice(["beginner", "intermediate", "advanced"]),
                metadata={
                    "format": content_type,
                    "language": "English",
                    "accessibility": ["captions", "transcripts"] if content_type == "video" else [],
                    "keywords": [lesson.title.lower(), content_type, course.subject.lower() if course else "general"]
                },
                ai_generated=random.random() > 0.7,
                ai_model="gpt-4" if random.random() > 0.5 else "claude-3",
                status=random.choice([ContentStatus.APPROVED, ContentStatus.APPROVED, ContentStatus.PENDING]),
                quality_score=round(random.uniform(7.0, 10.0), 1)
            )
            
            content_list.append(content)
            db.add(content)
    
    await db.commit()
    print(f"✅ Created {len(content_list)} content items")
    return content_list


async def create_quizzes(db: AsyncSession, lessons: List[Lesson]) -> List[Quiz]:
    """Create quizzes for lessons"""
    print("Creating quizzes...")
    
    quizzes = []
    
    for lesson in lessons:
        # Create a quiz for 70% of lessons
        if random.random() < 0.7:
            quiz = Quiz(
                lesson_id=lesson.id,
                title=f"{lesson.title} Quiz",
                description=f"Test your knowledge of {lesson.title}",
                quiz_type="multiple_choice",
                difficulty=lesson.difficulty,
                time_limit=random.choice([600, 900, 1200, 1800]),  # 10-30 minutes
                passing_score=random.choice([60.0, 65.0, 70.0, 75.0, 80.0]),
                max_attempts=random.choice([1, 2, 3]),
                randomize_questions=True,
                randomize_answers=True,
                show_correct_answers=True,
                allow_review=True,
                is_active=True,
                is_published=True
            )
            
            quizzes.append(quiz)
            db.add(quiz)
    
    await db.commit()
    
    # Create questions for each quiz
    for quiz in quizzes:
        num_questions = random.randint(5, 10)
        
        for i in range(num_questions):
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=f"Sample question {i+1} for {quiz.title}?",
                question_type="multiple_choice",
                order_index=i+1,
                points=random.choice([1.0, 2.0, 5.0]),
                options=[f"Option A", f"Option B", f"Option C", f"Option D"],
                correct_answer={"answer": random.choice(["Option A", "Option B", "Option C", "Option D"]), 
                               "index": random.randint(0, 3)},
                explanation=f"The correct answer is based on the lesson content.",
                hints=[
                    "Review the lesson material",
                    "Think about the key concepts"
                ]
            )
            db.add(question)
    
    await db.commit()
    print(f"✅ Created {len(quizzes)} quizzes with questions")
    return quizzes


async def create_progress_records(db: AsyncSession, users: dict, courses: List[Course], lessons: List[Lesson]):
    """Create progress records for students"""
    print("Creating progress records...")
    
    students = [users['student1'], users['student2']]
    progress_count = 0
    
    for student in students:
        # Enroll in 2-3 courses
        enrolled_courses = random.sample(courses, min(3, len(courses)))
        
        for course in enrolled_courses:
            # Create course progress
            course_progress = UserProgress(
                user_id=student.id,
                course_id=course.id,
                progress_percentage=random.uniform(20.0, 90.0),
                time_spent=random.randint(3600, 36000),  # 1-10 hours
                last_accessed=datetime.utcnow() - timedelta(days=random.randint(0, 7))
            )
            db.add(course_progress)
            progress_count += 1
            
            # Create lesson progress
            course_lessons = [l for l in lessons if l.course_id == course.id]
            for lesson in course_lessons[:random.randint(1, len(course_lessons))]:
                lesson_progress = UserProgress(
                    user_id=student.id,
                    course_id=course.id,
                    lesson_id=lesson.id,
                    progress_percentage=random.uniform(0.0, 100.0),
                    time_spent=random.randint(600, 7200),  # 10 mins - 2 hours
                    last_accessed=datetime.utcnow() - timedelta(days=random.randint(0, 14))
                )
                db.add(lesson_progress)
                progress_count += 1
    
    await db.commit()
    print(f"✅ Created {progress_count} progress records")


async def create_achievements(db: AsyncSession, users: dict):
    """Create achievement records for users"""
    print("Creating achievements...")
    
    achievement_templates = [
        ("First Steps", "Complete your first lesson", AchievementType.MILESTONE, 10),
        ("Quiz Master", "Score 100% on a quiz", AchievementType.MASTERY, 50),
        ("Week Warrior", "Study 7 days in a row", AchievementType.STREAK, 25),
        ("Course Complete", "Finish an entire course", AchievementType.COMPLETION, 100),
        ("Early Bird", "Start studying before 8 AM", AchievementType.SPECIAL, 15),
        ("Night Owl", "Study after 10 PM", AchievementType.SPECIAL, 15),
        ("Perfect Attendance", "Login every day for a month", AchievementType.STREAK, 75),
        ("Knowledge Seeker", "Complete 50 lessons", AchievementType.MILESTONE, 200)
    ]
    
    achievements_count = 0
    
    for name, desc, achievement_type, points in achievement_templates:
        # Give random achievements to students
        for student in [users['student1'], users['student2']]:
            if random.random() > 0.5:
                achievement = UserAchievement(
                    user_id=student.id,
                    achievement_type=achievement_type,
                    name=name,
                    description=desc,
                    points=points,
                    icon_url=f"https://example.com/badges/{name.lower().replace(' ', '_')}.png",
                    earned_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                )
                db.add(achievement)
                achievements_count += 1
    
    await db.commit()
    print(f"✅ Created {achievements_count} achievements")


async def main():
    """Main function to seed the database"""
    print("\n🌱 Starting database seeding...\n")
    
    try:
        # Initialize database connection
        await db_manager.initialize()
        
        async with db_manager.get_connection() as conn:
            # Check if database is already seeded
            result = await conn.fetchval("SELECT COUNT(*) FROM users")
            if result > 0:
                print("⚠️  Database already contains data. Skipping seed to avoid duplicates.")
                print("    To reseed, please clear the database first.")
                return
        
        # Get database session
        async for db in get_async_session():
            # Create data in order of dependencies
            users = await create_users(db)
            courses = await create_courses(db, users)
            lessons = await create_lessons(db, courses)
            content = await create_content(db, lessons, users)
            quizzes = await create_quizzes(db, lessons)
            await create_progress_records(db, users, courses, lessons)
            await create_achievements(db, users)
            
            print("\n✅ Database seeding completed successfully!")
            print("\n📊 Summary:")
            print(f"   - Users: {len(users)}")
            print(f"   - Courses: {len(courses)}")
            print(f"   - Lessons: {len(lessons)}")
            print(f"   - Content Items: {len(content)}")
            print(f"   - Quizzes: {len(quizzes)}")
            print("\n🔑 Test Credentials:")
            print("   Admin: admin@toolboxai.com / admin123")
            print("   Teacher: teacher1@toolboxai.com / teacher123")
            print("   Student: student1@toolboxai.com / student123")
            print("   Parent: parent1@toolboxai.com / parent123")
            
            break  # Exit after first iteration
            
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await db_manager.close_all()


if __name__ == "__main__":
    asyncio.run(main())