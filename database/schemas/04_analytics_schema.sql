-- ============================================================================
-- ToolboxAI Roblox Environment - Analytics and Monitoring Database Schema
-- ============================================================================
-- This file creates the analytics and monitoring schema for the ToolboxAI platform
-- Run after 01_core_schema.sql, 02_ai_agents_schema.sql, and 03_lms_integration_schema.sql
-- ============================================================================
-- ANALYTICS AND MONITORING MODELS
-- ============================================================================
-- Usage analytics and metrics
CREATE TABLE usage_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Event identification
    event_type VARCHAR(50) NOT NULL,
    -- page_view, content_generation, quiz_attempt
    event_category VARCHAR(50) NOT NULL,
    -- user_action, system_event, error
    event_name VARCHAR(100) NOT NULL,
    -- Context information
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES user_sessions(id),
    content_id UUID REFERENCES educational_content(id),
    agent_id UUID REFERENCES ai_agents(id),
    -- Request/Response data
    endpoint VARCHAR(200),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    -- Geographic and device data
    ip_address INET,
    country VARCHAR(2),
    user_agent TEXT,
    device_type VARCHAR(20),
    -- desktop, mobile, tablet
    browser VARCHAR(50),
    os VARCHAR(50),
    -- Custom properties
    properties JSONB DEFAULT '{}',
    tags JSONB [] DEFAULT '{}',
    -- Performance data
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5, 2),
    database_query_time_ms INTEGER,
    ai_processing_time_ms INTEGER,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);
-- Educational analytics and insights
CREATE TABLE educational_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Educational context
    user_id UUID REFERENCES users(id),
    content_id UUID REFERENCES educational_content(id),
    quiz_id UUID REFERENCES quizzes(id),
    learning_objective_id UUID REFERENCES learning_objectives(id),
    -- Learning metrics
    metric_type VARCHAR(50) NOT NULL,
    -- engagement, comprehension, retention, progress
    metric_value DECIMAL(10, 4) NOT NULL,
    metric_unit VARCHAR(20),
    -- percentage, seconds, count, score
    -- Context and dimensions
    subject VARCHAR(50),
    grade_level INTEGER,
    difficulty_level VARCHAR(20),
    activity_type VARCHAR(50),
    -- Time dimensions
    session_duration_seconds INTEGER,
    time_to_completion_seconds INTEGER,
    attempts_before_success INTEGER,
    -- Comparative data
    peer_average DECIMAL(10, 4),
    -- Average for peer group
    historical_average DECIMAL(10, 4),
    -- User's historical average
    benchmark_value DECIMAL(10, 4),
    -- Target benchmark
    -- Additional context
    context_data JSONB DEFAULT '{}',
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);
-- Error tracking and debugging
CREATE TABLE error_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Error identification
    error_type VARCHAR(50) NOT NULL,
    -- validation, system, network, ai
    error_code VARCHAR(50),
    error_message TEXT NOT NULL,
    error_hash VARCHAR(64),
    -- For duplicate detection
    -- Context information
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES user_sessions(id),
    agent_id UUID REFERENCES ai_agents(id),
    task_id UUID REFERENCES agent_tasks(id),
    -- Request context
    endpoint VARCHAR(200),
    method VARCHAR(10),
    request_data JSONB,
    response_data JSONB,
    -- Technical details
    stack_trace TEXT,
    environment VARCHAR(20),
    -- development, staging, production
    service_name VARCHAR(50),
    service_version VARCHAR(20),
    -- Resolution tracking
    severity VARCHAR(20) DEFAULT 'medium',
    -- low, medium, high, critical
    status VARCHAR(20) DEFAULT 'new',
    -- new, investigating, resolved, ignored
    assigned_to VARCHAR(100),
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    -- Occurrence tracking
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    occurrence_count INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- System health and performance monitoring
CREATE TABLE system_health_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Service identification
    service_name VARCHAR(50) NOT NULL,
    -- fastapi, flask, ghost, dashboard
    service_version VARCHAR(20),
    instance_id VARCHAR(100),
    -- Health status
    status VARCHAR(20) NOT NULL,
    -- healthy, degraded, unhealthy
    overall_score DECIMAL(5, 2),
    -- 0-100 health score
    -- Performance metrics
    response_time_ms INTEGER,
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5, 2),
    disk_usage_percent DECIMAL(5, 2),
    -- Database metrics
    active_connections INTEGER,
    db_response_time_ms INTEGER,
    cache_hit_rate DECIMAL(5, 2),
    -- External dependencies
    external_services_status JSONB,
    -- Status of dependent services
    -- Detailed health data
    health_details JSONB DEFAULT '{}',
    error_messages TEXT [],
    warnings TEXT [],
    checked_at TIMESTAMPTZ DEFAULT NOW()
);
-- API request logs for rate limiting and analytics
CREATE TABLE api_request_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Request identification
    client_identifier VARCHAR(255) NOT NULL,
    -- IP, user_id, or API key
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    -- Request details
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    status_code INTEGER,
    response_time_ms INTEGER,
    -- Rate limiting
    rate_limit_remaining INTEGER,
    rate_limit_reset TIMESTAMPTZ,
    -- Context
    user_agent TEXT,
    ip_address INET,
    country VARCHAR(2),
    -- Additional data
    request_data JSONB,
    response_data JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
