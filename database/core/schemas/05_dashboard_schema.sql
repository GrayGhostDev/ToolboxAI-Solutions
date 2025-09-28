-- ============================================================================
-- Dashboard Backend Schema for ToolboxAI Educational Platform
-- ============================================================================
-- This file creates the dashboard-specific database schema
-- Tables: schools, classes, users (dashboard), assessments, lessons, etc.

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- SCHOOLS AND INSTITUTIONS
-- ============================================================================

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

-- ============================================================================
-- DASHBOARD USERS (separate from core users table)
-- ============================================================================

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

-- ============================================================================
-- CLASSES AND ENROLLMENT
-- ============================================================================

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

-- ============================================================================
-- ASSIGNMENTS AND SUBMISSIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS assignments (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL DEFAULT 'assignment',
    subject VARCHAR(100) NOT NULL,
    class_id VARCHAR(36) REFERENCES classes(id) NOT NULL,
    teacher_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
    due_date TIMESTAMPTZ,
    points INTEGER DEFAULT 100,
    status VARCHAR(20) DEFAULT 'active',
    instructions TEXT,
    materials_url VARCHAR(500),
    is_published BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS submissions (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    assignment_id VARCHAR(36) REFERENCES assignments(id) ON DELETE CASCADE,
    student_id VARCHAR(36) REFERENCES dashboard_users(id) ON DELETE CASCADE,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'submitted',
    grade DECIMAL(5,2),
    progress INTEGER DEFAULT 0,
    content TEXT,
    file_url VARCHAR(500),
    feedback TEXT,
    graded_at TIMESTAMPTZ,
    graded_by VARCHAR(36) REFERENCES dashboard_users(id),
    UNIQUE(assignment_id, student_id)
);

-- ============================================================================
-- LESSONS AND SCHEDULING
-- ============================================================================

CREATE TABLE IF NOT EXISTS lessons (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    subject VARCHAR(100) NOT NULL,
    class_id VARCHAR(36) REFERENCES classes(id) NOT NULL,
    teacher_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER DEFAULT 50,
    lesson_type VARCHAR(50) DEFAULT 'standard',
    content_url VARCHAR(500),
    roblox_world_id VARCHAR(100),
    learning_objectives TEXT[],
    materials TEXT[],
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- STUDENT PROGRESS AND ANALYTICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS student_progress (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    student_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
    class_id VARCHAR(36) REFERENCES classes(id),
    subject VARCHAR(100),
    grade_level INTEGER,
    xp_points INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    streak_days INTEGER DEFAULT 0,
    total_badges INTEGER DEFAULT 0,
    rank_position INTEGER DEFAULT 0,
    gpa DECIMAL(3,2),
    attendance_rate DECIMAL(5,2) DEFAULT 0,
    assignments_completed INTEGER DEFAULT 0,
    assignments_total INTEGER DEFAULT 0,
    last_activity TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, class_id)
);

CREATE TABLE IF NOT EXISTS student_activity (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    student_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    xp_earned INTEGER DEFAULT 0,
    class_id VARCHAR(36) REFERENCES classes(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- ACHIEVEMENTS AND GAMIFICATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS student_achievements (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    student_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
    achievement_id INTEGER REFERENCES achievements(id) NOT NULL,
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    class_id VARCHAR(36) REFERENCES classes(id),
    UNIQUE(student_id, achievement_id)
);

-- ============================================================================
-- ATTENDANCE TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS attendance (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    student_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
    class_id VARCHAR(36) REFERENCES classes(id) NOT NULL,
    lesson_id VARCHAR(36) REFERENCES lessons(id),
    date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'present',
    notes TEXT,
    recorded_by VARCHAR(36) REFERENCES dashboard_users(id),
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, class_id, date)
);

-- ============================================================================
-- MESSAGES AND COMMUNICATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    sender_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
    recipient_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(20) DEFAULT 'general',
    priority VARCHAR(20) DEFAULT 'normal',
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    class_id VARCHAR(36) REFERENCES classes(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- PARENT-CHILD RELATIONSHIPS
-- ============================================================================

CREATE TABLE IF NOT EXISTS parent_children (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    parent_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
    student_id VARCHAR(36) REFERENCES dashboard_users(id) NOT NULL,
    relationship VARCHAR(50) DEFAULT 'parent',
    is_primary BOOLEAN DEFAULT false,
    can_view_grades BOOLEAN DEFAULT true,
    can_view_attendance BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(parent_id, student_id)
);

-- ============================================================================
-- SYSTEM LOGS AND MONITORING
-- ============================================================================

CREATE TABLE IF NOT EXISTS system_events (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    event_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    user_id VARCHAR(36) REFERENCES dashboard_users(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    method VARCHAR(10) NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time DECIMAL(10,3),
    user_id VARCHAR(36) REFERENCES dashboard_users(id),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS compliance_records (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    details JSONB DEFAULT '{}',
    reviewed_by VARCHAR(36) REFERENCES dashboard_users(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- School indexes
CREATE INDEX IF NOT EXISTS idx_schools_district ON schools(district);
CREATE INDEX IF NOT EXISTS idx_schools_active ON schools(is_active) WHERE is_active = true;

-- User indexes
CREATE INDEX IF NOT EXISTS idx_dashboard_users_email ON dashboard_users(email) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_dashboard_users_role ON dashboard_users(role);
CREATE INDEX IF NOT EXISTS idx_dashboard_users_school ON dashboard_users(school_id);

-- Class indexes
CREATE INDEX IF NOT EXISTS idx_classes_teacher ON classes(teacher_id);
CREATE INDEX IF NOT EXISTS idx_classes_school ON classes(school_id);
CREATE INDEX IF NOT EXISTS idx_classes_subject_grade ON classes(subject, grade_level);
CREATE INDEX IF NOT EXISTS idx_class_students_class ON class_students(class_id);
CREATE INDEX IF NOT EXISTS idx_class_students_student ON class_students(student_id);

-- Assignment indexes
CREATE INDEX IF NOT EXISTS idx_assignments_class ON assignments(class_id);
CREATE INDEX IF NOT EXISTS idx_assignments_teacher ON assignments(teacher_id);
CREATE INDEX IF NOT EXISTS idx_assignments_due_date ON assignments(due_date);
CREATE INDEX IF NOT EXISTS idx_submissions_assignment ON submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_submissions_student ON submissions(student_id);

-- Lesson indexes
CREATE INDEX IF NOT EXISTS idx_lessons_class ON lessons(class_id);
CREATE INDEX IF NOT EXISTS idx_lessons_scheduled ON lessons(scheduled_at);

-- Progress indexes
CREATE INDEX IF NOT EXISTS idx_student_progress_student ON student_progress(student_id);
CREATE INDEX IF NOT EXISTS idx_student_progress_class ON student_progress(class_id);
CREATE INDEX IF NOT EXISTS idx_student_activity_student ON student_activity(student_id);

-- Attendance indexes
CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance(student_id, date);
CREATE INDEX IF NOT EXISTS idx_attendance_class_date ON attendance(class_id, date);

-- Message indexes
CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id, created_at DESC);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_dashboard_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to relevant tables
CREATE OR REPLACE TRIGGER update_schools_updated_at
    BEFORE UPDATE ON schools
    FOR EACH ROW EXECUTE FUNCTION update_dashboard_updated_at_column();

CREATE OR REPLACE TRIGGER update_dashboard_users_updated_at
    BEFORE UPDATE ON dashboard_users
    FOR EACH ROW EXECUTE FUNCTION update_dashboard_updated_at_column();

CREATE OR REPLACE TRIGGER update_classes_updated_at
    BEFORE UPDATE ON classes
    FOR EACH ROW EXECUTE FUNCTION update_dashboard_updated_at_column();

CREATE OR REPLACE TRIGGER update_assignments_updated_at
    BEFORE UPDATE ON assignments
    FOR EACH ROW EXECUTE FUNCTION update_dashboard_updated_at_column();

CREATE OR REPLACE TRIGGER update_lessons_updated_at
    BEFORE UPDATE ON lessons
    FOR EACH ROW EXECUTE FUNCTION update_dashboard_updated_at_column();

CREATE OR REPLACE TRIGGER update_student_progress_updated_at
    BEFORE UPDATE ON student_progress
    FOR EACH ROW EXECUTE FUNCTION update_dashboard_updated_at_column();

-- ============================================================================
-- FUNCTIONS TO MAINTAIN DENORMALIZED COUNTS
-- ============================================================================

-- Function to update school counts
CREATE OR REPLACE FUNCTION update_school_counts()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'dashboard_users' THEN
        -- Update teacher count
        UPDATE schools SET teacher_count = (
            SELECT COUNT(*) FROM dashboard_users 
            WHERE school_id = COALESCE(NEW.school_id, OLD.school_id) 
            AND role = 'teacher' AND is_active = true
        ) WHERE id = COALESCE(NEW.school_id, OLD.school_id);
        
        -- Update student count  
        UPDATE schools SET student_count = (
            SELECT COUNT(*) FROM dashboard_users 
            WHERE school_id = COALESCE(NEW.school_id, OLD.school_id) 
            AND role = 'student' AND is_active = true
        ) WHERE id = COALESCE(NEW.school_id, OLD.school_id);
    END IF;
    
    IF TG_TABLE_NAME = 'classes' THEN
        -- Update class count
        UPDATE schools SET class_count = (
            SELECT COUNT(*) FROM classes 
            WHERE school_id = COALESCE(NEW.school_id, OLD.school_id) 
            AND is_active = true
        ) WHERE id = COALESCE(NEW.school_id, OLD.school_id);
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

-- Apply count update triggers
CREATE OR REPLACE TRIGGER update_school_user_counts
    AFTER INSERT OR UPDATE OR DELETE ON dashboard_users
    FOR EACH ROW EXECUTE FUNCTION update_school_counts();

CREATE OR REPLACE TRIGGER update_school_class_counts
    AFTER INSERT OR UPDATE OR DELETE ON classes
    FOR EACH ROW EXECUTE FUNCTION update_school_counts();

-- Function to update class student counts
CREATE OR REPLACE FUNCTION update_class_student_counts()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE classes SET student_count = (
        SELECT COUNT(*) FROM class_students 
        WHERE class_id = COALESCE(NEW.class_id, OLD.class_id) 
        AND status = 'active'
    ) WHERE id = COALESCE(NEW.class_id, OLD.class_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

CREATE OR REPLACE TRIGGER update_class_enrollment_counts
    AFTER INSERT OR UPDATE OR DELETE ON class_students
    FOR EACH ROW EXECUTE FUNCTION update_class_student_counts();

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Dashboard database schema created successfully!';
    RAISE NOTICE '📊 Tables created: schools, dashboard_users, classes, class_students, assignments, submissions, lessons, student_progress, student_activity, student_achievements, attendance, messages, parent_children, system_events, api_logs, compliance_records';
    RAISE NOTICE '🔍 Indexes created for optimal performance';
    RAISE NOTICE '⚡ Triggers created for automatic updates and count maintenance';
END $$;