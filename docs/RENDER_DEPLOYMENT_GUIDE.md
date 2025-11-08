# Render Deployment Guide - ToolboxAI Solutions

## Prerequisites Checklist

- [ ] Supabase cloud project created at https://supabase.com/dashboard
- [ ] GitHub repository accessible: GrayGhostDev/ToolboxAI-Solutions
- [ ] Render account created at https://render.com
- [ ] All API keys collected (see Environment Variables section)

## Step 1: Retrieve Supabase Cloud Credentials

### A. Get Project URL and API Keys

1. Go to https://supabase.com/dashboard
2. Select your project
3. Navigate to **Project Settings** → **API**
4. Copy the following values:
   - **Project URL**: `https://[project-ref].supabase.co`
   - **anon/public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (starts with eyJ)
   - **service_role key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (different from anon key)

### B. Get Database Connection String

1. In the same Supabase Dashboard, go to **Project Settings** → **Database**
2. Scroll to **Connection String** section
3. Select **Connection pooling** tab (NOT Direct connection)
4. Mode: **Transaction**
5. Copy the connection string that looks like:
   ```
   postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```
6. Replace `[YOUR-PASSWORD]` with your actual database password

**Important:** Use port **6543** (pooler) NOT port **5432** (direct) for production services.

### C. Create Storage Bucket

1. In Supabase Dashboard, navigate to **Storage**
2. Click **Create bucket**
3. Bucket name: `toolboxai-uploads`
4. Set as **Public** if user uploads should be accessible, or **Private** if access control needed
5. Click **Create bucket**

## Step 2: Prepare Environment Variables

You'll need to set these environment variables in Render. Create a local file to organize them first:

### Required Supabase Values (from Step 1)

```bash
# From Supabase Dashboard → Project Settings → API
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...[anon-key]
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...[service-role-key]

# From Supabase Dashboard → Project Settings → Database (Connection Pooling, Port 6543)
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# Storage configuration
STORAGE_BACKEND=supabase
SUPABASE_STORAGE_BUCKET=toolboxai-uploads
```

### Required AI API Keys

```bash
# OpenAI (get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-proj-...

# Anthropic Claude (get from https://console.anthropic.com/settings/keys)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Google AI (get from https://makersuite.google.com/app/apikey)
GOOGLE_API_KEY=AIzaSy...
```

### Required Pusher Credentials

```bash
# From https://dashboard.pusher.com → App Keys
PUSHER_APP_ID=2050003
PUSHER_KEY=[your-pusher-key]
PUSHER_SECRET=[your-pusher-secret]
PUSHER_CLUSTER=us2
```

### Required Monitoring

```bash
# Sentry (already have)
SENTRY_DSN_BACKEND=https://6175c9912112e5a9fa094247539d13f5@o4509912543199232.ingest.us.sentry.io/4510294208937984

# Celery Flower monitoring basic auth
FLOWER_BASIC_AUTH_PASSWORD=[generate-secure-password]
```

### Security Tokens (Generate New)

```bash
# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=[generate-64-char-hex]
SECRET_KEY=[generate-64-char-hex]
ENCRYPTION_KEY=[generate-64-char-hex]
```

