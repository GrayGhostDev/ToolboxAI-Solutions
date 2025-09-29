# Terminal 4: Database and Integration Specialist

## CRITICAL: Setup Real Database with Production Data

### Your Role
You are the **Database and Integration Specialist**. Your mission is to set up the production database, populate it with real data, and ensure all services integrate properly.

### Immediate Tasks

#### 1. PostgreSQL Database Setup (HIGH PRIORITY)
```bash
# Start PostgreSQL if not running
pg_ctl start -D /usr/local/var/postgres

# Create database and user
psql postgres << 'EOF'
-- Drop existing database if exists
DROP DATABASE IF EXISTS toolboxai_db;
DROP USER IF EXISTS toolboxai_user;

-- Create production database
CREATE DATABASE toolboxai_db;
CREATE USER toolboxai_user WITH PASSWORD 'staging_password_2024';
GRANT ALL PRIVILEGES ON DATABASE toolboxai_db TO toolboxai_user;

-- Connect to the database
\c toolboxai_db

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
EOF
```

#### 2. Create Production Schema
```bash
cd database

# Create comprehensive schema
cat > schemas/02_production_schema.sql << 'EOF'
-- Production Database Schema
-- ToolBoxAI Educational Platform

-- Schools table
CREATE TABLE IF NOT EXISTS schools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(255),
    district VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table with real fields
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'teacher', 'student', 'parent')),
    school_id INTEGER REFERENCES schools(id) ON DELETE SET NULL,
    grade_level INTEGER,
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    subject VARCHAR(100),
    grade_level INTEGER,
    teacher_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Course enrollments (many-to-many)
CREATE TABLE IF NOT EXISTS course_enrollments (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'enrolled',
    UNIQUE(course_id, student_id)
);

-- Lessons table
CREATE TABLE IF NOT EXISTS lessons (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    content JSONB,
    order_index INTEGER,
    duration_minutes INTEGER,
    is_published BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI-generated content
CREATE TABLE IF NOT EXISTS generated_content (
    id SERIAL PRIMARY KEY,
    lesson_id INTEGER REFERENCES lessons(id) ON DELETE CASCADE,
    created_by_id INTEGER REFERENCES users(id),
    content_type VARCHAR(50),
    content_data JSONB NOT NULL,
    metadata JSONB,
    is_approved BOOLEAN DEFAULT false,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quizzes table
CREATE TABLE IF NOT EXISTS quizzes (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    lesson_id INTEGER REFERENCES lessons(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    total_points INTEGER DEFAULT 100,
    time_limit INTEGER, -- in minutes
    attempts_allowed INTEGER DEFAULT 1,
    created_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quiz questions
CREATE TABLE IF NOT EXISTS quiz_questions (
    id SERIAL PRIMARY KEY,
    quiz_id INTEGER REFERENCES quizzes(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL,
    options JSONB,
    correct_answer JSONB NOT NULL,
    points INTEGER DEFAULT 10,
    explanation TEXT,
    order_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quiz results
CREATE TABLE IF NOT EXISTS quiz_results (
    id SERIAL PRIMARY KEY,
    quiz_id INTEGER REFERENCES quizzes(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    score DECIMAL(5,2),
    total_points INTEGER,
    answers JSONB,
    time_taken INTEGER, -- in seconds
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(quiz_id, student_id, completed_at)
);

-- Student progress tracking
CREATE TABLE IF NOT EXISTS student_progress (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    lesson_id INTEGER REFERENCES lessons(id) ON DELETE CASCADE,
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    time_spent INTEGER DEFAULT 0, -- in seconds
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE(student_id, lesson_id)
);

-- Analytics events
CREATE TABLE IF NOT EXISTS analytics_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Roblox integration
CREATE TABLE IF NOT EXISTS roblox_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    roblox_user_id VARCHAR(100),
    game_instance_id VARCHAR(255),
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    session_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    message TEXT,
    data JSONB,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_school ON users(school_id);
CREATE INDEX idx_courses_teacher ON courses(teacher_id);
CREATE INDEX idx_courses_school ON courses(school_id);
CREATE INDEX idx_enrollments_student ON course_enrollments(student_id);
CREATE INDEX idx_enrollments_course ON course_enrollments(course_id);
CREATE INDEX idx_lessons_course ON lessons(course_id);
CREATE INDEX idx_progress_student ON student_progress(student_id);
CREATE INDEX idx_progress_lesson ON student_progress(lesson_id);
CREATE INDEX idx_analytics_user ON analytics_events(user_id);
CREATE INDEX idx_analytics_created ON analytics_events(created_at);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_schools_updated_at BEFORE UPDATE ON schools
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lessons_updated_at BEFORE UPDATE ON lessons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_quizzes_updated_at BEFORE UPDATE ON quizzes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EOF

# Apply schema
psql -U toolboxai_user -d toolboxai_db -f schemas/02_production_schema.sql
```

