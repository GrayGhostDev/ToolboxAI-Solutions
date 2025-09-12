-- ToolboxAI Roblox Environment Database Schema
-- PostgreSQL 15+ recommended
-- Created: 2025-09-07

-- Drop existing schema if needed (be careful in production!)
-- DROP SCHEMA IF EXISTS toolboxai CASCADE;

-- Create schema
CREATE SCHEMA IF NOT EXISTS toolboxai;
SET search_path TO toolboxai, public;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search

-- =============================================================================
-- USER MANAGEMENT TABLES
-- =============================================================================

-- Users table (educators, students, admins)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'educator', 'admin', 'parent')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'pending')),
    
    -- Profile information
    avatar_url TEXT,
    bio TEXT,
    grade_level INTEGER,
    school_id UUID,
    
    -- LMS Integration
    schoology_id VARCHAR(100),
    canvas_id VARCHAR(100),
    google_id VARCHAR(100),
    moodle_id VARCHAR(100),
    
    -- Settings
    preferences JSONB DEFAULT '{}',
    notification_settings JSONB DEFAULT '{"email": true, "in_app": true}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    INDEX idx_users_email (email),
    INDEX idx_users_username (username),
    INDEX idx_users_role (role),
    INDEX idx_users_school_id (school_id)
);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_hash VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_sessions_user_id (user_id),
    INDEX idx_sessions_token (token_hash),
    INDEX idx_sessions_expires (expires_at)
);

-- =============================================================================
-- EDUCATIONAL CONTENT TABLES
-- =============================================================================

-- Courses/Classes table
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    subject VARCHAR(100) NOT NULL,
    grade_level INTEGER,
    educator_id UUID REFERENCES users(id),
    
    -- LMS Integration
    lms_platform VARCHAR(50),
    lms_course_id VARCHAR(100),
    sync_enabled BOOLEAN DEFAULT false,
    last_synced_at TIMESTAMP WITH TIME ZONE,
    
    -- Settings
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    enrollment_code VARCHAR(20) UNIQUE,
    max_students INTEGER DEFAULT 50,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    start_date DATE,
    end_date DATE,
    
    INDEX idx_courses_educator (educator_id),
    INDEX idx_courses_subject (subject),
    INDEX idx_courses_code (enrollment_code)
);

-- Course enrollments
CREATE TABLE IF NOT EXISTS enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'dropped', 'pending')),
    grade DECIMAL(5, 2),
    
    UNIQUE(course_id, student_id),
    INDEX idx_enrollments_course (course_id),
    INDEX idx_enrollments_student (student_id)
);

-- Lessons table
CREATE TABLE IF NOT EXISTS lessons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    learning_objectives TEXT[],
    
    -- Content
    content_type VARCHAR(50) NOT NULL,
    content_data JSONB NOT NULL,
    
    -- Roblox Integration
    roblox_place_id VARCHAR(100),
    roblox_scripts JSONB,
    environment_type VARCHAR(50),
    terrain_config JSONB,
    
    -- Settings
    duration_minutes INTEGER,
    difficulty_level VARCHAR(20) CHECK (difficulty_level IN ('easy', 'medium', 'hard', 'expert')),
    order_index INTEGER DEFAULT 0,
    is_published BOOLEAN DEFAULT false,
    
    -- AI Generation Metadata
    ai_generated BOOLEAN DEFAULT false,
    ai_model VARCHAR(50),
    ai_prompt TEXT,
    generation_params JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_lessons_course (course_id),
    INDEX idx_lessons_published (is_published),
    INDEX idx_lessons_order (course_id, order_index)
);

-- =============================================================================
-- QUIZ AND ASSESSMENT TABLES
-- =============================================================================

-- Quizzes table
CREATE TABLE IF NOT EXISTS quizzes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lesson_id UUID REFERENCES lessons(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Quiz configuration
    quiz_type VARCHAR(50) DEFAULT 'standard' CHECK (quiz_type IN ('standard', 'timed', 'practice', 'exam')),
    time_limit_minutes INTEGER,
    passing_score DECIMAL(5, 2) DEFAULT 70.0,
    max_attempts INTEGER DEFAULT 3,
    shuffle_questions BOOLEAN DEFAULT true,
    shuffle_answers BOOLEAN DEFAULT true,
    
    -- AI Generation
    ai_generated BOOLEAN DEFAULT false,
    generation_prompt TEXT,
    
    -- Status
    is_published BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    available_from TIMESTAMP WITH TIME ZONE,
    available_until TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_quizzes_lesson (lesson_id),
    INDEX idx_quizzes_course (course_id)
);

-- Quiz questions table
CREATE TABLE IF NOT EXISTS quiz_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL CHECK (question_type IN ('multiple_choice', 'true_false', 'short_answer', 'essay', 'matching', 'ordering')),
    
    -- Question data (varies by type)
    options JSONB, -- For multiple choice
    correct_answer JSONB, -- Flexible for different types
    explanation TEXT,
    
    -- Scoring
    points DECIMAL(5, 2) DEFAULT 1.0,
    partial_credit_allowed BOOLEAN DEFAULT false,
    
    -- Media
    image_url TEXT,
    audio_url TEXT,
    video_url TEXT,
    
    -- Order
    order_index INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_questions_quiz (quiz_id),
    INDEX idx_questions_order (quiz_id, order_index)
);

