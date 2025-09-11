-- ============================================================================
-- ToolboxAI Roblox Environment - Core Database Schema
-- ============================================================================
-- This file creates the core database schema for the ToolboxAI platform
-- Run this after setting up the database and users
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
-- ============================================================================
-- CORE USER MANAGEMENT
-- ============================================================================
-- Users table with comprehensive profile information
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    -- Profile information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    avatar_url VARCHAR(500),
    bio TEXT,
    -- Educational context
    role VARCHAR(20) DEFAULT 'student',
    -- student, teacher, admin, developer
    grade_level INTEGER,
    school_name VARCHAR(200),
    district_name VARCHAR(200),
    subjects_taught JSONB [],
    -- For teachers
    subjects_interested JSONB [],
    -- For students
    -- Account status
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    is_superuser BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMPTZ,
    -- Authentication
    last_login TIMESTAMPTZ,
    login_count INTEGER DEFAULT 0,
    failed_login_count INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(255),
    -- Preferences and settings
    settings JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    notification_settings JSONB DEFAULT '{}',
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    version INTEGER DEFAULT 1,
    audit_log JSONB DEFAULT '[]'
);
-- User roles for RBAC
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT false,
    priority INTEGER DEFAULT 0,
    permissions JSONB [] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- User-role associations
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);
-- Enhanced session management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    refresh_token VARCHAR(500) UNIQUE,
    -- Session context
    session_type VARCHAR(20) DEFAULT 'web',
    -- web, roblox, api, mobile
    ip_address INET,
    user_agent TEXT,
    device_id VARCHAR(255),
    browser_fingerprint VARCHAR(500),
    -- Geographic and context data
    country VARCHAR(2),
    -- ISO country code
    timezone VARCHAR(50),
    locale VARCHAR(10),
    -- Expiration management
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    refresh_expires_at TIMESTAMPTZ,
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    -- Status
    is_active BOOLEAN DEFAULT true,
    revoked_at TIMESTAMPTZ,
    revoked_reason VARCHAR(255),
    -- Security
    security_events JSONB DEFAULT '[]'
);
-- ============================================================================
-- EDUCATIONAL CONTENT SYSTEM
-- ============================================================================
-- Learning objectives and curriculum alignment
CREATE TABLE learning_objectives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    subject VARCHAR(50) NOT NULL,
    grade_level INTEGER CHECK (
        grade_level BETWEEN 1 AND 12
    ),
    bloom_level VARCHAR(20),
    curriculum_standard VARCHAR(100),
    measurable BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Educational content templates and generated content
CREATE TABLE educational_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    subject VARCHAR(50) NOT NULL,
    grade_level INTEGER NOT NULL,
    environment_type VARCHAR(50) NOT NULL,
    terrain_size VARCHAR(20) DEFAULT 'medium',
    difficulty_level VARCHAR(20) DEFAULT 'medium',
    duration_minutes INTEGER DEFAULT 30,
    max_students INTEGER DEFAULT 30,
    content_data JSONB NOT NULL,
    -- Full content structure
    generated_scripts JSONB [],
    -- Array of Lua scripts
    terrain_config JSONB,
    -- Terrain configuration
    game_mechanics JSONB,
    -- Game mechanics settings
    accessibility_features BOOLEAN DEFAULT false,
    multilingual BOOLEAN DEFAULT false,
    version INTEGER DEFAULT 1,
    is_template BOOLEAN DEFAULT false,
    is_published BOOLEAN DEFAULT false,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Content-objective relationships
CREATE TABLE content_objectives (
    content_id UUID REFERENCES educational_content(id) ON DELETE CASCADE,
    objective_id UUID REFERENCES learning_objectives(id) ON DELETE CASCADE,
    PRIMARY KEY (content_id, objective_id)
);
-- ============================================================================
-- QUIZ AND ASSESSMENT SYSTEM
-- ============================================================================
-- Quiz definitions
CREATE TABLE quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    subject VARCHAR(50) NOT NULL,
    grade_level INTEGER NOT NULL,
    content_id UUID REFERENCES educational_content(id),
    time_limit INTEGER,
    -- seconds
    passing_score INTEGER DEFAULT 70,
    max_attempts INTEGER DEFAULT 3,
    shuffle_questions BOOLEAN DEFAULT true,
    shuffle_options BOOLEAN DEFAULT true,
    show_results BOOLEAN DEFAULT true,
    is_adaptive BOOLEAN DEFAULT false,
    difficulty_progression JSONB,
    -- Adaptive learning rules
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Quiz questions
CREATE TABLE quiz_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID REFERENCES quizzes(id) ON DELETE CASCADE,
    question_type VARCHAR(20) NOT NULL,
    question_text TEXT NOT NULL,
    correct_answer TEXT,
    difficulty VARCHAR(20) DEFAULT 'medium',
    points INTEGER DEFAULT 1,
    time_limit INTEGER,
    -- per question
    hint TEXT,
    explanation TEXT,
    order_index INTEGER NOT NULL,
    question_data JSONB,
    -- Additional question metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- Quiz question options
