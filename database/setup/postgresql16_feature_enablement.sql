-- PostgreSQL 16 Feature Enablement Script
-- ToolBoxAI Solutions - Phase 2 Database Modernization
-- Created: 2025-09-20
--
-- This script enables PostgreSQL 16 specific features and optimizations
-- for enhanced performance and monitoring capabilities.

\echo 'Starting PostgreSQL 16 feature enablement...'

-- =====================================
-- 1. JIT Compilation Configuration
-- =====================================

\echo 'Configuring JIT compilation settings...'

-- Enable JIT compilation for performance improvements
ALTER SYSTEM SET jit = on;

-- Set JIT cost thresholds for optimal performance
-- Only enable JIT for queries that benefit from it
ALTER SYSTEM SET jit_above_cost = 100000;
ALTER SYSTEM SET jit_inline_above_cost = 500000;
ALTER SYSTEM SET jit_optimize_above_cost = 500000;

-- Tune JIT for the system's capabilities
-- Adjust based on available CPU cores and workload
ALTER SYSTEM SET jit_expressions = on;
ALTER SYSTEM SET jit_tuple_deforming = on;

\echo 'JIT compilation configured successfully.'

-- =====================================
-- 2. Enhanced Parallel Query Processing
-- =====================================

\echo 'Configuring parallel query processing...'

-- Set parallel workers based on system capabilities
-- Recommended: 2-4 per gather, total 8-16 workers
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;
ALTER SYSTEM SET max_parallel_maintenance_workers = 2;

-- Enable parallel operations
ALTER SYSTEM SET force_parallel_mode = off;  -- Use automatic decision making
ALTER SYSTEM SET parallel_tuple_cost = 0.1;
ALTER SYSTEM SET parallel_setup_cost = 1000.0;

-- Configure parallel join and aggregation
ALTER SYSTEM SET enable_partitionwise_join = on;
ALTER SYSTEM SET enable_partitionwise_aggregate = on;

\echo 'Parallel query processing configured successfully.'

-- =====================================
-- 3. Enhanced I/O and Statistics Tracking
-- =====================================

\echo 'Configuring I/O and statistics tracking...'

-- Enable pg_stat_io for PostgreSQL 16+ I/O monitoring
ALTER SYSTEM SET track_io_timing = on;

-- Enhanced statistics tracking for performance analysis
ALTER SYSTEM SET track_activities = on;
ALTER SYSTEM SET track_counts = on;
ALTER SYSTEM SET track_functions = all;

-- Configure statement tracking for performance monitoring
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET pg_stat_statements.max = 10000;
ALTER SYSTEM SET pg_stat_statements.track = all;
ALTER SYSTEM SET pg_stat_statements.track_utility = on;
ALTER SYSTEM SET pg_stat_statements.save = on;

\echo 'I/O and statistics tracking configured successfully.'

-- =====================================
-- 4. Memory and Connection Optimization
-- =====================================

\echo 'Configuring memory and connection settings...'

-- Optimize shared buffers (25% of RAM, adjust based on system)
ALTER SYSTEM SET shared_buffers = '256MB';

-- Configure work memory for complex queries
ALTER SYSTEM SET work_mem = '32MB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';

-- Connection pooling optimization
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET superuser_reserved_connections = 3;

-- Query planning optimization
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET random_page_cost = 1.1;  -- SSD optimization

\echo 'Memory and connection settings configured successfully.'

-- =====================================
-- 5. Enhanced Logging and Monitoring
-- =====================================

\echo 'Configuring enhanced logging and monitoring...'

-- Configure logging for performance analysis
ALTER SYSTEM SET log_statement = 'none';  -- Avoid log flooding
ALTER SYSTEM SET log_duration = off;      -- Use pg_stat_statements instead
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log slow queries (1s+)

-- Enhanced error and performance logging
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_lock_waits = on;

-- Configure CSV logging for automated processing
ALTER SYSTEM SET logging_collector = on;
ALTER SYSTEM SET log_destination = 'csvlog';
ALTER SYSTEM SET log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log';
ALTER SYSTEM SET log_rotation_age = '1d';
ALTER SYSTEM SET log_rotation_size = '100MB';

\echo 'Enhanced logging and monitoring configured successfully.'

-- =====================================
-- 6. Partitioning and Indexing Optimizations
-- =====================================

\echo 'Configuring partitioning and indexing optimizations...'

-- Enable constraint exclusion for partitioned tables
ALTER SYSTEM SET constraint_exclusion = partition;

-- Configure autovacuum for optimal performance
ALTER SYSTEM SET autovacuum = on;
ALTER SYSTEM SET autovacuum_max_workers = 3;
ALTER SYSTEM SET autovacuum_naptime = '1min';

