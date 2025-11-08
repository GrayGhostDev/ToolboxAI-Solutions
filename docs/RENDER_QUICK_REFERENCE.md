# Render Deployment Quick Reference

**One-page reference for common deployment tasks**

---

## 🔗 Essential URLs

| Service | URL |
|---------|-----|
| **Production Dashboard** | https://toolboxai-dashboard.onrender.com |
| **Backend API** | https://toolboxai-backend.onrender.com |
| **Backend Health** | https://toolboxai-backend.onrender.com/health |
| **API Docs** | https://toolboxai-backend.onrender.com/docs |
| **Celery Monitoring** | https://toolboxai-celery-flower.onrender.com |
| **Render Dashboard** | https://dashboard.render.com |
| **Supabase Dashboard** | https://supabase.com/dashboard |
| **Sentry Dashboard** | https://sentry.io |

---

## 🔐 Get Supabase Credentials (Production)

### Quick Steps:
1. Go to: https://supabase.com/dashboard → Your Project
2. **Project Settings** → **API**:
   - Copy Project URL
   - Copy anon/public key
   - Copy service_role key
3. **Project Settings** → **Database** → **Connection pooling**:
   - Mode: Transaction
   - Copy connection string (port **6543**)

### Connection String Format:
```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

---

## 🔑 Generate Security Tokens

```bash
# 64-character hex tokens (for JWT, SECRET, ENCRYPTION keys)
openssl rand -hex 32

# 32-character base64 passwords (for Grafana, Flower)
openssl rand -base64 24

# Generate all three security tokens at once
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)"
echo "SECRET_KEY=$(openssl rand -hex 32)"
echo "ENCRYPTION_KEY=$(openssl rand -hex 32)"
```

---

## ✅ Validate Configuration

```bash
# Navigate to project
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Validate environment variables
python scripts/validate_render_env.py

# Validate specific file
python scripts/validate_render_env.py --env-file .env.production

# Quiet mode (summary only)
python scripts/validate_render_env.py --quiet
```

---

## 🚀 Deploy to Render

### Option 1: Dashboard (Recommended)
1. Go to: https://dashboard.render.com → **Blueprints**
2. **New Blueprint Instance**
3. Repository: **GrayGhostDev/ToolboxAI-Solutions**
4. Branch: **main**
5. Blueprint: `infrastructure/render/render.production.yaml`
6. Configure environment variable groups
7. Click **Apply**

### Option 2: CLI
```bash
# Install Render CLI
npm install -g @render/cli

# Login
render login

# Deploy blueprint
render deploy --blueprint infrastructure/render/render.production.yaml
```

---

## 📊 Service Overview

| Service | Type | Plan | Cost | Port |
|---------|------|------|------|------|
| toolboxai-backend | Web | Starter | $7 | 8000 |
| toolboxai-redis | Redis | Starter | $10 | 6379 |
| toolboxai-dashboard | Static | Free | $0 | - |
| toolboxai-mcp | Web | Starter | $7 | 8001 |
| toolboxai-agent-coordinator | Web | Starter | $7 | 8002 |
| toolboxai-celery-worker | Worker | Starter | $7 | - |
| toolboxai-celery-beat | Worker | Starter | $7 | - |
| toolboxai-celery-flower | Web | Starter | $7 | 5555 |
| toolboxai-monitoring | Worker | Starter | $7 | - |
| toolboxai-cleanup | Cron | Free | $0 | - |
| **Total** | | | **$59/mo** | |

---

## 🔍 Health Check Commands

```bash
# Backend health
curl https://toolboxai-backend.onrender.com/health

# MCP health
curl https://toolboxai-mcp.onrender.com/health

# Agent Coordinator health
curl https://toolboxai-agent-coordinator.onrender.com/health

# All at once
for service in backend mcp agent-coordinator; do
  echo "Checking toolboxai-$service..."
  curl -s https://toolboxai-$service.onrender.com/health | jq
done
```

---

## 📋 Required Environment Variables

### Supabase (5 variables)
```bash
SUPABASE_URL=https://[project].supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres.[project]:...@...pooler.supabase.com:6543/postgres
SUPABASE_STORAGE_BUCKET=toolboxai-uploads
```

### AI APIs (3 variables)
```bash
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...
GOOGLE_API_KEY=AIzaSy...
```

### Pusher (4 variables)
```bash
PUSHER_APP_ID=2050003
PUSHER_KEY=[20-char-hex]
PUSHER_SECRET=[40-char-hex]
PUSHER_CLUSTER=us2
```

### Security (3 variables)
```bash
JWT_SECRET_KEY=[64-char-hex]
SECRET_KEY=[64-char-hex]
ENCRYPTION_KEY=[64-char-hex]
```

### Monitoring (1 variable)
```bash
SENTRY_DSN_BACKEND=https://6175c9912112e5a9fa094247539d13f5@o4509912543199232.ingest.us.sentry.io/4510294208937984
```

---

## 🔧 Troubleshooting Commands

### View Logs
```bash
# Using Render CLI
render logs toolboxai-backend
render logs toolboxai-celery-worker --tail

