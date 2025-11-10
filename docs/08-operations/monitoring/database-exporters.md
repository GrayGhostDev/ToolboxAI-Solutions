# Database Metric Exporters

**Last Updated:** November 2025
**Status:** Production-Ready
**Purpose:** PostgreSQL and Redis monitoring integration

---

## Overview

Database metric exporters provide detailed performance and health metrics to Prometheus for comprehensive monitoring of PostgreSQL and Redis services. These exporters collect real-time data about database operations, connections, resource usage, and performance characteristics.

### Why Monitor Databases?

- **Performance Optimization**: Identify slow queries and bottlenecks
- **Capacity Planning**: Track resource usage trends
- **Proactive Alerting**: Detect issues before they impact users
- **SLA Compliance**: Monitor uptime and response times
- **Cost Management**: Optimize resource allocation

---

## PostgreSQL Exporter

### Overview

**Image:** `quay.io/prometheuscommunity/postgres-exporter:v0.15.0`
**Port:** `9187`
**Metrics Endpoint:** `http://postgres-exporter:9187/metrics`

The PostgreSQL exporter connects to the PostgreSQL database and exposes detailed metrics about database performance, connections, queries, tables, and replication status.

### Metrics Collected

#### Connection Metrics
- `pg_stat_activity_count` - Number of active connections by state
- `pg_stat_database_numbackends` - Number of backends connected
- `pg_settings_max_connections` - Maximum allowed connections

#### Query Performance
- `pg_stat_database_xact_commit` - Number of committed transactions
- `pg_stat_database_xact_rollback` - Number of rolled back transactions
- `pg_stat_database_blks_read` - Number of disk blocks read
- `pg_stat_database_blks_hit` - Number of disk blocks found in cache
- `pg_stat_database_tup_returned` - Number of rows returned
- `pg_stat_database_tup_fetched` - Number of rows fetched

#### Table Statistics
- `pg_stat_user_tables_seq_scan` - Number of sequential scans
- `pg_stat_user_tables_idx_scan` - Number of index scans
- `pg_stat_user_tables_n_tup_ins` - Number of rows inserted
- `pg_stat_user_tables_n_tup_upd` - Number of rows updated
- `pg_stat_user_tables_n_tup_del` - Number of rows deleted
- `pg_stat_user_tables_n_live_tup` - Estimated number of live rows
- `pg_stat_user_tables_n_dead_tup` - Estimated number of dead rows

#### Index Statistics
- `pg_stat_user_indexes_idx_scan` - Number of index scans
- `pg_stat_user_indexes_idx_tup_read` - Index entries returned
- `pg_stat_user_indexes_idx_tup_fetch` - Live rows fetched

#### Replication (if applicable)
- `pg_replication_lag_bytes` - Replication lag in bytes
- `pg_stat_replication_sent_lsn` - Last WAL byte sent
- `pg_stat_replication_write_lsn` - Last WAL byte written to disk

#### Deadlocks and Conflicts
- `pg_stat_database_deadlocks` - Number of deadlocks detected
- `pg_stat_database_conflicts` - Number of queries canceled due to conflicts

### Key Performance Metrics

#### Cache Hit Ratio
```promql
# Calculate cache hit ratio (should be > 90%)
sum(rate(pg_stat_database_blks_hit[5m]))
/
(sum(rate(pg_stat_database_blks_hit[5m])) + sum(rate(pg_stat_database_blks_read[5m])))
```

**Target:** > 95% (indicates efficient use of shared_buffers)

#### Active Connections
```promql
# Current active connections
pg_stat_activity_count{state="active"}

# Total connections
sum(pg_stat_database_numbackends)
```

**Target:** < 80% of `max_connections`

#### Transaction Rate
```promql
# Transactions per second
rate(pg_stat_database_xact_commit[5m])

# Rollback rate (should be low)
rate(pg_stat_database_xact_rollback[5m])
```

**Target:** Rollback rate < 1% of commit rate

#### Table Size and Growth
```promql
# Total database size in bytes
pg_database_size_bytes

# Table size
pg_total_relation_size_bytes

# Growth rate
deriv(pg_database_size_bytes[1h])
```

#### Slow Queries
```promql
# Long-running queries (> 30 seconds)
pg_stat_activity_max_tx_duration > 30
```

**Target:** No queries running > 60 seconds regularly

### Configuration

#### Connection String
The exporter connects using the `DATA_SOURCE_NAME` environment variable:

