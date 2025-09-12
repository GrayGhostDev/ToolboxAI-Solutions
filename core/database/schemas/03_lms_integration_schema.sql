-- ============================================================================
-- ToolboxAI Roblox Environment - LMS Integration Database Schema
-- ============================================================================
-- This file creates the LMS integration schema for the ToolboxAI platform
-- Run after 01_core_schema.sql and 02_ai_agents_schema.sql
-- ============================================================================
-- LMS INTEGRATION MODELS
-- ============================================================================
-- LMS platform configurations
CREATE TABLE lms_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_name VARCHAR(50) NOT NULL,
    -- schoology, canvas, blackboard, moodle
    institution_name VARCHAR(200) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    api_version VARCHAR(20),
    -- Authentication configuration
    auth_type VARCHAR(20) NOT NULL,
    -- oauth2, api_key, basic
    client_id VARCHAR(255),
    client_secret_encrypted TEXT,
    api_key_encrypted TEXT,
    auth_endpoint VARCHAR(500),
    token_endpoint VARCHAR(500),
    refresh_token_encrypted TEXT,
    -- Integration settings
    sync_frequency_hours INTEGER DEFAULT 24,
    grade_passback_enabled BOOLEAN DEFAULT true,
    roster_sync_enabled BOOLEAN DEFAULT true,
    content_sync_enabled BOOLEAN DEFAULT true,
    -- Status and monitoring
    is_active BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMPTZ,
    last_sync_status VARCHAR(20),
    -- success, partial, failed
    sync_error_message TEXT,
    health_check_url VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- LMS course synchronization
