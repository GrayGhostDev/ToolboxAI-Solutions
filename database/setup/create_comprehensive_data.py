#!/usr/bin/env python3
"""
Create Comprehensive Real Initial Data for ToolboxAI

This script creates realistic test data for all databases with
actual educational content, proper relationships, and production-ready configurations.
"""

import os
import random
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import hashlib

from sqlalchemy import text

from database.connection_manager import get_session


def hash_password(password: str) -> str:
    """Simple password hashing for demo purposes"""
    # In production, use bcrypt or similar
    return "$2b$12$" + hashlib.sha256(password.encode()).hexdigest()[:56]


def create_comprehensive_data():
    """Create comprehensive real initial data for all databases."""
    print("🌱 Creating Comprehensive Real Data for ToolboxAI")
    print("=" * 50)

    try:
        with get_session("education") as session:
            print("📊 Creating comprehensive data for educational platform...")

            # ========== CREATE REALISTIC USERS ==========
            print("👥 Creating realistic users...")

            # Teacher accounts
            teachers_sql = """
            INSERT INTO users (id, username, email, password_hash, first_name, last_name, 
                             role, grade_level, school_name, is_active, is_verified, 
                             subjects_taught, bio, created_at)
            VALUES 
            (gen_random_uuid(), 'john_smith', 'john.smith@school.edu', 
             :pwd1, 'John', 'Smith', 'teacher', 7, 'Lincoln Middle School', 
             true, true, ARRAY['["Science", "Physics"]'::jsonb], 
             'Experienced science teacher with 10 years of teaching middle school physics and chemistry.',
             NOW()),
            
            (gen_random_uuid(), 'sarah_johnson', 'sarah.johnson@school.edu', 
             :pwd2, 'Sarah', 'Johnson', 'teacher', 8, 'Lincoln Middle School', 
             true, true, ARRAY['["Mathematics", "Algebra"]'::jsonb],
             'Math department head, specializing in algebra and geometry.',
             NOW()),
             
            (gen_random_uuid(), 'michael_brown', 'michael.brown@school.edu', 
             :pwd3, 'Michael', 'Brown', 'teacher', 7, 'Lincoln Middle School', 
             true, true, ARRAY['["History", "Social Studies"]'::jsonb],
             'History teacher passionate about making ancient civilizations come alive.',
             NOW())
            ON CONFLICT (email) DO NOTHING
            RETURNING id, username;
            """

            # Execute with password hashes
            result = session.execute(
                text(teachers_sql),
                {
                    "pwd1": hash_password("Teacher123!"),
                    "pwd2": hash_password("Teacher123!"),
                    "pwd3": hash_password("Teacher123!"),
                },
            )
            teacher_ids = [(row[0], row[1]) for row in result]
            print(f"  ✅ Created {len(teacher_ids)} teachers")

            # Student accounts
            students = [
                (
                    "alice_wilson",
                    "alice.wilson@student.edu",
                    "Alice",
                    "Wilson",
                    7,
                    "A dedicated student who loves science experiments",
                ),
                (
                    "bob_davis",
                    "bob.davis@student.edu",
                    "Bob",
                    "Davis",
                    7,
                    "Math enthusiast and chess club member",
                ),
                (
                    "charlie_miller",
                    "charlie.miller@student.edu",
                    "Charlie",
                    "Miller",
                    8,
                    "Creative thinker with interest in history and art",
                ),
                (
                    "diana_garcia",
                    "diana.garcia@student.edu",
                    "Diana",
                    "Garcia",
                    7,
                    "Top performer in mathematics and science",
                ),
                (
                    "ethan_martinez",
                    "ethan.martinez@student.edu",
                    "Ethan",
                    "Martinez",
                    8,
                    "Aspiring game developer and coding club president",
                ),
                (
                    "fiona_anderson",
                    "fiona.anderson@student.edu",
                    "Fiona",
                    "Anderson",
                    7,
                    "Environmental science advocate",
                ),
                (
                    "george_taylor",
                    "george.taylor@student.edu",
                    "George",
                    "Taylor",
                    8,
                    "History buff and debate team captain",
                ),
                (
                    "hannah_thomas",
                    "hannah.thomas@student.edu",
                    "Hannah",
                    "Thomas",
                    7,
                    "Straight-A student with perfect attendance",
                ),
            ]

            for username, email, first, last, grade, bio in students:
                student_sql = """
                INSERT INTO users (username, email, password_hash, first_name, last_name, 
                                 role, grade_level, school_name, is_active, is_verified, bio)
                VALUES (:username, :email, :password_hash, :first_name, :last_name, 'student', :grade_level, 'Lincoln Middle School', 
                        true, true, :bio)
                ON CONFLICT (email) DO NOTHING;
                """
                session.execute(
                    text(student_sql),
                    {
                        "username": username,
                        "email": email,
                        "password_hash": hash_password("Student123!"),
                        "first_name": first,
                        "last_name": last,
                        "grade_level": grade,
                        "bio": bio,
                    },
                )
            print(f"  ✅ Created {len(students)} students")

            # Admin account
            admin_sql = """
            INSERT INTO users (username, email, password_hash, first_name, last_name, 
                             role, is_active, is_verified, bio)
            VALUES ('admin', 'admin@toolboxai.com', :password_hash, 'System', 'Administrator', 
                    'admin', true, true, 'Platform administrator with full system access')
            ON CONFLICT (email) DO NOTHING;
            """
            session.execute(text(admin_sql), {"password_hash": hash_password("Admin123!")})
            print("  ✅ Created admin account")

            # ========== CREATE EDUCATIONAL CONTENT ==========
            print("\n📚 Creating educational content...")

            # Science Curriculum - 7th Grade
            science_content = [
                {
                    "title": "The Solar System",
                    "subject": "Science",
                    "grade": 7,
                    "objectives": [
                        "Identify planets in our solar system",
                        "Understand orbital mechanics",
                        "Learn about planetary characteristics",
                    ],
                    "description": "Comprehensive exploration of our solar system, including all planets, their moons, and the sun.",
                    "lessons": [
                        (
                            "Introduction to the Solar System",
                            "Overview of our cosmic neighborhood",
                            45,
                        ),
                        ("The Inner Planets", "Mercury, Venus, Earth, and Mars", 60),
                        ("The Outer Planets", "Jupiter, Saturn, Uranus, and Neptune", 60),
                        ("Moons and Asteroids", "Natural satellites and small bodies", 45),
                        ("Space Exploration", "History and future of space missions", 50),
                    ],
                },
                {
                    "title": "Cell Biology",
                    "subject": "Science",
                    "grade": 7,
                    "objectives": [
                        "Understand cell structure",
                        "Learn about organelles",
                        "Compare plant and animal cells",
                    ],
                    "description": "Deep dive into the building blocks of life - cells and their components.",
                    "lessons": [
                        ("What is a Cell?", "Introduction to cellular biology", 45),
                        ("Cell Membrane and Wall", "Protective barriers of cells", 50),
                        ("Nucleus and DNA", "The control center of the cell", 60),
                        ("Organelles", "Mitochondria, chloroplasts, and more", 55),
                        ("Cell Division", "Mitosis and cellular reproduction", 60),
                    ],
                },
            ]

            # Mathematics Curriculum - 7th & 8th Grade
            math_content = [
                {
                    "title": "Linear Equations",
                    "subject": "Mathematics",
                    "grade": 7,
                    "objectives": [
                        "Solve one-step equations",
                        "Solve two-step equations",
                        "Graph linear equations",
                    ],
                    "description": "Master the fundamentals of linear equations and their applications.",
                    "lessons": [
                        ("Introduction to Equations", "What are equations and why they matter", 45),
                        ("One-Step Equations", "Solving simple equations", 50),
                        ("Two-Step Equations", "More complex equation solving", 55),
                        ("Graphing Lines", "Visualizing linear equations", 60),
                        ("Word Problems", "Real-world applications", 60),
                    ],
                },
                {
                    "title": "Geometry Basics",
                    "subject": "Mathematics",
                    "grade": 8,
                    "objectives": [
                        "Understand angles and shapes",
                        "Calculate perimeter and area",
                        "Learn geometric proofs",
                    ],
                    "description": "Explore the world of shapes, angles, and spatial reasoning.",
                    "lessons": [
                        ("Points, Lines, and Angles", "Foundation of geometry", 45),
                        ("Triangles", "Types and properties of triangles", 55),
                        ("Quadrilaterals", "Squares, rectangles, and more", 50),
                        ("Circles", "Properties and measurements", 60),
                        ("Volume and Surface Area", "3D shapes", 65),
                    ],
                },
            ]

            # History Curriculum - 7th & 8th Grade
            history_content = [
                {
                    "title": "Ancient Civilizations",
                    "subject": "History",
                    "grade": 7,
                    "objectives": [
                        "Study major ancient civilizations",
                        "Understand cultural development",
                        "Learn about historical impact",
                    ],
                    "description": "Journey through the great civilizations of the ancient world.",
                    "lessons": [
                        ("Mesopotamia", "Cradle of civilization", 50),
                        ("Ancient Egypt", "Pharaohs and pyramids", 55),
                        ("Ancient Greece", "Democracy and philosophy", 60),
                        ("Roman Empire", "Rise and fall of Rome", 60),
                        ("Ancient China", "Dynasties and inventions", 55),
                    ],
                }
            ]

            # Create all content
            all_content = science_content + math_content + history_content

            for content in all_content:
                # Create learning objectives
                objectives_ids = []
                for obj in content["objectives"]:
                    obj_sql = """
                    INSERT INTO learning_objectives (title, description, subject, grade_level)
                    VALUES (:title, :description, :subject, :grade_level)
                    RETURNING id;
                    """
                    result = session.execute(
                        text(obj_sql),
                        {
                            "title": obj[:100],
                            "description": obj,
                            "subject": content["subject"],
                            "grade_level": content["grade"],
                        },
                    )
                    obj_id = result.scalar()
                    if obj_id:
                        objectives_ids.append(str(obj_id))

                # Create educational content
                content_sql = """
                INSERT INTO educational_content (
                    title, subject, grade_level, description,
                    environment_type, content_data, is_published, created_by
                )
                VALUES (:title, :subject, :grade_level, :description, 
                        :environment_type, :content_data, true, 
                        (SELECT id FROM users WHERE role = 'teacher' LIMIT 1))
                ON CONFLICT (title) DO NOTHING
                RETURNING id;
                """

                content_data = {
                    "type": "course",
                    "objectives": objectives_ids,
                    "tags": [content["subject"].lower(), "interactive", "gamified"],
                    "lessons": content.get("lessons", []),
                }

                result = session.execute(
                    text(content_sql),
                    {
                        "title": content["title"],
                        "subject": content["subject"],
                        "grade_level": content["grade"],
                        "description": content["description"],
                        "environment_type": "classroom",
                        "content_data": content_data,
                    },
                )
                content_id = result.scalar()

                # Create lessons for each content
                if content_id and "lessons" in content:
                    for idx, (lesson_title, lesson_desc, duration) in enumerate(
                        content["lessons"], 1
                    ):
                        lesson_sql = """
                        INSERT INTO lessons (
                            content_id, title, description, sequence_order,
                            duration_minutes, is_published
                        )
                        VALUES (:content_id, :title, :description, :sequence_order, :duration_minutes, true)
                        ON CONFLICT DO NOTHING;
                        """
                        session.execute(
                            text(lesson_sql),
                            {
                                "content_id": content_id,
                                "title": lesson_title,
                                "description": lesson_desc,
                                "sequence_order": idx,
                                "duration_minutes": duration,
                            },
                        )

            print(f"  ✅ Created {len(all_content)} courses with lessons")

            # ========== CREATE QUIZZES WITH REAL QUESTIONS ==========
            print("\n❓ Creating quizzes with real questions...")

            quiz_data = [
                {
                    "title": "Solar System Quiz",
                    "subject": "Science",
                    "questions": [
                        (
                            "What is the largest planet in our solar system?",
                            "multiple_choice",
                            ["Jupiter", "Saturn", "Earth", "Mars"],
                            0,
                            10,
                        ),
                        (
                            "How many planets are in our solar system?",
                            "multiple_choice",
                            ["7", "8", "9", "10"],
                            1,
                            10,
                        ),
                        (
                            "Which planet is known as the Red Planet?",
                            "multiple_choice",
                            ["Venus", "Mars", "Jupiter", "Mercury"],
                            1,
                            10,
                        ),
                        (
                            "What is the closest planet to the Sun?",
                            "multiple_choice",
                            ["Venus", "Earth", "Mercury", "Mars"],
                            2,
                            10,
                        ),
                        (
                            "Which planet has the most moons?",
                            "multiple_choice",
                            ["Earth", "Mars", "Jupiter", "Saturn"],
                            3,
                            15,
                        ),
                        (
                            "True or False: The Earth is the third planet from the Sun.",
                            "true_false",
                            ["True", "False"],
                            0,
                            5,
                        ),
                        (
                            "True or False: Pluto is classified as a planet.",
                            "true_false",
                            ["True", "False"],
                            1,
                            5,
                        ),
                        (
                            "Name the four inner planets in order from the Sun.",
                            "short_answer",
                            ["Mercury, Venus, Earth, Mars"],
                            0,
                            20,
                        ),
                        (
                            "What keeps planets in orbit around the Sun?",
                            "short_answer",
                            ["Gravity"],
                            0,
                            15,
                        ),
                        (
                            "How long does it take Earth to orbit the Sun?",
                            "multiple_choice",
                            ["365 days", "30 days", "24 hours", "12 months"],
                            0,
                            10,
                        ),
                    ],
                },
                {
                    "title": "Linear Equations Practice",
                    "subject": "Mathematics",
                    "questions": [
                        (
                            "Solve for x: 2x + 5 = 13",
                            "multiple_choice",
                            ["x = 4", "x = 6", "x = 8", "x = 9"],
                            0,
                            15,
                        ),
                        (
                            "Solve for y: y - 7 = 15",
                            "multiple_choice",
                            ["y = 8", "y = 22", "y = 15", "y = 7"],
                            1,
                            10,
                        ),
                        (
                            "What is the slope of y = 3x + 2?",
                            "multiple_choice",
                            ["2", "3", "-3", "1/3"],
                            1,
                            10,
                        ),
                        (
                            "True or False: x = 5 is a solution to 2x - 10 = 0",
                            "true_false",
                            ["True", "False"],
                            0,
                            10,
                        ),
                        ("If 3x = 18, what is x?", "short_answer", ["6"], 0, 10),
                        ("Solve: 4x + 2 = 2x + 10", "short_answer", ["x = 4", "4"], 0, 20),
                        (
                            "What is the y-intercept of y = 2x - 5?",
                            "multiple_choice",
                            ["-5", "2", "5", "-2"],
                            0,
                            15,
                        ),
                        (
                            "Which equation represents a horizontal line?",
                            "multiple_choice",
                            ["y = 5", "x = 5", "y = x", "y = 2x"],
                            0,
                            15,
                        ),
                        (
                            "True or False: All linear equations have exactly one solution",
                            "true_false",
                            ["True", "False"],
                            1,
                            10,
                        ),
                        (
                            "Solve for x: 5(x - 2) = 15",
                            "multiple_choice",
                            ["x = 1", "x = 3", "x = 5", "x = 7"],
                            2,
                            15,
                        ),
                    ],
                },
            ]

            for quiz in quiz_data:
                # Create quiz
                quiz_sql = """
                INSERT INTO quizzes (
                    title, description, subject, grade_level, 
                    total_points, time_limit_minutes, is_published,
                    created_by
                )
                VALUES (:title, :description, :subject, 7, :total_points, :time_limit, true,
                        (SELECT id FROM users WHERE role = 'teacher' LIMIT 1))
                ON CONFLICT (title) DO NOTHING
                RETURNING id;
                """

                total_points = sum(q[5] for q in quiz["questions"])
                result = session.execute(
                    text(quiz_sql),
                    {
                        "title": quiz["title"],
                        "description": f"Test your knowledge of {quiz['subject'].lower()} concepts",
                        "subject": quiz["subject"],
                        "total_points": total_points,
                        "time_limit": 30,
                    },
                )
                quiz_id = result.scalar()

                # Create questions
                if quiz_id:
                    for idx, (question, q_type, options, correct_idx, points) in enumerate(
                        quiz["questions"], 1
                    ):
                        question_sql = """
                        INSERT INTO quiz_questions (
                            quiz_id, question_text, question_type,
                            options, correct_answer, points, sequence_order
                        )
                        VALUES (:quiz_id, :question_text, :question_type, :options, :correct_answer, :points, :sequence_order)
                        ON CONFLICT DO NOTHING;
                        """

                        correct_answer = (
                            options[correct_idx]
                            if isinstance(options[correct_idx], str)
                            else str(options[correct_idx])
                        )
                        session.execute(
                            text(question_sql),
                            {
                                "quiz_id": quiz_id,
                                "question_text": question,
                                "question_type": q_type,
                                "options": options,
                                "correct_answer": correct_answer,
                                "points": points,
                                "sequence_order": idx,
                            },
                        )

            print(f"  ✅ Created {len(quiz_data)} quizzes with real questions")

            # ========== CREATE AI AGENT CONFIGURATIONS ==========
            print("\n🤖 Creating AI agent configurations...")

            agents_sql = """
            INSERT INTO ai_agents (name, agent_type, description, version, model_config, 
                                  capabilities, is_active, performance_metrics)
            VALUES 
            ('supervisor', 'supervisor', 
             'Main orchestration agent that coordinates all sub-agents for complex educational tasks', 
             '2.0.0', 
             '{"model": "gpt-4", "temperature": 0.7, "max_tokens": 4000, "top_p": 0.95}'::jsonb,
             ARRAY['["orchestration", "task_management", "workflow_coordination", "quality_control"]'::jsonb], 
             true,
             '{"success_rate": 0.95, "avg_response_time": 2.3, "tasks_completed": 1543}'::jsonb),
            
            ('content_generator', 'content', 
             'Specialized in creating educational content aligned with curriculum standards', 
             '2.0.0',
             '{"model": "gpt-4", "temperature": 0.8, "max_tokens": 8000, "top_p": 0.9}'::jsonb,
             ARRAY['["content_creation", "curriculum_alignment", "adaptive_learning", "multimodal_content"]'::jsonb],
             true,
             '{"success_rate": 0.92, "avg_response_time": 3.5, "content_created": 2156}'::jsonb),
            
            ('quiz_master', 'quiz',
             'Creates assessments and quizzes with varying difficulty levels',
             '2.0.0',
             '{"model": "gpt-4", "temperature": 0.6, "max_tokens": 4000, "top_p": 0.85}'::jsonb,
             ARRAY['["quiz_creation", "assessment_design", "adaptive_testing", "answer_validation"]'::jsonb],
             true,
             '{"success_rate": 0.94, "avg_response_time": 2.8, "quizzes_created": 892}'::jsonb),
            
            ('terrain_builder', 'terrain',
             'Generates immersive 3D environments for Roblox educational experiences',
             '2.0.0',
             '{"model": "gpt-4", "temperature": 0.9, "max_tokens": 6000, "top_p": 0.95}'::jsonb,
             ARRAY['["terrain_creation", "environment_design", "3d_modeling", "physics_simulation"]'::jsonb],
             true,
             '{"success_rate": 0.89, "avg_response_time": 4.2, "environments_created": 445}'::jsonb),
            
            ('script_wizard', 'script',
             'Generates optimized Lua scripts for Roblox game mechanics',
             '2.0.0',
             '{"model": "gpt-4", "temperature": 0.5, "max_tokens": 8000, "top_p": 0.9}'::jsonb,
             ARRAY['["script_creation", "code_generation", "optimization", "debugging", "roblox_api"]'::jsonb],
             true,
             '{"success_rate": 0.91, "avg_response_time": 3.8, "scripts_generated": 1789}'::jsonb),
            
            ('quality_reviewer', 'review',
             'Reviews and validates all generated content for quality and accuracy',
             '2.0.0',
             '{"model": "gpt-4", "temperature": 0.4, "max_tokens": 4000, "top_p": 0.85}'::jsonb,
             ARRAY['["content_review", "quality_assurance", "fact_checking", "improvement_suggestions"]'::jsonb],
             true,
             '{"success_rate": 0.97, "avg_response_time": 2.1, "reviews_completed": 3421}'::jsonb)
            ON CONFLICT (name) DO UPDATE 
            SET model_config = EXCLUDED.model_config,
                performance_metrics = EXCLUDED.performance_metrics;
            """

            session.execute(text(agents_sql))
            print("  ✅ Created 6 AI agents with production configurations")

            # ========== CREATE ACHIEVEMENTS AND GAMIFICATION ==========
            print("\n🏆 Creating achievements and gamification elements...")

            achievements_sql = """
            INSERT INTO achievements (name, description, type, points, icon_url, criteria, 
                                    tier, unlock_message)
            VALUES 
            ('First Steps', 'Complete your first lesson', 'milestone', 10, 
             '/icons/first-steps.png', '{"lessons_completed": 1}'::jsonb, 'bronze',
             'Welcome to your learning journey!'),
            
            ('Quiz Master', 'Score 100% on any quiz', 'performance', 25, 
             '/icons/quiz-master.png', '{"perfect_score": true}'::jsonb, 'silver',
             'Perfect score! You''re a true Quiz Master!'),
            
            ('Week Warrior', 'Maintain a 7-day learning streak', 'consistency', 50, 
             '/icons/streak.png', '{"streak_days": 7}'::jsonb, 'gold',
             'One week of consistent learning!'),
            
            ('Content Creator', 'Create your first educational content', 'creative', 30, 
             '/icons/creator.png', '{"content_created": 1}'::jsonb, 'silver',
             'You''re now a content creator!'),
            
            ('Team Player', 'Collaborate with 5 different students', 'social', 20, 
             '/icons/team.png', '{"unique_collaborators": 5}'::jsonb, 'bronze',
             'Teamwork makes the dream work!'),
            
            ('Science Explorer', 'Complete all science modules', 'subject', 100,
             '/icons/science.png', '{"subject": "Science", "completion": 100}'::jsonb, 'platinum',
             'You''ve mastered Science!'),
            
            ('Math Genius', 'Solve 100 math problems correctly', 'subject', 75,
             '/icons/math.png', '{"subject": "Mathematics", "problems_solved": 100}'::jsonb, 'gold',
             'Mathematical excellence achieved!'),
            
            ('History Buff', 'Complete all history lessons', 'subject', 80,
             '/icons/history.png', '{"subject": "History", "completion": 100}'::jsonb, 'gold',
             'You know your history!'),
            
            ('Speed Learner', 'Complete a lesson in under 10 minutes', 'performance', 15,
             '/icons/speed.png', '{"time_under": 600}'::jsonb, 'bronze',
             'Lightning fast learning!'),
            
            ('Perfectionist', 'Get 10 perfect quiz scores', 'performance', 150,
             '/icons/perfect.png', '{"perfect_scores": 10}'::jsonb, 'platinum',
             'Absolute perfection!')
            ON CONFLICT (name) DO UPDATE 
            SET points = EXCLUDED.points,
                criteria = EXCLUDED.criteria;
            """

            session.execute(text(achievements_sql))
            print("  ✅ Created 10 achievements with real criteria")

            # ========== CREATE LEADERBOARDS ==========
            print("\n📊 Creating leaderboards...")

            leaderboards_sql = """
            INSERT INTO leaderboards (name, description, type, scope, criteria, 
                                     reset_period, is_active)
            VALUES 
            ('Weekly Top Learners', 'Students with most XP gained this week', 
             'performance', 'global', '{"metric": "xp_gained", "period": "weekly"}'::jsonb,
             'weekly', true),
            
            ('Quiz Champions', 'Highest average quiz scores', 
             'academic', 'global', '{"metric": "quiz_average", "min_quizzes": 5}'::jsonb,
             'monthly', true),
            
            ('Helping Hands', 'Students who help others the most', 
             'social', 'global', '{"metric": "help_given", "type": "count"}'::jsonb,
             'monthly', true),
            
            ('Class Leaders', 'Top performers in each class', 
             'performance', 'class', '{"metric": "overall_score", "scope": "class"}'::jsonb,
             'weekly', true),
            
            ('Subject Masters', 'Top students by subject', 
             'academic', 'subject', '{"metric": "subject_score", "group_by": "subject"}'::jsonb,
             'monthly', true),
            
            ('Streak Warriors', 'Longest learning streaks', 
             'consistency', 'global', '{"metric": "streak_days", "active": true}'::jsonb,
             'never', true)
            ON CONFLICT (name) DO UPDATE 
            SET criteria = EXCLUDED.criteria,
                is_active = EXCLUDED.is_active;
            """

            session.execute(text(leaderboards_sql))
            print("  ✅ Created 6 active leaderboards")

            # ========== CREATE SAMPLE STUDENT PROGRESS ==========
            print("\n📈 Creating sample student progress...")

            # Get student and content IDs
            students_query = "SELECT id, username FROM users WHERE role = 'student' LIMIT 5"
            students_result = session.execute(text(students_query))
            student_data = [(row[0], row[1]) for row in students_result]

            content_query = "SELECT id, title FROM educational_content LIMIT 3"
            content_result = session.execute(text(content_query))
            content_data = [(row[0], row[1]) for row in content_result]

            # Create progress for each student
            for student_id, student_name in student_data:
                for content_id, content_title in content_data:
                    progress = random.randint(20, 100)
                    xp = progress * 10

                    progress_sql = f"""
                    INSERT INTO user_progress (
                        user_id, content_id, progress_percentage, 
                        xp_earned, time_spent_minutes, last_accessed
                    )
                    VALUES (:user_id, :content_id, :progress_percentage, :xp_earned, :time_spent, NOW() - INTERVAL '{random.randint(0, 7)} days')
                    ON CONFLICT (user_id, content_id) DO UPDATE
                    SET progress_percentage = EXCLUDED.progress_percentage,
                        xp_earned = EXCLUDED.xp_earned;
                    """

                    session.execute(
                        text(progress_sql),
                        {
                            "user_id": student_id,
                            "content_id": content_id,
                            "progress_percentage": progress,
                            "xp_earned": xp,
                            "time_spent": random.randint(30, 180),
                        },
                    )

            print(f"  ✅ Created progress records for {len(student_data)} students")

            # ========== CREATE ANALYTICS DATA ==========
            print("\n📊 Creating analytics data...")

            analytics_sql = """
            INSERT INTO educational_analytics (
                user_id, event_type, event_data, created_at
            )
            SELECT 
                u.id,
                CASE (random() * 4)::int
                    WHEN 0 THEN 'lesson_completed'
                    WHEN 1 THEN 'quiz_attempted'
                    WHEN 2 THEN 'achievement_earned'
                    WHEN 3 THEN 'content_viewed'
                    ELSE 'login'
                END,
                jsonb_build_object(
                    'duration', (random() * 60 + 10)::int,
                    'score', (random() * 100)::int,
                    'device', CASE (random() * 3)::int 
                        WHEN 0 THEN 'desktop'
                        WHEN 1 THEN 'tablet'
                        ELSE 'mobile'
                    END
                ),
                NOW() - (random() * INTERVAL '30 days')
            FROM users u
            WHERE u.role = 'student'
            LIMIT 50;
            """

            session.execute(text(analytics_sql))
            print("  ✅ Created 50 analytics events")

            # Commit all changes
            session.commit()
            print("\n🎉 Comprehensive data creation completed successfully!")

            # Print summary
            print("\n📊 Data Summary:")
            print("  - Teachers: 3")
            print("  - Students: 8")
            print("  - Admin: 1")
            print("  - Courses: 5 (with 25 lessons total)")
            print("  - Quizzes: 2 (with 20 questions total)")
            print("  - AI Agents: 6")
            print("  - Achievements: 10")
            print("  - Leaderboards: 6")
            print("  - Progress Records: Multiple")
            print("  - Analytics Events: 50+")

            return True

    except Exception as e:
        print(f"❌ Failed to create comprehensive data: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Change to project directory
    os.chdir(str(project_root))
    success = create_comprehensive_data()
    sys.exit(0 if success else 1)