-- Quiz attempts table
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    time_spent_seconds INTEGER,
    
    -- Scoring
    score DECIMAL(5, 2),
    points_earned DECIMAL(10, 2),
    points_possible DECIMAL(10, 2),
    passed BOOLEAN,
    
    -- Data
    answers JSONB NOT NULL DEFAULT '{}',
    feedback JSONB,
    
    -- Status
    status VARCHAR(20) DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned', 'submitted')),
    
    UNIQUE(quiz_id, student_id, attempt_number),
    INDEX idx_attempts_quiz (quiz_id),
    INDEX idx_attempts_student (student_id),
    INDEX idx_attempts_status (status)
);

-- =============================================================================
-- PROGRESS TRACKING TABLES
-- =============================================================================

-- Student progress table
CREATE TABLE IF NOT EXISTS student_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES lessons(id) ON DELETE CASCADE,
    
    -- Progress metrics
    completion_percentage DECIMAL(5, 2) DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    
    -- Performance metrics
    average_score DECIMAL(5, 2),
    quizzes_completed INTEGER DEFAULT 0,
    quizzes_passed INTEGER DEFAULT 0,
    
    -- Detailed progress data
    progress_data JSONB DEFAULT '{}',
    checkpoints_completed JSONB DEFAULT '[]',
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(student_id, course_id, lesson_id),
    INDEX idx_progress_student (student_id),
    INDEX idx_progress_course (course_id),
    INDEX idx_progress_lesson (lesson_id)
);

-- =============================================================================
-- GAMIFICATION TABLES
-- =============================================================================

-- Achievements table
CREATE TABLE IF NOT EXISTS achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    
    -- Achievement criteria
    criteria_type VARCHAR(50) NOT NULL,
    criteria_value JSONB NOT NULL,
    
    -- Rewards
    points INTEGER DEFAULT 10,
    badge_image_url TEXT,
    badge_color VARCHAR(7),
    
    -- Availability
    is_active BOOLEAN DEFAULT true,
    is_hidden BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_achievements_category (category),
    INDEX idx_achievements_active (is_active)
);

-- User achievements table
CREATE TABLE IF NOT EXISTS user_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    
    -- Progress
    progress DECIMAL(5, 2) DEFAULT 0,
    unlocked BOOLEAN DEFAULT false,
    unlocked_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    UNIQUE(user_id, achievement_id),
    INDEX idx_user_achievements_user (user_id),
    INDEX idx_user_achievements_unlocked (unlocked)
);

-- Leaderboard table
CREATE TABLE IF NOT EXISTS leaderboard (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    
    -- Scores
    total_points INTEGER DEFAULT 0,
    weekly_points INTEGER DEFAULT 0,
    monthly_points INTEGER DEFAULT 0,
    
    -- Rankings
    global_rank INTEGER,
    course_rank INTEGER,
    weekly_rank INTEGER,
    
    -- Stats
    achievements_count INTEGER DEFAULT 0,
    perfect_quizzes INTEGER DEFAULT 0,
    streak_days INTEGER DEFAULT 0,
    
    -- Timestamps
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, course_id),
    INDEX idx_leaderboard_user (user_id),
    INDEX idx_leaderboard_course (course_id),
    INDEX idx_leaderboard_points (total_points DESC)
);

-- =============================================================================
-- ANALYTICS TABLES
-- =============================================================================

-- Analytics events table
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID,
    
    -- Event information
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(50),
    event_data JSONB DEFAULT '{}',
    
    -- Context
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    lesson_id UUID REFERENCES lessons(id) ON DELETE SET NULL,
    quiz_id UUID REFERENCES quizzes(id) ON DELETE SET NULL,
    
    -- Technical details
    ip_address INET,
    user_agent TEXT,
    platform VARCHAR(50),
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_analytics_user (user_id),
    INDEX idx_analytics_type (event_type),
    INDEX idx_analytics_time (created_at),
    INDEX idx_analytics_course (course_id)
);

-- Learning analytics summary table
CREATE TABLE IF NOT EXISTS learning_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    period_type VARCHAR(20) CHECK (period_type IN ('daily', 'weekly', 'monthly')),
    period_date DATE NOT NULL,
    
    -- Metrics
    time_spent_minutes INTEGER DEFAULT 0,
    lessons_completed INTEGER DEFAULT 0,
    quizzes_taken INTEGER DEFAULT 0,
    average_quiz_score DECIMAL(5, 2),
    
    -- Engagement metrics
    login_count INTEGER DEFAULT 0,
    interaction_count INTEGER DEFAULT 0,
    collaboration_score DECIMAL(5, 2),
    
    -- Detailed data
    metrics_data JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, course_id, period_type, period_date),
    INDEX idx_learning_analytics_user (user_id),
    INDEX idx_learning_analytics_course (course_id),
    INDEX idx_learning_analytics_period (period_date)
);

