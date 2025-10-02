# Infrastructure Dashboard - Production Deployment Guide

**Created:** October 1, 2025
**Branch:** development-infrastructure-dashboard
**Status:** Production Ready ✅

## Overview

This guide provides step-by-step instructions for deploying the Infrastructure Dashboard to production. The deployment includes database migrations, backend service updates, frontend integration, and operational monitoring setup.

## Prerequisites

### System Requirements
- **Python:** 3.12+
- **Node.js:** 22+
- **PostgreSQL:** 15+
- **Redis:** 7+
- **Docker:** 25+ (optional, recommended)

### Environment Configuration
- Backend `.env` file configured with production values
- Frontend `.env.local` configured for production API
- Pusher credentials configured for real-time streaming
- Database credentials with appropriate permissions

### Access Requirements
- Database admin access for running migrations
- Backend server deployment access
- Frontend hosting/CDN deployment access
- Monitoring and alerting system access

## Deployment Steps

### Step 1: Database Migration

#### 1.1 Backup Current Database
```bash
# Create backup before migration
pg_dump -h localhost -U eduplatform educational_platform_dev > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backup_*.sql
```

#### 1.2 Run Infrastructure Metrics Migration
```bash
# Navigate to project root
cd /Users/grayghostdataconsultants/Development/projects/clients/Toolbox014/ToolboxAI-Solutions

# Activate virtual environment
source venv/bin/activate

# Run migration
alembic upgrade head

# Verify migration
alembic current
# Expected: infra_metrics_001 (head)
```

#### 1.3 Verify Database Tables
```bash
# Connect to database
psql -h localhost -U eduplatform -d educational_platform_dev

# List new tables
\dt *metrics* *infrastructure* *aggregation*

# Expected tables:
# - system_metrics_history
# - process_metrics_history
# - infrastructure_health
# - infrastructure_alerts
# - metric_aggregations

# Verify indexes
\di idx_system_metrics_*
\di idx_process_metrics_*
\di idx_infra_health_*
\di idx_alerts_*
\di idx_agg_*

# Exit psql
\q
```

### Step 2: Backend Deployment

#### 2.1 Update Backend Dependencies
```bash
# Ensure all dependencies are installed
cd apps/backend
pip install -r ../../requirements.txt

# Verify psutil is installed (critical for metrics)
python3 -c "import psutil; print(f'psutil version: {psutil.__version__}')"
```

#### 2.2 Verify Backend Configuration
```bash
# Check infrastructure metrics service
python3 -c "from apps.backend.services.infrastructure_metrics import infrastructure_metrics; print('✓ Service loaded')"

# Check observability endpoints
python3 -c "from apps.backend.api.v1.endpoints.observability import router; print('✓ Router loaded')"

# Verify router registration
grep -A 5 "observability" apps/backend/api/routers/__init__.py
# Should show: ("apps.backend.api.v1.endpoints.observability", "router", "/api/v1")
```

#### 2.3 Restart Backend Service

**Development:**
```bash
# Stop existing server (Ctrl+C if running)

# Start with reload
uvicorn apps.backend.main:app --host 127.0.0.1 --port 8009 --reload
```

**Production (systemd):**
```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Restart backend service
sudo systemctl restart toolboxai-backend

# Verify status
sudo systemctl status toolboxai-backend

# Check logs
sudo journalctl -u toolboxai-backend -f
```

**Production (Docker):**
```bash
# Rebuild backend image
docker compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.prod.yml \
               build fastapi-backend

# Restart backend container
docker compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.prod.yml \
               up -d fastapi-backend

# Verify health
docker compose logs fastapi-backend | grep "Application startup complete"
```

#### 2.4 Test Backend Endpoints
```bash
# Get authentication token (replace with your credentials)
TOKEN=$(curl -s -X POST http://localhost:8009/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.data.access_token')

# Test infrastructure endpoints
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8009/api/v1/observability/infrastructure/system | jq

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8009/api/v1/observability/infrastructure/process | jq

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8009/api/v1/observability/infrastructure/health | jq

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8009/api/v1/observability/infrastructure/report | jq

# Expected: All should return status: "success" with data
```

