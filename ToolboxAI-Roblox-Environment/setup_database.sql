-- ============================================================================
-- ToolboxAI Platform Database Setup
-- ============================================================================

-- Create user and database if needed (run with superuser privileges)
-- CREATE USER eduplatform WITH PASSWORD 'eduplatform2024' CREATEDB LOGIN;
-- CREATE DATABASE educational_platform_dev OWNER eduplatform;
-- GRANT ALL PRIVILEGES ON DATABASE educational_platform_dev TO eduplatform;

-- Connect to educational_platform_dev database and run the rest

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

-- ============================================================================
-- SAMPLE DATA INSERTION
-- ============================================================================

-- Insert sample school
INSERT INTO schools (name, address, city, state, zip_code, principal_name) 
VALUES ('Demo Elementary School', '123 Main St', 'Springfield', 'IL', '62701', 'Dr. Jane Smith')
ON CONFLICT DO NOTHING;

-- Insert demo users with SHA256 hashed password for "demo123"
INSERT INTO dashboard_users (username, email, password_hash, first_name, last_name, role, grade_level, school_id) VALUES
('demo_admin', 'admin@demo.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Admin', 'User', 'admin', NULL, (SELECT id FROM schools LIMIT 1)),
('demo_teacher', 'teacher@demo.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Sarah', 'Johnson', 'teacher', NULL, (SELECT id FROM schools LIMIT 1)),
('demo_student', 'student@demo.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Alex', 'Wilson', 'student', 7, (SELECT id FROM schools LIMIT 1)),
('jane_student', 'jane@demo.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Jane', 'Smith', 'student', 7, (SELECT id FROM schools LIMIT 1))
ON CONFLICT (username) DO UPDATE SET updated_at = NOW();

-- Insert sample classes
INSERT INTO classes (name, code, subject, grade_level, teacher_id, school_id) VALUES
('Math 7th Grade', 'MATH7A', 'Mathematics', 7, (SELECT id FROM dashboard_users WHERE username = 'demo_teacher'), (SELECT id FROM schools LIMIT 1)),
('Science 7th Grade', 'SCI7A', 'Science', 7, (SELECT id FROM dashboard_users WHERE username = 'demo_teacher'), (SELECT id FROM schools LIMIT 1))
ON CONFLICT (code) DO UPDATE SET updated_at = NOW();

-- Enroll students in classes
INSERT INTO class_students (class_id, student_id) VALUES
((SELECT id FROM classes WHERE code = 'MATH7A'), (SELECT id FROM dashboard_users WHERE username = 'demo_student')),
((SELECT id FROM classes WHERE code = 'SCI7A'), (SELECT id FROM dashboard_users WHERE username = 'demo_student')),
((SELECT id FROM classes WHERE code = 'MATH7A'), (SELECT id FROM dashboard_users WHERE username = 'jane_student')),
((SELECT id FROM classes WHERE code = 'SCI7A'), (SELECT id FROM dashboard_users WHERE username = 'jane_student'))
ON CONFLICT (class_id, student_id) DO NOTHING;

-- Insert sample assignments
INSERT INTO assignments (title, type, subject, due_date, class_id, teacher_id) VALUES
('Algebra Basics Quiz', 'quiz', 'Mathematics', NOW() + INTERVAL '7 days', (SELECT id FROM classes WHERE code = 'MATH7A'), (SELECT id FROM dashboard_users WHERE username = 'demo_teacher')),
('Solar System Project', 'project', 'Science', NOW() + INTERVAL '14 days', (SELECT id FROM classes WHERE code = 'SCI7A'), (SELECT id FROM dashboard_users WHERE username = 'demo_teacher'));

-- Insert student progress
INSERT INTO student_progress (student_id, xp_points, level, streak_days, total_badges, rank_position) VALUES
((SELECT id FROM dashboard_users WHERE username = 'demo_student'), 1250, 5, 3, 8, 15),
((SELECT id FROM dashboard_users WHERE username = 'jane_student'), 980, 4, 2, 5, 22)
ON CONFLICT (student_id) DO UPDATE SET 
    xp_points = EXCLUDED.xp_points,
    updated_at = NOW();

-- Insert sample achievements
INSERT INTO achievements (name, description, xp_reward, badge_type) VALUES
('First Login', 'Welcome to ToolboxAI!', 50, 'welcome'),
('Quiz Master', 'Complete 5 quizzes with 90% or higher', 200, 'academic'),
('Streak Champion', 'Maintain a 7-day learning streak', 300, 'engagement');

-- Grant achievements to students
INSERT INTO student_achievements (student_id, achievement_id) VALUES
((SELECT id FROM dashboard_users WHERE username = 'demo_student'), (SELECT id FROM achievements WHERE name = 'First Login')),
((SELECT id FROM dashboard_users WHERE username = 'jane_student'), (SELECT id FROM achievements WHERE name = 'First Login'))
ON CONFLICT (student_id, achievement_id) DO NOTHING;

-- Insert sample activity
INSERT INTO student_activity (student_id, type, description, xp_earned) VALUES
((SELECT id FROM dashboard_users WHERE username = 'demo_student'), 'quiz_completion', 'Completed Algebra Basics Quiz', 100),
((SELECT id FROM dashboard_users WHERE username = 'demo_student'), 'login', 'Daily login bonus', 25),
((SELECT id FROM dashboard_users WHERE username = 'jane_student'), 'assignment_submission', 'Submitted Science homework', 75);

-- Insert some sample lessons
INSERT INTO lessons (title, subject, class_id, teacher_id, scheduled_at) VALUES
('Introduction to Algebra', 'Mathematics', (SELECT id FROM classes WHERE code = 'MATH7A'), (SELECT id FROM dashboard_users WHERE username = 'demo_teacher'), NOW() + INTERVAL '1 day'),
('Solar System Overview', 'Science', (SELECT id FROM classes WHERE code = 'SCI7A'), (SELECT id FROM dashboard_users WHERE username = 'demo_teacher'), NOW() + INTERVAL '2 days');

-- Insert compliance records
INSERT INTO compliance_records (type, status, description) VALUES
('COPPA', 'compliant', 'Children''s Online Privacy Protection Act compliance verified'),
('FERPA', 'compliant', 'Family Educational Rights and Privacy Act compliance verified');

-- Insert some API logs for testing
INSERT INTO api_logs (endpoint, method, status_code, response_time, timestamp) VALUES
('/api/dashboard/data', 'GET', 200, 45, NOW() - INTERVAL '1 hour'),
('/api/dashboard/data', 'GET', 200, 38, NOW() - INTERVAL '30 minutes'),
('/auth/login', 'POST', 200, 120, NOW() - INTERVAL '2 hours');

-- Insert system events
INSERT INTO system_events (event_type, message, severity) VALUES
('system_startup', 'ToolboxAI platform started successfully', 'info'),
('user_registration', 'New user registered: demo_student', 'info'),
('database_backup', 'Daily database backup completed', 'info');

COMMIT;