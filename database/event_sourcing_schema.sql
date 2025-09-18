-- Event Sourcing Schema for PostgreSQL
-- Author: ToolboxAI Team
-- Created: 2025-09-16
-- Version: 1.0.0

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gist";  -- For exclusion constraints

-- Create schema for event sourcing
CREATE SCHEMA IF NOT EXISTS event_store;

-- Event Store Table
-- This is the append-only log of all events
CREATE TABLE IF NOT EXISTS event_store.events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(255) NOT NULL,
    aggregate_type VARCHAR(255) NOT NULL,
    aggregate_id UUID NOT NULL,
    event_version INTEGER NOT NULL,
    event_data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    user_id VARCHAR(255),
    correlation_id UUID,
    causation_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Ensure events are unique per aggregate and version
    CONSTRAINT unique_aggregate_version UNIQUE (aggregate_id, event_version),

    -- Indexes for common queries
    INDEX idx_aggregate_lookup (aggregate_id, event_version),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at),
    INDEX idx_correlation_id (correlation_id),
    INDEX idx_causation_id (causation_id),
    INDEX idx_event_data_gin (event_data) USING gin
);

-- Add partitioning for scalability (partition by month)
-- Uncomment and adjust based on your needs
-- ALTER TABLE event_store.events PARTITION BY RANGE (created_at);

-- Snapshots Table
-- Store aggregate snapshots for performance optimization
CREATE TABLE IF NOT EXISTS event_store.snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    aggregate_type VARCHAR(255) NOT NULL,
    aggregate_id UUID NOT NULL,
    snapshot_version INTEGER NOT NULL,
    snapshot_data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Ensure only one snapshot per aggregate and version
    CONSTRAINT unique_snapshot_version UNIQUE (aggregate_id, snapshot_version),

    -- Indexes
    INDEX idx_snapshot_lookup (aggregate_id, snapshot_version DESC)
);

-- Projections Table
-- Store read models/projections
CREATE TABLE IF NOT EXISTS event_store.projections (
    projection_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    projection_name VARCHAR(255) NOT NULL,
    projection_type VARCHAR(255) NOT NULL,
    projection_data JSONB NOT NULL,
    last_event_id UUID REFERENCES event_store.events(event_id),
    last_event_version INTEGER,
    checksum VARCHAR(64),  -- For integrity checking
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Ensure unique projection names
    CONSTRAINT unique_projection_name UNIQUE (projection_name),

    -- Indexes
    INDEX idx_projection_type (projection_type),
    INDEX idx_projection_updated (updated_at),
    INDEX idx_projection_data_gin (projection_data) USING gin
);

-- Sagas/Process Managers Table
-- Track long-running processes
CREATE TABLE IF NOT EXISTS event_store.sagas (
    saga_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    saga_type VARCHAR(255) NOT NULL,
    saga_state VARCHAR(50) NOT NULL CHECK (saga_state IN ('pending', 'active', 'completed', 'failed', 'compensating')),
    saga_data JSONB NOT NULL,
    correlation_id UUID NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Indexes
    INDEX idx_saga_correlation (correlation_id),
    INDEX idx_saga_state (saga_state),
    INDEX idx_saga_type (saga_type)
);

-- Command Queue Table (for CQRS)
-- Store commands to be processed
CREATE TABLE IF NOT EXISTS event_store.commands (
    command_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    command_type VARCHAR(255) NOT NULL,
    aggregate_type VARCHAR(255) NOT NULL,
    aggregate_id UUID,
    command_data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    user_id VARCHAR(255),
    correlation_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'rejected')),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMPTZ,

    -- Indexes
    INDEX idx_command_status (status, created_at),
    INDEX idx_command_type (command_type),
    INDEX idx_command_correlation (correlation_id)
);

-- Event Subscriptions Table
-- Track which projections/handlers have processed which events
CREATE TABLE IF NOT EXISTS event_store.subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscriber_name VARCHAR(255) NOT NULL,
    last_processed_event_id UUID REFERENCES event_store.events(event_id),
    last_processed_at TIMESTAMPTZ,
    checkpoint_data JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,

    -- Ensure unique subscriber names
    CONSTRAINT unique_subscriber UNIQUE (subscriber_name),

    -- Indexes
    INDEX idx_subscription_active (is_active)
);

-- Audit Log Table
-- Track all database operations for compliance
CREATE TABLE IF NOT EXISTS event_store.audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    record_id UUID,
    old_data JSONB,
    new_data JSONB,
    user_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_audit_created (created_at),
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_table (table_name)
);

-- Create trigger function for updated_at
CREATE OR REPLACE FUNCTION event_store.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger to projections table
CREATE TRIGGER update_projections_updated_at
    BEFORE UPDATE ON event_store.projections
    FOR EACH ROW
    EXECUTE FUNCTION event_store.update_updated_at();