### Step 3: Frontend Deployment

#### 3.1 Update Frontend Dependencies
```bash
cd apps/dashboard

# Install dependencies (use Docker on external drives)
npm install --no-bin-links --legacy-peer-deps

# Verify observability service
grep -A 10 "getInfrastructureReport" src/services/observability.ts
```

#### 3.2 Build Frontend for Production
```bash
# Production build
npm run build

# Verify build output
ls -lh dist/
# Expected: index.html, assets/, etc.

# Test build locally
npm run preview
# Access: http://localhost:4173
```

#### 3.3 Deploy Frontend

**Static Hosting (Vercel/Netlify):**
```bash
# Vercel
vercel --prod

# Netlify
netlify deploy --prod --dir=dist
```

**Docker Production:**
```bash
# Rebuild dashboard image
docker compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.prod.yml \
               build dashboard-frontend

# Deploy
docker compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.prod.yml \
               up -d dashboard-frontend
```

#### 3.4 Verify Frontend Access
```bash
# Access dashboard
open http://localhost:5179/observability

# Or production URL
open https://your-domain.com/observability

# Verify infrastructure tab loads
# Check browser console for errors
# Confirm real-time metrics update every 5 seconds
```

### Step 4: Testing & Validation

#### 4.1 Run Backend Test Suite
```bash
# Navigate to project root
cd /Users/grayghostdataconsultants/Development/projects/clients/Toolbox014/ToolboxAI-Solutions

# Activate venv
source venv/bin/activate

# Run infrastructure tests
pytest tests/api/v1/endpoints/test_observability_infrastructure.py -v

# Expected: All 15 tests should pass
# TestInfrastructureSystemMetrics::test_get_system_metrics_success PASSED
# TestInfrastructureProcessMetrics::test_get_process_metrics_success PASSED
# ... (13 more tests)

# Run with coverage
pytest tests/api/v1/endpoints/test_observability_infrastructure.py --cov=apps.backend.api.v1.endpoints.observability --cov-report=html

# View coverage report
open htmlcov/index.html
```

#### 4.2 Integration Testing
```bash
# Test complete workflow
cat > /tmp/test_infrastructure_workflow.sh << 'EOF'
#!/bin/bash
set -e

echo "Testing infrastructure dashboard workflow..."

# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8009/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.data.access_token')

echo "✓ Authentication successful"

# Test all endpoints
endpoints=(
  "/api/v1/observability/infrastructure/system"
  "/api/v1/observability/infrastructure/process"
  "/api/v1/observability/infrastructure/platform"
  "/api/v1/observability/infrastructure/summary"
  "/api/v1/observability/infrastructure/health"
  "/api/v1/observability/infrastructure/report"
)

for endpoint in "${endpoints[@]}"; do
  response=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8009$endpoint")

  status=$(echo "$response" | jq -r '.status')

  if [ "$status" = "success" ]; then
    echo "✓ $endpoint - SUCCESS"
  else
    echo "✗ $endpoint - FAILED"
    echo "$response" | jq
    exit 1
  fi
done

echo "✅ All infrastructure endpoints operational"
EOF

chmod +x /tmp/test_infrastructure_workflow.sh
/tmp/test_infrastructure_workflow.sh
```

#### 4.3 Performance Testing
```bash
# Test response times
cat > /tmp/test_performance.sh << 'EOF'
#!/bin/bash

TOKEN=$(curl -s -X POST http://localhost:8009/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.data.access_token')

# Time the report endpoint (most comprehensive)
echo "Testing report endpoint performance..."
time curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8009/api/v1/observability/infrastructure/report \
  > /dev/null

# Expected: < 1 second for localhost, < 3 seconds for remote
EOF

chmod +x /tmp/test_performance.sh
/tmp/test_performance.sh
```

### Step 5: Operational Configuration

#### 5.1 Configure Production Thresholds

Edit `apps/backend/services/infrastructure_metrics.py`:

