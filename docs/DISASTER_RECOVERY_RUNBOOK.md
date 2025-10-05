# Disaster Recovery Runbook

**Version:** 1.0.0
**Last Updated:** 2025-10-02
**Owner:** Infrastructure Team
**Status:** Production Ready

## Table of Contents

1. [Overview](#overview)
2. [Recovery Time Objectives](#recovery-time-objectives)
3. [Emergency Contacts](#emergency-contacts)
4. [Pre-Disaster Preparation](#pre-disaster-preparation)
5. [Disaster Scenarios](#disaster-scenarios)
6. [Recovery Procedures](#recovery-procedures)
7. [Post-Recovery Validation](#post-recovery-validation)
8. [Lessons Learned Template](#lessons-learned-template)

---

## Overview

This runbook provides comprehensive procedures for recovering ToolboxAI infrastructure from various disaster scenarios. Follow these procedures in order during a disaster event.

### Quick Reference

| Scenario | RTO | RPO | Priority | Page |
|----------|-----|-----|----------|------|
| Complete Infrastructure Loss | 4 hours | 1 hour | P0 | [Link](#complete-infrastructure-loss) |
| Database Corruption | 2 hours | 15 min | P0 | [Link](#database-corruption) |
| Application Failure | 30 min | 0 min | P1 | [Link](#application-failure) |
| Network Outage | 1 hour | 0 min | P1 | [Link](#network-outage) |
| Security Breach | Immediate | 0 min | P0 | [Link](#security-breach) |

---

## Recovery Time Objectives

### Service Tier Classifications

#### Tier 1: Critical Services (RTO: 30 minutes)
- **Backend API** - Core application logic
- **PostgreSQL Database** - Primary data store
- **Redis Cache** - Session and cache data
- **Authentication Services** - User access

#### Tier 2: Essential Services (RTO: 2 hours)
- **Dashboard Frontend** - User interface
- **MCP Server** - Model context protocol
- **Agent Coordinator** - AI agent orchestration
- **Monitoring Stack** - Prometheus, Grafana

#### Tier 3: Supporting Services (RTO: 4 hours)
- **Celery Workers** - Background jobs
- **Roblox Sync** - Game environment sync
- **Log Aggregation** - Loki, Promtail
- **Tracing** - Jaeger distributed tracing

### Recovery Point Objectives (RPO)

| Data Type | RPO | Backup Frequency | Retention |
|-----------|-----|------------------|-----------|
| Database (Critical) | 15 minutes | Continuous WAL + 15min snapshots | 30 days |
| Database (Full) | 1 hour | Hourly snapshots | 7 days |
| Configuration | 0 minutes | Git-tracked, real-time | Infinite |
| Application State | 5 minutes | Redis AOF | 24 hours |
| Logs | 1 minute | Loki streaming | 14 days |

---

## Emergency Contacts

### On-Call Rotation

```
Primary On-Call: [PHONE] [EMAIL]
Secondary On-Call: [PHONE] [EMAIL]
Infrastructure Lead: [PHONE] [EMAIL]
CTO/Technical Director: [PHONE] [EMAIL]
```

### External Contacts

```
Cloud Provider Support: [PHONE]
Database Support: [PHONE]
Security Team: [EMAIL]
Legal/Compliance: [EMAIL]
```

### Communication Channels

- **Incident Slack Channel:** `#incident-response`
- **Status Page:** `https://status.toolboxai.com`
- **Incident Bridge:** `[Conference Line]`

---

## Pre-Disaster Preparation

### Daily Checks ✅

```bash
# 1. Verify backups completed successfully
docker compose -f infrastructure/docker/compose/docker-compose.yml \
  logs backup-coordinator | grep "Backup completed successfully"

# 2. Check monitoring health
curl -f http://localhost:9090/-/healthy
curl -f http://localhost:3000/api/health

# 3. Verify data replication
docker compose exec postgres pg_isready
docker compose exec redis redis-cli ping

# 4. Test recovery procedures (weekly)
./scripts/test-recovery.sh --dry-run
```

### Backup Verification

```bash
# Verify PostgreSQL backups
ls -lh /backup/postgres/ | tail -10

# Verify backup integrity
./scripts/verify-backup.sh --latest

# Test backup restoration (staging)
./scripts/restore-backup.sh --test --environment staging
```

### Documentation

- ✅ All runbooks up to date
- ✅ Architecture diagrams current
- ✅ Network topology documented
- ✅ Access credentials stored securely
- ✅ Recovery scripts tested monthly

---

## Disaster Scenarios

### Scenario 1: Complete Infrastructure Loss

**Trigger:** Data center outage, catastrophic hardware failure, natural disaster

**Initial Assessment (5 minutes)**

1. Confirm scope of outage
2. Activate incident response team
3. Notify stakeholders via status page
4. Establish incident bridge

**Recovery Steps**

#### Phase 1: Infrastructure Provisioning (30-60 minutes)

```bash
# 1. Provision new infrastructure
cd infrastructure/terraform
terraform init
terraform plan -out=disaster-recovery.tfplan
terraform apply disaster-recovery.tfplan

# 2. Verify networking
./scripts/verify-network.sh

# 3. Configure DNS (if needed)
./scripts/update-dns.sh --disaster-recovery
```

#### Phase 2: Data Restoration (60-90 minutes)

```bash
# 1. Identify most recent valid backup
./scripts/list-backups.sh --latest --verified

# 2. Restore PostgreSQL database
./scripts/restore-database.sh \
  --backup-id [BACKUP_ID] \
  --target-host [NEW_DB_HOST] \
  --verify

# 3. Restore Redis state
./scripts/restore-redis.sh \
  --backup-id [BACKUP_ID] \
  --target-host [NEW_REDIS_HOST]

# 4. Verify data integrity
./scripts/verify-data-integrity.sh --full-check
```

#### Phase 3: Service Deployment (45-60 minutes)

```bash
# 1. Deploy core services
docker compose -f infrastructure/docker/compose/docker-compose.yml \
  -f infrastructure/docker/compose/docker-compose.prod.yml \
  up -d postgres redis

# Wait for databases to be healthy
./scripts/wait-for-services.sh --timeout 300 postgres redis

# 2. Deploy application services
docker compose -f infrastructure/docker/compose/docker-compose.yml \
  -f infrastructure/docker/compose/docker-compose.prod.yml \
  up -d backend dashboard mcp-server agent-coordinator

# 3. Deploy supporting services
docker compose -f infrastructure/docker/compose/docker-compose.yml \
  -f infrastructure/docker/compose/docker-compose.prod.yml \
  up -d celery-worker celery-beat prometheus grafana
```

#### Phase 4: Validation (15-30 minutes)

```bash
# Run comprehensive health checks
./scripts/health-check.sh --full --critical-only

# Verify all services
docker compose ps | grep "Up (healthy)"

# Run smoke tests
./tests/smoke-tests.sh --production

# Monitor for errors
./scripts/monitor-logs.sh --duration 300 --alert-on-error
```

**Total Estimated Recovery Time: 3.5 - 4 hours**

---

### Scenario 2: Database Corruption

**Trigger:** Data corruption, failed migration, hardware failure

**Immediate Actions (< 5 minutes)**

```bash
# 1. Stop writes to database immediately
docker compose stop backend celery-worker

# 2. Assess corruption scope
docker compose exec postgres pg_dump --schema-only > /tmp/schema-check.sql

# 3. Check WAL status
docker compose exec postgres psql -c "SELECT pg_last_wal_receive_lsn();"
```

**Recovery Options**

#### Option A: Point-in-Time Recovery (Preferred)

```bash
# 1. Stop PostgreSQL
docker compose stop postgres

# 2. Backup corrupted data (forensics)
sudo tar -czf /backup/corrupted-$(date +%Y%m%d-%H%M%S).tar.gz \
  /data/postgres/

# 3. Restore from latest clean backup
./scripts/restore-database.sh \
  --point-in-time "2025-10-02 14:30:00" \
  --verify-before-restore

# 4. Replay WAL to specific point
./scripts/replay-wal.sh --until "2025-10-02 14:30:00"

# 5. Start PostgreSQL and verify
docker compose up -d postgres
./scripts/verify-database.sh --integrity-check
```

#### Option B: Full Backup Restore

```bash
# 1. Identify last known good backup
./scripts/list-backups.sh --verified --before-incident

# 2. Restore from backup
./scripts/restore-database.sh \
  --backup-id [BACKUP_ID] \
  --force \
  --verify

# 3. Check data consistency
./scripts/verify-data-consistency.sh --full
```

#### Option C: Replica Promotion (if available)

```bash
# 1. Stop primary database
docker compose stop postgres

# 2. Promote read replica to primary
./scripts/promote-replica.sh --replica-id [REPLICA_ID]

# 3. Update application configuration
./scripts/update-db-config.sh --new-primary [NEW_PRIMARY_HOST]

# 4. Restart applications
docker compose restart backend celery-worker
```

**Total Estimated Recovery Time: 1 - 2 hours**

---

### Scenario 3: Application Failure

**Trigger:** Application crash, memory leak, deadlock, code bug

**Quick Recovery (< 30 minutes)**

```bash
# 1. Identify failing service
docker compose ps | grep -v "Up (healthy)"

# 2. Check service logs
docker compose logs --tail=100 [SERVICE_NAME]

# 3. Restart service
docker compose restart [SERVICE_NAME]

# 4. If restart fails, rollback to previous version
docker compose down [SERVICE_NAME]
docker tag toolboxai/[SERVICE]:previous toolboxai/[SERVICE]:latest
docker compose up -d [SERVICE_NAME]

# 5. Monitor recovery
watch -n 5 'docker compose ps [SERVICE_NAME]'
```

**If Issue Persists**

```bash
# 1. Scale down to isolate issue
docker compose scale [SERVICE_NAME]=1

# 2. Check resource usage
docker stats [SERVICE_NAME]

# 3. Enable debug logging
docker compose restart [SERVICE_NAME] --env LOG_LEVEL=DEBUG

# 4. Collect diagnostics
./scripts/collect-diagnostics.sh --service [SERVICE_NAME]

# 5. Escalate to development team
./scripts/create-incident.sh --severity high --service [SERVICE_NAME]
```

**Total Estimated Recovery Time: 15 - 30 minutes**

---

### Scenario 4: Network Outage

**Trigger:** Network partition, DNS failure, routing issues

**Diagnosis (5-10 minutes)**

```bash
# 1. Check container connectivity
docker compose exec backend ping -c 3 postgres
docker compose exec backend ping -c 3 redis

# 2. Verify DNS resolution
docker compose exec backend nslookup postgres
docker compose exec backend nslookup redis

# 3. Check Docker networks
docker network ls
docker network inspect toolboxai_backend

# 4. Verify external connectivity
curl -I https://api.toolboxai.com/health
```

**Recovery Steps**

#### Internal Network Issues

```bash
# 1. Restart affected containers
docker compose restart [AFFECTED_SERVICES]

# 2. If that fails, recreate networks
docker compose down
docker network prune -f
docker compose up -d

# 3. Verify network connectivity
./scripts/test-network-connectivity.sh --full
```

#### External Network Issues

```bash
# 1. Verify cloud provider network status
# Check provider status page

# 2. Switch to backup network path (if available)
./scripts/switch-network-path.sh --backup

# 3. Update firewall rules if needed
./scripts/update-firewall.sh --emergency

# 4. Test connectivity
./scripts/test-external-connectivity.sh
```

**Total Estimated Recovery Time: 30 - 60 minutes**

---

### Scenario 5: Security Breach

**Trigger:** Unauthorized access, data leak, malware detection

**Immediate Actions (< 5 minutes) 🚨**

```bash
# 1. ISOLATE COMPROMISED SYSTEMS
docker compose stop [COMPROMISED_SERVICES]

# 2. BLOCK ATTACKER IP ADDRESSES
./scripts/block-ips.sh --ips [ATTACKER_IPS] --immediate

# 3. ROTATE ALL CREDENTIALS
./scripts/rotate-credentials.sh --emergency --all

# 4. ENABLE ENHANCED LOGGING
./scripts/enable-audit-logging.sh --level maximum

# 5. NOTIFY SECURITY TEAM
./scripts/alert-security-team.sh --severity critical
```

**Investigation Phase (1-2 hours)**

```bash
# 1. Collect forensic evidence
./scripts/collect-forensics.sh --preserve-evidence

# 2. Analyze access logs
./scripts/analyze-access-logs.sh --suspicious-activity

# 3. Check for data exfiltration
./scripts/check-data-exfiltration.sh --timerange "last 48 hours"

# 4. Identify compromised accounts
./scripts/identify-compromised-accounts.sh

# 5. Document timeline
./scripts/create-incident-timeline.sh --security-breach
```

**Containment Phase (2-4 hours)**

```bash
# 1. Rebuild compromised systems from clean images
./scripts/rebuild-compromised-systems.sh --verified-images

# 2. Apply security patches
./scripts/apply-security-patches.sh --emergency

# 3. Strengthen access controls
./scripts/harden-security.sh --maximum-security

# 4. Deploy intrusion detection
./scripts/deploy-ids.sh --enhanced-monitoring

# 5. Verify no backdoors remain
./scripts/scan-for-backdoors.sh --comprehensive
```

**Recovery Phase (2-4 hours)**

```bash
# 1. Restore from pre-breach backup
./scripts/restore-from-backup.sh --before-breach

# 2. Gradually restore services
./scripts/restore-services.sh --gradual --monitored

# 3. Monitor for continued attacks
./scripts/monitor-for-attacks.sh --duration 24h

# 4. Communicate with stakeholders
./scripts/send-security-notification.sh --users-affected
```

**Total Estimated Recovery Time: 8 - 12 hours**

---

## Recovery Procedures

### Standard Recovery Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DETECT → 2. ASSESS → 3. CONTAIN → 4. RECOVER → 5. VERIFY │
└─────────────────────────────────────────────────────────────┘
```

### Phase 1: Detection & Assessment

**Checklist:**
- [ ] Incident detected and confirmed
- [ ] Incident commander assigned
- [ ] Incident severity classified (P0-P3)
- [ ] Initial assessment completed
- [ ] Stakeholders notified
- [ ] Status page updated

### Phase 2: Containment

**Checklist:**
- [ ] Stop impact from spreading
- [ ] Isolate affected systems
- [ ] Preserve evidence if needed
- [ ] Document initial findings
- [ ] Establish recovery timeline

### Phase 3: Recovery

**Checklist:**
- [ ] Recovery plan approved
- [ ] Backup integrity verified
- [ ] Recovery scripts tested
- [ ] Services restored in priority order
- [ ] Configuration validated
- [ ] Security hardening applied

### Phase 4: Verification

**Checklist:**
- [ ] All services healthy
- [ ] Data integrity verified
- [ ] Performance metrics normal
- [ ] Security scan passed
- [ ] Smoke tests passed
- [ ] User acceptance testing completed

### Phase 5: Post-Incident

**Checklist:**
- [ ] Incident timeline documented
- [ ] Root cause identified
- [ ] Preventive measures defined
- [ ] Runbook updated
- [ ] Post-mortem scheduled
- [ ] Lessons learned shared

---

## Post-Recovery Validation

### Automated Validation Suite

```bash
#!/bin/bash
# Run after recovery to verify system health

echo "Starting post-recovery validation..."

# 1. Service Health Checks
echo "Checking service health..."
./scripts/health-check.sh --all-services

# 2. Data Integrity Checks
echo "Verifying data integrity..."
./scripts/verify-data-integrity.sh --full

# 3. Performance Baseline
echo "Checking performance metrics..."
./scripts/baseline-performance.sh --compare-to-normal

# 4. Security Scan
echo "Running security scan..."
./scripts/security-scan.sh --comprehensive

# 5. Integration Tests
echo "Running integration tests..."
./tests/integration-tests.sh --production-safe

# 6. User Acceptance Tests
echo "Running UAT scenarios..."
./tests/uat-scenarios.sh --critical-paths

echo "Validation complete. Review results above."
```

### Manual Validation Checklist

#### Application Layer
- [ ] Can users log in successfully
- [ ] Can users access their data
- [ ] All features functioning correctly
- [ ] No error messages displayed
- [ ] Response times acceptable

#### Data Layer
- [ ] Recent data present
- [ ] No data corruption detected
- [ ] Backup job successful
- [ ] Replication working
- [ ] Indexes rebuilt

#### Infrastructure Layer
- [ ] All containers running
- [ ] Resource usage normal
- [ ] Network connectivity verified
- [ ] Monitoring operational
- [ ] Alerting functional

---

## Lessons Learned Template

```markdown
# Post-Incident Review: [INCIDENT_ID]

## Incident Summary
- **Date:** YYYY-MM-DD
- **Duration:** X hours
- **Severity:** PX
- **Services Affected:** [List]

## Timeline
| Time | Event |
|------|-------|
| 00:00 | Incident detected |
| 00:15 | Response team activated |
| ... | ... |

## Root Cause
[Detailed analysis of what caused the incident]

## Recovery Actions Taken
1. [Action 1]
2. [Action 2]
...

## What Went Well
- [Success 1]
- [Success 2]

## What Can Be Improved
- [Improvement 1]
- [Improvement 2]

## Action Items
| Item | Owner | Due Date | Status |
|------|-------|----------|--------|
| [Action] | [Name] | YYYY-MM-DD | Open |

## Preventive Measures
1. [Prevention 1]
2. [Prevention 2]

## Runbook Updates Required
- [ ] Update detection procedures
- [ ] Update recovery steps
- [ ] Add new failure scenario
- [ ] Update contact information
```

---

## Appendices

### Appendix A: Quick Command Reference

```bash
# Emergency Stop All Services
docker compose down --remove-orphans

# Start Core Services Only
docker compose up -d postgres redis backend

# View Real-Time Logs
docker compose logs -f --tail=100 [SERVICE]

# Check Service Health
curl -f http://localhost:8009/health

# Force Restart Container
docker compose restart --timeout 30 [SERVICE]

# Exec into Container
docker compose exec [SERVICE] /bin/bash

# Check Resource Usage
docker stats --no-stream

# Network Diagnostics
docker network ls
docker network inspect [NETWORK_NAME]
```

### Appendix B: Backup Locations

```
Primary Backups:   /backup/postgres/
Secondary Backups: s3://toolboxai-backups/
Tertiary Backups:  [Cloud provider backup service]

Configuration:     git@github.com:toolboxai/infrastructure.git
Docker Images:     docker.io/toolboxai/*
Secrets:           [Secret manager service]
```

### Appendix C: Important URLs

```
Production:   https://app.toolboxai.com
Status Page:  https://status.toolboxai.com
Monitoring:   https://metrics.toolboxai.com
Logs:         https://logs.toolboxai.com
Dashboards:   https://grafana.toolboxai.com
```

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-02 | Infrastructure Team | Initial version |

**Next Review Date:** 2025-11-02

---

## Emergency Hotline

```
🚨 EMERGENCY INFRASTRUCTURE SUPPORT 🚨
Phone: [EMERGENCY_NUMBER]
Email: emergency@toolboxai.com
Slack: #incident-response
```

**Remember:** Stay calm, follow the procedures, communicate clearly, and document everything.
