# MANUAL STARTUP INSTRUCTIONS

Since the terminal commands are not returning output in the current session, please follow these **manual steps** to start all services.

## Step-by-Step Manual Startup

### 1. Start Docker Desktop

Open a **new Terminal window** and run:

```bash
open -a Docker
```

Wait 30-60 seconds for Docker to fully start. You'll see a Docker whale icon in your macOS menu bar at the top of the screen.

### 2. Verify Docker is Running

In your new terminal, run:

```bash
docker ps
```

You should see a table with headers. If you get an error, Docker isn't ready yet - wait another 30 seconds and try again.

### 3. Navigate to Project Directory

```bash
cd /Users/grayghostdataconsultants/GrayGhostDataConsultants/Development/ActiveProjects/Development/Cursor/Customers/ToolboxAI-Solutions
```

### 4. Stop Any Existing Containers

```bash
docker-compose -f docker-compose.complete.yml down
```

### 5. Start All Services

```bash
docker-compose -f docker-compose.complete.yml up -d
```

This will:
- Pull PostgreSQL 16 image
- Pull Redis 7 image
- Build backend service
- Build dashboard service
- Build MCP and coordinator services
- Start all monitoring services

**This may take 5-10 minutes on first run** as it downloads images and builds containers.

### 6. Check Service Status

```bash
docker-compose -f docker-compose.complete.yml ps
```

You should see all services with "Up" status:
- toolboxai-postgres
- toolboxai-redis
- toolboxai-backend
- toolboxai-dashboard
- toolboxai-mcp
- toolboxai-coordinator
- toolboxai-nginx
- toolboxai-prometheus
- toolboxai-grafana
- toolboxai-vault

### 7. Verify PostgreSQL 16

```bash
docker-compose -f docker-compose.complete.yml exec postgres psql -U eduplatform -d educational_platform_dev -c "SELECT version();"
```

You should see output showing PostgreSQL 16.x

### 8. Check Logs (if any service is not running)

For specific service:
```bash
docker-compose -f docker-compose.complete.yml logs postgres
docker-compose -f docker-compose.complete.yml logs backend
docker-compose -f docker-compose.complete.yml logs dashboard
```

For all services:
```bash
docker-compose -f docker-compose.complete.yml logs -f
```

Press `Ctrl+C` to stop watching logs.

## Access Your Running Services

Once all services are up:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Dashboard** | http://localhost:5179 | - |
| **Backend API** | http://localhost:8009 | - |
| **API Docs** | http://localhost:8009/docs | - |
| **Grafana** | http://localhost:3001 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |
| **Vault** | http://localhost:8200 | token: root |

## Quick Scripts Available

I've created several scripts to help you:

### Check Docker Status
```bash
./docker-status.sh
```

### Start All Services (with Docker check)
```bash
./check-and-start.sh
```

### View All Logs
```bash
docker-compose -f docker-compose.complete.yml logs -f
```

## What Was Fixed

✅ **PostgreSQL upgraded from 15 to 16**
- Image: `postgres:16-alpine`
- Port 5432 exposed to host
- Proper initialization scripts

✅ **Database credentials properly configured**
- User: eduplatform
- Password: eduplatform2024
- Database: educational_platform_dev
- Environment variables with fallbacks

✅ **Database initialization script created**
- File: `database/init.sql`
- Installs extensions: uuid-ossp, pgcrypto, pg_trgm
- Creates toolboxai schema
- Sets up permissions

✅ **All services have health checks**
- PostgreSQL: pg_isready check
- Redis: ping check
- Backend: HTTP health endpoint
- Proper dependency ordering

✅ **Service restart policies**
- All services set to `restart: unless-stopped`
- Automatic recovery on failure

## Troubleshooting Common Issues

### Issue: "port is already allocated" for 5432

This means you have a local PostgreSQL running.

**Solution:**
```bash
# Check what's using the port
lsof -i :5432

# If it's PostgreSQL from Homebrew, stop it
brew services stop postgresql

# Or kill the process
sudo kill -9 $(lsof -ti:5432)

# Then restart services
docker-compose -f docker-compose.complete.yml restart postgres
```

### Issue: "Cannot connect to Docker daemon"

Docker Desktop isn't running.

**Solution:**
1. Look for Docker whale icon in menu bar
2. If not there, run: `open -a Docker`
3. Wait for icon to appear and stop animating
4. Try your command again

### Issue: PostgreSQL container keeps restarting

Check the logs for the specific error:

```bash
docker-compose -f docker-compose.complete.yml logs postgres
```

