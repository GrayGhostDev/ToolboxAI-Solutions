# ToolBoxAI Staging Environment Setup

This document provides comprehensive instructions for setting up and managing the ToolBoxAI staging environment with PostgreSQL 16 migration, Redis 7 upgrade, and complete monitoring stack.

## Overview

The staging environment includes:

- **PostgreSQL 16** with JIT compilation and logical replication
- **Redis 7** with advanced features and ACL configuration
- **PgBouncer** for connection pooling
- **Comprehensive monitoring** with Prometheus, Grafana, and Loki
- **Zero-downtime migration** procedures
- **Automated rollback** capabilities
- **Performance benchmarking** and validation

## Quick Start

### 1. Deploy Complete Staging Environment

```bash
# Full deployment with migration
./scripts/staging_deploy.sh full

# Deploy without migration (if already migrated)
./scripts/staging_deploy.sh full true

# Dry run to validate configuration
./scripts/staging_deploy.sh full false true
```

### 2. Access Services

After deployment, access your services at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboard**: http://localhost:3001 (admin/staging_grafana_2024)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### 3. Verify Deployment

```bash
# Run comprehensive health checks
./scripts/health_checks/run_health_checks.sh staging

# Check all containers are running
docker ps

# View logs
docker-compose -f docker-compose.staging.yml logs -f
```

## Architecture

### Database Layer

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL 15 │    │   PostgreSQL 16 │    │    PgBouncer    │
│   (Legacy)      │───▶│   (Primary)     │◀───│  (Pool Manager) │
│   Port: 5433    │    │   Port: 5432    │    │   Port: 6432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                  │
                       ┌─────────────────┐
                       │     Redis 7     │
                       │   Port: 6379    │
                       └─────────────────┘
```

### Application Layer

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │    Backend      │    │    Frontend     │
│  (Reverse Proxy)│───▶│   (FastAPI)     │◀───│   (React/Vite)  │
│   Port: 80/443  │    │   Port: 8000    │    │   Port: 3000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Monitoring Layer

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │◀───│     Grafana     │    │      Loki       │
│   Port: 9090    │    │   Port: 3001    │    │   Port: 3100    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
    ┌────▼──────┬─────────────────▼──────┬────────────────▼────┐
    │  Node     │   Postgres/Redis       │      Promtail      │
    │ Exporter  │     Exporters          │   (Log Collector)  │
    └───────────┴────────────────────────┴─────────────────────┘
```

## Detailed Setup Instructions

### Prerequisites

1. **System Requirements**:
   - Docker 20.10+
   - Docker Compose 2.0+
   - 8GB RAM (minimum 4GB)
   - 20GB free disk space
   - Ubuntu 20.04+ or equivalent

2. **Network Requirements**:
   - Ports 80, 443, 3000, 3001, 5432, 5433, 6379, 6432, 8000, 9090-9200 available
   - Internet access for Docker image pulls

### Environment Configuration

1. **Review Environment Settings**:
   ```bash
   # Edit staging configuration
   nano .env.staging

   # Key settings to review:
   # - Database passwords
   # - Redis passwords
   # - JWT secrets
   # - External API keys
   ```

2. **Database Configuration**:
   ```bash
   # PostgreSQL 16 settings
   nano configs/postgresql16_staging.conf

   # Redis 7 settings
   nano configs/redis7_staging.conf

   # PgBouncer settings
   nano configs/pgbouncer_staging.ini
   ```

### Step-by-Step Deployment

#### Phase 1: Infrastructure Setup

```bash
# 1. Validate prerequisites
./scripts/staging_deploy.sh full false true  # Dry run

# 2. Setup Docker networks and volumes
docker network create backend
docker network create monitoring

# 3. Create necessary directories
mkdir -p logs/{postgresql,redis,nginx,monitoring}
mkdir -p backups uploads
```

#### Phase 2: Database Deployment

```bash
# 1. Deploy database services only
./scripts/staging_deploy.sh database-only

# 2. Verify database connectivity
./scripts/health_checks/run_health_checks.sh staging

# 3. Run migration (if needed)
./scripts/staging_postgres16_migration.sh
```

#### Phase 3: Application Deployment

```bash
# 1. Build and deploy application services
docker-compose -f docker-compose.staging.yml up -d --build backend frontend nginx

# 2. Verify application endpoints
curl http://localhost:8000/health
curl http://localhost:3000
```

