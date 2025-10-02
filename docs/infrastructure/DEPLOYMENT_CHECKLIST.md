# Infrastructure Dashboard - Production Deployment Checklist

**Created:** October 1, 2025
**Branch:** development-infrastructure-dashboard
**Status:** Ready for Production

## Pre-Deployment Checklist

### Phase 1: Code Review & Testing ✅

- [ ] **Code Review Complete**
  - [ ] All infrastructure metrics code reviewed
  - [ ] Backend endpoints tested
  - [ ] Frontend components verified
  - [ ] No hardcoded secrets or credentials
  - [ ] Code follows project standards

- [ ] **Test Suite Execution**
  ```bash
  # Run backend tests
  pytest tests/api/v1/endpoints/test_observability_infrastructure.py -v
  # Expected: 15/15 tests passing
  ```
  - [ ] All 15 infrastructure tests passing
  - [ ] Integration tests completed
  - [ ] Performance tests run successfully
  - [ ] No critical bugs identified

- [ ] **Security Audit**
  - [ ] JWT secrets validated (64+ characters, high entropy)
  - [ ] Database passwords are strong
  - [ ] No API keys in code or version control
  - [ ] CORS configuration restricted to production domains
  - [ ] Swagger UI disabled in production
  - [ ] Debug mode disabled

### Phase 2: Environment Configuration 🔧

- [ ] **Backend Environment Setup**
  ```bash
  # Location: .env or apps/backend/.env
  ```
  - [ ] DATABASE_URL configured (PostgreSQL connection string)
  - [ ] REDIS_URL configured
  - [ ] SECRET_KEY generated (32+ characters)
  - [ ] JWT_SECRET_KEY generated (64+ characters)
  - [ ] PUSHER credentials (APP_ID, KEY, SECRET, CLUSTER)
  - [ ] ENVIRONMENT set to "production"
  - [ ] DEBUG=false
  - [ ] CORS_ORIGINS includes production frontend URL
  - [ ] SENTRY_DSN configured (if using error tracking)
  - [ ] ADMIN_EMAIL and ADMIN_PASSWORD for maintenance scripts

- [ ] **Frontend Environment Setup**
  ```bash
  # Location: apps/dashboard/.env.production
  ```
  - [ ] VITE_API_BASE_URL points to production backend
  - [ ] VITE_PUSHER_KEY matches backend configuration
  - [ ] VITE_PUSHER_CLUSTER matches backend
  - [ ] VITE_ENABLE_REAL_TIME=true
  - [ ] VITE_SENTRY_DSN configured (if using)

- [ ] **Health Check Thresholds**
  - [ ] HEALTH_CPU_WARNING appropriate for infrastructure
  - [ ] HEALTH_CPU_CRITICAL set (recommendation: 90.0-95.0)
  - [ ] HEALTH_MEMORY_WARNING appropriate
  - [ ] HEALTH_MEMORY_CRITICAL set (recommendation: 90.0-95.0)
  - [ ] HEALTH_DISK_WARNING set (recommendation: 80.0-85.0)
  - [ ] HEALTH_DISK_CRITICAL set (recommendation: 95.0-98.0)

### Phase 3: Database Setup 🗄️

- [ ] **Database Preparation**
  ```bash
  # Backup existing database
  pg_dump -h localhost -U YOUR_USER YOUR_DB > backup_$(date +%Y%m%d).sql
  ```
  - [ ] Current database backed up
  - [ ] Backup verified and stored securely
  - [ ] Database user has necessary permissions
  - [ ] Connection tested successfully

- [ ] **Run Migrations**
  ```bash
  cd database
  alembic current  # Check current state
  alembic upgrade head  # Run migrations
  ```
  - [ ] Alembic migrations executed successfully
  - [ ] Current revision shows: infra_metrics_001
  - [ ] All 5 tables created:
    - [ ] system_metrics_history
    - [ ] process_metrics_history
    - [ ] infrastructure_health
    - [ ] infrastructure_alerts
    - [ ] metric_aggregations
  - [ ] Indexes created successfully
  - [ ] PostgreSQL enums created (metrictype, healthstatus)

- [ ] **Database Verification**
  ```bash
  psql "$DATABASE_URL" -c "\dt *metrics* *infrastructure*"
  psql "$DATABASE_URL" -c "\di idx_system_* idx_process_* idx_infra_* idx_alerts_*"
  ```
  - [ ] Tables visible and accessible
  - [ ] Indexes exist on all timestamp columns
  - [ ] Performance indexes created

### Phase 4: Backend Deployment 🚀

