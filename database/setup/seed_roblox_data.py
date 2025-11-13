#!/usr/bin/env python3
"""
Seed data script for Roblox integration tables
Creates sample data for testing and development
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import (
    Course,
    Lesson,
    RobloxAchievement,
    RobloxContent,
    RobloxPlayerProgress,
    RobloxQuizResult,
    RobloxSession,
    RobloxTemplate,
    User,
)


async def create_sample_data():
    """Create comprehensive sample data for Roblox integration."""

    # Database connection
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://eduplatform:eduplatform2024@localhost:5432/educational_platform_dev")
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # First, check if we have any existing users and lessons
            result = await session.execute(text("SELECT id FROM users LIMIT 1"))
            existing_user = result.fetchone()

            result = await session.execute(text("SELECT id FROM lessons LIMIT 1"))
            existing_lesson = result.fetchone()

            if not existing_user or not existing_lesson:
                print("⚠️  No existing users or lessons found. Please run the basic seed data first.")
                return

            # Get sample user and lesson IDs
            teacher_result = await session.execute(text("SELECT id FROM users WHERE role = 'TEACHER' OR role = 'ADMIN' LIMIT 1"))
            teacher_id = teacher_result.fetchone()
            if teacher_id:
                teacher_id = teacher_id[0]
            else:
                teacher_id = existing_user[0]

            student_result = await session.execute(text("SELECT id FROM users WHERE role = 'STUDENT' LIMIT 3"))
            student_ids = [row[0] for row in student_result.fetchall()]
            if not student_ids:
                # Use any user as student for demo
                student_ids = [existing_user[0]]

            lesson_id = existing_lesson[0]

            print("🎮 Creating Roblox Templates...")

            # 1. Create Roblox Templates
            templates_data = [
                {
                    "name": "Math Adventures Template",
                    "description": "Interactive math learning environment for K-12",
                    "category": "mathematics",
                    "subject_area": "algebra",
                    "grade_level_min": 6,
                    "grade_level_max": 12,
                    "template_type": "SCRIPT",
                    "base_structure": {
                        "workspace": {
                            "terrain": "flat_baseplate",
                            "lighting": "bright_daytime",
                            "spawn_point": {"x": 0, "y": 5, "z": 0}
                        },
                        "gui": {
                            "progress_bar": True,
                            "hint_system": True,
                            "score_display": True
                        }
                    },
                    "customization_points": [
                        {"name": "difficulty_level", "type": "enum", "values": ["easy", "medium", "hard"]},
                        {"name": "problem_count", "type": "integer", "range": [5, 50]},
                        {"name": "time_limit", "type": "integer", "range": [60, 1800]}
                    ],
                    "required_assets": [
                        {"type": "model", "id": "123456", "name": "Math Classroom"},
                        {"type": "sound", "id": "789012", "name": "Success Sound"}
                    ],
                    "script_templates": {
                        "main_script": '''
-- Math Adventures Main Script
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- Initialize math problem generator
local mathProblems = require(ReplicatedStorage.MathProblems)
mathProblems:init()

print("Math Adventures initialized for " .. player.Name)
                        '''
                    }
                },
                {
                    "name": "Science Lab Simulator",
                    "description": "Virtual chemistry and physics lab",
                    "category": "science",
                    "subject_area": "chemistry",
                    "grade_level_min": 9,
                    "grade_level_max": 12,
                    "template_type": "MODEL",
                    "base_structure": {
                        "lab_equipment": {
                            "beakers": 6,
                            "bunsen_burners": 4,
                            "microscopes": 2,
                            "periodic_table": True
                        },
                        "safety_features": {
                            "fire_extinguisher": True,
                            "eye_wash_station": True,
                            "safety_shower": True
                        }
                    },
                    "customization_points": [
                        {"name": "experiment_type", "type": "enum", "values": ["acid_base", "organic", "physical"]},
                        {"name": "safety_level", "type": "enum", "values": ["basic", "intermediate", "advanced"]}
                    ]
                }
            ]

            templates = []
            for template_data in templates_data:
                template = RobloxTemplate(
                    id=uuid.uuid4(),
                    creator_id=teacher_id,
                    **template_data
                )
                session.add(template)
                templates.append(template)

            await session.flush()  # Get IDs
            print(f"✅ Created {len(templates)} Roblox templates")

            print("🎮 Creating Roblox Sessions...")

            # 2. Create Roblox Sessions
            sessions = []
            for i in range(3):
                session_data = RobloxSession(
                    id=uuid.uuid4(),
                    lesson_id=lesson_id,
                    teacher_id=teacher_id,
                    universe_id="8505376973",
                    place_id=f"1234567{i}",
                    server_id=f"server_{i}_abc123",
                    job_id=f"job_{i}_def456",
                    client_id="2214511122270781418",
                    websocket_session_id=f"ws_session_{i}_{uuid.uuid4().hex[:8]}",
                    websocket_connection_active=True if i < 2 else False,
                    status="ACTIVE" if i < 2 else "COMPLETED",
                    max_players=30,
                    current_players=len(student_ids) if i < 2 else 0,
                    sync_frequency_seconds=5,
                    last_sync_at=datetime.utcnow(),
                    sync_data={
                        "last_heartbeat": datetime.utcnow().isoformat(),
                        "player_positions": {},
                        "game_state": "active"
                    },
                    coppa_consent_verified=True,
                    audit_log=[
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            "event": "session_created",
                            "details": "Session initialized by teacher"
                        }
                    ],
                    started_at=datetime.utcnow() - timedelta(hours=i),
                    ended_at=datetime.utcnow() if i >= 2 else None,
                    last_activity_at=datetime.utcnow()
                )
                session.add(session_data)
                sessions.append(session_data)

            await session.flush()
            print(f"✅ Created {len(sessions)} Roblox sessions")

            print("🎮 Creating Roblox Content...")

            # 3. Create Roblox Content
            contents = []
            content_types = ["SCRIPT", "MODEL", "GUI"]
            for i, content_type in enumerate(content_types):
                content = RobloxContent(
                    id=uuid.uuid4(),
                    lesson_id=lesson_id,
                    template_id=templates[0].id,
                    title=f"Generated {content_type.title()} Content {i+1}",
                    content_type=content_type,
                    version="1.0.0",
                    place_id=sessions[0].place_id,
                    asset_id=f"asset_{i+1000}",
                    content_data={
                        "type": content_type.lower(),
                        "properties": {
                            "name": f"Generated_{content_type}_{i+1}",
                            "description": f"AI-generated {content_type} for math lesson"
                        },
                        "educational_context": {
                            "learning_objective": "Practice algebraic equations",
                            "difficulty": "intermediate",
                            "estimated_time": 15
                        }
                    },
                    roblox_properties={
                        "parent": "Workspace" if content_type == "MODEL" else "StarterGui",
                        "archivable": True,
                        "className": content_type.title()
                    },
                    educational_metadata={
                        "standards_alignment": ["CCSS.MATH.8.EE.A.1"],
                        "prerequisites": ["basic_algebra"],
                        "assessment_criteria": ["accuracy", "speed", "understanding"]
                    },
                    ai_generated=True,
                    ai_model="gpt-4",
                    generation_parameters={
                        "temperature": 0.7,
                        "max_tokens": 2000,
                        "difficulty_target": "grade_8"
                    },
                    generation_prompt=f"Create a {content_type} for teaching algebra to 8th graders",
                    is_deployed=True if i < 2 else False,
                    deployed_at=datetime.utcnow() if i < 2 else None,
                    usage_count=random_usage_count := (i + 1) * 5,
                    performance_metrics={
                        "average_completion_time": 12.5 + i * 2,
                        "success_rate": 0.85 - i * 0.05,
                        "user_satisfaction": 4.2 + i * 0.1
                    },
                    coppa_compliant=True,
                    content_rating="E"
                )
                session.add(content)
                contents.append(content)

            await session.flush()
            print(f"✅ Created {len(contents)} Roblox content items")

            print("🎮 Creating Player Progress...")

            # 4. Create Player Progress
            player_progress_records = []
            for session_record in sessions[:2]:  # Only active sessions
                for j, student_id in enumerate(student_ids[:2]):  # Limit to 2 students per session
                    progress = RobloxPlayerProgress(
                        id=uuid.uuid4(),
                        session_id=session_record.id,
                        student_id=student_id,
                        lesson_id=lesson_id,
                        roblox_user_id=f"roblox_user_{j+100}",
                        roblox_username=f"Student{j+1}",
                        progress_percentage=min(90, 30 + j * 25),  # Varying progress
                        checkpoints_completed=[
                            f"checkpoint_{k}" for k in range(1, min(6, j+3))
                        ],
                        objectives_met=[
                            "solve_linear_equations",
                            "understand_variables" if j > 0 else None
                        ],
                        score=85 + j * 5,
                        time_spent_seconds=900 + j * 300,
                        actions_completed=25 + j * 5,
                        mistakes_made=3 - j,
                        hints_used=2 - j if j < 2 else 0,
                        current_position={"x": 10 + j * 5, "y": 5, "z": 15 + j * 3},
                        current_activity="solving_equation_3",
                        last_interaction=datetime.utcnow() - timedelta(minutes=j * 5),
                        team_id=f"team_{j+1}" if j > 0 else None,
                        collaborative_actions=j * 3,
                        peer_interactions=j * 2,
                        difficulty_adjustments=[
                            {
                                "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
                                "from": "medium",
                                "to": "hard" if j > 0 else "easy",
                                "reason": "performance_based"
                            }
                        ],
                        learning_path=[
                            "intro_algebra",
                            "linear_equations",
                            "problem_solving"
                        ],
                        performance_trends={
                            "accuracy_trend": [0.7, 0.8, 0.85, 0.9],
                            "speed_trend": [45, 38, 32, 28],
                            "confidence_trend": [0.6, 0.7, 0.8, 0.85]
                        },
                        age_verified=True,
                        parental_consent_given=True,
                        data_collection_consent=True,
                        joined_at=datetime.utcnow() - timedelta(minutes=30),
                        session_duration_seconds=1800,
                        disconnections=0
                    )
                    session.add(progress)
                    player_progress_records.append(progress)

            await session.flush()
            print(f"✅ Created {len(player_progress_records)} player progress records")

            print("🎮 Creating Quiz Results...")

            # 5. Create Quiz Results
            quiz_results = []
            for progress_record in player_progress_records:
                for quiz_num in range(2):  # 2 quizzes per player
                    quiz_result = RobloxQuizResult(
                        id=uuid.uuid4(),
                        session_id=progress_record.session_id,
                        player_progress_id=progress_record.id,
                        quiz_name=f"Algebra Quiz {quiz_num + 1}",
                        quiz_type="interactive",
                        difficulty_level="INTERMEDIATE",
                        total_questions=10,
                        correct_answers=7 + quiz_num,
                        incorrect_answers=2 - quiz_num,
                        skipped_questions=1 if quiz_num == 0 else 0,
                        raw_score=70 + quiz_num * 10,
                        percentage_score=(70 + quiz_num * 10) / 10 * 10,
                        weighted_score=75 + quiz_num * 8,
                        bonus_points=5 if quiz_num > 0 else 0,
                        time_allocated_seconds=600,
                        time_taken_seconds=480 - quiz_num * 60,
                        average_time_per_question=48 - quiz_num * 6,
                        question_responses=[
                            {
                                "question_id": f"q_{i+1}",
                                "question": f"Solve for x: {i+2}x + 5 = {(i+2)*3 + 5}",
                                "student_answer": f"x = 3",
                                "correct_answer": f"x = 3",
                                "is_correct": True,
                                "time_taken": 45 + i * 3,
                                "hints_used": 0
                            } for i in range(5)
                        ] + [
                            {
                                "question_id": f"q_{i+6}",
                                "question": f"What is the slope of y = {i+2}x + 1?",
                                "student_answer": f"{i+2}",
                                "correct_answer": f"{i+2}",
                                "is_correct": i < 3,  # Some wrong answers
                                "time_taken": 35 + i * 2,
                                "hints_used": 1 if i >= 3 else 0
                            } for i in range(5)
                        ],
                        in_game_location={"x": 20, "y": 5, "z": 30},
                        game_context={
                            "area": "quiz_zone",
                            "difficulty_mode": "standard",
                            "assistance_level": "hints_available"
                        },
                        interactive_elements=[
                            "virtual_whiteboard",
                            "calculator",
                            "formula_reference"
                        ],
                        hints_provided=1 + quiz_num,
                        help_requests=quiz_num,
                        completed=True,
                        passed=(70 + quiz_num * 10) >= 70,
                        started_at=datetime.utcnow() - timedelta(minutes=25 - quiz_num * 10),
                        completed_at=datetime.utcnow() - timedelta(minutes=17 - quiz_num * 8)
                    )
                    session.add(quiz_result)
                    quiz_results.append(quiz_result)

            await session.flush()
            print(f"✅ Created {len(quiz_results)} quiz results")

            print("🎮 Creating Achievements...")

            # 6. Create Achievements
            achievements = []
            achievement_types = ["MILESTONE", "COMPLETION", "MASTERY"]
            achievement_names = [
                "First Steps in Algebra",
                "Problem Solver",
                "Algebra Master"
            ]

            for progress_record in player_progress_records[:2]:  # First 2 players get achievements
                for i, (ach_type, ach_name) in enumerate(zip(achievement_types, achievement_names)):
                    achievement = RobloxAchievement(
                        id=uuid.uuid4(),
                        session_id=progress_record.session_id,
                        student_id=progress_record.student_id,
                        achievement_name=ach_name,
                        achievement_type=ach_type,
                        description=f"Earned for {ach_name.lower()} in algebra lesson",
                        in_game_badge_id=f"badge_{i+1000}",
                        roblox_asset_id=f"asset_badge_{i+2000}",
                        game_location_earned={
                            "x": 15 + i * 5,
                            "y": 5,
                            "z": 25 + i * 3
                        },
                        points_awarded=10 + i * 5,
                        difficulty_multiplier=1.0 + i * 0.2,
                        rarity_bonus=i * 2,
                        trigger_conditions={
                            "type": ach_type.lower(),
                            "criteria": {
                                "progress_threshold": 50 + i * 25,
                                "accuracy_required": 0.7 + i * 0.1,
                                "time_limit": None
                            }
                        },
                        performance_context={
                            "score_when_earned": 85 + i * 5,
                            "progress_when_earned": 60 + i * 15,
                            "time_spent": 900 + i * 300
                        },
                        icon_url=f"https://roblox.com/asset-thumbnail/image?assetId={i+3000}",
                        badge_color=["#FFD700", "#C0C0C0", "#CD7F32"][i],  # Gold, Silver, Bronze
                        is_shareable=True,
                        shared_count=i,
                        likes_received=i * 2,
                        current_progress=100.0,
                        milestone_data={
                            "milestone_reached": ach_name,
                            "next_milestone": achievement_names[i+1] if i < len(achievement_names)-1 else None,
                            "total_milestones": len(achievement_names)
                        },
                        earned_at=datetime.utcnow() - timedelta(minutes=20 - i * 5)
                    )
                    session.add(achievement)
                    achievements.append(achievement)

            await session.flush()
            print(f"✅ Created {len(achievements)} achievements")

            # Commit all changes
            await session.commit()

            print("\\n🎉 Successfully created comprehensive Roblox integration seed data!")
            print(f"📊 Summary:")
            print(f"   • {len(templates)} Roblox Templates")
            print(f"   • {len(sessions)} Roblox Sessions")
            print(f"   • {len(contents)} Content Items")
            print(f"   • {len(player_progress_records)} Player Progress Records")
            print(f"   • {len(quiz_results)} Quiz Results")
            print(f"   • {len(achievements)} Achievements")
            print("\\n✅ Ready for Roblox integration testing!")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating seed data: {e}")
            raise

        finally:
            await engine.dispose()


def main():
    """Main entry point."""
    print("🚀 Creating Roblox Integration Seed Data...")
    print("=" * 50)

    asyncio.run(create_sample_data())


if __name__ == "__main__":
    main()