#### Phase 4: Monitoring Setup

```bash
# 1. Deploy monitoring stack
./scripts/staging_deploy.sh monitoring-only

# 2. Access Grafana
open http://localhost:3001
# Login: admin / staging_grafana_2024
```

## Migration Process

### PostgreSQL 16 Migration

The migration uses logical replication for zero-downtime migration:

```bash
# 1. Run pre-migration checks
./scripts/staging_postgres16_migration.sh --validate

# 2. Create backup
./scripts/staging_postgres16_migration.sh --backup-only

# 3. Execute full migration
./scripts/staging_postgres16_migration.sh

# 4. Validate post-migration
./scripts/health_checks/run_health_checks.sh staging
```

### Migration Features

1. **JIT Compilation**: Enabled for queries with cost > 100,000
2. **Parallel Queries**: Up to 4 workers per gather operation
3. **Logical Replication**: For zero-downtime migration
4. **Performance Monitoring**: Built-in pg_stat_io monitoring
5. **Automated Rollback**: In case of migration failure

## Monitoring and Observability

### Prometheus Metrics

Access metrics at http://localhost:9090

Key metrics monitored:
- Database performance and connections
- Redis operations and memory usage
- Application response times
- System resource utilization
- Migration-specific metrics

### Grafana Dashboards

Access dashboards at http://localhost:3001

Available dashboards:
- **PostgreSQL Overview**: Database performance, connections, queries
- **Redis Monitoring**: Memory usage, operations, latency
- **Application Metrics**: API response times, error rates
- **System Resources**: CPU, memory, disk, network
- **Migration Progress**: Migration-specific metrics and alerts

### Log Aggregation

Logs are collected by Promtail and stored in Loki:
- Application logs: `/logs/`
- Database logs: Container logs
- System logs: `/var/log/`

Query logs in Grafana using LogQL syntax.

## Health Checks and Validation

### Comprehensive Health Checks

```bash
# Run all health checks
./scripts/health_checks/run_health_checks.sh staging

# Check specific components
docker exec toolboxai-postgres16-staging pg_isready
docker exec toolboxai-redis7-staging redis-cli ping
curl -f http://localhost:8000/health
```

### Performance Validation

```bash
# Run performance benchmarks
./scripts/staging_postgres16_migration.sh --benchmark-only

# Monitor JIT compilation
psql -h localhost -p 5432 -U toolboxai_user -d toolboxai_staging \
  -c "SELECT * FROM pg_stat_statements WHERE jit_functions > 0;"

# Check parallel query execution
psql -h localhost -p 5432 -U toolboxai_user -d toolboxai_staging \
  -c "EXPLAIN (ANALYZE, BUFFERS) SELECT COUNT(*) FROM users;"
```

## Rollback Procedures

### Emergency Rollback

```bash
# Full system rollback
./scripts/staging_rollback.sh full

# Database-only rollback
./scripts/staging_rollback.sh postgres15

# Check rollback status
./scripts/health_checks/run_health_checks.sh staging
```

### Rollback Objectives

- **RTO (Recovery Time Objective)**: 30 minutes
- **RPO (Recovery Point Objective)**: 5 minutes
- **Automated rollback** in case of migration failure
- **Data integrity validation** during rollback

## Troubleshooting

### Common Issues

1. **Port Conflicts**:
   ```bash
   # Check port usage
   netstat -tulpn | grep :5432

   # Kill conflicting processes
   sudo fuser -k 5432/tcp
   ```

2. **Docker Issues**:
   ```bash
   # Restart Docker daemon
   sudo systemctl restart docker

   # Clean up Docker resources
   docker system prune -f
   ```

3. **Database Connection Issues**:
   ```bash
   # Check PostgreSQL logs
   docker logs toolboxai-postgres16-staging

   # Test direct connection
   psql -h localhost -p 5432 -U toolboxai_user -d toolboxai_staging
   ```

4. **Memory Issues**:
   ```bash
   # Check memory usage
   free -h
   docker stats

   # Adjust PostgreSQL memory settings
   nano configs/postgresql16_staging.conf
   ```

### Log Locations