#### 3. Populate with Real Sample Data
```bash
# Create real data population script
cat > scripts/populate_real_data.py << 'EOF'
"""
Populate database with realistic sample data
"""
import asyncio
import random
from datetime import datetime, timedelta
from faker import Faker
import asyncpg
from passlib.context import CryptContext

fake = Faker()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def populate_database():
    # Connect to database
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='toolboxai_user',
        password='staging_password_2024',
        database='toolboxai_db'
    )
    
    try:
        # Create schools
        schools = []
        for i in range(5):
            school = await conn.fetchrow(
                """INSERT INTO schools (name, address, phone, email, district)
                VALUES ($1, $2, $3, $4, $5) RETURNING id""",
                f"{fake.city()} Elementary School",
                fake.address(),
                fake.phone_number(),
                fake.email(),
                f"District {i+1}"
            )
            schools.append(school['id'])
        
        print(f"Created {len(schools)} schools")
        
        # Create admin users
        admin_password = pwd_context.hash("admin123")
        admin = await conn.fetchrow(
            """INSERT INTO users (email, password_hash, full_name, role, school_id)
            VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            "admin@toolboxai.com",
            admin_password,
            "System Administrator",
            "admin",
            schools[0]
        )
        
        # Create teachers
        teachers = []
        teacher_password = pwd_context.hash("teacher123")
        for school_id in schools:
            for i in range(3):
                teacher = await conn.fetchrow(
                    """INSERT INTO users (email, password_hash, full_name, role, school_id)
                    VALUES ($1, $2, $3, $4, $5) RETURNING id""",
                    fake.email(),
                    teacher_password,
                    fake.name(),
                    "teacher",
                    school_id
                )
                teachers.append(teacher['id'])
        
        print(f"Created {len(teachers)} teachers")
        
        # Create students
        students = []
        student_password = pwd_context.hash("student123")
        for school_id in schools:
            for grade in range(1, 9):
                for i in range(20):
                    student = await conn.fetchrow(
                        """INSERT INTO users (email, password_hash, full_name, role, school_id, grade_level)
                        VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
                        fake.email(),
                        student_password,
                        fake.name(),
                        "student",
                        school_id,
                        grade
                    )
                    students.append(student['id'])
        
        print(f"Created {len(students)} students")
        
        # Create courses
        subjects = ['Mathematics', 'Science', 'English', 'History', 'Geography', 'Computer Science']
        courses = []
        
        for teacher_id in teachers:
            teacher_school = await conn.fetchval(
                "SELECT school_id FROM users WHERE id = $1", teacher_id
            )
            
            for grade in range(1, 9):
                subject = random.choice(subjects)
                course = await conn.fetchrow(
                    """INSERT INTO courses (title, description, subject, grade_level, teacher_id, school_id, start_date, end_date)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id""",
                    f"Grade {grade} {subject}",
                    f"Comprehensive {subject.lower()} curriculum for grade {grade}",
                    subject,
                    grade,
                    teacher_id,
                    teacher_school,
                    datetime.now().date(),
                    (datetime.now() + timedelta(days=180)).date()
                )
                courses.append((course['id'], grade, teacher_school))
        
        print(f"Created {len(courses)} courses")
        
        # Enroll students in courses
        enrollments = 0
        for student_id in students:
            student_data = await conn.fetchrow(
                "SELECT school_id, grade_level FROM users WHERE id = $1", student_id
            )
            
            # Find matching courses
            matching_courses = [c for c in courses if c[1] == student_data['grade_level'] and c[2] == student_data['school_id']]
            
            for course_id, _, _ in matching_courses[:4]:  # Enroll in 4 courses
                await conn.execute(
                    """INSERT INTO course_enrollments (course_id, student_id)
                    VALUES ($1, $2) ON CONFLICT DO NOTHING""",
                    course_id,
                    student_id
                )
                enrollments += 1
        
        print(f"Created {enrollments} enrollments")
        
        # Create lessons for each course
        lesson_count = 0
        for course_id, _, _ in courses:
            for week in range(1, 21):  # 20 weeks of lessons
                lesson = await conn.fetchrow(
                    """INSERT INTO lessons (course_id, title, description, order_index, duration_minutes, is_published)
                    VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
                    course_id,
                    f"Week {week}: {fake.catch_phrase()}",
                    fake.paragraph(),
                    week,
                    random.randint(30, 90),
                    week <= 10  # First 10 weeks published
                )
                lesson_count += 1
                
                # Add student progress for published lessons
                if week <= 10:
                    enrolled_students = await conn.fetch(
                        """SELECT student_id FROM course_enrollments WHERE course_id = $1""",
                        course_id
                    )
                    
                    for student in enrolled_students[:10]:  # Sample of students
                        progress = random.uniform(0, 100) if week < 10 else 100
                        await conn.execute(
                            """INSERT INTO student_progress (student_id, lesson_id, progress_percentage, time_spent)
                            VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING""",
                            student['student_id'],
                            lesson['id'],
                            progress,
                            random.randint(600, 3600)
                        )
        
        print(f"Created {lesson_count} lessons with progress tracking")
        
        # Create sample quizzes
        quiz_count = 0
        for course_id, _, _ in courses[:20]:  # Sample courses
            lessons = await conn.fetch(
                "SELECT id FROM lessons WHERE course_id = $1 LIMIT 5",
                course_id
            )
            
            for lesson in lessons:
                quiz = await conn.fetchrow(
                    """INSERT INTO quizzes (course_id, lesson_id, title, description, total_points, time_limit, created_by_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
                    course_id,
                    lesson['id'],
                    f"Quiz: {fake.catch_phrase()}",
                    "Test your understanding of the lesson material",
                    100,
                    30,
                    random.choice(teachers)
                )
                quiz_count += 1
                
                # Add questions
                for q in range(5):
                    await conn.execute(
                        """INSERT INTO quiz_questions (quiz_id, question_text, question_type, options, correct_answer, points)
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        quiz['id'],
                        fake.sentence() + "?",
                        "multiple_choice",
                        {"A": fake.word(), "B": fake.word(), "C": fake.word(), "D": fake.word()},
                        {"answer": "A"},
                        20
                    )
        
        print(f"Created {quiz_count} quizzes with questions")
        
        # Add sample analytics events
        event_types = ['login', 'lesson_view', 'quiz_start', 'quiz_complete', 'content_generated']
        for _ in range(1000):
            await conn.execute(
                """INSERT INTO analytics_events (user_id, event_type, event_data, session_id)
                VALUES ($1, $2, $3, $4)""",
                random.choice(students + teachers),
                random.choice(event_types),
                {"timestamp": datetime.now().isoformat()},
                fake.uuid4()
            )
        
        print("Created 1000 analytics events")
        
        print("\n✅ Database populated successfully!")
        print("\nSample login credentials:")
        print("Admin: admin@toolboxai.com / admin123")
        print("Teacher: Use any teacher email / teacher123")
        print("Student: Use any student email / student123")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(populate_database())
EOF

# Run population script
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
python database/scripts/populate_real_data.py
```

