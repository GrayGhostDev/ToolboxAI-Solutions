# Supabase Integration Guide

## Overview

This guide covers the integration of Supabase as the primary database service for ToolboxAI, leveraging its built-in high availability, automated backups, and managed PostgreSQL features.

## Architecture

```
┌─────────────────────────────────────────┐
│         Application Layer                │
│   (Backend, Workers, MCP Servers)        │
└──────────────┬──────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│      Supabase Connection Pool            │
│         (PgBouncer Built-in)             │
└──────────────┬──────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│         Supabase PostgreSQL              │
│    (Managed HA with Replicas)            │
│    - Primary (Read/Write)                │
│    - Replica (Read-only)                 │
│    - Automated Backups                   │
│    - Point-in-Time Recovery              │
└──────────────────────────────────────────┘
```

## Benefits of Supabase

1. **Built-in High Availability**
   - Automatic failover
   - Read replicas
   - No manual configuration needed

2. **Automated Backups**
   - Daily automated backups
   - Point-in-Time Recovery (PITR)
   - Up to 30 days retention

3. **Connection Pooling**
   - Built-in PgBouncer
   - Optimized for serverless
   - No separate pooler needed

4. **Security**
   - SSL/TLS by default
   - Row Level Security (RLS)
   - API authentication
   - IP allowlisting

5. **Monitoring**
   - Built-in dashboard
   - Query performance insights
   - Resource usage metrics

---

## Setup Instructions

### 1. Create Supabase Project

#### Development/Staging
```bash
# Already configured in supabase/config.toml
cd supabase
supabase start
```

#### Production
1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Create new project:
   - **Name**: toolboxai-production
   - **Region**: Closest to your users
   - **Database Password**: Generate strong password (store in Vault)
   - **Plan**: Pro (for PITR and better performance)

3. Note your credentials:
   - Project URL: `https://[project-id].supabase.co`
   - Anon Key: `eyJ...` (public)
   - Service Role Key: `eyJ...` (secret - store in Vault)
   - Database URL: `postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres`

### 2. Store Credentials in Vault

```bash
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="<your-vault-token>"

# Store Supabase credentials
vault kv put secret/toolboxai/supabase \
  url="https://[project-id].supabase.co" \
  anon_key="eyJ..." \
  service_role_key="eyJ..." \
  database_url="postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres" \
  jwt_secret="your-jwt-secret"

# Store database password separately
vault kv put secret/toolboxai/database \
  password="<supabase-db-password>" \
  provider="supabase" \
  connection_pool_size=20
```

### 3. Configure Environment Variables

Update `.env.production`:

```bash
# Supabase Configuration
SUPABASE_ENABLED=true
SUPABASE_URL=https://[project-id].supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret

# Database Configuration
DATABASE_URL=postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres
DATABASE_POOL_SIZE=20
DATABASE_SSL_MODE=require

# Connection Pooling (Supabase Pooler)
SUPABASE_POOLER_URL=postgresql://postgres:[password]@pooler.db.[project-id].supabase.co:6543/postgres
USE_POOLER=true
```

### 4. Update Docker Compose

Since we're using Supabase, we'll remove the local PostgreSQL container and PgBouncer:

```yaml
# infrastructure/docker/compose/docker-compose.supabase.yml
version: '3.9'

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
  cache:
    driver: bridge
    internal: true

services:
  # Backend now connects to Supabase directly
  backend:
    build:
      context: ../../
      dockerfile: infrastructure/docker/dockerfiles/backend.Dockerfile
    container_name: toolboxai-backend
    restart: unless-stopped
    environment:
      # Supabase configuration
      DATABASE_URL: ${SUPABASE_POOLER_URL}
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
      SUPABASE_SERVICE_KEY_FILE: /run/secrets/supabase_service_key
      
      # Other configuration
      REDIS_URL: rediss://toolboxai_backend@redis:6380
      VAULT_ADDR: http://vault:8200
      NODE_ENV: production
    secrets:
      - supabase_service_key
    networks:
      - backend
      - cache
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis remains the same (from Phase 1)
  redis:
    image: redis:7-alpine
    container_name: toolboxai-redis
    restart: unless-stopped
    command: redis-server /etc/redis/redis.conf
    volumes:
      - redis_data:/data
      - ../config/redis/redis.conf:/etc/redis/redis.conf:ro
      - ../config/redis/users.acl:/etc/redis/users.acl:ro
      - ../certificates/redis:/etc/redis/certs:ro
    networks:
      - cache
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "--tls", "-p", "6380", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

secrets:
  supabase_service_key:
    external: true

volumes:
  redis_data:
```

---

## Database Migration

### 1. Export Existing Schema

```bash
# If migrating from local PostgreSQL
pg_dump -h localhost -U toolboxai -d toolboxai \
  --schema-only \
  --no-owner \
  --no-privileges \
  > schema.sql

# Export data
pg_dump -h localhost -U toolboxai -d toolboxai \
  --data-only \
  --no-owner \
  --no-privileges \
  > data.sql
```

### 2. Create Supabase Migration

```bash
# Initialize Supabase CLI
supabase init

# Create migration
supabase migration new initial_schema

# Edit migration file
cat schema.sql > supabase/migrations/[timestamp]_initial_schema.sql

# Apply migration
supabase db push
```

### 3. Import Data

```bash
# Using psql
PGPASSWORD=[password] psql \
  -h db.[project-id].supabase.co \
  -U postgres \
  -d postgres \
  < data.sql

# Or using Supabase dashboard
# Go to Table Editor > Import Data
```

