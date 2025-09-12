-- ============================================================================
-- ToolboxAI Roblox Environment - AI Agents Database Schema
-- ============================================================================
-- This file creates the AI agent system schema for the ToolboxAI platform
-- Run after 01_core_schema.sql
-- ============================================================================
-- AI AGENT SYSTEM MODELS
-- ============================================================================
-- AI agent definitions and configurations
CREATE TABLE ai_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    agent_type VARCHAR(50) NOT NULL,
    -- supervisor, content, quiz, terrain, script, review
    description TEXT,
    version VARCHAR(20) NOT NULL,
    model_config JSONB NOT NULL,
    -- LLM and framework config
    capabilities JSONB [],
    -- Array of capabilities
    dependencies JSONB [],
    -- Agent dependencies
    priority INTEGER DEFAULT 5,
    max_concurrent_tasks INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 300,
    retry_count INTEGER DEFAULT 3,
    is_active BOOLEAN DEFAULT true,
    health_check_url VARCHAR(500),
    last_health_check TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Agent task management and workflow tracking
CREATE TABLE agent_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES ai_agents(id),
    parent_task_id UUID REFERENCES agent_tasks(id),
    -- For sub-tasks
    workflow_id UUID,
    -- Groups related tasks
    task_type VARCHAR(50) NOT NULL,
    task_name VARCHAR(200) NOT NULL,
    input_data JSONB NOT NULL,
    output_data JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    -- pending, running, completed, failed, cancelled
    priority INTEGER DEFAULT 5,
    created_by UUID REFERENCES users(id),
    assigned_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    error_details JSONB,
    progress_percentage INTEGER DEFAULT 0,
    intermediate_results JSONB,
    -- For long-running tasks
    context_data JSONB,
    -- SPARC framework context
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Agent state management for SPARC framework
CREATE TABLE agent_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES ai_agents(id),
    workflow_id UUID NOT NULL,
    state_type VARCHAR(50) NOT NULL,
    -- situation, problem, action, result, context
    state_data JSONB NOT NULL,
    sequence_number INTEGER NOT NULL,
    quality_score DECIMAL(3, 2),
    -- Quality assessment
    confidence_score DECIMAL(3, 2),
    -- Confidence level
    reviewed_by UUID REFERENCES ai_agents(id),
    -- Review agent
    approved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(workflow_id, state_type, sequence_number)
);
-- Agent performance metrics and learning
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES ai_agents(id),
    task_id UUID REFERENCES agent_tasks(id),
    metric_type VARCHAR(50) NOT NULL,
    -- execution_time, success_rate, quality_score
    metric_value DECIMAL(10, 4) NOT NULL,
    benchmark_value DECIMAL(10, 4),
    context JSONB,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);
-- Agent communication and coordination
CREATE TABLE agent_communications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_agent_id UUID REFERENCES ai_agents(id),
    receiver_agent_id UUID REFERENCES ai_agents(id),
    workflow_id UUID NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    -- request, response, notification, error
    message_content JSONB NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    -- low, normal, high, urgent
    status VARCHAR(20) DEFAULT 'sent',
    -- sent, delivered, read, failed
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    response_required BOOLEAN DEFAULT false,
    response_deadline TIMESTAMPTZ
);
-- Agent learning and adaptation data
CREATE TABLE agent_learning_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES ai_agents(id),
    learning_type VARCHAR(50) NOT NULL,
    -- feedback, performance, user_interaction
    input_data JSONB NOT NULL,
    expected_output JSONB,
    actual_output JSONB,
    feedback_score DECIMAL(3, 2),
    learning_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- ============================================================================
