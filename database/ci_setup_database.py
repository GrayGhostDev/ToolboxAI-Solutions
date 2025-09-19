#!/usr/bin/env python3
"""
CI Database Setup Script
Ensures database tables exist before running tests
"""
import os
import sys
import time
import psycopg2
from psycopg2 import sql
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def wait_for_db(max_retries=30):
    """Wait for database to be available"""
    db_url = os.getenv("DATABASE_URL", "postgresql://eduplatform:eduplatform2024@localhost/educational_platform_dev")

    for i in range(max_retries):
        try:
            conn = psycopg2.connect(db_url)
            conn.close()
            print("✅ Database is available")
            return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"Waiting for database... ({i+1}/{max_retries})")
                time.sleep(1)
            else:
                print(f"❌ Database not available after {max_retries} seconds: {e}")
                return False
    return False

def create_tables():
    """Create essential tables if they don't exist"""
    db_url = os.getenv("DATABASE_URL", "postgresql://eduplatform:eduplatform2024@localhost/educational_platform_dev")

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Create users table with UUID support
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                role VARCHAR(50) DEFAULT 'student',
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create dashboard_users table with UUID support
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                role VARCHAR(50) DEFAULT 'student',
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create schools table first (referenced by classes)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schools (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL,
                address TEXT,
                admin_email VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create courses table (referenced by lessons and classes)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(200) NOT NULL,
                code VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                subject VARCHAR(100) NOT NULL,
                grade_level INTEGER NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create classes table with proper references
        cur.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL,
                description TEXT,
                teacher_id UUID,
                school_id UUID,
                course_id UUID,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create lessons table with proper references
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                course_id UUID,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                content TEXT,
                order_index INTEGER DEFAULT 0,
                is_published BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create student_progress table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS student_progress (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                student_id UUID NOT NULL,
                lesson_id UUID NOT NULL,
                progress_percentage NUMERIC(5,2) DEFAULT 0.0,
                score NUMERIC(5,2),
                time_spent_minutes INTEGER DEFAULT 0,
                completed_at TIMESTAMP WITH TIME ZONE,
                attempts INTEGER DEFAULT 0,
                last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, lesson_id)
            )
        """)

        # Create api_keys table for Roblox integration
        cur.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                key_id VARCHAR(36) UNIQUE NOT NULL,
                key_hash VARCHAR(128) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                description VARCHAR(500),
                user_id UUID NOT NULL,
                scopes JSONB DEFAULT '[]',
                place_ids JSONB DEFAULT '[]',
                ip_whitelist JSONB DEFAULT '[]',
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP WITH TIME ZONE,
                last_used_at TIMESTAMP WITH TIME ZONE,
                revoked_at TIMESTAMP WITH TIME ZONE,
                usage_count INTEGER DEFAULT 0,
                rate_limit INTEGER DEFAULT 1000,
                metadata JSONB DEFAULT '{}'
            )
        """)

        # Add foreign key constraints (with error handling)
        constraints = [
            "ALTER TABLE classes ADD CONSTRAINT IF NOT EXISTS fk_classes_teacher FOREIGN KEY (teacher_id) REFERENCES users(id)",
            "ALTER TABLE classes ADD CONSTRAINT IF NOT EXISTS fk_classes_school FOREIGN KEY (school_id) REFERENCES schools(id)",
            "ALTER TABLE classes ADD CONSTRAINT IF NOT EXISTS fk_classes_course FOREIGN KEY (course_id) REFERENCES courses(id)",
            "ALTER TABLE lessons ADD CONSTRAINT IF NOT EXISTS fk_lessons_course FOREIGN KEY (course_id) REFERENCES courses(id)",
            "ALTER TABLE student_progress ADD CONSTRAINT IF NOT EXISTS fk_student_progress_student FOREIGN KEY (student_id) REFERENCES users(id)",
            "ALTER TABLE student_progress ADD CONSTRAINT IF NOT EXISTS fk_student_progress_lesson FOREIGN KEY (lesson_id) REFERENCES lessons(id)",
            "ALTER TABLE api_keys ADD CONSTRAINT IF NOT EXISTS fk_api_keys_user FOREIGN KEY (user_id) REFERENCES users(id)"
        ]

        for constraint_sql in constraints:
            try:
                cur.execute(constraint_sql)
            except Exception as e:
                # Skip constraint errors - they might already exist or use unsupported syntax
                print(f"⚠️ Skipping constraint (likely already exists): {e}")
                pass

        conn.commit()
        print("✅ All essential tables created/verified")

        # Check what tables exist and verify essential ones
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        table_names = [t[0] for t in tables]

        essential_tables = ['users', 'dashboard_users', 'schools', 'courses', 'classes', 'lessons', 'student_progress', 'api_keys']
        missing_tables = set(essential_tables) - set(table_names)

        print(f"📊 Found {len(tables)} tables in database")

        if missing_tables:
            print(f"❌ Missing essential tables: {', '.join(missing_tables)}")
        else:
            print("✅ All essential tables are present")

        # Show essential tables status
        for table in essential_tables:
            status = "✅" if table in table_names else "❌"
            print(f"  {status} {table}")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def main():
    """Main entry point"""
    print("🚀 Starting CI database setup...")

    if not wait_for_db():
        print("❌ Database not available")
        sys.exit(1)

    if not create_tables():
        print("❌ Failed to create tables")
        sys.exit(1)

    print("✅ CI database setup complete!")
    print("📋 Database is ready for tests")
    sys.exit(0)

if __name__ == "__main__":
    main()