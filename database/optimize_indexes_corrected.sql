-- ============================================================================
-- ToolboxAI Database Optimization: Index Creation Script (Corrected)
-- ============================================================================
-- This script creates optimized indexes for the actual database schema
-- Matches the core schema (01_core_schema.sql) and dashboard schema (05_dashboard_schema.sql)
-- Run this after initial schema creation for improved query performance

-- Enable required extensions for advanced indexing
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ============================================================================
-- CORE USER MANAGEMENT INDEXES
-- ============================================================================

-- Users table - Core authentication and profile queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active 
ON users(email) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username_active 
ON users(username) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role_grade 
ON users(role, grade_level) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_login 
ON users(last_login DESC) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_school_district 
ON users(school_name, district_name) WHERE is_active = true;

-- GIN index for JSONB columns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_subjects_taught 
ON users USING GIN(subjects_taught) WHERE role = 'teacher';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_subjects_interested 
ON users USING GIN(subjects_interested) WHERE role = 'student';

-- User sessions - Authentication and security
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_user_active 
ON user_sessions(user_id, last_activity DESC) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_token_active 
ON user_sessions(token) WHERE is_active = true AND expires_at > NOW();

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_expires_cleanup 
ON user_sessions(expires_at) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_device_security 
ON user_sessions(device_id, ip_address, created_at DESC);

