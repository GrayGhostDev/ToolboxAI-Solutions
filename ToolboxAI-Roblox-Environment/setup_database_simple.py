#!/usr/bin/env python3
"""
Simple Database Setup Script for ToolboxAI Platform
Uses only psycopg2 for compatibility
"""

import psycopg2
import psycopg2.extras
import os
import sys
import hashlib
from datetime import datetime, timedelta
import uuid

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'eduplatform'),
    'password': os.getenv('DB_PASSWORD', 'eduplatform2024'),
    'database': os.getenv('DB_NAME', 'educational_platform_dev')
}

def create_user_and_database():
    """Create database user and database if they don't exist"""
    print("🔧 Creating database user and database...")
    
    try:
        # Connect as superuser to create user and database
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database='postgres'
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Create user if not exists
        try:
            cur.execute(f"""
                CREATE USER {DB_CONFIG['user']} 
                WITH PASSWORD '{DB_CONFIG['password']}' 
                CREATEDB LOGIN;
            """)
            print(f"✅ Created user: {DB_CONFIG['user']}")
        except psycopg2.errors.DuplicateObject:
            print(f"ℹ️  User {DB_CONFIG['user']} already exists")
        
        # Create database if not exists
        try:
            cur.execute(f"CREATE DATABASE {DB_CONFIG['database']} OWNER {DB_CONFIG['user']};")
            print(f"✅ Created database: {DB_CONFIG['database']}")
        except psycopg2.errors.DuplicateDatabase:
            print(f"ℹ️  Database {DB_CONFIG['database']} already exists")
        
        # Grant privileges
        cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_CONFIG['database']} TO {DB_CONFIG['user']};")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create user/database: {e}")
        print("ℹ️  Make sure you have PostgreSQL superuser access")
        return False