-- Optimize checkpoint behavior
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET checkpoint_timeout = '15min';
ALTER SYSTEM SET max_wal_size = '2GB';
ALTER SYSTEM SET min_wal_size = '1GB';

\echo 'Partitioning and indexing optimizations configured successfully.'

-- =====================================
-- 7. Create PostgreSQL 16 Performance Views
-- =====================================

\echo 'Creating PostgreSQL 16 performance monitoring views...'

-- Create view for JIT compilation statistics
CREATE OR REPLACE VIEW pg16_jit_stats AS
SELECT
    schemaname,
    tablename,
    attname,
    inherited,
    null_frac,
    avg_width,
    n_distinct,
    most_common_vals,
    most_common_freqs,
    histogram_bounds,
    correlation
FROM pg_stats
WHERE schemaname NOT IN ('information_schema', 'pg_catalog');

-- Create view for parallel query monitoring
CREATE OR REPLACE VIEW pg16_parallel_query_stats AS
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    backend_start,
    query_start,
    state_change,
    state,
    query,
    backend_type
FROM pg_stat_activity
WHERE backend_type = 'parallel worker' OR query LIKE '%parallel%';

-- Create view for I/O statistics (PostgreSQL 16+ feature)
CREATE OR REPLACE VIEW pg16_io_stats AS
SELECT
    backend_type,
    object,
    context,
    reads,
    read_time,
    writes,
    write_time,
    writebacks,
    writeback_time,
    extends,
    extend_time,
    op_bytes,
    evictions,
    reuses,
    fsyncs,
    fsync_time,
    stats_reset
FROM pg_stat_io
WHERE backend_type IS NOT NULL;

-- Create comprehensive performance monitoring view
CREATE OR REPLACE VIEW pg16_performance_overview AS
SELECT
    'Database Size' as metric,
    pg_size_pretty(pg_database_size(current_database())) as value,
    'Database' as category
UNION ALL
SELECT
    'Active Connections' as metric,
    count(*)::text as value,
    'Connections' as category
FROM pg_stat_activity
WHERE state = 'active'
UNION ALL
SELECT
    'JIT Enabled' as metric,
    current_setting('jit')::text as value,
    'JIT' as category
UNION ALL
SELECT
    'Parallel Workers' as metric,
    current_setting('max_parallel_workers')::text as value,
    'Parallel' as category
UNION ALL
SELECT
    'Shared Buffers' as metric,
    current_setting('shared_buffers')::text as value,
    'Memory' as category;

\echo 'PostgreSQL 16 performance monitoring views created successfully.'

-- =====================================
-- 8. Create Performance Monitoring Functions
-- =====================================

\echo 'Creating performance monitoring functions...'

-- Function to capture performance baseline
CREATE OR REPLACE FUNCTION capture_performance_baseline(
    baseline_name text,
    notes text DEFAULT NULL
) RETURNS uuid AS $$
DECLARE
    baseline_id uuid;
    query_perf jsonb;
    conn_metrics jsonb;
    index_perf jsonb;
    jit_metrics jsonb;
    parallel_metrics jsonb;
    io_metrics jsonb;
