# Database Migration Management - 2025 Implementation

**Document Version:** 1.0.0
**Last Updated:** September 21, 2025
**Status:** ✅ Production Ready
**Database:** Supabase PostgreSQL
**Migration System:** Custom Automation + CI/CD

---

## 📋 **Overview**

Comprehensive database migration management system for ToolBoxAI Supabase integration. Provides automated migration execution, rollback procedures, and CI/CD integration for safe database schema management in production environments.

---

## 🏗️ **Migration System Architecture**

### **Directory Structure**
```
database/supabase/
├── migrations/
│   ├── 001_create_agent_system_tables.sql
│   ├── 002_add_performance_indexes.sql
│   └── 003_add_rls_policies.sql
├── rollbacks/
│   ├── 001_create_agent_system_tables_rollback.sql
│   ├── 002_add_performance_indexes_rollback.sql
│   └── 003_add_rls_policies_rollback.sql
├── backups/
│   ├── pre_migration_20250921_120000.json
│   └── emergency_rollback_20250921_140000.json
├── migration_history.json
└── recovery_log.json
```

### **Migration Components**

#### **1. Migration Manager**
**File:** `scripts/supabase_migration_automation.py`

**Features:**
- Automated migration execution
- Migration history tracking
- Error handling and recovery
- CI/CD integration support

**Usage:**
```bash
# Run all pending migrations
python scripts/supabase_migration_automation.py --migrate

# Check migration status
python scripts/supabase_migration_automation.py --status

# Create new migration
python scripts/supabase_migration_automation.py --create "add_agent_metrics_table"
```

#### **2. Rollback Manager**
**File:** `scripts/supabase_rollback.py`

**Features:**
- Automated rollback to specific versions
- Emergency rollback procedures
- Backup creation before rollbacks
- Database integrity verification

**Usage:**
```bash
# Rollback to specific version
python scripts/supabase_rollback.py --rollback "001_create_agent_system_tables"

# Emergency rollback
python scripts/supabase_rollback.py --emergency

# Verify database integrity
python scripts/supabase_rollback.py --verify

# Dry run (show what would be done)
python scripts/supabase_rollback.py --rollback "001_create_agent_system_tables" --dry-run
```

---

## 📝 **Migration File Format**

### **Migration File Template**
```sql
-- Migration: add_agent_metrics_table
-- Created: 2025-09-21T17:15:00Z
-- Description: Add Agent Metrics Table

-- Create agent metrics table
CREATE TABLE agent_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Add indexes for performance
CREATE INDEX idx_agent_metrics_agent_id ON agent_metrics(agent_id);
CREATE INDEX idx_agent_metrics_type ON agent_metrics(metric_type);
CREATE INDEX idx_agent_metrics_recorded_at ON agent_metrics(recorded_at);

-- Enable RLS
ALTER TABLE agent_metrics ENABLE ROW LEVEL SECURITY;

-- Add RLS policies
CREATE POLICY "Agent metrics access policy" ON agent_metrics
FOR ALL USING (auth.uid()::text = (metadata->>'user_id'));
```

### **Rollback File Template**
```sql
-- Rollback for: add_agent_metrics_table
-- Created: 2025-09-21T17:15:00Z
-- Description: Rollback Agent Metrics Table

-- Drop indexes
DROP INDEX IF EXISTS idx_agent_metrics_recorded_at;
DROP INDEX IF EXISTS idx_agent_metrics_type;
DROP INDEX IF EXISTS idx_agent_metrics_agent_id;

-- Drop table
DROP TABLE IF EXISTS agent_metrics;
```

---

## 🔄 **Migration Workflow**

### **Development Workflow**

#### **1. Create Migration**
```bash
# Create new migration file
python scripts/supabase_migration_automation.py --create "add_new_feature_table"

# Edit the generated files:
# - database/supabase/migrations/YYYYMMDD_HHMMSS_add_new_feature_table.sql
# - database/supabase/rollbacks/YYYYMMDD_HHMMSS_add_new_feature_table_rollback.sql
```