```python
# Production thresholds (adjust based on your infrastructure)
THRESHOLDS = {
    "cpu_warning": 80.0,      # Increased from 70.0 for production workloads
    "cpu_critical": 95.0,     # Increased from 90.0
    "memory_warning": 85.0,   # Increased from 75.0
    "memory_critical": 95.0,  # Increased from 90.0
    "disk_warning": 85.0,     # Increased from 80.0
    "disk_critical": 98.0,    # Increased from 95.0
}
```

Restart backend after changes.

#### 5.2 Set Up Data Retention Cleanup Job

Create cleanup script:

```bash
cat > scripts/maintenance/cleanup_old_metrics.py << 'EOF'
#!/usr/bin/env python3
"""
Cleanup old infrastructure metrics data

Run daily via cron to maintain database size
"""
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models.infrastructure_metrics import cleanup_old_metrics
from toolboxai_settings.settings import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print(f"Starting cleanup at {datetime.now(timezone.utc)}")
        await cleanup_old_metrics(session, days_to_keep=30)
        print("✓ Cleanup completed")

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x scripts/maintenance/cleanup_old_metrics.py
```

Add cron job:

```bash
# Edit crontab
crontab -e

# Add daily cleanup at 2 AM
0 2 * * * cd /path/to/ToolboxAI-Solutions && source venv/bin/activate && python3 scripts/maintenance/cleanup_old_metrics.py >> logs/metrics_cleanup.log 2>&1
```

#### 5.3 Configure Alert Notifications

Create alert handler:

```bash
cat > scripts/maintenance/infrastructure_alerts.py << 'EOF'
#!/usr/bin/env python3
"""
Monitor infrastructure health and send alerts

Run every 5 minutes via cron
"""
import asyncio
import httpx
from datetime import datetime, timezone

BACKEND_URL = "http://localhost:8009"
SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

async def check_and_alert():
    async with httpx.AsyncClient() as client:
        # Get auth token
        auth_response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "admin123"}
        )
        token = auth_response.json()["data"]["access_token"]

        # Check health
        health_response = await client.get(
            f"{BACKEND_URL}/api/v1/observability/infrastructure/health",
            headers={"Authorization": f"Bearer {token}"}
        )

        health_data = health_response.json()["data"]

        # Send alerts for warnings or critical issues
        if health_data["warnings"] or health_data["critical"]:
            message = {
                "text": f"⚠️ Infrastructure Alert at {datetime.now(timezone.utc)}",
                "attachments": [
                    {
                        "color": "danger" if health_data["critical"] else "warning",
                        "fields": [
                            {"title": "Status", "value": health_data["status"], "short": True},
                            {"title": "Warnings", "value": str(len(health_data["warnings"])), "short": True},
                            {"title": "Critical", "value": str(len(health_data["critical"])), "short": True}
                        ]
                    }
                ]
            }

            # Send to Slack
            await client.post(SLACK_WEBHOOK, json=message)
            print(f"✓ Alert sent: {health_data['status']}")

if __name__ == "__main__":
    asyncio.run(check_and_alert())
EOF

chmod +x scripts/maintenance/infrastructure_alerts.py
```

Add cron job:

```bash
# Run every 5 minutes
*/5 * * * * cd /path/to/ToolboxAI-Solutions && source venv/bin/activate && python3 scripts/maintenance/infrastructure_alerts.py >> logs/infrastructure_alerts.log 2>&1
```

## Verification Checklist

### Database
- [ ] Migration applied successfully (`alembic current` shows `infra_metrics_001`)
- [ ] All 5 tables created with proper indexes
- [ ] PostgreSQL enums created (metrictype, healthstatus)
- [ ] Database backup created and verified

### Backend
- [ ] Backend service restarted successfully
- [ ] All 6 infrastructure endpoints return 200 OK
- [ ] Authentication working (401 for invalid tokens)
- [ ] Response format matches specification (status, data, metadata)
- [ ] Pusher streaming functional (optional, for real-time)

