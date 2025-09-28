-- Create Agent System Tables for Supabase
-- Migration: 001_create_agent_system_tables
-- Created: 2025-09-21
-- Version: 1.0.0

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE agent_type AS ENUM (
    'content_generator',
    'quiz_generator', 
    'terrain_generator',
    'script_generator',
    'code_reviewer',
    'roblox_asset',
    'roblox_testing',
    'roblox_analytics'
);

CREATE TYPE agent_status AS ENUM (
    'initializing',
    'idle',
    'busy', 
    'processing',
    'waiting',
    'error',
    'offline',
    'maintenance'
);

CREATE TYPE task_status AS ENUM (
    'pending',
    'queued',
    'running',
    'completed',
    'failed',
    'cancelled',
    'retrying'
);

CREATE TYPE task_priority AS ENUM (
    'low',
    'normal',
    'high',
    'urgent',
    'critical'
);

-- Agent Instances Table
CREATE TABLE agent_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id TEXT UNIQUE NOT NULL,
    agent_type agent_type NOT NULL,
    status agent_status NOT NULL DEFAULT 'initializing',
    
    -- Configuration
    configuration JSONB DEFAULT '{}',
    resource_limits JSONB DEFAULT '{}',
    performance_thresholds JSONB DEFAULT '{}',
    
    -- Current state
    current_task_id TEXT,
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    
    -- Performance counters
    total_tasks_completed INTEGER DEFAULT 0,
    total_tasks_failed INTEGER DEFAULT 0,
    total_execution_time FLOAT DEFAULT 0.0,
    average_execution_time FLOAT DEFAULT 0.0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent Executions Table
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id TEXT UNIQUE NOT NULL,
    
    -- Agent reference
    agent_instance_id UUID REFERENCES agent_instances(id) ON DELETE CASCADE,
    agent_type agent_type NOT NULL,
    
    -- Task details
    task_type TEXT NOT NULL,
    priority task_priority DEFAULT 'normal',
    
    -- Task data
    input_data JSONB NOT NULL DEFAULT '{}',
    output_data JSONB,
    context_data JSONB DEFAULT '{}',
    
    -- Execution status
    status task_status NOT NULL DEFAULT 'pending',
    error_message TEXT,
    error_details JSONB,
    
    -- Performance metrics
    execution_time_seconds FLOAT,
    memory_usage_mb FLOAT,
    cpu_usage_percent FLOAT,
    
    -- Quality metrics
    quality_score FLOAT CHECK (quality_score >= 0 AND quality_score <= 1),
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- User context
    user_id UUID,
    session_id TEXT,
    
    -- Retry information
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    max_retries INTEGER DEFAULT 3,
    parent_task_id TEXT
);

-- Agent Metrics Table
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Agent reference
    agent_instance_id UUID REFERENCES agent_instances(id) ON DELETE CASCADE,
    agent_type agent_type NOT NULL,
    
    -- Time period
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    period_duration_minutes INTEGER NOT NULL,
    
    -- Task metrics
    tasks_completed INTEGER DEFAULT 0,
    tasks_failed INTEGER DEFAULT 0,
    tasks_cancelled INTEGER DEFAULT 0,
    total_tasks INTEGER DEFAULT 0,
    
    -- Performance metrics
    success_rate FLOAT DEFAULT 0.0 CHECK (success_rate >= 0 AND success_rate <= 100),
    error_rate FLOAT DEFAULT 0.0 CHECK (error_rate >= 0 AND error_rate <= 100),
    average_execution_time FLOAT DEFAULT 0.0,
    median_execution_time FLOAT DEFAULT 0.0,
    p95_execution_time FLOAT DEFAULT 0.0,
    
    -- Throughput metrics
    tasks_per_minute FLOAT DEFAULT 0.0,
    tasks_per_hour FLOAT DEFAULT 0.0,
    
    -- Quality metrics
    average_quality_score FLOAT DEFAULT 0.0,
    average_confidence_score FLOAT DEFAULT 0.0,
    average_user_rating FLOAT DEFAULT 0.0,
    
    -- Resource metrics
    average_memory_usage_mb FLOAT DEFAULT 0.0,
    peak_memory_usage_mb FLOAT DEFAULT 0.0,
    average_cpu_usage_percent FLOAT DEFAULT 0.0,
    peak_cpu_usage_percent FLOAT DEFAULT 0.0,
    
    -- System metrics
    uptime_percentage FLOAT DEFAULT 100.0 CHECK (uptime_percentage >= 0 AND uptime_percentage <= 100),
    availability_percentage FLOAT DEFAULT 100.0 CHECK (availability_percentage >= 0 AND availability_percentage <= 100),
    
    -- Custom metrics
    custom_metrics JSONB DEFAULT '{}',
    
    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_period CHECK (period_end > period_start),
    CONSTRAINT unique_agent_period UNIQUE (agent_instance_id, period_start)
);

