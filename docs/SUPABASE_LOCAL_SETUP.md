# Supabase Local Development Setup

This guide explains how to set up and use Supabase locally for development.

## 🎯 Overview

**Local Supabase** provides a complete Supabase stack running on your machine:
- PostgreSQL database on port 54322
- API server on port 54321
- Studio UI on port 54323
- Email testing with Mailpit on port 54324
- S3-compatible storage
- GraphQL API
- MCP (Model Context Protocol) endpoint

## 📋 Prerequisites

1. **Docker Desktop** (or Docker Engine)
   ```bash
   # Check if Docker is running
   docker --version
   ```

2. **Supabase CLI**
   ```bash
   # Install with npm
   npm install -g supabase

   # Or with Homebrew (macOS)
   brew install supabase/tap/supabase

   # Verify installation
   supabase --version
   ```

## 🚀 Quick Start

### 1. Start Supabase

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Start all Supabase services
supabase start
```

**Expected Output:**
```
Started supabase local development setup.

         API URL: http://127.0.0.1:54321
     GraphQL URL: http://127.0.0.1:54321/graphql/v1
  S3 Storage URL: http://127.0.0.1:54321/storage/v1/s3
         MCP URL: http://127.0.0.1:54321/mcp
    Database URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
      Studio URL: http://127.0.0.1:54323
     Mailpit URL: http://127.0.0.1:54324
 Publishable key: sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH
      Secret key: sb_secret_N7UND0UgjKTVK-Uodkm0Hg_xSvEMPvz
   S3 Access Key: 625729a08b95bf1b7ff351a663f3a23c
   S3 Secret Key: 850181e4652dd023b7a98c58ae0d2d34bd487ee0cc3254aed6eda37307425907
       S3 Region: local
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.supabase.local.example .env.local

# The file contains all necessary configuration
```

### 3. Run Your Application

**Backend:**
```bash
cd apps/backend

# Activate virtual environment
source ../../venv/bin/activate  # or venv_clean/bin/activate

# Run development server
uvicorn main:app --reload --port 8009
```

**Frontend:**
```bash
cd apps/dashboard

# Install dependencies (if needed)
npm install

# Run development server
npm run dev
```

### 4. Access Services

- **Backend API**: http://localhost:8009
- **Frontend Dashboard**: http://localhost:5179
- **Supabase Studio**: http://127.0.0.1:54323
- **Mailpit (Email Testing)**: http://127.0.0.1:54324
- **GraphQL Playground**: http://127.0.0.1:54321/graphql/v1

## 🗄️ Database Management

### Access PostgreSQL

**Via psql:**
```bash
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

**Via Supabase Studio:**
1. Open http://127.0.0.1:54323
2. Navigate to "SQL Editor"
3. Run queries directly in the UI

### Run Migrations

```bash
# Create a new migration
supabase migration new create_users_table

# Apply migrations
supabase db push

# Reset database (WARNING: Deletes all data!)
supabase db reset
```

### Seed Data

Create `supabase/seed.sql`:
```sql
-- Insert test data
INSERT INTO users (email, name) VALUES
  ('test@example.com', 'Test User'),
  ('admin@example.com', 'Admin User');
```

Apply seed:
```bash
supabase db reset  # Includes seed.sql automatically
```

## 📦 Storage Management

### Create Storage Bucket

**Via Supabase Studio:**
1. Open http://127.0.0.1:54323
2. Go to "Storage"
3. Click "Create bucket"
4. Name: `toolboxai-uploads`
5. Set public/private as needed

**Via SQL:**
```sql
-- Create bucket
INSERT INTO storage.buckets (id, name, public)
VALUES ('toolboxai-uploads', 'toolboxai-uploads', true);

-- Set policies
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
USING (bucket_id = 'toolboxai-uploads');
```

### Test File Upload

**Python:**
```python
from supabase import create_client

supabase = create_client(
    "http://127.0.0.1:54321",
    "sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH"
)

# Upload file
with open("test.txt", "rb") as f:
    supabase.storage.from_("toolboxai-uploads").upload(
        "test.txt",
        f
    )
```

## 📧 Email Testing with Mailpit

All emails sent by your application are captured by Mailpit:

1. Open http://127.0.0.1:54324
2. View all sent emails
3. Test email templates
4. Inspect HTML and plain text versions