- [ ] **Service Preparation**
  - [ ] Dependencies installed (requirements.txt)
  - [ ] psutil library available
  - [ ] Virtual environment configured
  - [ ] Python 3.12+ available

- [ ] **Backend Start/Restart**
  ```bash
  # Development
  uvicorn apps.backend.main:app --host 127.0.0.1 --port 8009 --reload

  # Production (systemd)
  sudo systemctl restart toolboxai-backend

  # Production (Docker)
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d fastapi-backend
  ```
  - [ ] Backend service started successfully
  - [ ] No errors in startup logs
  - [ ] Health endpoint accessible
  - [ ] API documentation accessible (if enabled)

- [ ] **Endpoint Verification**
  ```bash
  # Get auth token
  TOKEN=$(curl -s -X POST http://YOUR_BACKEND/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@example.com","password":"YOUR_PASSWORD"}' \
    | jq -r '.data.access_token')

  # Test endpoints
  curl -H "Authorization: Bearer $TOKEN" http://YOUR_BACKEND/api/v1/observability/infrastructure/system
  curl -H "Authorization: Bearer $TOKEN" http://YOUR_BACKEND/api/v1/observability/infrastructure/health
  curl -H "Authorization: Bearer $TOKEN" http://YOUR_BACKEND/api/v1/observability/infrastructure/report
  ```
  - [ ] /infrastructure/system returns 200 OK
  - [ ] /infrastructure/process returns 200 OK
  - [ ] /infrastructure/platform returns 200 OK
  - [ ] /infrastructure/summary returns 200 OK
  - [ ] /infrastructure/health returns 200 OK
  - [ ] /infrastructure/report returns 200 OK
  - [ ] All responses have status: "success"
  - [ ] Metric data is accurate and realistic

### Phase 5: Frontend Deployment 🎨

- [ ] **Build Frontend**
  ```bash
  cd apps/dashboard
  npm install --no-bin-links  # If on external drive
  npm run build
  ```
  - [ ] Build completes without errors
  - [ ] dist/ directory created
  - [ ] Assets optimized and bundled
  - [ ] Source maps generated (if needed)

- [ ] **Deploy Frontend**
  ```bash
  # Vercel
  vercel --prod

  # Netlify
  netlify deploy --prod --dir=dist

  # Docker
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d dashboard-frontend
  ```
  - [ ] Frontend deployed successfully
  - [ ] HTTPS certificate configured
  - [ ] CDN configured (if applicable)
  - [ ] Cache headers set appropriately

- [ ] **Frontend Verification**
  - [ ] Dashboard loads at production URL
  - [ ] Authentication works
  - [ ] /observability route accessible
  - [ ] Infrastructure tab displays
  - [ ] Metrics load and display
  - [ ] Real-time updates working (5-second refresh)
  - [ ] No console errors
  - [ ] Responsive on mobile/tablet
  - [ ] Pusher connection established

### Phase 6: Operational Setup ⚙️

- [ ] **Maintenance Scripts Configuration**
  ```bash
  # Make scripts executable
  chmod +x scripts/maintenance/*.py

  # Test scripts
  python3 scripts/maintenance/cleanup_old_metrics.py --dry-run
  python3 scripts/maintenance/infrastructure_alerts.py
  python3 scripts/maintenance/create_metric_aggregations.py --hours 1
  ```
  - [ ] cleanup_old_metrics.py tested
  - [ ] infrastructure_alerts.py tested
  - [ ] create_metric_aggregations.py tested
  - [ ] All scripts run without errors

- [ ] **Cron Jobs Setup**
  ```bash
  crontab -e
  ```
  - [ ] Daily cleanup job scheduled (2 AM)
    ```cron
    0 2 * * * cd /path/to/project && source venv/bin/activate && python3 scripts/maintenance/cleanup_old_metrics.py --vacuum >> logs/cleanup.log 2>&1
    ```
  - [ ] Health monitoring (every 5 minutes)
    ```cron
    */5 * * * * cd /path/to/project && source venv/bin/activate && python3 scripts/maintenance/infrastructure_alerts.py --slack-webhook "URL" >> logs/alerts.log 2>&1
    ```
  - [ ] Hourly aggregations
    ```cron
    0 * * * * cd /path/to/project && source venv/bin/activate && python3 scripts/maintenance/create_metric_aggregations.py --hours 2 >> logs/aggregations.log 2>&1
    ```
  - [ ] Daily aggregations (3 AM)
    ```cron
    0 3 * * * cd /path/to/project && source venv/bin/activate && python3 scripts/maintenance/create_metric_aggregations.py --period daily --hours 48 >> logs/aggregations.log 2>&1
    ```

