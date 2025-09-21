# Phase 2 Deployment Documentation

This directory contains deployment guides, staging environment setup, and infrastructure documentation for Phase 2.

## Deployment Overview

Phase 2 deployment involves modern infrastructure with PostgreSQL 16, Redis 7, comprehensive monitoring, and zero-downtime migration capabilities.

## Infrastructure Components

### Database Layer
- **PostgreSQL 16**: Modern database with JIT compilation and logical replication
- **Redis 7**: Advanced caching with ACL v2 and Redis Functions
- **PgBouncer**: Connection pooling for performance optimization

### Application Layer
- **Backend**: FastAPI application on port 8000
- **Frontend**: React/Vite application on port 3000
- **Nginx**: Reverse proxy and load balancer

### Monitoring Layer
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation and analysis
- **Alertmanager**: Alert management and notifications

## Staging Environment

### Quick Start
```bash
# Full deployment with migration
./scripts/staging_deploy.sh full

# Deploy without migration (if already migrated)
./scripts/staging_deploy.sh full true

# Dry run to validate configuration
./scripts/staging_deploy.sh full false true
```

### Service Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboard**: http://localhost:3001 (admin/staging_grafana_2024)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### Health Verification
```bash
# Run comprehensive health checks
./scripts/health_checks/run_health_checks.sh staging

# Check all containers are running
docker ps

# View logs
docker-compose -f docker-compose.staging.yml logs -f
```

## Migration Procedures

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
Key metrics monitored:
- Database performance and connections
- Redis operations and memory usage
- Application response times
- System resource utilization
- Migration-specific metrics

### Grafana Dashboards
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
1. **Port Conflicts**: Check and resolve port usage conflicts
2. **Docker Issues**: Docker daemon and resource management
3. **Database Connection Issues**: PostgreSQL connectivity troubleshooting
4. **Memory Issues**: System and container memory management

### Debug Mode
Enable debug mode for detailed logging:
```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with verbose output
./scripts/staging_deploy.sh full 2>&1 | tee deployment.log
```

### Log Locations
- **Deployment logs**: `logs/deployment/`
- **Migration logs**: `logs/migration/`
- **Health check logs**: `logs/health_checks/`
- **Application logs**: `logs/`
- **Container logs**: `docker logs <container_name>`

## Maintenance

### Regular Maintenance Tasks
1. **Database Maintenance**: Weekly VACUUM ANALYZE and statistics updates
2. **Backup Management**: Weekly backups and cleanup procedures
3. **Log Rotation**: Application and system log rotation
4. **Monitoring Review**: Regular dashboard and alert review

### Update Procedures
1. **Application Updates**: Code deployment and rebuild procedures
2. **Database Updates**: Migration execution and statistics updates
3. **Configuration Updates**: Environment and service configuration updates

## Deployment Files

### Main Deployment Documentation
- **[STAGING_SETUP_README.md](./STAGING_SETUP_README.md)** - Comprehensive staging setup guide

### Infrastructure Scripts
- **Deployment Scripts**: `/scripts/staging_deploy.sh`
- **Migration Scripts**: `/scripts/staging_postgres16_migration.sh`
- **Health Checks**: `/scripts/health_checks/run_health_checks.sh`
- **Rollback Scripts**: `/scripts/staging_rollback.sh`

### Configuration Files
- **Docker Compose**: `docker-compose.staging.yml`
- **Environment**: `.env.staging`
- **Database Configs**: `configs/postgresql16_staging.conf`
- **Redis Configs**: `configs/redis7_staging.conf`

## Success Metrics

### Deployment Objectives
- **Zero Downtime**: Maintain service availability during migrations
- **Performance**: 30% improvement with new infrastructure
- **Reliability**: Enhanced monitoring and alerting
- **Security**: Modern security practices and configurations

### Validation Criteria
- ✅ All services operational after deployment
- ✅ Database migration completed without data loss
- ✅ Performance metrics meet or exceed targets
- ✅ Monitoring and alerting functional
- ✅ Rollback procedures validated

---

**Deployment Status**: Infrastructure Ready (Scripts and configs complete)
**Staging Environment**: Fully configured and documented
**Production Readiness**: Ready for deployment by November 30, 2025