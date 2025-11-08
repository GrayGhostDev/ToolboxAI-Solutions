# Disaster Recovery Runbook

## Overview

This runbook provides step-by-step procedures for recovering from various disaster scenarios affecting the ToolboxAI platform.

**Target RTO (Recovery Time Objective):** 15 minutes  
**Target RPO (Recovery Point Objective):** 5 minutes

---

## Escalation Chain

| Role | Name | Contact | Responsibility |
|------|------|---------|----------------|
| On-Call Engineer | TBD | +1-XXX-XXX-XXXX | First responder |
| DevOps Lead | TBD | +1-XXX-XXX-XXXX | Escalation point |
| CTO | TBD | +1-XXX-XXX-XXXX | Executive escalation |

---

## Scenario 1: Database Failure (Supabase)

### Symptoms
- Application cannot connect to database
- 500 errors on API endpoints
- Database queries timing out

### Diagnosis
```bash
# Check Supabase status
curl https://status.supabase.com/api/v2/status.json

# Test database connection
psql "$SUPABASE_DATABASE_URL" -c "SELECT 1"

# Check application logs
docker logs toolboxai-backend1 | grep -i "database\|connection"
```

### Recovery Steps

#### Option A: Supabase is Down (Wait for Recovery)
1. **Check Supabase Status Page**
   - Visit: https://status.supabase.com
   - Subscribe to updates

2. **Enable Maintenance Mode**
   ```bash
   # Redirect traffic to maintenance page
   docker exec toolboxai-nginx-proxy \
     cp /etc/nginx/maintenance.conf /etc/nginx/sites-enabled/default.conf
   docker exec toolboxai-nginx-proxy nginx -s reload
   ```

3. **Communicate with Stakeholders**
   - Post status update
   - Notify customers
   - Provide ETA if available

4. **Monitor Recovery**
   ```bash
   # Continuously test connection
   watch -n 30 'psql "$SUPABASE_DATABASE_URL" -c "SELECT 1"'
   ```

5. **Restore Service**
   ```bash
   # Revert maintenance mode
   docker exec toolboxai-nginx-proxy \
     cp /etc/nginx/sites-enabled/toolboxai.conf.backup \
     /etc/nginx/sites-enabled/default.conf
   docker exec toolboxai-nginx-proxy nginx -s reload
   ```

#### Option B: Restore from Backup
1. **Access Latest Backup**
   ```bash
   # List backups
   aws s3 ls s3://your-backup-bucket/supabase/ --recursive

   # Download latest backup
   aws s3 cp s3://your-backup-bucket/supabase/backup_latest.dump ./
   ```

2. **Create New Supabase Project**
   - Go to Supabase dashboard
   - Create new project
   - Note credentials

3. **Restore Data**
   ```bash
   # Restore from backup
   pg_restore -h db.NEW-PROJECT-ID.supabase.co \
     -U postgres \
     -d postgres \
     --clean \
     --if-exists \
     --no-owner \
     --no-privileges \
     backup_latest.dump
   ```

4. **Update Application Configuration**
   ```bash
   # Update credentials in Vault
   vault kv put secret/toolboxai/supabase \
     url="https://NEW-PROJECT-ID.supabase.co" \
     database_url="postgresql://postgres:PASSWORD@db.NEW-PROJECT-ID.supabase.co:5432/postgres"
   
   # Restart backend services
   docker-compose -f docker-compose.phase2.yml restart backend1 backend2 backend3
   ```

5. **Verify Recovery**
   ```bash
   # Test API
   curl https://api.toolboxai.com/health
   
   # Check database
   psql "$NEW_SUPABASE_URL" -c "SELECT count(*) FROM users"
   ```

**Recovery Time:** 30-45 minutes

---

## Scenario 2: Redis Failure

### Symptoms
- Cache misses
- Slow API responses
- Session management issues