**No emails are actually sent** - perfect for development!

## 🔐 Authentication Testing

### Test User Creation

**Via Supabase Studio:**
1. Open http://127.0.0.1:54323
2. Go to "Authentication" → "Users"
3. Click "Add user"
4. Create test account

**Via API:**
```bash
curl -X POST http://127.0.0.1:54321/auth/v1/signup \
  -H "apikey: sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### Check Confirmation Email

1. Open Mailpit: http://127.0.0.1:54324
2. Find confirmation email
3. Click confirmation link (auto-confirmed in local dev)

## 🛠️ Common Commands

```bash
# Start Supabase
supabase start

# Stop Supabase
supabase stop

# Check status
supabase status

# View logs
supabase logs

# Reset database
supabase db reset

# Generate TypeScript types
supabase gen types typescript --local > types/supabase.ts

# Link to remote project (for migrations)
supabase link --project-ref <your-project-ref>

# Pull remote schema to local
supabase db pull

# Push local migrations to remote
supabase db push
```

## 🔄 Development Workflow

### Typical Daily Workflow

```bash
# 1. Start Supabase
supabase start

# 2. Start backend
cd apps/backend
source ../../venv/bin/activate
uvicorn main:app --reload --port 8009

# 3. Start frontend (new terminal)
cd apps/dashboard
npm run dev

# 4. Develop your features...

# 5. When done for the day
supabase stop
```

### Making Database Changes

```bash
# 1. Create migration
supabase migration new add_profile_table

# 2. Edit the migration file in supabase/migrations/
# Add your SQL

# 3. Apply migration
supabase db reset  # or: supabase db push

# 4. Generate types
supabase gen types typescript --local > types/supabase.ts
```

## 🚨 Troubleshooting

### Port Already in Use

```bash
# Check what's using port 54321
lsof -i :54321

# Kill the process
kill -9 <PID>

# Or use different ports
supabase start --port 54325
```

### Docker Issues

```bash
# Restart Docker Desktop

# Or reset Supabase completely
supabase stop
docker system prune -a
supabase start
```

### Database Connection Failed

```bash
# Check if PostgreSQL container is running
docker ps | grep supabase-db

# View database logs
supabase logs db

# Reset database
supabase db reset
```

### Studio Not Loading

```bash
# Clear browser cache
# Or try incognito mode

# Check Studio logs
supabase logs studio
```

## 📊 Monitoring & Debugging

### View Logs

```bash
# All services
supabase logs

# Specific service
supabase logs api
supabase logs db
supabase logs storage
```

### Database Queries

```sql
-- View active connections
SELECT * FROM pg_stat_activity;

-- View table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🌐 Production vs Local

| Feature | Local | Production |
|---------|-------|------------|
| API URL | http://127.0.0.1:54321 | https://[project].supabase.co |
| Database | postgresql://...@127.0.0.1:54322 | postgresql://...supabase.co:5432 |
| Keys | Local dev keys | Production keys (secret!) |
| Email | Mailpit (captured) | Real SMTP (sent) |
| Storage | Local filesystem | Cloud storage |
| Backups | Manual | Automatic daily |

## 🔗 Integration with Backend

Your backend should detect local vs production automatically:

```python
import os

# Auto-detect environment
SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "http://127.0.0.1:54321"  # Default to local
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY",
    "sb_secret_N7UND0UgjKTVK-Uodkm0Hg_xSvEMPvz"  # Local dev key
)

# Check if we're in local development
IS_LOCAL = "127.0.0.1" in SUPABASE_URL

if IS_LOCAL:
    print("🔧 Using LOCAL Supabase")
else:
    print("🚀 Using PRODUCTION Supabase")
```

## 📚 Additional Resources

- **Supabase CLI Docs**: https://supabase.com/docs/guides/cli
- **Local Development**: https://supabase.com/docs/guides/cli/local-development
- **Migrations**: https://supabase.com/docs/guides/cli/migrations
- **Studio**: https://supabase.com/docs/guides/platform/studio

## ⚠️ Security Notes

1. **Never commit real credentials** - Use `.env.local` (in `.gitignore`)
2. **Local keys are safe** - They only work on localhost
3. **Production keys are secret** - Never share or commit them
4. **Reset production keys** if accidentally exposed

---

**Status**: ✅ Supabase local development environment ready for use!