-- =============================================================================
-- COLLABORATION TABLES
-- =============================================================================

-- Groups table
CREATE TABLE IF NOT EXISTS groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Settings
    max_members INTEGER DEFAULT 5,
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_groups_course (course_id)
);

-- Group members table
CREATE TABLE IF NOT EXISTS group_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member' CHECK (role IN ('leader', 'member')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(group_id, user_id),
    INDEX idx_group_members_group (group_id),
    INDEX idx_group_members_user (user_id)
);

-- =============================================================================
-- CONTENT GENERATION HISTORY
-- =============================================================================

-- AI content generation history
CREATE TABLE IF NOT EXISTS content_generation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Request information
    request_type VARCHAR(50) NOT NULL,
    request_data JSONB NOT NULL,
    prompt TEXT,
    
    -- Response information
    response_data JSONB,
    generated_content TEXT,
    
    -- AI Details
    ai_model VARCHAR(50),
    tokens_used INTEGER,
    generation_time_ms INTEGER,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    
    -- Associated entities
    lesson_id UUID REFERENCES lessons(id) ON DELETE SET NULL,
    quiz_id UUID REFERENCES quizzes(id) ON DELETE SET NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_generation_user (user_id),
    INDEX idx_generation_status (status),
    INDEX idx_generation_type (request_type)
);

-- =============================================================================
-- SYSTEM TABLES
-- =============================================================================

-- System configuration table
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id)
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_entity (entity_type, entity_id),
    INDEX idx_audit_time (created_at)
);

-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lessons_updated_at BEFORE UPDATE ON lessons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quizzes_updated_at BEFORE UPDATE ON quizzes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quiz_questions_updated_at BEFORE UPDATE ON quiz_questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_student_progress_updated_at BEFORE UPDATE ON student_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leaderboard_updated_at BEFORE UPDATE ON leaderboard
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_analytics_updated_at BEFORE UPDATE ON learning_analytics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_groups_updated_at BEFORE UPDATE ON groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Text search indexes
CREATE INDEX idx_lessons_search ON lessons USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
CREATE INDEX idx_courses_search ON courses USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
CREATE INDEX idx_quizzes_search ON quizzes USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- JSONB indexes
CREATE INDEX idx_users_preferences ON users USING gin(preferences);
CREATE INDEX idx_lessons_content ON lessons USING gin(content_data);
CREATE INDEX idx_quiz_attempts_answers ON quiz_attempts USING gin(answers);
CREATE INDEX idx_analytics_events_data ON analytics_events USING gin(event_data);

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert default system configuration
INSERT INTO system_config (key, value, description) VALUES
    ('max_file_size', '{"value": 10485760}', 'Maximum file upload size in bytes'),
    ('session_timeout', '{"value": 3600}', 'Session timeout in seconds'),
    ('maintenance_mode', '{"value": false}', 'System maintenance mode flag'),
    ('ai_models', '{"models": ["gpt-4", "gpt-3.5-turbo"]}', 'Available AI models'),
    ('supported_lms', '{"platforms": ["schoology", "canvas", "google_classroom", "moodle"]}', 'Supported LMS platforms')
ON CONFLICT (key) DO NOTHING;

-- Insert default achievements
INSERT INTO achievements (name, description, category, criteria_type, criteria_value, points) VALUES
    ('First Steps', 'Complete your first lesson', 'beginner', 'lessons_completed', '{"count": 1}', 10),
    ('Quiz Master', 'Score 100% on a quiz', 'performance', 'perfect_quiz', '{"score": 100}', 25),
    ('Dedicated Learner', 'Study for 7 days in a row', 'engagement', 'streak_days', '{"days": 7}', 50),
    ('Team Player', 'Join a study group', 'collaboration', 'group_joined', '{"count": 1}', 15),
    ('Knowledge Seeker', 'Complete 10 lessons', 'progress', 'lessons_completed', '{"count": 10}', 30)
ON CONFLICT DO NOTHING;

-- =============================================================================
-- PERMISSIONS (adjust for your specific needs)
-- =============================================================================

-- Create read-only role
CREATE ROLE toolboxai_readonly;
GRANT USAGE ON SCHEMA toolboxai TO toolboxai_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA toolboxai TO toolboxai_readonly;

-- Create application role
CREATE ROLE toolboxai_app;
GRANT USAGE ON SCHEMA toolboxai TO toolboxai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA toolboxai TO toolboxai_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA toolboxai TO toolboxai_app;

-- =============================================================================
-- MAINTENANCE QUERIES
-- =============================================================================

-- Query to check table sizes
/*
SELECT
    schemaname AS table_schema,
    tablename AS table_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'toolboxai'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
*/

-- Query to check index usage
/*
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans
FROM pg_stat_user_indexes
WHERE schemaname = 'toolboxai'
ORDER BY idx_scan DESC;
*/

-- =============================================================================
-- CLEANUP (if needed)
-- =============================================================================

-- To completely remove the schema and start over:
-- DROP SCHEMA IF EXISTS toolboxai CASCADE;

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================