- **Deployment logs**: `logs/deployment/`
- **Migration logs**: `logs/migration/`
- **Health check logs**: `logs/health_checks/`
- **Application logs**: `logs/`
- **Container logs**: `docker logs <container_name>`

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with verbose output
./scripts/staging_deploy.sh full 2>&1 | tee deployment.log
```

## Security Considerations

### Database Security

1. **Passwords**: All default passwords should be changed in production
2. **SSL/TLS**: Configure SSL for database connections in production
3. **Network Security**: Restrict database access to application networks
4. **Backup Encryption**: Enable backup encryption for sensitive data

### Application Security

1. **JWT Secrets**: Use strong, unique JWT secrets
2. **CORS Configuration**: Restrict CORS origins to known domains
3. **Rate Limiting**: Configure appropriate rate limits
4. **Input Validation**: Ensure all inputs are properly validated

### Infrastructure Security

1. **Container Security**: Regular image updates and vulnerability scanning
2. **Network Segmentation**: Proper network isolation between services
3. **Monitoring Security**: Secure access to monitoring dashboards
4. **Backup Security**: Secure backup storage and access

## Performance Optimization

### PostgreSQL 16 Optimizations

1. **JIT Compilation**: Automatically enabled for expensive queries
2. **Parallel Queries**: Optimized for multi-core systems
3. **Connection Pooling**: PgBouncer reduces connection overhead
4. **Statistics**: Enhanced statistics collection for query optimization

### Redis 7 Optimizations

1. **Memory Management**: Optimized memory usage and eviction policies
2. **Persistence**: Balanced RDB and AOF for data safety and performance
3. **ACL Security**: Role-based access control for enhanced security
4. **Functions**: Redis Functions for complex operations

### Application Optimizations

1. **Caching Strategy**: Multi-level caching with Redis
2. **Database Queries**: Optimized queries with proper indexing
3. **Connection Management**: Efficient connection pooling
4. **Resource Monitoring**: Continuous performance monitoring

## Maintenance

### Regular Maintenance Tasks

1. **Database Maintenance**:
   ```bash
   # Run VACUUM ANALYZE weekly
   psql -h localhost -p 5432 -U toolboxai_user -d toolboxai_staging -c "VACUUM ANALYZE;"

   # Update statistics
   psql -h localhost -p 5432 -U toolboxai_user -d toolboxai_staging -c "ANALYZE;"
   ```

2. **Backup Management**:
   ```bash
   # Create weekly backups
   pg_dump -h localhost -p 5432 -U toolboxai_user -d toolboxai_staging > backup_$(date +%Y%m%d).sql

   # Clean old backups (keep 30 days)
   find backups/ -name "*.sql" -mtime +30 -delete
   ```

3. **Log Rotation**:
   ```bash
   # Rotate application logs
   logrotate -f /etc/logrotate.d/toolboxai-staging

   # Clean old Docker logs
   docker system prune -f
   ```

4. **Monitoring Review**:
   - Review Grafana dashboards weekly
   - Check for performance degradation
   - Validate alert thresholds
   - Update monitoring configurations

### Update Procedures

1. **Application Updates**:
   ```bash
   # Pull latest code
   git pull origin main

   # Rebuild and deploy
   docker-compose -f docker-compose.staging.yml up -d --build
   ```

2. **Database Updates**:
   ```bash
   # Run database migrations
   python -m alembic upgrade head

   # Update statistics
   psql -h localhost -p 5432 -U toolboxai_user -d toolboxai_staging -c "ANALYZE;"
   ```

3. **Configuration Updates**:
   ```bash
   # Update configurations
   nano .env.staging

   # Restart affected services
   docker-compose -f docker-compose.staging.yml restart
   ```

## Support and Documentation

### Additional Resources

- **Project Documentation**: `docs/`
- **API Documentation**: http://localhost:8000/docs
- **Database Schema**: `database/schema/`
- **Monitoring Guides**: `docs/monitoring/`

### Getting Help

1. **Check Logs**: Always start with application and system logs
2. **Run Health Checks**: Use the comprehensive health check script
3. **Review Metrics**: Check Grafana dashboards for performance issues
4. **Rollback if Needed**: Use automated rollback procedures if issues persist

### Contact Information

For support with this staging environment setup, please refer to:
- **Project Repository**: [ToolBoxAI-Solutions](https://github.com/your-org/ToolBoxAI-Solutions)
- **Documentation**: `docs/` directory
- **Issue Tracker**: GitHub Issues

---

**Last Updated**: September 2024
**Version**: 1.0
**Environment**: Staging
**PostgreSQL Version**: 16
**Redis Version**: 7