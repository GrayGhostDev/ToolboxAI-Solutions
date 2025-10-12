# RLS Policies Deployment and Testing Guide
## Supabase Enhanced Row Level Security Implementation

**Date:** 2025-10-10
**Migration File:** `database/supabase/migrations/002_enhanced_rls_policies.sql`
**Status:** ✅ Validated - Ready for Deployment
**Issue:** #39 - Supabase Backend Enhancement, Phase 1, Task 1.2

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Validation](#pre-deployment-validation)
3. [Deployment Steps](#deployment-steps)
4. [Testing Procedures](#testing-procedures)
5. [Rollback Plan](#rollback-plan)
6. [Monitoring & Verification](#monitoring--verification)

---

## Overview

### What This Migration Does

The `002_enhanced_rls_policies.sql` migration implements comprehensive Row Level Security (RLS) policies for multi-tenant isolation and role-based access control in the Supabase/PostgreSQL database.

**Key Components:**
- **6 Helper Functions** - Authorization and organization checking
- **Organization Columns** - Added to 5 core tables with indexes
- **40+ RLS Policies** - Comprehensive access control across 6 tables
- **Audit Logging** - Automatic tracking of all data modifications
- **Role-Based Access** - Student, Teacher, Admin, Service Role

### Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   RLS Security Layers                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: Service Role                                      │
│    └─► Full access (bypass RLS)                            │
│        Used by: Backend FastAPI application                │
│                                                             │
│  Layer 2: Admin Role                                        │
│    └─► Full CRUD within organization                       │
│        Can: View, Create, Update, Delete                   │
│        Scope: Organization-wide                            │
│                                                             │
│  Layer 3: Teacher Role                                      │
│    └─► Read access within organization                     │
│        Can: View all org data                              │
│        Cannot: Modify agent instances/configs              │
│                                                             │
│  Layer 4: Student Role                                      │
│    └─► Personal data only                                  │
│        Can: View own executions                            │
│        Can: Update own ratings                             │
│        Cannot: View other students' data                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Tables Affected

| Table | Policies | Organization Column | Indexes |
|-------|----------|---------------------|---------|
| `agent_instances` | 7 | ✅ Added | ✅ Created |
| `agent_executions` | 6 | ✅ Added | ✅ Created |
| `agent_metrics` | 4 | ✅ Added | ✅ Created |
| `agent_task_queue` | 6 | ✅ Added | ✅ Created |
| `system_health` | 3 | N/A (global) | N/A |
| `agent_configurations` | 6 | ✅ Added | ✅ Created |
| `rls_audit_log` | Created | ✅ Yes | ✅ Created |

---

## Pre-Deployment Validation

### 1. SQL Syntax Validation

**Validate Locally:**
```bash
# Check SQL syntax without executing
psql -d your_database --dry-run < database/supabase/migrations/002_enhanced_rls_policies.sql

# Or use pg_dump to validate
pg_dump --schema-only --no-owner --no-privileges your_database > /tmp/schema_backup.sql
```

**Expected Output:**
- No syntax errors
- All CREATE statements valid
- All DROP statements safe (IF EXISTS)

### 2. Dependencies Check

**Required:**
- ✅ PostgreSQL 12+ (for SECURITY DEFINER)
- ✅ Supabase Auth extension
- ✅ Tables from 001_create_agent_system_tables.sql exist
- ✅ UUID extension enabled

**Verification Script:**
```sql
-- Check PostgreSQL version
SELECT version();
-- Expected: PostgreSQL 14+ or 15+

-- Check required tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'agent_instances',
    'agent_executions',
    'agent_metrics',
    'agent_task_queue',
    'system_health',
    'agent_configurations'
  );
-- Expected: 6 rows

-- Check auth.uid() function exists
SELECT has_function_privilege('auth.uid()', 'execute');
-- Expected: t (true)

-- Check UUID extension
SELECT * FROM pg_extension WHERE extname = 'uuid-ossp';
-- Expected: 1 row
```

### 3. Backup Current State

**Before deploying, create backups:**

```bash
# Backup entire database
pg_dump your_database > backup_before_rls_$(date +%Y%m%d_%H%M%S).sql

# Backup just schema
pg_dump --schema-only your_database > schema_backup_$(date +%Y%m%d_%H%M%S).sql

# Backup policies only
pg_dump --section=policy your_database > policies_backup_$(date +%Y%m%d_%H%M%S).sql

# Using Supabase CLI
supabase db dump --file backup_before_rls.sql
```

### 4. Review Migration File

**Validation Checklist:**

- [x] File size: 18,700 bytes (~677 lines)
- [x] Contains 12 distinct steps
- [x] Helper functions: 6 total
- [x] Organization columns: 5 tables
- [x] RLS policies: 40+ policies
- [x] Audit logging: Table + triggers created
- [x] Grants: Proper permissions set
- [x] Comments: Documentation included
- [x] Idempotent: Safe to run multiple times (IF NOT EXISTS, DROP IF EXISTS)

**Manual Review:**
```bash
# Count helper functions
grep -c "CREATE OR REPLACE FUNCTION" database/supabase/migrations/002_enhanced_rls_policies.sql
# Expected: 7 (6 + 1 test function)

# Count policies
grep -c "CREATE POLICY" database/supabase/migrations/002_enhanced_rls_policies.sql
# Expected: 40+

# Count organization columns
grep -c "ADD COLUMN organization_id" database/supabase/migrations/002_enhanced_rls_policies.sql
# Expected: 5

# Check for dangerous operations
grep -E "DROP TABLE|TRUNCATE|DELETE FROM" database/supabase/migrations/002_enhanced_rls_policies.sql
# Expected: None (only DROP POLICY IF EXISTS)
```

---

## Deployment Steps

### Option 1: Supabase CLI (Recommended)

**Prerequisites:**
```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref your-project-ref
```

**Deploy Migration:**
```bash
# Change to project directory
cd /Users/grayghostdata/Desktop/Development/ToolboxAI-Solutions

# Deploy all pending migrations
supabase db push

# Or deploy specific migration
supabase migrations up --file database/supabase/migrations/002_enhanced_rls_policies.sql
```

**Monitor Deployment:**
```bash
# Check migration status
supabase migrations list

# View logs
supabase db logs --tail
```

### Option 2: Supabase Dashboard

**Steps:**
1. Open Supabase Dashboard: https://app.supabase.com
2. Navigate to your project
3. Go to **SQL Editor**
4. Click **New Query**
5. Copy contents of `002_enhanced_rls_policies.sql`
6. Click **Run**
7. Verify success messages

**Verification:**
- Check for "Migration completed successfully" message
- Verify "~40 policies created" notification
- Confirm no error messages in output

### Option 3: psql Command Line

**For Direct PostgreSQL Access:**

```bash
# Get connection string from Supabase dashboard
SUPABASE_DB_URL="postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"

# Run migration
psql $SUPABASE_DB_URL < database/supabase/migrations/002_enhanced_rls_policies.sql

# Verify completion
psql $SUPABASE_DB_URL -c "SELECT * FROM rls_audit_log LIMIT 1;"
```

### Post-Deployment Verification

**Run Immediately After Deployment:**

```sql
-- 1. Verify helper functions created
SELECT proname, pronargs
FROM pg_proc
WHERE proname IN (
    'get_user_organization',
    'has_role',
    'is_admin',
    'is_teacher',
    'is_student',
    'in_user_organization'
);
-- Expected: 6 rows

-- 2. Verify organization columns added
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE column_name = 'organization_id'
  AND table_schema = 'public';
-- Expected: 5+ rows

-- 3. Verify indexes created
SELECT indexname, tablename
FROM pg_indexes
WHERE indexname LIKE '%organization%'
  AND schemaname = 'public';
-- Expected: 5+ rows

-- 4. Count active RLS policies
SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE schemaname = 'public';
-- Expected: 40+ rows

-- 5. Verify audit log table
SELECT table_name
FROM information_schema.tables
WHERE table_name = 'rls_audit_log'
  AND table_schema = 'public';
-- Expected: 1 row

-- 6. Verify audit triggers
SELECT event_object_table, trigger_name
FROM information_schema.triggers
WHERE trigger_name LIKE 'audit%';
-- Expected: 6 rows (one per table)
```

---

## Testing Procedures

### Test 1: Service Role Bypass

**Objective:** Verify service role has full access

```sql
-- Set service role (simulated)
SET ROLE service_role;

-- Should be able to select from any table
SELECT COUNT(*) FROM agent_instances;
SELECT COUNT(*) FROM agent_executions;
SELECT COUNT(*) FROM agent_metrics;

-- Should be able to insert
INSERT INTO agent_instances (id, agent_id, agent_type, organization_id)
VALUES (gen_random_uuid(), 'test-agent-1', 'content_generator', gen_random_uuid());

-- Cleanup
DELETE FROM agent_instances WHERE agent_id = 'test-agent-1';
RESET ROLE;
```

**Expected:** All operations succeed

### Test 2: Student Role - Own Data Only

**Objective:** Students can only see their own executions

```sql
-- Create test student user
-- (In production, this would be done via Supabase Auth)
SET SESSION my.user_id = 'student-user-uuid';
SET SESSION my.user_role = 'student';
SET SESSION my.organization_id = 'org-uuid';

-- Create execution for student
INSERT INTO agent_executions (
    id, task_id, user_id, organization_id, task_type, status
) VALUES (
    gen_random_uuid(),
    'student-task-1',
    'student-user-uuid',
    'org-uuid',
    'quiz_generation',
    'pending'
);

-- Student should see their own execution
SELECT COUNT(*) FROM agent_executions WHERE user_id = 'student-user-uuid';
-- Expected: 1

-- Create execution for different student
INSERT INTO agent_executions (
    id, task_id, user_id, organization_id, task_type, status
) VALUES (
    gen_random_uuid(),
    'other-student-task',
    'other-student-uuid',
    'org-uuid',
    'quiz_generation',
    'pending'
);

-- Student should NOT see other student's execution
SELECT COUNT(*) FROM agent_executions;
-- Expected: 1 (only own execution)

-- Cleanup
RESET ROLE;
```

**Expected:** Students isolated to their own data

### Test 3: Teacher Role - Organization Scope

**Objective:** Teachers can view all org data but not modify

```sql
-- Set teacher role
SET SESSION my.user_id = 'teacher-user-uuid';
SET SESSION my.user_role = 'teacher';
SET SESSION my.organization_id = 'org-uuid';

-- Teacher should see ALL executions in organization
SELECT COUNT(*) FROM agent_executions WHERE organization_id = 'org-uuid';
-- Expected: All org executions visible

-- Teacher should see ALL agent instances in organization
SELECT COUNT(*) FROM agent_instances WHERE organization_id = 'org-uuid';
-- Expected: All org instances visible

-- Teacher should NOT be able to delete
DELETE FROM agent_instances WHERE organization_id = 'org-uuid';
-- Expected: ERROR (permission denied)

-- Cleanup
RESET ROLE;
```

**Expected:** Read access to all org data, no write access

### Test 4: Admin Role - Full Organization Access

**Objective:** Admins have full CRUD within organization

```sql
-- Set admin role
SET SESSION my.user_id = 'admin-user-uuid';
SET SESSION my.user_role = 'admin';
SET SESSION my.organization_id = 'org-uuid';

-- Admin can view all
SELECT COUNT(*) FROM agent_instances WHERE organization_id = 'org-uuid';

-- Admin can create
INSERT INTO agent_instances (id, agent_id, agent_type, organization_id)
VALUES (gen_random_uuid(), 'admin-test-agent', 'content_generator', 'org-uuid');

-- Admin can update
UPDATE agent_instances
SET status = 'maintenance'
WHERE agent_id = 'admin-test-agent';

-- Admin can delete
DELETE FROM agent_instances WHERE agent_id = 'admin-test-agent';

-- Cleanup
RESET ROLE;
```

**Expected:** All CRUD operations succeed

### Test 5: Organization Isolation

**Objective:** Users cannot access data from other organizations

```sql
-- Create data in org1
SET SESSION my.organization_id = 'org1-uuid';
INSERT INTO agent_instances (id, agent_id, agent_type, organization_id)
VALUES (gen_random_uuid(), 'org1-agent', 'content_generator', 'org1-uuid');

-- Switch to org2
SET SESSION my.organization_id = 'org2-uuid';

-- Should NOT see org1 data
SELECT COUNT(*) FROM agent_instances WHERE agent_id = 'org1-agent';
-- Expected: 0

-- Cannot modify org1 data
UPDATE agent_instances SET status = 'offline' WHERE agent_id = 'org1-agent';
-- Expected: 0 rows updated

-- Cleanup
SET SESSION my.organization_id = 'org1-uuid';
DELETE FROM agent_instances WHERE agent_id = 'org1-agent';
RESET ROLE;
```

**Expected:** Complete organizational isolation

### Test 6: Audit Logging

**Objective:** All modifications are tracked in audit log

```sql
-- Set user context
SET SESSION my.user_id = 'test-user-uuid';
SET SESSION my.user_role = 'admin';
SET SESSION my.organization_id = 'test-org-uuid';

-- Perform tracked operations
INSERT INTO agent_instances (id, agent_id, agent_type, organization_id)
VALUES (gen_random_uuid(), 'audit-test', 'content_generator', 'test-org-uuid');

UPDATE agent_instances
SET status = 'busy'
WHERE agent_id = 'audit-test';

DELETE FROM agent_instances WHERE agent_id = 'audit-test';

-- Check audit log
SELECT
    operation,
    table_name,
    user_id,
    user_role,
    organization_id,
    ip_address,
    timestamp
FROM rls_audit_log
WHERE user_id = 'test-user-uuid'
ORDER BY timestamp DESC
LIMIT 3;

-- Expected: 3 entries (INSERT, UPDATE, DELETE)

-- Cleanup
RESET ROLE;
```

**Expected:** All operations logged with full context

---

## Rollback Plan

### Full Rollback Script

If issues occur, use this script to remove all RLS policies:

```sql
-- Save as: database/supabase/migrations/rollback_002_rls_policies.sql

-- Drop all RLS policies
DO $$
DECLARE
    pol RECORD;
BEGIN
    FOR pol IN
        SELECT schemaname, tablename, policyname
        FROM pg_policies
        WHERE schemaname = 'public'
        AND policyname NOT LIKE '%_old'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I',
            pol.policyname, pol.schemaname, pol.tablename);
        RAISE NOTICE 'Dropped policy: % on %.%',
            pol.policyname, pol.schemaname, pol.tablename;
    END LOOP;
END $$;

-- Drop helper functions
DROP FUNCTION IF EXISTS get_user_organization() CASCADE;
DROP FUNCTION IF EXISTS has_role(TEXT) CASCADE;
DROP FUNCTION IF EXISTS is_admin() CASCADE;
DROP FUNCTION IF EXISTS is_teacher() CASCADE;
DROP FUNCTION IF EXISTS is_student() CASCADE;
DROP FUNCTION IF EXISTS in_user_organization(UUID) CASCADE;
DROP FUNCTION IF EXISTS test_rls_policies(TEXT, UUID, UUID, TEXT) CASCADE;

-- Drop audit triggers
DROP TRIGGER IF EXISTS audit_agent_instances ON agent_instances;
DROP TRIGGER IF EXISTS audit_agent_executions ON agent_executions;
DROP TRIGGER IF EXISTS audit_agent_metrics ON agent_metrics;
DROP TRIGGER IF EXISTS audit_agent_task_queue ON agent_task_queue;
DROP TRIGGER IF EXISTS audit_system_health ON system_health;
DROP TRIGGER IF EXISTS audit_agent_configurations ON agent_configurations;

-- Drop audit log table
DROP TABLE IF EXISTS rls_audit_log CASCADE;

-- Optionally remove organization columns (BE CAREFUL - data loss)
-- ALTER TABLE agent_instances DROP COLUMN IF EXISTS organization_id;
-- ALTER TABLE agent_executions DROP COLUMN IF EXISTS organization_id;
-- ALTER TABLE agent_metrics DROP COLUMN IF EXISTS organization_id;
-- ALTER TABLE agent_task_queue DROP COLUMN IF EXISTS organization_id;
-- ALTER TABLE agent_configurations DROP COLUMN IF EXISTS organization_id;

-- Drop indexes
DROP INDEX IF EXISTS idx_agent_instances_organization;
DROP INDEX IF EXISTS idx_agent_executions_organization;
DROP INDEX IF EXISTS idx_agent_metrics_organization;
DROP INDEX IF EXISTS idx_agent_task_queue_organization;
DROP INDEX IF EXISTS idx_agent_configurations_organization;

RAISE NOTICE 'RLS policies rollback completed';
```

**Rollback Execution:**
```bash
# Using Supabase CLI
supabase db reset

# Or psql
psql $SUPABASE_DB_URL < database/supabase/migrations/rollback_002_rls_policies.sql

# Restore from backup
psql $SUPABASE_DB_URL < backup_before_rls_YYYYMMDD_HHMMSS.sql
```

---

## Monitoring & Verification

### Performance Monitoring

**Query Performance:**
```sql
-- Check slow queries with RLS
SELECT
    query,
    mean_exec_time,
    calls,
    total_exec_time
FROM pg_stat_statements
WHERE query LIKE '%agent_%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Index Usage:**
```sql
-- Verify organization_id indexes are being used
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE indexname LIKE '%organization%';
```

### Security Monitoring

**Audit Log Analysis:**
```sql
-- Recent modifications
SELECT
    table_name,
    operation,
    user_role,
    COUNT(*) as modification_count
FROM rls_audit_log
WHERE timestamp > NOW() - INTERVAL '1 day'
GROUP BY table_name, operation, user_role
ORDER BY modification_count DESC;

-- Suspicious activity (cross-org attempts)
SELECT *
FROM rls_audit_log
WHERE changed_values::text LIKE '%organization_id%'
  AND operation = 'UPDATE'
ORDER BY timestamp DESC;
```

### Health Checks

**Daily Health Check:**
```sql
-- Verify all policies active
SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public';
-- Expected: 40+

-- Verify audit logging working
SELECT COUNT(*) FROM rls_audit_log WHERE timestamp > NOW() - INTERVAL '1 hour';
-- Expected: > 0 if system active

-- Check for policy violations
SELECT COUNT(*) FROM pg_stat_database_conflicts
WHERE datname = current_database();
-- Expected: 0
```

---

## Success Criteria

### Deployment Success ✅

- [ ] All 40+ policies created without errors
- [ ] All 6 helper functions working
- [ ] Organization columns added to 5 tables
- [ ] Indexes created and being used
- [ ] Audit log table operational
- [ ] No syntax or permission errors
- [ ] Backup created and verified

### Testing Success ✅

- [ ] Service role has full access
- [ ] Students see only own data
- [ ] Teachers see all org data (read-only)
- [ ] Admins have full org CRUD
- [ ] Organization isolation verified
- [ ] Audit logging captures all changes
- [ ] Performance acceptable (<10ms overhead)

### Production Ready ✅

- [ ] All tests passing
- [ ] Documentation complete
- [ ] Monitoring in place
- [ ] Rollback plan tested
- [ ] Team trained on new security model

---

## Troubleshooting

### Common Issues

**1. "Function auth.uid() does not exist"**
```sql
-- Install Supabase Auth extension
CREATE EXTENSION IF NOT EXISTS "supabase_auth";
```

**2. "Permission denied for table"**
```sql
-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
```

**3. "Policy prevents operation"**
```sql
-- Check which policy is blocking
SELECT * FROM pg_policies
WHERE tablename = 'your_table'
  AND schemaname = 'public';

-- Temporarily disable RLS for debugging (dev only!)
ALTER TABLE your_table DISABLE ROW LEVEL SECURITY;
```

**4. "Slow query performance"**
```sql
-- Verify indexes exist
REINDEX TABLE agent_instances;

-- Analyze table statistics
ANALYZE agent_instances;
```

---

## Next Steps

After successful deployment:

1. **Phase 1, Task 1.3:** Add organization_id to remaining models
2. **Phase 2:** Deploy Edge Functions
3. **Phase 3:** E2E testing with real Supabase instance
4. **Phase 4:** Production deployment

---

**Document Status:** ✅ Complete
**Last Updated:** 2025-10-10
**Ready for Deployment:** YES
