#!/usr/bin/env python3
"""
Quick script to verify database contents after seeding
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db_session
from models import User, Class, Badge, Lesson, ClassEnrollment

def verify_database():
    print("✅ Verifying database contents...")
    
    with get_db_session() as db:
        user_count = db.query(User).count()
        class_count = db.query(Class).count()
        badge_count = db.query(Badge).count()
        lesson_count = db.query(Lesson).count()
        enrollment_count = db.query(ClassEnrollment).count()
        
        print(f"Users: {user_count}")
        print(f"Classes: {class_count}")
        print(f"Badges: {badge_count}")
        print(f"Lessons: {lesson_count}")
        print(f"Enrollments: {enrollment_count}")
        
        if user_count > 0 and class_count > 0 and badge_count > 0:
            print("✅ Database successfully populated!")
        else:
            print("❌ Database appears to be empty")

if __name__ == "__main__":
    verify_database()