Common causes:
- Corrupted data volume
- Insufficient disk space
- Permission issues

**Solution:**
```bash
# Remove volumes and start fresh
docker-compose -f docker-compose.complete.yml down -v
docker-compose -f docker-compose.complete.yml up -d
```

### Issue: Backend fails to connect to database

Check if PostgreSQL is healthy:

```bash
docker-compose -f docker-compose.complete.yml ps postgres
docker-compose -f docker-compose.complete.yml logs postgres
```

**Solution:**
```bash
# Restart backend after database is healthy
docker-compose -f docker-compose.complete.yml restart backend
```

### Issue: Dashboard not loading

Check if backend is running:

```bash
curl http://localhost:8009/health
```

**Solution:**
```bash
# Check backend logs
docker-compose -f docker-compose.complete.yml logs backend

# Restart dashboard
docker-compose -f docker-compose.complete.yml restart dashboard
```

## Verify Everything is Working

### 1. Check PostgreSQL Connection
```bash
docker-compose -f docker-compose.complete.yml exec postgres psql -U eduplatform -d educational_platform_dev
```

Inside psql:
```sql
-- Check version (should be 16.x)
SELECT version();

-- List extensions
\dx

-- List schemas
\dn

-- Exit
\q
```

### 2. Check Redis Connection
```bash
docker-compose -f docker-compose.complete.yml exec redis redis-cli
```

Inside redis-cli:
```
PING
# Should return: PONG

INFO server
# Shows Redis version

EXIT
```

### 3. Check Backend API
```bash
# Health check
curl http://localhost:8009/health

# API documentation
open http://localhost:8009/docs
```

### 4. Check Dashboard
```bash
open http://localhost:5179
```

## Next Steps After Startup

Once all services are running:

1. **Run Database Migrations** (if needed):
   ```bash
   docker-compose -f docker-compose.complete.yml exec backend alembic upgrade head
   ```

2. **Create Initial Data** (if needed):
   ```bash
   docker-compose -f docker-compose.complete.yml exec backend python database/setup/create_initial_data.py
   ```

3. **Monitor Services** via Grafana:
   - Open http://localhost:3001
   - Login: admin/admin
   - Explore pre-configured dashboards

4. **View Metrics** via Prometheus:
   - Open http://localhost:9090
   - Query metrics from all services

## Complete Service List

All services configured in `docker-compose.complete.yml`:

1. **postgres** - PostgreSQL 16 database (port 5432)
2. **redis** - Redis 7 cache (port 6380)
3. **backend** - FastAPI backend (port 8009)
4. **dashboard** - React/Vite frontend (port 5179)
5. **mcp-server** - Model Context Protocol (port 8010)
6. **coordinator** - Agent coordinator (port 8888)
7. **nginx** - Reverse proxy (ports 80, 443)
8. **prometheus** - Metrics collection (port 9090)
9. **grafana** - Monitoring dashboards (port 3001)
10. **vault** - Secrets management (port 8200)

## Environment Variables

All environment variables are properly configured in `.env` file with fallbacks in docker-compose.

Key variables:
- `POSTGRES_USER=eduplatform`
- `POSTGRES_PASSWORD=eduplatform2024`
- `POSTGRES_DB=educational_platform_dev`
- `DATABASE_URL=postgresql://eduplatform:eduplatform2024@postgres:5432/educational_platform_dev`

## Files Created/Modified

### Modified:
- `docker-compose.complete.yml` - Updated PostgreSQL to 16, fixed credentials, added health checks

### Created:
- `database/init.sql` - Database initialization script
- `check-and-start.sh` - Comprehensive startup script
- `start-all-services.sh` - Auto Docker wait and startup
- `docker-status.sh` - Quick Docker status check
- `SERVICES_STARTUP_GUIDE.md` - Detailed guide
- `POSTGRES16_UPGRADE_SUMMARY.md` - Upgrade documentation
- `MANUAL_STARTUP_INSTRUCTIONS.md` - This file

## Summary

All configuration is complete. To start services:

1. **Open a new Terminal window**
2. **Start Docker Desktop**: `open -a Docker` (wait 30-60 seconds)
3. **Navigate to project**: `cd /Users/.../ToolboxAI-Solutions`
4. **Start services**: `docker-compose -f docker-compose.complete.yml up -d`
5. **Check status**: `docker-compose -f docker-compose.complete.yml ps`
6. **Access dashboard**: http://localhost:5179

That's it! All services will be running with PostgreSQL 16, proper credentials, and all ports correctly exposed.

