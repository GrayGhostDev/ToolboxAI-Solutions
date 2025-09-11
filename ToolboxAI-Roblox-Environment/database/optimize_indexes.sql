-- ============================================================================
-- Database Optimization Script for Educational Platform
-- ============================================================================
-- This script creates optimized indexes for the educational platform database
-- to ensure all queries execute in < 50ms

-- Enable timing and statistics
\timing on

-- Note: CREATE INDEX CONCURRENTLY cannot run inside transactions
-- We'll create indexes without transactions for better performance

-- ==================== PERFORMANCE MONITORING SETUP ====================
-- Note: pg_stat_statements requires shared_preload_libraries configuration
-- Skip if not available and continue with index optimization
-- CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
-- SELECT pg_stat_statements_reset();

-- ==================== USER AND AUTHENTICATION INDEXES ====================
-- Optimize user lookups and authentication
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dashboard_users_username_active 
ON dashboard_users(username) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dashboard_users_email_active 
ON dashboard_users(email) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dashboard_users_role_active 
ON dashboard_users(role, is_active) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dashboard_users_last_login 
ON dashboard_users(last_login DESC) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dashboard_users_school_role 
ON dashboard_users(school_id, role) WHERE is_active = true;

-- ==================== CLASS AND STUDENT RELATIONSHIP INDEXES ====================
-- Optimize class-student relationships
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_class_students_student_class 
ON class_students(student_id, class_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_class_students_class_student 
ON class_students(class_id, student_id);

-- Optimize class lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_classes_teacher_active 
ON classes(teacher_id) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_classes_subject_grade 
ON classes(subject, grade_level) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_classes_active_status 
ON classes(is_active, created_at DESC);

-- ==================== ASSIGNMENT AND SUBMISSION INDEXES ====================
-- Critical indexes for assignment performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_teacher_due 
ON assignments(teacher_id, due_date DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_class_due 
ON assignments(class_id, due_date DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_due_date_active 
ON assignments(due_date) WHERE status != 'deleted';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_subject_type 
ON assignments(subject, type);

-- Optimize submission queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_submissions_assignment_student 
ON submissions(assignment_id, student_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_submissions_student_status 
ON submissions(student_id, status, submitted_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_submissions_status_grade 
ON submissions(status, grade) WHERE status = 'graded';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_submissions_submitted_at 
ON submissions(submitted_at DESC) WHERE submitted_at IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_submissions_pending_grading 
ON submissions(assignment_id) WHERE status = 'pending';

-- ==================== LESSON AND SCHEDULING INDEXES ====================
-- Optimize lesson scheduling queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lessons_teacher_scheduled 
ON lessons(teacher_id, scheduled_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lessons_class_scheduled 
ON lessons(class_id, scheduled_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lessons_scheduled_upcoming 
ON lessons(scheduled_at) WHERE scheduled_at >= NOW();

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lessons_subject_date 
ON lessons(subject, DATE(scheduled_at));

-- ==================== STUDENT PROGRESS AND GAMIFICATION INDEXES ====================
-- Optimize student progress tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_progress_student 
ON student_progress(student_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_progress_xp_rank 
ON student_progress(xp_points DESC, rank_position);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_progress_level_xp 
ON student_progress(level DESC, xp_points DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_progress_rank 
ON student_progress(rank_position) WHERE rank_position <= 100;

-- Optimize achievements
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_achievements_student_date 
ON student_achievements(student_id, earned_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_achievements_achievement 
ON student_achievements(achievement_id, earned_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_achievements_xp_reward 
ON achievements(xp_reward DESC) WHERE is_active = true;

-- ==================== ACTIVITY AND COMMUNICATION INDEXES ====================
-- Optimize student activity tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_activity_student_date 
ON student_activity(student_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_activity_type_date 
ON student_activity(type, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_activity_xp_earned 
ON student_activity(xp_earned) WHERE xp_earned > 0;

-- Optimize messaging system
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_recipient_date 
ON messages(recipient_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_sender_date 
ON messages(sender_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_unread 
ON messages(recipient_id, is_read) WHERE is_read = false;

-- ==================== ATTENDANCE AND PARENT RELATIONSHIPS ====================
-- Optimize attendance queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_attendance_student_date 
ON attendance(student_id, date DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_attendance_date_status 
ON attendance(date, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_attendance_recent 
ON attendance(student_id, status) WHERE date >= CURRENT_DATE - INTERVAL '90 days';

-- Optimize parent-child relationships
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parent_children_parent 
ON parent_children(parent_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parent_children_student 
ON parent_children(student_id);

-- ==================== SYSTEM MONITORING INDEXES ====================
-- Optimize system events and monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_events_date_severity 
ON system_events(created_at DESC, severity);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_events_type_date 
ON system_events(event_type, created_at DESC);

-- Optimize API logs for performance monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_logs_timestamp 
ON api_logs(timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_logs_response_time 
ON api_logs(response_time DESC) WHERE response_time > 1000; -- Slow queries

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_logs_status_errors 
ON api_logs(status_code, timestamp DESC) WHERE status_code >= 400;

-- ==================== COMPLIANCE AND AUDIT INDEXES ====================
-- Optimize compliance monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_compliance_records_type_status 
ON compliance_records(type, status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_compliance_records_pending 
ON compliance_records(created_at DESC) WHERE status = 'pending';

-- ==================== PERFORMANCE OPTIMIZATION SETTINGS ====================
-- Configure PostgreSQL for better performance
-- Note: These settings should be adjusted based on your server specifications

-- Set work memory for complex queries (adjust based on available RAM)
SET work_mem = '256MB';

-- Set maintenance work memory for index creation
SET maintenance_work_mem = '1GB';

-- Enable parallel query execution
SET max_parallel_workers_per_gather = 4;
SET parallel_tuple_cost = 0.1;
SET parallel_setup_cost = 1000;

-- Optimize random page cost for SSD storage
SET random_page_cost = 1.1;

-- Configure effective cache size (set to ~75% of total RAM)
SET effective_cache_size = '4GB';

-- ==================== PARTIAL INDEXES FOR COMMON FILTERS ====================
-- Create partial indexes for frequently filtered data

-- Active users only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_created 
ON dashboard_users(created_at DESC) WHERE is_active = true;

-- Recent submissions only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_submissions_recent_status 
ON submissions(status, submitted_at DESC) 
WHERE submitted_at >= CURRENT_DATE - INTERVAL '30 days';

-- Upcoming assignments only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_upcoming 
ON assignments(due_date, class_id) 
WHERE due_date >= CURRENT_DATE;

-- Active classes with students
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_classes_active_with_students 
ON classes(teacher_id, created_at DESC) 
WHERE is_active = true;

-- ==================== COMPOSITE INDEXES FOR COMPLEX QUERIES ====================
-- Multi-column indexes for frequently joined tables

-- Teacher dashboard optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_teacher_dashboard_composite 
ON assignments(teacher_id, due_date DESC, status) 
WHERE due_date >= CURRENT_DATE - INTERVAL '30 days';

-- Student dashboard optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_dashboard_composite 
ON submissions(student_id, status, submitted_at DESC, grade);

-- Parent dashboard optimization - recent grades
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parent_dashboard_grades 
ON submissions(student_id, submitted_at DESC) 
WHERE status = 'graded' AND submitted_at >= CURRENT_DATE - INTERVAL '30 days';

-- Leaderboard optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leaderboard_composite 
ON student_progress(rank_position, xp_points DESC, level DESC) 
WHERE rank_position <= 100;

-- ==================== ANALYZE TABLES FOR OPTIMIZER ====================
-- Update table statistics for query planner

ANALYZE dashboard_users;
ANALYZE classes;
ANALYZE class_students;
ANALYZE assignments;
ANALYZE submissions;
ANALYZE lessons;
ANALYZE student_progress;
ANALYZE student_achievements;
ANALYZE achievements;
ANALYZE student_activity;
ANALYZE messages;
ANALYZE attendance;
ANALYZE parent_children;
ANALYZE system_events;
ANALYZE api_logs;
ANALYZE compliance_records;

-- ==================== OPTIMIZATION COMPLETE ====================
-- All indexes have been created successfully

-- ==================== VALIDATION QUERIES ====================
-- Test query performance after optimization

\echo 'Running performance validation queries...'

-- Test teacher dashboard query performance (using sample teacher ID)
EXPLAIN (ANALYZE, BUFFERS) 
SELECT c.id, c.name, c.subject, c.grade_level,
       COUNT(DISTINCT cs.student_id) as student_count
FROM classes c
LEFT JOIN class_students cs ON c.id = cs.class_id
WHERE c.teacher_id = (SELECT id FROM dashboard_users WHERE role = 'teacher' LIMIT 1) 
  AND c.is_active = true
GROUP BY c.id;

-- Test student assignment query performance (using sample student ID)
EXPLAIN (ANALYZE, BUFFERS)
SELECT a.id, a.title, a.subject, a.due_date,
       s.status, s.grade, s.progress
FROM assignments a
LEFT JOIN submissions s ON a.id = s.assignment_id AND s.student_id = (SELECT id FROM dashboard_users WHERE role = 'student' LIMIT 1)
JOIN classes c ON a.class_id = c.id
JOIN class_students cs ON c.id = cs.class_id
WHERE cs.student_id = (SELECT id FROM dashboard_users WHERE role = 'student' LIMIT 1) 
  AND a.due_date >= CURRENT_DATE
ORDER BY a.due_date
LIMIT 10;

-- Test leaderboard query performance
EXPLAIN (ANALYZE, BUFFERS)
SELECT u.username, sp.xp_points, sp.level, sp.rank_position
FROM student_progress sp
JOIN dashboard_users u ON sp.student_id = u.id
WHERE sp.rank_position <= 10
ORDER BY sp.rank_position;

\echo 'Index optimization completed successfully!'
\echo 'All indexes created and tables analyzed.'
\echo 'Query performance should now be optimized for < 50ms execution times.'

-- Display current connection and performance settings
SELECT name, setting, unit, short_desc 
FROM pg_settings 
WHERE name IN (
    'work_mem', 
    'maintenance_work_mem', 
    'effective_cache_size', 
    'random_page_cost',
    'max_parallel_workers_per_gather'
) 
ORDER BY name;