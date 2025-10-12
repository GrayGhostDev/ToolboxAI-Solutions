# Supabase Backend Enhancement - Implementation Checklist
## Quick Reference for Issue #39

**Last Updated:** 2025-10-10
**Status:** 📋 Ready to Begin
**Full Plan:** [SUPABASE_BACKEND_ENHANCEMENT_PLAN.md](./SUPABASE_BACKEND_ENHANCEMENT_PLAN.md)

---

## Quick Start Commands

### Environment Setup

```bash
# Set required environment variables
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_ANON_KEY=your-anon-key
export SUPABASE_SERVICE_ROLE_KEY=your-service-key
export PUSHER_APP_ID=your-app-id
export PUSHER_KEY=your-key
export PUSHER_SECRET=your-secret
export PUSHER_CLUSTER=us2

# Frontend (.env.local)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_PUSHER_KEY=your-key
VITE_PUSHER_CLUSTER=us2
```

### Deploy Edge Functions

```bash
cd apps/backend/supabase/functions

# Deploy all Edge Functions
supabase functions deploy file-processing
supabase functions deploy notification-dispatcher
supabase functions deploy analytics-aggregation --schedule "*/5 * * * *"

# Verify deployment
supabase functions list
```

### Run Database Migration

```bash
# Apply RLS policies migration
supabase db push

# Or manually
psql $SUPABASE_URL -f database/supabase/migrations/002_enhanced_rls_policies.sql
```

---

## Phase 1: Database Integration (Week 1) - 16-20 hours

### Task 1.1: Storage Provider Database Integration (6-8 hours)

**File:** `apps/backend/services/storage/supabase_provider.py`

- [ ] Replace `_create_file_record()` with SQLAlchemy
- [ ] Replace `_get_file_record()` with SQLAlchemy
- [ ] Replace `_list_file_records()` with SQLAlchemy
- [ ] Replace `_delete_file_record()` with SQLAlchemy
- [ ] Replace `_soft_delete_file_record()` with SQLAlchemy
- [ ] Replace `_update_file_path()` with SQLAlchemy
- [ ] Replace `_track_file_access()` with `FileAccessLog` model
- [ ] Replace `_validate_tenant_access()` with org checks
- [ ] Unit tests for all 8 methods
- [ ] Integration tests with PostgreSQL
- [ ] Test multi-tenant isolation

**Verification:**
```bash
pytest tests/unit/services/test_storage_provider.py -v
pytest tests/integration/test_storage_integration.py -v
```

---

### Task 1.2: RLS Policies Migration (4-6 hours)

**File:** `database/supabase/migrations/002_enhanced_rls_policies.sql`

- [ ] Review migration file (677 lines)
- [ ] Apply migration to Supabase
- [ ] Test student role (own data only)
- [ ] Test teacher role (org data)
- [ ] Test admin role (full access)
- [ ] Test service role (bypass RLS)
- [ ] Verify organization isolation
- [ ] Check audit logging works

**Test Queries:**
```sql
-- Test as student
SET SESSION my.user_id = '<student-id>';
SET SESSION my.user_role = 'student';
SET SESSION my.organization_id = '<org-id>';
SELECT COUNT(*) FROM agent_executions;  -- Should see only own

-- Test audit log
SELECT * FROM rls_audit_log ORDER BY timestamp DESC LIMIT 10;
```

---

### Task 1.3: Database Models Integration (3-4 hours)

**Files:** `database/models/*.py`

- [ ] Add `organization_id` to all models
- [ ] Create indexes for `organization_id`
- [ ] Generate Alembic migration
- [ ] Apply migration to database
- [ ] Update service layer with org filtering
- [ ] Test queries include org filter

**Commands:**
```bash
alembic revision --autogenerate -m "Add organization_id for RLS"
alembic upgrade head
```

---

## Phase 2: Edge Functions Deployment (Week 2) - 12-16 hours