### Diagnosis
```bash
# Check Redis master
docker exec toolboxai-redis-master redis-cli --tls -p 6380 -a PASSWORD ping

# Check Sentinel status
docker exec toolboxai-redis-sentinel1 redis-cli -p 26379 sentinel master toolboxai-master

# Check replication
docker exec toolboxai-redis-master redis-cli --tls -p 6380 -a PASSWORD info replication
```

### Recovery Steps

#### Option A: Sentinel Automatic Failover
1. **Verify Failover Occurred**
   ```bash
   # Check new master
   docker exec toolboxai-redis-sentinel1 \
     redis-cli -p 26379 sentinel get-master-addr-by-name toolboxai-master
   ```

2. **Application Should Auto-Reconnect**
   - Sentinel-aware clients reconnect automatically
   - Monitor application logs

3. **Restart Failed Node**
   ```bash
   docker-compose -f docker-compose.phase2.yml restart redis-master
   ```

**Recovery Time:** < 5 minutes (automatic)

#### Option B: Manual Failover
1. **Trigger Manual Failover**
   ```bash
   docker exec toolboxai-redis-sentinel1 \
     redis-cli -p 26379 sentinel failover toolboxai-master
   ```

2. **Verify New Master**
   ```bash
   docker exec toolboxai-redis-sentinel1 \
     redis-cli -p 26379 sentinel master toolboxai-master
   ```

3. **Restart Backend Services**
   ```bash
   docker-compose -f docker-compose.phase2.yml restart backend1 backend2 backend3
   ```

**Recovery Time:** 5-10 minutes

---

## Scenario 3: Complete Infrastructure Loss

### Symptoms
- All services down
- No response from any endpoint
- Infrastructure completely unavailable

### Recovery Steps

1. **Assess Damage**
   - Determine scope of failure
   - Identify available resources
   - Check backup accessibility

2. **Provision New Infrastructure**
   ```bash
   # On new server
   git clone https://github.com/your-org/toolboxai.git
   cd toolboxai
   
   # Install Docker
   curl -fsSL https://get.docker.com | sh
   
   # Initialize Docker Swarm
   docker swarm init
   ```

3. **Restore Certificates**
   ```bash
   # Restore from backup
   aws s3 sync s3://your-backup-bucket/certificates/ infrastructure/certificates/
   
   # Or regenerate
   cd infrastructure/scripts
   ./generate-certs.sh
   ```

4. **Create Docker Secrets**
   ```bash
   # Restore from Vault backup or regenerate
   aws s3 cp s3://your-backup-bucket/vault/vault-keys.txt ./
   
   # Create secrets
   cat vault-keys.txt | grep "Root Token" | awk '{print $3}' | docker secret create vault_token -
   # ... create other secrets
   ```

5. **Restore Vault Data**
   ```bash
   # Start Vault
   docker-compose -f infrastructure/docker/compose/docker-compose.phase2.yml up -d vault
   
   # Restore snapshot
   aws s3 cp s3://your-backup-bucket/vault/vault-snapshot.snap ./
   vault operator raft snapshot restore vault-snapshot.snap
   ```

6. **Start Services**
   ```bash
   cd infrastructure/docker/compose
   docker-compose -f docker-compose.phase2.yml up -d
   ```

7. **Verify All Services**
   ```bash
   # Check health
   docker ps
   curl https://api.toolboxai.com/health
   
   # Test database
   psql "$SUPABASE_DATABASE_URL" -c "SELECT 1"
   
   # Test Redis
   docker exec toolboxai-redis-master redis-cli --tls -p 6380 ping
   ```

**Recovery Time:** 1-2 hours

---

## Scenario 4: Application Service Failure

### Symptoms
- API endpoints returning errors
- Backend containers crashing
- Load balancer showing backends down

### Diagnosis
```bash
# Check service status
docker-compose -f docker-compose.phase2.yml ps

# Check logs
docker logs toolboxai-backend1 --tail 100

# Check resource usage
docker stats
```

### Recovery Steps