```bash
DATA_SOURCE_NAME="postgresql://toolboxai:password@postgres:5432/toolboxai?sslmode=disable"
```

**Security Note:** In production, use secrets management (Vault) for credentials.

#### Prometheus Scrape Config
```yaml
- job_name: 'postgres-exporter'
  static_configs:
    - targets: ['postgres-exporter:9187']
  metrics_path: /metrics
  scrape_interval: 30s
```

#### Custom Queries (Optional)
Create custom queries by mounting a queries.yaml file:

```yaml
# queries.yaml
pg_custom_slow_queries:
  query: "SELECT COUNT(*) as slow_queries FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '5 seconds'"
  metrics:
    - slow_queries:
        usage: "GAUGE"
        description: "Number of queries running > 5 seconds"
```

Mount in docker-compose.yml:
```yaml
volumes:
  - ./config/postgres-exporter/queries.yaml:/etc/queries.yaml:ro
environment:
  PG_EXPORTER_EXTEND_QUERY_PATH: /etc/queries.yaml
```

---

## Redis Exporter

### Overview

**Image:** `oliver006/redis_exporter:v1.55.0`
**Port:** `9121`
**Metrics Endpoint:** `http://redis-exporter:9121/metrics`

The Redis exporter connects to Redis and exposes metrics about memory usage, commands, key statistics, persistence, and replication.

### Metrics Collected

#### Memory Usage
- `redis_memory_used_bytes` - Total memory used by Redis
- `redis_memory_max_bytes` - Maximum memory Redis can use
- `redis_memory_used_rss_bytes` - Resident set size
- `redis_memory_fragmentation_ratio` - Memory fragmentation ratio

#### Command Statistics
- `redis_commands_total` - Total number of commands processed
- `redis_commands_duration_seconds_total` - Total time spent executing commands
- `redis_commands_processed_total` - Number of commands processed per second

#### Key Statistics
- `redis_db_keys` - Total number of keys per database
- `redis_db_keys_expiring` - Number of keys with expiration set
- `redis_evicted_keys_total` - Total number of evicted keys
- `redis_expired_keys_total` - Total number of expired keys

#### Client Connections
- `redis_connected_clients` - Number of connected clients
- `redis_blocked_clients` - Number of blocked clients
- `redis_rejected_connections_total` - Total connections rejected due to maxclients

#### Persistence
- `redis_rdb_last_save_timestamp_seconds` - Timestamp of last RDB save
- `redis_rdb_changes_since_last_save` - Number of changes since last save
- `redis_aof_enabled` - AOF enabled flag
- `redis_aof_last_rewrite_time_sec` - Duration of last AOF rewrite

#### Replication (if applicable)
- `redis_connected_slaves` - Number of connected replicas
- `redis_master_repl_offset` - Master replication offset
- `redis_slave_repl_offset` - Replica replication offset

#### Network
- `redis_net_input_bytes_total` - Total bytes received
- `redis_net_output_bytes_total` - Total bytes sent

### Key Performance Metrics

#### Memory Usage Percentage
```promql
# Memory usage as percentage of max
(redis_memory_used_bytes / redis_memory_max_bytes) * 100
```

**Target:** < 85% (leave headroom for spikes)

#### Cache Hit Rate
```promql
# Hit rate calculation
rate(redis_keyspace_hits_total[5m])
/
(rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
```

**Target:** > 90% (indicates effective caching)

#### Commands Per Second
```promql
# Total commands per second
rate(redis_commands_total[5m])

# Commands by type
rate(redis_commands_total{cmd="get"}[5m])
rate(redis_commands_total{cmd="set"}[5m])
```

**Target:** Monitor for sudden spikes or drops

#### Eviction Rate
```promql
# Keys evicted per second (should be low)
rate(redis_evicted_keys_total[5m])
```

**Target:** Near zero (evictions indicate memory pressure)

#### Connected Clients
```promql
# Current connected clients
redis_connected_clients
```

**Target:** < 10,000 (adjust based on redis config)

#### Blocked Clients
```promql
# Clients blocked on BLPOP, BRPOP, BRPOPLPUSH
redis_blocked_clients
```

**Target:** < 10 (many blocked clients may indicate issues)

### Configuration

#### Connection Settings
The exporter connects using environment variables:

```bash
REDIS_ADDR=redis:6379
REDIS_PASSWORD=your_redis_password
```