def deploy_basic_schema():
    """Deploy basic schema for dashboard"""
    print("📋 Deploying basic database schema...")
    
    schema_sql = """
    -- Enable required extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    
    -- Schools table
    CREATE TABLE IF NOT EXISTS schools (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        name VARCHAR(200) NOT NULL,
        address VARCHAR(500) NOT NULL,
        city VARCHAR(100) NOT NULL,
        state VARCHAR(50) NOT NULL,
        zip_code VARCHAR(10) NOT NULL,
        phone VARCHAR(20),
        email VARCHAR(100),
        principal_name VARCHAR(100),
        district VARCHAR(200),
        max_students INTEGER DEFAULT 500,
        student_count INTEGER DEFAULT 0,
        teacher_count INTEGER DEFAULT 0,
        class_count INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT true,
        logo_url VARCHAR(500),
        website VARCHAR(500),
        founded_year INTEGER,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Dashboard users table
    CREATE TABLE IF NOT EXISTS dashboard_users (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        username VARCHAR(100) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        role VARCHAR(20) NOT NULL DEFAULT 'student',
        school_id VARCHAR(36) REFERENCES schools(id),
        grade_level INTEGER,
        phone VARCHAR(20),
        address TEXT,
        emergency_contact_name VARCHAR(100),
        emergency_contact_phone VARCHAR(20),
        is_active BOOLEAN DEFAULT true,
        is_verified BOOLEAN DEFAULT false,
        profile_picture_url VARCHAR(500),
        last_login TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Classes table
    CREATE TABLE IF NOT EXISTS classes (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        name VARCHAR(200) NOT NULL,
        code VARCHAR(50) UNIQUE NOT NULL,
        description TEXT,
        subject VARCHAR(100) NOT NULL,
        grade_level INTEGER NOT NULL,
        teacher_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
        school_id VARCHAR(36) REFERENCES schools(id),
        schedule VARCHAR(200),
        start_date DATE,
        end_date DATE,
        max_students INTEGER DEFAULT 30,
        student_count INTEGER DEFAULT 0,
        room VARCHAR(50),
        is_active BOOLEAN DEFAULT true,
        syllabus_url VARCHAR(500),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Class students enrollment
    CREATE TABLE IF NOT EXISTS class_students (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        class_id VARCHAR(36) REFERENCES classes(id) ON DELETE CASCADE,
        student_id VARCHAR(36) REFERENCES dashboard_users(id) ON DELETE CASCADE,
        enrolled_at TIMESTAMPTZ DEFAULT NOW(),
        status VARCHAR(20) DEFAULT 'active',
        grade DECIMAL(5,2),
        attendance_rate DECIMAL(5,2) DEFAULT 0,
        UNIQUE(class_id, student_id)
    );
    
    -- Assignments table
    CREATE TABLE IF NOT EXISTS assignments (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        title VARCHAR(300) NOT NULL,
        description TEXT,
        type VARCHAR(50) NOT NULL DEFAULT 'assignment',
        subject VARCHAR(100) NOT NULL,
        due_date TIMESTAMPTZ,
        points INTEGER DEFAULT 100,
        class_id VARCHAR(36) REFERENCES classes(id) NOT NULL,
        teacher_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
        status VARCHAR(20) DEFAULT 'active',
        instructions TEXT,
        resources JSONB DEFAULT '[]',
        rubric JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Submissions table
    CREATE TABLE IF NOT EXISTS submissions (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        assignment_id VARCHAR(36) REFERENCES assignments(id) ON DELETE CASCADE,
        student_id VARCHAR(36) REFERENCES dashboard_users(id) ON DELETE CASCADE,
        content TEXT,
        file_urls JSONB DEFAULT '[]',
        status VARCHAR(20) DEFAULT 'draft',
        grade DECIMAL(5,2),
        feedback TEXT,
        submitted_at TIMESTAMPTZ,
        graded_at TIMESTAMPTZ,
        progress INTEGER DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(assignment_id, student_id)
    );
    
    -- Student progress table
    CREATE TABLE IF NOT EXISTS student_progress (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        student_id VARCHAR(36) REFERENCES dashboard_users(id) ON DELETE CASCADE UNIQUE,
        xp_points INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        streak_days INTEGER DEFAULT 0,
        total_badges INTEGER DEFAULT 0,
        rank_position INTEGER DEFAULT 0,
        grade_level INTEGER,
        gpa DECIMAL(3,2),
        attendance_rate DECIMAL(5,2) DEFAULT 0,
        last_activity TIMESTAMPTZ DEFAULT NOW(),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Student achievements table
    CREATE TABLE IF NOT EXISTS achievements (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        name VARCHAR(200) NOT NULL,
        description TEXT,
        icon_url VARCHAR(500),
        xp_reward INTEGER DEFAULT 0,
        badge_type VARCHAR(50) DEFAULT 'standard',
        requirements JSONB DEFAULT '{}',
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    CREATE TABLE IF NOT EXISTS student_achievements (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        student_id VARCHAR(36) REFERENCES dashboard_users(id) ON DELETE CASCADE,
        achievement_id VARCHAR(36) REFERENCES achievements(id) ON DELETE CASCADE,
        earned_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(student_id, achievement_id)
    );
    
    -- Student activity table
    CREATE TABLE IF NOT EXISTS student_activity (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        student_id VARCHAR(36) REFERENCES dashboard_users(id) ON DELETE CASCADE,
        type VARCHAR(50) NOT NULL,
        description TEXT NOT NULL,
        xp_earned INTEGER DEFAULT 0,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- System events table
    CREATE TABLE IF NOT EXISTS system_events (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        event_type VARCHAR(100) NOT NULL,
        message TEXT NOT NULL,
        severity VARCHAR(20) DEFAULT 'info',
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- API logs table
    CREATE TABLE IF NOT EXISTS api_logs (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        endpoint VARCHAR(500) NOT NULL,
        method VARCHAR(10) NOT NULL,
        status_code INTEGER NOT NULL,
        response_time INTEGER NOT NULL,
        user_id VARCHAR(36),
        ip_address INET,
        user_agent TEXT,
        timestamp TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Lessons table
    CREATE TABLE IF NOT EXISTS lessons (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        title VARCHAR(300) NOT NULL,
        subject VARCHAR(100) NOT NULL,
        class_id VARCHAR(36) REFERENCES classes(id) NOT NULL,
        teacher_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
        content TEXT,
        objectives JSONB DEFAULT '[]',
        resources JSONB DEFAULT '[]',
        scheduled_at TIMESTAMPTZ,
        duration_minutes INTEGER DEFAULT 50,
        status VARCHAR(20) DEFAULT 'draft',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Messages table for parent-teacher communication
    CREATE TABLE IF NOT EXISTS messages (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        sender_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
        recipient_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
        subject VARCHAR(300) NOT NULL,
        body TEXT NOT NULL,
        is_read BOOLEAN DEFAULT false,
        thread_id VARCHAR(36),
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Parent-children relationships
    CREATE TABLE IF NOT EXISTS parent_children (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        parent_id VARCHAR(36) REFERENCES dashboard_users(id) ON DELETE CASCADE,
        student_id VARCHAR(36) REFERENCES dashboard_users(id) ON DELETE CASCADE,
        relationship VARCHAR(50) DEFAULT 'parent',
        is_primary BOOLEAN DEFAULT false,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(parent_id, student_id)
    );
    
    -- Attendance tracking
    CREATE TABLE IF NOT EXISTS attendance (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        student_id VARCHAR(36) REFERENCES dashboard_users(id) ON DELETE CASCADE,
        class_id VARCHAR(36) REFERENCES classes(id),
        date DATE NOT NULL,
        status VARCHAR(20) DEFAULT 'present',
        notes TEXT,
        recorded_by VARCHAR(36) REFERENCES dashboard_users(id),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(student_id, class_id, date)
    );
    
    -- Compliance records
    CREATE TABLE IF NOT EXISTS compliance_records (
        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
        type VARCHAR(50) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        description TEXT,
        metadata JSONB DEFAULT '{}',
        reviewed_by VARCHAR(36) REFERENCES dashboard_users(id),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Execute schema SQL
        cur.execute(schema_sql)
        conn.commit()
        
        cur.close()
        conn.close()
        print("✅ Basic schema deployed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to deploy schema: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    print("👥 Creating sample data...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Hash password for demo users
        demo_password = "demo123"
        password_hash = hashlib.sha256(demo_password.encode()).hexdigest()
        
        # Create sample school
        cur.execute("""
            INSERT INTO schools (name, address, city, state, zip_code, principal_name)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, ('Demo Elementary School', '123 Main St', 'Springfield', 'IL', '62701', 'Dr. Jane Smith'))
        
        school_result = cur.fetchone()
        if school_result:
            school_id = school_result['id']
        else:
            # Get existing school
            cur.execute("SELECT id FROM schools LIMIT 1")
            result = cur.fetchone()
            school_id = result['id'] if result else None
        
        # Create sample users
        users_data = [
            ('demo_admin', 'admin@demo.com', 'Admin', 'User', 'admin', None),
            ('demo_teacher', 'teacher@demo.com', 'Sarah', 'Johnson', 'teacher', None),
            ('demo_student', 'student@demo.com', 'Alex', 'Wilson', 'student', 7),
            ('jane_student', 'jane@demo.com', 'Jane', 'Smith', 'student', 7)
        ]
        
        user_ids = {}
        for username, email, first_name, last_name, role, grade_level in users_data:
            try:
                cur.execute("""
                    INSERT INTO dashboard_users 
                    (username, email, password_hash, first_name, last_name, role, grade_level, school_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO UPDATE SET updated_at = NOW()
                    RETURNING id
                """, (username, email, password_hash, first_name, last_name, role, grade_level, school_id))
                
                result = cur.fetchone()
                if result:
                    user_ids[role] = result['id']
                    print(f"✅ Created user: {username} (role: {role})")
            except Exception as e:
                print(f"⚠️  Warning creating user {username}: {e}")
        
        # Create sample classes
        if 'teacher' in user_ids:
            classes_data = [
                ('Math 7th Grade', 'MATH7A', 'Mathematics', 7),
                ('Science 7th Grade', 'SCI7A', 'Science', 7)
            ]
            
            class_ids = []
            for name, code, subject, grade_level in classes_data:
                try:
                    cur.execute("""
                        INSERT INTO classes 
                        (name, code, subject, grade_level, teacher_id, school_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (code) DO UPDATE SET updated_at = NOW()
                        RETURNING id
                    """, (name, code, subject, grade_level, user_ids['teacher'], school_id))
                    
                    result = cur.fetchone()
                    if result:
                        class_ids.append(result['id'])
                        print(f"✅ Created class: {name}")
                except Exception as e:
                    print(f"⚠️  Warning creating class {name}: {e}")
            
            # Enroll students in classes
            student_id = user_ids.get('student')
            if student_id and class_ids:
                for class_id in class_ids:
                    try:
                        cur.execute("""
                            INSERT INTO class_students (class_id, student_id)
                            VALUES (%s, %s)
                            ON CONFLICT (class_id, student_id) DO NOTHING
                        """, (class_id, student_id))
                    except Exception as e:
                        print(f"⚠️  Warning enrolling student: {e}")
                
                print(f"✅ Enrolled student in {len(class_ids)} classes")
            
            # Create sample assignments
            if class_ids:
                assignments_data = [
                    ('Algebra Basics Quiz', 'quiz', 'Mathematics', class_ids[0]),
                    ('Solar System Project', 'project', 'Science', class_ids[1] if len(class_ids) > 1 else class_ids[0])
                ]
                
                for title, assignment_type, subject, class_id in assignments_data:
                    try:
                        due_date = datetime.now() + timedelta(days=7)
                        cur.execute("""
                            INSERT INTO assignments 
                            (title, type, subject, due_date, class_id, teacher_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (title, assignment_type, subject, due_date, class_id, user_ids['teacher']))
                        print(f"✅ Created assignment: {title}")
                    except Exception as e:
                        print(f"⚠️  Warning creating assignment {title}: {e}")
        
        # Create student progress
        if 'student' in user_ids:
            try:
                cur.execute("""
                    INSERT INTO student_progress 
                    (student_id, xp_points, level, streak_days, total_badges, rank_position)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (student_id) DO UPDATE SET 
                        xp_points = EXCLUDED.xp_points,
                        updated_at = NOW()
                """, (user_ids['student'], 1250, 5, 3, 8, 15))
                print("✅ Created student progress data")
            except Exception as e:
                print(f"⚠️  Warning creating progress data: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Sample data created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        return False

def verify_setup():
    """Verify the database setup"""
    print("🔍 Verifying database setup...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Check tables exist
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        table_names = [row['table_name'] for row in tables]
        required_tables = ['dashboard_users', 'schools', 'classes', 'assignments', 'class_students']
        
        print(f"📊 Found {len(table_names)} tables:")
        for table in table_names[:10]:  # Show first 10
            print(f"   - {table}")
        if len(table_names) > 10:
            print(f"   ... and {len(table_names) - 10} more")
        
        missing_tables = [t for t in required_tables if t not in table_names]
        if missing_tables:
            print(f"⚠️  Missing required tables: {missing_tables}")
        else:
            print("✅ All required tables present")
        
        # Check users
        cur.execute("SELECT COUNT(*) as count FROM dashboard_users")
        user_count = cur.fetchone()['count']
        print(f"👥 Users in database: {user_count}")
        
        if user_count > 0:
            cur.execute("SELECT username, role FROM dashboard_users LIMIT 5")
            users = cur.fetchall()
            for user in users:
                print(f"   - {user['username']} ({user['role']})")
        
        # Check classes
        cur.execute("SELECT COUNT(*) as count FROM classes")
        class_count = cur.fetchone()['count']
        print(f"🎓 Classes in database: {class_count}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 ToolboxAI Platform - Simple Database Setup")
    print("=" * 60)
    
    # Step 1: Create user and database
    if not create_user_and_database():
        print("❌ Failed to create user/database. Exiting.")
        return 1
    
    # Step 2: Deploy basic schema
    if not deploy_basic_schema():
        print("❌ Failed to deploy schema. Exiting.")
        return 1
    
    # Step 3: Create sample data
    if not create_sample_data():
        print("❌ Failed to create sample data. Exiting.")
        return 1
    
    # Step 4: Verify setup
    if not verify_setup():
        print("❌ Database verification failed. Exiting.")
        return 1
    
    print("\n🎉 Database setup completed successfully!")
    print("\nDemo Credentials:")
    print("  Admin:   username=demo_admin,   password=demo123")
    print("  Teacher: username=demo_teacher, password=demo123")
    print("  Student: username=demo_student, password=demo123")
    print("\nNow you can run the verification test again:")
    print("  python test_comprehensive_verification.py --verbose")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)