-- Notifications system
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    -- Notification content
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    -- info, warning, error, success
    -- Delivery settings
    delivery_method VARCHAR(20) DEFAULT 'in_app',
    -- in_app, email, push, sms
    priority VARCHAR(20) DEFAULT 'normal',
    -- low, normal, high, urgent
    -- Status tracking
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    failure_reason TEXT,
    -- Additional data
    action_url VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);
-- Gamification and achievements
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    -- learning, participation, mastery, social
    icon_url VARCHAR(500),
    -- Achievement criteria
    criteria JSONB NOT NULL,
    -- Conditions to unlock
    points INTEGER DEFAULT 0,
    rarity VARCHAR(20) DEFAULT 'common',
    -- common, uncommon, rare, epic, legendary
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_hidden BOOLEAN DEFAULT false,
    -- Hidden until unlocked
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- User achievements
CREATE TABLE user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    achievement_id UUID REFERENCES achievements(id),
    -- Achievement tracking
    unlocked_at TIMESTAMPTZ DEFAULT NOW(),
    progress_percentage DECIMAL(5, 2) DEFAULT 0,
    progress_data JSONB DEFAULT '{}',
    -- Display settings
    is_featured BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,
    UNIQUE(user_id, achievement_id)
);
-- Leaderboards
CREATE TABLE leaderboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    -- global, class, subject, time_period
    scope JSONB DEFAULT '{}',
    -- Filters for leaderboard scope
    -- Scoring
    scoring_metric VARCHAR(50) NOT NULL,
    -- points, completion_rate, time_spent
    time_period VARCHAR(20) DEFAULT 'all_time',
    -- daily, weekly, monthly, all_time
    -- Settings
    max_entries INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    auto_refresh BOOLEAN DEFAULT true,
    refresh_frequency_hours INTEGER DEFAULT 24,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Leaderboard entries
