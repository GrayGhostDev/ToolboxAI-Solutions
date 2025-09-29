-- ============================================
-- TOOLBOXAI POSTGRESQL INITIALIZATION SCRIPT
-- ============================================
-- Database initialization for ToolBoxAI platform
-- Security-hardened with proper roles and permissions
-- Updated: 2025-09-25
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ============================================
-- ROLE MANAGEMENT
-- ============================================

-- Create application-specific roles
DO $$
BEGIN
    -- Main application role
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'toolboxai_app') THEN
        CREATE ROLE toolboxai_app WITH
            LOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            PASSWORD 'toolboxai_app_secure_2024';
    END IF;

    -- Read-only role for analytics/reporting
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'toolboxai_readonly') THEN
        CREATE ROLE toolboxai_readonly WITH
            LOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            PASSWORD 'toolboxai_readonly_2024';
    END IF;

    -- Migration role for database updates
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'toolboxai_migration') THEN
        CREATE ROLE toolboxai_migration WITH
            LOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            PASSWORD 'toolboxai_migration_2024';
    END IF;
END
$$;

-- ============================================
-- DATABASE CONFIGURATION
-- ============================================

-- Set application name for better monitoring
ALTER DATABASE toolboxai SET application_name = 'ToolBoxAI Platform';

-- Optimize for application workload
ALTER DATABASE toolboxai SET shared_preload_libraries = 'pg_stat_statements';
ALTER DATABASE toolboxai SET log_statement = 'mod';
ALTER DATABASE toolboxai SET log_min_duration_statement = 1000;

-- ============================================
-- SCHEMA CREATION
-- ============================================

-- Core application schemas
CREATE SCHEMA IF NOT EXISTS auth AUTHORIZATION toolboxai_app;
CREATE SCHEMA IF NOT EXISTS users AUTHORIZATION toolboxai_app;
CREATE SCHEMA IF NOT EXISTS content AUTHORIZATION toolboxai_app;
CREATE SCHEMA IF NOT EXISTS agents AUTHORIZATION toolboxai_app;
CREATE SCHEMA IF NOT EXISTS roblox AUTHORIZATION toolboxai_app;
CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION toolboxai_app;
CREATE SCHEMA IF NOT EXISTS system AUTHORIZATION toolboxai_app;

-- ============================================
-- BASE TABLES (if not created by Alembic)
-- ============================================

-- System configuration table
CREATE TABLE IF NOT EXISTS system.config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Application health monitoring
CREATE TABLE IF NOT EXISTS system.health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('healthy', 'unhealthy', 'degraded')),
    details JSONB,
    response_time_ms INTEGER,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User authentication base table (minimal - Alembic will extend)
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email CITEXT NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(20) DEFAULT 'student' CHECK (role IN ('student', 'teacher', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- User sessions for authentication tracking
CREATE TABLE IF NOT EXISTS auth.user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    refresh_token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address INET
);

-- Agent coordination tracking
CREATE TABLE IF NOT EXISTS agents.agent_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'idle' CHECK (status IN ('idle', 'running', 'paused', 'error', 'stopped')),
    config JSONB NOT NULL DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP WITH TIME ZONE
);

-- Agent task queue
CREATE TABLE IF NOT EXISTS agents.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents.agent_instances(id) ON DELETE CASCADE,
    task_type VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Authentication indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON auth.users USING btree (email);