**Security Note:** Use Docker secrets or Vault for password management.

#### Prometheus Scrape Config
```yaml
- job_name: 'redis-exporter'
  static_configs:
    - targets: ['redis-exporter:9121']
  metrics_path: /metrics
  scrape_interval: 30s
```

#### Multi-Instance Monitoring (Optional)
Monitor multiple Redis instances:

```yaml
redis-exporter:
  environment:
    REDIS_ADDR: "redis://redis1:6379,redis://redis2:6379"
    REDIS_EXPORTER_CHECK_KEYS: "my-key:*,other-key:*"
```

---

## Grafana Dashboards

### PostgreSQL Dashboard

**Import ID:** 9628 (PostgreSQL Database by Prometheus Community)

**Panels Include:**
- Connection count by state
- Query performance (QPS, duration)
- Cache hit ratio
- Table and index statistics
- Disk I/O operations
- Deadlocks and conflicts
- Database size and growth
- Long-running queries

**Import Command:**
```bash
# In Grafana UI
Dashboard → Import → 9628 → Load → Select Prometheus data source → Import
```

### Redis Dashboard

**Import ID:** 763 (Redis Dashboard for Prometheus Redis Exporter)

**Panels Include:**
- Memory usage and fragmentation
- Operations per second
- Hit/miss ratio
- Connected clients
- Keyspace statistics
- Evictions and expirations
- Network throughput
- Persistence status

**Import Command:**
```bash
# In Grafana UI
Dashboard → Import → 763 → Load → Select Prometheus data source → Import
```

### Custom Dashboard Recommendations

**Combined Database Health Dashboard:**
- PostgreSQL connection pool status
- Redis cache hit rate
- Database response times (p50, p95, p99)
- Error rates by database operation
- Resource usage comparison (CPU, memory)
- Alert history and trends

---

## Alerts

### PostgreSQL Alert Rules

```yaml
# alert_rules.yml additions

# PostgreSQL is down
- alert: PostgreSQLDown
  expr: pg_up == 0
  for: 5m
  labels:
    severity: critical
    service: postgresql
  annotations:
    summary: "PostgreSQL is down"
    description: "PostgreSQL instance {{ $labels.instance }} is down for more than 5 minutes"

# Too many connections
- alert: PostgreSQLTooManyConnections
  expr: sum(pg_stat_activity_count) > 180
  for: 10m
  labels:
    severity: warning
    service: postgresql
  annotations:
    summary: "PostgreSQL has too many connections"
    description: "PostgreSQL has {{ $value }} active connections (threshold: 180)"

# Low cache hit ratio
- alert: PostgreSQLLowCacheHitRatio
  expr: |
    sum(rate(pg_stat_database_blks_hit[5m]))
    /
    (sum(rate(pg_stat_database_blks_hit[5m])) + sum(rate(pg_stat_database_blks_read[5m])))
    < 0.90
  for: 15m
  labels:
    severity: warning
    service: postgresql
  annotations:
    summary: "PostgreSQL cache hit ratio is low"
    description: "Cache hit ratio is {{ $value | humanizePercentage }} (threshold: 90%)"

# Slow queries
- alert: PostgreSQLSlowQueries
  expr: pg_stat_activity_max_tx_duration > 300
  for: 5m
  labels:
    severity: warning
    service: postgresql
  annotations:
    summary: "PostgreSQL has slow queries"
    description: "Query running for {{ $value }} seconds on {{ $labels.instance }}"

# High deadlock rate
- alert: PostgreSQLHighDeadlockRate
  expr: rate(pg_stat_database_deadlocks[5m]) > 0.1
  for: 10m
  labels:
    severity: warning
    service: postgresql
  annotations:
    summary: "PostgreSQL experiencing deadlocks"
    description: "Deadlock rate is {{ $value }} per second"

# Database size growth
- alert: PostgreSQLDatabaseGrowthHigh
  expr: deriv(pg_database_size_bytes[1h]) > 1000000000  # 1GB/hour
  for: 2h
  labels:
    severity: info
    service: postgresql
  annotations:
    summary: "PostgreSQL database growing rapidly"
    description: "Database {{ $labels.datname }} growing at {{ $value | humanize }}B/hour"
```

### Redis Alert Rules