### Task 2.1: File Processing Edge Function (4-5 hours)

**File:** `apps/backend/supabase/functions/file-processing/index.ts`

- [ ] Review function code (612 lines)
- [ ] Configure environment variables
- [ ] Deploy to Supabase
- [ ] Create storage triggers
- [ ] Test with sample file upload
- [ ] Verify virus scanning works
- [ ] Check thumbnail generation
- [ ] Monitor function logs

**Deploy:**
```bash
supabase functions deploy file-processing
```

**Test:**
```bash
curl -X POST https://<ref>.supabase.co/functions/v1/file-processing \
  -H "Authorization: Bearer <key>" \
  -d '{"bucket":"files","objectName":"test.jpg"}'
```

---

### Task 2.2: Notification Dispatcher (4-5 hours)

**File:** `apps/backend/supabase/functions/notification-dispatcher/index.ts`

- [ ] Configure Pusher credentials
- [ ] Deploy to Supabase
- [ ] Configure database webhooks
- [ ] Test notification sending
- [ ] Verify rate limiting (60/min)
- [ ] Check message batching
- [ ] Monitor Pusher dashboard

**Deploy:**
```bash
supabase functions deploy notification-dispatcher
```

**Test:**
```bash
curl -X POST https://<ref>.supabase.co/functions/v1/notification-dispatcher \
  -H "Authorization: Bearer <key>" \
  -d '{"type":"UPDATE","table":"agent_executions","record":{"status":"completed"}}'
```

---

### Task 2.3: Analytics Aggregation (4-6 hours)

**File:** `apps/backend/supabase/functions/analytics-aggregation/index.ts`

- [ ] Deploy with cron schedule
- [ ] Verify cron runs every 5 minutes
- [ ] Check metrics aggregation
- [ ] Verify health score calculation
- [ ] Test manual trigger
- [ ] Monitor function performance
- [ ] Check data retention cleanup

**Deploy:**
```bash
supabase functions deploy analytics-aggregation --schedule "*/5 * * * *"
```

**Monitor:**
```bash
supabase functions logs analytics-aggregation --tail
```

---

## Phase 3: Integration & Testing (Week 3) - 20-24 hours

### Task 3.1: Frontend Supabase Client (6-8 hours)

**Files to Create:**
- [ ] `apps/dashboard/src/lib/supabase.ts`
- [ ] `apps/dashboard/src/hooks/useSupabaseAuth.ts`
- [ ] `apps/dashboard/src/hooks/useSupabaseRealtime.ts`
- [ ] `apps/dashboard/src/contexts/SupabaseContext.tsx`

**Implementation:**
- [ ] Initialize Supabase client
- [ ] Create auth hook
- [ ] Create real-time hook
- [ ] Add to component tree
- [ ] Test authentication flow
- [ ] Test real-time subscriptions

---

### Task 3.2: E2E Integration Tests (8-10 hours)

**Files to Create:**
- [ ] `tests/e2e/supabase/test_rls_policies.py`
- [ ] `tests/e2e/supabase/test_edge_functions.py`
- [ ] `tests/e2e/supabase/test_storage_integration.py`
- [ ] `tests/e2e/supabase/test_realtime_features.py`

**Test Coverage:**
- [ ] RLS policies for all roles
- [ ] Organization isolation
- [ ] Edge Function endpoints
- [ ] Storage upload/download
- [ ] Real-time subscriptions
- [ ] Performance benchmarks

**Run Tests:**
```bash
pytest tests/e2e/supabase/ -v --cov
```

---

### Task 3.3: Performance Testing (6 hours)

**Tools:** Apache Bench, Locust, k6

- [ ] Load test Edge Functions (>100 req/sec)
- [ ] Measure RLS query overhead (<5ms)
- [ ] Test real-time subscriptions (100+ channels)
- [ ] Monitor memory usage
- [ ] Check rate limits
- [ ] Generate performance report