CREATE INDEX IF NOT EXISTS idx_users_username ON auth.users USING btree (username);
CREATE INDEX IF NOT EXISTS idx_users_active ON auth.users USING btree (is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_sessions_user ON auth.user_sessions USING btree (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON auth.user_sessions USING btree (session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON auth.user_sessions USING btree (expires_at);

-- Agent indexes
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents.agent_instances USING btree (agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents.agent_instances USING btree (status);
CREATE INDEX IF NOT EXISTS idx_agents_heartbeat ON agents.agent_instances USING btree (last_heartbeat);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON agents.tasks USING btree (agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON agents.tasks USING btree (status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON agents.tasks USING btree (priority DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON agents.tasks USING btree (created_at);

-- System monitoring indexes
CREATE INDEX IF NOT EXISTS idx_health_service ON system.health_checks USING btree (service_name);
CREATE INDEX IF NOT EXISTS idx_health_status ON system.health_checks USING btree (status);
CREATE INDEX IF NOT EXISTS idx_health_checked ON system.health_checks USING btree (checked_at);

-- ============================================
-- FUNCTIONS AND TRIGGERS
-- ============================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
DROP TRIGGER IF EXISTS update_users_updated_at ON auth.users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_agents_updated_at ON agents.agent_instances;
CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents.agent_instances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_config_updated_at ON system.config;
CREATE TRIGGER update_config_updated_at
    BEFORE UPDATE ON system.config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- PERMISSIONS AND SECURITY
-- ============================================

-- Grant schema usage permissions
GRANT USAGE ON SCHEMA auth TO toolboxai_app;
GRANT USAGE ON SCHEMA users TO toolboxai_app;
GRANT USAGE ON SCHEMA content TO toolboxai_app;
GRANT USAGE ON SCHEMA agents TO toolboxai_app;
GRANT USAGE ON SCHEMA roblox TO toolboxai_app;
GRANT USAGE ON SCHEMA analytics TO toolboxai_app;
GRANT USAGE ON SCHEMA system TO toolboxai_app;

-- Grant table permissions to application role
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA auth TO toolboxai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA users TO toolboxai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA content TO toolboxai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA agents TO toolboxai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA roblox TO toolboxai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analytics TO toolboxai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA system TO toolboxai_app;

-- Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA auth TO toolboxai_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA users TO toolboxai_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA content TO toolboxai_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA agents TO toolboxai_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA roblox TO toolboxai_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA analytics TO toolboxai_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA system TO toolboxai_app;

-- Read-only role permissions
GRANT USAGE ON SCHEMA auth, users, content, agents, roblox, analytics, system TO toolboxai_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA auth TO toolboxai_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA users TO toolboxai_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA content TO toolboxai_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA agents TO toolboxai_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA roblox TO toolboxai_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO toolboxai_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA system TO toolboxai_readonly;

-- Migration role permissions (for Alembic)
GRANT ALL PRIVILEGES ON SCHEMA auth, users, content, agents, roblox, analytics, system TO toolboxai_migration;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO toolboxai_migration;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA users TO toolboxai_migration;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA content TO toolboxai_migration;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agents TO toolboxai_migration;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA roblox TO toolboxai_migration;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO toolboxai_migration;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA system TO toolboxai_migration;

-- Grant permissions on future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO toolboxai_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA users GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO toolboxai_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA content GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO toolboxai_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA agents GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO toolboxai_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA roblox GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO toolboxai_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO toolboxai_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA system GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO toolboxai_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT SELECT ON TABLES TO toolboxai_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA users GRANT SELECT ON TABLES TO toolboxai_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA content GRANT SELECT ON TABLES TO toolboxai_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA agents GRANT SELECT ON TABLES TO toolboxai_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA roblox GRANT SELECT ON TABLES TO toolboxai_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO toolboxai_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA system GRANT SELECT ON TABLES TO toolboxai_readonly;

-- ============================================
-- INITIAL DATA
-- ============================================

-- Insert default system configuration
INSERT INTO system.config (key, value, description) VALUES
    ('app_version', '"1.0.0"', 'Current application version'),
    ('maintenance_mode', 'false', 'Enable maintenance mode'),
    ('max_agent_instances', '10', 'Maximum concurrent agent instances'),
    ('session_timeout_hours', '24', 'User session timeout in hours'),
    ('enable_analytics', 'true', 'Enable analytics collection'),
    ('roblox_integration_enabled', 'true', 'Enable Roblox integration features')
ON CONFLICT (key) DO NOTHING;

-- Create default admin user (password: admin123 - CHANGE IN PRODUCTION)
INSERT INTO auth.users (email, username, password_hash, role, is_verified) VALUES
    ('admin@toolboxai.dev', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewwuaOI5zNXTeBPu', 'admin', TRUE)
ON CONFLICT (email) DO NOTHING;

-- ============================================
-- LOGGING AND MONITORING
-- ============================================

-- Log successful initialization
INSERT INTO system.health_checks (service_name, status, details)
VALUES ('postgres_init', 'healthy', '{"message": "Database initialization completed successfully", "timestamp": "' || CURRENT_TIMESTAMP || '"}');

-- Enable row-level security (RLS) preparation
-- Note: RLS policies should be defined by the application, not here

COMMIT;

-- Final message
DO $$
BEGIN
    RAISE NOTICE 'ToolBoxAI PostgreSQL initialization completed successfully!';
    RAISE NOTICE 'Database version: %', version();
    RAISE NOTICE 'Extensions enabled: uuid-ossp, citext, pg_trgm, btree_gin';
    RAISE NOTICE 'Schemas created: auth, users, content, agents, roblox, analytics, system';
    RAISE NOTICE 'Default admin user created: admin@toolboxai.dev (CHANGE PASSWORD IN PRODUCTION)';
END
$$;