CREATE TABLE quiz_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID REFERENCES quiz_questions(id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT false,
    explanation TEXT,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- Student quiz attempts and progress
CREATE TABLE quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID REFERENCES quizzes(id),
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES user_sessions(id),
    attempt_number INTEGER NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    score DECIMAL(5, 2),
    passed BOOLEAN,
    time_taken INTEGER,
    -- seconds
    answers JSONB,
    -- Student answers
    feedback JSONB,
    -- AI-generated feedback
    adaptive_adjustments JSONB,
    -- Difficulty adjustments made
    UNIQUE(quiz_id, user_id, attempt_number)
);
-- ============================================================================
-- LEARNING PROGRESS AND ANALYTICS
-- ============================================================================
-- Learning progress and achievement tracking
CREATE TABLE user_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    content_id UUID REFERENCES educational_content(id),
    progress_type VARCHAR(20) NOT NULL,
    -- lesson, quiz, activity, project
    -- Progress metrics
    completion_percentage DECIMAL(5, 2) DEFAULT 0,
    time_spent_seconds INTEGER DEFAULT 0,
    attempts_count INTEGER DEFAULT 0,
    best_score DECIMAL(5, 2),
    current_streak INTEGER DEFAULT 0,
    max_streak INTEGER DEFAULT 0,
    -- Learning analytics
    difficulty_level VARCHAR(20),
    mastery_level VARCHAR(20),
    -- novice, developing, proficient, advanced
    last_interaction TIMESTAMPTZ,
    next_recommended_content UUID REFERENCES educational_content(id),
    -- Adaptive learning data
    learning_style JSONB,
    -- Visual, auditory, kinesthetic preferences
    performance_trends JSONB,
    -- Historical performance data
    recommendations JSONB [],
    -- AI-generated recommendations
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, content_id, progress_type)
);
-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================
-- User indexes
CREATE INDEX idx_users_email ON users(email)
WHERE is_active = true;
CREATE INDEX idx_users_username ON users(username)
WHERE is_active = true;
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
-- Session indexes
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id)
WHERE is_active = true;
CREATE INDEX idx_sessions_token ON user_sessions(token)
WHERE is_active = true;
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at)
WHERE is_active = true;
-- Content indexes
CREATE INDEX idx_content_subject_grade ON educational_content(subject, grade_level)
WHERE is_published = true;
CREATE INDEX idx_content_created_by ON educational_content(created_by, created_at DESC);
CREATE INDEX idx_content_published ON educational_content(is_published, created_at DESC);
-- Quiz indexes
CREATE INDEX idx_quiz_attempts_user ON quiz_attempts(user_id, completed_at DESC);
CREATE INDEX idx_quiz_attempts_quiz ON quiz_attempts(quiz_id, score DESC);
CREATE INDEX idx_quiz_questions_quiz ON quiz_questions(quiz_id, order_index);
-- Progress indexes
CREATE INDEX idx_progress_user_content ON user_progress(user_id, content_id);
CREATE INDEX idx_progress_completion ON user_progress(
    completion_percentage DESC,
    last_interaction DESC
);
-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================
-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW();
RETURN NEW;
END;
$$ language 'plpgsql';
-- Apply trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE
UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_educational_content_updated_at BEFORE
UPDATE ON educational_content FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_quizzes_updated_at BEFORE
UPDATE ON quizzes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_progress_updated_at BEFORE
UPDATE ON user_progress FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- ============================================================================
-- INITIAL DATA
-- ============================================================================
-- Insert default roles
INSERT INTO roles (
        name,
        description,
        is_system,
        priority,
        permissions
    )
VALUES (
        'admin',
        'System Administrator',
        true,
        100,
        ARRAY ['["*"] '::jsonb]
    ),
    (
        ' teacher ',
        ' Educator / Teacher ',
        true,
        50,
        ARRAY[' ["content:create", "content:edit", "content:view", "quiz:create", "quiz:edit", "quiz:view", "progress:view"] '::jsonb]
    ),
    (
        ' student ',
        ' Student / Learner ',
        true,
        10,
        ARRAY[' ["content:view", "quiz:take", "progress:view_own"] '::jsonb]
    ),
    (
        ' developer ',
        ' System Developer ',
        true,
        75,
        ARRAY[' ["*"] '::jsonb]
    );
-- Insert default learning objectives
INSERT INTO learning_objectives (
        title,
        description,
        subject,
        grade_level,
        bloom_level,
        curriculum_standard
    )
VALUES (
        ' Basic Programming Concepts ',
        ' Understand fundamental programming concepts ',
        ' Computer Science ',
        6,
        ' understand ',
        ' CSTA - 1A - AP -10 '
    ),
    (
        ' Problem Solving ',
        ' Develop problem - solving skills through coding ',
        ' Computer Science ',
        6,
        ' apply ',
        ' CSTA - 1A - AP -11 '
    ),
    (
        ' Collaboration ',
        ' Work effectively in teams ',
        ' Computer Science ',
        6,
        ' apply ',
        ' CSTA - 1A - AP -12 '
    );
-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE ' ✅ Core database schema created successfully ! ';
    RAISE NOTICE ' 📊 Tables created: users,
        roles,
        user_roles,
        user_sessions,
        learning_objectives,
        educational_content,
        content_objectives,
        quizzes,
        quiz_questions,
        quiz_options,
        quiz_attempts,
        user_progress ';
    RAISE NOTICE ' 🔍 Indexes created for optimal performance ';
    RAISE NOTICE ' ⚡ Triggers created for automatic timestamp updates ';
    RAISE NOTICE ' 📝 Initial data inserted: default roles
        and learning objectives ';
END $$;