- [ ] **Alert Configuration**
  - [ ] Slack webhook URL configured
  - [ ] Slack channel created (#infrastructure-alerts)
  - [ ] Test alert sent successfully
  - [ ] Alert thresholds appropriate
  - [ ] Alert cooldown configured (15 minutes)

- [ ] **Log Management**
  ```bash
  # Create log directory
  mkdir -p logs

  # Setup log rotation
  sudo nano /etc/logrotate.d/toolboxai-infrastructure
  ```
  - [ ] Log directory created
  - [ ] Log rotation configured
  - [ ] Log retention policy set (30 days)
  - [ ] Disk space monitored

### Phase 7: Monitoring & Validation 📊

- [ ] **Performance Testing**
  ```bash
  # Test response times
  time curl -H "Authorization: Bearer $TOKEN" http://YOUR_BACKEND/api/v1/observability/infrastructure/report
  ```
  - [ ] /report endpoint < 1 second (localhost)
  - [ ] /report endpoint < 3 seconds (remote)
  - [ ] Dashboard loads < 2 seconds
  - [ ] Metrics refresh smoothly
  - [ ] No memory leaks observed

- [ ] **Stress Testing**
  ```bash
  # Use Apache Bench or similar
  ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" http://YOUR_BACKEND/api/v1/observability/infrastructure/health
  ```
  - [ ] Backend handles concurrent requests
  - [ ] No 500 errors under load
  - [ ] Response times acceptable
  - [ ] Database connections stable

- [ ] **Data Verification**
  ```bash
  # Check metrics are being stored
  psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM system_metrics_history;"
  psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM process_metrics_history;"
  ```
  - [ ] Metrics storing successfully
  - [ ] Data is accurate
  - [ ] Timestamps are correct (UTC)
  - [ ] No duplicate entries

### Phase 8: Documentation & Handoff 📚

- [ ] **Documentation Complete**
  - [ ] INFRASTRUCTURE_DASHBOARD.md reviewed
  - [ ] PRODUCTION_DEPLOYMENT.md reviewed
  - [ ] PRODUCTION_ENV_TEMPLATE.md reviewed
  - [ ] scripts/maintenance/README.md reviewed
  - [ ] All configuration examples accurate

- [ ] **Team Training**
  - [ ] DevOps team trained on dashboard
  - [ ] Alert response procedures documented
  - [ ] Escalation process defined
  - [ ] Troubleshooting guide shared

- [ ] **Runbook Created**
  - [ ] Common issues documented
  - [ ] Resolution steps defined
  - [ ] Contact information included
  - [ ] Emergency procedures outlined

### Phase 9: Post-Deployment Verification ✅

- [ ] **24-Hour Monitoring**
  - [ ] No critical errors in logs
  - [ ] Metrics collecting consistently
  - [ ] Alerts functioning properly
  - [ ] Dashboard accessible and stable
  - [ ] Database growth normal
  - [ ] No performance degradation

- [ ] **7-Day Review**
  - [ ] Data retention working
  - [ ] Aggregations creating successfully
  - [ ] Alert threshold tuning needed?
  - [ ] Performance optimization needed?
  - [ ] User feedback collected

## Rollback Plan

If issues occur, follow this rollback procedure:

### 1. Database Rollback
```bash
# Rollback migration
cd database
alembic downgrade -1

# Restore from backup
psql "$DATABASE_URL" < backup_YYYYMMDD.sql
```

### 2. Backend Rollback
```bash
# Git rollback
git checkout main
git pull origin main

# Restart service
sudo systemctl restart toolboxai-backend
```

### 3. Frontend Rollback
```bash
# Vercel
vercel rollback

# Netlify
netlify rollback
```

## Success Criteria

Deployment is successful when:

✅ All 6 infrastructure endpoints return 200 OK
✅ Dashboard displays real-time metrics
✅ Metrics update every 5 seconds
✅ Health scores calculate correctly
✅ Alerts trigger on threshold violations
✅ Data persists to database
✅ Maintenance scripts run successfully
✅ No errors in logs for 24 hours
✅ Performance meets requirements
✅ Team trained and comfortable with system

## Sign-Off

- [ ] **Technical Lead Approval**
  - Name: ___________________________
  - Date: ___________________________
  - Signature: ______________________

- [ ] **DevOps Approval**
  - Name: ___________________________
  - Date: ___________________________
  - Signature: ______________________

- [ ] **Product Owner Approval**
  - Name: ___________________________
  - Date: ___________________________
  - Signature: ______________________

---

**Deployment Date:** _______________
**Deployed By:** _______________
**Production URL:** _______________
**Version:** 1.0.0

**Next Review Date:** _______________