# Or in Dashboard
# https://dashboard.render.com → Select Service → Logs tab
```

### Restart Service
```bash
# Using CLI
render restart toolboxai-backend

# Or in Dashboard
# Select Service → Manual Deploy → Deploy latest commit
```

### Check Service Status
```bash
# Using CLI
render services list

# Check specific service
render services get toolboxai-backend
```

---

## 🗄️ Database Commands

### Connect to Supabase Database
```bash
# Using connection pooler (production)
psql "postgresql://postgres.[project]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"

# Using direct connection (migrations only)
psql "postgresql://postgres.[project]:[password]@db.[project].supabase.co:5432/postgres"
```

### Run Migrations
```bash
# See: docs/DATABASE_MIGRATION.md
```

### Check Database Size
```sql
SELECT
    pg_size_pretty(pg_database_size(current_database())) as database_size,
    count(*) as table_count
FROM information_schema.tables
WHERE table_schema = 'public';
```

---

## 📦 Common Tasks

### Update Environment Variable
1. Go to: https://dashboard.render.com
2. Select service
3. **Environment** tab
4. Update variable
5. Save (service will auto-redeploy)

### Scale Service
```bash
# Using CLI
render scale toolboxai-backend --plan standard

# Or in Dashboard
# Service → Settings → Instance Type → Select plan
```

### View Celery Tasks
1. Go to: https://toolboxai-celery-flower.onrender.com
2. Login: `admin` / [your-flower-password]
3. View: Tasks, Workers, Monitor tabs

### Check Disk Usage
```bash
# SSH into service (if shell enabled)
render shell toolboxai-backend

# Check disk usage
df -h
du -sh /opt/render/project/src/*
```

---

## 🚨 Emergency Procedures

### Service Down
1. Check: https://status.render.com
2. Check: https://dashboard.render.com → Service → Logs
3. Restart: Service → Manual Deploy → Deploy latest commit
4. If database issue: Check Supabase status and connection string

### Database Connection Lost
1. Verify: SUPABASE_URL and DATABASE_URL are correct
2. Check: Supabase Dashboard → Database → Health
3. Test: Connection string in local psql
4. Restart: All backend services

### High Error Rate
1. Check: Sentry dashboard for error details
2. Check: Render service logs
3. Check: Celery Flower for failed tasks
4. Roll back: If recent deployment caused issues

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `DEPLOYMENT_CHECKLIST.md` | 85-step deployment checklist |
| `docs/RENDER_DEPLOYMENT_GUIDE.md` | Comprehensive deployment guide |
| `docs/SUPABASE_LOCAL_SETUP.md` | Local development with Supabase |
| `infrastructure/render/render.production.yaml` | Blueprint definition |
| `infrastructure/render/ENVIRONMENT_VARIABLES.template` | Environment variable template |
| `scripts/validate_render_env.py` | Configuration validation script |

---

## 💰 Cost Breakdown

### Monthly Costs (Render)
- Backend API: $7
- MCP API: $7
- Agent Coordinator: $7
- Celery Worker: $7
- Celery Beat: $7
- Celery Flower: $7
- Monitoring: $7
- Redis: $10
- Dashboard: Free
- Cleanup Cron: Free
- **Subtotal: $59/month**

### Monthly Costs (External)
- Supabase: Free tier (500MB DB, 1GB storage)
- OpenAI API: Pay-per-use
- Anthropic API: Pay-per-use
- Google AI API: Pay-per-use
- Pusher: Free tier (100 connections)
- Sentry: Free tier (5k events/month)

### Scaling Costs
- Upgrade to Standard plan: $21/service (vs $7 Starter)
- Pro plan: $85/service (vs $7 Starter)
- Additional Redis: $10/instance (Starter)

---

## 🔗 Important Links

- **Render Docs**: https://render.com/docs
- **Render Status**: https://status.render.com
- **Supabase Docs**: https://supabase.com/docs
- **Supabase Status**: https://status.supabase.com
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **React Docs**: https://react.dev
- **Celery Docs**: https://docs.celeryq.dev

---

## 📞 Support Contacts

- **Render Support**: support@render.com
- **Supabase Support**: support@supabase.io
- **Project Issues**: https://github.com/GrayGhostDev/ToolboxAI-Solutions/issues

---

*Last Updated: 2025-11-07*
*Keep this reference handy for quick deployment tasks*