-- Agent Task Queue Table
CREATE TABLE agent_task_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id TEXT UNIQUE NOT NULL,
    
    -- Task specification
    agent_type agent_type NOT NULL,
    task_type TEXT NOT NULL,
    priority task_priority DEFAULT 'normal',
    
    -- Task data
    task_data JSONB NOT NULL DEFAULT '{}',
    context_data JSONB DEFAULT '{}',
    
    -- Scheduling
    status task_status NOT NULL DEFAULT 'pending',
    scheduled_at TIMESTAMPTZ,
    deadline TIMESTAMPTZ,
    max_execution_time_seconds INTEGER DEFAULT 300 CHECK (max_execution_time_seconds > 0),
    
    -- Assignment
    assigned_agent_id TEXT,
    assigned_at TIMESTAMPTZ,
    
    -- Dependencies
    depends_on JSONB DEFAULT '[]',
    blocks JSONB DEFAULT '[]',
    
    -- Retry configuration
    max_retries INTEGER DEFAULT 3 CHECK (max_retries >= 0),
    retry_delay_seconds INTEGER DEFAULT 60,
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    last_retry_at TIMESTAMPTZ,
    
    -- User context
    user_id UUID,
    session_id TEXT,
    callback_url TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- System Health Table
CREATE TABLE system_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Time period
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    period_minutes INTEGER DEFAULT 5,
    
    -- Agent metrics
    total_agents INTEGER DEFAULT 0,
    active_agents INTEGER DEFAULT 0,
    idle_agents INTEGER DEFAULT 0,
    busy_agents INTEGER DEFAULT 0,
    error_agents INTEGER DEFAULT 0,
    
    -- Task metrics
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    queued_tasks INTEGER DEFAULT 0,
    running_tasks INTEGER DEFAULT 0,
    
    -- Performance metrics
    system_success_rate FLOAT DEFAULT 0.0 CHECK (system_success_rate >= 0 AND system_success_rate <= 100),
    system_error_rate FLOAT DEFAULT 0.0 CHECK (system_error_rate >= 0 AND system_error_rate <= 100),
    average_response_time FLOAT DEFAULT 0.0,
    p95_response_time FLOAT DEFAULT 0.0,
    
    -- Throughput metrics
    tasks_per_minute FLOAT DEFAULT 0.0,
    tasks_per_hour FLOAT DEFAULT 0.0,
    
    -- Resource metrics
    total_memory_usage_mb FLOAT DEFAULT 0.0,
    total_cpu_usage_percent FLOAT DEFAULT 0.0,
    disk_usage_percent FLOAT DEFAULT 0.0,
    network_io_mbps FLOAT DEFAULT 0.0,
    
    -- Queue metrics
    queue_length INTEGER DEFAULT 0,
    average_queue_wait_time FLOAT DEFAULT 0.0,
    queue_processing_rate FLOAT DEFAULT 0.0,
    
    -- Health indicators
    overall_health_score FLOAT DEFAULT 100.0 CHECK (overall_health_score >= 0 AND overall_health_score <= 100),
    availability_percentage FLOAT DEFAULT 100.0 CHECK (availability_percentage >= 0 AND availability_percentage <= 100),
    
    -- Alerts
    active_alerts INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    warnings INTEGER DEFAULT 0,
    
    -- Custom metrics
    custom_metrics JSONB DEFAULT '{}'
);

-- Agent Configurations Table
CREATE TABLE agent_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Configuration identity
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    agent_type agent_type NOT NULL,
    
    -- Configuration data
    configuration JSONB NOT NULL DEFAULT '{}',
    resource_limits JSONB DEFAULT '{}',
    performance_thresholds JSONB DEFAULT '{}',
    
    -- Metadata
    description TEXT,
    environment TEXT DEFAULT 'production',
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    
    -- Validation
    schema_version TEXT DEFAULT '1.0',
    validation_rules JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    
    -- Constraints
    CONSTRAINT unique_config_name_version_type UNIQUE (name, version, agent_type)
);

-- Create indexes for performance
CREATE INDEX idx_agent_instances_agent_type_status ON agent_instances(agent_type, status);
CREATE INDEX idx_agent_instances_last_activity ON agent_instances(last_activity);
CREATE INDEX idx_agent_instances_performance ON agent_instances(total_tasks_completed, total_tasks_failed);

CREATE INDEX idx_agent_executions_status_created ON agent_executions(status, created_at);
CREATE INDEX idx_agent_executions_agent_task_type ON agent_executions(agent_type, task_type);
CREATE INDEX idx_agent_executions_user_session ON agent_executions(user_id, session_id);
CREATE INDEX idx_agent_executions_performance ON agent_executions(execution_time_seconds, quality_score);

