#!/usr/bin/env python3
"""
Seed data script for Educational Platform
Creates sample users, classes, lessons, and other data for development
"""

import sys
import os
from datetime import datetime, timedelta
import uuid
import bcrypt
import random
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import SessionLocal, init_db
from models import (
    User, UserRole,
    Class, ClassEnrollment,
    Lesson, LessonStatus, LessonDifficulty,
    Badge, BadgeCategory, BadgeRarity,
    XPTransaction, XPSource,
    UserBadge,
    ConsentRecord, ConsentType
)

# Load environment variables
load_dotenv()

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_users(db):
    """Create sample users"""
    print("👥 Creating users...")
    
    users = []
    
    # Admin user
    admin = User(
        id=str(uuid.uuid4()),
        email="admin@toolboxai.com",
        username="admin",
        password_hash=hash_password("Admin123!"),
        first_name="System",
        last_name="Administrator",
        display_name="Admin",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        total_xp=0,
        level=1,
        language="en",
        timezone="UTC"
    )
    users.append(admin)
    
    # Teachers
    teachers = [
        ("jane.smith@school.edu", "jsmith", "Jane", "Smith", "Ms. Smith"),
        ("john.doe@school.edu", "jdoe", "John", "Doe", "Mr. Doe"),
        ("mary.johnson@school.edu", "mjohnson", "Mary", "Johnson", "Mrs. Johnson"),
    ]
    
    for email, username, first, last, display in teachers:
        teacher = User(
            id=str(uuid.uuid4()),
            email=email,
            username=username,
            password_hash=hash_password("Teacher123!"),
            first_name=first,
            last_name=last,
            display_name=display,
            role=UserRole.TEACHER,
            is_active=True,
            is_verified=True,
            total_xp=0,
            level=1,
            language="en",
            timezone="America/New_York"
        )
        users.append(teacher)
    
    # Students
    student_data = [
        ("alex.johnson@student.edu", "alexj", "Alex", "Johnson", 14),
        ("sarah.williams@student.edu", "sarahw", "Sarah", "Williams", 13),
        ("mike.chen@student.edu", "mikec", "Mike", "Chen", 15),
        ("emma.davis@student.edu", "emmad", "Emma", "Davis", 12),
        ("lucas.brown@student.edu", "lucasb", "Lucas", "Brown", 14),
        ("sophia.garcia@student.edu", "sophiag", "Sophia", "Garcia", 13),
        ("william.martinez@student.edu", "williamm", "William", "Martinez", 15),
        ("olivia.rodriguez@student.edu", "oliviar", "Olivia", "Rodriguez", 12),
        ("james.wilson@student.edu", "jamesw", "James", "Wilson", 14),
        ("ava.anderson@student.edu", "avaa", "Ava", "Anderson", 13),
    ]
    
    for email, username, first, last, age in student_data:
        birth_date = datetime.now() - timedelta(days=age*365)
        student = User(
            id=str(uuid.uuid4()),
            email=email,
            username=username,
            password_hash=hash_password("Student123!"),
            first_name=first,
            last_name=last,
            display_name=f"{first} {last[0]}.",
            role=UserRole.STUDENT,
            is_active=True,
            is_verified=True,
            birth_date=birth_date,
            consent_given=True,
            consent_date=datetime.now(),
            total_xp=random.randint(500, 3000),
            level=random.randint(5, 25),
            streak_days=random.randint(0, 15),
            best_streak=random.randint(5, 30),
            language="en",
            timezone="America/New_York"
        )
        users.append(student)
    
    # Parents
    parent_data = [
        ("robert.johnson@parent.edu", "robertj", "Robert", "Johnson"),
        ("linda.williams@parent.edu", "lindaw", "Linda", "Williams"),
        ("david.chen@parent.edu", "davidc", "David", "Chen"),
        ("jennifer.davis@parent.edu", "jenniferd", "Jennifer", "Davis"),
    ]
    
    for email, username, first, last in parent_data:
        parent = User(
            id=str(uuid.uuid4()),
            email=email,
            username=username,
            password_hash=hash_password("Parent123!"),
            first_name=first,
            last_name=last,
            display_name=f"{first} {last}",
            role=UserRole.PARENT,
            is_active=True,
            is_verified=True,
            total_xp=0,
            level=1,
            language="en",
            timezone="America/New_York"
        )
        users.append(parent)
    
    # Add all users to database
    for user in users:
        db.add(user)
    
    db.commit()
    print(f"✅ Created {len(users)} users")
    return users

