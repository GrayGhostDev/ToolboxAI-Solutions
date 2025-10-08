# ToolboxAI Services - Quick Start Guide

## Current Status: Services Not Running

**Issue:** Docker Desktop is not currently running on your system.

## Steps to Start All Services

### Step 1: Start Docker Desktop

**Option A - Using Command Line:**
```bash
open -a Docker
```

**Option B - Manual Start:**
1. Go to your **Applications** folder
2. Find and double-click **Docker.app**
3. Wait for Docker to fully start (you'll see a Docker whale icon in your menu bar)
4. The icon will stop animating when Docker is ready

**Important:** Docker can take 30-60 seconds to fully start up!

### Step 2: Verify Docker is Running

```bash
docker ps
```

If this shows a table (even if empty), Docker is ready!

### Step 3: Start All ToolboxAI Services

Run the comprehensive startup script:

```bash
cd /Users/grayghostdataconsultants/GrayGhostDataConsultants/Development/ActiveProjects/Development/Cursor/Customers/ToolboxAI-Solutions
./check-and-start.sh
```

**OR** manually:

```bash
cd /Users/grayghostdataconsultants/GrayGhostDataConsultants/Development/ActiveProjects/Development/Cursor/Customers/ToolboxAI-Solutions
docker-compose -f docker-compose.complete.yml up -d
```

## Verify Services are Running

After starting, check status:

```bash
docker-compose -f docker-compose.complete.yml ps
```

You should see these services running:
- ✅ toolboxai-postgres (PostgreSQL 16)
- ✅ toolboxai-redis
- ✅ toolboxai-backend
- ✅ toolboxai-dashboard
- ✅ toolboxai-mcp
- ✅ toolboxai-coordinator
- ✅ toolboxai-nginx
- ✅ toolboxai-prometheus
- ✅ toolboxai-grafana
- ✅ toolboxai-vault

## Access Your Services

Once running, access at:

- **Dashboard:** http://localhost:5179
- **Backend API:** http://localhost:8009
- **API Documentation:** http://localhost:8009/docs
- **Grafana Monitoring:** http://localhost:3001 (admin/admin)
- **Prometheus:** http://localhost:9090

## Common Issues & Solutions

### Issue: "Cannot connect to Docker daemon"
**Solution:** Docker Desktop isn't running. Start it using step 1 above.

### Issue: Port already in use (e.g., 5432)
**Solution:** 
```bash
# Check what's using the port
lsof -i :5432

# If it's a local PostgreSQL, stop it
brew services stop postgresql
```

### Issue: Services show "starting" but never become healthy
**Solution:**
```bash
# Check logs for specific service
docker-compose -f docker-compose.complete.yml logs postgres
docker-compose -f docker-compose.complete.yml logs backend

# Restart services
docker-compose -f docker-compose.complete.yml restart
```

### Issue: "No space left on device"
**Solution:**
```bash
# Clean up Docker resources
docker system prune -a
docker volume prune
```

## Useful Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.complete.yml logs -f

# Specific service
docker-compose -f docker-compose.complete.yml logs -f postgres
docker-compose -f docker-compose.complete.yml logs -f backend
```

### Restart Services
```bash
# All services
docker-compose -f docker-compose.complete.yml restart

# Specific service
docker-compose -f docker-compose.complete.yml restart postgres
```

### Stop Services
```bash
# Stop but keep data
docker-compose -f docker-compose.complete.yml down

# Stop and remove all data
docker-compose -f docker-compose.complete.yml down -v
```

### Check Service Health
```bash
# PostgreSQL
docker-compose -f docker-compose.complete.yml exec postgres psql -U eduplatform -d educational_platform_dev -c "SELECT version();"

# Redis
docker-compose -f docker-compose.complete.yml exec redis redis-cli ping

# Backend API
curl http://localhost:8009/health
```

## Scripts Available

1. **check-and-start.sh** - Comprehensive startup with health checks
2. **start-all-services.sh** - Automatic Docker wait and startup
3. **start-services.sh** - Basic service startup

## PostgreSQL 16 Configuration

The database is now running **PostgreSQL 16** with:
- **User:** eduplatform
- **Password:** eduplatform2024
- **Database:** educational_platform_dev
- **Port:** 5432 (exposed to host)

Extensions installed:
- uuid-ossp
- pgcrypto
- pg_trgm

## What to Do Right Now

1. **Open Docker Desktop** - Look for it in Applications or use: `open -a Docker`
2. **Wait for Docker icon** to appear in your menu bar (and stop animating)
3. **Run the startup script:** `./check-and-start.sh`
4. **Open browser** to http://localhost:5179

That's it! Your services will be running.