CREATE TABLE leaderboard_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    leaderboard_id UUID REFERENCES leaderboards(id),
    user_id UUID REFERENCES users(id),
    -- Ranking data
    rank INTEGER NOT NULL,
    score DECIMAL(10, 4) NOT NULL,
    additional_metrics JSONB DEFAULT '{}',
    -- Time tracking
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    UNIQUE(leaderboard_id, user_id)
);
-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================
-- Usage Analytics indexes
CREATE INDEX idx_usage_analytics_event_type ON usage_analytics(event_type, recorded_at DESC);
CREATE INDEX idx_usage_analytics_user ON usage_analytics(user_id, recorded_at DESC);
CREATE INDEX idx_usage_analytics_session ON usage_analytics(session_id, recorded_at DESC);
CREATE INDEX idx_usage_analytics_endpoint ON usage_analytics(endpoint, recorded_at DESC);
CREATE INDEX idx_usage_analytics_timestamp ON usage_analytics(recorded_at DESC);
-- Educational Analytics indexes
CREATE INDEX idx_educational_analytics_user ON educational_analytics(user_id, recorded_at DESC);
CREATE INDEX idx_educational_analytics_metric_type ON educational_analytics(metric_type, recorded_at DESC);
CREATE INDEX idx_educational_analytics_content ON educational_analytics(content_id, metric_type);
CREATE INDEX idx_educational_analytics_quiz ON educational_analytics(quiz_id, metric_type);
-- Error Logs indexes
CREATE INDEX idx_error_logs_type ON error_logs(error_type, created_at DESC);
CREATE INDEX idx_error_logs_user ON error_logs(user_id, created_at DESC);
CREATE INDEX idx_error_logs_status ON error_logs(status, severity, created_at DESC);
CREATE INDEX idx_error_logs_hash ON error_logs(error_hash, occurrence_count DESC);
CREATE INDEX idx_error_logs_service ON error_logs(service_name, created_at DESC);
-- System Health indexes
CREATE INDEX idx_system_health_service ON system_health_checks(service_name, checked_at DESC);
CREATE INDEX idx_system_health_status ON system_health_checks(status, checked_at DESC);
CREATE INDEX idx_system_health_score ON system_health_checks(overall_score, checked_at DESC);
-- API Request Logs indexes
CREATE INDEX idx_api_logs_client ON api_request_logs(client_identifier, timestamp DESC);
CREATE INDEX idx_api_logs_endpoint ON api_request_logs(endpoint, timestamp DESC);
CREATE INDEX idx_api_logs_status ON api_request_logs(status_code, timestamp DESC);
CREATE INDEX idx_api_logs_timestamp ON api_request_logs(timestamp DESC);
-- Notifications indexes
CREATE INDEX idx_notifications_user ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read, created_at DESC)
WHERE is_read = false;
CREATE INDEX idx_notifications_type ON notifications(notification_type, created_at DESC);
CREATE INDEX idx_notifications_expires ON notifications(expires_at)
WHERE expires_at IS NOT NULL;
-- Achievements indexes
CREATE INDEX idx_achievements_category ON achievements(category, is_active);
CREATE INDEX idx_achievements_rarity ON achievements(rarity, is_active);
CREATE INDEX idx_achievements_active ON achievements(is_active, created_at DESC);
-- User Achievements indexes
CREATE INDEX idx_user_achievements_user ON user_achievements(user_id, unlocked_at DESC);
CREATE INDEX idx_user_achievements_achievement ON user_achievements(achievement_id, unlocked_at DESC);
CREATE INDEX idx_user_achievements_featured ON user_achievements(user_id, is_featured, display_order);
-- Leaderboards indexes
CREATE INDEX idx_leaderboards_category ON leaderboards(category, is_active);
CREATE INDEX idx_leaderboards_active ON leaderboards(is_active, auto_refresh);
-- Leaderboard Entries indexes
CREATE INDEX idx_leaderboard_entries_leaderboard ON leaderboard_entries(leaderboard_id, rank);
CREATE INDEX idx_leaderboard_entries_user ON leaderboard_entries(user_id, calculated_at DESC);
CREATE INDEX idx_leaderboard_entries_score ON leaderboard_entries(leaderboard_id, score DESC);
-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================
-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_achievements_updated_at BEFORE
UPDATE ON achievements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_leaderboards_updated_at BEFORE
UPDATE ON leaderboards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- ============================================================================
-- MATERIALIZED VIEWS FOR COMPLEX QUERIES
-- ============================================================================
-- User activity summary (refresh daily)
CREATE MATERIALIZED VIEW mv_user_activity_summary AS
SELECT u.id as user_id,
    u.email,
    COUNT(DISTINCT qs.id) as total_sessions,
    COUNT(DISTINCT qr.id) as quizzes_taken,
    AVG(qr.score) as avg_quiz_score,
    COUNT(DISTINCT lp.content_id) as content_accessed,
    MAX(u.last_login) as last_active,
    EXTRACT(
        EPOCH
        FROM SUM(qs.ended_at - qs.started_at)
    ) / 3600 as total_hours
FROM users u
    LEFT JOIN roblox_game_sessions qs ON u.id = qs.teacher_id
    LEFT JOIN quiz_attempts qr ON u.id = qr.user_id
    LEFT JOIN user_progress lp ON u.id = lp.user_id
WHERE u.is_active = true
GROUP BY u.id,
    u.email;