#### 4. Setup Alembic Migrations
```bash
cd database

# Initialize Alembic if not done
alembic init migrations

# Update alembic.ini
cat > alembic.ini << 'EOF'
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://toolboxai_user:staging_password_2024@localhost:5432/toolboxai_db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

# Create initial migration
alembic revision --autogenerate -m "Initial production schema"
alembic upgrade head
```

#### 5. Redis Setup for Caching
```bash
# Start Redis
redis-server --daemonize yes

# Configure Redis
redis-cli << 'EOF'
CONFIG SET requirepass staging_redis_2024
CONFIG SET maxmemory 256mb
CONFIG SET maxmemory-policy allkeys-lru
CONFIG REWRITE
EOF

# Test Redis connection
redis-cli -a staging_redis_2024 ping
```

#### 6. Database Monitoring Script
```bash
# Create monitoring script
cat > scripts/monitor_database.sh << 'EOF'
#!/bin/bash

echo "📊 Database Health Check"
echo "========================"

# Check PostgreSQL
echo -e "\n🐘 PostgreSQL Status:"
pg_isready -h localhost -p 5432

# Check database size
psql -U toolboxai_user -d toolboxai_db -c "
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'toolboxai_db';"

# Check table counts
psql -U toolboxai_user -d toolboxai_db -c "
SELECT 
    'Users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'Courses', COUNT(*) FROM courses
UNION ALL
SELECT 'Lessons', COUNT(*) FROM lessons
UNION ALL
SELECT 'Enrollments', COUNT(*) FROM course_enrollments
UNION ALL
SELECT 'Quiz Results', COUNT(*) FROM quiz_results
UNION ALL
SELECT 'Analytics Events', COUNT(*) FROM analytics_events;"

# Check Redis
echo -e "\n📦 Redis Status:"
redis-cli -a staging_redis_2024 ping
redis-cli -a staging_redis_2024 INFO keyspace

# Check connections
echo -e "\n🔌 Active Connections:"
psql -U toolboxai_user -d toolboxai_db -c "
SELECT COUNT(*) as active_connections 
FROM pg_stat_activity 
WHERE datname = 'toolboxai_db';"

echo -e "\n✅ Database health check complete!"
EOF

chmod +x scripts/monitor_database.sh
```

#### 7. Backup Script
```bash
# Create backup script
cat > scripts/backup_database.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/toolboxai_db_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

echo "🔄 Starting database backup..."
pg_dump -U toolboxai_user -d toolboxai_db -f $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "✅ Backup completed: $BACKUP_FILE"
    
    # Compress backup
    gzip $BACKUP_FILE
    echo "📦 Compressed: ${BACKUP_FILE}.gz"
    
    # Remove old backups (keep last 10)
    ls -t $BACKUP_DIR/*.gz | tail -n +11 | xargs rm -f
else
    echo "❌ Backup failed!"
    exit 1
fi
EOF

chmod +x scripts/backup_database.sh
```

## Communication Protocol
- Provide database credentials to Terminal 2
- Share schema with Terminal 3 for frontend models
- Coordinate with Terminal 5 for test data
- Update Terminal 1 when moving database files

## Success Metrics
✅ PostgreSQL running and accessible
✅ All tables created successfully
✅ Sample data populated
✅ Indexes optimized for performance
✅ Redis caching operational
✅ Backup system working
✅ Monitoring scripts functional
✅ No connection errors

## Notes
- Use realistic sample data
- Maintain referential integrity
- Optimize queries with indexes
- Regular backups scheduled
- Monitor performance metrics