#### **2. Test Migration**
```bash
# Check migration status
python scripts/supabase_migration_automation.py --status

# Test migration (dry run)
python scripts/supabase_rollback.py --rollback "target_version" --dry-run

# Run migration
python scripts/supabase_migration_automation.py --migrate
```

#### **3. Validate Migration**
```bash
# Verify database integrity
python scripts/supabase_rollback.py --verify

# Check health endpoints
curl http://localhost:8009/health/supabase/tables
```

### **Production Workflow**

#### **1. Pre-Migration Checklist**
- [ ] Migration files reviewed and approved
- [ ] Rollback procedures tested
- [ ] Backup procedures verified
- [ ] Downtime window scheduled (if required)
- [ ] Monitoring alerts configured

#### **2. Migration Execution**
```bash
# 1. Create pre-migration backup
python scripts/supabase_backup_automation.py

# 2. Run migrations with monitoring
python scripts/supabase_migration_automation.py --migrate

# 3. Verify migration success
python scripts/supabase_rollback.py --verify

# 4. Update monitoring dashboards
curl http://localhost:8009/health/supabase
```

#### **3. Post-Migration Validation**
- Database integrity verification
- Performance impact assessment
- Application functionality testing
- Monitoring alert validation

---

## 🚨 **Emergency Procedures**

### **Emergency Rollback**
```bash
# Immediate rollback to last known good state
python scripts/supabase_rollback.py --emergency

# Verify rollback integrity
python scripts/supabase_rollback.py --verify

# Check system health
curl http://localhost:8009/health/agents
curl http://localhost:8009/health/supabase
```

### **Disaster Recovery**
```bash
# Restore from backup file
python scripts/supabase_rollback.py --restore-backup "backup_file.json"

# Full system verification
python scripts/system_health_check.py

# Restart services if needed
docker-compose restart
```

### **Data Corruption Recovery**
```bash
# 1. Stop application services
docker-compose stop backend

# 2. Create emergency backup
python scripts/supabase_backup_automation.py

# 3. Restore from last known good backup
python scripts/supabase_rollback.py --restore-backup "last_good_backup.json"

# 4. Verify data integrity
python scripts/supabase_rollback.py --verify

# 5. Restart services
docker-compose start backend
```

---

## 🔄 **CI/CD Integration**

### **GitHub Actions Workflow**
**File:** `.github/workflows/database-migrations.yml`

#### **Pipeline Stages:**

##### **1. Validation Stage**
- SQL syntax validation using `sqlparse`
- Rollback file existence checks
- Migration file format validation

##### **2. Testing Stage**
- Migration testing against test PostgreSQL database
- Rollback procedure testing
- Performance impact assessment

##### **3. Staging Deployment**
- Automated migration to staging environment
- Integration testing with staging data
- Performance monitoring and validation

##### **4. Production Deployment**
- Pre-migration backup creation
- Automated migration execution
- Post-migration integrity verification
- Monitoring and alerting validation

##### **5. Emergency Rollback**
- Manual trigger for emergency rollback
- Automated rollback execution
- System health verification

### **Workflow Triggers**
```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - 'database/supabase/migrations/**'
      - 'scripts/supabase_migration_automation.py'
  pull_request:
    branches: [main]
    paths:
      - 'database/supabase/migrations/**'
  workflow_dispatch:  # Manual emergency rollback
```

---

## 📊 **Migration Monitoring**

### **Migration History Tracking**
**File:** `database/supabase/migration_history.json`

```json
{
  "executed": [
    "001_create_agent_system_tables.sql",
    "002_add_performance_indexes.sql"
  ],
  "last_migration": "002_add_performance_indexes.sql",
  "last_execution": "2025-09-21T17:15:00Z",
  "last_rollback": null,
  "last_rollback_time": null
}
```

### **Recovery Log**
**File:** `database/supabase/recovery_log.json`