### Application Configuration

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false
CORS_ORIGINS=["https://toolboxai-dashboard.onrender.com"]
```

## Step 3: Deploy Blueprint to Render

### A. Using Render Dashboard (Recommended)

1. Go to https://dashboard.render.com
2. Click **Blueprints** in the left sidebar
3. Click **New Blueprint Instance**
4. Connect your GitHub account if not already connected
5. Select repository: **GrayGhostDev/ToolboxAI-Solutions**
6. Branch: **main**
7. Blueprint path: `infrastructure/render/render.production.yaml`
8. Click **Apply**

### B. Configure Environment Variable Groups

Render will detect the environment variable groups from the blueprint. You'll need to fill in the values:

#### toolboxai-secrets Group

Set all the values from Step 2 (Supabase, API keys, Pusher, Sentry, etc.)

#### toolboxai-frontend-env Group

```bash
VITE_API_BASE_URL=https://toolboxai-backend.onrender.com
VITE_PUSHER_KEY=[same-as-PUSHER_KEY-above]
VITE_PUSHER_CLUSTER=us2
VITE_SENTRY_DSN=[your-frontend-sentry-dsn]
```

#### toolboxai-monitoring Group

```bash
GRAFANA_ADMIN_PASSWORD=[generate-secure-password]
PROMETHEUS_RETENTION_TIME=15d
LOKI_RETENTION_PERIOD=30d
ALERTMANAGER_SLACK_WEBHOOK_URL=[optional-slack-webhook]
```

#### supabase-local Group

**Note:** These are for local development only. Set them to the local values from `.env.supabase.local.example` - they won't be used in production.

### C. Review and Deploy

1. Review all services that will be created:
   - ✅ toolboxai-backend (Web Service, Starter)
   - ✅ toolboxai-redis (Redis, Starter)
   - ✅ toolboxai-dashboard (Static Site, Free)
   - ✅ toolboxai-mcp (Web Service, Starter)
   - ✅ toolboxai-agent-coordinator (Web Service, Starter)
   - ✅ toolboxai-celery-worker (Worker, Starter)
   - ✅ toolboxai-celery-beat (Worker, Starter)
   - ✅ toolboxai-celery-flower (Web Service, Starter)
   - ✅ toolboxai-monitoring (Worker, Starter)
   - ✅ toolboxai-cleanup (Cron Job, Free)

2. Estimated monthly cost: **~$50/month**
   - 7 Starter web/worker services × $7 = $49
   - 1 Starter Redis = $10
   - 1 Static site = Free
   - 1 Cron job = Free
   - **Total: $59/month**

3. Click **Apply** to start deployment

## Step 4: Verify Deployment

### A. Check Service Health

Once deployment completes (typically 5-10 minutes), verify each service:

1. **Backend API**: https://toolboxai-backend.onrender.com/health
   - Should return: `{"status": "healthy", "database": "connected"}`

2. **Dashboard**: https://toolboxai-dashboard.onrender.com
   - Should load the React application

3. **MCP API**: https://toolboxai-mcp.onrender.com/health
   - Should return health status

4. **Agent Coordinator**: https://toolboxai-agent-coordinator.onrender.com/health
   - Should return health status

5. **Celery Flower**: https://toolboxai-celery-flower.onrender.com
   - Should show Celery monitoring dashboard (requires basic auth)

### B. Check Database Connection

1. In Render Dashboard, go to **toolboxai-backend** service
2. Click **Logs** tab
3. Verify you see: `✅ Database connection successful`
4. Check for any error messages related to Supabase

### C. Test Key Features

1. **User Registration/Login** - Test authentication flow
2. **File Upload** - Verify Supabase Storage integration
3. **Real-time Updates** - Test Pusher Channels integration
4. **Background Tasks** - Verify Celery workers are processing

## Step 5: Configure Custom Domain (Optional)

### A. Add Custom Domain to Dashboard

1. In Render Dashboard, go to **toolboxai-dashboard** service
2. Click **Settings** tab
3. Scroll to **Custom Domain**
4. Click **Add Custom Domain**
5. Enter your domain: `app.toolboxai.com` (example)
6. Follow Render's instructions to add DNS records

### B. Update Frontend Environment Variables

After adding custom domain:

1. Go to **toolboxai-frontend-env** group
2. Update `VITE_API_BASE_URL` if backend also has custom domain
3. Update CORS settings in backend if using custom domain

## Troubleshooting

### Database Connection Issues

**Error:** `connection refused` or `timeout`
- ✅ Verify you're using port **6543** (pooler) not 5432
- ✅ Check DATABASE_URL format matches the pooler connection string
- ✅ Verify password doesn't contain special characters that need URL encoding

**Error:** `relation does not exist`
- ✅ Run database migrations: See `DATABASE_MIGRATION.md`

### Celery Not Processing Tasks

**Error:** Tasks stuck in pending state
- ✅ Check Redis connection in Celery Worker logs
- ✅ Verify `REDIS_URL` environment variable is set correctly
- ✅ Check Celery Beat is running (should see heartbeat in logs)

### Frontend Cannot Connect to Backend

**Error:** CORS errors in browser console
- ✅ Verify `CORS_ORIGINS` includes dashboard URL
- ✅ Check `VITE_API_BASE_URL` points to correct backend URL
- ✅ Verify backend service is running (check logs)

### Storage Upload Failures

**Error:** Cannot upload files
- ✅ Verify `toolboxai-uploads` bucket exists in Supabase
- ✅ Check bucket permissions (public vs private)
- ✅ Verify `SUPABASE_SERVICE_ROLE_KEY` is set correctly

## Monitoring and Maintenance

### View Logs

1. **Application Logs**: Render Dashboard → Service → Logs tab
2. **Error Tracking**: Sentry Dashboard (https://sentry.io)
3. **Celery Monitoring**: Flower Dashboard (https://toolboxai-celery-flower.onrender.com)

### Backup Strategy

**Database Backups:**
- Supabase provides automatic daily backups
- Configure backup retention in Supabase Dashboard → Database → Backups
- Recommended: Enable Point-in-Time Recovery (PITR) for production

**Configuration Backups:**
- Blueprint YAML is version controlled in Git
- Environment variables should be documented securely (not in Git)
- Consider using a password manager to store all credentials

### Scaling Considerations

**When to Upgrade Plans:**

1. **Starter → Standard** ($21/month each):
   - Backend handling > 1000 requests/minute
   - Need more than 512MB RAM
   - Want faster build times

2. **Add Database Read Replicas**:
   - High read traffic causing performance issues
   - Configure in Supabase Dashboard → Database → Read Replicas

3. **Enable Auto-Scaling**:
   - Unpredictable traffic patterns
   - Add to Blueprint: `scaling: { minInstances: 2, maxInstances: 10 }`

## Security Checklist

- [ ] All secrets use strong, randomly generated values
- [ ] Supabase Row Level Security (RLS) enabled on all tables
- [ ] Rate limiting configured in FastAPI backend
- [ ] HTTPS enforced (automatic with Render)
- [ ] Security headers configured on static site
- [ ] Sentry monitoring active
- [ ] Regular dependency updates scheduled
- [ ] Database backups verified
- [ ] Access logs reviewed weekly

## Support Resources

- **Render Documentation**: https://render.com/docs
- **Supabase Documentation**: https://supabase.com/docs
- **Render Status Page**: https://status.render.com
- **Supabase Status Page**: https://status.supabase.com

## Cost Optimization Tips

1. **Use Free Static Site**: Dashboard hosting is free on Render
2. **Optimize Worker Usage**: Consider reducing Celery workers during low-traffic hours
3. **Database Connection Pooling**: Using port 6543 (already configured) reduces connection overhead
4. **Monitor Bandwidth**: Render includes generous bandwidth, but monitor usage in Dashboard
5. **Supabase Free Tier**: Up to 500MB database, 1GB file storage, 50GB bandwidth per month included

---

**Deployment Status:** Ready for deployment after environment variables are configured
**Estimated Setup Time:** 30-45 minutes
**Monthly Cost:** ~$59 USD (Render) + Supabase usage (free tier available)
