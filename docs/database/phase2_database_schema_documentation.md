# Phase 2 Database Schema Documentation
**ToolBoxAI Solutions - Educational Technology Platform**

**Document Version**: 2.0.0
**Last Updated**: September 20, 2025
**PostgreSQL Target**: 16.x
**Redis Target**: 7.x

---

## Table of Contents

1. [Overview](#overview)
2. [PostgreSQL 16 Schema Changes](#postgresql-16-schema-changes)
3. [Redis 7 Schema Updates](#redis-7-schema-updates)
4. [Performance Monitoring Schema](#performance-monitoring-schema)
5. [Migration Tracking Schema](#migration-tracking-schema)
6. [Indexes and Performance](#indexes-and-performance)
7. [Connection Pool Configuration](#connection-pool-configuration)
8. [Monitoring Metrics Schema](#monitoring-metrics-schema)

---

## Overview

Phase 2 database modernization introduces significant schema enhancements focused on:

- **Phase completion tracking** with timestamps and metrics
- **GPT model migration tracking** for AI service transitions
- **Enhanced performance monitoring** with PostgreSQL 16 features
- **Redis 7 ACL and function management**
- **Comprehensive baseline capture** for performance analysis

### Key Improvements

- ✅ **JIT Compilation Support**: Optimized indexes for PostgreSQL 16 JIT
- ✅ **Parallel Query Optimization**: Enhanced partitioning and indexing
- ✅ **I/O Monitoring**: pg_stat_io integration for PostgreSQL 16
- ✅ **Redis Functions**: Secure operations with Redis 7 functions
- ✅ **ACL v2**: Advanced security with key patterns and command categories

---

## PostgreSQL 16 Schema Changes

### New Tables

#### 1. phase_completions
```sql
CREATE TABLE phase_completions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase_name VARCHAR(50) NOT NULL UNIQUE,
    completion_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    version VARCHAR(20) NOT NULL,
    features_completed JSONB NOT NULL DEFAULT '{}',
    performance_metrics JSONB,
    rollback_point VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) NOT NULL DEFAULT 'system',
    notes TEXT
);

-- Indexes
CREATE INDEX idx_phase_completions_phase_name ON phase_completions(phase_name);
CREATE INDEX idx_phase_completions_completion_timestamp ON phase_completions(completion_timestamp);
```

**Purpose**: Track completion status and metrics for each development phase.

#### 2. gpt_migration_tracking
```sql
CREATE TYPE gpt_model_type AS ENUM (
    'gpt-4', 'gpt-4-turbo', 'gpt-4.1', 'gpt-4.5', 'gpt-5',
    'claude-3-haiku', 'claude-3-sonnet', 'claude-3-opus', 'claude-4'
);

CREATE TYPE migration_status_type AS ENUM (
    'pending', 'in_progress', 'completed', 'failed', 'rollback'
);

CREATE TABLE gpt_migration_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    migration_id VARCHAR(100) NOT NULL UNIQUE,
    from_model gpt_model_type NOT NULL,
    to_model gpt_model_type NOT NULL,
    migration_status migration_status_type NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    deadline TIMESTAMP WITH TIME ZONE NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    affected_services VARCHAR(50)[] NOT NULL,
    performance_baseline JSONB,
    performance_current JSONB,
    cost_impact JSONB,
    rollback_plan TEXT,
    migration_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) NOT NULL DEFAULT 'system'
);

-- Indexes for efficient querying
CREATE INDEX idx_gpt_migration_migration_id ON gpt_migration_tracking(migration_id);
CREATE INDEX idx_gpt_migration_status ON gpt_migration_tracking(migration_status);
CREATE INDEX idx_gpt_migration_deadline ON gpt_migration_tracking(deadline);
CREATE INDEX idx_gpt_migration_priority ON gpt_migration_tracking(priority);
CREATE INDEX idx_gpt_migration_models ON gpt_migration_tracking(from_model, to_model);
```

**Purpose**: Track AI model migrations with deadlines, performance impacts, and rollback procedures.

#### 3. system_performance_metrics
```sql
CREATE TYPE performance_status_type AS ENUM (
    'healthy', 'warning', 'critical', 'degraded', 'unknown'
);

CREATE TABLE system_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    environment VARCHAR(50) NOT NULL DEFAULT 'production',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(20) NOT NULL,
    status performance_status_type NOT NULL DEFAULT 'healthy',
    threshold_warning FLOAT,
    threshold_critical FLOAT,
    metadata JSONB,
    baseline_value FLOAT,
    trend_direction VARCHAR(20), -- 'up', 'down', 'stable'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance monitoring
CREATE INDEX idx_performance_metrics_name_service ON system_performance_metrics(metric_name, service_name);
CREATE INDEX idx_performance_metrics_timestamp ON system_performance_metrics(timestamp);
CREATE INDEX idx_performance_metrics_status ON system_performance_metrics(status);
CREATE INDEX idx_performance_metrics_environment ON system_performance_metrics(environment);
```

**Purpose**: Real-time system performance monitoring with alerting thresholds.

### PostgreSQL 16 Optimized Views

#### 1. pg16_jit_stats
```sql
CREATE VIEW pg16_jit_stats AS
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
```

#### 2. pg16_io_stats (PostgreSQL 16+ feature)
```sql
CREATE VIEW pg16_io_stats AS
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
```

---

## Redis 7 Schema Updates

### ACL Configuration

Redis 7 introduces enhanced ACL v2 with key patterns and command categories:

```redis
# Application service users
ACL SETUSER backend_api on >password ~app:cache:* ~app:session:* +@read +@write -@dangerous

# Security patterns
ACL SETUSER cache_service on >password ~cache:* ~temp:* +@read +@write +expire +ttl

# Pub/Sub channel restrictions
ACL SETUSER backend_api &notifications:* &events:user:*
```

### Redis Functions (Redis 7 Feature)

#### 1. Safe Counter with Expiration
```lua
local function safe_increment(keys, args)
    local key = keys[1]
    local increment = tonumber(args[1]) or 1
    local ttl = tonumber(args[2]) or 3600

    local current = redis.call('INCR', key)
    if current == 1 then
        redis.call('EXPIRE', key, ttl)
    end

    return current
end

redis.register_function('safe_increment', safe_increment)
```

#### 2. Session Validation
```lua
local function validate_session(keys, args)
    local session_key = keys[1]
    local user_id = args[1]
    local max_age = tonumber(args[2]) or 3600

    -- Session validation logic
    -- Returns {1, 'valid'} or {0, 'error_reason'}
end

redis.register_function('validate_session', validate_session)
```

### Redis Performance Tracking

```sql
CREATE TABLE redis_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    redis_version VARCHAR(20) NOT NULL,
    instance_name VARCHAR(100) NOT NULL,
    measurement_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    memory_usage_mb FLOAT NOT NULL,
    connected_clients INTEGER NOT NULL,
    commands_per_second FLOAT NOT NULL,
    keyspace_hits BIGINT NOT NULL,
    keyspace_misses BIGINT NOT NULL,
    hit_rate_percent FLOAT NOT NULL,
    evicted_keys BIGINT NOT NULL,
    pub_sub_channels INTEGER NOT NULL,
    pub_sub_patterns INTEGER NOT NULL,
    acl_users INTEGER, -- Redis 7+ feature
    functions_count INTEGER, -- Redis 7+ feature
    performance_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Performance Monitoring Schema

### Database Performance Baselines

```sql
CREATE TABLE database_performance_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baseline_name VARCHAR(100) NOT NULL UNIQUE,
    database_version VARCHAR(20) NOT NULL,
    measurement_date TIMESTAMP WITH TIME ZONE NOT NULL,
    query_performance JSONB NOT NULL,
    connection_metrics JSONB NOT NULL,
    index_performance JSONB NOT NULL,
    jit_metrics JSONB, -- PostgreSQL 16+ JIT compilation stats
    parallel_query_metrics JSONB, -- Parallel processing stats
    io_metrics JSONB, -- pg_stat_io data (PostgreSQL 16+)
    cache_hit_ratio FLOAT NOT NULL,
    avg_response_time_ms FLOAT NOT NULL,
    transactions_per_second FLOAT NOT NULL,
    active_connections INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) NOT NULL DEFAULT 'system'
);
```

### Test Execution Metrics

```sql
CREATE TYPE test_status_type AS ENUM (
    'passed', 'failed', 'skipped', 'error', 'timeout'
);

CREATE TABLE test_execution_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_run_id VARCHAR(100) NOT NULL,
    test_suite VARCHAR(100) NOT NULL,
    test_name VARCHAR(200) NOT NULL,
    test_file VARCHAR(500) NOT NULL,
    status test_status_type NOT NULL,
    execution_time_ms FLOAT NOT NULL,
    memory_usage_mb FLOAT,
    cpu_usage_percent FLOAT,
    database_queries INTEGER,
    api_calls INTEGER,
    error_message TEXT,
    stack_trace TEXT,
    coverage_data JSONB,
    environment_info JSONB NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Indexes and Performance

### PostgreSQL 16 JIT-Optimized Indexes

#### High-Performance Indexes for JIT Compilation

```sql
-- Optimized for JIT compilation and parallel queries
CREATE INDEX idx_users_active_jit ON users(id, status, last_login)
WHERE status = 'active' AND last_login > NOW() - INTERVAL '30 days';

-- Partial index for performance monitoring
CREATE INDEX idx_performance_metrics_recent ON system_performance_metrics(timestamp, metric_name, value)
WHERE timestamp > NOW() - INTERVAL '24 hours';

-- Covering index for query optimization
CREATE INDEX idx_gpt_migration_comprehensive ON gpt_migration_tracking(
    migration_status, deadline, priority
) INCLUDE (from_model, to_model, affected_services);
```

#### B-tree Indexes for Range Queries

```sql
-- Time-series data optimization
CREATE INDEX idx_metrics_time_series ON system_performance_metrics
USING btree(service_name, metric_name, timestamp DESC);

-- Phase completion tracking
CREATE INDEX idx_phase_completion_timeline ON phase_completions
USING btree(completion_timestamp DESC, phase_name);
```

#### GIN Indexes for JSONB Data

```sql
-- JSONB performance data indexing
CREATE INDEX idx_performance_baseline_jsonb ON database_performance_baselines
USING gin(query_performance, connection_metrics);

-- GPT migration metadata indexing
CREATE INDEX idx_gpt_migration_jsonb ON gpt_migration_tracking
USING gin(performance_baseline, performance_current);
```

### Index Maintenance for PostgreSQL 16

#### Automatic Index Maintenance

```sql
-- Configure autovacuum for optimal performance
ALTER TABLE system_performance_metrics SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05,
    autovacuum_vacuum_cost_delay = 10
);

-- Optimize for high-write tables
ALTER TABLE test_execution_metrics SET (
    fillfactor = 85,
    autovacuum_vacuum_scale_factor = 0.2
);
```

---

## Connection Pool Configuration

### PostgreSQL 16 Connection Pool Settings

```python
# Database connection pool configuration for PostgreSQL 16
DATABASE_POOL_CONFIG = {
    "postgresql": {
        "pool_size": 20,
        "max_overflow": 30,
        "pool_timeout": 30,
        "pool_recycle": 3600,  # 1 hour
        "pool_pre_ping": True,
        "pool_reset_on_return": "commit",

        # PostgreSQL 16 optimizations
        "connect_args": {
            "server_settings": {
                "application_name": "toolboxai_backend",
                "jit": "on",
                "shared_preload_libraries": "pg_stat_statements",
                "work_mem": "32MB",
                "maintenance_work_mem": "128MB"
            }
        }
    }
}
```

### Redis 7 Connection Pool Settings

```python
# Redis 7 connection pool configuration
REDIS_POOL_CONFIG = {
    "redis": {
        "connection_pool_kwargs": {
            "max_connections": 50,
            "retry_on_timeout": True,
            "health_check_interval": 30,
            "socket_keepalive": True,
            "socket_keepalive_options": {},

            # Redis 7 features
            "protocol": 3,  # RESP3 protocol
            "decode_responses": True,
            "username": "backend_api",  # ACL user
        }
    }
}
```

---

## Monitoring Metrics Schema

### Real-Time Dashboard Views

```sql
-- Performance dashboard view
CREATE VIEW performance_dashboard AS
SELECT
    'PostgreSQL' as component,
    'Database Size' as metric,
    pg_size_pretty(pg_database_size(current_database())) as current_value,
    'N/A' as baseline_value,
    'bytes' as unit,
    CASE
        WHEN pg_database_size(current_database()) > 1073741824 THEN 'warning'
        ELSE 'healthy'
    END as status
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
```

### Performance Alerting Functions

```sql
-- Performance threshold checking
CREATE FUNCTION check_performance_thresholds()
RETURNS TABLE(
    component text,
    metric text,
    current_value float,
    threshold_value float,
    severity text,
    message text
) AS $$
BEGIN
    -- Database size check
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
        'Database size: ' || pg_size_pretty(pg_database_size(current_database()));

    -- Additional checks...
    RETURN;
END;
$$ LANGUAGE plpgsql;
```

---

## Migration Procedures

### Alembic Migration Commands

```bash
# Generate new migration for Phase 2 features
alembic revision --autogenerate -m "phase2_completion_tracking"

# Apply Phase 2 migrations
alembic upgrade head

# Capture baseline before migration
psql -d database_name -f database/performance_baseline_capture.sql

# Enable PostgreSQL 16 features
psql -d database_name -f database/postgresql16_feature_enablement.sql
```

### Redis 7 Migration Commands

```bash
# Apply Redis 7 ACL configuration
redis-cli < database/redis7_acl_configuration.sql

# Verify ACL setup
redis-cli ACL LIST

# Test Redis Functions
redis-cli FCALL safe_increment 1 counter:test 1 3600
```

---

## Performance Optimization Guidelines

### PostgreSQL 16 Best Practices

1. **JIT Configuration**:
   - Enable JIT for complex analytical queries
   - Set appropriate cost thresholds
   - Monitor JIT effectiveness

2. **Parallel Query Optimization**:
   - Configure parallel workers based on CPU cores
   - Use partition-wise joins for large tables
   - Monitor parallel query performance

3. **Index Strategy**:
   - Use covering indexes for frequently accessed columns
   - Implement partial indexes for filtered queries
   - Regularly analyze index usage

### Redis 7 Best Practices

1. **ACL Security**:
   - Use minimal required permissions
   - Implement key pattern restrictions
   - Regular ACL audits

2. **Redis Functions**:
   - Replace Lua scripts with Redis Functions
   - Implement proper error handling
   - Monitor function performance

3. **Memory Optimization**:
   - Configure appropriate eviction policies
   - Monitor memory usage patterns
   - Use Redis 7 memory optimization features

---

## Troubleshooting Guide

### Common Issues and Solutions

#### PostgreSQL 16 Issues

1. **JIT Compilation Problems**:
   ```sql
   -- Check JIT status
   SHOW jit;

   -- Monitor JIT usage
   SELECT * FROM pg_stat_statements WHERE jit_functions > 0;
   ```

2. **Parallel Query Issues**:
   ```sql
   -- Check parallel workers
   SHOW max_parallel_workers;

   -- Monitor parallel queries
   SELECT * FROM pg_stat_activity WHERE backend_type = 'parallel worker';
   ```

#### Redis 7 Issues

1. **ACL Permission Errors**:
   ```redis
   # Check user permissions
   ACL GETUSER username

   # View ACL logs
   ACL LOG
   ```

2. **Function Execution Errors**:
   ```redis
   # List available functions
   FUNCTION LIST

   # Check function stats
   FUNCTION STATS
   ```

---

This documentation provides comprehensive coverage of the Phase 2 database schema changes, optimizations, and monitoring capabilities. Regular updates should be made as the system evolves and new features are added.