def create_classes(db, teachers):
    """Create sample classes"""
    print("📚 Creating classes...")
    
    classes = []
    class_data = [
        ("MATH101", "Mathematics Grade 5", "Mathematics", 5, 0),
        ("SCI201", "Science Grade 6", "Science", 6, 1),
        ("ENG101", "English Language Arts", "Language Arts", 5, 0),
        ("HIST201", "World History", "Social Studies", 6, 2),
        ("TECH101", "Introduction to Programming", "Technology", 5, 1),
        ("ART101", "Creative Arts", "Arts", 5, 2),
    ]
    
    for code, name, subject, grade, teacher_idx in class_data:
        class_obj = Class(
            id=str(uuid.uuid4()),
            name=name,
            code=code,
            description=f"Comprehensive {subject.lower()} curriculum for grade {grade}",
            subject=subject,
            grade_level=grade,
            teacher_id=teachers[teacher_idx].id,
            schedule="MWF 9:00-10:00 AM",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now() + timedelta(days=150),
            max_students=30,
            is_active=True,
            is_online=random.choice([True, False]),
            allow_late_enrollment=True,
            settings={}
        )
        classes.append(class_obj)
        db.add(class_obj)
    
    db.commit()
    print(f"✅ Created {len(classes)} classes")
    return classes

def create_enrollments(db, students, classes):
    """Create student enrollments in classes"""
    print("📝 Creating enrollments...")
    
    enrollments = []
    
    # Enroll each student in 2-3 random classes
    for student in students:
        num_classes = random.randint(2, min(3, len(classes)))
        enrolled_classes = random.sample(classes, num_classes)
        
        for class_obj in enrolled_classes:
            enrollment = ClassEnrollment(
                id=str(uuid.uuid4()),
                user_id=student.id,
                class_id=class_obj.id,
                enrollment_date=datetime.now() - timedelta(days=random.randint(10, 30)),
                is_active=True,
                progress_percentage=random.randint(20, 80),
                lessons_completed=random.randint(2, 10),
                assessments_completed=random.randint(1, 5),
                average_score=random.uniform(70, 95),
                class_xp=random.randint(100, 1000),
                class_rank=random.randint(1, 20)
            )
            enrollments.append(enrollment)
            db.add(enrollment)
    
    db.commit()
    print(f"✅ Created {len(enrollments)} enrollments")
    return enrollments

def create_badges(db):
    """Create sample badges"""
    print("🏆 Creating badges...")
    
    badges_data = [
        ("Problem Solver", "Solved 10 math problems correctly", BadgeCategory.ACHIEVEMENT, BadgeRarity.COMMON, 50, "#FFD700"),
        ("Science Explorer", "Completed all science lessons", BadgeCategory.MILESTONE, BadgeRarity.RARE, 200, "#4CAF50"),
        ("Team Player", "Participated in 5 group projects", BadgeCategory.SOCIAL, BadgeRarity.UNCOMMON, 100, "#2196F3"),
        ("Perfect Week", "Completed all assignments for a week", BadgeCategory.CONSISTENCY, BadgeRarity.RARE, 150, "#9C27B0"),
        ("Math Master", "Achieved 90% in all math assessments", BadgeCategory.MASTERY, BadgeRarity.EPIC, 300, "#FF9800"),
        ("First Steps", "Completed your first lesson", BadgeCategory.ACHIEVEMENT, BadgeRarity.COMMON, 25, "#795548"),
        ("Early Bird", "First to submit an assignment", BadgeCategory.ACHIEVEMENT, BadgeRarity.UNCOMMON, 75, "#00BCD4"),
        ("Perfect Score", "Got 100% on an assessment", BadgeCategory.ACHIEVEMENT, BadgeRarity.RARE, 150, "#E91E63"),
        ("Streak Master", "Maintained a 30-day streak", BadgeCategory.CONSISTENCY, BadgeRarity.LEGENDARY, 500, "#673AB7"),
        ("Helper", "Helped 10 classmates", BadgeCategory.SOCIAL, BadgeRarity.UNCOMMON, 100, "#8BC34A"),
    ]
    
    badges = []
    for name, desc, category, rarity, xp, color in badges_data:
        badge = Badge(
            id=str(uuid.uuid4()),
            name=name,
            description=desc,
            category=category,
            rarity=rarity,
            image_url=f"/badges/{name.lower().replace(' ', '-')}.png",
            color=color,
            requirements={"type": "automatic", "criteria": desc},
            xp_reward=xp,
            is_active=True,
            is_secret=False,
            times_earned=random.randint(0, 50)
        )
        badges.append(badge)
        db.add(badge)
    
    db.commit()
    print(f"✅ Created {len(badges)} badges")
    return badges