CREATE INDEX idx_agent_metrics_period ON agent_metrics(period_start, period_end);
CREATE INDEX idx_agent_metrics_performance ON agent_metrics(success_rate, average_execution_time);

CREATE INDEX idx_agent_task_queue_priority_created ON agent_task_queue(priority, created_at);
CREATE INDEX idx_agent_task_queue_agent_status ON agent_task_queue(agent_type, status);
CREATE INDEX idx_agent_task_queue_scheduled ON agent_task_queue(scheduled_at, status);
CREATE INDEX idx_agent_task_queue_user_session ON agent_task_queue(user_id, session_id);

CREATE INDEX idx_system_health_timestamp ON system_health(timestamp);
CREATE INDEX idx_system_health_score ON system_health(overall_health_score, availability_percentage);

CREATE INDEX idx_agent_configurations_active ON agent_configurations(is_active, agent_type);
CREATE INDEX idx_agent_configurations_environment ON agent_configurations(environment, is_active);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_agent_instances_updated_at BEFORE UPDATE ON agent_instances FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agent_task_queue_updated_at BEFORE UPDATE ON agent_task_queue FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agent_configurations_updated_at BEFORE UPDATE ON agent_configurations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) for multi-tenant support
ALTER TABLE agent_instances ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_task_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_health ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_configurations ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
CREATE POLICY "Users can view agent instances" ON agent_instances FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Users can view agent executions" ON agent_executions FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Users can view agent metrics" ON agent_metrics FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Users can manage their own tasks" ON agent_task_queue FOR ALL USING (auth.uid() = user_id OR auth.role() = 'service_role');
CREATE POLICY "Users can view system health" ON system_health FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Admins can manage configurations" ON agent_configurations FOR ALL USING (auth.role() = 'service_role');

-- Create functions for common operations
CREATE OR REPLACE FUNCTION get_agent_health_summary()
RETURNS TABLE (
    total_agents BIGINT,
    healthy_agents BIGINT,
    busy_agents BIGINT,
    error_agents BIGINT,
    success_rate NUMERIC,
    avg_response_time NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_agents,
        COUNT(*) FILTER (WHERE status IN ('idle', 'busy', 'processing')) as healthy_agents,
        COUNT(*) FILTER (WHERE status IN ('busy', 'processing')) as busy_agents,
        COUNT(*) FILTER (WHERE status = 'error') as error_agents,
        ROUND(
            CASE 
                WHEN COUNT(*) > 0 THEN 
                    (SUM(total_tasks_completed)::NUMERIC / NULLIF(SUM(total_tasks_completed + total_tasks_failed), 0)) * 100
                ELSE 0 
            END, 2
        ) as success_rate,
        ROUND(AVG(average_execution_time), 2) as avg_response_time
    FROM agent_instances;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to clean up old data
CREATE OR REPLACE FUNCTION cleanup_old_agent_data(days_to_keep INTEGER DEFAULT 30)
RETURNS TABLE (
    executions_deleted BIGINT,
    metrics_deleted BIGINT,
    health_deleted BIGINT
) AS $$
DECLARE
    cutoff_date TIMESTAMPTZ;
    exec_count BIGINT;
    metrics_count BIGINT;
    health_count BIGINT;
BEGIN
    cutoff_date := NOW() - (days_to_keep || ' days')::INTERVAL;
    
    -- Clean up old executions
    DELETE FROM agent_executions 
    WHERE created_at < cutoff_date 
    AND status IN ('completed', 'failed', 'cancelled');
    GET DIAGNOSTICS exec_count = ROW_COUNT;
    
    -- Clean up old metrics
    DELETE FROM agent_metrics 
    WHERE created_at < cutoff_date;
    GET DIAGNOSTICS metrics_count = ROW_COUNT;
    
    -- Clean up old health data
    DELETE FROM system_health 
    WHERE timestamp < cutoff_date;
    GET DIAGNOSTICS health_count = ROW_COUNT;
    
    RETURN QUERY SELECT exec_count, metrics_count, health_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create real-time subscriptions for agent updates
-- Note: This requires the Supabase realtime extension to be enabled

-- Insert initial system health record
INSERT INTO system_health (
    total_agents, active_agents, idle_agents, busy_agents, error_agents,
    total_tasks, completed_tasks, failed_tasks, queued_tasks, running_tasks,
    system_success_rate, system_error_rate, overall_health_score, availability_percentage
) VALUES (
    0, 0, 0, 0, 0,
    0, 0, 0, 0, 0,
    100.0, 0.0, 100.0, 100.0
);

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated, anon;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated, anon;
GRANT INSERT, UPDATE ON agent_task_queue TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO service_role;