CREATE UNIQUE INDEX ON mv_user_activity_summary(user_id);
-- Content performance metrics (refresh hourly)
CREATE MATERIALIZED VIEW mv_content_performance AS
SELECT ec.id as content_id,
    ec.title,
    ec.subject,
    ec.grade_level,
    COUNT(DISTINCT lp.user_id) as unique_users,
    AVG(lp.completion_percentage) as avg_completion,
    COUNT(DISTINCT qa.id) as quiz_attempts,
    AVG(qa.score) as avg_quiz_score
FROM educational_content ec
    LEFT JOIN user_progress lp ON ec.id = lp.content_id
    LEFT JOIN quiz_attempts qa ON ec.id = qa.quiz_id
WHERE ec.is_published = true
GROUP BY ec.id,
    ec.title,
    ec.subject,
    ec.grade_level;
CREATE UNIQUE INDEX ON mv_content_performance(content_id);
-- ============================================================================
-- INITIAL ANALYTICS DATA
-- ============================================================================
-- Insert default achievements
INSERT INTO achievements (
        name,
        description,
        category,
        criteria,
        points,
        rarity
    )
VALUES (
        'First Steps',
        'Complete your first lesson',
        'learning',
        '{"type": "lesson_completion", "count": 1}',
        10,
        'common'
    ),
    (
        'Quiz Master',
        'Score 100% on a quiz',
        'mastery',
        '{"type": "quiz_score", "score": 100}',
        25,
        'uncommon'
    ),
    (
        'Dedicated Learner',
        'Complete 10 lessons',
        'learning',
        '{"type": "lesson_completion", "count": 10}',
        50,
        'uncommon'
    ),
    (
        'Speed Demon',
        'Complete a lesson in under 5 minutes',
        'mastery',
        '{"type": "lesson_time", "max_seconds": 300}',
        15,
        'rare'
    ),
    (
        'Social Butterfly',
        'Participate in 5 collaborative sessions',
        'social',
        '{"type": "collaboration_sessions", "count": 5}',
        30,
        'uncommon'
    ),
    (
        'Content Creator',
        'Create your first educational content',
        'participation',
        '{"type": "content_creation", "count": 1}',
        40,
        'rare'
    ),
    (
        'Perfect Score',
        'Score 100% on 5 quizzes',
        'mastery',
        '{"type": "quiz_score", "score": 100, "count": 5}',
        100,
        'epic'
    ),
    (
        'Marathon Runner',
        'Spend 10 hours learning',
        'learning',
        '{"type": "time_spent", "hours": 10}',
        75,
        'rare'
    ),
    (
        'Team Player',
        'Collaborate with 10 different users',
        'social',
        '{"type": "unique_collaborators", "count": 10}',
        60,
        'uncommon'
    ),
    (
        'Legendary Scholar',
        'Complete 100 lessons with 90%+ average',
        'mastery',
        '{"type": "lesson_completion", "count": 100, "min_average": 90}',
        500,
        'legendary'
    );
-- Insert default leaderboards
INSERT INTO leaderboards (
        name,
        description,
        category,
        scoring_metric,
        time_period,
        max_entries
    )
VALUES (
        'Global Learning Leaders',
        'Top learners by total points',
        'global',
        'points',
        'all_time',
        100
    ),
    (
        'Weekly Quiz Champions',
        'Best quiz scores this week',
        'global',
        'quiz_score',
        'weekly',
        50
    ),
    (
        'Subject Masters',
        'Top performers by subject',
        'subject',
        'completion_rate',
        'monthly',
        25
    ),
    (
        'Speed Learners',
        'Fastest lesson completions',
        'global',
        'time_efficiency',
        'daily',
        20
    );
-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$ BEGIN RAISE NOTICE '✅ Analytics and Monitoring database schema created successfully!';
RAISE NOTICE '📊 Analytics tables: usage_analytics, educational_analytics, error_logs, system_health_checks, api_request_logs';
RAISE NOTICE '🔔 Notification tables: notifications, achievements, user_achievements, leaderboards, leaderboard_entries';
RAISE NOTICE '🔍 Performance indexes created for all tables';
RAISE NOTICE '📈 Materialized views created: user_activity_summary, content_performance';
RAISE NOTICE '⚡ Triggers created for automatic timestamp updates';
RAISE NOTICE '🏆 Initial achievements and leaderboards inserted';
END $$;