def create_lessons(db, teachers, classes, badges):
    """Create sample lessons"""
    print("📖 Creating lessons...")
    
    lessons_data = [
        ("Introduction to Fractions", "Learn the basics of fractions", "Mathematics", 5, LessonDifficulty.BEGINNER, 45, 100),
        ("Solar System Exploration", "Journey through our solar system", "Science", 6, LessonDifficulty.INTERMEDIATE, 60, 150),
        ("Creative Writing Workshop", "Develop storytelling skills", "Language Arts", 5, LessonDifficulty.BEGINNER, 30, 75),
        ("Ancient Civilizations", "Explore ancient Egypt and Rome", "Social Studies", 6, LessonDifficulty.INTERMEDIATE, 45, 125),
        ("Introduction to Python", "Your first programming lesson", "Technology", 5, LessonDifficulty.BEGINNER, 60, 200),
        ("Digital Art Basics", "Learn digital drawing techniques", "Arts", 5, LessonDifficulty.BEGINNER, 45, 100),
        ("Algebra Fundamentals", "Introduction to algebraic concepts", "Mathematics", 6, LessonDifficulty.INTERMEDIATE, 50, 150),
        ("Chemical Reactions", "Understanding chemical changes", "Science", 6, LessonDifficulty.ADVANCED, 55, 175),
        ("Poetry and Rhyme", "Exploring poetic forms", "Language Arts", 5, LessonDifficulty.BEGINNER, 35, 80),
        ("American Revolution", "The birth of a nation", "Social Studies", 6, LessonDifficulty.INTERMEDIATE, 45, 120),
    ]
    
    lessons = []
    for title, desc, subject, grade, difficulty, time, xp in lessons_data:
        # Find appropriate teacher
        teacher = random.choice([t for t in teachers if t.role == UserRole.TEACHER])
        
        lesson = Lesson(
            id=str(uuid.uuid4()),
            title=title,
            description=desc,
            subject=subject,
            grade_level=grade,
            teacher_id=teacher.id,
            content={"type": "interactive", "sections": []},
            resources={},
            status=LessonStatus.PUBLISHED,
            difficulty=difficulty,
            estimated_time_minutes=time,
            xp_reward=xp,
            badge_id=random.choice(badges).id if random.random() > 0.7 else None,
            thumbnail_url=f"/lessons/{title.lower().replace(' ', '-')}.jpg",
            tags=[subject.lower(), f"grade{grade}"],
            prerequisites=[],
            times_completed=random.randint(0, 100),
            average_rating=random.uniform(4.0, 5.0)
        )
        lessons.append(lesson)
        db.add(lesson)
    
    db.commit()
    print(f"✅ Created {len(lessons)} lessons")
    return lessons

def create_xp_transactions(db, students):
    """Create sample XP transactions"""
    print("💰 Creating XP transactions...")
    
    transactions = []
    sources = list(XPSource)
    
    for student in students[:5]:  # Create transactions for first 5 students
        for _ in range(random.randint(3, 8)):
            transaction = XPTransaction(
                id=str(uuid.uuid4()),
                user_id=student.id,
                amount=random.randint(10, 100),
                source=random.choice(sources),
                reason="Sample achievement",
                multiplier=1.0,
                bonus_applied=False,
                total_xp_after=student.total_xp,
                level_after=student.level,
                level_up=False
            )
            transactions.append(transaction)
            db.add(transaction)
    
    db.commit()
    print(f"✅ Created {len(transactions)} XP transactions")
    return transactions