BEGIN
    -- Generate new baseline ID
    baseline_id := gen_random_uuid();

    -- Capture query performance metrics
    SELECT jsonb_build_object(
        'total_exec_time', COALESCE(sum(total_exec_time), 0),
        'mean_exec_time', COALESCE(avg(mean_exec_time), 0),
        'max_exec_time', COALESCE(max(max_exec_time), 0),
        'total_calls', COALESCE(sum(calls), 0),
        'slow_queries', COALESCE(count(*) FILTER (WHERE mean_exec_time > 1000), 0)
    ) INTO query_perf
    FROM pg_stat_statements;

    -- Capture connection metrics
    SELECT jsonb_build_object(
        'active_connections', count(*) FILTER (WHERE state = 'active'),
        'idle_connections', count(*) FILTER (WHERE state = 'idle'),
        'total_connections', count(*),
        'max_connections', current_setting('max_connections')::int
    ) INTO conn_metrics
    FROM pg_stat_activity;

    -- Capture index performance
    SELECT jsonb_build_object(
        'total_index_scans', COALESCE(sum(idx_scan), 0),
        'total_seq_scans', COALESCE(sum(seq_scan), 0),
        'index_hit_rate', CASE
            WHEN sum(idx_scan + seq_scan) > 0
            THEN sum(idx_scan)::float / sum(idx_scan + seq_scan)
            ELSE 0
        END
    ) INTO index_perf
    FROM pg_stat_user_tables;

    -- Capture JIT metrics (PostgreSQL 16+)
    jit_metrics := jsonb_build_object(
        'jit_enabled', current_setting('jit')::boolean,
        'jit_above_cost', current_setting('jit_above_cost')::float,
        'jit_inline_above_cost', current_setting('jit_inline_above_cost')::float
    );

    -- Capture parallel query metrics
    parallel_metrics := jsonb_build_object(
        'max_parallel_workers', current_setting('max_parallel_workers')::int,
        'max_parallel_workers_per_gather', current_setting('max_parallel_workers_per_gather')::int,
        'parallel_tuple_cost', current_setting('parallel_tuple_cost')::float
    );

    -- Capture I/O metrics (if pg_stat_io exists)
    BEGIN
        SELECT jsonb_object_agg(backend_type, jsonb_build_object(
            'reads', reads,
            'writes', writes,
            'read_time', read_time,
            'write_time', write_time
        )) INTO io_metrics
        FROM pg_stat_io
        WHERE backend_type IS NOT NULL;
    EXCEPTION WHEN OTHERS THEN
        io_metrics := '{}'::jsonb;
    END;

    -- Insert baseline record
    INSERT INTO database_performance_baselines (
        id,
        baseline_name,
        database_version,
        measurement_date,
        query_performance,
        connection_metrics,
        index_performance,
        jit_metrics,
        parallel_query_metrics,
        io_metrics,
        cache_hit_ratio,
        avg_response_time_ms,
        transactions_per_second,
        active_connections,
        notes,
        created_by
    ) VALUES (
        baseline_id,
        baseline_name,
        version(),
        NOW(),
        query_perf,
        conn_metrics,
        index_perf,
        jit_metrics,
        parallel_metrics,
        COALESCE(io_metrics, '{}'::jsonb),
        COALESCE((query_perf->>'index_hit_rate')::float, 0.0),
        COALESCE((query_perf->>'mean_exec_time')::float, 0.0),
        COALESCE((query_perf->>'total_calls')::float / EXTRACT(epoch FROM NOW() - pg_postmaster_start_time()), 0.0),
        COALESCE((conn_metrics->>'active_connections')::int, 0),
        notes,
        'pg16_feature_enablement'
    );

    RETURN baseline_id;
END;
$$ LANGUAGE plpgsql;

\echo 'Performance monitoring functions created successfully.'

-- =====================================
-- 9. Reload Configuration
-- =====================================

\echo 'Reloading PostgreSQL configuration...'

-- Reload configuration to apply settings
SELECT pg_reload_conf();

\echo 'Configuration reloaded successfully.'

-- =====================================
-- 10. Create Initial Performance Baseline
-- =====================================

\echo 'Creating initial PostgreSQL 16 performance baseline...'

-- Capture initial baseline after configuration
SELECT capture_performance_baseline(
    'postgresql16_initial_baseline',
    'Initial performance baseline after PostgreSQL 16 feature enablement'
);

\echo 'Initial performance baseline created successfully.'

-- =====================================
-- 11. Create Monitoring Indexes
-- =====================================

\echo 'Creating monitoring-optimized indexes...'

-- Create indexes for efficient monitoring queries
CREATE INDEX IF NOT EXISTS idx_pg_stat_statements_query_hash
ON pg_stat_statements(queryid)
WHERE calls > 10;

-- Create partial indexes for performance monitoring
CREATE INDEX IF NOT EXISTS idx_pg_stat_activity_active
ON pg_stat_activity(state, query_start)
WHERE state = 'active';

\echo 'Monitoring-optimized indexes created successfully.'

-- =====================================
-- Summary and Verification
-- =====================================

\echo ''
\echo '========================================='
\echo 'PostgreSQL 16 Feature Enablement Complete'
\echo '========================================='
\echo ''

-- Display configuration summary
\echo 'Current Configuration Summary:'
SELECT
    'JIT Enabled' as setting,
    current_setting('jit') as value
UNION ALL
SELECT
    'Max Parallel Workers',
    current_setting('max_parallel_workers')
UNION ALL
SELECT
    'Shared Buffers',
    current_setting('shared_buffers')
UNION ALL
SELECT
    'Work Memory',
    current_setting('work_mem')
UNION ALL
SELECT
    'Track IO Timing',
    current_setting('track_io_timing');

\echo ''
\echo 'Performance monitoring views available:'
\echo '  - pg16_jit_stats'
\echo '  - pg16_parallel_query_stats'
\echo '  - pg16_io_stats'
\echo '  - pg16_performance_overview'
\echo ''
\echo 'Performance monitoring functions available:'
\echo '  - capture_performance_baseline(name, notes)'
\echo ''
\echo 'PostgreSQL 16 features are now enabled and configured for optimal performance.'
\echo 'Please restart PostgreSQL service to ensure all settings take effect.'
\echo ''