**Commands:**
```bash
ab -n 1000 -c 10 https://<ref>.supabase.co/functions/v1/file-processing
k6 run tests/performance/edge-functions.js
```

---

## Phase 4: Documentation & Deployment (Week 4) - 12-16 hours

### Task 4.1: Comprehensive Documentation (8-10 hours)

**Documents to Create:**
- [ ] `docs/integration/supabase-complete-guide.md` (2,000+ words)
- [ ] `docs/api/supabase-api-reference.md` (1,500+ words)
- [ ] `docs/development/supabase-development.md` (1,000+ words)
- [ ] `docs/operations/supabase-runbook.md` (500+ words)

**Content Requirements:**
- [ ] Architecture diagrams
- [ ] Setup instructions
- [ ] API reference
- [ ] Code examples
- [ ] Troubleshooting guide
- [ ] Operations runbook

---

### Task 4.2: Monitoring & Observability (4-6 hours)

**Setup:**
- [ ] Supabase dashboard configuration
- [ ] Prometheus metrics implementation
- [ ] Grafana dashboards creation
- [ ] Alert rules configuration
- [ ] Test alert notifications
- [ ] Document runbook for alerts

**Metrics to Track:**
- Edge Function invocations
- Query performance (with RLS)
- System health score
- Storage usage
- Real-time connections
- Error rates

---

## Verification Checklist

### Before Production Deployment

**Technical:**
- [ ] All Edge Functions deployed and responding
- [ ] RLS policies active and tested
- [ ] Storage provider using real database
- [ ] E2E tests passing (>80% coverage)
- [ ] Performance benchmarks met
- [ ] Security audit completed

**Operational:**
- [ ] Monitoring dashboards configured
- [ ] Alerts set up and tested
- [ ] Documentation complete
- [ ] Runbook reviewed
- [ ] Team training completed

**Security:**
- [ ] 0 high-severity vulnerabilities
- [ ] Audit logging operational
- [ ] Rate limiting tested
- [ ] Organization isolation verified
- [ ] Compliance requirements met

---

## Quick Troubleshooting

### Edge Function Not Deploying

```bash
# Check Supabase CLI version
supabase --version  # Should be >=1.27.0

# Re-authenticate
supabase login

# Deploy with verbose output
supabase functions deploy <function-name> --debug
```

### RLS Policies Not Working

```sql
-- Check if RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';

-- Check active policies
SELECT * FROM pg_policies WHERE schemaname = 'public';

-- Test with specific user context
SET SESSION my.user_id = '<user-id>';
SET SESSION my.organization_id = '<org-id>';
```

### Real-time Subscriptions Not Receiving Updates

```javascript
// Enable debug logging
const { createClient } = require('@supabase/supabase-js');
const supabase = createClient(url, key, {
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
    log_level: 'debug',
  },
});
```

---

## Success Metrics

**Target Metrics:**
- ✅ Test Coverage: >80%
- ✅ RLS Overhead: <5ms
- ✅ Edge Function P95: <2s
- ✅ Real-time Latency: <500ms
- ✅ Error Rate: <0.1%
- ✅ Uptime: >99.9%

**Track Progress:**
```bash
# Test coverage
pytest --cov=apps/backend/services/storage --cov-report=term-missing

# Performance
k6 run --summary-export=summary.json tests/performance/supabase-load.js
```

---

## Resources

**Documentation:**
- [Full Implementation Plan](./SUPABASE_BACKEND_ENHANCEMENT_PLAN.md)
- [Supabase Docs](https://supabase.com/docs)
- [Edge Functions Guide](https://supabase.com/docs/guides/functions)
- [RLS Guide](https://supabase.com/docs/guides/auth/row-level-security)

**Support:**
- Supabase Discord: https://discord.supabase.com
- GitHub Issues: https://github.com/GrayGhostDev/ToolboxAI-Solutions/issues/39

---

**Last Updated:** 2025-10-10
**Status:** Ready for Implementation
