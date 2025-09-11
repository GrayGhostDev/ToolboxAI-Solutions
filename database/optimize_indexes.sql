-- Database Optimization: Index Creation for ToolboxAI Roblox Environment
-- =======================================================================
-- This script creates optimized indexes for all major tables to improve query performance
-- Run this after initial schema creation and periodically analyze query patterns

-- ==========================================
-- Memory Store Indexes (SQLite)
-- ==========================================

-- For memory_store.py - Memory table indexes
-- Already created in code:
-- CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp);
-- CREATE INDEX IF NOT EXISTS idx_access_count ON memories(access_count);
-- CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance);

-- Additional composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_memories_importance_access 
ON memories(importance DESC, access_count DESC);

CREATE INDEX IF NOT EXISTS idx_memories_timestamp_importance 
ON memories(timestamp DESC, importance DESC);

-- ==========================================
-- PostgreSQL Indexes (Main Database)
-- ==========================================

-- Users table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email 
ON users(email) WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at 
ON users(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_active 
ON users(last_active DESC) WHERE is_active = true;

-- Sessions table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_user_id 
ON sessions(user_id) WHERE expired_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_token_hash 
ON sessions(token_hash) WHERE expired_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_expired_at 
ON sessions(expired_at) WHERE expired_at IS NOT NULL;

-- Educational content table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_subject_grade 
ON educational_content(subject_area, grade_level) WHERE is_published = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_created_by 
ON educational_content(created_by, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_learning_objectives 
ON educational_content USING GIN(learning_objectives) WHERE is_published = true;

-- Full-text search index for content
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_search 
ON educational_content USING GIN(
    to_tsvector('english', 
        COALESCE(title, '') || ' ' || 
        COALESCE(description, '') || ' ' || 
        COALESCE(content_body, '')
    )
);

-- Quiz results table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_results_user_id 
ON quiz_results(user_id, completed_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_results_quiz_id 
ON quiz_results(quiz_id, score DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_results_completed 
ON quiz_results(completed_at DESC) WHERE is_completed = true;

-- Composite index for leaderboard queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_leaderboard 
ON quiz_results(quiz_id, score DESC, time_taken ASC) 
WHERE is_completed = true;

-- Learning progress table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_progress_user_content 
ON learning_progress(user_id, content_id) WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_progress_completion 
ON learning_progress(completion_percentage DESC, last_accessed DESC);

-- Agent execution logs indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_logs_timestamp 
ON agent_execution_logs(timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_logs_agent_type 
ON agent_execution_logs(agent_type, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_logs_status 
ON agent_execution_logs(status, timestamp DESC) 
WHERE status IN ('failed', 'error');

-- SPARC state history indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sparc_states_user 
ON sparc_state_history(user_id, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sparc_states_type 
ON sparc_state_history(state_type, timestamp DESC);

-- Partial index for active states
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sparc_active_states 
ON sparc_state_history(user_id, state_type) 
WHERE is_active = true;

-- Roblox game sessions indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_game_sessions_user 
ON roblox_game_sessions(user_id, started_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_game_sessions_active 
ON roblox_game_sessions(server_id) 
WHERE ended_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_game_sessions_duration 
ON roblox_game_sessions(
    EXTRACT(EPOCH FROM (ended_at - started_at))
) WHERE ended_at IS NOT NULL;

-- API request logs indexes (for rate limiting and analytics)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_logs_client 
ON api_request_logs(client_identifier, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_logs_endpoint 
ON api_request_logs(endpoint, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_logs_status 
ON api_request_logs(status_code, timestamp DESC) 
WHERE status_code >= 400;

-- Notifications table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_user 
ON notifications(user_id, created_at DESC) 
WHERE is_read = false;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_type 
ON notifications(notification_type, created_at DESC);

-- ==========================================
-- Materialized Views for Complex Queries
-- ==========================================

-- User activity summary (refresh daily)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_user_activity_summary AS
SELECT 
    u.id as user_id,
    u.email,
    COUNT(DISTINCT qs.id) as total_sessions,
    COUNT(DISTINCT qr.id) as quizzes_taken,
    AVG(qr.score) as avg_quiz_score,
    COUNT(DISTINCT lp.content_id) as content_accessed,
    MAX(u.last_active) as last_active,
    EXTRACT(EPOCH FROM SUM(qs.ended_at - qs.started_at))/3600 as total_hours
FROM users u
LEFT JOIN roblox_game_sessions qs ON u.id = qs.user_id
LEFT JOIN quiz_results qr ON u.id = qr.user_id
LEFT JOIN learning_progress lp ON u.id = lp.user_id
WHERE u.deleted_at IS NULL
GROUP BY u.id, u.email;

CREATE UNIQUE INDEX ON mv_user_activity_summary(user_id);

-- Content performance metrics (refresh hourly)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_content_performance AS
SELECT 
    ec.id as content_id,
    ec.title,
    ec.subject_area,
    ec.grade_level,
    COUNT(DISTINCT lp.user_id) as unique_users,
    AVG(lp.completion_percentage) as avg_completion,
    COUNT(DISTINCT qr.id) as quiz_attempts,
    AVG(qr.score) as avg_quiz_score
FROM educational_content ec
LEFT JOIN learning_progress lp ON ec.id = lp.content_id
LEFT JOIN quiz_results qr ON ec.id = qr.quiz_id
WHERE ec.is_published = true
GROUP BY ec.id, ec.title, ec.subject_area, ec.grade_level;

CREATE UNIQUE INDEX ON mv_content_performance(content_id);

-- ==========================================
-- Performance Optimization Settings
-- ==========================================

-- Analyze tables to update statistics
ANALYZE users;
ANALYZE sessions;
ANALYZE educational_content;
ANALYZE quiz_results;
ANALYZE learning_progress;
ANALYZE agent_execution_logs;
ANALYZE sparc_state_history;
ANALYZE roblox_game_sessions;

-- ==========================================
-- Index Maintenance Commands
-- ==========================================

-- Check index usage (PostgreSQL)
-- Run this query to see which indexes are being used:
/*
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
*/

-- Find missing indexes (PostgreSQL)
-- This query suggests potential new indexes based on query patterns:
/*
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE 
    schemaname NOT IN ('pg_catalog', 'information_schema')
    AND n_distinct > 100
    AND correlation < 0.1
ORDER BY n_distinct DESC;
*/

-- Rebuild indexes periodically (PostgreSQL)
-- REINDEX CONCURRENTLY INDEX idx_name;

-- ==========================================
-- Cleanup and Maintenance
-- ==========================================

-- Remove unused indexes (check pg_stat_user_indexes first)
-- DROP INDEX CONCURRENTLY IF EXISTS idx_name;

-- Vacuum and analyze tables regularly
-- VACUUM ANALYZE tablename;

-- ==========================================
-- Monitoring Queries
-- ==========================================

-- Monitor slow queries
/*
CREATE OR REPLACE VIEW v_slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    rows
FROM pg_stat_statements
WHERE mean_time > 100  -- queries taking more than 100ms
ORDER BY mean_time DESC
LIMIT 20;
*/

-- Monitor table bloat
/*
CREATE OR REPLACE VIEW v_table_bloat AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup,
    n_dead_tup,
    ROUND(100 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_percentage
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
*/