1. **Identify Failing Service**
   ```bash
   # Check HAProxy stats
   curl http://localhost:8404/stats
   
   # Check individual backends
   docker exec toolboxai-backend1 curl localhost:8000/health
   ```

2. **Restart Failed Service**
   ```bash
   docker-compose -f docker-compose.phase2.yml restart backend1
   ```

3. **If Restart Fails, Investigate**
   ```bash
   # Check detailed logs
   docker logs toolboxai-backend1 -f
   
   # Check resource limits
   docker inspect toolboxai-backend1 | jq '.[0].HostConfig.Memory'
   
   # Check dependencies
   docker exec toolboxai-backend1 nc -zv redis-master 6380
   ```

4. **Rollback if Needed**
   ```bash
   # Revert to previous image
   docker tag toolboxai/backend:previous toolboxai/backend:latest
   docker-compose -f docker-compose.phase2.yml up -d backend1
   ```

**Recovery Time:** 5-15 minutes

---

## Scenario 5: Network Partition

### Symptoms
- Services can't communicate
- Database connection issues
- Redis replication lag

### Diagnosis
```bash
# Test network connectivity
docker exec toolboxai-backend1 ping redis-master
docker exec toolboxai-backend1 nc -zv db.project-id.supabase.co 5432

# Check Docker networks
docker network ls
docker network inspect toolboxai_backend
```

### Recovery Steps

1. **Verify Network Configuration**
   ```bash
   # Check network settings
   docker network inspect toolboxai_backend | jq '.[0].IPAM'
   ```

2. **Recreate Networks**
   ```bash
   # Stop services
   docker-compose -f docker-compose.phase2.yml down
   
   # Remove networks
   docker network rm toolboxai_backend toolboxai_cache
   
   # Restart (networks auto-recreate)
   docker-compose -f docker-compose.phase2.yml up -d
   ```

3. **Verify Connectivity**
   ```bash
   # Test internal connectivity
   docker exec toolboxai-backend1 ping backend2
   docker exec toolboxai-backend1 nc -zv redis-master 6380
   ```

**Recovery Time:** 10-20 minutes

---

## Post-Incident Actions

After any recovery:

1. **Document Incident**
   - What happened
   - When it was detected
   - How it was resolved
   - Time to recovery

2. **Update Runbook**
   - Add any new procedures
   - Improve existing steps
   - Document lessons learned

3. **Post-Mortem Meeting**
   - Review timeline
   - Identify root cause
   - Action items to prevent recurrence

4. **Improve Monitoring**
   - Add alerts for this scenario
   - Improve detection time
   - Automate recovery if possible

---

## Testing Schedule

| Test | Frequency | Last Run | Next Run |
|------|-----------|----------|----------|
| Database failover | Quarterly | TBD | TBD |
| Redis failover | Monthly | TBD | TBD |
| Full DR drill | Bi-annually | TBD | TBD |
| Backup restore | Monthly | TBD | TBD |

---

## Important Contacts

### External Services
- **Supabase Support**: support@supabase.com
- **Cloud Provider**: [Provider support]
- **DNS Provider**: [Provider support]

### Internal
- **Engineering Slack**: #toolboxai-incidents
- **Status Page**: https://status.toolboxai.com

---

## Quick Reference Commands

```bash
# Check all service health
docker-compose -f docker-compose.phase2.yml ps

# View logs
docker-compose -f docker-compose.phase2.yml logs -f

# Restart all services
docker-compose -f docker-compose.phase2.yml restart

# Full restart (with rebuild)
docker-compose -f docker-compose.phase2.yml down
docker-compose -f docker-compose.phase2.yml up -d

# Database backup
./infrastructure/scripts/backup-supabase.sh

# Check Supabase connection
psql "$SUPABASE_DATABASE_URL" -c "SELECT version()"

# Check Redis master
docker exec toolboxai-redis-sentinel1 redis-cli -p 26379 sentinel master toolboxai-master
```

---

**Last Updated**: November 7, 2025  
**Version**: 1.0  
**Owner**: DevOps Team