-- Function to append an event
CREATE OR REPLACE FUNCTION event_store.append_event(
    p_event_type VARCHAR(255),
    p_aggregate_type VARCHAR(255),
    p_aggregate_id UUID,
    p_event_data JSONB,
    p_metadata JSONB DEFAULT '{}',
    p_user_id VARCHAR(255) DEFAULT NULL,
    p_correlation_id UUID DEFAULT NULL,
    p_causation_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
    v_event_version INTEGER;
BEGIN
    -- Get next version number for this aggregate
    SELECT COALESCE(MAX(event_version), 0) + 1
    INTO v_event_version
    FROM event_store.events
    WHERE aggregate_id = p_aggregate_id;

    -- Insert the event
    INSERT INTO event_store.events (
        event_type,
        aggregate_type,
        aggregate_id,
        event_version,
        event_data,
        metadata,
        user_id,
        correlation_id,
        causation_id
    ) VALUES (
        p_event_type,
        p_aggregate_type,
        p_aggregate_id,
        v_event_version,
        p_event_data,
        p_metadata,
        p_user_id,
        p_correlation_id,
        p_causation_id
    ) RETURNING event_id INTO v_event_id;

    -- Notify subscribers
    PERFORM pg_notify(
        'event_stored',
        json_build_object(
            'event_id', v_event_id,
            'event_type', p_event_type,
            'aggregate_id', p_aggregate_id,
            'event_version', v_event_version
        )::text
    );

    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

-- Function to replay events for an aggregate
CREATE OR REPLACE FUNCTION event_store.replay_events(
    p_aggregate_id UUID,
    p_from_version INTEGER DEFAULT 0,
    p_to_version INTEGER DEFAULT NULL
)
RETURNS TABLE(
    event_id UUID,
    event_type VARCHAR(255),
    event_version INTEGER,
    event_data JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.event_id,
        e.event_type,
        e.event_version,
        e.event_data,
        e.metadata,
        e.created_at
    FROM event_store.events e
    WHERE e.aggregate_id = p_aggregate_id
        AND e.event_version > p_from_version
        AND (p_to_version IS NULL OR e.event_version <= p_to_version)
    ORDER BY e.event_version ASC;
END;
$$ LANGUAGE plpgsql;

-- Function to get aggregate state from snapshot + events
CREATE OR REPLACE FUNCTION event_store.get_aggregate_state(
    p_aggregate_id UUID
)
RETURNS JSONB AS $$
DECLARE
    v_snapshot_data JSONB;
    v_snapshot_version INTEGER;
    v_events JSONB;
BEGIN
    -- Get latest snapshot if exists
    SELECT snapshot_data, snapshot_version
    INTO v_snapshot_data, v_snapshot_version
    FROM event_store.snapshots
    WHERE aggregate_id = p_aggregate_id
    ORDER BY snapshot_version DESC
    LIMIT 1;

    -- If no snapshot, start from version 0
    IF v_snapshot_data IS NULL THEN
        v_snapshot_data := '{}'::jsonb;
        v_snapshot_version := 0;
    END IF;

    -- Get events after snapshot
    SELECT json_agg(
        json_build_object(
            'event_type', event_type,
            'event_data', event_data,
            'event_version', event_version,
            'created_at', created_at
        ) ORDER BY event_version
    )
    INTO v_events
    FROM event_store.events
    WHERE aggregate_id = p_aggregate_id
        AND event_version > v_snapshot_version;

    -- Return combined state
    RETURN json_build_object(
        'snapshot', v_snapshot_data,
        'snapshot_version', v_snapshot_version,
        'events', COALESCE(v_events, '[]'::jsonb)
    );
END;
$$ LANGUAGE plpgsql;

-- Function to create a snapshot
CREATE OR REPLACE FUNCTION event_store.create_snapshot(
    p_aggregate_type VARCHAR(255),
    p_aggregate_id UUID,
    p_snapshot_version INTEGER,
    p_snapshot_data JSONB,
    p_metadata JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    v_snapshot_id UUID;
BEGIN
    INSERT INTO event_store.snapshots (
        aggregate_type,
        aggregate_id,
        snapshot_version,
        snapshot_data,
        metadata
    ) VALUES (
        p_aggregate_type,
        p_aggregate_id,
        p_snapshot_version,
        p_snapshot_data,
        p_metadata
    ) RETURNING snapshot_id INTO v_snapshot_id;

    RETURN v_snapshot_id;
END;
$$ LANGUAGE plpgsql;

-- Create read permissions for application user
GRANT USAGE ON SCHEMA event_store TO eduplatform;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA event_store TO eduplatform;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA event_store TO eduplatform;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA event_store TO eduplatform;

-- Create indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_aggregate_type_created
    ON event_store.events (aggregate_type, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_user_created
    ON event_store.events (user_id, created_at DESC)
    WHERE user_id IS NOT NULL;

-- Add comments for documentation
COMMENT ON SCHEMA event_store IS 'Event Sourcing and CQRS implementation schema';
COMMENT ON TABLE event_store.events IS 'Append-only event log for all domain events';
COMMENT ON TABLE event_store.snapshots IS 'Aggregate snapshots for performance optimization';
COMMENT ON TABLE event_store.projections IS 'Read models built from events';
COMMENT ON TABLE event_store.commands IS 'Command queue for CQRS pattern';
COMMENT ON TABLE event_store.sagas IS 'Long-running process management';
COMMENT ON FUNCTION event_store.append_event IS 'Append a new event to the event store';
COMMENT ON FUNCTION event_store.replay_events IS 'Replay events for an aggregate';
COMMENT ON FUNCTION event_store.get_aggregate_state IS 'Get current state from snapshot + events';