---

## Row Level Security (RLS)

### Enable RLS on Tables

```sql
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view own data"
  ON users
  FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own data"
  ON users
  FOR UPDATE
  USING (auth.uid() = id);

-- Project access policy
CREATE POLICY "Users can view own projects"
  ON projects
  FOR SELECT
  USING (
    owner_id = auth.uid() OR
    id IN (
      SELECT project_id FROM project_members
      WHERE user_id = auth.uid()
    )
  );
```

---

## Connection Pooling

### Supabase Pooler (Recommended)

Supabase provides built-in PgBouncer:

```python
# Python/FastAPI
from sqlalchemy import create_engine

# Use pooler URL for high-traffic applications
DATABASE_URL = os.getenv('SUPABASE_POOLER_URL')

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Configuration

```bash
# Enable Supabase Pooler in dashboard
# Settings > Database > Connection Pooling
# Mode: Transaction (recommended)
# Pool Size: 20
```

---

## Backup & Recovery

### Automated Backups

Supabase automatically backs up your database:
- **Frequency**: Daily
- **Retention**: 7 days (Starter), 30 days (Pro)
- **PITR**: Available on Pro plan

### Point-in-Time Recovery

```bash
# Using Supabase CLI
supabase db restore --time "2025-11-07T10:30:00Z"

# Or via dashboard
# Settings > Database > Backups > Restore to point in time
```

### Manual Backups

Create additional backups:

```bash
# Create backup script
#!/bin/bash
# infrastructure/scripts/backup-supabase.sh

PROJECT_ID="your-project-id"
DB_PASSWORD="$(vault kv get -field=password secret/toolboxai/database)"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/supabase"

mkdir -p "$BACKUP_DIR"

# Backup with pg_dump
PGPASSWORD="$DB_PASSWORD" pg_dump \
  -h db.${PROJECT_ID}.supabase.co \
  -U postgres \
  -d postgres \
  --format=custom \
  --compress=9 \
  -f "${BACKUP_DIR}/backup_${DATE}.dump"

# Upload to S3
aws s3 cp "${BACKUP_DIR}/backup_${DATE}.dump" \
  s3://your-backup-bucket/supabase/

# Clean up old local backups (keep 7 days)
find "$BACKUP_DIR" -name "backup_*.dump" -mtime +7 -delete

echo "Backup completed: backup_${DATE}.dump"
```

Make it executable and schedule:

```bash
chmod +x infrastructure/scripts/backup-supabase.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /path/to/infrastructure/scripts/backup-supabase.sh
```

---

## Monitoring

### Supabase Dashboard

Access monitoring at: `https://app.supabase.com/project/[project-id]/reports`

Metrics available:
- Database CPU usage
- Memory usage
- Connection count
- Query performance
- Slow queries
- API usage

### Custom Monitoring

```python
# Python health check
import psycopg2

def check_supabase_health():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        conn.close()
        return {"status": "healthy", "provider": "supabase"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

---

## Performance Optimization

### Indexes

Create indexes for common queries:

```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_clerk_id ON users(clerk_id);

-- Project queries
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_projects_created ON projects(created_at DESC);

-- Workspace queries
CREATE INDEX idx_workspaces_user ON workspace_members(user_id);
```

### Query Optimization

Use the Supabase query analyzer:

```sql
-- Check query plan
EXPLAIN ANALYZE
SELECT * FROM projects WHERE owner_id = 'user-id';

-- Use prepared statements
PREPARE get_user_projects AS
SELECT * FROM projects WHERE owner_id = $1;

EXECUTE get_user_projects('user-id');
```

---

## Security Best Practices

1. **Use Service Role Key Carefully**
   - Only use in backend
   - Never expose to frontend
   - Store in Vault

2. **Enable SSL**
   - Always use `sslmode=require`
   - Verify certificates in production

3. **Row Level Security**
   - Enable on all tables
   - Test policies thoroughly
   - Audit regularly

4. **API Keys Rotation**
   - Rotate service role keys quarterly
   - Update in Vault
   - Redeploy services

5. **IP Allowlisting**
   - Configure in Supabase dashboard
   - Add application server IPs
   - Monitor unauthorized access

---

## Troubleshooting

### Connection Issues

```bash
# Test connection
psql "postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres"

# Check SSL
psql "postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres?sslmode=require"

# Test pooler
psql "postgresql://postgres:[password]@pooler.db.[project-id].supabase.co:6543/postgres"
```

### Performance Issues

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;

-- Kill long-running query
SELECT pg_terminate_backend(pid);
```

### Backup/Restore Issues

```bash
# Verify backup
pg_restore --list backup_20251107.dump

# Test restore to local
createdb test_restore
pg_restore -d test_restore backup_20251107.dump

# Check data
psql test_restore -c "SELECT count(*) FROM users;"
```

---

## Cost Optimization

### Pro Plan Features ($25/month)
- 8 GB database
- 100 GB bandwidth
- Point-in-Time Recovery
- Daily backups
- Read replicas

### Optimization Tips
1. Use connection pooling
2. Optimize queries and indexes
3. Archive old data
4. Use appropriate column types
5. Monitor and tune regularly

---

## References

- [Supabase Documentation](https://supabase.com/docs)
- [Connection Pooling Guide](https://supabase.com/docs/guides/database/connection-pooling)
- [Point-in-Time Recovery](https://supabase.com/docs/guides/platform/backups)
- [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)

