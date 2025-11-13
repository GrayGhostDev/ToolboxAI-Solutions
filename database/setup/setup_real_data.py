#!/usr/bin/env python3
"""
Setup Real Data for ToolboxAI Educational Platform
Creates actual database with real user accounts and educational content.
"""

import hashlib
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "grayghostdata",
    "password": "grayghostdata",
}


def create_database():
    """Create the educational_platform database if it doesn't exist."""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database="postgres",
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'educational_platform'")
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("CREATE DATABASE educational_platform")
            print("✅ Created database: educational_platform")
        else:
            print("ℹ️  Database educational_platform already exists")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False


def setup_schema():
    """Set up the database schema for the educational platform."""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database="educational_platform",
        )
        cursor = conn.cursor()

        # Create users table with all necessary fields
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                display_name VARCHAR(200),
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'teacher', 'student', 'parent')),
                school_id INTEGER,
                class_ids INTEGER[],
                is_active BOOLEAN DEFAULT true,
                is_verified BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                avatar_url TEXT,
                bio TEXT,
                preferences JSONB DEFAULT '{}'::jsonb
            )
        """
        )

        # Create schools table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schools (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                address TEXT,
                city VARCHAR(100),
                state VARCHAR(50),
                country VARCHAR(100),
                postal_code VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create classes table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS classes (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                subject VARCHAR(100),
                grade_level INTEGER,
                teacher_id INTEGER REFERENCES users(id),
                school_id INTEGER REFERENCES schools(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create courses table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                subject VARCHAR(100),
                grade_level INTEGER,
                teacher_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_published BOOLEAN DEFAULT false
            )
        """
        )

        # Create assignments table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS assignments (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                course_id INTEGER REFERENCES courses(id),
                class_id INTEGER REFERENCES classes(id),
                assigned_by INTEGER REFERENCES users(id),
                due_date TIMESTAMP,
                points_possible INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create student_progress table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS student_progress (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES users(id),
                course_id INTEGER REFERENCES courses(id),
                assignment_id INTEGER REFERENCES assignments(id),
                progress_percentage DECIMAL(5,2),
                score DECIMAL(5,2),
                xp_earned INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, course_id, assignment_id)
            )
        """
        )

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Database schema created successfully")
        return True

    except Exception as e:
        print(f"❌ Error setting up schema: {e}")
        return False


def hash_password(password):
    """Hash a password for storing in the database."""
    # In production, use bcrypt or similar
    return hashlib.sha256(password.encode()).hexdigest()


def create_users():
    """Create real user accounts."""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database="educational_platform",
        )
        cursor = conn.cursor()

        # Create schools first
        schools = [
            ("Lincoln High School", "123 Main St", "Springfield", "IL", "USA", "62701"),
            ("Washington Academy", "456 Oak Ave", "Portland", "OR", "USA", "97201"),
        ]

        school_ids = []
        for school in schools:
            cursor.execute(
                """
                INSERT INTO schools (name, address, city, state, country, postal_code)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
            """,
                school,
            )
            result = cursor.fetchone()
            if result:
                school_ids.append(result[0])

        # Get existing school IDs if none were created
        if not school_ids:
            cursor.execute("SELECT id FROM schools LIMIT 2")
            school_ids = [row[0] for row in cursor.fetchall()]

        # Create users
        users = [
            # Admin
            (
                "admin",
                "admin@toolboxai.com",
                "Admin123!",
                "System",
                "Administrator",
                "Admin",
                "admin",
                None,
            ),
            # Teachers
            (
                "john_teacher",
                "john.smith@school.edu",
                "Teacher123!",
                "John",
                "Smith",
                "Mr. Smith",
                "teacher",
                school_ids[0] if school_ids else None,
            ),
            (
                "jane_teacher",
                "jane.doe@school.edu",
                "Teacher123!",
                "Jane",
                "Doe",
                "Ms. Doe",
                "teacher",
                school_ids[0] if school_ids else None,
            ),
            # Students
            (
                "alex_student",
                "alex.johnson@student.edu",
                "Student123!",
                "Alex",
                "Johnson",
                "Alex",
                "student",
                school_ids[0] if school_ids else None,
            ),
            (
                "maria_student",
                "maria.garcia@student.edu",
                "Student123!",
                "Maria",
                "Garcia",
                "Maria",
                "student",
                school_ids[0] if school_ids else None,
            ),
            # Parents
            (
                "robert_parent",
                "robert.johnson@parent.com",
                "Parent123!",
                "Robert",
                "Johnson",
                "Mr. Johnson",
                "parent",
                None,
            ),
        ]

        created_users = []
        for user_data in users:
            username, email, password, first_name, last_name, display_name, role, school_id = (
                user_data
            )

            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, first_name, last_name, display_name, role, school_id, is_active, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true, true)
                ON CONFLICT (username) DO UPDATE
                SET email = EXCLUDED.email,
                    password_hash = EXCLUDED.password_hash,
                    is_active = true,
                    is_verified = true
                RETURNING id, username, role
            """,
                (
                    username,
                    email,
                    hash_password(password),
                    first_name,
                    last_name,
                    display_name,
                    role,
                    school_id,
                ),
            )

            result = cursor.fetchone()
            if result:
                created_users.append(result)
                print(f"✅ Created/Updated user: {result[1]} ({result[2]})")

        # Create classes
        if created_users and school_ids:
            teacher_ids = [u[0] for u in created_users if u[2] == "teacher"]

            if teacher_ids:
                classes = [
                    ("Mathematics 101", "Mathematics", 9, teacher_ids[0], school_ids[0]),
                    (
                        "Science 201",
                        "Science",
                        10,
                        teacher_ids[1] if len(teacher_ids) > 1 else teacher_ids[0],
                        school_ids[0],
                    ),
                ]

                for class_data in classes:
                    cursor.execute(
                        """
                        INSERT INTO classes (name, subject, grade_level, teacher_id, school_id)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """,
                        class_data,
                    )

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Users created successfully")
        return True

    except Exception as e:
        print(f"❌ Error creating users: {e}")
        return False