-- User roles - RBAC system
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_roles_user 
ON user_roles(user_id, assigned_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_roles_role 
ON user_roles(role_id, assigned_at DESC);

-- ============================================================================
-- EDUCATIONAL CONTENT SYSTEM INDEXES
-- ============================================================================

-- Educational content - Core content queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_subject_grade_published 
ON educational_content(subject, grade_level, created_at DESC) 
WHERE is_published = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_environment_difficulty 
ON educational_content(environment_type, difficulty_level) 
WHERE is_published = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_creator_date 
ON educational_content(created_by, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_duration_students 
ON educational_content(duration_minutes, max_students) 
WHERE is_published = true;

-- Full-text search index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_search_text 
ON educational_content USING GIN(
    to_tsvector('english', 
        COALESCE(title, '') || ' ' || 
        COALESCE(description, '')
    )
) WHERE is_published = true;

-- JSONB content data index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_data 
ON educational_content USING GIN(content_data);

-- Learning objectives
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_objectives_subject_grade 
ON learning_objectives(subject, grade_level, bloom_level);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_objectives_curriculum 
ON learning_objectives(curriculum_standard) WHERE curriculum_standard IS NOT NULL;

-- Content-objective relationships
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_objectives_content 
ON content_objectives(content_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_objectives_objective 
ON content_objectives(objective_id);

-- ============================================================================
-- QUIZ AND ASSESSMENT SYSTEM INDEXES
-- ============================================================================

-- Quizzes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quizzes_subject_grade 
ON quizzes(subject, grade_level, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quizzes_content 
ON quizzes(content_id, created_at DESC) WHERE content_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quizzes_adaptive 
ON quizzes(is_adaptive, subject, grade_level) WHERE is_adaptive = true;

-- Quiz questions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_questions_quiz_order 
ON quiz_questions(quiz_id, order_index);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_questions_type_difficulty 
ON quiz_questions(question_type, difficulty);

-- JSONB index for question data
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_questions_data 
ON quiz_questions USING GIN(question_data);

-- Quiz options
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_options_question_order 
ON quiz_options(question_id, order_index);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_options_correct 
ON quiz_options(question_id, is_correct) WHERE is_correct = true;

-- Quiz attempts - Critical for performance and leaderboards
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_attempts_user_quiz 
ON quiz_attempts(user_id, quiz_id, attempt_number DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_attempts_leaderboard 
ON quiz_attempts(quiz_id, score DESC, time_taken ASC) 
WHERE completed_at IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_attempts_completion 
ON quiz_attempts(completed_at DESC) WHERE completed_at IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_attempts_session 
ON quiz_attempts(session_id, started_at DESC) WHERE session_id IS NOT NULL;

-- JSONB indexes for answers and feedback
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_attempts_answers 
ON quiz_attempts USING GIN(answers);

-- ============================================================================
-- LEARNING PROGRESS AND ANALYTICS INDEXES
-- ============================================================================

-- User progress - Critical for dashboard and analytics
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_progress_user_content_type 
ON user_progress(user_id, content_id, progress_type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_progress_completion_recent 
ON user_progress(completion_percentage DESC, last_interaction DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_progress_mastery_level 
ON user_progress(mastery_level, completion_percentage DESC) 
WHERE mastery_level IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_progress_streaks 
ON user_progress(current_streak DESC, max_streak DESC) 
WHERE current_streak > 0;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_progress_recommendations 
ON user_progress(next_recommended_content, updated_at DESC) 
WHERE next_recommended_content IS NOT NULL;

-- JSONB indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_progress_performance_trends 
ON user_progress USING GIN(performance_trends);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_progress_learning_style 
ON user_progress USING GIN(learning_style);

-- ============================================================================
-- DASHBOARD SCHEMA INDEXES
-- ============================================================================

-- Schools
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_schools_district_active 
ON schools(district, is_active) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_schools_student_count 
ON schools(student_count DESC, teacher_count DESC) WHERE is_active = true;

-- Dashboard users
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dashboard_users_school_role 
ON dashboard_users(school_id, role, grade_level) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dashboard_users_login 
ON dashboard_users(last_login DESC) WHERE is_active = true;

-- Classes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_classes_teacher_subject 
ON classes(teacher_id, subject, grade_level) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_classes_schedule 
ON classes(start_date, end_date, schedule) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_classes_enrollment 
ON classes(student_count DESC, max_students) WHERE is_active = true;

-- Class enrollment
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_class_students_enrollment 
ON class_students(class_id, enrolled_at DESC) WHERE status = 'active';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_class_students_performance 
ON class_students(student_id, grade DESC, attendance_rate DESC);

-- Assignments
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_class_due 
ON assignments(class_id, due_date ASC) WHERE is_published = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_teacher_subject 
ON assignments(teacher_id, subject, created_at DESC);

-- Submissions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_submissions_assignment_grade 
ON submissions(assignment_id, grade DESC) WHERE grade IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_submissions_student_recent 
ON submissions(student_id, submitted_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_submissions_grading 
ON submissions(graded_by, graded_at DESC) WHERE graded_at IS NOT NULL;

-- Lessons
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lessons_class_schedule 
ON lessons(class_id, scheduled_at ASC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lessons_teacher_subject 
ON lessons(teacher_id, subject, scheduled_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lessons_roblox 
ON lessons(roblox_world_id, scheduled_at DESC) 
WHERE roblox_world_id IS NOT NULL;

-- Student progress (dashboard)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_progress_class_xp 
ON student_progress(class_id, xp_points DESC, level DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_progress_leaderboard 
ON student_progress(class_id, rank_position ASC, xp_points DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_progress_gpa 
ON student_progress(gpa DESC, attendance_rate DESC) WHERE gpa IS NOT NULL;

-- Attendance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_attendance_class_date 
ON attendance(class_id, date DESC, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_attendance_student_recent 
ON attendance(student_id, date DESC);

-- Messages
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_recipient_unread 
ON messages(recipient_id, created_at DESC) WHERE is_read = false;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_class_recent 
ON messages(class_id, created_at DESC) WHERE class_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_priority 
ON messages(priority, created_at DESC) WHERE priority != 'normal';

-- ============================================================================
-- COMPOSITE INDEXES FOR COMPLEX QUERIES
-- ============================================================================

-- User analytics composite index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_analytics_composite 
ON users(role, grade_level, school_name, last_login DESC) 
WHERE is_active = true;

-- Content discovery composite index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_discovery_composite 
ON educational_content(subject, grade_level, difficulty_level, duration_minutes) 
WHERE is_published = true;

-- Performance tracking composite index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_tracking_composite 
ON user_progress(user_id, mastery_level, completion_percentage DESC, last_interaction DESC);

-- ============================================================================
-- ANALYZE TABLES FOR UPDATED STATISTICS
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Analyzing tables to update query planner statistics...';
    
    -- Core tables
    ANALYZE users;
    ANALYZE user_sessions;
    ANALYZE educational_content;
    ANALYZE learning_objectives;
    ANALYZE quizzes;
    ANALYZE quiz_questions;
    ANALYZE quiz_options;
    ANALYZE quiz_attempts;
    ANALYZE user_progress;
    
    -- Dashboard tables
    ANALYZE schools;
    ANALYZE dashboard_users;
    ANALYZE classes;
    ANALYZE class_students;
    ANALYZE assignments;
    ANALYZE submissions;
    ANALYZE lessons;
    ANALYZE student_progress;
    ANALYZE attendance;
    ANALYZE messages;
    
    RAISE NOTICE 'Table analysis completed successfully!';
END $$;

-- ============================================================================
-- CLEANUP
-- ============================================================================

-- No cleanup needed - all indexes created with IF NOT EXISTS

-- ============================================================================
-- PERFORMANCE MONITORING VIEWS
-- ============================================================================

-- View to monitor index usage
CREATE OR REPLACE VIEW v_index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- View to identify unused indexes
CREATE OR REPLACE VIEW v_unused_indexes AS
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;

-- ============================================================================
-- SUCCESS SUMMARY
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Database optimization completed successfully!';
    RAISE NOTICE '🔍 Created performance indexes for:';
    RAISE NOTICE '   • User management (authentication, sessions, roles)';
    RAISE NOTICE '   • Educational content (search, filtering, relationships)';
    RAISE NOTICE '   • Quiz system (attempts, leaderboards, questions)';
    RAISE NOTICE '   • Progress tracking (analytics, mastery, streaks)';
    RAISE NOTICE '   • Dashboard features (classes, assignments, attendance)';
    RAISE NOTICE '   • JSONB data (content_data, learning_style, performance_trends)';
    RAISE NOTICE '   • Full-text search (content titles and descriptions)';
    RAISE NOTICE '📊 Performance monitoring views created: v_index_usage, v_unused_indexes';
    RAISE NOTICE '⚡ All indexes created with CONCURRENTLY IF NOT EXISTS for safety and rerun capability';
    RAISE NOTICE '📈 Run "SELECT * FROM v_index_usage;" to monitor index performance';
    RAISE NOTICE '🧹 Run "SELECT * FROM v_unused_indexes;" to identify unused indexes';
END $$;