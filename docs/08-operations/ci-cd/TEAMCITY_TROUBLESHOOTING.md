# TeamCity Troubleshooting Guide

**Created**: 2025-11-08
**TeamCity Version**: 2025.07 (build 197242)
**Database**: Supabase PostgreSQL 17.6
**Project**: ToolBoxAI Solutions

---

## 📋 Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Server Issues](#server-issues)
3. [Database Issues](#database-issues)
4. [Build Agent Issues](#build-agent-issues)
5. [Build Failures](#build-failures)
6. [VCS/Git Issues](#vcsgit-issues)
7. [Docker Registry Issues](#docker-registry-issues)
8. [Build Cache Issues](#build-cache-issues)
9. [Performance Issues](#performance-issues)
10. [Log Analysis](#log-analysis)

---

## 🚨 Quick Diagnostics

### Run Complete Health Check

```bash
# Navigate to project root
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Check all services
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml ps

# Check TeamCity server health
curl -I http://localhost:8111

# Check database connectivity
psql "postgresql://supabase_admin:postgres@localhost:54322/teamcity" -c "SELECT version();"

# Check agent status
docker logs teamcity-agent-frontend --tail 20
docker logs teamcity-agent-backend --tail 20
docker logs teamcity-agent-integration --tail 20

# Check disk space
df -h | grep -E "(Filesystem|G-DRIVE|/data)"

# Check network connectivity
docker network inspect teamcity-network
docker network inspect supabase_network_supabase
```

### Quick Status Summary

```bash
#!/bin/bash
echo "=== TeamCity Quick Status ==="
echo ""
echo "Server Status:"
docker ps --filter "name=teamcity-server" --format "  {{.Status}}"
echo ""
echo "Agent Status:"
docker ps --filter "name=teamcity-agent" --format "  {{.Names}}: {{.Status}}"
echo ""
echo "Database:"
psql "postgresql://supabase_admin:postgres@localhost:54322/teamcity" -t -c "SELECT COUNT(*) || ' tables' FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "  ❌ Not accessible"
echo ""
echo "Web UI:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8111/)
echo "  HTTP $HTTP_CODE"
```

---

## 🖥️ Server Issues

### Issue: TeamCity Server Won't Start

**Symptoms:**
- Container exits immediately after starting
- Status shows "Exited (1)" or similar
- Web UI inaccessible at http://localhost:8111

**Diagnosis:**
```bash
# Check container status
docker ps -a --filter "name=teamcity-server"

# View full logs
docker logs teamcity-server --tail 100

# Check for permission errors
docker logs teamcity-server 2>&1 | grep -i "permission denied"

# Check for port conflicts
lsof -i :8111
```

**Common Causes & Solutions:**

#### Cause 1: Permission Denied on Data Directory

**Error Message:**
```
ERROR: Could not create a file in directory "/data/teamcity_server/datadir/config"
Reason: Permission denied
```

**Solution:**
```bash
# Fix volume permissions (TeamCity runs as UID 1000)
docker run --rm \
  -v compose_teamcity_data:/data \
  alpine sh -c "chown -R 1000:1000 /data && chmod -R 755 /data"

docker run --rm \
  -v compose_teamcity_logs:/logs \
  alpine sh -c "chown -R 1000:1000 /logs && chmod -R 755 /logs"

docker run --rm \
  -v compose_teamcity_cache:/cache \
  alpine sh -c "chown -R 1000:1000 /cache && chmod -R 755 /cache"

# Restart TeamCity
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart teamcity-server
```

#### Cause 2: Port 8111 Already in Use

**Solution:**
```bash
# Find process using port 8111
lsof -ti:8111

# Kill process (replace PID)
kill -9 <PID>

# Or change TeamCity port in docker-compose.teamcity.yml
# ports:
#   - "8112:8111"  # Change host port
```

#### Cause 3: Insufficient Memory

**Error Message:**
```
java.lang.OutOfMemoryError: Java heap space
```

**Solution:**
```bash
# Increase server memory in docker-compose.teamcity.yml
environment:
  TEAMCITY_SERVER_MEM_OPTS: "-Xmx8g -XX:MaxPermSize=512m -XX:ReservedCodeCacheSize=640m"
  # Increased from 6g to 8g

# Restart
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart teamcity-server
```

### Issue: Server Stuck in Initialization

**Symptoms:**
- Web UI shows "TeamCity is starting..."
- Initialization takes longer than 5 minutes
- No errors in logs

**Diagnosis:**
```bash
# Monitor initialization progress
docker logs teamcity-server --follow | grep -E "(Initialization|Started|ERROR)"

# Check database schema creation
psql "postgresql://supabase_admin:postgres@localhost:54322/teamcity" \
  -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
```

**Solution:**
```bash
# First build takes 2-3 minutes for schema creation (~152 tables)
# If stuck > 5 minutes:

# 1. Check database connectivity
docker exec teamcity-server nc -zv db.supabase.internal 5432

# 2. Check for locks
psql "postgresql://supabase_admin:postgres@localhost:54322/teamcity" \
  -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# 3. Restart if necessary
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart teamcity-server
```

### Issue: Server Responds with HTTP 503

**Symptoms:**
- Web UI shows "Service Unavailable"
- `curl http://localhost:8111` returns 503

**Diagnosis:**
```bash
# Check if server is fully initialized
docker logs teamcity-server 2>&1 | grep "Server started"

# Check memory usage
docker stats teamcity-server --no-stream
```

**Solution:**
```bash
# Server still initializing - wait for "Server started" message
docker logs teamcity-server --follow | grep "Server started"

# If memory maxed out, increase limits in docker-compose.teamcity.yml
```

---

## 🗄️ Database Issues

### Issue: Database Connection Failed

**Symptoms:**
```
ERROR: Can't connect to database: Connection refused
ERROR: Could not create connection to database server
```

**Diagnosis:**
```bash
# Test database from host
psql "postgresql://supabase_admin:postgres@localhost:54322/teamcity" -c "SELECT 1;"

# Test database from container
docker exec teamcity-server nc -zv db.supabase.internal 5432

# Check Supabase is running
docker ps | grep supabase_db

# Verify TeamCity is on correct network
docker inspect teamcity-server | jq '.[0].NetworkSettings.Networks'
```

**Solutions:**

#### Solution 1: Supabase Not Running

```bash
# Start Supabase
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
npx supabase start

# Wait for PostgreSQL to be ready
docker logs supabase_db_supabase --tail 20 | grep "ready to accept connections"

# Restart TeamCity
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart teamcity-server
```

#### Solution 2: Network Misconfiguration

```bash
# Verify external network exists
docker network ls | grep supabase_network_supabase

# Reconnect TeamCity to network
docker network connect supabase_network_supabase teamcity-server

# Verify connectivity
docker exec teamcity-server ping -c 2 db.supabase.internal
```

#### Solution 3: Wrong Credentials

```bash
# Verify database.properties inside container
docker exec teamcity-server cat /data/teamcity_server/datadir/config/database.properties

# Should contain:
# connectionUrl=jdbc:postgresql://db.supabase.internal:5432/teamcity
# connectionProperties.user=supabase_admin
# connectionProperties.password=postgres

# If incorrect, update and restart
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart teamcity-server
```

### Issue: JDBC Driver Not Found

**Error Message:**
```
ERROR: JDBC driver for PostgreSQL not found
ERROR: Can't download JDBC driver as `/data/teamcity_server/datadir/lib/jdbc` not writable
```

**Solution:**
```bash
# Download PostgreSQL JDBC driver
curl -L -o /tmp/postgresql-42.7.4.jar \
  https://jdbc.postgresql.org/download/postgresql-42.7.4.jar

# Copy to TeamCity container
docker cp /tmp/postgresql-42.7.4.jar \
  teamcity-server:/data/teamcity_server/datadir/lib/jdbc/

# Verify
docker exec teamcity-server ls -lh /data/teamcity_server/datadir/lib/jdbc/

# Restart
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart teamcity-server
```

### Issue: Database Migration Failed

**Error Message:**
```
ERROR: Data format version mismatch
ERROR: The database schema version is newer than the TeamCity version
```

**Solution:**
```bash
# Option 1: Fresh database (if no important data)
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml down
docker volume rm compose_teamcity_data

# Drop and recreate database
psql "postgresql://supabase_admin:postgres@localhost:54322/postgres" \
  -c "DROP DATABASE IF EXISTS teamcity;" \
  -c "CREATE DATABASE teamcity OWNER supabase_admin;"

# Restart for fresh initialization
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml up -d

# Option 2: Backup and restore (if data needed)
# Export from TeamCity UI: Administration → Backup
# Then restore after database reset
```

---

## 🤖 Build Agent Issues

### Issue: Agents Not Appearing

**Symptoms:**
- No agents visible in UI under "Agents → Unauthorized"
- Agents not connecting to server

**Diagnosis:**
```bash
# Check agent containers are running
docker ps --filter "name=teamcity-agent"

# Check agent logs
docker logs teamcity-agent-frontend --tail 50
docker logs teamcity-agent-backend --tail 50
docker logs teamcity-agent-integration --tail 50

# Look for connection errors
docker logs teamcity-agent-frontend 2>&1 | grep -i "error\|connection\|failed"
```

**Common Causes & Solutions:**

#### Cause 1: Server URL Misconfigured

**Error in Logs:**
```
ERROR: Can't connect to server at http://teamcity-server:8111
Connection refused
```

**Solution:**
```bash
# Verify SERVER_URL environment variable
docker exec teamcity-agent-frontend env | grep SERVER_URL

# Should be: SERVER_URL=http://teamcity-server:8111

# If incorrect, update docker-compose.teamcity.yml and restart
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart \
  teamcity-agent-frontend teamcity-agent-backend teamcity-agent-integration
```

#### Cause 2: Network Isolation

**Solution:**
```bash
# Verify agents are on teamcity-network
docker network inspect teamcity-network | jq '.[0].Containers' | grep agent

# Reconnect if needed
docker network connect teamcity-network teamcity-agent-frontend
docker network connect teamcity-network teamcity-agent-backend
docker network connect teamcity-network teamcity-agent-integration
```

#### Cause 3: Server Not Fully Initialized

**Solution:**
```bash
# Wait for server to complete initialization
docker logs teamcity-server --follow | grep "Server started"

# Once started, restart agents
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart \
  teamcity-agent-frontend teamcity-agent-backend teamcity-agent-integration
```

### Issue: Agent Shows as Disconnected

**Symptoms:**
- Agent was connected, now shows "Disconnected" in UI
- Agent container is still running

**Diagnosis:**
```bash
# Check agent health
docker logs teamcity-agent-frontend --tail 30 | grep -i "disconnect\|error"

# Check network connectivity
docker exec teamcity-agent-frontend curl -I http://teamcity-server:8111

# Check memory usage
docker stats teamcity-agent-frontend --no-stream
```

**Solutions:**

#### Solution 1: Network Interruption

```bash
# Restart affected agent
docker restart teamcity-agent-frontend

# Monitor reconnection
docker logs teamcity-agent-frontend --follow | grep "Connected to TeamCity server"
```

#### Solution 2: Memory Exhaustion

```bash
# Check if agent hit memory limit
docker stats teamcity-agent-frontend --no-stream | grep -E "MEM|agent"

# Increase limit in docker-compose.teamcity.yml if needed
deploy:
  resources:
    limits:
      memory: 6G  # Increase from 4G
    reservations:
      memory: 3G  # Increase from 2G

# Restart
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml up -d --force-recreate teamcity-agent-frontend
```

### Issue: Agent Incompatible with Build Configuration

**Symptoms:**
- Build stays in queue
- Message: "No compatible agents"

**Diagnosis:**
```bash
# Check agent compatibility from UI
# Navigate to: Agents → [Agent Name] → Compatible Configurations

# Check agent requirements in build configuration
# Navigate to: Build Configuration → Agent Requirements
```

**Solution:**
```bash
# Option 1: Install missing tools on agent
docker exec teamcity-agent-frontend apt-get update && apt-get install -y <package>

# Option 2: Adjust agent requirements in .teamcity/settings.kts
requirements {
    // Make requirement optional or remove if not critical
    // contains("system.agent.name", "Frontend", RunnersProvider.RQ_CONTAINS_OPTIONAL)
}

# Option 3: Add capability to agent
# Administration → Agents → [Agent] → Parameters
# Add: system.custom.capability = value
```

---

## 🔨 Build Failures

### Issue: Build Fails at Checkout

**Error Message:**
```
ERROR: Failed to clone repository
ERROR: Authentication failed for 'https://github.com/...'
```

**Diagnosis:**
```bash
# Test VCS root connection from UI
# Administration → VCS Roots → MainRepository → Test Connection

# Check GitHub token is valid
curl -H "Authorization: token ${GITHUB_PAT_TOKEN}" https://api.github.com/user
```

**Solutions:**

#### Solution 1: Invalid GitHub Token

```bash
# Generate new GitHub PAT with required scopes:
# - repo (full repository access)
# - workflow (workflow permissions)
# - read:packages (if using GitHub Packages)

# Update in TeamCity:
# Administration → Root Project → Parameters
# Edit: credentialsJSON:github-token
# Value: <new token>

# Retry build
```

#### Solution 2: VCS Root Misconfigured

```bash
# Verify VCS root in .teamcity/settings.kts
object MainRepository : GitVcsRoot({
    name = "ToolBoxAI Main Repository"
    url = "https://github.com/GrayGhostDev/ToolboxAI-Solutions.git"  # Correct URL?
    branch = "refs/heads/main"  # Correct branch?
    authMethod = password {
        userName = "%env.GITHUB_USERNAME%"
        password = "credentialsJSON:github-token"
    }
})

# Apply changes and retry
```

### Issue: Build Fails at Dependency Installation

**Error Message:**
```
ERROR: npm install failed with exit code 1
ERROR: Failed to install package xyz
```

**Diagnosis:**
```bash
# Check build logs for specific error
# Build → [Build Number] → Build Log

# Common errors:
# - Network timeout
# - Missing authentication for private packages
# - Incompatible Node/npm version
```

**Solutions:**

#### Solution 1: Network Timeout

```bash
# Increase npm timeout in build step
npm config set fetch-timeout 600000
npm install --verbose

# Or add to .teamcity/settings.kts
script {
    content = """
        npm config set fetch-timeout 600000
        npm install
    """.trimIndent()
}
```

#### Solution 2: Private Package Authentication

```bash
# Add .npmrc to project parameters
# Administration → Root Project → Parameters
# Add: env.NPM_TOKEN (password type)

# In build step, create .npmrc
script {
    content = """
        echo "//registry.npmjs.org/:_authToken=%env.NPM_TOKEN%" > .npmrc
        npm install
        rm .npmrc
    """.trimIndent()
}
```

#### Solution 3: Node Version Mismatch

```bash
# Verify Node version on agent
docker exec teamcity-agent-frontend node --version

# Update agent Node version
docker exec teamcity-agent-frontend bash -c "
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y nodejs
"

# Or use nvm in build step
script {
    content = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm install 22
        nvm use 22
        npm install
    """.trimIndent()
}
```

### Issue: Build Fails at Docker Image Build

**Error Message:**
```
ERROR: Cannot connect to the Docker daemon
ERROR: Error response from daemon: unauthorized
```

**Diagnosis:**
```bash
# Check Docker-in-Docker is working
docker exec teamcity-agent-frontend docker ps

# Check Docker registry credentials
# Administration → Root Project → Docker Registry
```

**Solutions:**

#### Solution 1: Docker Daemon Not Running

```bash
# Verify Docker-in-Docker service
docker exec teamcity-agent-frontend dockerd --version

# Check privileged mode enabled in docker-compose.teamcity.yml
privileged: true  # Required for Docker-in-Docker

# Restart agent if needed
docker restart teamcity-agent-frontend
```

#### Solution 2: Registry Authentication Failed

```bash
# Test Docker login from agent
docker exec teamcity-agent-frontend docker login \
  https://build-cloud.docker.com:443 \
  -u thegrayghost23 \
  -p <password>

# Update credentials in TeamCity:
# Administration → Root Project → Docker Registry
# Name: TeamCity Cloud Registry
# Username: thegrayghost23
# Password: credentialsJSON:teamcity-cloud-docker

# Save and retry build
```

### Issue: Tests Fail with Timeout

**Error Message:**
```
ERROR: Test execution timed out after 900 seconds
```

**Solution:**
```bash
# Increase test timeout in .teamcity/settings.kts
failureConditions {
    executionTimeoutMin = 30  # Increase from 15 to 30 minutes
}

# Or in test command
script {
    content = """
        pytest --timeout=1800  # 30 minutes per test
    """.trimIndent()
}
```

---

## 🔗 VCS/Git Issues

### Issue: VCS Root Connection Test Fails

**Error Message:**
```
ERROR: Failed to connect to repository
ERROR: Couldn't verify git host key
```

**Solutions:**

#### Solution 1: SSH Host Key Verification

```bash
# For GitHub, add known_hosts entry
docker exec teamcity-server bash -c "
  mkdir -p ~/.ssh
  ssh-keyscan github.com >> ~/.ssh/known_hosts
"

# Or disable strict checking (less secure)
# In VCS root configuration:
# Custom configuration parameters:
#   teamcity.git.sshHostKeyVerificationStrategy = accept_any
```

#### Solution 2: GitHub Rate Limiting

```bash
# Check rate limit status
curl -H "Authorization: token ${GITHUB_PAT_TOKEN}" https://api.github.com/rate_limit

# Wait for reset or use authenticated requests
# Ensure GitHub token is configured in VCS root
```

### Issue: Branch Not Detected

**Symptoms:**
- Build doesn't trigger on commit to branch
- Branch not visible in "Run custom build" dialog

**Solution:**
```bash
# Update branch specification in VCS root
branchSpec = """
    +:refs/heads/*        # All branches
    +:refs/tags/*         # All tags
    +:refs/pull/*/merge   # All pull requests
""".trimIndent()

# Or specify explicit branches
branchSpec = """
    +:refs/heads/main
    +:refs/heads/develop
    +:refs/heads/feature/*
""".trimIndent()
```

---

## 🐳 Docker Registry Issues

### Issue: Push to Registry Fails

**Error Message:**
```
ERROR: denied: requested access to the resource is denied
ERROR: unauthorized: authentication required
```

**Solution:**
```bash
# 1. Verify credentials
# Administration → Root Project → Docker Registry
# Test Connection

# 2. Check token/password hasn't expired
# Generate new Docker access token if needed

# 3. Update parameter
# credentialsJSON:teamcity-cloud-docker = <new token>

# 4. For Docker Hub, verify repository exists
# Repository format: thegrayghost23/toolboxai-dashboard

# 5. Retry build
```

### Issue: Image Pull Fails

**Error Message:**
```
ERROR: pull access denied for image:tag
ERROR: manifest unknown
```

**Solution:**
```bash
# 1. Verify image name and tag are correct
# In Dockerfile or build step

# 2. For private images, ensure registry credentials configured
# Add Docker Registry connection in TeamCity

# 3. Try pulling manually from agent
docker exec teamcity-agent-frontend docker pull <image:tag>

# 4. If public image, check rate limiting
# https://docs.docker.com/docker-hub/download-rate-limit/
```

---

## 💾 Build Cache Issues

### Issue: Build Cache Not Working

**Symptoms:**
- All builds re-download dependencies
- Cache hit rate = 0%
- Build times not improving

**Diagnosis:**
```bash
# Check Build Cache is enabled
# Administration → Build Features → Build Cache
# Status should show "Enabled"

# Check cache directory exists
ls -lh /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/TeamCity/cache

# Check cache rules in .teamcity/settings.kts
grep -A10 "BuildCache" .teamcity/settings.kts

# Monitor cache usage in build logs
# Build → [Build Number] → Build Log
# Search for "cache"
```

**Solutions:**

#### Solution 1: Cache Directory Not Writable

```bash
# Fix permissions
chmod -R 755 /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/TeamCity/cache
chown -R 1000:1000 /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/TeamCity/cache

# Verify volume mount in docker-compose.teamcity.yml
volumes:
  - /Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/TeamCity/cache:/data/teamcity_server/system/caches/build_cache
```

#### Solution 2: Cache Rules Incorrect

```bash
# Verify cache rules match your dependencies
# In .teamcity/settings.kts

feature {
    type = "BuildCache"
    param("rules", """
        # Frontend (Node.js)
        +:**/node_modules/** => directory
        +:**/.npm/** => directory
        +:**/dist/** => directory

        # Backend (Python)
        +:**/.venv/** => directory
        +:**/__pycache__/** => directory
        +:**/.pytest_cache/** => directory
        +:**/.ruff_cache/** => directory

        # Docker
        +:**/.docker/** => directory
    """.trimIndent())
}
```

#### Solution 3: First Build Hasn't Completed

**Note:** Cache is only available **after** first build completes successfully.

```bash
# Run a complete build first
# Subsequent builds will use cache

# Verify cache published in build log
# Look for: "Published build cache: X MB"
```

### Issue: Cache Size Exceeded

**Error Message:**
```
WARNING: Build cache size exceeded limit (10GB)
INFO: Cleaning oldest cache entries
```

**Solution:**
```bash
# Increase cache size limit in .teamcity/settings.kts
feature {
    type = "BuildCache"
    param("publish.max.size", "20GB")  # Increase from 10GB
}

# Or clean cache manually
# Administration → Build Cache → Clean

# Or adjust cache rules to be more selective
```

---

## ⚡ Performance Issues

### Issue: Builds Taking Too Long

**Diagnosis:**
```bash
# Compare build times
# Projects → ToolBoxAI Solutions → Build History
# Look for trends and outliers

# Check agent resource usage during build
docker stats teamcity-agent-frontend --no-stream

# Identify slow steps
# Build → [Build Number] → Build Log
# Check step execution times
```

**Optimization Strategies:**

#### Strategy 1: Enable Parallel Tests

```kotlin
// In .teamcity/settings.kts
object DashboardBuild : BuildType({
    // ...existing config

    features {
        feature {
            type = "parallelTests"
            param("numberOfBatches", "3")  // Run tests in 3 parallel batches
        }
    }
})
```

**Note:** First build gathers test statistics, subsequent builds parallelized automatically.

#### Strategy 2: Optimize Docker Builds

```dockerfile
# Use multi-stage builds
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:22-alpine
COPY --from=builder /app/node_modules ./node_modules
COPY . .

# Use BuildKit
# In build step:
script {
    content = """
        export DOCKER_BUILDKIT=1
        docker build -t image:tag .
    """.trimIndent()
}
```

#### Strategy 3: Add Checkout Rules

```kotlin
// Exclude unnecessary files from checkout
vcs {
    root(MainRepository)
    checkoutMode = CheckoutMode.ON_AGENT

    checkoutRules = """
        -:.teamcity => .
        -:.github => .
        -:docs => .
        -:**/*.md => .
        -:*.md => .
    """.trimIndent()
}
```

#### Strategy 4: Use Artifact Dependencies

```kotlin
// Instead of rebuilding dependencies
dependencies {
    artifacts(BackendBuild) {
        artifactRules = ".venv/** => ."
        cleanDestination = false
    }
}
```

### Issue: Server Running Slow

**Diagnosis:**
```bash
# Check server memory usage
docker stats teamcity-server --no-stream

# Check database performance
psql "postgresql://supabase_admin:postgres@localhost:54322/teamcity" -c "
    SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    LIMIT 10;
"

# Check disk I/O
docker stats --no-stream
```

**Solutions:**

#### Solution 1: Increase Server Memory

```yaml
# In docker-compose.teamcity.yml
environment:
  TEAMCITY_SERVER_MEM_OPTS: "-Xmx8g -XX:MaxPermSize=512m"  # Increase from 6g

deploy:
  resources:
    limits:
      memory: 10G  # Increase from 6G
    reservations:
      memory: 6G   # Increase from 4G
```

#### Solution 2: Database Maintenance

```sql
-- Run as supabase_admin
-- Vacuum and analyze tables
VACUUM ANALYZE;

-- Reindex
REINDEX DATABASE teamcity;

-- Update statistics
ANALYZE;
```

#### Solution 3: Clean Old Builds

```bash
# Administration → Clean-up Rules
# Set up automatic cleanup:
# - Keep builds for 30 days
# - Keep successful builds for 14 days
# - Keep artifacts for 7 days
```

---

## 📊 Log Analysis

### Finding Errors in Logs

```bash
# Server errors
docker logs teamcity-server 2>&1 | grep -i "error\|exception\|failed"

# Agent errors
docker logs teamcity-agent-frontend 2>&1 | grep -i "error\|exception\|failed"

# Database errors
docker logs teamcity-server 2>&1 | grep -i "sql\|database\|jdbc"

# Network errors
docker logs teamcity-server 2>&1 | grep -i "connection\|timeout\|refused"
```

### Understanding Common Log Messages

#### Normal Messages (Can Ignore)

```
INFO - Successfully connected to database
INFO - Server started
INFO - Agent registered successfully
INFO - Build started
INFO - Tests passed
INFO - Artifacts published
```

#### Warning Messages (Monitor)

```
WARN - Build cache size approaching limit
WARN - Agent disconnected, attempting reconnect
WARN - VCS root check failed, retrying
WARN - Test execution slow (> 300s)
```

#### Error Messages (Action Required)

```
ERROR - Database connection failed
ERROR - Permission denied
ERROR - Out of memory
ERROR - Authentication failed
ERROR - Build failed with exit code 1
```

### Log File Locations

```bash
# Server logs (container)
docker exec teamcity-server ls -lh /opt/teamcity/logs/

# Server logs (volume)
docker run --rm -v compose_teamcity_logs:/logs alpine ls -lh /logs/

# Agent logs (container)
docker exec teamcity-agent-frontend ls -lh /opt/buildagent/logs/

# Build logs (UI only)
# Build → [Build Number] → Build Log
```

### Export Logs for Analysis

```bash
# Export last 1000 lines of server logs
docker logs teamcity-server --tail 1000 > teamcity-server-$(date +%Y%m%d).log

# Export agent logs
docker logs teamcity-agent-frontend --tail 1000 > agent-frontend-$(date +%Y%m%d).log
docker logs teamcity-agent-backend --tail 1000 > agent-backend-$(date +%Y%m%d).log
docker logs teamcity-agent-integration --tail 1000 > agent-integration-$(date +%Y%m%d).log

# Compress for sharing
tar -czf teamcity-logs-$(date +%Y%m%d).tar.gz *.log
```

---

## 🔍 Advanced Diagnostics

### Complete System Health Check

```bash
#!/bin/bash
# Save as: teamcity_health_check.sh

echo "=== TeamCity Health Check ==="
echo "Date: $(date)"
echo ""

echo "1. Docker Services:"
docker ps --filter "name=teamcity" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "2. Server Health:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8111/)
echo "  Web UI: HTTP $HTTP_CODE"
echo ""

echo "3. Database:"
DB_TABLES=$(psql "postgresql://supabase_admin:postgres@localhost:54322/teamcity" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null)
echo "  Tables: ${DB_TABLES:-ERROR}"
echo ""

echo "4. Agents:"
docker exec teamcity-agent-frontend curl -s http://teamcity-server:8111 > /dev/null && echo "  Frontend: Connected" || echo "  Frontend: Disconnected"
docker exec teamcity-agent-backend curl -s http://teamcity-server:8111 > /dev/null && echo "  Backend: Connected" || echo "  Backend: Disconnected"
docker exec teamcity-agent-integration curl -s http://teamcity-server:8111 > /dev/null && echo "  Integration: Connected" || echo "  Integration: Disconnected"
echo ""

echo "5. Resources:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep teamcity
echo ""

echo "6. Disk Space:"
df -h | grep -E "(Filesystem|G-DRIVE)" | head -2
echo ""

echo "7. Recent Errors:"
docker logs teamcity-server --tail 50 2>&1 | grep -i error | tail -5
echo ""

echo "=== Health Check Complete ==="
```

### Network Diagnostics

```bash
# Test all network connections
docker network inspect teamcity-network | jq '.[0].Containers'
docker network inspect supabase_network_supabase | jq '.[0].Containers | select(.Name | contains("teamcity"))'

# Test DNS resolution
docker exec teamcity-server nslookup db.supabase.internal
docker exec teamcity-agent-frontend nslookup teamcity-server

# Test connectivity
docker exec teamcity-server nc -zv db.supabase.internal 5432
docker exec teamcity-agent-frontend nc -zv teamcity-server 8111
```

---

## 📞 Getting Help

### Information to Collect

When seeking help, collect:

1. **Version Information**:
   ```bash
   docker exec teamcity-server cat /opt/teamcity/BUILD_NUMBER
   ```

2. **System Information**:
   ```bash
   docker info
   df -h
   docker stats --no-stream
   ```

3. **Configuration**:
   ```bash
   docker exec teamcity-server cat /data/teamcity_server/datadir/config/database.properties
   ```

4. **Logs** (last 100 lines):
   ```bash
   docker logs teamcity-server --tail 100 > server.log
   docker logs teamcity-agent-frontend --tail 100 > agent.log
   ```

5. **Build Configuration** (if build-related):
   - Build logs from UI
   - Build configuration from .teamcity/settings.kts
   - Agent compatibility information

### Support Resources

- **TeamCity Documentation**: http://localhost:8111/help/teamcity-documentation.html
- **Kotlin DSL Reference**: http://localhost:8111/app/dsl-documentation/
- **JetBrains Community**: https://teamcity-support.jetbrains.com/
- **Project Documentation**: `docs/08-operations/ci-cd/`

---

**Troubleshooting Guide Version**: 1.0.0
**Last Updated**: 2025-11-08
**Prepared By**: Claude Code Automation