```yaml
# Redis is down
- alert: RedisDown
  expr: redis_up == 0
  for: 5m
  labels:
    severity: critical
    service: redis
  annotations:
    summary: "Redis is down"
    description: "Redis instance {{ $labels.instance }} is down for more than 5 minutes"

# High memory usage
- alert: RedisMemoryHigh
  expr: (redis_memory_used_bytes / redis_memory_max_bytes) > 0.90
  for: 10m
  labels:
    severity: warning
    service: redis
  annotations:
    summary: "Redis memory usage is high"
    description: "Redis memory usage is {{ $value | humanizePercentage }} (threshold: 90%)"

# Low cache hit rate
- alert: RedisLowHitRate
  expr: |
    rate(redis_keyspace_hits_total[5m])
    /
    (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
    < 0.80
  for: 15m
  labels:
    severity: warning
    service: redis
  annotations:
    summary: "Redis cache hit rate is low"
    description: "Cache hit rate is {{ $value | humanizePercentage }} (threshold: 80%)"

# Rejected connections
- alert: RedisRejectedConnections
  expr: rate(redis_rejected_connections_total[5m]) > 0
  for: 5m
  labels:
    severity: warning
    service: redis
  annotations:
    summary: "Redis rejecting connections"
    description: "Redis rejecting {{ $value }} connections/sec due to maxclients limit"

# High eviction rate
- alert: RedisHighEvictionRate
  expr: rate(redis_evicted_keys_total[5m]) > 10
  for: 10m
  labels:
    severity: warning
    service: redis
  annotations:
    summary: "Redis evicting keys frequently"
    description: "Redis evicting {{ $value }} keys/sec (indicates memory pressure)"

# Replication lag (if using replication)
- alert: RedisReplicationLag
  expr: (redis_master_repl_offset - redis_slave_repl_offset) > 1000000  # 1MB
  for: 10m
  labels:
    severity: warning
    service: redis
  annotations:
    summary: "Redis replication lag detected"
    description: "Replication lag is {{ $value | humanize }}B on {{ $labels.instance }}"
```

---

## Troubleshooting

### PostgreSQL Exporter Not Scraping

**Symptoms:**
- `pg_up` metric is 0 or missing
- Prometheus target shows as DOWN
- No PostgreSQL metrics in Prometheus

**Diagnosis:**

```bash
# Check exporter logs
docker logs toolboxai-postgres-exporter

# Test exporter endpoint
curl http://localhost:9187/metrics

# Test PostgreSQL connection from exporter
docker exec toolboxai-postgres-exporter sh -c \\
  'wget -O- http://localhost:9187/metrics | grep pg_up'
```

**Common Issues:**

1. **Wrong credentials:**
```bash
# Verify DATABASE_URL in .env
grep POSTGRES_PASSWORD .env

# Test connection manually
docker exec toolboxai-postgres psql -U toolboxai -d toolboxai -c "SELECT version();"
```

2. **Network connectivity:**
```bash
# Verify exporter can reach PostgreSQL
docker exec toolboxai-postgres-exporter nc -zv postgres 5432

# Check networks
docker network inspect toolboxai_database
```

3. **PostgreSQL not ready:**
```bash
# Check PostgreSQL health
docker exec toolboxai-postgres pg_isready -U toolboxai
```

**Solution:**

```bash
# Restart exporter with correct credentials
docker restart toolboxai-postgres-exporter

# Verify metrics available
curl http://localhost:9187/metrics | grep pg_up
# Should show: pg_up 1
```

---

### Redis Exporter Not Scraping

**Symptoms:**
- `redis_up` metric is 0 or missing
- Prometheus target shows as DOWN
- No Redis metrics in Prometheus

**Diagnosis:**

```bash
# Check exporter logs
docker logs toolboxai-redis-exporter

# Test exporter endpoint
curl http://localhost:9121/metrics

# Check redis_up metric
curl http://localhost:9121/metrics | grep redis_up
```

**Common Issues:**

1. **Authentication failure:**
```bash
# Verify Redis password
grep REDIS_PASSWORD .env

# Test Redis connection
docker exec toolboxai-redis redis-cli -a <password> ping
# Should return: PONG
```

2. **Network connectivity:**
```bash
# Verify exporter can reach Redis
docker exec toolboxai-redis-exporter nc -zv redis 6379

# Check networks
docker network inspect toolboxai_cache
```

3. **Redis not ready:**
```bash
# Check Redis health
docker exec toolboxai-redis redis-cli ping
```

**Solution:**