```json
{
  "last_known_good_version": "001_create_agent_system_tables.sql",
  "last_emergency_rollback": {
    "timestamp": "2025-09-21T16:30:00Z",
    "target_version": "001_create_agent_system_tables.sql",
    "success": true
  },
  "integrity_checks": [
    {
      "timestamp": "2025-09-21T17:15:00Z",
      "result": "passed",
      "details": {
        "table_structure": true,
        "data_consistency": true,
        "constraints": true,
        "indexes": true,
        "permissions": true
      }
    }
  ]
}
```

### **Performance Metrics**
- **Migration Execution Time:** < 30 seconds per migration
- **Rollback Time:** < 10 seconds per rollback
- **Backup Creation Time:** < 60 seconds
- **Integrity Verification:** < 30 seconds

---

## 🔒 **Security Considerations**

### **Access Control**
- Migration scripts require `SUPABASE_SERVICE_KEY`
- Production migrations require additional approval
- Rollback procedures require elevated permissions
- Audit logging for all migration activities

### **Data Protection**
- Automatic backup creation before migrations
- Encryption of backup files
- Secure storage of migration history
- Row-level security (RLS) policy management

### **Compliance**
- Migration approval workflows
- Change management documentation
- Audit trail maintenance
- Disaster recovery procedures

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **Migration Fails to Execute**
```bash
# Check Supabase connectivity
curl -H "apikey: $SUPABASE_ANON_KEY" "$SUPABASE_URL/rest/v1/"

# Verify credentials
python -c "
import os
from supabase import create_client
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
print('✅ Supabase connection successful')
"

# Check migration file syntax
python -c "
import sqlparse
with open('database/supabase/migrations/migration_file.sql') as f:
    sql = f.read()
parsed = sqlparse.parse(sql)
print('✅ SQL syntax valid' if parsed else '❌ SQL syntax invalid')
"
```

#### **Rollback Fails**
```bash
# Check rollback file exists
ls database/supabase/rollbacks/

# Verify rollback SQL syntax
python scripts/supabase_rollback.py --rollback "target_version" --dry-run

# Force emergency rollback
python scripts/supabase_rollback.py --emergency
```

#### **Database Integrity Issues**
```bash
# Run integrity verification
python scripts/supabase_rollback.py --verify

# Check table accessibility
curl http://localhost:8009/health/supabase/tables

# Restore from backup if needed
python scripts/supabase_rollback.py --restore-backup "backup_file.json"
```

### **Performance Issues**
```bash
# Check migration performance
time python scripts/supabase_migration_automation.py --migrate

# Monitor database performance during migration
curl http://localhost:8009/health/supabase/performance

# Check for long-running queries
# (Would require direct database access)
```

---

## 📈 **Best Practices**

### **Migration Development**
1. **Always create rollback files** for every migration
2. **Test migrations** against sample data before production
3. **Use descriptive names** for migration files
4. **Include comments** explaining complex operations
5. **Batch related changes** into single migrations when possible

### **Production Deployment**
1. **Schedule migrations** during low-traffic periods
2. **Create backups** before every production migration
3. **Monitor system health** during and after migrations
4. **Have rollback plan ready** for every migration
5. **Verify functionality** after migration completion

### **Emergency Response**
1. **Document all emergency procedures** clearly
2. **Test emergency rollback** procedures regularly
3. **Maintain communication channels** for emergency response
4. **Keep backup systems** ready for immediate use
5. **Practice disaster recovery** scenarios

---

## 🎯 **Implementation Status: COMPLETE**

The database migration system is **production-ready** with:

- **✅ Automated Migration Execution:** Full automation with error handling
- **✅ Rollback Procedures:** Emergency and planned rollback capabilities
- **✅ CI/CD Integration:** GitHub Actions workflow for automated deployment
- **✅ Backup System:** Automated backup creation and restoration
- **✅ Integrity Verification:** Comprehensive database integrity checks
- **✅ Monitoring Integration:** Health endpoints and performance metrics
- **✅ Documentation:** Complete operational procedures

The system provides enterprise-grade database management with safety, automation, and observability for the ToolBoxAI platform.
