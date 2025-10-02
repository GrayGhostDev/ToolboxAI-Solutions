# Infrastructure Dashboard - Quick Start Guide

**Created:** October 1, 2025
**Time to Complete:** ~15 minutes
**Difficulty:** Intermediate

## Overview

This guide will help you quickly set up and access the Infrastructure Dashboard in your local development environment. For production deployment, see [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md).

## Prerequisites

✅ **Required:**
- Python 3.12+ installed
- PostgreSQL 15+ running
- Node.js 22+ installed
- Git repository cloned

✅ **Recommended:**
- Docker Desktop (alternative to local services)
- Redis 7+ running (optional, for caching)

## Quick Start (5 Steps)

### Step 1: Configure Environment (2 min)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your database credentials
nano .env
```

**Minimum required in .env:**
```bash
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/your_database
SECRET_KEY=generate_a_random_secret_key_here
JWT_SECRET_KEY=generate_a_longer_jwt_secret_at_least_64_characters
PUSHER_APP_ID=your_pusher_app_id
PUSHER_KEY=your_pusher_key
PUSHER_SECRET=your_pusher_secret
PUSHER_CLUSTER=your_cluster  # e.g., us2
```

**Generate secrets quickly:**
```bash
# Secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# JWT secret (save this output)
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Step 2: Database Setup (3 min)

**Option A: Using existing database**
```bash
# Run migration
cd database
alembic upgrade head

# Verify tables created
psql "$DATABASE_URL" -c "\dt *metrics* *infrastructure*"
```

**Option B: Fresh database**
```bash
# Create database
createdb toolboxai_dev

# Update .env with database name
DATABASE_URL=postgresql://user:pass@localhost:5432/toolboxai_dev

# Run migrations
cd database && alembic upgrade head
```

### Step 3: Start Backend (1 min)

```bash
# From project root
python3 -m uvicorn apps.backend.main:app --host 127.0.0.1 --port 8009 --reload

# You should see:
# INFO:     Uvicorn running on http://127.0.0.1:8009
# INFO:     Application startup complete
```

**Test backend:**
```bash
# In another terminal
curl http://127.0.0.1:8009/docs
# Should return Swagger UI HTML
```

### Step 4: Start Frontend (2 min)

```bash
# Navigate to dashboard
cd apps/dashboard

# Install dependencies (first time only)
npm install --no-bin-links  # Use if on external drive

# Start development server
npm run dev

# You should see:
# VITE v6.0.1  ready in X ms
# ➜  Local:   http://localhost:5179/
```

### Step 5: Access Dashboard (1 min)

1. **Open browser:** http://localhost:5179
2. **Login** with admin credentials (from .env: ADMIN_EMAIL/ADMIN_PASSWORD)
3. **Navigate** to Observability section
4. **Click** "Infrastructure" tab
5. **View** real-time metrics

**Expected Display:**
- Health Score (0-100) with ring progress indicator
- CPU, Memory, Disk, Network metric cards
- Process metrics (PID, CPU %, Memory %)
- Auto-refresh every 5 seconds
- Color-coded warnings/critical alerts

## Verification Steps

### ✅ Backend Verification

```bash
# Test infrastructure endpoints
curl http://127.0.0.1:8009/api/v1/observability/infrastructure/system | jq
curl http://127.0.0.1:8009/api/v1/observability/infrastructure/health | jq

# Expected output:
# {
#   "status": "success",
#   "data": { ... metrics ... }
# }
```

### ✅ Frontend Verification

Open browser console (F12) and check:
1. No red errors
2. Network tab shows successful API calls to localhost:8009
3. Pusher connection established (look for "Pusher connected")
4. Metrics updating every 5 seconds

### ✅ Database Verification

```bash
# Check tables exist
psql "$DATABASE_URL" -c "
SELECT table_name
FROM information_schema.tables
WHERE table_name LIKE '%metrics%' OR table_name LIKE '%infrastructure%';
"

# Expected tables:
# system_metrics_history
# process_metrics_history
# infrastructure_health
# infrastructure_alerts
# metric_aggregations
```

## Troubleshooting

### Issue: Backend won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

**Error:** `sqlalchemy.exc.OperationalError: could not translate host name`

**Solution:**
```bash
# Check DATABASE_URL in .env
echo $DATABASE_URL

# Test database connection
psql "$DATABASE_URL" -c "SELECT 1"

# If fails, update DATABASE_URL with correct credentials
```