```bash
# Restart exporter
docker restart toolboxai-redis-exporter

# Verify metrics
curl http://localhost:9121/metrics | grep redis_up
# Should show: redis_up 1
```

---

### Metrics Not Appearing in Prometheus

**Symptoms:**
- Exporters running but metrics not in Prometheus
- Targets show as UP but no data
- Queries return empty results

**Diagnosis:**

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job | contains("exporter"))'

# Check scrape configuration
docker exec toolboxai-prometheus cat /etc/prometheus/prometheus.yml | grep -A5 postgres-exporter

# Check Prometheus logs
docker logs toolboxai-prometheus | grep -i error
```

**Solution:**

```bash
# Reload Prometheus configuration
docker exec toolboxai-prometheus curl -X POST http://localhost:9090/-/reload

# Restart Prometheus
docker restart toolboxai-prometheus

# Verify targets
open http://localhost:9090/targets
```

---

### High Cardinality Issues

**Symptoms:**
- Prometheus using excessive memory
- Slow query performance
- "too many active series" errors

**Cause:**
- Table-level metrics with many tables
- Command-level metrics with many unique commands
- Key-level metrics in Redis

**Solution:**

**Limit PostgreSQL metrics:**
```yaml
# In docker-compose.yml
postgres-exporter:
  environment:
    PG_EXPORTER_DISABLE_DEFAULT_METRICS: "true"
    PG_EXPORTER_AUTO_DISCOVER_DATABASES: "false"
    PG_EXPORTER_CONSTANT_LABELS: "env=production"
```

**Filter Redis metrics:**
```yaml
# In prometheus.yml
- job_name: 'redis-exporter'
  metric_relabel_configs:
    # Only keep essential metrics
    - source_labels: [__name__]
      regex: 'redis_(memory|connected|evicted|keyspace).*'
      action: keep
```

---

## Performance Tuning

### PostgreSQL Exporter Optimization

**Reduce scrape frequency for large databases:**
```yaml
# prometheus.yml
- job_name: 'postgres-exporter'
  scrape_interval: 60s  # Increase from 30s
  scrape_timeout: 15s   # Increase timeout
```

**Disable expensive metrics:**
```yaml
postgres-exporter:
  environment:
    PG_EXPORTER_EXCLUDE_DATABASES: "template0,template1"
    PG_EXPORTER_DISABLE_SETTINGS_METRICS: "true"
```

### Redis Exporter Optimization

**Reduce command tracking:**
```yaml
redis-exporter:
  command:
    - "--redis.password=${REDIS_PASSWORD}"
    - "--skip-check-config-presence"
    - "--is-cluster=false"
```

**Limit key scanning:**
```yaml
environment:
  REDIS_EXPORTER_CHECK_KEYS: ""  # Disable key checking
  REDIS_EXPORTER_CHECK_SINGLE_KEYS: ""
```

---

## Best Practices

### Monitoring Strategy

1. **Start Simple**: Enable exporters with default metrics
2. **Monitor Basics**: Focus on connections, memory, hit rates first
3. **Add Alerts**: Set up critical alerts (service down, high memory)
4. **Tune Gradually**: Add custom queries only when needed
5. **Review Regularly**: Check dashboards weekly, tune alerts monthly

### Security

1. **Use Read-Only Accounts**: Grant minimal permissions to exporters
2. **Secure Credentials**: Use Docker secrets or Vault
3. **Network Isolation**: Keep exporters on monitoring network
4. **Update Regularly**: Keep exporter images up to date
5. **Audit Access**: Monitor who accesses metrics

### Cost Optimization

1. **Control Cardinality**: Limit high-cardinality metrics
2. **Adjust Scrape Intervals**: Use longer intervals for stable metrics
3. **Use Recording Rules**: Pre-compute expensive queries
4. **Retention Policy**: Balance history needs with storage costs
5. **Metric Filtering**: Drop unnecessary metrics at scrape time

---

## References

- [PostgreSQL Exporter Documentation](https://github.com/prometheus-community/postgres_exporter)
- [Redis Exporter Documentation](https://github.com/oliver006/redis_exporter)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Dashboard 9628](https://grafana.com/grafana/dashboards/9628)
- [Grafana Dashboard 763](https://grafana.com/grafana/dashboards/763)

---

**Document Version:** 1.0
**Last Updated:** November 2025
**Maintained By:** ToolBoxAI DevOps Team