-- ROBLOX INTEGRATION MODELS
-- ============================================================================
-- Roblox Studio plugin registrations
CREATE TABLE roblox_plugins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    studio_id VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id),
    plugin_version VARCHAR(20) NOT NULL,
    port INTEGER DEFAULT 64989,
    capabilities JSONB [],
    -- Plugin capabilities
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    last_heartbeat TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active',
    -- active, inactive, error
    error_message TEXT,
    connection_metadata JSONB,
    UNIQUE(studio_id, user_id)
);
-- Generated Roblox scripts and assets
CREATE TABLE roblox_scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES educational_content(id),
    name VARCHAR(200) NOT NULL,
    script_type VARCHAR(20) NOT NULL,
    -- server, client, module
    content TEXT NOT NULL,
    dependencies JSONB [],
    description TEXT,
    roblox_version VARCHAR(20),
    performance_metrics JSONB,
    tested BOOLEAN DEFAULT false,
    test_results JSONB,
    deployed_to_studio BOOLEAN DEFAULT false,
    created_by UUID REFERENCES users(id),
    reviewed_by UUID REFERENCES ai_agents(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Terrain generation data and configurations
CREATE TABLE roblox_terrain (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES educational_content(id),
    name VARCHAR(200) NOT NULL,
    terrain_type VARCHAR(50) NOT NULL,
    material VARCHAR(50) DEFAULT 'Grass',
    size VARCHAR(20) DEFAULT 'medium',
    biome VARCHAR(50) DEFAULT 'temperate',
    features JSONB [],
    -- hills, water, caves, etc.
    elevation_data JSONB,
    -- Height map data
    generation_script TEXT,
    preview_image_url VARCHAR(500),
    complexity_score INTEGER DEFAULT 1,
    educational_context JSONB,
    performance_impact JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- Roblox game instances and sessions
CREATE TABLE roblox_game_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES educational_content(id),
    teacher_id UUID REFERENCES users(id),
    roblox_place_id BIGINT,
    roblox_universe_id BIGINT,
    session_name VARCHAR(200) NOT NULL,
    max_players INTEGER DEFAULT 30,
    current_players INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'planning',
    -- planning, active, paused, completed
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    session_data JSONB,
    -- Game state, player progress
    analytics_data JSONB,
    -- Performance metrics
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- Player participation in Roblox sessions
CREATE TABLE roblox_player_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_session_id UUID REFERENCES roblox_game_sessions(id),
    user_id UUID REFERENCES users(id),
    roblox_user_id BIGINT,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    left_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    progress_data JSONB,
    -- Learning progress
    achievements JSONB [],
    -- Earned achievements
    performance_metrics JSONB
);
-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================
-- AI Agent indexes
CREATE INDEX idx_ai_agents_type ON ai_agents(agent_type, is_active);
CREATE INDEX idx_ai_agents_active ON ai_agents(is_active, priority DESC);
CREATE INDEX idx_ai_agents_health ON ai_agents(last_health_check DESC)
WHERE is_active = true;
-- Agent Task indexes
CREATE INDEX idx_agent_tasks_agent ON agent_tasks(agent_id, status, created_at DESC);
CREATE INDEX idx_agent_tasks_workflow ON agent_tasks(workflow_id, status);
CREATE INDEX idx_agent_tasks_status ON agent_tasks(status, priority DESC, created_at ASC);
CREATE INDEX idx_agent_tasks_created_by ON agent_tasks(created_by, created_at DESC);
-- Agent State indexes
CREATE INDEX idx_agent_states_workflow ON agent_states(workflow_id, sequence_number);
CREATE INDEX idx_agent_states_type ON agent_states(state_type, created_at DESC);
CREATE INDEX idx_agent_states_agent ON agent_states(agent_id, created_at DESC);
-- Agent Metrics indexes
CREATE INDEX idx_agent_metrics_agent ON agent_metrics(agent_id, recorded_at DESC);
CREATE INDEX idx_agent_metrics_type ON agent_metrics(metric_type, recorded_at DESC);
CREATE INDEX idx_agent_metrics_task ON agent_metrics(task_id, metric_type);
-- Agent Communication indexes
CREATE INDEX idx_agent_comm_sender ON agent_communications(sender_agent_id, sent_at DESC);
CREATE INDEX idx_agent_comm_receiver ON agent_communications(receiver_agent_id, status, sent_at DESC);
CREATE INDEX idx_agent_comm_workflow ON agent_communications(workflow_id, sent_at DESC);
-- Roblox Plugin indexes
CREATE INDEX idx_roblox_plugins_user ON roblox_plugins(user_id, status);
CREATE INDEX idx_roblox_plugins_studio ON roblox_plugins(studio_id, status);
CREATE INDEX idx_roblox_plugins_heartbeat ON roblox_plugins(last_heartbeat DESC)
WHERE status = 'active';
-- Roblox Script indexes
CREATE INDEX idx_roblox_scripts_content ON roblox_scripts(content_id, script_type);
CREATE INDEX idx_roblox_scripts_creator ON roblox_scripts(created_by, created_at DESC);
CREATE INDEX idx_roblox_scripts_deployed ON roblox_scripts(deployed_to_studio, created_at DESC);
-- Roblox Terrain indexes
CREATE INDEX idx_roblox_terrain_content ON roblox_terrain(content_id, terrain_type);
CREATE INDEX idx_roblox_terrain_creator ON roblox_terrain(created_by, created_at DESC);
-- Roblox Game Session indexes
CREATE INDEX idx_roblox_sessions_teacher ON roblox_game_sessions(teacher_id, started_at DESC);
CREATE INDEX idx_roblox_sessions_status ON roblox_game_sessions(status, started_at DESC);
CREATE INDEX idx_roblox_sessions_content ON roblox_game_sessions(content_id, started_at DESC);
-- Roblox Player Session indexes
CREATE INDEX idx_roblox_player_sessions_user ON roblox_player_sessions(user_id, joined_at DESC);
CREATE INDEX idx_roblox_player_sessions_game ON roblox_player_sessions(game_session_id, joined_at DESC);
-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================
-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_ai_agents_updated_at BEFORE
UPDATE ON ai_agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agent_tasks_updated_at BEFORE
UPDATE ON agent_tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_roblox_scripts_updated_at BEFORE
UPDATE ON roblox_scripts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- ============================================================================
-- INITIAL AI AGENT DATA
-- ============================================================================
-- Insert default AI agents
INSERT INTO ai_agents (
        name,
        agent_type,
        description,
        version,
        model_config,
        capabilities,
        dependencies,
        priority
    )
VALUES (
        'supervisor_agent',
        'supervisor',
        'Main orchestration agent that coordinates all other agents',
        '1.0.0',
        '{"model": "gpt-4", "temperature": 0.7, "max_tokens": 2000}',
        '["orchestration", "task_management", "workflow_coordination"]',
        '[]',
        100
    ),
    (
        'content_agent',
        'content',
        'Generates educational content and lesson plans',
        '1.0.0',
        '{"model": "gpt-4", "temperature": 0.8, "max_tokens": 3000}',
        '["content_generation", "lesson_planning", "curriculum_alignment"]',
        '["supervisor_agent"]',
        80
    ),
    (
        'quiz_agent',
        'quiz',
        'Creates and manages quizzes and assessments',
        '1.0.0',
        '{"model": "gpt-4", "temperature": 0.6, "max_tokens": 2000}',
        '["quiz_generation", "assessment_creation", "adaptive_learning"]',
        '["supervisor_agent", "content_agent"]',
        70
    ),
    (
        'terrain_agent',
        'terrain',
        'Generates 3D terrain and environments for Roblox',
        '1.0.0',
        '{"model": "gpt-4", "temperature": 0.7, "max_tokens": 1500}',
        '["terrain_generation", "environment_design", "3d_modeling"]',
        '["supervisor_agent", "content_agent"]',
        60
    ),
    (
        'script_agent',
        'script',
        'Generates Lua scripts for Roblox games',
        '1.0.0',
        '{"model": "gpt-4", "temperature": 0.5, "max_tokens": 4000}',
        '["lua_scripting", "roblox_api", "game_mechanics"]',
        '["supervisor_agent", "content_agent", "terrain_agent"]',
        50
    ),
    (
        'review_agent',
        'review',
        'Reviews and validates generated content',
        '1.0.0',
        '{"model": "gpt-4", "temperature": 0.3, "max_tokens": 2000}',
        '["content_review", "quality_assurance", "validation"]',
        '["supervisor_agent"]',
        90
    );
-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$ BEGIN RAISE NOTICE '✅ AI Agents database schema created successfully!';
RAISE NOTICE '🤖 AI Agent tables: ai_agents, agent_tasks, agent_states, agent_metrics, agent_communications, agent_learning_data';
RAISE NOTICE '🎮 Roblox Integration tables: roblox_plugins, roblox_scripts, roblox_terrain, roblox_game_sessions, roblox_player_sessions';
RAISE NOTICE '🔍 Performance indexes created for all tables';
RAISE NOTICE '⚡ Triggers created for automatic timestamp updates';
RAISE NOTICE '📝 Initial AI agents inserted: supervisor, content, quiz, terrain, script, review';
END $$;