CREATE TABLE lms_courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lms_integration_id UUID REFERENCES lms_integrations(id),
    external_course_id VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    subject VARCHAR(50),
    grade_level INTEGER,
    instructor_name VARCHAR(200),
    instructor_email VARCHAR(255),
    enrollment_count INTEGER DEFAULT 0,
    start_date DATE,
    end_date DATE,
    -- Synchronization tracking
    last_synced_at TIMESTAMPTZ,
    sync_hash VARCHAR(64),
    -- For change detection
    raw_data JSONB,
    -- Full LMS response
    -- ToolboxAI integration
    linked_content_ids UUID [],
    -- Array of linked educational content
    auto_sync_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(lms_integration_id, external_course_id)
);
-- LMS assignment integration
CREATE TABLE lms_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lms_course_id UUID REFERENCES lms_courses(id),
    external_assignment_id VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    assignment_type VARCHAR(50),
    -- quiz, project, discussion, etc.
    points_possible DECIMAL(8, 2),
    due_date TIMESTAMPTZ,
    unlock_date TIMESTAMPTZ,
    lock_date TIMESTAMPTZ,
    -- ToolboxAI integration
    toolboxai_content_id UUID REFERENCES educational_content(id),
    toolboxai_quiz_id UUID REFERENCES quizzes(id),
    grade_passback_enabled BOOLEAN DEFAULT true,
    -- Synchronization
    last_synced_at TIMESTAMPTZ,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(lms_course_id, external_assignment_id)
);
-- Grade passback tracking
CREATE TABLE lms_grade_passbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lms_assignment_id UUID REFERENCES lms_assignments(id),
    user_id UUID REFERENCES users(id),
    external_user_id VARCHAR(100) NOT NULL,
    -- Grade information
    score DECIMAL(8, 2),
    points_possible DECIMAL(8, 2),
    percentage DECIMAL(5, 2),
    letter_grade VARCHAR(5),
    -- Passback status
    status VARCHAR(20) DEFAULT 'pending',
    -- pending, success, failed
    attempt_count INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    error_message TEXT,
    -- Source data
    quiz_attempt_id UUID REFERENCES quiz_attempts(id),
    progress_id UUID REFERENCES user_progress(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- LMS user synchronization
CREATE TABLE lms_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lms_integration_id UUID REFERENCES lms_integrations(id),
    external_user_id VARCHAR(100) NOT NULL,
    toolboxai_user_id UUID REFERENCES users(id),
    -- User information from LMS
    lms_username VARCHAR(100),
    lms_email VARCHAR(255),
    lms_first_name VARCHAR(100),
    lms_last_name VARCHAR(100),
    lms_role VARCHAR(50),
    -- student, teacher, admin
    -- Synchronization tracking
    last_synced_at TIMESTAMPTZ,
    sync_status VARCHAR(20) DEFAULT 'active',
    -- active, inactive, error
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(lms_integration_id, external_user_id)
);
-- LMS enrollment synchronization
CREATE TABLE lms_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lms_course_id UUID REFERENCES lms_courses(id),
    lms_user_id UUID REFERENCES lms_users(id),
    external_enrollment_id VARCHAR(100),
    -- Enrollment information
    role VARCHAR(50),
    -- student, teacher, ta, observer
    status VARCHAR(20) DEFAULT 'active',
    -- active, inactive, completed, dropped
    enrollment_date TIMESTAMPTZ,
    completion_date TIMESTAMPTZ,
    -- Synchronization tracking
    last_synced_at TIMESTAMPTZ,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(lms_course_id, lms_user_id)
);
-- ============================================================================
-- REAL-TIME COLLABORATION MODELS
-- ============================================================================
-- WebSocket connection management
CREATE TABLE websocket_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES user_sessions(id),
    connection_id VARCHAR(100) UNIQUE NOT NULL,
    socket_id VARCHAR(100) UNIQUE NOT NULL,
    -- Connection context
    connection_type VARCHAR(20) NOT NULL,
    -- dashboard, roblox, plugin, mobile
    client_info JSONB,
    -- Browser, device, version info
    -- Channel subscriptions
    subscribed_channels JSONB [],
    -- Array of channel names
    permissions JSONB,
    -- Channel-specific permissions
    -- Connection state
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    last_ping TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    disconnected_at TIMESTAMPTZ,
    disconnect_reason VARCHAR(100),
    -- Rate limiting
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMPTZ,
    rate_limit_hits INTEGER DEFAULT 0
);
-- Real-time collaboration sessions
CREATE TABLE collaboration_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES educational_content(id),
    session_name VARCHAR(200) NOT NULL,
    session_type VARCHAR(20) NOT NULL,
    -- content_editing, live_class, review
    -- Session management
    owner_id UUID REFERENCES users(id),
    max_participants INTEGER DEFAULT 30,
    current_participants INTEGER DEFAULT 0,
    require_approval BOOLEAN DEFAULT false,
    -- Session state
    status VARCHAR(20) DEFAULT 'planning',
    -- planning, active, paused, ended
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    -- Collaboration data
    shared_state JSONB DEFAULT '{}',
    -- Current shared state
    change_log JSONB [] DEFAULT '{}',
    -- History of changes
    -- Settings
    settings JSONB DEFAULT '{}',
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Collaboration participants
CREATE TABLE collaboration_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES collaboration_sessions(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(20) DEFAULT 'participant',
    -- owner, moderator, participant, observer
    -- Participation tracking
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    left_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    contribution_count INTEGER DEFAULT 0,
    last_contribution TIMESTAMPTZ,
    -- Permissions and status
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    muted BOOLEAN DEFAULT false,
    PRIMARY KEY (session_id, user_id)
);
-- Real-time change tracking
CREATE TABLE collaboration_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES collaboration_sessions(id),
    user_id UUID REFERENCES users(id),
    change_type VARCHAR(50) NOT NULL,
    -- content_edit, script_update, terrain_modify
    -- Change details
    target_object VARCHAR(100),
    -- What was changed
    change_data JSONB NOT NULL,
    -- Detailed change information
    previous_state JSONB,
    -- State before change
    new_state JSONB,
    -- State after change
    -- Change metadata
    change_sequence INTEGER NOT NULL,
    -- Order of changes
    applied BOOLEAN DEFAULT true,
    conflict_resolution JSONB,
    -- If conflicts occurred
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================
-- LMS Integration indexes
CREATE INDEX idx_lms_integrations_platform ON lms_integrations(platform_name, is_active);
CREATE INDEX idx_lms_integrations_institution ON lms_integrations(institution_name);
CREATE INDEX idx_lms_integrations_sync ON lms_integrations(last_sync_at DESC)
WHERE is_active = true;
-- LMS Course indexes
CREATE INDEX idx_lms_courses_integration ON lms_courses(lms_integration_id, last_synced_at DESC);
CREATE INDEX idx_lms_courses_external ON lms_courses(external_course_id);
CREATE INDEX idx_lms_courses_sync ON lms_courses(auto_sync_enabled, last_synced_at DESC);
-- LMS Assignment indexes
CREATE INDEX idx_lms_assignments_course ON lms_assignments(lms_course_id, due_date DESC);
CREATE INDEX idx_lms_assignments_external ON lms_assignments(external_assignment_id);
CREATE INDEX idx_lms_assignments_toolboxai ON lms_assignments(toolboxai_content_id, toolboxai_quiz_id);
-- LMS Grade Passback indexes
CREATE INDEX idx_lms_grade_passbacks_assignment ON lms_grade_passbacks(lms_assignment_id, status);
CREATE INDEX idx_lms_grade_passbacks_user ON lms_grade_passbacks(user_id, created_at DESC);
CREATE INDEX idx_lms_grade_passbacks_status ON lms_grade_passbacks(status, last_attempt_at DESC);
-- LMS User indexes
CREATE INDEX idx_lms_users_integration ON lms_users(lms_integration_id, sync_status);
CREATE INDEX idx_lms_users_external ON lms_users(external_user_id);
CREATE INDEX idx_lms_users_toolboxai ON lms_users(toolboxai_user_id);
-- LMS Enrollment indexes
CREATE INDEX idx_lms_enrollments_course ON lms_enrollments(lms_course_id, status);
CREATE INDEX idx_lms_enrollments_user ON lms_enrollments(lms_user_id, status);
CREATE INDEX idx_lms_enrollments_role ON lms_enrollments(role, status);
-- WebSocket Connection indexes
CREATE INDEX idx_websocket_connections_user ON websocket_connections(user_id, is_active);
CREATE INDEX idx_websocket_connections_active ON websocket_connections(is_active, last_ping DESC);
CREATE INDEX idx_websocket_connections_type ON websocket_connections(connection_type, is_active);
-- Collaboration Session indexes
CREATE INDEX idx_collaboration_sessions_owner ON collaboration_sessions(owner_id, status);
CREATE INDEX idx_collaboration_sessions_content ON collaboration_sessions(content_id, status);
CREATE INDEX idx_collaboration_sessions_active ON collaboration_sessions(status, last_activity DESC);
-- Collaboration Participant indexes
CREATE INDEX idx_collaboration_participants_session ON collaboration_participants(session_id, is_active);
CREATE INDEX idx_collaboration_participants_user ON collaboration_participants(user_id, joined_at DESC);
-- Collaboration Change indexes
CREATE INDEX idx_collaboration_changes_session ON collaboration_changes(session_id, change_sequence);
CREATE INDEX idx_collaboration_changes_user ON collaboration_changes(user_id, created_at DESC);
CREATE INDEX idx_collaboration_changes_type ON collaboration_changes(change_type, created_at DESC);
-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================
-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_lms_integrations_updated_at BEFORE
UPDATE ON lms_integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lms_courses_updated_at BEFORE
UPDATE ON lms_courses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lms_assignments_updated_at BEFORE
UPDATE ON lms_assignments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lms_grade_passbacks_updated_at BEFORE
UPDATE ON lms_grade_passbacks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lms_users_updated_at BEFORE
UPDATE ON lms_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lms_enrollments_updated_at BEFORE
UPDATE ON lms_enrollments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_collaboration_sessions_updated_at BEFORE
UPDATE ON collaboration_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- ============================================================================
-- INITIAL LMS INTEGRATION DATA
-- ============================================================================
-- Insert default LMS integration templates
INSERT INTO lms_integrations (
        platform_name,
        institution_name,
        base_url,
        auth_type,
        sync_frequency_hours,
        is_active
    )
VALUES (
        'canvas',
        'Example University',
        'https://university.instructure.com',
        'oauth2',
        24,
        false
    ),
    (
        'schoology',
        'Example School District',
        'https://district.schoology.com',
        'oauth2',
        12,
        false
    ),
    (
        'blackboard',
        'Example College',
        'https://college.blackboard.com',
        'oauth2',
        24,
        false
    ),
    (
        'moodle',
        'Example Institution',
        'https://moodle.institution.edu',
        'api_key',
        6,
        false
    );
-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$ BEGIN RAISE NOTICE '✅ LMS Integration database schema created successfully!';
RAISE NOTICE '🏫 LMS Integration tables: lms_integrations, lms_courses, lms_assignments, lms_grade_passbacks, lms_users, lms_enrollments';
RAISE NOTICE '⚡ Real-time Collaboration tables: websocket_connections, collaboration_sessions, collaboration_participants, collaboration_changes';
RAISE NOTICE '🔍 Performance indexes created for all tables';
RAISE NOTICE '⚡ Triggers created for automatic timestamp updates';
RAISE NOTICE '📝 Initial LMS integration templates inserted: Canvas, Schoology, Blackboard, Moodle';
END $$;