def create_user_badges(db, students, badges):
    """Assign badges to students"""
    print("🎖️ Assigning badges to students...")
    
    user_badges = []
    
    for student in students:
        # Each student gets 1-3 random badges
        num_badges = random.randint(1, min(3, len(badges)))
        earned_badges = random.sample(badges, num_badges)
        
        for badge in earned_badges:
            user_badge = UserBadge(
                id=str(uuid.uuid4()),
                user_id=student.id,
                badge_id=badge.id,
                earned_at=datetime.now() - timedelta(days=random.randint(1, 30)),
                progress=100,
                is_featured=random.choice([True, False]),
                display_order=random.randint(0, 10)
            )
            user_badges.append(user_badge)
            db.add(user_badge)
    
    db.commit()
    print(f"✅ Assigned {len(user_badges)} badges to students")
    return user_badges

def create_consent_records(db, students, parents):
    """Create COPPA consent records"""
    print("📋 Creating consent records...")
    
    consent_records = []
    
    # Create parental consent for students under 13
    for student in students:
        if student.birth_date:
            age = (datetime.now() - student.birth_date).days // 365
            if age < 13:
                parent = random.choice(parents) if parents else None
                if parent:
                    consent = ConsentRecord(
                        id=str(uuid.uuid4()),
                        user_id=student.id,
                        parent_id=parent.id,
                        consent_type=ConsentType.COPPA_PARENTAL,
                        granted=True,
                        granted_at=datetime.now() - timedelta(days=random.randint(30, 90)),
                        scope=["data_processing", "educational_activities"],
                        version="1.0",
                        method="explicit",
                        verified=True,
                        verified_at=datetime.now() - timedelta(days=random.randint(20, 80)),
                        verification_method="email",
                        withdrawn=False
                    )
                    consent_records.append(consent)
                    db.add(consent)
    
    db.commit()
    print(f"✅ Created {len(consent_records)} consent records")
    return consent_records

def main():
    """Main function to seed the database"""
    print("🚀 Starting database seeding...")
    
    # Initialize database (ensure tables exist)
    init_db()
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print("⚠️  Database already contains data. Skipping seed.")
            response = input("Do you want to clear existing data and reseed? (yes/no): ")
            if response.lower() != 'yes':
                print("Exiting without changes.")
                return
            
            # Clear existing data
            print("🗑️  Clearing existing data...")
            # Delete in reverse order of dependencies
            db.query(UserBadge).delete()
            db.query(XPTransaction).delete()
            db.query(ConsentRecord).delete()
            db.query(ClassEnrollment).delete()
            db.query(Lesson).delete()
            db.query(Class).delete()
            db.query(Badge).delete()
            db.query(User).delete()
            db.commit()
            print("✅ Existing data cleared")
        
        # Create seed data
        users = create_users(db)
        
        # Separate users by role
        teachers = [u for u in users if u.role == UserRole.TEACHER]
        students = [u for u in users if u.role == UserRole.STUDENT]
        parents = [u for u in users if u.role == UserRole.PARENT]
        
        # Create other entities
        classes = create_classes(db, teachers)
        enrollments = create_enrollments(db, students, classes)
        badges = create_badges(db)
        lessons = create_lessons(db, teachers, classes, badges)
        xp_transactions = create_xp_transactions(db, students)
        user_badges = create_user_badges(db, students, badges)
        consent_records = create_consent_records(db, students, parents)
        
        print("\n" + "="*50)
        print("✅ Database seeding completed successfully!")
        print("="*50)
        print("\n📊 Summary:")
        print(f"  - Users: {len(users)}")
        print(f"    - Admin: 1")
        print(f"    - Teachers: {len(teachers)}")
        print(f"    - Students: {len(students)}")
        print(f"    - Parents: {len(parents)}")
        print(f"  - Classes: {len(classes)}")
        print(f"  - Enrollments: {len(enrollments)}")
        print(f"  - Lessons: {len(lessons)}")
        print(f"  - Badges: {len(badges)}")
        print(f"  - User Badges: {len(user_badges)}")
        print(f"  - XP Transactions: {len(xp_transactions)}")
        print(f"  - Consent Records: {len(consent_records)}")
        
        print("\n🔐 Login Credentials:")
        print("  Admin: admin@toolboxai.com / Admin123!")
        print("  Teacher: jane.smith@school.edu / Teacher123!")
        print("  Student: alex.johnson@student.edu / Student123!")
        print("  Parent: robert.johnson@parent.edu / Parent123!")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()