### Frontend
- [ ] Dashboard builds successfully (`npm run build`)
- [ ] Observability tab accessible at `/observability`
- [ ] Infrastructure sub-tab displays metrics
- [ ] Real-time updates working (5-second refresh)
- [ ] No console errors in browser
- [ ] Responsive layout on mobile/tablet

### Testing
- [ ] All 15 backend tests passing
- [ ] Integration workflow test passing
- [ ] Performance test < 1s response time
- [ ] End-to-end user workflow verified

### Operations
- [ ] Production thresholds configured
- [ ] Data retention cleanup job scheduled
- [ ] Alert notifications configured and tested
- [ ] Monitoring dashboard accessible to operations team

## Rollback Procedure

If deployment encounters issues, follow this rollback procedure:

### 1. Database Rollback
```bash
# Rollback migration
alembic downgrade -1

# Verify rollback
alembic current
# Should show: b6d899aab2fb (previous migration)

# Restore from backup if needed
psql -h localhost -U eduplatform -d educational_platform_dev < backup_YYYYMMDD_HHMMSS.sql
```

### 2. Backend Rollback
```bash
# Git rollback
git checkout main
git pull origin main

# Restart backend
sudo systemctl restart toolboxai-backend

# Or Docker
docker compose restart fastapi-backend
```

### 3. Frontend Rollback
```bash
# Revert to previous deployment
vercel rollback  # For Vercel
# Or
netlify rollback  # For Netlify

# Or Docker
docker compose restart dashboard-frontend
```

## Troubleshooting

### Issue: Migration Fails
**Symptoms:** `alembic upgrade head` returns errors
**Solution:**
1. Check database connectivity: `psql -h localhost -U eduplatform -d educational_platform_dev`
2. Verify migration file syntax: `cat database/migrations/versions/20251001_2200-add_infrastructure_metrics.py`
3. Check for conflicting table names: `\dt *metrics*` in psql
4. Review alembic history: `alembic history`

### Issue: Backend Endpoints Return 500
**Symptoms:** `/infrastructure/report` returns internal server error
**Solution:**
1. Check backend logs: `sudo journalctl -u toolboxai-backend -n 100`
2. Verify psutil installed: `python3 -c "import psutil"`
3. Check database connection: Verify DATABASE_URL in .env
4. Test infrastructure_metrics service: `python3 -c "from apps.backend.services.infrastructure_metrics import infrastructure_metrics; print(infrastructure_metrics.collect_system_metrics())"`

### Issue: Frontend Shows No Data
**Symptoms:** Infrastructure tab loads but shows loading spinner
**Solution:**
1. Open browser console: Check for API errors
2. Verify API URL: Check VITE_API_BASE_URL in .env.local
3. Test backend directly: `curl http://localhost:8009/api/v1/observability/infrastructure/report`
4. Check CORS configuration: Verify frontend URL in backend CORS settings
5. Verify authentication: Check token storage in browser localStorage

### Issue: Real-time Updates Not Working
**Symptoms:** Metrics don't refresh automatically
**Solution:**
1. Verify Pusher credentials in backend .env
2. Check Pusher dashboard for connection status
3. Test `/api/v1/observability/start-metrics-stream` endpoint
4. Verify frontend Pusher configuration in .env.local
5. Check browser console for Pusher connection errors

## Post-Deployment

### Monitoring
- **Health Checks:** Monitor `/infrastructure/health` endpoint every 5 minutes
- **Performance:** Track response times via application monitoring (Sentry, New Relic)
- **Database:** Monitor table sizes and query performance
- **Alerts:** Configure PagerDuty/Slack for critical infrastructure issues

### Maintenance
- **Daily:** Review infrastructure health dashboard
- **Weekly:** Check database growth and cleanup job logs
- **Monthly:** Review and adjust production thresholds based on actual usage
- **Quarterly:** Audit alert configurations and update as needed

### Documentation Updates
- Update architecture diagrams with new infrastructure components
- Document any custom threshold configurations
- Record performance baselines for comparison
- Maintain changelog of infrastructure updates

---

**Deployment Date:** _____________
**Deployed By:** _____________
**Verified By:** _____________
**Production URL:** _____________