### Issue: Frontend won't build

**Error:** `spawn Unknown system error -88` (on external drive)

**Solution:**
```bash
# Use Docker instead (recommended for external drives)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d dashboard-frontend

# OR convert vite config to JavaScript
mv vite.config.ts vite.config.js
# Then install with --no-bin-links
npm install --no-bin-links
```

---

**Error:** `Module not found: Can't resolve '@mantine/core'`

**Solution:**
```bash
# Install Mantine dependencies
npm install @mantine/core@8.3.2 @mantine/hooks@8.3.2
npm install @tabler/icons-react
```

### Issue: Dashboard shows no data

**Solution:**
```bash
# 1. Check backend is running
curl http://127.0.0.1:8009/api/v1/observability/infrastructure/report

# 2. Check VITE_API_BASE_URL in apps/dashboard/.env.local
echo "VITE_API_BASE_URL=http://127.0.0.1:8009" >> apps/dashboard/.env.local

# 3. Restart frontend
npm run dev

# 4. Clear browser cache and reload
```

### Issue: Pusher not connecting

**Solution:**
```bash
# Check Pusher credentials in .env
grep PUSHER .env

# Test Pusher connection
python3 << 'EOF'
import os
from pusher import Pusher

pusher = Pusher(
    app_id=os.getenv('PUSHER_APP_ID'),
    key=os.getenv('PUSHER_KEY'),
    secret=os.getenv('PUSHER_SECRET'),
    cluster=os.getenv('PUSHER_CLUSTER'),
    ssl=True
)

pusher.trigger('test-channel', 'test-event', {'message': 'hello'})
print("✅ Pusher connection successful")
EOF
```

## Docker Quick Start (Alternative)

If you prefer Docker:

```bash
# Start all services
docker compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.dev.yml up -d

# Check status
docker compose ps

# View logs
docker compose logs -f backend dashboard

# Access dashboard
open http://localhost:5179

# Stop all services
docker compose down
```

## Next Steps

### 🎯 Optional Enhancements

1. **Set up maintenance scripts:**
   ```bash
   # Test cleanup script
   python3 scripts/maintenance/cleanup_old_metrics.py --dry-run

   # Test alert script
   python3 scripts/maintenance/infrastructure_alerts.py
   ```

2. **Configure Slack alerts:**
   ```bash
   # Add to .env
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

   # Test alert
   python3 scripts/maintenance/infrastructure_alerts.py --slack-webhook "$SLACK_WEBHOOK_URL"
   ```

3. **Enable metric aggregations:**
   ```bash
   # Create hourly aggregations
   python3 scripts/maintenance/create_metric_aggregations.py --hours 24
   ```

### 📚 Additional Resources

- **Full Documentation:** [INFRASTRUCTURE_DASHBOARD.md](./INFRASTRUCTURE_DASHBOARD.md)
- **Production Deployment:** [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)
- **Environment Config:** [PRODUCTION_ENV_TEMPLATE.md](./PRODUCTION_ENV_TEMPLATE.md)
- **Deployment Checklist:** [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)
- **Maintenance Scripts:** [../scripts/maintenance/README.md](../../scripts/maintenance/README.md)

## Common Commands Reference

```bash
# Backend
python3 -m uvicorn apps.backend.main:app --host 127.0.0.1 --port 8009 --reload

# Frontend
cd apps/dashboard && npm run dev

# Database migration
cd database && alembic upgrade head

# Database rollback
cd database && alembic downgrade -1

# Test infrastructure endpoints
curl http://127.0.0.1:8009/api/v1/observability/infrastructure/report

# Check database tables
psql "$DATABASE_URL" -c "\dt *metrics*"

# Run maintenance script
python3 scripts/maintenance/cleanup_old_metrics.py --dry-run

# Docker services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

## Support

- **Documentation Issues:** Check [INFRASTRUCTURE_DASHBOARD.md](./INFRASTRUCTURE_DASHBOARD.md)
- **Deployment Issues:** See [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)
- **Configuration Issues:** Review [PRODUCTION_ENV_TEMPLATE.md](./PRODUCTION_ENV_TEMPLATE.md)
- **Questions:** Create an issue in the repository

---

**Last Updated:** October 1, 2025
**Version:** 1.0.0
**Estimated Setup Time:** 15 minutes