def create_educational_content():
    """Create sample educational content."""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database="educational_platform",
        )
        cursor = conn.cursor()

        # Get teacher IDs
        cursor.execute("SELECT id FROM users WHERE role = 'teacher' LIMIT 2")
        teacher_ids = [row[0] for row in cursor.fetchall()]

        if teacher_ids:
            # Create courses
            courses = [
                (
                    "Introduction to Algebra",
                    "Learn the fundamentals of algebraic equations and problem solving",
                    "Mathematics",
                    9,
                    teacher_ids[0],
                ),
                (
                    "Basic Science Concepts",
                    "Explore the world of science through hands-on experiments",
                    "Science",
                    10,
                    teacher_ids[1] if len(teacher_ids) > 1 else teacher_ids[0],
                ),
            ]

            course_ids = []
            for course in courses:
                cursor.execute(
                    """
                    INSERT INTO courses (title, description, subject, grade_level, teacher_id, is_published)
                    VALUES (%s, %s, %s, %s, %s, true)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """,
                    course,
                )
                result = cursor.fetchone()
                if result:
                    course_ids.append(result[0])

            # Get class IDs
            cursor.execute("SELECT id FROM classes LIMIT 2")
            class_ids = [row[0] for row in cursor.fetchall()]

            # Create assignments
            if course_ids and class_ids:
                assignments = [
                    (
                        "Algebra Problem Set 1",
                        "Solve linear equations",
                        course_ids[0],
                        class_ids[0] if class_ids else None,
                        teacher_ids[0],
                        100,
                    ),
                    (
                        "Science Lab Report",
                        "Document your experiment findings",
                        course_ids[1] if len(course_ids) > 1 else course_ids[0],
                        class_ids[1] if len(class_ids) > 1 else class_ids[0],
                        teacher_ids[1] if len(teacher_ids) > 1 else teacher_ids[0],
                        150,
                    ),
                ]

                for assignment in assignments:
                    title, desc, course_id, class_id, teacher_id, points = assignment
                    due_date = datetime.now() + timedelta(days=7)

                    cursor.execute(
                        """
                        INSERT INTO assignments (title, description, course_id, class_id, assigned_by, due_date, points_possible)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """,
                        (title, desc, course_id, class_id, teacher_id, due_date, points),
                    )

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Educational content created successfully")
        return True

    except Exception as e:
        print(f"❌ Error creating educational content: {e}")
        return False


def verify_data():
    """Verify that data has been created."""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database="educational_platform",
        )
        cursor = conn.cursor()

        print("\n📊 Data Verification:")
        print("-" * 40)

        # Check users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"Users: {user_count}")

        # Show sample users
        cursor.execute(
            """
            SELECT username, email, role 
            FROM users 
            WHERE is_active = true 
            ORDER BY role, username
            LIMIT 10
        """
        )

        print("\n👥 Active Users:")
        for row in cursor.fetchall():
            print(f"  - {row[0]:20} ({row[2]:10}) - {row[1]}")

        # Check other tables
        tables = ["schools", "classes", "courses", "assignments"]
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table.capitalize()}: {count}")

        cursor.close()
        conn.close()

        print("\n✅ Data verification complete")
        return True

    except Exception as e:
        print(f"❌ Error verifying data: {e}")
        return False


def main():
    """Main function to set up the database with real data."""
    print("🚀 Setting up ToolboxAI Educational Platform Database")
    print("=" * 50)

    # Step 1: Create database
    if not create_database():
        return False

    # Step 2: Setup schema
    if not setup_schema():
        return False

    # Step 3: Create users
    if not create_users():
        return False

    # Step 4: Create content
    if not create_educational_content():
        return False

    # Step 5: Verify
    if not verify_data():
        return False

    print("\n🎉 Database setup completed successfully!")
    print("\n📝 Login Credentials:")
    print("-" * 40)
    print("Admin:   admin / Admin123!")
    print("Teacher: john_teacher / Teacher123!")
    print("Student: alex_student / Student123!")
    print("Parent:  robert_parent / Parent123!")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
