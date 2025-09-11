#!/usr/bin/env python3
"""
Complete Database Setup Script for ToolboxAI Platform

This script:
1. Creates the eduplatform user and educational_platform_dev database
2. Deploys all required schemas
3. Creates sample data for testing
4. Verifies the setup
"""

import asyncio
import asyncpg
import psycopg2
import os
import sys
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'eduplatform'),
    'password': os.getenv('DB_PASSWORD', 'eduplatform2024'),
    'database': os.getenv('DB_NAME', 'educational_platform_dev')
}

ADMIN_DB_CONFIG = {
    'host': DB_CONFIG['host'],
    'port': DB_CONFIG['port'],
    'database': 'postgres'  # Connect to postgres db as admin
}

class DatabaseSetup:
    """Handles complete database setup for ToolboxAI platform"""
    
    def __init__(self):
        self.db_config = DB_CONFIG
        self.admin_config = ADMIN_DB_CONFIG
        
    def create_user_and_database(self):
        """Create database user and database if they don't exist"""
        print("🔧 Creating database user and database...")
        
        try:
            # Connect as superuser to create user and database
            conn = psycopg2.connect(**self.admin_config)
            conn.autocommit = True
            cur = conn.cursor()
            
            # Create user if not exists
            try:
                cur.execute(f"""
                    CREATE USER {self.db_config['user']} 
                    WITH PASSWORD '{self.db_config['password']}' 
                    CREATEDB LOGIN;
                """)
                print(f"✅ Created user: {self.db_config['user']}")
            except psycopg2.errors.DuplicateObject:
                print(f"ℹ️  User {self.db_config['user']} already exists")
            
            # Create database if not exists
            try:
                cur.execute(f"CREATE DATABASE {self.db_config['database']} OWNER {self.db_config['user']};")
                print(f"✅ Created database: {self.db_config['database']}")
            except psycopg2.errors.DuplicateDatabase:
                print(f"ℹ️  Database {self.db_config['database']} already exists")
            
            # Grant privileges
            cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {self.db_config['database']} TO {self.db_config['user']};")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Failed to create user/database: {e}")
            print("ℹ️  Make sure you have PostgreSQL superuser access")
            return False
    
    async def deploy_schemas(self):
        """Deploy all database schemas"""
        print("📋 Deploying database schemas...")
        
        schema_files = [
            "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/database/schemas/01_core_schema.sql",
            "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/database/schemas/05_dashboard_schema.sql",
            "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/database/schemas/02_ai_agents_schema.sql",
            "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/database/schemas/03_lms_integration_schema.sql",
            "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/database/schemas/04_analytics_schema.sql"
        ]
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            for schema_file in schema_files:
                if Path(schema_file).exists():
                    print(f"📄 Deploying {Path(schema_file).name}...")
                    with open(schema_file, 'r') as f:
                        schema_sql = f.read()
                    
                    # Split by semicolon and execute each statement
                    statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
                    for statement in statements:
                        try:
                            await conn.execute(statement)
                        except Exception as e:
                            # Skip errors for CREATE TABLE IF NOT EXISTS, etc.
                            if "already exists" in str(e).lower():
                                continue
                            print(f"⚠️  Warning in {Path(schema_file).name}: {e}")
                    
                    print(f"✅ Deployed {Path(schema_file).name}")
                else:
                    print(f"⚠️  Schema file not found: {schema_file}")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Failed to deploy schemas: {e}")
            return False
    
    async def create_sample_data(self):
        """Create sample data for testing"""
        print("👥 Creating sample data...")
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Create sample schools
            schools_data = [
                {
                    'name': 'Lincoln Elementary School',
                    'address': '123 Main St',
                    'city': 'Springfield',
                    'state': 'IL',
                    'zip_code': '62701',
                    'principal_name': 'Dr. Jane Smith'
                },
                {
                    'name': 'Washington Middle School',
                    'address': '456 Oak Ave',
                    'city': 'Springfield',
                    'state': 'IL',
                    'zip_code': '62702',
                    'principal_name': 'Mr. John Doe'
                }
            ]
            
            school_ids = []
            for school in schools_data:
                school_id = await conn.fetchval("""
                    INSERT INTO schools (name, address, city, state, zip_code, principal_name)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (name) DO UPDATE SET updated_at = NOW()
                    RETURNING id
                """, school['name'], school['address'], school['city'], 
                    school['state'], school['zip_code'], school['principal_name'])
                school_ids.append(school_id)
            
            # Hash password for demo users
            demo_password = "demo123"
            password_hash = hashlib.sha256(demo_password.encode()).hexdigest()
            
            # Create sample users
            users_data = [
                {
                    'username': 'demo_admin',
                    'email': 'admin@demo.com',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'role': 'admin',
                    'school_id': school_ids[0] if school_ids else None
                },
                {
                    'username': 'demo_teacher',
                    'email': 'teacher@demo.com',
                    'first_name': 'Sarah',
                    'last_name': 'Johnson',
                    'role': 'teacher',
                    'school_id': school_ids[0] if school_ids else None
                },
                {
                    'username': 'demo_student',
                    'email': 'student@demo.com',
                    'first_name': 'Alex',
                    'last_name': 'Wilson',
                    'role': 'student',
                    'grade_level': 7,
                    'school_id': school_ids[0] if school_ids else None
                },
                {
                    'username': 'jane_student',
                    'email': 'jane@demo.com',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'role': 'student',
                    'grade_level': 7,
                    'school_id': school_ids[0] if school_ids else None
                }
            ]
            
            user_ids = []
            for user in users_data:
                try:
                    user_id = await conn.fetchval("""
                        INSERT INTO dashboard_users 
                        (username, email, password_hash, first_name, last_name, role, grade_level, school_id)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (username) DO UPDATE SET updated_at = NOW()
                        RETURNING id
                    """, user['username'], user['email'], password_hash, 
                        user['first_name'], user['last_name'], user['role'], 
                        user.get('grade_level'), user.get('school_id'))
                    user_ids.append(user_id)
                    print(f"✅ Created user: {user['username']} (role: {user['role']})")
                except Exception as e:
                    print(f"⚠️  Warning creating user {user['username']}: {e}")
            
            # Get teacher and student IDs
            teacher_id = None
            student_ids = []
            
            for i, user in enumerate(users_data):
                if user['role'] == 'teacher' and i < len(user_ids):
                    teacher_id = user_ids[i]
                elif user['role'] == 'student' and i < len(user_ids):
                    student_ids.append(user_ids[i])
            
            # Create sample classes
            if teacher_id:
                classes_data = [
                    {
                        'name': 'Math 7th Grade',
                        'code': 'MATH7A',
                        'subject': 'Mathematics',
                        'grade_level': 7,
                        'teacher_id': teacher_id,
                        'school_id': school_ids[0] if school_ids else None
                    },
                    {
                        'name': 'Science 7th Grade',
                        'code': 'SCI7A',
                        'subject': 'Science',
                        'grade_level': 7,
                        'teacher_id': teacher_id,
                        'school_id': school_ids[0] if school_ids else None
                    }
                ]
                
                class_ids = []
                for class_data in classes_data:
                    try:
                        class_id = await conn.fetchval("""
                            INSERT INTO classes 
                            (name, code, subject, grade_level, teacher_id, school_id)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT (code) DO UPDATE SET updated_at = NOW()
                            RETURNING id
                        """, class_data['name'], class_data['code'], class_data['subject'],
                            class_data['grade_level'], class_data['teacher_id'], class_data['school_id'])
                        class_ids.append(class_id)
                        print(f"✅ Created class: {class_data['name']}")
                    except Exception as e:
                        print(f"⚠️  Warning creating class {class_data['name']}: {e}")
                
                # Enroll students in classes
                for class_id in class_ids:
                    for student_id in student_ids:
                        try:
                            await conn.execute("""
                                INSERT INTO class_students (class_id, student_id)
                                VALUES ($1, $2)
                                ON CONFLICT (class_id, student_id) DO NOTHING
                            """, class_id, student_id)
                        except Exception as e:
                            print(f"⚠️  Warning enrolling student: {e}")
                
                print(f"✅ Enrolled {len(student_ids)} students in {len(class_ids)} classes")
            
            # Create sample assignments
            if class_ids and teacher_id:
                assignments_data = [
                    {
                        'title': 'Algebra Basics Quiz',
                        'type': 'quiz',
                        'subject': 'Mathematics',
                        'due_date': datetime.now() + timedelta(days=7),
                        'class_id': class_ids[0],
                        'teacher_id': teacher_id
                    },
                    {
                        'title': 'Solar System Project',
                        'type': 'project',
                        'subject': 'Science',
                        'due_date': datetime.now() + timedelta(days=14),
                        'class_id': class_ids[1] if len(class_ids) > 1 else class_ids[0],
                        'teacher_id': teacher_id
                    }
                ]
                
                for assignment in assignments_data:
                    try:
                        await conn.execute("""
                            INSERT INTO assignments 
                            (title, type, subject, due_date, class_id, teacher_id)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT DO NOTHING
                        """, assignment['title'], assignment['type'], assignment['subject'],
                            assignment['due_date'], assignment['class_id'], assignment['teacher_id'])
                        print(f"✅ Created assignment: {assignment['title']}")
                    except Exception as e:
                        print(f"⚠️  Warning creating assignment {assignment['title']}: {e}")
            
            # Create sample progress data
            for student_id in student_ids:
                try:
                    await conn.execute("""
                        INSERT INTO student_progress 
                        (student_id, xp_points, level, streak_days, total_badges, rank_position)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (student_id) DO UPDATE SET 
                            xp_points = EXCLUDED.xp_points,
                            updated_at = NOW()
                    """, student_id, 1250, 5, 3, 8, 15)
                except Exception as e:
                    print(f"⚠️  Warning creating progress data: {e}")
            
            await conn.close()
            print("✅ Sample data created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create sample data: {e}")
            return False
    
    async def verify_setup(self):
        """Verify the database setup"""
        print("🔍 Verifying database setup...")
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Check tables exist
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
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
            user_count = await conn.fetchval("SELECT COUNT(*) FROM dashboard_users")
            print(f"👥 Users in database: {user_count}")
            
            if user_count > 0:
                users = await conn.fetch("SELECT username, role FROM dashboard_users LIMIT 5")
                for user in users:
                    print(f"   - {user['username']} ({user['role']})")
            
            # Check classes
            class_count = await conn.fetchval("SELECT COUNT(*) FROM classes")
            print(f"🎓 Classes in database: {class_count}")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Database verification failed: {e}")
            return False

async def main():
    """Main setup function"""
    print("🚀 ToolboxAI Platform - Complete Database Setup")
    print("=" * 60)
    
    setup = DatabaseSetup()
    
    # Step 1: Create user and database
    if not setup.create_user_and_database():
        print("❌ Failed to create user/database. Exiting.")
        return 1
    
    # Step 2: Deploy schemas
    if not await setup.deploy_schemas():
        print("❌ Failed to deploy schemas. Exiting.")
        return 1
    
    # Step 3: Create sample data
    if not await setup.create_sample_data():
        print("❌ Failed to create sample data. Exiting.")
        return 1
    
    # Step 4: Verify setup
    if not await setup.verify_setup():
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
    exit_code = asyncio.run(main())
    sys.exit(exit_code)