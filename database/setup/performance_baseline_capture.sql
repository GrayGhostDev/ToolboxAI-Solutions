-- Performance Baseline Capture Script
-- ToolBoxAI Solutions - Phase 2 Database Modernization
-- Created: 2025-09-20
--
-- This script captures comprehensive performance baselines
-- for both PostgreSQL and Redis before and after migrations.

\echo 'Starting comprehensive performance baseline capture...'

-- =====================================
-- 1. PostgreSQL Performance Baseline
-- =====================================

\echo 'Capturing PostgreSQL performance baseline...'

-- Create function to capture detailed PostgreSQL metrics
CREATE OR REPLACE FUNCTION capture_postgresql_baseline(
    baseline_name text,
    baseline_type text DEFAULT 'comprehensive'
) RETURNS jsonb AS $$
DECLARE
    result jsonb := '{}';
    db_stats jsonb;
    table_stats jsonb;
    index_stats jsonb;
    query_stats jsonb;
    connection_stats jsonb;
    system_stats jsonb;
    vacuum_stats jsonb;
    wal_stats jsonb;
BEGIN
    -- Database-level statistics
    SELECT jsonb_build_object(
        'database_name', current_database(),
        'database_size_bytes', pg_database_size(current_database()),
        'database_size_pretty', pg_size_pretty(pg_database_size(current_database())),
        'version', version(),
        'started_at', pg_postmaster_start_time(),
        'uptime_seconds', EXTRACT(epoch FROM (NOW() - pg_postmaster_start_time())),
        'current_timestamp', NOW()
    ) INTO db_stats;

    -- Table-level statistics
    SELECT jsonb_agg(jsonb_build_object(
        'schema_name', schemaname,
        'table_name', tablename,
        'table_size_bytes', pg_total_relation_size(schemaname||'.'||tablename),
        'table_size_pretty', pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)),
        'row_count', n_tup_ins + n_tup_upd + n_tup_del,
        'seq_scans', seq_scan,
        'seq_tup_read', seq_tup_read,
        'idx_scans', idx_scan,
        'idx_tup_fetch', idx_tup_fetch,
        'n_tup_ins', n_tup_ins,
        'n_tup_upd', n_tup_upd,
        'n_tup_del', n_tup_del,
        'n_tup_hot_upd', n_tup_hot_upd,
        'n_live_tup', n_live_tup,
        'n_dead_tup', n_dead_tup,
        'last_vacuum', last_vacuum,
        'last_autovacuum', last_autovacuum,
        'last_analyze', last_analyze,
        'last_autoanalyze', last_autoanalyze,
        'vacuum_count', vacuum_count,
        'autovacuum_count', autovacuum_count,
        'analyze_count', analyze_count,
        'autoanalyze_count', autoanalyze_count
    )) INTO table_stats
    FROM pg_stat_user_tables
    WHERE schemaname NOT IN ('information_schema', 'pg_catalog');

    -- Index statistics
    SELECT jsonb_agg(jsonb_build_object(
        'schema_name', schemaname,
        'table_name', tablename,
        'index_name', indexrelname,
        'index_size_bytes', pg_relation_size(schemaname||'.'||indexrelname),
        'index_size_pretty', pg_size_pretty(pg_relation_size(schemaname||'.'||indexrelname)),
        'idx_scans', idx_scan,
        'idx_tup_read', idx_tup_read,
        'idx_tup_fetch', idx_tup_fetch
    )) INTO index_stats
    FROM pg_stat_user_indexes
    WHERE schemaname NOT IN ('information_schema', 'pg_catalog');

    -- Query statistics (if pg_stat_statements is available)
    BEGIN
        SELECT jsonb_build_object(
            'total_queries', count(*),
            'total_exec_time_ms', sum(total_exec_time),
            'avg_exec_time_ms', avg(mean_exec_time),
            'max_exec_time_ms', max(max_exec_time),
            'min_exec_time_ms', min(min_exec_time),
            'total_calls', sum(calls),
            'total_rows', sum(rows),
            'slow_queries_count', count(*) FILTER (WHERE mean_exec_time > 1000),
            'cache_hit_ratio',
                CASE WHEN sum(shared_blks_hit + shared_blks_read) > 0
                THEN sum(shared_blks_hit)::float / sum(shared_blks_hit + shared_blks_read)
                ELSE 0 END
        ) INTO query_stats
        FROM pg_stat_statements;
    EXCEPTION WHEN OTHERS THEN
        query_stats := '{"error": "pg_stat_statements not available"}';
    END;

    -- Connection statistics
    SELECT jsonb_build_object(
        'total_connections', count(*),
        'active_connections', count(*) FILTER (WHERE state = 'active'),
        'idle_connections', count(*) FILTER (WHERE state = 'idle'),
        'idle_in_transaction', count(*) FILTER (WHERE state = 'idle in transaction'),
        'waiting_connections', count(*) FILTER (WHERE wait_event IS NOT NULL),
        'max_connections', current_setting('max_connections')::int,
        'connection_utilization', (count(*)::float / current_setting('max_connections')::int) * 100
    ) INTO connection_stats
    FROM pg_stat_activity;

    -- System configuration statistics
    SELECT jsonb_build_object(
        'shared_buffers', current_setting('shared_buffers'),
        'work_mem', current_setting('work_mem'),
        'maintenance_work_mem', current_setting('maintenance_work_mem'),
        'effective_cache_size', current_setting('effective_cache_size'),
        'max_connections', current_setting('max_connections'),
        'max_parallel_workers', current_setting('max_parallel_workers'),
        'max_parallel_workers_per_gather', current_setting('max_parallel_workers_per_gather'),
        'jit', current_setting('jit'),
        'jit_above_cost', current_setting('jit_above_cost'),
        'track_io_timing', current_setting('track_io_timing'),
        'checkpoint_completion_target', current_setting('checkpoint_completion_target'),
        'wal_buffers', current_setting('wal_buffers'),
        'max_wal_size', current_setting('max_wal_size')
    ) INTO system_stats;

    -- WAL statistics
    SELECT jsonb_build_object(
        'wal_records', wal_records,
        'wal_fpi', wal_fpi,
        'wal_bytes', wal_bytes,
        'wal_buffers_full', wal_buffers_full,
        'wal_write', wal_write,
        'wal_sync', wal_sync,
        'wal_write_time', wal_write_time,
        'wal_sync_time', wal_sync_time,
        'stats_reset', stats_reset
    ) INTO wal_stats
    FROM pg_stat_wal;

    -- Vacuum and auto-vacuum statistics
    SELECT jsonb_build_object(
        'autovacuum_enabled', current_setting('autovacuum'),
        'autovacuum_max_workers', current_setting('autovacuum_max_workers'),
        'autovacuum_naptime', current_setting('autovacuum_naptime'),
        'tables_need_vacuum', count(*) FILTER (WHERE n_dead_tup > 1000),
        'tables_need_analyze', count(*) FILTER (WHERE n_mod_since_analyze > 1000)
    ) INTO vacuum_stats
    FROM pg_stat_user_tables;

    -- Combine all statistics
    result := jsonb_build_object(
        'baseline_name', baseline_name,
        'baseline_type', baseline_type,
        'capture_timestamp', NOW(),
        'database_stats', db_stats,
        'table_stats', table_stats,
        'index_stats', index_stats,
        'query_stats', query_stats,
        'connection_stats', connection_stats,
        'system_stats', system_stats,
        'wal_stats', wal_stats,
        'vacuum_stats', vacuum_stats
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Create function to capture Redis baseline metrics (to be executed via application)
CREATE OR REPLACE FUNCTION capture_redis_baseline_metadata(
    baseline_name text
) RETURNS jsonb AS $$
DECLARE
    result jsonb;
BEGIN
    -- This function creates metadata for Redis baseline capture
    -- Actual Redis metrics will be captured via Redis CLI or application
    result := jsonb_build_object(
        'baseline_name', baseline_name,
        'capture_timestamp', NOW(),
        'redis_baseline_required', true,
        'metrics_to_capture', jsonb_build_array(
            'memory_usage',
            'connected_clients',
            'total_commands_processed',
            'keyspace_hits',
            'keyspace_misses',
            'used_memory_human',
            'used_memory_peak_human',
            'total_connections_received',
            'expired_keys',
            'evicted_keys',
            'pubsub_channels',
            'pubsub_patterns',
            'latest_fork_usec',
            'loading',
            'rdb_changes_since_last_save',
            'rdb_bgsave_in_progress',
            'rdb_last_save_time',
            'aof_enabled',
            'aof_rewrite_in_progress',
            'aof_last_rewrite_time_sec'
        )
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =====================================
-- 2. Capture Current PostgreSQL Baseline
-- =====================================

\echo 'Capturing current PostgreSQL baseline...'

-- Insert baseline into database_performance_baselines table
DO $$
DECLARE
    baseline_data jsonb;
    cache_hit_ratio float;
    avg_response_time float;
    tps float;
    active_conn int;
BEGIN
    -- Capture comprehensive baseline
    SELECT capture_postgresql_baseline('phase2_pre_migration_baseline', 'comprehensive')
    INTO baseline_data;

    -- Extract key metrics for the table
    cache_hit_ratio := COALESCE((baseline_data->'query_stats'->>'cache_hit_ratio')::float, 0.0);
    avg_response_time := COALESCE((baseline_data->'query_stats'->>'avg_exec_time_ms')::float, 0.0);
    tps := COALESCE((baseline_data->'query_stats'->>'total_calls')::float /
                   GREATEST((baseline_data->'database_stats'->>'uptime_seconds')::float, 1), 0.0);
    active_conn := COALESCE((baseline_data->'connection_stats'->>'active_connections')::int, 0);

    -- Insert into performance baselines table
    INSERT INTO database_performance_baselines (
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
        'phase2_pre_migration_baseline',
        baseline_data->'database_stats'->>'version',
        NOW(),
        baseline_data->'query_stats',
        baseline_data->'connection_stats',
        jsonb_build_object(
            'table_stats', baseline_data->'table_stats',
            'index_stats', baseline_data->'index_stats'
        ),
        baseline_data->'system_stats',
        jsonb_build_object(
            'parallel_config', baseline_data->'system_stats',
            'wal_stats', baseline_data->'wal_stats'
        ),
        baseline_data->'vacuum_stats',
        cache_hit_ratio,
        avg_response_time,
        tps,
        active_conn,
        'Comprehensive baseline captured before Phase 2 migration',
        'performance_baseline_capture'
    );

    RAISE NOTICE 'PostgreSQL baseline captured successfully';
    RAISE NOTICE 'Cache Hit Ratio: %', cache_hit_ratio;
    RAISE NOTICE 'Average Response Time: % ms', avg_response_time;
    RAISE NOTICE 'Transactions Per Second: %', tps;
    RAISE NOTICE 'Active Connections: %', active_conn;
END;
$$;

-- =====================================
-- 3. Create Performance Monitoring Views
-- =====================================

\echo 'Creating performance monitoring views...'

-- View for real-time performance monitoring
CREATE OR REPLACE VIEW performance_dashboard AS
SELECT
    'PostgreSQL' as component,
    'Database Size' as metric,
    pg_size_pretty(pg_database_size(current_database())) as current_value,
    'N/A' as baseline_value,
    'bytes' as unit,
    CASE
        WHEN pg_database_size(current_database()) > 1073741824 THEN 'warning'  -- > 1GB
        ELSE 'healthy'
    END as status
UNION ALL
SELECT
    'PostgreSQL',
    'Active Connections',
    count(*)::text,
    '0',
    'connections',
    CASE
        WHEN count(*) > current_setting('max_connections')::int * 0.8 THEN 'warning'
        WHEN count(*) > current_setting('max_connections')::int * 0.9 THEN 'critical'
        ELSE 'healthy'
    END
FROM pg_stat_activity
WHERE state = 'active'
UNION ALL
SELECT
    'PostgreSQL',
    'Cache Hit Ratio',
    CASE
        WHEN sum(blks_hit + blks_read) > 0
        THEN round((sum(blks_hit)::float / sum(blks_hit + blks_read) * 100)::numeric, 2)::text
        ELSE '0'
    END,
    '95',
    'percent',
    CASE
        WHEN sum(blks_hit + blks_read) = 0 THEN 'unknown'
        WHEN sum(blks_hit)::float / sum(blks_hit + blks_read) < 0.90 THEN 'critical'
        WHEN sum(blks_hit)::float / sum(blks_hit + blks_read) < 0.95 THEN 'warning'
        ELSE 'healthy'
    END
FROM pg_stat_database
WHERE datname = current_database();

-- View for baseline comparison
CREATE OR REPLACE VIEW baseline_comparison AS
SELECT
    baseline_name,
    database_version,
    measurement_date,
    cache_hit_ratio,
    avg_response_time_ms,
    transactions_per_second,
    active_connections,
    notes,
    CASE
        WHEN measurement_date > NOW() - interval '7 days' THEN 'recent'
        WHEN measurement_date > NOW() - interval '30 days' THEN 'current'
        ELSE 'historical'
    END as recency
FROM database_performance_baselines
ORDER BY measurement_date DESC;

-- View for performance trends
CREATE OR REPLACE VIEW performance_trends AS
WITH metrics AS (
    SELECT
        DATE_TRUNC('hour', timestamp) as hour,
        metric_name,
        service_name,
        AVG(value) as avg_value,
        MIN(value) as min_value,
        MAX(value) as max_value,
        COUNT(*) as sample_count
    FROM system_performance_metrics
    WHERE timestamp > NOW() - interval '24 hours'
    GROUP BY DATE_TRUNC('hour', timestamp), metric_name, service_name
)
SELECT
    hour,
    metric_name,
    service_name,
    avg_value,
    min_value,
    max_value,
    sample_count,
    CASE
        WHEN metric_name = 'response_time_ms' AND avg_value > 1000 THEN 'critical'
        WHEN metric_name = 'response_time_ms' AND avg_value > 500 THEN 'warning'
        WHEN metric_name = 'cpu_usage_percent' AND avg_value > 90 THEN 'critical'
        WHEN metric_name = 'cpu_usage_percent' AND avg_value > 70 THEN 'warning'
        WHEN metric_name = 'memory_usage_mb' AND avg_value > 1024 THEN 'critical'
        WHEN metric_name = 'memory_usage_mb' AND avg_value > 512 THEN 'warning'
        ELSE 'healthy'
    END as status
FROM metrics
ORDER BY hour DESC, metric_name, service_name;

-- =====================================
-- 4. Create Performance Alert Functions
-- =====================================

\echo 'Creating performance alert functions...'

-- Function to check performance thresholds
CREATE OR REPLACE FUNCTION check_performance_thresholds() RETURNS TABLE(
    component text,
    metric text,
    current_value float,
    threshold_value float,
    severity text,
    message text
) AS $$
BEGIN
    -- Check database size
    RETURN QUERY
    SELECT
        'PostgreSQL'::text,
        'Database Size'::text,
        pg_database_size(current_database())::float,
        2147483648.0, -- 2GB threshold
        CASE
            WHEN pg_database_size(current_database()) > 2147483648 THEN 'warning'
            ELSE 'healthy'
        END::text,
        'Database size: ' || pg_size_pretty(pg_database_size(current_database()))
    ;

    -- Check connection utilization
    RETURN QUERY
    SELECT
        'PostgreSQL'::text,
        'Connection Utilization'::text,
        (count(*)::float / current_setting('max_connections')::float * 100),
        80.0,
        CASE
            WHEN count(*)::float / current_setting('max_connections')::float > 0.9 THEN 'critical'
            WHEN count(*)::float / current_setting('max_connections')::float > 0.8 THEN 'warning'
            ELSE 'healthy'
        END::text,
        'Connection utilization: ' ||
        round((count(*)::float / current_setting('max_connections')::float * 100)::numeric, 1) || '%'
    FROM pg_stat_activity;

    -- Check for long-running queries
    RETURN QUERY
    SELECT
        'PostgreSQL'::text,
        'Long Running Queries'::text,
        count(*)::float,
        0.0,
        CASE
            WHEN count(*) > 5 THEN 'critical'
            WHEN count(*) > 0 THEN 'warning'
            ELSE 'healthy'
        END::text,
        count(*)::text || ' queries running longer than 5 minutes'
    FROM pg_stat_activity
    WHERE state = 'active'
    AND query_start < NOW() - interval '5 minutes'
    AND query NOT LIKE '%pg_stat_activity%';

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- =====================================
-- 5. Performance Summary Report
-- =====================================

\echo 'Generating performance summary report...'

-- Display current performance status
SELECT
    'PERFORMANCE BASELINE CAPTURE SUMMARY' as report_section,
    '========================================' as separator;

-- Show database overview
SELECT
    'Database: ' || current_database() as info,
    'Version: ' || version() as details
UNION ALL
SELECT
    'Size: ' || pg_size_pretty(pg_database_size(current_database())),
    'Uptime: ' || (NOW() - pg_postmaster_start_time())::text;

-- Show connection status
SELECT
    'CONNECTION STATUS' as report_section,
    '==================' as separator;

SELECT
    state,
    count(*) as connection_count,
    round(count(*)::numeric / (SELECT count(*) FROM pg_stat_activity) * 100, 1) as percentage
FROM pg_stat_activity
GROUP BY state
ORDER BY connection_count DESC;

-- Show table statistics summary
SELECT
    'TABLE STATISTICS SUMMARY' as report_section,
    '=========================' as separator;

SELECT
    schemaname,
    count(*) as table_count,
    sum(n_live_tup) as total_live_rows,
    pg_size_pretty(sum(pg_total_relation_size(schemaname||'.'||tablename))) as total_size
FROM pg_stat_user_tables
GROUP BY schemaname
ORDER BY sum(pg_total_relation_size(schemaname||'.'||tablename)) DESC;

-- Show performance alerts
SELECT
    'PERFORMANCE ALERTS' as report_section,
    '==================' as separator;

SELECT * FROM check_performance_thresholds()
WHERE severity != 'healthy';

\echo ''
\echo 'Performance baseline capture completed successfully!'
\echo 'Use the following views for ongoing monitoring:'
\echo '  - performance_dashboard: Real-time metrics'
\echo '  - baseline_comparison: Historical baselines'
\echo '  - performance_trends: 24-hour trends'
\echo ''
\echo 'Use check_performance_thresholds() function for alerts.'
\echo ''